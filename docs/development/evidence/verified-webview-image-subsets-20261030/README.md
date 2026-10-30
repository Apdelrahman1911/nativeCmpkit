# Verified WebView/value and UIImage subset

**#72/NATIVE-015 and #140/UI-037 CLOSED/completed** immediately after their
three original acceptance criteria were reviewed. Independent authenticated
readbacks verify closure and unchanged original technical bodies/titles/labels:
[NATIVE-015](NATIVE-015-closure-readback.json), [UI-037](UI-037-closure-readback.json).
Previous resolution records, including remaining requirements, are preserved
before the additive ledger updates. The baseline164 findings are unchanged.

- [NATIVE-015 criteria](NATIVE-015-original-criteria-acceptance.json): real
  Android Chromium/iOS WebKit/JavaFX/JS/Wasm values, threading and invocation-local
  callbacks, plus eight exact unchanged Android-host fault regressions. Destruction
  may drop pending callbacks; promises are not awaited; asynchronous iOS callbacks
  must not throw across Objective-C. Shared41003730413 remains **FAILED** at the
  separate Android remount/iOS compiler failures. #62/#89 stay open.
- [UI-037 criteria](UI-037-original-criteria-acceptance.json): nine prior real
  UIImage cases/two real1MP/concurrent-GC/native-failure methods reused, not replayed;
  one fresh native workload passes369 rounds/738 conversions under requested Darwin
  diagnostics. No ASan/every-allocator attestation. Actual Instruments exits21 with
  zero allocation rows/zero leaks invocations; **#141 remains open**. Strict startup
  failure40989310808 is preserved, not repaired or waived.

[Fresh census](issue-counts-readback.json): **80 closed / 92 open / 172 total**.
No physical/minimum-provider/native-matrix, ABI, packaged-consumer, dependency,
security or release clearance. No packages/releases/deployments/Pages created.

