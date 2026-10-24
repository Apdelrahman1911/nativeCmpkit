# Prioritized development roadmap

This is an evidence-based development proposal, **not authorization to publish or
begin a major rewrite**. The complete backlog contains every finding and the six
independent actionable historical topics; nothing is discarded because it does
not fit the first milestone.

- [All items in dependency-respecting order](backlog.md)
- [Machine-readable phases, modules, dependencies and required tests](backlog.json)
- [Full technical findings](../audit/findings-index.md)
- [Historical request dispositions](../migration/upstream-actionable-decisions.json)

## Triage and sequencing

Priorities: 0 Critical, 37 High, 106 Medium, 21 Low audit findings. High-priority
test infrastructure is a release gate, not a claim of an exploitable vulnerability.
Three baseline build findings are migration-resolved; all unresolved defects and
risks remain in the backlog. The six imported topics add one Medium and five Low
items, not six new source-confirmed bugs.

Effort is a relative engineering estimate: **S** localized change plus focused
tests; **M** multi-path or multi-platform change; **L** coordinated ownership/API
or integration work; **XL** broad architecture/compatibility work requiring its
own decision. There are 39 S, 96 M, 27 L and two XL audit items. These are not
calendar promises; OS/device access and review can dominate implementation time.
Historical topics are marked **triage-first**, not given fabricated estimates.

The generated order respects explicit dependencies. Lower-priority prerequisites
are promoted into the phase they unblock. Items without recorded dependencies
may run in parallel **only if they do not edit shared APIs/native owners**. Absence
of a dependency edge is not proof of independence.

## Phase 0 — Preserve the migration safety baseline

Retain BUILD-008/009/011 evidence and the removed deployment workflows as inert
archives. Keep original history, notice files, retained namespaces and publication
interlocks. Verify checksum and issue-map receipts before future refactors. This
phase does not mean a release pipeline exists or has been certified.

## Phase 1 — Before a supported preview

| Workstream | Impact / urgency | Starting items and dependencies | Required exit evidence |
|---|---|---|---|
| Memory/data integrity | Prevent source deletion, empty exports and unsafe native copies | IO-001/002/003/004; IO-005 after ownership contract IO-008 | Boundary-size/empty file tests, same-file/overwrite tests, rotation/recomposition, race/cancel/repeated disposal harness |
| Native ownership | Stop retained engines/presenters and late-callback misuse | NATIVE-002; UI-018 after UI-016/017; UI-012/013/014 | Repeated compose/dispose, simultaneous present/dismiss, iPad popover and callback-freshness tests; leak instrumentation |
| Permission orchestration | Fix request/result identity and real OS prerequisites | PERM-002 after PERM-001; PERM-004 after PERM-003; PERM-008 after 003/007/009; PERM-009 after 007; PERM-011/013 | Batch/alias result tests, sequential prompting, background upgrade, old/new iOS calendar and Bonjour cancellation fixtures |
| Incomplete advertised state | Avoid apparently working state/navigation APIs losing data | PERM-018 then PERM-020/021; NAV-001 then NAV-002 | Observable location update/error tests; duplicate-route independent state and arguments tests |
| Native date/bars/input | Correct calendar interpretation, geometry and accessibility | UI-001/002, UI-020 then 021; UI-027; UI-029/031 after UI-030 | Non-Gregorian/timezone/locale cases; rotation/insets/transition layout; semantics/keyboard and pointer-cancel tests |
| Desktop/web boundaries | Fix stop command and cookie ownership; make risky fallback policy explicit | NATIVE-001/013; conditional NATIVE-010/027 | Real FX engine stop test, cookie-handler coexistence, iframe sandbox policy, non-executing share fallback fixture |
| Reproducible build/consumer gates | Avoid host-dependent artifacts and misleading green CI | BUILD-001/003/004/005/006/007/010/012; UI-040; NAV-009 | Host/architecture matrix, reviewed locks/hashes, native contents/provenance, API/ABI and min-SDK consumer checks, artifact notice payload |

All High findings are included, even where omitted from this short workstream
table; the generated backlog is authoritative for the complete set. Source
defects proven by narrow probes still need real integration regressions.

## Phase 2 — Compatibility, robustness and performance

- Normalize launch completion to exactly once; represent unsupported, cancelled,
  denied and failed outcomes without silently reusing success values. Evolve
  APIs with compatible adapters rather than silently breaking consumers.
- Resolve Medium platform discrepancies: iOS security-scoped resources and temp
  ownership, Android storage/permission version mappings, browser save/read errors,
  WebView navigation/cookie limitations, stale remembered inputs and UI state.
- Add size/scheduling guidance and streaming paths for whole-file IO/Coil; profile
  native view retention, observer lifetime and animation/frame work before adopting
  an optimization. Require before/after memory/CPU evidence and regressions.
- Design truthful capability reporting for camera, permissions, sharing, geo and
  iframe-backed WebView; tests must reject accidental silent no-ops.
- Reproduce upstream #34 on a current iOS fixture before treating the old report
  as a live defect. Keep its archived discussion and current-source assessment.

## Phase 3 — Breadth, polish and deliberate architecture

Address remaining Low findings, accessibility polish, documentation and API
ergonomics. Triage upstream #72, #78, #259, #343 and #471 as scoped work: web focus,
contacts/OTP product scope, busy-dialog examples, file preview and remaining bar
styling. Maps/media/notification scheduling are not implemented features; require
a product/capability decision rather than promoting empty modules.

Before any XL ownership/navigation redesign, write a new ADR with alternatives,
source-compatible migration, binary/resource/JNI implications, error/lifecycle
contracts and platform acceptance matrices. The audit intentionally did not begin
such rewrites.

## Release gate — separate owner authorization required

1. Resolve applicable High findings or explicitly narrow the supported surface;
   document accepted risks, not merely close issues.
2. Run real Gradle common/desktop/Android/browser tests and Apple framework linking;
   add device tests for native behavior. A Cargo run with zero tests is insufficient.
3. Verify consumer builds on minimum SDK/runtime and all promised desktop
   architectures; inspect Maven/native contents, API/ABI and duplicate-class risks.
4. Freeze/verify dependency graphs, complete licensing payloads, scan the resolved
   graph and review publishing identity/signing with the owner.
5. Obtain **explicit authorization** for any release/package/deployment. This
   migration created none, and read-only verification is not publishing approval.

An issue is done only with the required tests, reviewed evidence, compatibility
assessment and documentation update. Keep baseline findings/history intact; add
current-resolution evidence and update the issue rather than deleting the record.
