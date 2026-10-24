# [Medium][IO-018] Multiple selection accepts invalid limits and differs across platform fallback paths

<!-- nativecmpkit-item:audit:IO-018 -->
## Classification
- **Finding:** IO-018
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.kt:147-160`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.kt#L147-L160) — `FilePickerSelectionMode.Multiple`
- [`calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.android.kt:125-150,207-214`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.android.kt#L125-L150) — `multiple contracts/results`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:355-358`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L355-L358) — `configuration.selectionLimit`
- [`calf-file-picker/src/jsMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.js.kt:70-78`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/jsMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.js.kt#L70-L78) — `files.take(maxItems)`
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt:166-169`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt#L166-L169) — `result.take(maxItems)`

## Root cause
Multiple(maxItems) has no validation. Negative values reach Kotlin take or native APIs; zero means unlimited in PHPicker but an empty result on truncating platforms. Android PickMultipleVisualMedia has native contract limit constraints, and its own successful/fallback result callback is not post-truncated unlike the explicit OpenMultipleDocuments fallback.

## Impact and preconditions
The same public configuration can throw, select nothing or mean unlimited depending on platform. Small/oversized Android photo limits may be rejected by AndroidX, and OS-controlled fallbacks need consistent enforcement. Device-specific Android behavior was not executed.

## Supporting evidence
- Common Multiple merely stores the nullable Int. iOS uses maxItems directly or 0; truncating implementations call take(maxItems).
- Android lines 146-150 return all media-picker results, unlike explicit document fallback lines 129-131.
- AndroidX exact OS contract behaviors require pinned-version/device tests; no assertion here that every fallback exceeds the limit.

## Recommended solution
Define and validate a portable limit domain (for example null unlimited, positive counts; route count=1 to single selection where required), clamp/adapt to native maximums, and enforce result limits consistently after native fallbacks. Validate at configuration creation rather than deep in callbacks.

## Risks and compatibility
Rejecting values previously accepted on one platform is observable. Keep Multiple companion-object backward compatibility and document Android platform caps for null/unlimited.

## Required tests / acceptance criteria
- null, -1, 0, 1, 2 and very large limits on each target
- Android native photo picker and ACTION_OPEN_DOCUMENT fallback
- JS/Wasm negative input does not silently become cancel
- Limit change during composition
- iOS limit0 distinction

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
