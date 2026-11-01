# #99 / NAV-012 — native secure-input preparation

The genuine sample now obtains its existing name/password descriptors from one
isolated, unchanged-behavior callback factory. Neither callback logs input. The
library `iosTest` compiles only that single source-bound helper, not a sample
module/application; its screen is held for provenance and is not compiled.
Public library APIs and descriptor behavior remain unchanged.

- Independent important controls: **21/21 once, 43 subtests /10.653s**; already
  accepted outcomes are reused, not replayed during lead integration.
- Actual offline invocation compiled the production KLIB, then **failed1/55.01s**
  before test compilation on uncached `ui-test-iossimulatorarm64:1.12.0`.
- Failed-test-task-only ordinary-resolution recovery: **0/46.01s**; test KLIB
  executes, production is UP-TO-DATE. Both1139/1215 input maps held, JDK17.0.20
  launcher/daemon correspondence and Gradle9.7.1 observed. This is dependency
  resolution, not dependency trust or native execution.
- The later #50 composition changes only three non-UI paths; applicable UI
  compiler results are reused, not relabelled as current whole-map equality.
- The shared18 newly affected tooling methods pass once; see the adjacent
  [owning C3 summary](../ios-provider-cancellation-owning090/README.md).

**ZERO Apple links/native executions. #99 remains open.** Next is the exact
`ios-secure-alert-input` profile: one genuine UIKit synthetic input/keyboard/
masked-pixel/stdout-stderr method plus nine real descriptor-capture and controlled
failure/refusal methods. Use no owner's input or system log dump. Capture is
current-process stdout/stderr, not all OS logging. Physical-device, full-log,
concurrency and true failed-kernel-syscall limits remain explicit; source controls
and injected refusals cannot substitute for native results or release/security
readiness. No publishing, deployment, Pages or main/history change.
