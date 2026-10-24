# [Medium][IO-026] Web picker catches application callback failures as cancellation and lacks disposal cleanup

<!-- nativecmpkit-item:audit:IO-026 -->
## Classification
- **Finding:** IO-026
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/jsMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.js.kt:26-31,42-46,61-91`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/jsMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.js.kt#L26-L31) — `onchange/oncancel/DOM lifetime`
- [`calf-file-picker/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.wasmJs.kt:23-28,39-43,58-88`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.wasmJs.kt#L23-L28) — `onchange/oncancel/DOM lifetime`

## Root cause
The broad try/catch includes currentOnResult; if application code throws after receiving selected files the catch calls onResult again with an empty list. oncancel invokes the callback before cleanup without finally. Inputs are per-launch DOM nodes with no DisposableEffect/session owner, and fileDialogVisible is never set true or used as a launch guard.

## Impact and preconditions
A callback exception can become a misleading second cancellation event; a throwing cancel handler leaves the node attached. Disposal while the dialog is open can retain callbacks/DOM nodes and later update an obsolete screen, while repeated launch calls have no explicit concurrency policy.

## Supporting evidence
- JS line 75 callback is inside try, catch line 78 invokes callback again; Wasm lines 72/75 mirror it.
- oncancel cleanup follows callback without finally; no DisposableEffect exists in either source file.
- No browser/UI lifecycle execution was available; branch/error behavior is source-confirmed.

## Recommended solution
Separate selection conversion failures from user callback invocation, put cleanup in finally before delivering terminal events, and own DOM/listener lifetime per launch/composition. Add an exactly-once completion guard and a supported repeated-launch policy.

## Risks and compatibility
Browser cancel-event support and user-activation timing vary. Do not swallow fatal/application errors as user cancellation or remove a node so early that native events are lost on a supported browser.

## Required tests / acceptance criteria
- onResult throws after success: no second callback
- oncancel throws: node still removed
- Composition disposed during dialog
- Two launch attempts
- Same file reselect and normal cancellation
- JS/Wasm parity

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
