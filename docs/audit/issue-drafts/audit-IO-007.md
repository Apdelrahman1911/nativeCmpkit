# [Medium][IO-007] iOS picker completion is not exactly once and document swipe dismissal is not observed

<!-- nativecmpkit-item:audit:IO-007 -->
## Classification
- **Finding:** IO-007
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:74-134`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L74-L134) — `UIDocumentPicker delegate`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:172-209`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L172-L209) — `PHPicker delegate/hasFinished`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:214-243`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L214-L243) — `photo dismiss delegate and guard reset`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt:48-78,137-150`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt#L48-L78) — `save document delegate/presentation`

## Root cause
PHPicker computes processResult with compareAndSet but only gates the empty-result branch; every nonempty didFinishPicking list is processed even when the guard is already set. UIDocumentPicker paths implement documentPickerWasCancelled but do not attach an adaptive presentation delegate for interactive dismissal.

## Impact and preconditions
Repeated photo completion can duplicate copies and callbacks; cancellation followed by late results can deliver contradictory events. Document picker/saver swipe-dismissal may never notify the caller or clean up pending staging.

## Supporting evidence
- Nonempty branch at 184 bypasses processResult whereas else-if at 203 uses it.
- Commit e927149 changed the previous unconditional duplicate guard into this branching structure.
- UIDocumentPicker has no adaptive presentation delegate in baseline; PR #551 adds one. Platform callback sequences remain device-unverified.

## Recommended solution
Use a per-launch terminal-state machine and enforce it for all result branches and late callbacks; support the platform interactive-dismiss callback for document picker and saver as well as photo picker. Keep delegates alive for the session.

## Risks and compatibility
Photo providers may emit cancellation and completion in surprising order; rejecting duplicates must not resurrect the historical lost-result problem. Separate dialog dismissal from asynchronous result-processing completion.

## Required tests / acceptance criteria
- Two nonempty photo delegate callbacks
- Empty then nonempty callback order
- Swipe dismissal for photo/document/save
- Cancel while NSItemProvider work is running
- Relaunch before old provider callback returns
- No duplicate temp copies/callbacks

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
- https://github.com/MohamedRejeb/Calf/commit/e927149
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
