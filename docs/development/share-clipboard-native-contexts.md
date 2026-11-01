# Clipboard fallback: native browser context verification

NATIVE-026/#82 preserves public sharing APIs and reuses accepted JS/Wasm
controlled-Promise C1/C2 results. `share-clipboard-native` selects only four missing
environment cases on both targets. Its two jobs run serially so one can coexist
with another native job under the global max2 limit.

[Preparation evidence](evidence/current-platform-recovery-20261101/clipboard-native-contexts-prepared078/README.md)
contains important controls and actual compilers, **not browser-native acceptance**.

## Implementation and ownership flow

- `calf-share/src/webTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardEnvironmentAcceptanceTest.kt`
  owns a random-token iframe, message listener and bounded control requests. Each
  child invokes only the exact selected method from the same emitted library test
  bundle; accepted old methods are not replayed.
- `calf-share/karma.config.d/nativecmpkit-clipboard-fixture.js` scopes a Karma
  launcher/middleware to this selection. It owns the actual Chrome child, an
  exclusive ordinary profile beneath Karma's disposable root, and the no-follow
  observed DevTools port file. Process/directory identities must remain exact;
  unrelated browser enumeration or attachment is forbidden.
- The JS/Wasm `WebClipboardNativeHarness.*.kt` actuals expose native browser
  properties, permission query, original write Promise and exact restoration.
  They add no production dependency or public API.
- Capability absence is confined to an owned secure child. Insecure mode uses
  actual HTTP at a reserved `.invalid` hostname mapped solely to loopback, not a
  shadowed `isSecureContext`. Denial uses actual document policy, PermissionStatus
  and native DOMException.
- An exact read-only owned DOM hit-test precedes CDP mouse input. The library
  call requires `event.isTrusted`, active transient activation and document focus,
  with no suspension before the write. No synthetic click, manual grant or
  `Runtime.evaluate(userGesture=true)` is used.
- Observation calls the saved native method and returns its original Promise.
  Outcomes must occur exactly once after settlement. Cleanup coalesces owned
  operations, releases input when needed, detaches/closes CDP, restores native
  descriptors/listeners, removes frames and retains failures. Complete native
  browser/profile cleanup still needs original results review.

## Cases required on both JS and Wasm

1. `secureContextWithAbsentClipboardApiReportsUnavailableWithoutPlatformCalls`
2. `genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable`
3. `actualDeniedClipboardPermissionRejectsOneTrustedGestureWriteWithoutSuccess`
4. `directTrustedGesturePreservesActivationAndCompletesOneActualOwnedTextWrite`

The planner binds exact method/source hashes. Each target requires one fresh
original XML/task marker; stale, missing, duplicate, foreign or skipped cases fail.

## Actual qualification and limits

Serial JS0/59.01s and Wasm0/50.01s compilers hold1129 library/1206 combined inputs,
JDK17.0.20/Gradle9.7.1. Eight important and97 affected synthetic methods compose105
unique methods. A later capacity-guard red/green is the same existing method;
subsequent compiler-map differences are only that CI guard/workflow.

The observer consumes a rejection, so it is **not replacement C1 unhandled-
rejection evidence**. Reuse the accepted controlled-Promise results. Zero absent-
API counters do not independently prove zero attempted calls. Native Promise
completion is not OS paste/readback or recipient delivery. Never read unrelated
clipboard contents. Other engines/physical devices, consumer/API-ABI/dependency/
legal/security/release gates remain independent. No publication, Pages, deployment
or main integration follows these tests.
