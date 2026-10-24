# [Medium][IO-023] Native parent-window pointers have unproven lifetime and thread-affinity guarantees

<!-- nativecmpkit-item:audit:IO-023 -->
## Classification
- **Finding:** IO-023
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt:24-38,46-54,62-74`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt#L24-L38) — `parentWindow.windowHandle acquisition`
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt:116-130`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt#L116-L130) — `IO-thread handle creation`
- [`calf-file-picker/native/src/lib.rs:105-128,139-162,179-187,218,246-247`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/native/src/lib.rs#L105-L128) — `ParentWindow/unsafe Send+Sync/build`

## Root cause
Rust stores raw window/display handles for reuse and unsafely asserts Send/Sync. macOS temporarily retains NSWindow and contentView during construction, then drops those Retained objects while storing only a raw NSView pointer. Creation can occur on Dispatchers.IO, including the AppKit contentView call and AWT/Compose handle retrieval. Lifetime comments are not enforced by ownership.

## Impact and preconditions
Window close/replacement or off-thread native access can yield stale handles or thread-affinity failures on affected platforms. Linux fabricates an Xlib handle/display hint and cannot represent all Wayland parents. No macOS/Windows/native-GUI failure was executed in Linux.

## Supporting evidence
- ParentWindow safety comments say the JVM AWT thread supplies a handle, but Kotlin constructs picker configs in Dispatchers.IO.
- macOS Retained values are local to from_raw_ptr; DialogConfig retains only ParentWindow raw fields.
- These are code-level precondition gaps; actual UI/backend behavior remains unverified.

## Recommended solution
Acquire platform handles on their required UI thread, retain owning native objects for the complete dialog session where needed, validate the supported Linux backend/handle kind, and release safely when dialogs/window sessions finish. Document unsupported ownership/modality combinations.

## Risks and compatibility
raw-window-handle borrowed lifetimes cannot be satisfied by comments alone. Main-thread dispatch must avoid deadlocks with rfd internal dispatch and Kotlin synchronous JNI calls.

## Required tests / acceptance criteria
- macOS main-thread checker during create/show/dispose
- Close/recreate parent while dialog opens
- Windows owned-dialog focus and parent destruction
- Linux X11 and Wayland portal parenting
- No-parent supported fallback

## Dependencies
- IO-003
- IO-017

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
