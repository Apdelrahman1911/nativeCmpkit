# Dependency and platform boundary map

Versions and declarations here are from `af388bd`, not a resolved SBOM. Successful
resolution, transitive vulnerabilities and host artifacts belong to the build
audit. Raw per-build-file declaration lists and the complete catalog are in
[source-inventory.json](../audit/source-inventory.json).

## Internal Gradle edges

| Consumer | `api(projects...)` edges | `implementation(projects...)` edges |
|---|---|---|
| `calf-core` | — | — |
| `calf-io` | `calf-core` | — |
| `calf-file-picker` | `calf-io` | — |
| `calf-camera-picker` | `calf-io` | — |
| `calf-share` | `calf-io` | — |
| `calf-file-picker-coil` | `calf-core`, `calf-io` | — |
| `calf-ui` | — | `calf-core` |
| Ten permission features | `calf-permissions-core` | — |
| `calf-permissions` umbrella | Core and all ten feature projects | — |
| WebView, navigation, geo, maps, icons | — | — |
| `sample/common` | `calf-ui` | File picker, Coil adapter, permissions aggregate, WebView, navigation, camera, share, Cupertino icons |

Transitive edges matter: selecting picker/camera/share exposes file and context
types; selecting every permission through the umbrella can introduce iOS API
references unrelated to the one permission an app intended to request. Gradle
artifact names of nested permission projects are renamed in settings, so
generated type-safe accessors read `projects.calfPermissions.calfPermissionsCore`
rather than the directory path. The maintained module paths are not Maven group
names.

## Direct runtime dependencies and why they exist

| Dependency at baseline | Direct consumers / use |
|---|---|
| Compose Multiplatform foundation/UI 1.12.0 | Most modules use runtime state/composition and foundation; UI types are visible in public APIs |
| Material3 1.12.0-alpha03 | UI controls/state/types, WebView's common UI context, navigation/sample; icons render via Material icon infrastructure |
| Compose resources 1.12.0 | Cupertino font loading; generated `Res` is a build output |
| kotlinx-coroutines 1.11.0 | UI/WebView common effects, Android main dispatcher, JVM Swing dispatcher, tests and sample; additional coroutine usage can arrive transitively |
| kotlinx-io 0.9.1 | `calf-io` exports `RawSource` (`api`); common consumers can stream without pretending content URIs are paths |
| Coil 3.6.2 | `calf-file-picker-coil` fetcher implementation; sample adds Compose rendering and Ktor network fetcher |
| kotlinx-browser 0.5.0 | Browser File/DOM/Promise APIs for IO, picker, share and WebView |
| Android activity-compose 1.13.0 | ActivityResult launchers and back handling used by Android integrations |
| Android documentfile 1.1.0 | Metadata for content/document URIs in IO |
| Android navigation-compose 2.9.7 | Separate Android `NavHostController` actual; kept on the minSdk-23-compatible line |
| Appcompat 1.8.0, lifecycle-extensions 2.2.0, play-services-location 21.4.0 | Android geo prototype's lifecycle/FusedLocation implementation |
| JavaFX base/graphics/controls/media/web/swing **19**, host classifier | Desktop WebView + Swing embedding; host-native libraries are not interchangeable across OS/CPU |
| Kyant backdrop 2.0.1 and shapes 1.2.1 | **iOS source set** glass/backdrop/shape implementation; previous vendored code was removed |
| Sample-only JetBrains navigation-compose 2.10.0-alpha02 | Catalogue's navigation dependencies; sample Android minSdk differs from library |
| Sample-only Ktor 3.5.2 | Image network fetching; OkHttp engines Android/JVM, Darwin iOS, JS and JS-Wasm browser engines |
| Sample-only kotlinx-datetime 0.8.0; material-icons-extended 1.7.3 | Demo dates and icons, not the file library's data model |

Where a public class extends or accepts an external type, changing only
`implementation` versus `api` may change downstream compilation; use consumer
compile tests and Kotlin metadata/API checks before changing scopes. Do not
infer a transitive dependency's exact selected version from this table.

## Desktop native dependencies

`calf-file-picker/native/Cargo.toml` builds a `cdylib` with `jni = 0.21`,
`rfd = 0.15`, `raw-window-handle = 0.6`; macOS adds `objc2 = 0.6` and
`objc2-app-kit = 0.3`. `calf-share/native/Cargo.toml` uses `jni = 0.21`;
macOS additionally uses `objc2`, `objc2-foundation`, `objc2-app-kit` and `block2`.
These semver ranges are declarations, not exact reproducible resolved graphs.
There is no baseline tracked `Cargo.lock` for either crate.

Picker's OS UI is `rfd` (Cocoa/Windows native dialog/Unix backend selected by its
dependency features). Share's macOS UI is handwritten AppKit integration;
Windows/Linux sharing uses JVM clipboard/browser/file-opening fallbacks rather
than that AppKit implementation. Host-name entries in build scripts do not prove
that a share sheet exists on those hosts. Desktop loaders first try the system
library path, then extraction/caching of packaged native resources; see the
security and ABI implications in the I/O/native/build findings.

The module Gradle tasks build current-host Cargo artifacts when prebuilt resources
are absent. The two modules repeat this logic. Native library basename, resource
path, Rust crate name and JNI symbol names are separate identities; an
uncoordinated namespace rename can compile Kotlin and still fail at load/call
time.

## SDK frameworks are dependencies too

- **Android:** `Context`, `ContentResolver`, `DocumentFile`, FileProvider,
  ActivityResult contracts, WebView/CookieManager, notification/settings APIs,
  runtime permissions, Google Play Services location. Apps own manifests,
  exported-component safety, permission requests and activity lifecycle.
- **iOS:** UIKit, Foundation, Photos/PhotosUI, UniformTypeIdentifiers,
  AVFoundation, CoreLocation, CoreBluetooth, Contacts, EventKit, UserNotifications,
  WebKit and NSNetService. Availability checks and Info.plist purpose strings
  are part of correctness, not merely integration documentation.
- **JVM:** AWT/Swing and JavaFX each have a distinct UI thread; JNI native dialogs
  add another ownership boundary. `Dispatchers.Main` on a Compose desktop app
  does not automatically mean JavaFX Application Thread.
- **Browser:** DOM file input, File/Blob/ArrayBuffer, iframe, document.cookie,
  user-activation/security rules, Web Share and clipboard APIs. JS and Wasm
  interop differ, but browser same-origin and permission restrictions do not.

## Build-tool graph

Root settings include the `convention-plugins` build and repository resolvers.
The baseline uses Kotlin 2.4.20, Compose plugin 1.12.0, AGP 9.4.0, Gradle wrapper
9.7.1, Java/JVM target 17, Foojay toolchain resolver 1.0.0 and Vanniktech publish
0.37.0. Build/publish signing credentials are external; their presence is not
needed to understand or archive the source and is never assumed. Native Rust,
Xcode SDKs, browser runtime/Skiko bundling and Android SDK 37 are additional host
requirements.

Upstream package aliases in the catalog are not proof they are still used; the
migration must audit consumer references instead of blindly downloading old
Calf packages. Independent Git history and metadata remove the GitHub-host
dependency, not the normal dependency on Maven, Cargo, SDK distributions or
third-party licenses. Never claim the project is an offline/vendored build
without recording and reproducing those additional artifacts.
