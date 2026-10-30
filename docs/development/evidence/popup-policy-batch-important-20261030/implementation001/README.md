# Explicit Android popup policy: focused implementation checks

NATIVE-038/#90 now has a bounded, Compose-observable rejection result for the
current native owner. The retained default denies requests without creating a
child, touching its transport, reading a guessed destination or opening an
external handler. False multiple-window mode is explicitly Android's raw
current-view fallback, not child-window support. See
[ADR0012](../../../../decisions/0012-android-popup-rejection-contract.md) and
[the contract](../../../android-popup-policy.md).

Actual local command: `:calf-webview:testAndroidHostTest --tests
com.mohamedrejeb.calf.ui.web.AndroidPopupRejectionTest
:calf-webview:assembleAndroidDeviceTest`, with the recorded fresh-test/JDK17 init
scripts, serial build and 8GiB reserve. Exit0/653.17s; **3/3 fresh Robolectric
methods** and device APK assembly pass. The inspected XML, task marker and all
**922 library/999 combined input hashes** agree. This is a dirty, held-source
host diagnostic, **zero actual device tests**, not an immutable release pass.
Raw build/thread diagnostics remain private; the command/result, digests and
console/property-free XML are preserved in [host-local001](host-local001/review.json).

Important source/synthetic checks: **93/93 methods** (6 new popup, 34 shared
matrix, 1 workflow-choice, 52 Android controller/contract). These are not library
executions. The first owning source guard failed before repair; its log stays.
An earlier wrong `-k` selection executed zero and is not counted. Actionlint1.7.12
passes. No accepted native identity/lifetime/dropdown tests were replayed.

**#90 remains open** pending one immutable three-method Chromium/API35 request
and original-criteria review. All previous ledgers/failures, other platform and
physical/minimum/ABI/consumer/dependency/legal/security/release gates remain.
No publication, release, deployment, Pages, main or history changes.
