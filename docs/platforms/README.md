# Platform capabilities: implemented is not verified

This matrix comes from baseline `af388bd` actual implementations and build
configuration, not the upstream README's platform badges. “Implemented” means a
code path exists; it does **not** mean all edge cases work, a native test passed,
or a package was published. See [testing](../testing/README.md) for actual runs.

## Target and host matrix

| Target | Declared by common convention | Important boundary |
|---|---|---|
| Android | AGP KMP Android library target | minSdk 23 / compileSdk 37 at baseline; sample minSdk 24 |
| Desktop | JVM named `desktop` | JVM 17; AWT/Swing + host-native libraries where used |
| Web JS | `js().browser()` | Browser target, not Node.js |
| Web WasmJS | `wasmJs().browser()` | Browser target; different typed-array/Promise/eval interop from JS |
| iOS device | `iosArm64()` | UIKit/Objective-C SDK, macOS/Xcode required |
| iOS simulator | `iosSimulatorArm64()` | Apple Silicon simulator; camera/device services may differ |
| iOS Intel simulator | **Not declared** | `iosX64` removed by PR #515; stale declarations in excluded projects do not restore support |
| macOS/Linux/Windows Kotlin/Native | **Not declared** | Do not confuse desktop JVM with native KMP targets |
| watchOS/tvOS/Android Native | **Not declared** | No implementation/verification claim |

The same target declaration is applied even to incomplete modules. Compiling a
stub is not a platform capability. Library target declarations are in
`convention-plugins/src/main/kotlin/Targets.kt:11-22`, Android setup in
`Android.kt:22-40`, and source-set groups in `Hirearchy.kt:10-32`.

## Feature matrix

Legend: **I** = implementation exists; **L** = intentionally limited/different
semantics; **S** = stub/no-op; **—** = absent/not applicable. Every I/L cell still
requires the corresponding audit findings and platform verification.

| Feature | Android | iOS | Desktop JVM | Web JS | Web WasmJS |
|---|---|---|---|---|---|
| Platform context | I: Context alias | L: sentinel | L: sentinel | L: sentinel | L: sentinel |
| `KmpFile` reads | I: ContentResolver | I: NSURL/copy | I: JVM file | I: browser File | I: browser File |
| `RawSource` | I: opened stream | I: filesystem source | I: filesystem source | L: whole-file buffering first | L: whole-file buffering first |
| File/document selection | I: system contracts | I: document picker | I: Rust/rfd JNI | I: file input | I: file input |
| Gallery/media selection | I: visual-media/document contracts | I: PhotosUI | L: file dialog, not gallery | L: file input | L: file input |
| Folder selection | I: document tree | I: document picker folder mode | I: rfd folder dialog | **S: returns empty list** | **S: returns empty list** |
| File saving/export | I: CreateDocument/write | I: export document controller | I: dialog then JVM write | L: download anchor, missing callback | L: download anchor, missing callback |
| Coil file adapter | I: whole-byte fetch | I: whole-byte fetch | I: whole-byte fetch | I: whole-byte fetch | I: whole-byte fetch |
| Camera capture | I: TakePicture + FileProvider | I: UIImagePickerController | **S: launch no-op** | **S: launch no-op** | **S: launch no-op** |
| Share text/URL/files | I/L: Android intents | I: activity controller | I macOS sheet; L Windows/Linux fallback | I/L: Web Share/clipboard | I/L: Web Share/clipboard |
| WebView | I: Android WebView | I: WKWebView | I/L: JavaFX 19 + Swing | L: iframe/same-origin rules | L: iframe/same-origin rules |
| Cookies | I/L: Android cookie store | I/L: WK cookie store | I/L: Java cookie handler | L: document.cookie | L: document.cookie |
| Adaptive controls | I: Material3 | I/L: UIKit + Compose Cupertino/glass | I: Material3, **not native desktop widgets** | I: Material3 | I: Material3 |
| Native bar integration | —: Material layout | L: host-controller overlays | —: Material layout | —: Material layout | —: Material layout |
| Permission requests | I/L: version/manifest dependent | I/L: helper/native-state dependent | **S: denied/no callback** | **S: denied/no callback** | **S: denied/no callback** |
| Geo tracking | **L: incomplete Android prototype; exposed states not fed** | **S: println/no updates** | **S: println/no updates** | **S: println/no updates** | **S: println/no updates** |
| Adaptive route navigation | L: common stack/back handler | L: common stack, no native gestures | L: common stack | L: no browser history sync | L: no browser history sync |
| Maps | **—: empty included project** | — | — | — | — |
| Media player | **—: excluded project, no implementation** | — | — | — | — |
| Notification scheduling | **—: excluded experiment** | — | — | — | — |

This is deliberately not a green/red “supported everywhere” table. For example,
the web library targets can build without implementing camera, while a native
mobile picker may exist but have confirmed correctness defects.

### Source evidence for unsupported/limited cells

- Camera: `calf-camera-picker/src/{desktopMain,webMain}/.../CameraPickerLauncher.*.kt`.
- Permissions: `calf-permissions/core/src/{desktopMain,jsMain,wasmJsMain}/.../
  MutablePermissionState.*.kt`, corresponding multiple-state implementations,
  and no-op feature registration actuals.
- Geo: five platform `LocationTracker` actuals under `calf-geo/src`; only Android
  creates real native updates, and those updates are not wired into public state.
- Maps/media/notifications: absence from relevant source trees and/or
  `settings.gradle.kts`; discussed in native-features report.
- Web IO/saving: `calf-io/src/webMain/.../KmpFileSource.web.kt` and
  `calf-file-picker/src/webMain/.../FileSaverLauncher.web.kt`, with separate
  JS/Wasm Blob interop helpers.
- Navigation: common `AdaptiveNavHostController`, platform `AndroidBackHandler`
  actuals, and absence of a native navigation-controller/browser-history adapter.
- UI: Material actuals in `materialMain` versus iOS implementations, including
  explicit ignored Material slots in native bar/alert contracts.

## Native desktop artifact matrix

Picker/share Gradle host mapping names these resource directories/triples:

| Directory | Rust target | Picker binary name |
|---|---|---|
| `macos-arm64` | `aarch64-apple-darwin` | `libcalf_filepicker_native.dylib` |
| `macos-x64` | `x86_64-apple-darwin` | same basename |
| `windows-x64` | `x86_64-pc-windows-msvc` | `calf_filepicker_native.dll` |
| `linux-x64` | `x86_64-unknown-linux-gnu` | `libcalf_filepicker_native.so` |
| `linux-arm64` | `aarch64-unknown-linux-gnu` | same basename |

Share uses the corresponding `calf_share_native` basename; availability of a
build task is not availability of a native share UI. Windows ARM64, 32-bit JVMs,
musl Linux and unusual `os.arch` aliases require explicit investigation. JavaFX
classifiers are constructed separately in `calf-webview/build.gradle.kts`; the
picker's host support does not establish the WebView's support.

## Platform guides

- [Android integration, lifecycle and tests](android.md)
- [iOS native objects, availability and privacy](ios.md)
- [Desktop threads, native packaging and tests](desktop.md)
- [Web JS/Wasm capabilities and browser restrictions](web.md)

Linux source inspection cannot prove an iOS release archive, macOS native dialog,
Windows installer or browser/device behavior. No platform badge in this document
overrides missing verification evidence.
