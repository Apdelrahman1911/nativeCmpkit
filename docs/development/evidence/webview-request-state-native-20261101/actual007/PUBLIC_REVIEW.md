# Actual iOS 41270913975 — FAILED before native

Run **41270913975**, attempt 1, `ios-webview-request-dns`, at immutable
`7cb5f46d2b3b820cfe6b485ab04c8f75cbbeed72` is terminal **FAILED**.
The original tooling job **124743330463** failed step 4,
“Offline verification-tool adversarial fixtures (not library passes)”.
Its original result is **1747 methods /1746 pass /one failure /74.139 s**, exit 1.
The profile-selection step and all six dependent jobs were skipped.
**ZERO Apple SDK/Gradle application tasks/native methods/original XML/artifacts.**
No iOS runtime failure, cleanup acceptance or issue closure is inferred.

## Exact original failure and source-backed cause

Original failing method:
`test_android_webview_request_state.AndroidWebViewRequestStateGuards.test_source_models_reject_reset_masking_filtering_early_cleanup_or_unbounded_fixture_shortcuts`

At frozen `scripts/ci/test_android_webview_request_state.py:377`, the standalone
assertion expects `ValueError` for:
`require_native_witnesses(source + "\nfun masked() { state.errorsForCurrentRequest = emptyList() }\n")`.
Original result: **`AssertionError: ValueError not raised`**. The actual log itself
contains this exact appended masking expression; this is not an unidentified
loop mutation. Sanitized original records and their raw-log SHA are retained.

The helper first projects the full source through `compiled_request_source`
(line 47). That projection (lines 108–114) takes only the legacy prefix/resume
through the separate Stop/redirect-helper marker and returns the SHA-frozen old
source. It discards the complete new helper suffix and therefore the extra
manual-reset function appended after that suffix. The forbidden reset regex
(lines 88–93) then sees only legacy source, so it cannot reject the appended
mask. Independent immutable source-range inspection confirms both markers occur
once and the projection retains legacy SHA
`a78930b54606b88fb9e4af3e9e3748d41f1abf5496f05dad84eb8a664afc1f40`.
No guard/model/test was invoked by this reviewer to establish these source facts.

This is the owning **source-guard projection/refusal defect**, not an Android/iOS
native behavior or Apple compiler/SDK cause. Only its owning guard boundary is
justified for repair; actual007 remains failed. No native source/assertion,
legitimate Stop/redirect, timeout, transport or cleanup relaxation is justified.

## Frozen source and exact unexecuted selection

Independently hashed **all 1097 library /1174 combined frozen inputs**, including
1107 distinct Git blobs, directly from the requested commit without checkout,
fetch or mutation. Every SHA and Git blob OID agrees with the copied lead freeze
and postcommit binding; the library map is the exact combined-map subset.
These are **frozen Git-source checks**: no uploaded actual-library or combined
input map exists because this run uploaded zero artifacts.

The three unchanged intended selectors are recorded verbatim in
`STATIC-SOURCE-CAUSE-AND-SELECTORS.json`: request2 + DNS1, one
`:calf-webview:iosSimulatorArm64ApplicationTest`, focus
`webview-ios-native-request-dns`. Source declarations are exactly two request
methods and one DNS method. No selected method was executed, no XML identity
was produced, and the accepted eleven are not substituted for these three.

## Native and cleanup evidence boundary

The native/library job was skipped before runner allocation. Thus there is no
actual iOS SDK/compiler/task exit, fresh report, UIKit/WebKit callback, native PID,
main/Worker activation/completion, application install/uninstall or simulator
creation/shutdown/deletion receipt. These fields are explicitly unavailable in
`EVIDENCE-BOUNDARIES.json`; “not started” is not graceful-cleanup acceptance.
The real host, WebKit methods and exact cleanup contracts remain source-bound
and unverified by this actual run. No TLS/DNS/Stop/redirect/Reload native pass,
profiler, physical/minimum/all-platform/API-ABI/consumer/security/readiness or
release/deployment inference is made. **#64 remains open.**

## Bounded independent acquisition and seal

Terminal metadata and an original artifact manifest were acquired once after the
initial bounded status read; the manifest is exactly empty. Only the failed iOS
tooling job's original log was downloaded once, exit 0 /652457 bytes /SHA
`6b83832e7b840799460e55dac4a17e88d60ccf43212f5964a0e1635cf0069b1e`.
No accepted/previous archive was downloaded, no download was retried, no test,
model, build, SDK/native/dispatch or shared/Git/GitHub mutation was performed.
Camera original receipts were not swapped in; only sanitized shared cause facts
were sent to its separate reviewer.

The sealed archive contains sanitized original run/job/artifact/result records,
frozen and independently checked source identities, exact immutable source
excerpts/native files and explicit absent-runtime/XML/protocol/cleanup boundaries.
Raw API metadata, raw terminal/tooling log, private runtime fixtures, credentials
and private environment values are excluded. The parent lead owns integration,
any owning repair, future finite request and original-criteria acceptance/closure.
