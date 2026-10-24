# Documentation, archive and migration verification

These are **tooling/integrity checks**, not Kotlin library tests. Their results
must remain separate from platform, unit, native and device coverage.

## Local documentation build

The audit installed an isolated Python virtual environment (outside the repository)
and ran:

```sh
python3 -m venv /tmp/nativecmpkit-docs-venv
# Reproduce the recorded package versions, or deliberately review an update.
/tmp/nativecmpkit-docs-venv/bin/pip install \
  -r docs/testing/evidence/documentation-toolchain.txt
/tmp/nativecmpkit-docs-venv/bin/mkdocs build --strict \
  --site-dir /tmp/nativecmpkit-site
```

**Observed result:** strict build succeeded; see
[`mkdocs-build.log`](evidence/mkdocs-build.log) and
[`documentation-toolchain.txt`](evidence/documentation-toolchain.txt).
This local documentation command did not deploy a site. A separate
[unintended legacy Pages event](../migration/pages-incident.md) occurred during
historical-ref import and must not be confused with this check. Versions are
recorded, but this freeze is not a complete
hash-verified, vendored documentation supply chain.

Archive/evidence/bundle/issue-draft trees are excluded from site generation and
search, not removed from Git. The site-link hook maps references to excluded
material and source outside `docs/` to the independent GitHub repository; regular
documentation links remain local. Its five offline fixtures check source links,
fragments, exclusions, directories and refusal to transform missing/outside paths.
An output-tree check confirmed no excluded archive/evidence directories were copied.

Version macros are **opt-in** in four reviewed usage guides. Audit prose, raw
GitHub bodies and archived workflows never become macro/template inputs. Four
historical icon screenshot links pointed to files absent from baseline Git; the
active guide now says so rather than rendering broken images or fabricated results.

## Reproducible evidence structure

```sh
python3 scripts/audit/source_inventory.py --check
python3 scripts/audit/validate_audit.py
python3 scripts/audit/render_knowledge_indexes.py
python3 -m unittest discover -s scripts/audit -p 'test_*.py' -v
python3 -m unittest discover -s scripts/migration -p 'test_*.py' -v
```

The inventory check reproduces immutable baseline bytes/classification. The
validator checks IDs, required fields, priorities/evidence classes, dependencies,
documentation links and all 424 exact finding locations, including the font's
binary hash instead of a fabricated line number. The generator retains every
finding/upstream action and promotes prerequisites into the phase they unblock.
None of these tools replaces compiler or semantic/native runtime verification.

Fixture logs are [`audit-tooling-tests.log`](evidence/audit-tooling-tests.log) and
[`migration-tooling-tests.log`](evidence/migration-tooling-tests.log). The exporter
suite checks pagination/provenance/error-not-empty semantics, cache integrity,
SHA coverage and commit-vs-blob classification. Issue-sync fixtures use fake APIs
only and prohibit real network access. JUnit fixtures separately ensure aggregate
and archived reports are not counted as fresh individual results, zero is not
misclassified as a passing suite, and DTD/entity declarations are rejected.

## Git and metadata recovery

```sh
python3 scripts/migration/verify_migration.py
python3 scripts/migration/verify_migration.py --remote \
  --output /tmp/nativecmpkit-verification.json
```

The local verifier validates unchanged Apache licensing/identity constraints,
all **9,257 metadata file hashes**, bundle checksums/ref manifests, Git object
integrity and completed referenced-commit retrieval. It restores the two bundles
into a newly empty temporary object database and checks all **1,354 referenced
commits**. The restored combined graph contains **1,380 commits**; the original
advertised snapshot alone contains 1,009. These are reachable-commit counts, not
issue counts or numbers of rewritten/new commits.

The supplemental archive contains **371 refs** from two successful recovery
passes (68 then 303 missing commits). Existing public Git objects already present
were not redundantly treated as newly fetched. `--remote` additionally reads
destination independence/ref state, disabled Actions, no new releases, approved
read-only workflow runs and the exact observed main SHA. It does not mutate GitHub
or upstream refs. The receipt describes its observation, not a later storing commit.

## Issue delivery and resumability

```sh
# Default is local-only rendering.
python3 scripts/migration/sync_github_issues.py
# Explicitly authorized mutation of this fixed destination only:
python3 scripts/migration/sync_github_issues.py --apply
# Read-only postcondition check:
python3 scripts/migration/verify_github_issues.py \
  --output /tmp/nativecmpkit-issues-verification.json
```

The [offline safety review](../migration/issue-sync-review.md) covers marker
identity, deterministic topic deduplication, original metadata, body size, user
edits, initial closed-state recovery and idempotency. It is not proof of delivery;
the actual map and remote verification receipt are required.

The first real invocation hit a client-only prerequisite: installed `gh` 2.45.0
does not implement `--slurp`. It stopped at a GET before mutations. A read-only
check confirmed zero issues. `github_json.py` now decodes normal `--paginate`
array/object streams; four fixtures and a live **read-only** smoke check passed.
The initial failure is retained in
[`github-issue-sync-initial-client-failure.log`](evidence/github-issue-sync-initial-client-failure.log).
No uncertain POST was blindly retried. See
[`issue-sync-client-compatibility.json`](evidence/issue-sync-client-compatibility.json)
for the corrected script hash and observation.

The corrected single-writer run completed all **170 issues**. A separate read-only
check verified every marker, number, URL, body hash, expected label, new author,
creation timestamp and recorded state: **167 open, three closed**, no duplicates
or unmanaged issues. See [`issue-map.json`](../migration/issue-map.json) and
[`issues-verification.json`](../migration/issues-verification.json). The closed
items are migration-resolved build findings, not unresolved functional defects.

Only one writer is supported. Do not run simultaneous syncs or edit managed bodies
mid-batch; there is no distributed lock/ETag transaction. Human issue lifecycle and
unmanaged labels survive future syncs; ambiguous markers/conflicting edits stop
the process for reconciliation. Original upstream authors are attributed, never
impersonated as the new issue author.

## Secret-marker scope

The advertised-history and staged-migration scans check selected recognizable
token/private-key patterns. The staged scan examined **9,511 text files**, skipped
65 binary/large files and found no selected matches; this is an observation of that
pre-upload snapshot, not an entropy scan, ZIP inspection or guarantee that secrets
never existed. Matched values would be redacted in receipts. Public attachments
were preserved as untrusted bytes and were not executed or extracted.

An additional scan included **both advertised history and all recovered
metadata-referenced commits**: 14,351 objects enumerated, **3,532 text blobs**
scanned, 166 binary blobs skipped, zero selected-marker matches. This supersedes
the earlier advertised-only scope without changing its historical receipt. See
[`complete-recovered-history-secret-marker-scan.json`](evidence/complete-recovered-history-secret-marker-scan.json).
To reproduce after restoring both bundles as documented in the migration guide:

```sh
python3 scripts/audit/scan_git_secret_markers.py --include-supplemental \
  --git-dir /tmp/nativecmpkit-upstream-recovery.git
```

The scanner is read-only and prints no matched values. This remains a narrow
recognizable-pattern check, not an entropy/credential-validity scan or a claim
that compressed attachments, inaccessible history or arbitrary secret formats
were exhaustively checked.
