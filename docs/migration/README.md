# Migration and independent recovery

**Destination:** [Apdelrahman1911/nativeCmpkit](https://github.com/Apdelrahman1911/nativeCmpkit)
— an independent GitHub repository, not a fork relationship.
**Source:** MohamedRejeb/Calf. **Baseline:**
`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. Migration began 2026-10-24 UTC.

## Preservation model

Git preserves commit bytes (author/committer identities, timestamps, parents,
messages and trees), not GitHub account metadata. All **46 advertised branches**
and **23 tags** were pushed with their original object IDs. New work advances
`main` by additive commits; the other **68 heads/tags remain unchanged**. The
baseline remains an ancestor of main. The advertised Git snapshot contains
**1,009 commits**, including 931 reachable from original main, plus **410 advertised
PR refs** in the self-contained Git bundle. PR refs are archival refs, not recreated
GitHub pull requests. No source branch/tag was deleted, rebased or force-pushed.

| Material | Independent copy | Verification |
|---|---|---|
| Advertised Git refs and complete reachable objects | [upstream.bundle](git/upstream.bundle), [ref manifest](git/upstream-refs.txt) | SHA256, bundle restore, exact ref IDs, object integrity |
| Additional publicly referenced commits | [referenced-commits.bundle](git/referenced-commits.bundle), [refs](git/referenced-commit-refs.txt) | [Final recovery receipt](git/referenced-commits-verification.json), dataset hash, offline commit lookup |
| GitHub issues/PRs/comments/reviews/releases/history | [Raw metadata archive](upstream-metadata/README.md) | 9,257 file hashes, raw-response hashes and consistency tests |
| Original changed docs/workflows | [Legacy tree](legacy/), immutable baseline Git tree | Original bytes and Git history; workflows are inert data |
| Migration identity/modifications | [identity.json](identity.json), [modification record](MODIFICATIONS.md), [ADR](../decisions/0001-independent-identity.md) | Coordinate/resource/configuration checks and additive commits |
| Original open-item decisions | [17 dispositions](upstream-actionable-decisions.json) | Baseline source + preserved authors, IDs, dates and references |
| New actionable work | [Issue plan](../audit/issue-plan.json), [issue map](issue-map.json), [roadmap](../roadmap/README.md) | Stable deduplicated markers; [read-only remote verification](issues-verification.json) |
| Operational Pages follow-up | [Issue #171](https://github.com/Apdelrahman1911/nativeCmpkit/issues/171), [creation/readback receipt](pages-followup-issue.json) | Separate from baseline findings and managed audit/history issues; unpublishing remains unverified |

The metadata inventory exposed **1,354 unique commit-semantic OIDs**, including
old force-push heads and deployment commits not advertised as current branches.
The first pass fetched 68 missing objects; its
[receipt](git/referenced-commits-first-pass.json) is retained. The final receipt
records successful recovery of all **303 additional missing commits**; together
with the first pass, **371 supplemental archival refs** are preserved. Offline
restoration verified all **1,354 metadata-referenced commits**. The receipt remains
authoritative for completion time and supplemental bundle digest. Never replace
retrieval failures with guessed SHAs
or assume an advertised-ref clone includes every historical force-push commit.

## GitHub metadata, provenance and unavoidable gaps

Preserved: **142 issues, 408 PRs, 448 conversation comments, 75 reviews, 13 inline
comments, 3,028 timeline entries, 318 public edit records, 23 releases and 306
deployment records/status histories**. Releases had zero uploaded assets.
**62 of 63 discovered attachments** were archived (108,519,393 bytes); one URL
returned 404. The archive contains 2,963 verbatim raw responses, convenient
derived arrays, response/file digests, request provenance and validation results.

Read [metadata coverage](metadata-coverage.md) before making completeness claims.
This was a paginated observation interval, not an atomic server snapshot.
ProjectsV2 was denied by token scope; wiki Git refs and some settings were
unavailable. Star edges returned zero despite a positive repository counter.
Fork representations disagree (REST 94, GraphQL 93). Twenty-one edit diffs are
null for an **unknown** reason. Discussions were disabled with zero accessible
records; deleted/private history cannot be reconstructed. Expired workflow logs,
arbitrary external websites/videos and avatars were not recursively mirrored.

GitHub does not let an ordinary repository migration faithfully transplant issue
numbers, authors, creation dates, review identities, PR relationships or reactions.
Those originals remain in the archive, not impersonated through the destination
account. Actionable issues are **new** issues with original metadata in their
bodies, exact source evidence and archive references. Six standalone historical
topics supplement 164 audit findings; implemented/covered requests are not duplicated.
Historical releases remain JSON/Git history, **not newly published releases**.

The destination contains **170 verified managed issues: 167 open and three
closed** at the delivery check. All 164 findings and six independent historical
topics have unique markers, exact body hashes, priorities and links. The three
closures are BUILD-008, BUILD-009 and BUILD-011, resolved by the migration; no
functional bug was silently marked fixed. Remote numbers, new author/timestamps
and original references are retained in `issue-map.json`. The verifier also checks
labels and lifecycle against that receipt without mutating the issues.

One separate **Medium operational issue**, [#171](https://github.com/Apdelrahman1911/nativeCmpkit/issues/171),
tracks the Pages cleanup described below and is assigned to the owner. This brings
the observed destination total to **171 issues: 168 open, three closed**. Its unique
operational marker is outside the audit synchronizer's namespace; the managed
verifier correctly reports **one unmanaged issue left untouched**. It is not a
165th baseline finding or a reason to reopen BUILD-008. The
[creation/readback receipt](pages-followup-issue.json) preserves its new author,
IDs, timestamps and exact body separately.

## Offline restoration, without the original repository

Run from an existing nativeCmpkit checkout. These commands create a **new empty
recovery directory**; never substitute your working repository for that path.

```sh
sha256sum -c docs/migration/git/upstream.bundle.sha256
sha256sum -c docs/migration/git/referenced-commits.bundle.sha256
(cd docs/migration/upstream-metadata && sha256sum -c SHA256SUMS)

git init --bare /tmp/nativecmpkit-upstream-recovery.git
git --git-dir=/tmp/nativecmpkit-upstream-recovery.git fetch \
  "$PWD/docs/migration/git/upstream.bundle" 'refs/*:refs/*'
git --git-dir=/tmp/nativecmpkit-upstream-recovery.git fetch \
  "$PWD/docs/migration/git/referenced-commits.bundle" 'refs/*:refs/*'
git --git-dir=/tmp/nativecmpkit-upstream-recovery.git fsck --full --no-dangling
git --git-dir=/tmp/nativecmpkit-upstream-recovery.git show \
  af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6:README.md
```

The recovery verifier creates its own disposable bare repository, restores both
bundles, compares all preserved refs and checks every metadata-referenced commit
without network access. The destination's new commits are already in its normal
Git history; the bundles intentionally preserve upstream snapshots separately.
The archive does not vendor Maven/Google/Rust/npm registries or Apple/Android SDKs.
Those normal build prerequisites remain external; **no build or source recovery
requires the Calf repository to remain available**. Upstream URLs are provenance.

## Identity and compatibility

- Project/repository: **nativeCmpkit**.
- Group: `io.github.apdelrahman1911.nativecmpkit`; 21 `nativecmpkit-*` prospective
  artifacts; development version `0.1.0-SNAPSHOT`, unpublished.
- Retained intentionally: `com.mohamedrejeb.calf.*`, `calf-*` Gradle paths, opt-in
  annotation names, Android namespaces, generated Cupertino resource package,
  Rust crate/JNI symbols/native filenames and sample Swift framework names.
- Cargo package version/metadata is independent and `publish = false`; crate
  names remain for ABI compatibility. Sample app IDs/display names were changed
  and the upstream Apple signing-team identity removed.
- Apache LICENSE is unchanged; original copyrights and derived-code headers
  remain. Added NOTICE, third-party license texts and provenance. See
  [THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md). Font notice distribution
  inside future artifacts still needs validation (NAV-009).
- Package namespace retention reduces gratuitous breakage but is **not an ABI
  compatibility certification**. Never load old/new coordinates together when
  they contain the same classes. Maven namespace ownership/signing is not provisioned.

## Automation and verification safety

The migration workspace's `upstream` remote has a disabled push URL. A fresh clone
with only `origin` does **not** need to add an upstream remote: the read-only
verifier accepts either absence or the explicit `DISABLED_READ_ONLY_UPSTREAM`
interlock on **every** configured push URL, and still rejects an unguarded
`upstream` or an empty returned URL list. Its receipt also
hashes the verifier script, so a dirty-worktree observation is not mistaken for an
unchanged tool revision. Only `origin` points to the new repository here.
Active inherited publishing/Pages/Netlify workflows were removed;
their originals remain archived. Current action versions are pinned by commit.
Only supervised read-only verification runs are enabled temporarily, with report
artifacts rather than release packages. Repository Actions are disabled afterward.

**Exception requiring owner follow-up:** GitHub recorded one unintended legacy
Pages deployment from the imported `gh-pages` ref. Legacy publishing has been
switched off, but REST deletion was rejected and existing deployment unpublishing
is not verified. See the [incident and containment record](pages-incident.md).
The owner's previously requested **Unpublish site** action is tracked in
[issue #171](https://github.com/Apdelrahman1911/nativeCmpkit/issues/171); no completed
action is assumed from the creation of that issue.
This is not a zero-deployment migration, and Git/archive integrity checks do not
certify that the site has been unpublished.
Publishing interlocks supplement, but never replace, explicit owner authorization.

```sh
# Local structural/archive verification: no remote mutation.
python3 scripts/migration/verify_migration.py
python3 scripts/audit/validate_audit.py

# Read-only destination checks, including final disabled-Actions policy.
python3 scripts/migration/verify_migration.py --remote \
  --output /tmp/nativecmpkit-migration-verification.json

# Safe default: generate local drafts only.
python3 scripts/migration/sync_github_issues.py
```

`sync_github_issues.py --apply` is an explicit mutation of **only** the fixed
destination. It reconciles stable markers, preserves owner lifecycle/unmanaged
labels, refuses conflicting edits and records successful creates immediately.
After an uncertain request failure, inspect remote state; do not blindly repeat a
POST. Fixtures exercise idempotency without network access.

The final committed `verification.json` records its observed checkout/remote SHA
and time. A receipt cannot cryptographically certify the later commit that stores
it; subsequent verification must state that later SHA separately. Do not claim a
receipt “verifies itself.” See [testing](../testing/README.md) for actual build/test
outcomes and [the final report](../audit/final-report.md) for remaining limitations.

The delivered receipt was rerun from a clean, independent GitHub clone at
`c808c97fe555324ff92f75c3c55d0fc30114b7ea`, with only `origin` configured and no
Git object alternates. All 551 integrity/control checks, the audit and issue
validators, and 35/55 offline tooling fixtures passed. Its original
[logs and checksums](../testing/evidence/fresh-clone-c808c97f/manifest.json) are
preserved. No original Calf repository request or new Gradle test run was needed.
Pages unpublishing remained explicitly unverified. The evidence-storing commit
comes after the checked revision; subsequent read-only verification must state
its actual observed SHA separately.
