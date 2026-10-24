# [Medium][NATIVE-032] Share callbacks can be delivered twice when application result handling throws

<!-- nativecmpkit-item:audit:NATIVE-032 -->
## Classification
- **Finding:** NATIVE-032
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt:26-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt#L26-L30) — `share launch try/catch`
- [`calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt:45-55`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt#L45-L55) — `handleSharePromise`
- [`calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt:10-18,29-37,48-54,64-70`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt#L10-L18) — `then/catch chains`

## Root cause
Android includes currentOnResult(Success) inside the try that handles startActivity; a callback exception is caught as a launch failure and the callback is invoked again with Unavailable. Browser promise.then invokes the callback before a trailing catch that treats the callback exception as a share rejection and invokes another outcome.

## Impact and preconditions
One operation can produce conflicting duplicate results; user bugs are hidden as platform failures and destructive callback side effects can repeat. A second throwing invocation may escape in a different place as an unhandled error.

## Supporting evidence
- Android currentOnResult at28 lies inside catch Exception. JS/Wasm append catch after then handlers that invoke callbacks.

## Recommended solution
Catch only platform operation errors, then invoke user callbacks outside that catch boundary. Use promise.then(onFulfilled,onRejected) or equivalent separate settlement handling so result callback exceptions are not remapped to share outcomes.

## Risks and compatibility
Application callbacks are normally expected not to throw, but library error boundaries must not manufacture a second terminal platform event. Preserve crash reporting for the original application exception.

## Required tests / acceptance criteria
- Callback deliberately throws after recording Success; exactly one callback invocation is observed.
- Platform start/share rejection invokes one failure and is distinct from callback failure.
- JS/Wasm resolved/rejected promises and Android ActivityNotFoundException paths.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/508
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
