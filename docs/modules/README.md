# Module knowledge base

Source names below intentionally remain `calf-*`; published coordinates, if
separately authorized later, use `io.github.apdelrahman1911.nativecmpkit` and
`nativecmpkit-*`. See the [complete mapping](../migration/identity.json).
Public `com.mohamedrejeb.calf.*` packages, JNI exports and generated resource
names remain compatibility boundaries. **No new packages are published.**

## Read by subsystem

| Included module(s) | Main responsibilities and interfaces | Detailed implementation guide |
|---|---|---|
| `calf-core` | PlatformContext, composition locals, API opt-in markers | [Core/navigation/icons/sample](navigation-core-icons-sample.md) |
| `calf-io` | KmpFile constructors, metadata, bytes and RawSource; URI/NSURL/File ownership | [IO/picker/Coil](io-and-file-picker.md) |
| `calf-file-picker` | Launcher/settings/type models; gallery/documents/folders; saver; JNI/rfd; MIME/cache | [IO/picker/Coil](io-and-file-picker.md) |
| `calf-file-picker-coil` | Coil Fetcher, context conversion and eager file reads | [IO/picker/Coil](io-and-file-picker.md) |
| `calf-ui` | Adaptive controls, Material actuals, native alerts/sheets/bars, date/time models, Cupertino/glass gestures | [UI, every control and native manager](ui.md) |
| `calf-camera-picker` | Android ActivityResult/FileProvider and iOS UIImagePickerController capture | [Native features](native-features.md) |
| `calf-share` | ShareContent/Result, Android intents, UIActivityViewController, AppKit JNI, browser promises/fallbacks | [Native features](native-features.md) |
| `calf-webview` | WebContent/State/Navigator/Settings, Android/WK/JavaFX/iframe engines, every cookie store | [Native features](native-features.md) |
| `calf-permissions` aggregate | Compatibility exports of all feature modules | [Permissions/geo](permissions-and-geo.md) |
| `calf-permissions/core` | Permission registry, statuses, single/multiple state, platform dispatch and built-ins | [Permissions/geo](permissions-and-geo.md) |
| Permission features: `background-location`, `bluetooth`, `calendar`, `camera`, `contacts`, `gallery`, `location`, `microphone`, `notifications`, `wifi` | Each platform mapping, registration, usage key, OS-level prerequisite and helper | [Permissions/geo](permissions-and-geo.md) |
| `calf-cupertino-icons` | MIT font codepoints, icon text rendering, content semantics | [Core/navigation/icons/sample](navigation-core-icons-sample.md) |
| `calf-navigation` | Experimental route/back-stack controller, argument/saved-state types, expect/actual controller | [Core/navigation/icons/sample](navigation-core-icons-sample.md) |
| `calf-geo` | Coordinates, radius/distance, incomplete location tracker | [Permissions/geo](permissions-and-geo.md) |
| `calf-maps` | Included build-only scaffold, no map API | [Native features](native-features.md) |

This is **24 included library projects**; navigation, geo and maps do not apply
the publication plugin. The other **21** prospective artifacts include the
permission aggregate, core and all ten permission features.

## Samples, generated material and excluded experiments

- `sample/common`, `sample/android`, `sample/desktop`, `sample/web-js`,
  `sample/web-wasm` and the non-Gradle Apple app shell are reviewed in the
  [sample guide](navigation-core-icons-sample.md). Samples illustrate integration;
  they are not proof of production-ready export, permission, back-stack or lifecycle
  behavior. Their platform manifests/configuration have their own constraints.
- `calf-media` is excluded stale build configuration. `calf-notifications` is an
  excluded iOS scheduling experiment, not the included notification-permission
  module. Neither is a working supported product surface.
- Generated `SFSymbol` names in `calf-ui` are distinct from the bundled Cupertino
  font in `calf-cupertino-icons`. Name uniqueness/glyph mapping and license
  provenance were checked; this does not establish per-iOS-version SF availability.
- Convention plugins, build scripts and dependency APIs are explained in
  [build/security](../audit/build-security.md) and the
  [dependency map](../architecture/dependency-map.md).

## Locating a function without repeating the audit

1. Find the module here, then use that report's API sections and per-file ledger.
2. Use [execution flows](../architecture/execution-flows.md) to follow the common
   entry point through remembered state, native callbacks, coroutine boundaries
   and disposal.
3. Inspect [source-inventory.json](../audit/source-inventory.json) for immutable
   hashes/declaration locations and **candidate**, not compiler-certified,
   expect/actual matches.
4. Look up its finding ID in [the full index](../audit/findings-index.md). Read
   required tests and compatibility risks before modifying behavior.
5. Consult the [platform guide](../platforms/README.md), then execute only the
   documented tests available on your host. Do not claim an unavailable device run.

The guides document both successful existing behavior and defects. An absent
finding is not a promise that the corresponding function is correct under every
input, OS version, thread or lifecycle transition.
