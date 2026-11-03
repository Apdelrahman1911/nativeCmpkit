# Original memory/Worker run445 — FAILED, 2026-11-03

[Run41574895107](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41574895107)
ran at **5e0dc71311035d074725fdd1e67f0ea1756de12b**. Its original logs/artifact
were acquired once and reviewed against **all1,256 actual before/after own-Git
inputs**, not the later1,262/1,266 preparations.

## Actual outcomes

- Three selected methods report **3passed/0failed/0errors/0skips in two fresh XML**.
- Partial native TeamCity frames agree exactly with these three XML identities.
- Whole Gradle invocation remains **exit1/1,553.16s**; collector `passed=false`.
- `application_protocol=null`; partial protocol has activation, all three
  finished cases, no open suites/case, but **completion=null**.
- Transport: **console0/9.8s**, `protocol-finish`, `missing-worker-completion`.
  Console cleanup was not requested. Console0 is not a native Worker witness.
- All four independent owning-app cleanup witnesses passed. Post-runtime/
  post-binary receipts were **not reached** and are not invented.
- One UIKit appearance-transition warning remains. No uniquely matching crash
  report was found; this does not establish crash absence or an exit cause.

**ZERO methods are accepted for complete native lifecycle verification.** Green
XML cannot close #31 or prove the required Worker termination/resource lifecycle.
The earlier captured-owner assertion is absent from these XML, but its exact
retention chain and the missing completion's cause remain unproven.

## Relevant implementation

The frozen `NativeUiApplicationHost.kt:startGeneratedTests/pollCompletion`
calls `testLauncherEntryPoint` on an owned Worker, consumes its Future on Main,
requests/consumes Worker termination, releases Main leases, then emits the
mandatory `NATIVECMPKIT_UIKIT_COMPLETED` marker before exiting.
`scripts/ci/ios_ui_application.py:NativeProtocol.finish/forward_application`
correctly refuses EOF/console0 without that marker; this gate is not relaxed.

The next [owning453 batch](../ios-worker-completion453/README.md) adds only
bounded phase observations to locate this gap and groups the unaccepted three
with the two missing same-operation cancellation cases. It is not a claimed
native fix, blind unchanged retry, release gate or justification for closure.

Original custody and review: [acquisition](acquisition.json),
[review](review.json), [run metadata](run-summary.json).
