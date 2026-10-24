# [Medium][NAV-013] Sample image export runs unbounded reads and image allocations without error or concurrency control

<!-- nativecmpkit-item:audit:NAV-013 -->
## Classification
- **Finding:** NAV-013
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `sample:common`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FileSaverScreen.kt:169-185`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FileSaverScreen.kt#L169-L185) — `export button coroutine`
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FileSaverScreen.kt:214-245`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FileSaverScreen.kt#L214-L245) — `circleCropImage`
- [`sample/common/src/androidMain/kotlin/com.mohamedrejeb.calf.sample/utils/ImageBitmapExt.android.kt:8-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/androidMain/kotlin/com.mohamedrejeb.calf.sample/utils/ImageBitmapExt.android.kt#L8-L12) — `PNG encode`
- [`sample/common/src/nonAndroidMain/kotlin/com.mohamedrejeb.calf.sample/utils/ImageBitmapExt.nonAndroid.kt:8-16`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/nonAndroidMain/kotlin/com.mohamedrejeb.calf.sample/utils/ImageBitmapExt.nonAndroid.kt#L8-L16) — `Skia encode`
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ImagePickerScreen.kt:125-135`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ImagePickerScreen.kt#L125-L135) — `eager selected-image list`

## Root cause
The export click launches in the composition scope, reads the entire file before switching to Default, then fully decodes/crops/encodes with no size/dimension cap, busy guard or exception handler. Android/JVM/iOS readByteArray actuals perform synchronous I/O. Non-Android encoding force-unwraps nullable data; selected images are all composed in a scrolling Column.

## Impact and preconditions
Large/corrupt/inaccessible inputs can freeze UI work, fail the coroutine or require several simultaneous full-size buffers; rapid clicks duplicate work. OOM magnitude and Skia resource lifetime are risks needing profiling, not measured leaks in this audit. Large multi-selection can also create excessive concurrent image work.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- readByteArray at line173 precedes withContext(Default) at174; no catch or in-flight state surrounds the launch.
- circleCropImage holds input bytes, a full source bitmap, a square output and encoded PNG; source.width/height directly determine allocation.
- Android encoder ignores Bitmap.compress Boolean; non-Android encodeToData uses !! and no explicit close on the temporary Image/Data.
- Cross-module source references: KmpFile.android.kt30-37, desktop.kt12, ios.kt35-42; synchronous reading despite suspend signatures.
- Cross-review boundary: IO-021 tracks library/Coil eager reads and API scheduling guidance; NAV-013 tracks the sample's distinct export orchestration, overlapping jobs, image allocations/encoder errors and eager preview list.

## Recommended solution
Separate I/O/CPU dispatch appropriately, bound input and decoded dimensions, downsample before crop, serialize/cancel exports, surface recoverable errors and retain CancellationException. Check encoder success/null results and deterministic release of owned native resources. Use a lazy bounded image list.

## Risks and compatibility
Dispatchers.Default is not a universal nonblocking-I/O guarantee, especially in browsers. Do not close Compose-owned bitmaps accidentally. Picker/saver native resource bugs are covered by the I/O audit rather than duplicated here.

## Required tests / acceptance criteria
- Corrupt/empty/revoked/large-dimension images fail gracefully without crashing or leaking handles.
- Rapid repeated export and navigation away cancel/serialize work correctly.
- Measure peak memory and UI responsiveness on representative Android/iOS/JVM devices and browsers.
- Encoder failure and multi-select hundreds-of-images paths have bounded work and lazy rendering.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
