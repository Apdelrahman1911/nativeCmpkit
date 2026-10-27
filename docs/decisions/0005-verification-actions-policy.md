# ADR 0005 — Authorized verification Actions; publishing remains gated

**Status:** accepted owner control-policy decision, 2026-10-26.

**Reaffirmation, 2026-10-27:** contained development without subagents continues;
verification authority and publishing/security restrictions below are unchanged.

## Context

The earlier containment checkpoint kept Actions disabled and required a six-action
allowlist and mandatory SHA pinning for a supervised verification window. That
prevented autonomous platform checks. The owner has now enabled **Allow all
actions and reusable workflows**, explicitly accepted no mandatory SHA pinning,
and authorized routine CI/development/dependency/consumer verification without
additional approval. The owner also explicitly prohibits using subagents.

## Decision

- Keep Actions enabled/all/no-required-pinning. Update executable policy checks,
  not just documentation. Existing SHA references may remain as voluntary
  reproducibility controls; named action versions are not rejected solely for
  being non-SHA references. Review newly used actions and executed source.
- Run single-agent. Necessary immutable development commits/pushes and reviewed
  verification dispatches are authorized. Preserve history and upstream
  read-only boundaries; do not dispatch inherited historical workflows.
- Separate **verification authority** from **publication readiness**. Use minimum
  read-only token permissions, no stored checkout credentials and test-evidence
  uploads only. No packages/releases/deployments/Pages while release/security
  gates remain unsatisfied. Local isolated Maven staging is verification only.
- Start with selected manual-dispatch library jobs on the existing registered
  workflow path. Bound concurrency and retain successful same-input evidence;
  no sample-app substitution or stale/cached-test success. A workflow file under
  `docs/` remains a design, not an executed workflow.

## Alternatives and consequences

Restoring the previous allowlist/pinning/disabled configuration would contradict
the explicit owner decision. Broad Actions availability does increase exposure
to future unreviewed workflow changes; counter it with source review, least
privilege, explicit trusted revisions and restricted verification operations, not
an unauthorized repository-setting reversal. Exact references alone never proved
bundled action/dependency safety. The migration verifier's lexical checks are
guardrails, **not a YAML interpreter or execution sandbox**.

No library API, package coordinate, imported author/history record or release
gate changes. Historical disabled-Actions receipts remain immutable. New checks
distinguish current control settings, workflow safety, in-progress CI and actual
runtime results. No source/native/package/security result is fabricated by
accepting the owner's configuration.

## Required verification

1. Authenticated readback of Actions/default-token settings, active workflows,
   Pages and releases; archive exact observations without credentials.
2. Offline regressions for owner-policy matching, explicit tag/SHA references,
   missing settings, unexpected write permissions and forbidden deployment paths.
3. Review each activated workflow and action; execute on immutable development
   revisions and inspect actual nonzero library test reports for each platform.
4. Continue native/consumer/ABI/dependency/legal gates independently of CI controls.

See [current containment](../development/containment.md) and
[release readiness](../development/release-readiness.md).
