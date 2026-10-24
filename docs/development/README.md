# nativeCmpkit development after the audit

The owner authorized fixes, library-level testing, efficient multi-platform CI and
the first **verified** preview on 2026-10-24. This is the live development record;
the [audit delivery report](../audit/final-report.md) remains a historical baseline.

## First actions

- [Pages resolution](evidence/pages-unpublishing/verification.json): owner action,
  authenticated null Pages status and public 404 responses verified; issue #171
  [closed with readback](evidence/pages-unpublishing-closure.json). Configuration
  and deployment history remain; Pages redeployment is not authorized.
- [Current upstream reconciliation](upstream-sync-20261024T183300Z/README.md):
  16 open issues, one separately recorded open PR; every issue already mapped.
  Fresh attributed descriptions, labels, comments and timelines are preserved.
  The apply receipt, not the existence of drafts, establishes posting/readback.

## Implementation and verification policy

Area owners maintain `resolutions/*.json` as JSON arrays, one record for each owned
baseline finding. Each record has `id`, `status` (`implemented`, `verified`,
`unresolved`, or `not-applicable`), `changes`, `affected_paths`, `tests`, `remaining`
and `compatibility`. Test entries name commands, results and committed evidence;
unavailable tests are explicitly unavailable, not assumed successful.

The lead reviews these against original `required_tests`, verifies the immutable
source revision, and decides issue closure. A passing characterization test might
prove the original bug exists, not that it is fixed. New test source without a run,
cached reports, platform stubs, `NO-SOURCE`, compilation and sample execution do
not count as native library functionality tests.

All 164 findings and imported topics remain in the roadmap until accurately
dispositioned. Feature requests for currently unimplemented modules must not be
silently declared fixed or expanded into unrelated features to inflate closure
counts. Public API and ownership changes need scoped design decisions and migration
guidance. Existing historical metadata and findings remain unchanged.

## Preview publication gate

Conditional owner authorization is not evidence that the gate passed. Before any
release/package publication, verify applicable issue fixes, runtime/native library
tests, stable cross-platform CI, packaged consumer fixtures, API compatibility,
native payload completeness/provenance, resolved dependency safety and artifact
licensing. Record exact versions, source SHA, task/test counts, hashes and limits.
No preview has been published by this phase at the time this document was started.

GitHub Packages can use a purpose-scoped Actions token and authenticated Maven
consumer configuration; unavailable Central credentials must not be represented
as a successful Central publication. Publication workflow templates stay outside
active workflows until all required gates pass. Documentation hosting stays off.
