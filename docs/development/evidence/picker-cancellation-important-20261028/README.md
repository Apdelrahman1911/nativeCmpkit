# Important desktop picker cancellation — 2026-10-28

**IO-003/#6 remains open.** Immutable `97effbd7dfa39ef5010b0700666d76334512fff1` passes **7/7** important Gradle desktop methods, two fresh XML, zero failure/error/skip, exit0/42.01s. [Result/source review](gradle003/important-result-review.json) checks all795 original Git blobs, unchanged inputs, JDK17 runtime marker and built Linux host native manifest/checksum. [Progress comment](issue-progress-review.json) was posted/read back immediately after review; original issue body/title/labels/milestone remain unchanged.

## Owning repair and evidence

Cancellation can occur while synchronous JNI creation is in progress, after `withContext(IO)` admitted the worker. `withActiveDialogHandle` checks before allocation, inside the claimed handle's `try/finally` after creation, and after use. Both production `PlatformFilePicker.pick/save` use it; every successfully claimed configuration is destroyed once. Existing selected-path saving separately owns interruptible streams/atomic commit and checks cancellation. Public APIs, namespaces and JNI/framework identities are unchanged.

- [Disclosed negative control](control001/receipt.json): exact old helper plus an explicitly added **unguarded new wrapper**, not an original upstream API; five executions,2pass/3fail. Failed tests/logs are retained.
- [Standalone repaired helper](green002/receipt.json):5/5, actual Kotlin2.4.20/coroutines1.11.0/JDK17/IO cancellation. This is a dirty three-input diagnostic, not immutable full-module evidence. Its final source predates a KDoc-only change.
- [Actual Gradle execution](gradle003/actual-gradle.log.result.json): complete production/test compilation and **seven fresh selected methods**, five real coroutine/worker checks with controlled numeric handles and **two actual packaged Linux JNI configuration/query/destroy/stale-ID checks**. Those five standalone methods overlap: **not12 unique methods**.
- [Native manifest](gradle003/native-linux-x64.json): Rust1.98.0/ABI1, source revision97effbd7/dirtyfalse,27source files, payload SHA256 `87926544e614f3e8d720b600cf11a241afa7fe82ce3da2c139ef02894b987306`. Manifest is reviewed provenance of these built resources, not a complete trusted-builder/consumer attestation. No native binary is archived here.

## Remaining original criteria

The new JNI tests deliberately use no raw parent or OS modal: a file query against a directory configuration cannot open a file modal, even if the admission guard regresses. They do **not** execute live Compose settings/disposal, immediate launch, visible-dialog window close, JNI config-build/show under Valgrind/ASan, macOS/Windows UI, X11/Wayland parenting or native-parent acquisition. Earlier [actual native config Valgrind results](../native-ownership-important-20261028/review.json) and48possible/544reachable bytes remain preserved.

Cancellation racing **after** the guard can still enter a synchronous native modal. No interruptible-dialog promise; IO-023's genuine parent ownership/thread-affinity repair remains unresolved. No release/security/minimum-platform/consumer gate is cleared and no package/release/deployment occurred.
