# Desktop WebView stop-loading verification

**NATIVE-001 remains open until actual results are reviewed.**
The production repair is already present in `WebView.desktop.kt`:
`DesktopWebViewOwner.navigate(StopLoading)` calls `engine.loadWorker.cancel()`
directly, without putting another StopLoading command into the navigator queue.
No public API or production refactor is introduced in this continuation.

## Focused important tests

- Retain `JavaFxWebViewTest.stopCancelsRealSlowLoadWithoutFeedbackLoop`: real
  JavaFX engine/HTTP slow request, one consumed command, native load stops.
- Add `repeatedStopsAfterDetachAndReattachCancelOnlyTheCurrentRealLoad`: the
  production JFXPanel/owner is mounted in a visible native JFrame. Two real slow
  HTTP requests exercise attached stop, queued detached stop and reattachment;
  native Worker cancellation transitions are counted. Repeated idle stops each
  consume once without feedback; another attachment must not replay consumed
  events. Native work runs on the FX thread, window operations on the AWT thread.
  Owned collectors, native listener, HTTP gate/executor and window are released.

This is actual JavaFX/AWT integration when executed, not a mock worker, a sample
application or public Compose mount/dispose certification. A native state transition
count is not a profiler/instrumented count of every Worker method invocation;
source review independently checks the single direct native call per Stop event.

## Preparation and efficient execution

[Preparation](evidence/webview-stop-preparation-20261027/preparation.json) records
**37 authored selected methods** in four source files: 24 common, five desktop
cookie and eight real JavaFX methods. **Zero local native/library executions or
compilation** for the new test. Four profile/outcome guards pass within418 CI
tooling methods; the initial expected missing-profile/policy red remains.

New finite `webview-desktop` selects only `calf-webview` on one Linux/Xvfb desktop
slot. Two exact native stop cases are mandatory in fresh XML; absent, duplicated,
wrong-target or headless/skipped outcomes fail. Full profiles retain all11 slots
and all modules; unrelated passing platform/UI/consumer suites are not repeated.
Local heavy builds stay prohibited below the8GiB reserve.

Run the immutable focused job, review its source/command/runtime/fresh cases and
both original NATIVE-001 criteria, **then close directly**; update documentation
afterward. A Python/preparation pass is not native acceptance. Separate WebView
composition/GC/cookie/security, other-host/minimum-platform, consumer/API-ABI/legal/
dependency and release gates remain open. No publishing/deployments/Pages.
