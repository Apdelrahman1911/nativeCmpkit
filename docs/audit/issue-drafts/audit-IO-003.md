# [High][IO-003] Desktop composition disposal races raw JNI handles; cancelled creation can leak handles

<!-- nativecmpkit-item:audit:IO-003 -->
## Classification
- **Finding:** IO-003
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt:98-145`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt#L98-L145) — `LaunchedEffect and DisposableEffect`
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt:152-166`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt#L152-L166) — `launch under dialogMutex`
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt:79-89`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt#L79-L89) — `showFilePicker/showDirectoryPicker`
- [`calf-file-picker/native/src/lib.rs:254-272`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/native/src/lib.rs#L254-L272) — `box_config/ref_config/drop_config`
- [`calf-file-picker/native/src/lib.rs:379-384,408-410,443-450`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/native/src/lib.rs#L379-L384) — `JNI show/destroy exports`

## Root cause
Launch and settings updates use dialogMutex, but onDispose destroys the same pointer without that mutex or a native ownership registry. A queued/starting IO show call can dereference freed DialogConfig memory. A handle allocated inside withContext(IO) is not yet owned by dialogHandle if prompt cancellation discards its return value.

## Impact and preconditions
Disposal interleaving with queued show/config.build can cause use-after-free and process crashes; panic catching does not make invalid pointer dereferences safe. Rapid settings changes/disposal during creation can leak native allocations. launch() before initial creation silently returns without a callback.

## Supporting evidence
- onDispose at 138-144 does not acquire dialogMutex, while launch holds it at 153.
- Rust ref_config blindly dereferences handle and manufactures a static reference; drop_config frees it.
- Source establishes the unsafe interleaving; no native GUI/race exploit was executed.

## Recommended solution
Introduce one owner for each dialog session: acquire/close/show via a safe handle registry or equivalent lifetime mechanism; mark disposed and serialize destruction with in-flight use. Ensure allocation cleanup on cancelled delivery, and queue or explicitly reject launch before readiness. Preserve the existing public API where possible.

## Risks and compatibility
Do not block the UI waiting for a user to close a native dialog. A raw pointer is not made safe by a Kotlin mutex unless every destructor participates; cancellation is not native-dialog termination.

## Required tests / acceptance criteria
- Deterministically pause IO show before JNI entry then dispose
- Dispose while config.build runs under ASan/Valgrind
- Cancel each creation handoff boundary and count allocations/frees
- Repeated settings changes + double launch
- Launch immediately after composition
- Window closes with dialog visible

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
