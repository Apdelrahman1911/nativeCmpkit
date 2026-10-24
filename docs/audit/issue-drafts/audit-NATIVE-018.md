# [Medium][NATIVE-018] Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes

<!-- nativecmpkit-item:audit:NATIVE-018 -->
## Classification
- **Finding:** NATIVE-018
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:50-54`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L50-L54) — `remember JFXPanel initialization`

## Root cause
JFXPanel() is created synchronously inside remember. The first panel can bootstrap JavaFX and enter a nested AWT event loop while Compose is composing/rendering; archived issue346 shows exactly this stack path. There is no coordinated preinitialization or failure UI.

## Impact and preconditions
On affected runtime/host combinations first WebView composition may re-enter Compose rendering and throw Reentry into ignoringRedrawRequests. Missing graphics/native prerequisites can also abort toolkit startup, but their exact root causes differ.

## Supporting evidence
- Archived issue346 stack includes SwingInteropContainer reentry via JFXPanel.initFx and library WebView creation.
- Current source retains direct remember { JFXPanel() }. Issue344 setting-thread failure is different and has a source fix (Platform.runLater at215-221).

## Recommended solution
Reproduce on current supported hosts/Compose first. Establish a documented toolkit startup stage outside an active composition and an error/capability path; marshal UI objects to their required threads and preserve multiwindow lifecycle.

## Risks and compatibility
Historical stack is evidence of a reported prior failure, not proof that current Compose1.12 reproduces it. JavaFX19 classifiers/prerequisites are separately tracked by build findings. Do not blindly move JFXPanel construction to a worker thread.

## Required tests / acceptance criteria
- Cold first WebView creation during recomposition with FX initially uninitialized.
- macOS AWT/Metal and Linux X11/Wayland graphics matrices; repeated removal/recreation.
- Explicit unsupported/headless environment result rather than unexplained renderer exception.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/346
- https://github.com/MohamedRejeb/Calf/issues/39
- https://github.com/MohamedRejeb/Calf/issues/151
- https://github.com/MohamedRejeb/Calf/issues/344
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
