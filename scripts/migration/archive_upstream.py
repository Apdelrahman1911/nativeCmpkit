#!/usr/bin/env python3
"""Read-only, resumable public GitHub metadata exporter (Python standard library).

Uses an already-authenticated `gh`; never reads, logs, or copies its token. REST
response bodies are preserved verbatim, with a safe response-header sidecar.
GraphQL response bodies and variables are preserved too. All imported text and
downloaded attachments are untrusted data: this program never executes them.

Example:
  python3 scripts/migration/archive_upstream.py --phase all
  python3 scripts/migration/archive_upstream.py --phase finalize --verify

Successful and failed responses are both cached. To deliberately re-observe an
endpoint, use a *new* output directory; do not silently replace an observation.
Git objects/ref preservation is a separate migration operation.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import threading
from datetime import datetime, timezone
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


SCHEMA_VERSION = 1
BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
SAFE_HEADERS = {
    "content-type", "date", "etag", "last-modified", "link", "location",
    "x-github-request-id", "x-ratelimit-limit", "x-ratelimit-remaining",
    "x-ratelimit-reset", "x-ratelimit-resource", "x-ratelimit-used",
    "retry-after", "deprecation", "sunset", "warning",
    "x-github-api-version-selected",
}
URL_RE = re.compile(r"https?://[^\s<>\"'`\\]+")
ATTACHMENT_HOSTS = {"user-images.githubusercontent.com", "private-user-images.githubusercontent.com"}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def next_link(headers):
    for link in headers.get("link", "").split(","):
        match = re.search(r'<([^>]+)>;\s*rel="next"', link)
        if match:
            return match.group(1)
    return None


class Archive:
    def __init__(self, args):
        self.args = args
        self.root = Path(args.output).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.repository = args.repository
        self.api_root = f"repos/{self.repository}"
        self.lock = threading.Lock()
        self.progress = read(self.root / "datasets.json", {})
        self.observation = read(self.root / "observation.json")
        if self.observation is None:
            self.observation = {
                "schema_version": SCHEMA_VERSION,
                "repository": self.repository,
                "repository_url": f"https://github.com/{self.repository}",
                "source_baseline": args.baseline,
                "started_at": utc_now(),
                "authentication": "Existing gh CLI authentication; tokens never exported",
                "api_version": "2022-11-28",
                "snapshot_semantics": "A paginated observation interval, not an atomic GitHub snapshot",
            }
            dump(self.root / "observation.json", self.observation)
        elif self.observation["repository"] != self.repository or self.observation["source_baseline"] != args.baseline:
            raise ValueError("Output directory belongs to another repository or baseline")

    def log(self, message):
        with self.lock:
            print(f"{utc_now()} {message}", flush=True)

    def dataset(self, name, **values):
        with self.lock:
            self.progress[name] = values
            dump(self.root / "datasets.json", self.progress)

    def request(self, relative, endpoint, *, query=None, variables=None, accept="application/vnd.github+json"):
        destination = self.root / relative
        sidecar = destination.with_name(destination.stem + ".http.json")
        existing = read(sidecar)
        if destination.exists() and existing is not None:
            if existing["endpoint"] != endpoint:
                raise ValueError(f"Cached endpoint differs for {relative}; use a new output path")
            if query and read(destination.with_name(destination.stem + ".query.json")) != {"query": query, "variables": variables or {}}:
                raise ValueError(f"Cached query differs for {relative}; version the query output path instead of overwriting an observation")
            # A cached failure remains an explicitly recorded failure, not a retry.
            try:
                return read(destination), existing
            except json.JSONDecodeError:
                return None, existing
        parsed_endpoint = urlsplit(endpoint)
        if parsed_endpoint.scheme and (parsed_endpoint.scheme != "https" or parsed_endpoint.netloc != "api.github.com"):
            raise ValueError("Refusing to pass gh authentication to a non-API endpoint")
        if endpoint.startswith("//"):
            raise ValueError("Protocol-relative API endpoints are not allowed")
        cmd = ["gh", "api", "--include", "--method", "POST" if query else "GET",
               "-H", f"Accept: {accept}",
               "-H", "X-GitHub-Api-Version: 2022-11-28", endpoint]
        input_bytes = None
        if query:
            cmd += ["--input", "-"]
            payload = {"query": query, "variables": variables or {}}
            input_bytes = json.dumps(payload).encode("utf-8")
            dump(destination.with_name(destination.stem + ".query.json"), payload)
        observed = utc_now()
        try:
            result = subprocess.run(cmd, input=input_bytes, capture_output=True, timeout=180)
            parts = re.split(rb"\r?\n\r?\n", result.stdout, maxsplit=1)
            status = None
            headers = {}
            body = result.stdout
            if len(parts) == 2 and parts[0].startswith(b"HTTP/"):
                status = int(parts[0].splitlines()[0].split()[1])
                for line in parts[0].splitlines()[1:]:
                    name, sep, value = line.partition(b":")
                    if sep and name.decode("ascii", "ignore").lower() in SAFE_HEADERS:
                        headers[name.decode("ascii").lower()] = value.strip().decode("utf-8", "replace")
                body = parts[1]
            meta = {
                "observed_at": observed,
                "completed_at": utc_now(),
                "endpoint": endpoint,
                "method": "POST (read-only GraphQL query)" if query else "GET",
                "request_accept": accept,
                "status": status,
                "gh_exit_code": result.returncode,
                "headers": headers,
                "response_body": str(destination.relative_to(self.root)),
                "response_sha256": hashlib.sha256(body).hexdigest(),
            }
            if result.returncode:
                meta["error"] = result.stderr.decode("utf-8", "replace").strip()
        except subprocess.TimeoutExpired:
            body = b"null\n"
            meta = {"observed_at": observed, "completed_at": utc_now(), "endpoint": endpoint,
                    "method": "POST (read-only GraphQL query)" if query else "GET", "status": None,
                    "gh_exit_code": None, "headers": {}, "response_body": relative,
                    "response_sha256": hashlib.sha256(body).hexdigest(), "error": "gh API request timed out after 180 seconds"}
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = None
            meta["error"] = "Response was not JSON; verbatim bytes preserved"
        if query and isinstance(data, dict) and data.get("errors"):
            meta["graphql_errors"] = data["errors"]
        meta["success"] = bool(meta.get("status") and 200 <= meta["status"] < 300 and
                               not meta.get("error") and not meta.get("graphql_errors"))
        dump(sidecar, meta)
        with self.lock:
            with (self.root / "requests.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(meta, ensure_ascii=False) + "\n")
        if not meta["success"]:
            self.log(f"Recorded API limitation: {relative}: HTTP {meta.get('status')} {meta.get('error', meta.get('graphql_errors', ''))}")
        remaining = meta.get("headers", {}).get("x-ratelimit-remaining")
        if remaining and int(remaining) < 80:
            raise RuntimeError("API rate limit reserve reached; retained all completed observations")
        return data, meta

    def pages(self, name, endpoint, *, key=None, output=None, accept="application/vnd.github+json"):
        combined = []
        page = 1
        complete = True
        seen = set()
        while endpoint:
            if endpoint in seen:
                raise RuntimeError(f"Pagination cycle at {endpoint}")
            seen.add(endpoint)
            relative = f"rest/{name}/page-{page:04}.json"
            data, metadata = self.request(relative, endpoint, accept=accept)
            values = data.get(key) if key and isinstance(data, dict) else data
            if not metadata["success"] or not isinstance(values, list):
                complete = False
                break
            combined.extend(values)
            endpoint = next_link(metadata["headers"])
            page += 1
        if output is None:
            output = f"{name}.json"
        dump(self.root / output, combined)
        self.dataset(name, output=output, count=len(combined), pages=page - (1 if complete else 0),
                     complete=complete, pagination="Followed every Link rel=next until absent" if complete else "Stopped at archived API error")
        return combined

    def single(self, name, suffix, *, absolute=False):
        data, meta = self.request(f"{name}.json", suffix if absolute else f"{self.api_root}/{suffix}")
        self.dataset(name, output=f"{name}.json", complete=meta["success"], status=meta["status"])
        return data if meta["success"] else None

    def parallel(self, work, fn, label):
        work = list(work)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.workers) as pool:
            pending = {pool.submit(fn, item): item for item in work}
            done = 0
            for future in concurrent.futures.as_completed(pending):
                future.result()
                done += 1
                if done % 40 == 0 or done == len(work):
                    self.log(f"{label}: {done}/{len(work)}")

    def initial(self):
        self.single("rate-limit-start", "rate_limit", absolute=True)
        self.single("repository", self.api_root, absolute=True)
        endpoints = [
            ("issues", "issues?state=all&sort=created&direction=asc&per_page=100"),
            ("pull-requests", "pulls?state=all&sort=created&direction=asc&per_page=100"),
            ("issue-comments", "issues/comments?sort=created&direction=asc&per_page=100"),
            ("review-comments", "pulls/comments?sort=created&direction=asc&per_page=100"),
            ("commit-comments", "comments?per_page=100"),
            ("releases", "releases?per_page=100"),
            ("labels", "labels?per_page=100"),
            ("milestones", "milestones?state=all&per_page=100"),
            ("branches", "branches?per_page=100"),
            ("tags", "tags?per_page=100"),
            ("contributors", "contributors?anon=true&per_page=100"),
            ("issue-events", "issues/events?per_page=100"),
        ]
        self.parallel(endpoints, lambda item: self.pages(item[0], f"{self.api_root}/{item[1]}"), "Initial datasets")
        self.log("Core issue/PR/comment/release lists ready for historical review")

    def details(self):
        issues = read(self.root / "issues.json")
        pulls = read(self.root / "pull-requests.json")
        if issues is None or pulls is None:
            raise ValueError("Run --phase initial first")

        def issue_detail(issue):
            number = issue["number"]
            prefix = f"issues/{number}"
            if "pull_request" not in issue:
                self.single(f"{prefix}/detail", f"issues/{number}")
            self.pages(f"{prefix}/timeline", f"{self.api_root}/issues/{number}/timeline?per_page=100")
            if issue.get("reactions", {}).get("total_count", 0):
                self.pages(f"{prefix}/reactions", f"{self.api_root}/issues/{number}/reactions?per_page=100")

        def pr_detail(pr):
            number = pr["number"]
            prefix = f"pull-requests/{number}"
            detail = self.single(f"{prefix}/detail", f"pulls/{number}")
            reviews = self.pages(f"{prefix}/reviews", f"{self.api_root}/pulls/{number}/reviews?per_page=100")
            files = self.pages(f"{prefix}/files", f"{self.api_root}/pulls/{number}/files?per_page=100")
            commits = self.pages(f"{prefix}/commits", f"{self.api_root}/pulls/{number}/commits?per_page=100")
            dump(self.root / prefix / "coverage.json", {
                "number": number, "reviews": len(reviews), "files": len(files), "commits": len(commits),
                "expected_files": detail.get("changed_files") if detail else None,
                "expected_commits": detail.get("commits") if detail else None,
                "files_count_matches_detail": bool(detail is not None and detail.get("changed_files") == len(files)),
                "commits_count_matches_detail": bool(detail is not None and detail.get("commits") == len(commits)),
                "documented_endpoint_limits": "REST pull files maximum 3000; pull commits maximum 250; Git bundle preserves available PR Git refs independently",
            })

        self.parallel(issues, issue_detail, "Issue/PR timelines and issue details")
        self.parallel(pulls, pr_detail, "PR details/reviews/files/commits")

        reaction_jobs = []
        for kind, suffix in [("issue-comments", "issues/comments"), ("review-comments", "pulls/comments"), ("commit-comments", "comments")]:
            for comment in read(self.root / f"{kind}.json", []):
                if comment.get("reactions", {}).get("total_count", 0):
                    reaction_jobs.append((f"reactions/{kind}/{comment['id']}", f"{self.api_root}/{suffix}/{comment['id']}/reactions?per_page=100"))
        self.parallel(reaction_jobs, lambda job: self.pages(*job), "Comment reaction actor lists")

        for release in read(self.root / "releases.json", []):
            self.pages(f"releases/{release['id']}/assets", f"{self.api_root}/releases/{release['id']}/assets?per_page=100")
            if release.get("reactions", {}).get("total_count", 0):
                self.pages(f"releases/{release['id']}/reactions", f"{self.api_root}/releases/{release['id']}/reactions?per_page=100")

    def graphql_connection(self, name, query, variables, extract):
        nodes = []
        cursor = None
        page = 1
        complete = True
        count = None
        while True:
            data, meta = self.request(f"graphql/{name}/page-{page:04}.json", "graphql", query=query,
                                      variables={**variables, "cursor": cursor})
            if not meta["success"]:
                complete = False
                break
            connection = extract(data)
            count = connection.get("totalCount", count)
            nodes.extend(connection.get("nodes", []))
            info = connection.get("pageInfo", {})
            if not info.get("hasNextPage"):
                break
            new_cursor = info.get("endCursor")
            if not new_cursor or new_cursor == cursor:
                raise RuntimeError(f"GraphQL pagination stalled: {name}")
            cursor = new_cursor
            page += 1
        dump(self.root / f"graphql/{name}.json", nodes)
        self.dataset(f"graphql/{name}", output=f"graphql/{name}.json", count=len(nodes),
                     totalCount=count, pages=page, complete=complete and (count is None or count == len(nodes)))
        return nodes

    def graphql(self):
        owner, name = self.repository.split("/")
        inventory = '''query($owner:String!,$name:String!){repository(owner:$owner,name:$name){
          id nameWithOwner url createdAt updatedAt pushedAt isArchived isDisabled isEmpty
          hasIssuesEnabled hasDiscussionsEnabled hasWikiEnabled isSecurityPolicyEnabled
          issues{totalCount} pullRequests{totalCount} discussions{totalCount}
          releases{totalCount} labels{totalCount} milestones{totalCount}
          stargazers{totalCount} watchers{totalCount} forks{totalCount}
          defaultBranchRef{name target{oid}} } rateLimit{cost remaining resetAt}}'''
        self.request("graphql/repository-inventory.json", "graphql", query=inventory, variables={"owner": owner, "name": name})
        discussion_query = '''query($owner:String!,$name:String!,$cursor:String){repository(owner:$owner,name:$name){
          discussions(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor} nodes{
            id number title body url createdAt updatedAt closed closedAt locked activeLockReason
            author{login url} authorAssociation isAnswered answerChosenAt answerChosenBy{login url}
            category{id name description emoji isAnswerable} answer{id url}
          }}} rateLimit{cost remaining resetAt}}'''
        discussions = self.graphql_connection("discussions", discussion_query, {"owner": owner, "name": name},
                                               lambda data: data["data"]["repository"]["discussions"])
        discussion_comment_fields = '''id body url createdAt updatedAt lastEditedAt author{login url} authorAssociation
          isAnswer isMinimized minimizedReason replyTo{id url}'''
        for discussion in discussions:
            number = discussion["number"]
            comments_query = '''query($id:ID!,$cursor:String){node(id:$id){... on Discussion{
              comments(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor} nodes{''' + discussion_comment_fields + '''
              replies{totalCount}}}}}}'''
            comments = self.graphql_connection(f"discussions/{number}/comments", comments_query, {"id": discussion["id"]},
                                                lambda data: data["data"]["node"]["comments"])
            for comment in comments:
                replies_query = '''query($id:ID!,$cursor:String){node(id:$id){... on DiscussionComment{
                  replies(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor} nodes{''' + discussion_comment_fields + '''}}}}}'''
                self.graphql_connection(f"discussions/{number}/replies/{comment['id']}", replies_query, {"id": comment["id"]},
                                        lambda data: data["data"]["node"]["replies"])
        self.graphql_connection("discussion-categories", '''query($owner:String!,$name:String!,$cursor:String){
          repository(owner:$owner,name:$name){discussionCategories(first:100,after:$cursor){totalCount
          pageInfo{hasNextPage endCursor} nodes{id name slug description emoji isAnswerable createdAt updatedAt}}}}''',
          {"owner": owner, "name": name}, lambda data: data["data"]["repository"]["discussionCategories"])
        self.graphql_connection("projects-v2", '''query($owner:String!,$name:String!,$cursor:String){
          repository(owner:$owner,name:$name){projectsV2(first:100,after:$cursor){totalCount
          pageInfo{hasNextPage endCursor} nodes{id number title shortDescription readme url closed createdAt updatedAt}}}}''',
          {"owner": owner, "name": name}, lambda data: data["data"]["repository"]["projectsV2"])

        comment_fields = '''id databaseId url body createdAt updatedAt lastEditedAt author{login url}
          authorAssociation isMinimized minimizedReason state path diffHunk position originalPosition
          line originalLine startLine originalStartLine replyTo{id databaseId} pullRequestReview{id databaseId}'''
        thread_fields = '''id isResolved isOutdated resolvedBy{id login url} path line originalLine
          startLine originalStartLine diffSide startDiffSide''' + ''' comments(first:100){
          totalCount pageInfo{hasNextPage endCursor} nodes{''' + comment_fields + '''}}'''
        closing_fields = '''id number url title state repository{nameWithOwner}'''
        pr_query = '''query($ids:[ID!]!){nodes(ids:$ids){... on PullRequest{
          id number url state isDraft createdAt updatedAt closedAt merged mergedAt author{login url}
          mergedBy{login url} mergeCommit{oid} baseRefName headRefName baseRefOid headRefOid
          reviewDecision mergeStateStatus mergeable maintainerCanModify isCrossRepository
          closingIssuesReferences(first:100){totalCount pageInfo{hasNextPage endCursor}
          nodes{''' + closing_fields + '''}}
          reviewThreads(first:100){totalCount pageInfo{hasNextPage endCursor} nodes{''' + thread_fields + '''}}
        }} rateLimit{cost remaining resetAt}}'''
        pulls = read(self.root / "pull-requests.json", [])
        summaries = []
        for i in range(0, len(pulls), 10):
            batch = pulls[i:i+10]
            result, meta = self.request(f"graphql/pull-requests/batch-v2-{i//10+1:04}.json", "graphql", query=pr_query,
                                        variables={"ids": [pr["node_id"] for pr in batch]})
            if not meta["success"]:
                raise RuntimeError("PR GraphQL enrichment failed; response preserved. Fix or document the error before resuming.")
            for pr in result["data"]["nodes"]:
                if pr is None:
                    continue
                number = pr["number"]
                dump(self.root / f"graphql/pull-requests/{number}.json", pr)
                summaries.append(pr)
                threads = pr["reviewThreads"]["nodes"]
                if pr["reviewThreads"]["pageInfo"]["hasNextPage"]:
                    query = '''query($id:ID!,$cursor:String){node(id:$id){... on PullRequest{
                      reviewThreads(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor} nodes{''' + thread_fields + '''}}}}}'''
                    threads = self.graphql_connection(f"pull-requests/{number}/review-threads", query, {"id": pr["id"]},
                                                       lambda data: data["data"]["node"]["reviewThreads"])
                for j, thread in enumerate(threads):
                    if thread["comments"]["pageInfo"]["hasNextPage"]:
                        query = '''query($id:ID!,$cursor:String){node(id:$id){... on PullRequestReviewThread{
                          comments(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor} nodes{''' + comment_fields + '''}}}}}'''
                        self.graphql_connection(f"pull-requests/{number}/thread-{j+1}/comments", query, {"id": thread["id"]},
                                                lambda data: data["data"]["node"]["comments"])
                if pr["closingIssuesReferences"]["pageInfo"]["hasNextPage"]:
                    query = '''query($id:ID!,$cursor:String){node(id:$id){... on PullRequest{
                      closingIssuesReferences(first:100,after:$cursor){totalCount
                      pageInfo{hasNextPage endCursor} nodes{''' + closing_fields + '''}}}}}'''
                    self.graphql_connection(f"pull-requests/{number}/closing-issues", query, {"id": pr["id"]},
                                            lambda data: data["data"]["node"]["closingIssuesReferences"])
            if (i // 10 + 1) % 10 == 0:
                self.log(f"GraphQL review-thread/closing-reference enrichment: {min(i+10,len(pulls))}/{len(pulls)}")
        dump(self.root / "graphql/pull-requests.json", summaries)
        self.dataset("graphql/pull-requests", output="graphql/pull-requests.json", count=len(summaries),
                     expected=len(pulls), complete=len(summaries) == len(pulls))

    def supplemental(self):
        single = [
            ("license", "license"), ("languages", "languages"), ("topics", "topics"),
            ("community-profile", "community/profile"), ("pages-settings", "pages"),
            ("dependency-sbom", "dependency-graph/sbom"),
        ]
        for name, endpoint in single:
            self.single(name, endpoint)
        lists = [
            ("forks", "forks?sort=oldest&per_page=100", None),
            ("watchers", "subscribers?per_page=100", None),
            ("projects-classic", "projects?state=all&per_page=100", None),
            ("rulesets", "rulesets?includes_parents=true&per_page=100", None),
            ("public-security-advisories", "security-advisories?per_page=100", None),
            ("workflows", "actions/workflows?per_page=100", "workflows"),
            ("deployments", "deployments?per_page=100", None),
            ("public-activity-events", "events?per_page=100", None),
        ]
        self.parallel(lists, lambda item: self.pages(item[0], f"{self.api_root}/{item[1]}", key=item[2]), "Supplemental public datasets")
        self.pages("stargazers", f"{self.api_root}/stargazers?per_page=100", accept="application/vnd.github.star+json")
        for branch in read(self.root / "branches.json", []):
            if branch.get("protected"):
                self.single(f"branch-protection/{quote(branch['name'], safe='')}", f"branches/{quote(branch['name'], safe='')}/protection")
        self.parallel(read(self.root / "deployments.json", []), lambda deployment:
                      self.pages(f"deployments/{deployment['id']}/statuses", f"{self.api_root}/deployments/{deployment['id']}/statuses?per_page=100"),
                      "Public deployment status histories")
        # Commit metadata/statuses for the audited baseline, not all historical CI logs.
        baseline = self.args.baseline
        self.single("baseline-commit", f"commits/{baseline}")
        self.pages("baseline-statuses", f"{self.api_root}/commits/{baseline}/statuses?per_page=100")
        self.pages("baseline-check-runs", f"{self.api_root}/commits/{baseline}/check-runs?per_page=100", key="check_runs")
        wiki_url = f"https://github.com/{self.repository}.wiki.git"
        if not (self.root / "wiki-observation.json").exists():
            result = subprocess.run(["git", "ls-remote", wiki_url], capture_output=True, text=True, timeout=120)
            dump(self.root / "wiki-observation.json", {
                "observed_at": utc_now(), "url": wiki_url, "operation": "git ls-remote (read-only)",
                "exit_code": result.returncode, "advertised_refs": result.stdout.splitlines(),
                "error": result.stderr.strip() if result.returncode else None,
                "interpretation": "Advertised wiki Git refs require separate bundling" if result.returncode == 0 else
                                  "Wiki Git repository not accessible; not proof that private/deleted wiki content never existed",
            })

    def community(self):
        """Read-only GraphQL fallback when public REST community endpoints deny access."""
        owner, name = self.repository.split("/")
        variables = {"owner": owner, "name": name}
        actor_fields = "id databaseId login url name avatarUrl"
        self.graphql_connection("watchers", """query($owner:String!,$name:String!,$cursor:String){
          repository(owner:$owner,name:$name){watchers(first:100,after:$cursor){totalCount
            pageInfo{hasNextPage endCursor} nodes{""" + actor_fields + """}}} rateLimit{cost remaining resetAt}}""",
            variables, lambda data: data["data"]["repository"]["watchers"])
        # Aliased edges preserve the star timestamp and its original user node together.
        self.graphql_connection("stargazers", """query($owner:String!,$name:String!,$cursor:String){
          repository(owner:$owner,name:$name){stargazers(first:100,after:$cursor){totalCount
            pageInfo{hasNextPage endCursor} nodes:edges{starredAt node{""" + actor_fields + """}}}}
            rateLimit{cost remaining resetAt}}""", variables, lambda data: data["data"]["repository"]["stargazers"])
        # Also preserve the canonical unaliased edges representation. This guards
        # against apparently successful yet inconsistent server/proxy responses.
        self.graphql_connection("stargazers-edges", """query($owner:String!,$name:String!,$cursor:String){
          repository(owner:$owner,name:$name){stargazers(first:100,after:$cursor){totalCount
            pageInfo{hasNextPage endCursor} edges{starredAt node{""" + actor_fields + """}}}}
            rateLimit{cost remaining resetAt}}""", variables,
            lambda data: {**data["data"]["repository"]["stargazers"], "nodes": data["data"]["repository"]["stargazers"].get("edges", [])})
        count_query = """query($owner:String!,$name:String!){repository(owner:$owner,name:$name){
          id nameWithOwner stargazerCount stargazers{totalCount} watchers{totalCount} forks{totalCount}
          issues{totalCount} pullRequests{totalCount} releases{totalCount}} rateLimit{cost remaining resetAt}}"""
        counts, metadata = self.request("graphql/community-counts-recheck.json", "graphql", query=count_query, variables=variables)
        if metadata["success"]:
            expected = counts["data"]["repository"]["stargazers"]["totalCount"]
            for dataset in ["graphql/stargazers", "graphql/stargazers-edges"]:
                value = dict(self.progress[dataset])
                value["independent_repository_count"] = expected
                value["count_matches_independent_repository_query"] = value["count"] == expected
                value["complete"] = value["complete"] and value["count"] == expected
                self.dataset(dataset, **value)

    def content_edits(self):
        """Preserve public edit diffs, editors and tombstones, including nested pages."""
        objects = {}
        for name in ["issues", "issue-comments", "review-comments", "commit-comments"]:
            for item in read(self.root / f"{name}.json", []):
                objects[item["node_id"]] = {"dataset": name, "id": item["id"], "url": item.get("html_url")}
        for path in (self.root / "pull-requests").glob("*/reviews.json"):
            for item in read(path):
                objects[item["node_id"]] = {"dataset": str(path.relative_to(self.root)), "id": item["id"], "url": item.get("html_url")}
        for item in read(self.root / "graphql/discussions.json", []):
            objects[item["id"]] = {"dataset": "graphql/discussions.json", "url": item["url"]}
        for path in (self.root / "graphql/discussions").rglob("*.json"):
            if not path.name.endswith((".http.json", ".query.json")):
                data = read(path)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item and "body" in item:
                            objects[item["id"]] = {"dataset": str(path.relative_to(self.root)), "url": item.get("url")}
        edit_fields = """id createdAt updatedAt editedAt editor{login url} deletedAt deletedBy{login url} diff"""
        query = """query($ids:[ID!]!){nodes(ids:$ids){... on Comment{
          __typename id createdAt updatedAt publishedAt lastEditedAt includesCreatedEdit editor{login url}
          userContentEdits(first:100){totalCount pageInfo{hasNextPage endCursor} nodes{""" + edit_fields + """}}
          ... on PullRequest{reviews{totalCount} comments{totalCount}}
          ... on Issue{comments{totalCount}}
          }} rateLimit{cost remaining resetAt}}"""
        summaries = []
        identifiers = sorted(objects)
        for i in range(0, len(identifiers), 40):
            data, meta = self.request(f"graphql/content-edits/batch-{i//40+1:04}.json", "graphql", query=query,
                                      variables={"ids": identifiers[i:i+40]})
            if not meta["success"]:
                raise RuntimeError("Content edit archive failed; response retained for investigation")
            for item in data["data"]["nodes"]:
                if not item or "id" not in item:
                    continue
                item["source"] = objects[item["id"]]
                if item["userContentEdits"]["pageInfo"]["hasNextPage"]:
                    follow = """query($id:ID!,$cursor:String){node(id:$id){... on Comment{
                      userContentEdits(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor} nodes{""" + edit_fields + """}}}}}"""
                    self.graphql_connection(f"content-edits/objects/{quote(item['id'], safe='')}", follow, {"id": item["id"]},
                                            lambda result: result["data"]["node"]["userContentEdits"])
                summaries.append(item)
            if i // 40 % 5 == 0:
                self.log(f"Public content edit histories: {min(i+40,len(identifiers))}/{len(identifiers)}")
        dump(self.root / "graphql/content-edits.json", summaries)
        self.dataset("graphql/content-edits", output="graphql/content-edits.json", count=len(summaries),
                     expected=len(objects), complete=len(summaries) == len(objects),
                     edit_count=sum(item["userContentEdits"]["totalCount"] for item in summaries))

    def history_enrichment(self):
        """REST force-push events omit beforeCommit; preserve that GraphQL context."""
        wanted = {"head_ref_force_pushed", "base_ref_changed", "head_ref_deleted", "head_ref_restored"}
        events = [event for event in read(self.root / "issue-events.json", []) if event["event"] in wanted]
        commit_fields = """oid url message authoredDate committedDate author{name email user{login url}}
          committer{name email user{login url}}"""
        query = """query($ids:[ID!]!){nodes(ids:$ids){id __typename
          ... on HeadRefForcePushedEvent{createdAt actor{login url} pullRequest{number url}
            beforeCommit{""" + commit_fields + """} afterCommit{""" + commit_fields + """} ref{name}}
          ... on BaseRefChangedEvent{createdAt actor{login url} pullRequest{number url} currentRefName previousRefName}
          ... on HeadRefDeletedEvent{createdAt actor{login url} pullRequest{number url} headRefName}
          ... on HeadRefRestoredEvent{createdAt actor{login url} pullRequest{number url}}
        } rateLimit{cost remaining resetAt}}"""
        results = []
        for i in range(0, len(events), 40):
            data, meta = self.request(f"graphql/history-events/batch-{i//40+1:04}.json", "graphql", query=query,
                                      variables={"ids": [event["node_id"] for event in events[i:i+40]]})
            if not meta["success"]:
                raise RuntimeError("History-event enrichment failed; response retained")
            results.extend(item for item in data["data"]["nodes"] if item is not None)
        dump(self.root / "graphql/history-events.json", results)
        self.dataset("graphql/history-events", output="graphql/history-events.json", count=len(results),
                     expected=len(events), complete=len(results) == len(events))

    def references(self):
        """Build a provenance-rich commit-OID inventory; do not confuse blob SHAs."""
        references = {}
        oid_pattern = re.compile(r"^[0-9a-fA-F]{40}$")
        explicit_fields = {"commit_id", "original_commit_id", "merge_commit_sha", "head_sha", "base_sha",
                           "before_commit", "after_commit", "baseRefOid", "headRefOid"}
        commit_url_pattern = re.compile(r"/(?:git/)?commits?/([0-9a-fA-F]{40})(?:$|[/?#])")

        def add(value, pointer, metadata, declared_url=None):
            if not isinstance(value, str) or not oid_pattern.fullmatch(value) or value == "0" * 40:
                return
            entry = {"response_body": metadata["response_body"], "json_pointer": pointer,
                     "endpoint": metadata["endpoint"]}
            if declared_url:
                entry["declared_commit_url"] = declared_url
            references.setdefault(value.lower(), []).append(entry)

        def traverse(value, pointer, metadata, parent_key=None):
            if isinstance(value, dict):
                for key, child in value.items():
                    child_pointer = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
                    if key in explicit_fields:
                        add(child, child_pointer, metadata, value.get("commit_url"))
                    elif key == "sha":
                        uri = value.get("url", "")
                        if (commit_url_pattern.search(uri) or parent_key in {"commit", "mergeCommit", "beforeCommit", "afterCommit"}
                            or (parent_key in {"head", "base"} and "ref" in value)
                            or ("statuses_url" in value and "environment" in value)
                            or value.get("event") == "committed"):
                            add(child, child_pointer, metadata, uri if commit_url_pattern.search(uri) else None)
                    elif key == "oid" and parent_key in {"commit", "mergeCommit", "beforeCommit", "afterCommit", "target"}:
                        add(child, child_pointer, metadata, value.get("url"))
                    elif key in {"before", "head", "after"} and parent_key == "payload":
                        add(child, child_pointer, metadata)
                    if key in {"commit_url", "url", "html_url"} and isinstance(child, str):
                        parsed = urlsplit(child)
                        if parsed.hostname in {"github.com", "api.github.com"}:
                            match = commit_url_pattern.search(parsed.path)
                            if match:
                                add(match.group(1), child_pointer, metadata, child)
                    traverse(child, child_pointer, metadata, key)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    traverse(child, f"{pointer}/{index}", metadata, parent_key)

        for sidecar in sorted(self.root.rglob("*.http.json")):
            metadata = read(sidecar)
            if metadata.get("success"):
                traverse(read(self.root / metadata["response_body"]), "", metadata)
        result = []
        for oid, entries in sorted(references.items()):
            unique = {json.dumps(entry, sort_keys=True): entry for entry in entries}
            result.append({"sha": oid, "references": [unique[key] for key in sorted(unique)]})
        dump(self.root / "referenced-commits.json", result)
        self.dataset("referenced-commits", output="referenced-commits.json", count=len(result), complete=True,
                     validation="Lowercase unique 40-hex commit-semantic OIDs with endpoint/raw JSON pointer provenance; existence/retrievability checked separately in supplemental Git preservation")
        self.log(f"Inventoried {len(result)} distinct metadata-referenced commit OIDs")

    def attachments(self):
        sources = {}
        all_links = {}

        def collect(value, origin):
            if isinstance(value, str):
                for matched in URL_RE.findall(value):
                    url = html.unescape(matched).rstrip(".,;:!?)])}")
                    parsed = urlsplit(url)
                    all_links.setdefault(url, set()).add(origin)
                    if parsed.hostname in ATTACHMENT_HOSTS or (
                        parsed.hostname == "github.com" and (
                            parsed.path.startswith("/user-attachments/") or
                            parsed.path.startswith(f"/{self.repository}/assets/") or
                            parsed.path.startswith(f"/{self.repository}/files/"))
                    ):
                        sources.setdefault(url, set()).add(origin)
            elif isinstance(value, dict):
                for child in value.values():
                    collect(child, origin)
            elif isinstance(value, list):
                for child in value:
                    collect(child, origin)

        for name in ["issues", "pull-requests", "issue-comments", "review-comments", "commit-comments", "releases"]:
            for item in read(self.root / f"{name}.json", []):
                collect(item, f"{name}.json#{item.get('number', item.get('id'))}")
        for filename in sorted((self.root / "pull-requests").glob("*/reviews.json")):
            collect(read(filename), str(filename.relative_to(self.root)))
        for filename in sorted((self.root / "graphql/discussions").rglob("*.json")):
            if not filename.name.endswith((".http.json", ".query.json")):
                collect(read(filename), str(filename.relative_to(self.root)))
        collect(read(self.root / "graphql/discussions.json", []), "graphql/discussions.json")
        for item in read(self.root / "graphql/content-edits.json", []):
            collect(item, f"graphql/content-edits.json#{item['id']}")
        # Read original documentation directly from the imported baseline: concurrent
        # local documentation edits cannot contaminate the upstream inventory.
        result = subprocess.run(["git", "ls-tree", "-r", "--name-only", self.args.baseline], capture_output=True, text=True)
        if result.returncode == 0:
            for filename in result.stdout.splitlines():
                if filename.lower().endswith((".md", ".html", ".yml", ".yaml")):
                    content = subprocess.run(["git", "show", f"{self.args.baseline}:{filename}"], capture_output=True).stdout.decode("utf-8", "replace")
                    collect(content, f"git:{self.args.baseline}:{filename}")
        release_assets = []
        for release in read(self.root / "releases.json", []):
            for asset in release.get("assets", []):
                url = asset["browser_download_url"]
                sources.setdefault(url, set()).add(f"releases.json#{release['id']}/assets/{asset['id']}")
                release_assets.append(asset)
        budget = self.args.attachment_total_mib * 1024 * 1024
        maximum = self.args.attachment_max_mib * 1024 * 1024
        stored_bytes = sum(path.stat().st_size for path in (self.root / "attachments/data").glob("*"))

        class SafeRedirect(HTTPRedirectHandler):
            def redirect_request(inner_self, request, fp, code, message, headers, newurl):
                host = urlsplit(newurl).hostname or ""
                allowed = host == "github.com" or host.endswith(".githubusercontent.com") or (
                    host.endswith(".s3.amazonaws.com") and host.startswith("github-production-"))
                if urlsplit(newurl).scheme != "https" or not allowed:
                    raise ValueError(f"Refused attachment redirect to non-allowlisted host: {host}")
                return super().redirect_request(request, fp, code, message, headers, newurl)

        opener = build_opener(SafeRedirect())
        inventory = []
        for index, (url, origins) in enumerate(sorted(sources.items()), 1):
            identifier = hashlib.sha256(url.encode("utf-8")).hexdigest()
            observation_path = self.root / f"attachments/observations/{identifier}.json"
            retry_paths = sorted(observation_path.parent.glob(f"{identifier}.retry-*.json"))
            cached_path = retry_paths[-1] if retry_paths else observation_path
            cached = read(cached_path)
            retry_size_skip = bool(cached and self.args.retry_skipped_attachments and cached.get("status") == "skipped" and
                                   "byte budget" in cached.get("error", cached.get("reason", "")))
            if cached:
                if retry_size_skip:
                    observation_path = observation_path.with_name(f"{identifier}.retry-{len(retry_paths)+1:04}.json")
                else:
                    entry = {**cached, "referenced_by": sorted(origins)}
                    inventory.append(entry)
                    continue
            parsed = urlsplit(url)
            entry = {"url": url, "referenced_by": sorted(origins), "observed_at": utc_now(),
                     "maximum_per_attachment_bytes_at_attempt": maximum, "maximum_total_bytes_at_attempt": budget}
            if retry_size_skip:
                entry["supersedes_size_skip_observation"] = str(cached_path.relative_to(self.root))
                entry["retry_reason"] = "Explicit --retry-skipped-attachments with revised byte limits; original observation preserved"
            initial_host = parsed.hostname or ""
            safe = initial_host == "github.com" or initial_host in ATTACHMENT_HOSTS
            if parsed.scheme != "https" or not safe:
                entry.update(status="skipped", reason="Only HTTPS allowlisted public attachment hosts are fetched")
            elif stored_bytes >= budget:
                entry.update(status="skipped", reason="Total attachment archive byte budget reached")
            else:
                temporary = self.root / f"attachments/data/{identifier}.download"
                temporary.parent.mkdir(parents=True, exist_ok=True)
                try:
                    request = Request(url, headers={"User-Agent": "nativeCmpkit-public-metadata-archive/1.0"})
                    with opener.open(request, timeout=60) as response:
                        final = urlsplit(response.geturl())
                        if final.hostname == "github.com" and final.path.startswith(("/login", "/session")):
                            raise ValueError("Public attachment URL redirected to an authentication page")
                        content_length = response.headers.get("Content-Length")
                        content_type = response.headers.get("Content-Type", "application/octet-stream")
                        if content_length and int(content_length) > min(maximum, budget - stored_bytes):
                            raise ValueError(f"Attachment size {content_length} exceeds per-file/remaining archive byte budget")
                        size = 0
                        digest = hashlib.sha256()
                        with temporary.open("wb") as stream:
                            while True:
                                block = response.read(128 * 1024)
                                if not block:
                                    break
                                size += len(block)
                                if size > min(maximum, budget - stored_bytes):
                                    raise ValueError("Streaming download exceeded per-file/remaining archive byte budget")
                                stream.write(block)
                                digest.update(block)
                        if content_length and size != int(content_length):
                            raise IOError(f"Incomplete attachment: received {size}, expected Content-Length {content_length}")
                        # Arbitrary content is saved as .bin and is never interpreted.
                        destination = temporary.with_suffix(".bin")
                        temporary.replace(destination)
                        stored_bytes += size
                        entry.update(status="archived", http_status=response.status, content_type=content_type,
                                     size=size, sha256=digest.hexdigest(), local_path=str(destination.relative_to(self.root)),
                                     final_url_without_query=urlunsplit((final.scheme, final.netloc, final.path, "", "")))
                except Exception as error:
                    temporary.unlink(missing_ok=True)
                    entry.update(status="unavailable" if not isinstance(error, ValueError) else "skipped", error=str(error))
            dump(observation_path, entry)
            inventory.append(entry)
            if index % 20 == 0:
                self.log(f"Public attachment inventory: {index}/{len(sources)} ({stored_bytes//(1024*1024)} MiB archived)")
        dump(self.root / "attachments/inventory.json", inventory)
        dump(self.root / "links/inventory.json", [{"url": url, "referenced_by": sorted(origins)}
                                                   for url, origins in sorted(all_links.items())])
        dump(self.root / "attachments/policy.json", {
            "public_anonymous_requests_only": True, "execute_or_extract_downloads": False,
            "maximum_per_attachment_bytes": maximum, "maximum_total_bytes": budget,
            "urls": len(inventory), "archived": sum(x["status"] == "archived" for x in inventory),
            "archived_bytes": stored_bytes, "release_asset_count": len(release_assets),
            "notes": "Original URLs remain in raw bodies. Local paths are SHA256(URL), never upstream-supplied filenames. CDN redirect query credentials are not recorded. External non-attachment links are retained in bodies, not recursively crawled.",
        })

    def finalize(self):
        self.references()
        self.single("rate-limit-end", "rate_limit", absolute=True)
        issues = read(self.root / "issues.json", [])
        pulls = read(self.root / "pull-requests.json", [])
        actual_issues = [item for item in issues if "pull_request" not in item]
        requests = []
        for path in sorted(self.root.rglob("*.http.json")):
            requests.append(read(path))
        failures = []
        for request in requests:
            if request.get("success"):
                continue
            failure = dict(request)
            if (re.fullmatch(r"graphql/pull-requests/batch-\d+\.json", request["response_body"]) and
                "includeClosed" in str(request.get("graphql_errors", request.get("error", ""))) and
                self.progress.get("graphql/pull-requests", {}).get("complete")):
                failure["disposition"] = "superseded-exporter-schema-probe"
                failure["resolution"] = "Unsupported includeClosed argument removed; corrected batch-v2 query successfully exported all PRs"
            elif (request["response_body"] == "rest/watchers/page-0001.json" and
                  self.progress.get("graphql/watchers", {}).get("complete")):
                failure["disposition"] = "endpoint-denied-data-recovered-via-graphql"
                failure["resolution"] = "Full watcher user nodes recovered through graphql/watchers.json"
            else:
                failure["disposition"] = "unresolved-endpoint-limitation"
            failures.append(failure)
        pull_coverage = [read(path) for path in sorted((self.root / "pull-requests").glob("*/coverage.json"))]
        reviews = sum(len(read(path)) for path in (self.root / "pull-requests").glob("*/reviews.json"))
        timeline_count = sum(len(read(path)) for path in (self.root / "issues").glob("*/timeline.json"))
        inventory = read(self.root / "graphql/repository-inventory.json", {}).get("data", {}).get("repository", {})
        totals = {key: value.get("totalCount") for key, value in inventory.items() if isinstance(value, dict) and "totalCount" in value}
        consistency = {
            "issue_count_matches_graphql": totals.get("issues") == len(actual_issues),
            "pr_count_matches_graphql": totals.get("pullRequests") == len(pulls),
            "issue_pr_union_matches": {item["number"] for item in issues if "pull_request" in item} == {item["number"] for item in pulls},
            "issue_numbers_unique": len({item["number"] for item in issues}) == len(issues),
            "pull_numbers_unique": len({item["number"] for item in pulls}) == len(pulls),
            "release_count_matches_graphql": totals.get("releases") == len(read(self.root / "releases.json", [])),
            "all_pr_details_present": len(list((self.root / "pull-requests").glob("*/detail.json"))) == len(pulls),
            "all_pr_file_counts_match_detail": len(pull_coverage) == len(pulls) and all(item["files_count_matches_detail"] for item in pull_coverage),
            "all_pr_commit_counts_match_detail": len(pull_coverage) == len(pulls) and all(item["commits_count_matches_detail"] for item in pull_coverage),
            "all_issue_and_pr_timelines_present": len(list((self.root / "issues").glob("*/timeline.json"))) == len(issues),
        }
        required_datasets = {"repository", "issues", "pull-requests", "issue-comments", "review-comments",
                             "commit-comments", "issue-events", "releases", "labels", "milestones", "branches", "tags",
                             "contributors", "graphql/pull-requests", "graphql/content-edits", "graphql/history-events",
                             "graphql/discussions", "graphql/discussion-categories"}
        consistency["all_core_datasets_complete"] = required_datasets.issubset(self.progress) and all(
            self.progress[name].get("complete") for name in required_datasets)
        consistency["all_core_nested_datasets_complete"] = all(value.get("complete") for name, value in self.progress.items()
            if name.startswith(("issues/", "pull-requests/", "reactions/", "releases/", "graphql/pull-requests/",
                                "graphql/content-edits/", "graphql/discussions/")))
        consistency["label_count_matches_graphql"] = totals.get("labels") == len(read(self.root / "labels.json", []))
        consistency["milestone_count_matches_graphql"] = totals.get("milestones") == len(read(self.root / "milestones.json", []))
        consistency["discussion_count_matches_graphql"] = totals.get("discussions") == len(read(self.root / "graphql/discussions.json", []))
        issue_comment_counts = {}
        for comment in read(self.root / "issue-comments.json", []):
            number = int(comment["issue_url"].rsplit("/", 1)[1])
            issue_comment_counts[number] = issue_comment_counts.get(number, 0) + 1
        mismatches = [{"number": issue["number"], "expected": issue["comments"], "archived": issue_comment_counts.get(issue["number"], 0)}
                      for issue in issues if issue.get("comments") != issue_comment_counts.get(issue["number"], 0)]
        consistency["all_issue_comment_counts_match"] = not mismatches
        inline_counts = {}
        inline_comments = read(self.root / "review-comments.json", [])
        for comment in inline_comments:
            number = int(comment["pull_request_url"].rsplit("/", 1)[1])
            inline_counts[number] = inline_counts.get(number, 0) + 1
        inline_mismatches = []
        for pr in pulls:
            detail = read(self.root / f"pull-requests/{pr['number']}/detail.json", {})
            expected = detail.get("review_comments")
            actual = inline_counts.get(pr["number"], 0)
            if expected != actual:
                inline_mismatches.append({"number": pr["number"], "expected": expected, "archived": actual})
        consistency["all_inline_comment_counts_match_pr_details"] = not inline_mismatches
        thread_comment_ids = set()
        for pr in read(self.root / "graphql/pull-requests.json", []):
            threads = pr["reviewThreads"]["nodes"]
            if pr["reviewThreads"]["pageInfo"]["hasNextPage"]:
                threads = read(self.root / f"graphql/pull-requests/{pr['number']}/review-threads.json", [])
            for index, thread in enumerate(threads, 1):
                comments = thread["comments"]["nodes"]
                if thread["comments"]["pageInfo"]["hasNextPage"]:
                    comments = read(self.root / f"graphql/pull-requests/{pr['number']}/thread-{index}/comments.json", [])
                thread_comment_ids.update(comment["databaseId"] for comment in comments)
        consistency["inline_comment_ids_match_graphql_threads"] = thread_comment_ids == {comment["id"] for comment in inline_comments}
        edit_histories = read(self.root / "graphql/content-edits.json", [])
        pr_edits = {item["id"]: item for item in edit_histories if item.get("__typename") == "PullRequest"}
        review_mismatches = []
        for pr in pulls:
            expected = pr_edits.get(pr["node_id"], {}).get("reviews", {}).get("totalCount")
            actual = len(read(self.root / f"pull-requests/{pr['number']}/reviews.json", []))
            if expected != actual:
                review_mismatches.append({"number": pr["number"], "expected": expected, "archived": actual})
        consistency["all_review_counts_match_graphql"] = not review_mismatches
        reaction_mismatches = []
        for source, location in [(issues, lambda item: f"issues/{item['number']}/reactions.json"),
                                 (read(self.root / "releases.json", []), lambda item: f"releases/{item['id']}/reactions.json")]:
            for item in source:
                expected = item.get("reactions", {}).get("total_count", 0)
                if expected and len(read(self.root / location(item), [])) != expected:
                    reaction_mismatches.append({"path": location(item), "expected": expected,
                                                "archived": len(read(self.root / location(item), []))})
        for category in ["issue-comments", "review-comments", "commit-comments"]:
            for item in read(self.root / f"{category}.json", []):
                expected = item.get("reactions", {}).get("total_count", 0)
                path = f"reactions/{category}/{item['id']}.json"
                if expected and len(read(self.root / path, [])) != expected:
                    reaction_mismatches.append({"path": path, "expected": expected, "archived": len(read(self.root / path, []))})
        consistency["all_positive_reaction_actor_counts_match"] = not reaction_mismatches
        dump(self.root / "validation.json", {"observed_at": utc_now(), "checks": consistency, "issue_comment_count_mismatches": mismatches,
             "inline_comment_count_mismatches": inline_mismatches, "review_count_mismatches": review_mismatches,
             "reaction_count_mismatches": reaction_mismatches,
             "pull_file_or_commit_mismatches": [item for item in pull_coverage if not item["files_count_matches_detail"] or not item["commits_count_matches_detail"]]})
        dump(self.root / "api-limitations.json", failures)
        manifest = {
            **self.observation, "finalized_at": utc_now(), "response_count": len(requests),
            "unsuccessful_response_count": len(failures), "graphql_inventory_totals": totals,
            "superseded_schema_probe_count": sum(item["disposition"] == "superseded-exporter-schema-probe" for item in failures),
            "unresolved_endpoint_limitations": sum(item["disposition"] == "unresolved-endpoint-limitation" for item in failures),
            "recovered_endpoint_denials": sum(item["disposition"] == "endpoint-denied-data-recovered-via-graphql" for item in failures),
            "query_files_without_completed_response": [str(path.relative_to(self.root)) for path in sorted(self.root.rglob("*.query.json"))
                if not path.with_name(path.name.replace(".query.json", ".http.json")).exists()],
            "inconsistent_public_connections": [{"dataset": name, **value} for name, value in self.progress.items()
                if value.get("count_matches_independent_repository_query") is False],
            "community_observations": {
                "fork_records_rest": len(read(self.root / "forks.json", [])),
                "fork_count_repository_graphql": totals.get("forks"),
                "watcher_records_graphql": len(read(self.root / "graphql/watchers.json", [])),
                "stargazer_count_repository_graphql": totals.get("stargazers"),
                "note": "REST fork records and repository counters need not agree; all observed records are preserved. Star-edge count inconsistency is explicit, not treated as complete.",
            },
            "counts": {"issues": len(actual_issues), "pull_requests": len(pulls),
                       "open_issues": sum(item["state"] == "open" for item in actual_issues),
                       "open_pull_requests": sum(item["state"] == "open" for item in pulls),
                       "issue_comments": len(read(self.root / "issue-comments.json", [])),
                       "review_comments": len(read(self.root / "review-comments.json", [])),
                       "commit_comments": len(read(self.root / "commit-comments.json", [])),
                       "reviews": reviews, "timeline_items": timeline_count,
                       "content_edit_objects": len(edit_histories),
                       "content_edits": sum(item["userContentEdits"]["totalCount"] for item in edit_histories),
                       "history_enrichment_events": len(read(self.root / "graphql/history-events.json", [])),
                       "referenced_commits": len(read(self.root / "referenced-commits.json", [])),
                       "releases": len(read(self.root / "releases.json", [])),
                       "branches": len(read(self.root / "branches.json", [])),
                       "tags": len(read(self.root / "tags.json", [])),
                       "discussions": len(read(self.root / "graphql/discussions.json", []))},
            "validation": consistency,
            "content_edit_visibility": {
                "objects_with_public_edit_histories": sum(item["userContentEdits"]["totalCount"] > 0 for item in edit_histories),
                "objects_with_creation_edit_exposed": sum(item["includesCreatedEdit"] for item in edit_histories),
                "null_diffs_in_initial_pages": sum(edit["diff"] is None for item in edit_histories for edit in item["userContentEdits"]["nodes"]),
                "deleted_edit_tombstones_in_initial_pages": sum(edit["deletedAt"] is not None for item in edit_histories for edit in item["userContentEdits"]["nodes"]),
                "interpretation": "Null/deleted diffs are preserved as returned, never reconstructed or silently treated as available content",
            },
            "limitations": [
                "Deleted, redacted, spam-hidden and inaccessible/private content cannot be reconstructed by these public APIs. Publicly accessible body edit diffs/editor identities are preserved under graphql/content-edits; deleted edit diffs may be null.",
                "Original IDs, authors, timestamps and links are retained as archive data; GitHub issue recreation cannot impersonate authors or retain original database IDs/timestamps.",
                "REST endpoint-specific failures and GraphQL errors are preserved in api-limitations.json; no absent/denied endpoint is claimed complete.",
                "REST issue timeline is the public timeline representation; inaccessible cross-referenced sources, private project context, redacted edit revisions and internal GitHub moderation events are not available.",
                "Public activity events API retains only its limited recent window (up to 300 events/90 days), not the full repository event history.",
                "Historical Actions logs/artifacts, secret settings, webhooks, private security advisories, audit logs, collaborators' private data and unpublished/draft content are outside this public archive. Source workflows and public deployment/check metadata are preserved separately.",
                "PR file/commit REST endpoint limits (3000 files/250 commits) are independently checked against PR detail counts; omitted binary diff content resides in the preserved Git objects where reachable.",
                "Archive is observed over an interval. Source may change during export; list counts and cross-endpoint consistency checks detect some, not all, concurrent changes.",
                "Public attachments are anonymous HTTPS downloads with byte limits. Unavailable/skipped assets and original URLs remain in attachments/inventory.json. Third-party external websites are not recursively copied.",
                "Release source ZIP/tarball URLs are retained but not redundantly downloaded because tagged source and Git history are preserved independently. Uploaded release asset inventory is explicit.",
            ],
            "integrity": "SHA256SUMS covers every archive file except itself; response sidecars additionally hash verbatim API response bodies",
            "exporter": {"path": "scripts/migration/archive_upstream.py", "sha256": sha256(Path(__file__))},
        }
        dump(self.root / "manifest.json", manifest)
        temporary_files = [str(path.relative_to(self.root)) for path in self.root.rglob("*")
                           if path.is_file() and path.name.endswith((".tmp", ".download"))]
        if temporary_files:
            raise RuntimeError(f"Cannot finalize an archive with unfinished temporary files: {temporary_files}")
        sums = []
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS" and not path.name.endswith(".tmp"):
                sums.append(f"{sha256(path)}  {path.relative_to(self.root)}")
        (self.root / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
        self.log(f"Finalized: {len(sums)} files; {manifest['counts']}; {len(failures)} explicit API limitations")
        if self.args.verify:
            verify_archive(self.root)


def verify_archive(root: Path):
    entries = (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    for entry in entries:
        expected, name = entry.split("  ", 1)
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Manifest path escaped archive root")
        if sha256(path) != expected:
            raise ValueError(f"SHA256 mismatch: {name}")
    listed = {entry.split("  ", 1)[1] for entry in entries}
    actual = {str(path.relative_to(root)) for path in root.rglob("*")
              if path.is_file() and path.name != "SHA256SUMS"}
    if listed != actual:
        raise ValueError(f"Unlisted/missing archive files: {sorted(listed.symmetric_difference(actual))}")
    for sidecar in root.rglob("*.http.json"):
        request = read(sidecar)
        body = (root / request["response_body"]).resolve()
        if not body.is_relative_to(root.resolve()):
            raise ValueError("Raw response path escaped archive root")
        if sha256(body) != request["response_sha256"]:
            raise ValueError(f"Raw API body hash mismatch: {request['response_body']}")
    validation = read(root / "validation.json", {})
    failed = [name for name, passed in validation.get("checks", {}).items() if not passed]
    if failed:
        raise ValueError(f"Archive consistency checks failed: {failed}")
    print(f"Verified {len(entries)} SHA256SUMS entries, raw response hashes, and {len(validation.get('checks', {}))} consistency checks", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repository", default="MohamedRejeb/Calf")
    parser.add_argument("--output", default="docs/migration/upstream-metadata")
    parser.add_argument("--baseline", default=BASELINE)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--attachment-max-mib", type=int, default=32)
    parser.add_argument("--attachment-total-mib", type=int, default=150)
    parser.add_argument("--retry-skipped-attachments", action="store_true", help="Explicitly retry only earlier byte-budget skips; preserve each original observation")
    parser.add_argument("--phase", choices=["initial", "details", "graphql", "content_edits", "history_enrichment", "references", "supplemental", "community", "attachments", "finalize", "verify", "all"], default="all")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("--repository must be OWNER/REPOSITORY")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.baseline):
        parser.error("--baseline must be a complete 40-hex Git commit OID")
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")
    if args.phase == "verify":
        verify_archive(Path(args.output).resolve())
        return
    archive = Archive(args)
    phases = ["initial", "graphql", "details", "content_edits", "history_enrichment", "supplemental", "community", "attachments", "finalize"] if args.phase == "all" else [args.phase]
    for phase in phases:
        archive.log(f"Starting {phase}")
        getattr(archive, phase)()
        archive.log(f"Completed {phase}")


if __name__ == "__main__":
    main()
