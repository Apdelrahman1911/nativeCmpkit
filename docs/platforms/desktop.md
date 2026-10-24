# Desktop JVM implementation guide

Desktop is the JVM `desktop` target with Java 17, not macOS/Linux/Windows
Kotlin/Native. Core/file code uses JVM APIs, adaptive widgets are Material3
Compose, picker/share can cross JNI, and WebView embeds JavaFX 19 through Swing.
That combination has several independent threading and native packaging models.

## Thread and lifecycle map

| Boundary | Execution constraint / audit concern |
|---|---|
| Compose/AWT/Swing | Host EDT/UI dispatcher; UI state and Swing panel insertion cannot be assumed safe from worker threads |
| JavaFX | `Platform.runLater` / FX Application Thread for engine/view/scene access, distinct from AWT EDT |
| File reads/writes | JVM blocking filesystem operations; `suspend` does not dispatch automatically |
| Picker JNI / rfd | Native dialog/parent handle lifecycle and per-platform UI dispatch; Kotlin cancellation does not automatically cancel/free safely |
| macOS share JNI | AppKit main-thread work, sharing-service completion and blocking Rust synchronization |

The current WebView correctly queues `applySettings` on FX, addressing old #344's
specific direct-EDT crash. It still constructs `JFXPanel()` during composition;
initializing JavaFX can enter a nested Swing loop, the scenario described by
#346. Startup, listener teardown, view disposal and callback behavior must be
tested independently. Do not treat `Platform.setImplicitExit(false)` as
per-view cleanup.

## Native picker and sharing packaging

Picker is JNI/Rust `rfd`; the old AWT/JNA implementation in historical commits
is not the current code path. PR #477 replaced it for features, native Linux
dialogs and reduced JNA overhead. Native handles are raw `Long` pointers;
concurrent disposal/launch is a memory-safety boundary, not just a coroutine
style issue. See the high-priority I/O findings before changing handle ownership.

Resources/build scripts recognize macOS x64/arm64, Windows x64, Linux glibc
x64/arm64. No Windows ARM64 or musl support is established. Check the exact host
binary in the resulting JAR; the presence of *one* prebuilt directory must not
be mistaken for a complete cross-platform publication. Baseline Rust semver
dependencies have no tracked lockfile, and build tasks can execute Cargo even
for JVM resource assembly.

Loaders prefer the system library path, then packaged extraction/cache. Picker's
cache uses content-sensitive names and non-replacement of identical binaries
(#540) to avoid Windows locked-DLL collisions. This is a source-verified fix
backed by a specific test file, not proof every cache/symlink/tamper/multi-process
case is safe. Audit system-path trust, extraction permissions, symbol compatibility
and cleanup. Preserve Kotlin/Rust JNI package names together.

macOS share uses NSSharingServicePicker. On Windows/Linux the share API generally
copies text or opens a URL/file via JVM facilities; that is not a Windows Share
contract or a Linux share-sheet standard. Completion “success” must reflect the
documented action rather than imaginary recipient delivery.

## JavaFX-specific prerequisites

`calf-webview/build.gradle.kts` explicitly includes six JavaFX artifacts at
version 19 using a host-derived classifier. Compose/Skiko's successful startup
does not prove JavaFX native libraries or its rendering pipeline work on the
same host. Historical #39/#47/#151 describe QuantumRenderer/toolkit failures,
including Ubuntu 24.04; verify libraries, architecture, display and graphics
environment before labeling any one application bug as the universal cause.

Headless CI can run selected pure JVM tests. Swing/Compose tests need a working
display or a correctly configured virtual display; real file dialogs, portals,
macOS window parentage and GPU/WebView paths need OS sessions. JVM installers
must include required runtime modules and host-native dependencies. The sample
has DMG/MSI/DEB targets and a macOS appearance JVM property, but no installer is
validated merely by that configuration existing.

## Explicitly missing desktop services

Camera launcher is a no-op. Permission states are permanently denied/no-op, not
automatically granted by the OS. Geo is a print-only stub. Adaptive navigation
has a common route stack with no native desktop back handling. UI is Material,
not AppKit/WinUI/GTK controls. Maps/media/notification scheduling have no active
implementation. Document these facts in consuming applications rather than
waiting indefinitely for callbacks that never arrive.

## Required verification

Test each OS/CPU separately: packaged native loading in clean JVM processes,
two applications using one library cache, repeated picker launch/disposal,
cancel during owner teardown, parent-window focus, unsupported host behavior,
permissions of cache/temp directories and very large file IO. Run WebView
startup/navigation/disposal on FX+EDT with no stale listeners. Real macOS share
completion/cancel and Windows file locking cannot be proven in a Linux-only
terminal audit; retain those limitations in release readiness.
