# Android WebView exact-two actual — FAILED, zero accepted methods

Run [41276056846](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41276056846), attempt 1,
workflow 395188384, at `ff41a9329c6f85dcae3c50d6372997ff92501395` is **FAILED**. Tooling passed; the owning
Android job failed. Its single original fresh XML contains **two actual methods,
two failures, zero passes/skips**. This is not a tooling-only failure and is not
native acceptance or an issue closure.

## Original evidence and fixed source binding

- Original owning artifact `13071239595` (`library-evidence-android-device-api35`)
  and the tooling/native job logs were acquired once each after terminal completion.
  The ZIP's 232801 bytes and SHA256 `12a6fbe7854fea70590311fc54103fbe03485c18a9d11537df3a37af621f783b` exactly
  match artifact metadata; all 20 confined original members were hashed/read back.
- `request-prerequisite-freeze005` binds 1104 library / 1181 combined paths at this
  commit. All 1181 paths independently match the immutable, untruncated Git tree.
  The four original before/after actual maps are **1104-library maps**, all equal
  to the frozen library subset. **No actual combined map was uploaded.**
- Exact API35/calf-webview/annotation selection, both original XML identities,
  guarded report layout, one strict marker reported by the original receipt and
  one independently visible marker in bounded child-log excerpts were reviewed.
  The full child log was not uploaded; duplicated job-log projections are not
  counted as repeated native task execution.
- Actual API35 / Android15 / x86_64 / boot1 / SELinux **Enforcing** identities
  agree at boot and before/after the connected task. JDK17.0.21 / Gradle9.7.1;
  assembly **0 / 218.06s**, AVD create **0 / 1.00s**, connected Gradle **1 / 68.03s**.
  Source/commit stayed unchanged and clean. Tooling's main CI1796 and consumer241
  batches are not native-library passes.

## Exact failed boundaries

1. `twoHeldNativeTransportFailuresResetErrorsAndNativeReloadUsesCurrentOwnerUrl`
   fails at the first held-start wait, source line75 / `awaitHeldStart`309 /
   `waitFor`367: “A real onPageStarted and still-held exact owned HTTP request”.
   The required simultaneous native-start/request operands are not archived.
   No completed fail/fail/recovery/Reload method is accepted.
2. `publicNavigatorStopClosesHeldTransportAndActual302RedirectReloadUsesCurrentOwner`
   fails at the first held Stop request, source line158 /
   `awaitStopRedirectHeld`244 / `waitFor`305, **before public Stop/302/Reload**.
   The primary wait operands and cause remain unknown. Retain the suppressed
   owned-server failure, including “Peer disconnected before public Stop was
   invoked”; do **not** call it the primary cause or a public cancellation witness.
   Activity/native-owner teardown precedes `server.close` and can supply that EOF
   observation after timeout. Its original chronology is not recorded.

The original XML SHA256 is `b7b6bd7994023991ea5da3188d3d6b0645d6e0b447c274403d7180dcce75ebb1` (4530 bytes). `CASES.json` is a
sanitized projection, **not reconstructed or substitute JUnit evidence**. Raw XML,
job logs and runtime-private strings stay in the sealed private originals.

## Cleanup and unchanged limits

The original controller records ownership-verified graceful guest shutdown,
child exit0, no forced group, and clean_shutdown=true. This WebView branch does
**not** record separate post-exit ADB transport absence or independent APK
signer/installed-UID/uninstall readback; do not borrow camera/IO/helper receipts.
Neither complete native method/disposal-oracle outcome is accepted.
Unuploaded logcat/protobuf bodies are not reacquired or inferred from inert hashes.
No exact WebView provider/version or Chromium callback-source revision was
recorded; API/image identity does not prove callback timing.

**#64 remains open; zero independently accepted complete methods and zero new
whole-issue closures.** Causes remain unknown. No replay, source edits, local
build/model/test execution, dispatch, Git/GitHub mutation or publishing occurred
in this review. DNS/TLS/offline/Desktop/iOS/all-target/minimum/physical/consumer/
ABI/dependency/legal/security/readiness and all capacity/publishing gates remain.
