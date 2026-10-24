# Core, navigation, icon catalogues and sample applications

## Scope, baseline and confidence

Reviewed against **`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`** (imported Calf
main). All line numbers below refer to that immutable baseline, not subsequent
nativeCmpkit identity edits. Read a cited file with `git show <baseline>:<path>`.
Public `com.mohamedrejeb.calf` packages and `calf-*` Gradle paths remain intentional
compatibility boundaries. This review did not rewrite library implementations.

| Reviewed tree | Baseline tracked files | Review method |
|---|---:|---|
| `calf-core/` | 9 | All source/configuration; every common/actual declaration |
| `calf-navigation/` | 22 | All source/configuration, both existing tests, parser/bundle execution reproductions |
| `calf-cupertino-icons/` | 4 | Renderer/configuration, every generated declaration mechanically checked, binary font tables/provenance |
| `sample/` | 71 | All Kotlin/Swift, platform shells, Xcode/Gradle/manifests/HTML/resources, including commented prototypes |
| `calf-ui/.../sf/symbols/SFSymbol.kt` | 1 additional file | All 6,984 generated declarations parsed/uniqueness checked; UIKit consumption traced with UI reviewer |

The **106 files in the four assigned trees plus one additional catalogue** are
covered here. Generated identifiers were exhaustively checked as data; that is
not a claim of individually rendering 8,306 symbols or knowing every Apple glyph's
OS availability. UI component internals, file/native APIs and permission
implementations have separate module reports. See [audit analysis](../audit/navigation-core-icons-sample.md),
[findings](../audit/findings/NAV.json) and [tests/evidence](../testing/navigation-core-icons-sample.md).

## Build and API boundaries

| Project | Direct responsibilities/dependencies | Publication/status at baseline |
|---|---|---|
| `:calf-core` | Compose convention; Compose foundation for composition locals | Applies `module.publication`; deliberately tiny common API |
| `:calf-navigation` | Compose foundation/Material3; AndroidX navigation on Android; Kotlin test and desktop Compose test dependencies | **No publication plugin**; incomplete prototype, not a mature navigation framework |
| `:calf-cupertino-icons` | Compose convention/publication; Material3 text + Compose resource font | Published-library configuration, but artifacts not verified by this review |
| `:sample:common` | UI, file picker/Coil, permissions umbrella, WebView, adaptive navigation, camera, share, icons; Material icons, datetime, Coil/Ktor | Example library, not a release artifact; static iOS framework `Common` exports `calf-ui` |
| Sample Android/desktop/JS/Wasm shells | Platform launchers and distribution settings | Runnable examples, not proof of native functionality |
| `sample/ios` | SwiftUI/Xcode host invokes Gradle framework integration | Requires macOS/Xcode/signing configuration; not executable on this Linux host |

Common conventions target Android, desktop JVM, iOS device/simulator Arm64,
browser JS and browser WasmJS. There is no navigation-specific Kotlin/Native
macOS/Windows/Linux target. The sample has a second JetBrains navigation dependency
which source does not use (`NAV-016`); do not interpret its presence as the actual
navigation implementation. Toolchain and dependency compatibility belong to the
[build audit](../audit/build-security.md); the central architecture
map is authoritative for the complete Gradle graph.

## `calf-core`: all declarations and ownership

All core Kotlin files use `src/<set>/kotlin/com.mohamedrejeb.calf/core/`.

| File/symbol | Exact behavior and constraints |
|---|---|
| `commonMain/PlatformContext.kt:3` | `expect abstract class PlatformContext`; opaque host context contract, no filesystem, lifecycle, coroutine or UI-controller methods |
| `commonMain/LocalPlatformContext.kt:5` | Expects a `ProvidableCompositionLocal<PlatformContext>`; callers read the current host context during composition |
| `androidMain/PlatformContext.android.kt:5` | Actual typealias to `android.content.Context`; an Activity versus application Context is determined by the caller/composition, not by core |
| `androidMain/LocalPlatformContext.android.kt:5` | Actual getter delegates to Compose Android `LocalContext`; no globally cached Activity in this module |
| `nonAndroidMain/PlatformContext.nonAndroid.kt:3-10` | Actual abstract class with private constructor and a companion singleton used as a sentinel; **not** a UIKit view controller or desktop Window |
| `nonAndroidMain/LocalPlatformContext.nonAndroid.kt:5-8` | Static composition local defaulting to the sentinel; desktop/iOS/JS/Wasm share this behavior |
| `ExperimentalCalfApi.kt:3-15` | `@RequiresOptIn` at ERROR level, BINARY retention; class/function/property/getter targets; existing name is part of the compatibility surface |
| `InternalCalfApi.kt:3-15` | Same opt-in severity/retention; class/function/property/constructor targets (no property-getter target); source-level boundary, not a runtime access-control mechanism |

Execution is simply `LocalPlatformContext.current -> platform actual`. This module
creates no observers, native views, threads or closeable handles. No core-only
tests are present. Positive source checks: non-Android code does not pretend to
have an Activity; core introduces no mutable global context reference. Android
context storage used by convenience file APIs lives in **calf-io**, reviewed there.

## `calf-navigation`: implementation map

Common paths below are relative to
`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/`.

### Controller and save/restore

`AdaptiveNavHostController.kt:8-45` contains the actual controller used by the
sample on **every** platform:

1. `rememberNavController()` uses `rememberSaveable` with the custom `Saver()`.
2. `backStack` is a **public mutable** snapshot list of route strings; external
   callers can mutate/clear it and bypass any controller policy.
3. `currentDestination` returns `lastOrNull()`; there is no per-entry object.
4. `navigate(route, arguments)` only appends `route` (`NAV-001`). No graph lookup,
   schema validation, value storage, URI decoding, transitions, single-top or
   lifecycle-owner setup occurs.
5. `popBackStack()` returns false for an empty/single-item stack, otherwise removes
   its last item. This correctly protects the root through the method, but not
   through direct public-list mutation.
6. `Saver.save` stores a String array and `restore` constructs a new controller
   and adds those strings. It does not restore payloads, graph compatibility,
   entry owners or unique identities. Saveability of the surrounding Compose
   host still depends on the platform host; a saver is not universal process-
   restoration or browser-reload persistence.

The implementation assumes UI/Compose-compatible mutation. No threading contract
or background-mutation test exists; the audit does not infer a reproducible race
solely from the absence of synchronization.

### Host and graph execution

`AdaptiveNavHost.kt:13-64` performs these operations at one composition site:

```text
AdaptiveNavHost(controller, start, builder)
  -> AndroidBackHandler(enabled = stack.size > 1) -> popBackStack()
  -> remember { NavGraphBuilder().also(builder) }       [initial closures only]
  -> LaunchedEffect(Unit): navigate(start) if stack empty
  -> rememberSaveableStateHolder()
  -> SideEffect: remove saved routes no longer in stack's route set
  -> Box -> find first exact matching route
         -> SaveableStateProvider(key = route)
            -> destination.content(destination.arguments)
```

There can be an initially empty frame before the launch effect initializes an
empty stack. Unknown routes render no content and duplicate graph routes select
the first registration (`NAV-007`). The graph remembers initial builder closures
and the start effect ignores controller replacement (`NAV-006`). The state holder
preserves **`rememberSaveable`**, not arbitrary `remember` objects/resources. Its
route keys conflate different visits to the same route (`NAV-002`). The cleanup
correctly covers fully removed, distinct route names but cannot remove an
individual duplicate entry or detect a same-frame pop/revisit by route alone.

`NavGraphBuilder.kt:5-22` owns a mutable internal list. `addDestination` appends
without uniqueness checks; `composable` constructs `NavDestination`. The latter
(`NavDestination.kt:5-9`) contains route, a **definition** map of `NavArgument`, and
a composable receiving that definition map. It is not a destination instance
carrying resolved navigation values. Graph registration does not execute type
parsing or default merging.

### Argument and bundle APIs

`NavArgument.kt` owns a type, nullability, default and presence flag. `putDefaultValue`
(`23-27`) writes only when the flag is true. `verify` (`29-39`) rejects an explicit
null for a nonnullable key and catches `ClassCastException` from typed reads; it
does **not** reject an absent key by itself. The separate
`missingRequiredArguments` extension (`138-147`) filters nonnullable/no-default
definitions and calls the supplied missing predicate. Equality/hashCode compare
type/default/presence/nullability; array-default structural equality is not
provided. `toString` includes the default value: callers should not put secrets
in schema defaults or log them casually.

The builder (`74-127`) accepts `setType`, `setIsNullable`, `setDefaultValue`, then
unconditionally requires a nonnull default. This contradicts both the builder
contract and required-argument helper; it also fails to verify the default's type.
These are executable JVM defects (`NAV-003`), not just stale KDoc.

`AdaptiveBundle.kt:12` is an empty subclass of `AdaptiveBaseBundle`, not a
Parcelable, lazy parcel container or persistent serializer despite inherited
Android-derived documentation. BaseBundle's complete operation families are:

| Baseline range | Symbols and semantics |
|---|---|
| `8-22` | Public `mMap: MutableMap<String, Any?>`; unused `mOwnsLazyValues`/`mFlags` remnants; no `mParcelledData` implementation |
| `27-92` | `clear`, `containsKey`, generic `get<T>`, `getValue`, `remove`, `putAll`, `keySet`; `keySet` exposes the backing map key view and values are not copied |
| `95-109` | `putObject` supports null/Boolean/Int/Long/Double/String and corresponding Boolean/Int/Long/Double arrays, not all explicit setters |
| `118-217` | `putBoolean`, `putByte`, `putChar`, `putShort`, `putInt`, `putLong`, `putFloat`, `putDouble`, `putString`, `putCharSequence`; direct map writes |
| `228-250` | `putIntegerArrayList`, `putStringArrayList`, `putCharSequenceArrayList`; nullable lists with nullable elements retained by reference |
| `261-360` | `putBooleanArray`, `putByteArray`, `putShortArray`, `putCharArray`, `putIntArray`, `putLongArray`, `putFloatArray`, `putDoubleArray`, `putStringArray`, `putCharSequenceArray`; nullable mutable arrays retained by reference |
| `371-553` | Boolean/Byte/Char/Short/Int/Long/Float/Double getters, each with no-default and explicit-default overloads; missing/null/wrong concrete type returns the supplied/default primitive value |
| `564-582` | Both String getters convert arbitrary stored objects via `toString`, unlike the documented type fallback |
| `593-612` | CharSequence getters use checked `as? CharSequence` and fallback |

No array/list-specific typed getters or defensive copying are added beyond generic
`get`. JVM type erasure defeats the generic null-on-wrong-type promise (`NAV-004`).
The numerous JVM/Android terminology remnants are also a provenance and API clarity
gate (`NAV-018`), not evidence that native parcels are being deserialized unsafely.

### NavType: every built-in and shared helper

`AdaptiveNavType.kt` is a common abstract typed put/get/parse abstraction. Shared
members are `put`, `get`, `parseValue(String)`, `parseValue(String, previous)` (by
default replaces rather than merges), two `parseAndPut` overloads (`74-102`),
`serializeAsValue` (`105-117`, default `toString`), `name`, and `toString` (name).
The previous-value parse helper requires the key already exist; a null new string
returns the previous value without another write.

| Built-in and range | Parsing/storage |
|---|---|
| `IntType:287-307` | Nonnullable Int, decimal or `0x` hexadecimal; typed bundle access |
| `ReferenceType:316-336` | Integer-style parser/storage and name `reference`; not an implemented resource-resolution/XML system |
| `IntArrayType:346-366` | Nullable IntArray; a single parsed integer becomes a one-element array; previous array appended by copy |
| `LongType:377-404` | Nonnullable Long; strips uppercase `L`, then decimal/`0x` hexadecimal |
| `LongArrayType:414-434` | Nullable LongArray with element parser and append-by-copy |
| `FloatType:443-459` | `toFloat()` parsing; no range/finite-value policy beyond Kotlin parsing |
| `FloatArrayType:469-489` | Nullable FloatArray with append-by-copy |
| `BoolType:498-522` | Exactly lowercase `true` or `false`; invalid strings throw rather than silently becoming false |
| `BoolArrayType:532-552` | Nullable BooleanArray, same strict element parser |
| `StringType:561-595` | Nullable string; literal `"null"` parses as null; serialization does not implement documented URI escaping |
| `StringArrayType:605-627` | Nullable Array<String>; parses raw element strings, append-by-copy; explicit put/get implemented but runtime inference omitted |

`fromArgType` (`147-201`) resolves these names, defaults absent/empty type to String,
and rejects custom types. Its Parcelable/Serializable/enum reflection branches are
commented out. `inferFromValue` (`207-235`) tries Int, Long, Float, Bool then String;
parsing exceptions drive that small fixed sequence. `inferFromValueType`
(`244-276`) recognizes numeric/Boolean scalar and primitive arrays plus String,
but not String arrays. Repeated array accumulation is O(n²) total copied elements;
no production host route parser currently invokes it. `NAV-005` separates proven
helper failures from a hypothetical future deep-link/security risk.

### Expect/actual controller and back handler

| Target/files | Behavior |
|---|---|
| Common `NavHostController.kt:3-7` | Separate expect class plus navigate/pop extensions; not the type returned by the Adaptive factory on Android |
| Android `NavHostController.android.kt:3-13` | Typealias to AndroidX NavHostController; extensions delegate to members (member resolution prevents invented recursive-call claims) |
| iOS/desktop/JS/Wasm controller actuals | Typealias to AdaptiveNavHostController and delegate navigate/pop to members; JS file is misleadingly named `NavHostController.ios.kt` but belongs to `jsMain` |
| Common `AndroidBackHandler.kt:5-9` | Expected composable with enabled and onBack |
| Android actual `AndroidBackHandler.android.kt:6-14` | Delegates to `androidx.activity.compose.BackHandler` |
| iOS/desktop/JS/Wasm back-handler actuals `5-11` | Explicit no-op; no browser history, key listener or native interactive-pop implementation |

There are no per-entry lifecycle/ViewModel owners, native UINavigationController
navigation stack, back gestures, URL synchronization, deep links, transition
engine or typed route serializer in this implementation. These are capability
boundaries, not proof that every consumer requires those features. `NAV-008` asks
for a design decision before making the prototype a supported public product.

## Icon renderer, font and generated catalogues

`calf-cupertino-icons/src/commonMain/kotlin/com/mohamedrejeb/calf/cupertino/icons/`:

- **`CupertinoIcons.kt:3-1335`:** 1,322 public Int constants, 1,234 distinct
  codepoints. Multiple names intentionally alias a codepoint. All fit one Kotlin
  `Char`; the renderer's conversion is valid for these constants, not an arbitrary
  future supplementary Unicode scalar. Public `const val` values may be inlined
  by consumers; silently reassigning names has compatibility consequences.
- **`CupertinoIcon.kt:43-85`:** resolve a Compose resource font, convert size Dp to
  Sp using local density, remember the single-character string, create a fixed
  square Box and centered single-line Material Text with explicit font, tint,
  line-height and trim. An optional parent description and `Role.Image` are set,
  but the child Text semantics remain (`NAV-010`). `size.toSp()` means the explicit
  icon dimensions, rather than free-flowing typography, drive visual sizing;
  real font-scale/layout tests are still needed.
- **`rememberCupertinoIconsFontFamily:88-91`:** calls `Font(Res.font.sf_symbols)`
  then remembers `FontFamily(font)` keyed by the resource result. It is not a custom
  manual font-file reader or a newly allocated font family on every stable
  recomposition. Resource availability/cache behavior requires platform builds.
- **`composeResources/font/sf_symbols.ttf`:** 257,628-byte CupertinoIcons Version
  1.08 font, Regular, FontForge metadata; misleading resource filename does not
  make it Apple's proprietary SF Symbols font. Byte-for-byte match and its MIT
  notice are archived locally in `licenses/` (`NAV-009`).
- **`calf-ui/.../sf/symbols/SFSymbol.kt`:** 6,984 String name constants, unique names
  and values; passed to `UIKitImage.SystemName` / Apple's image API, not bundled
  Apple glyph outlines. Version1.0-7.0 catalogue claims have no per-symbol OS
  availability table or reconstructible generator (`NAV-011`). Missing UIKit
  symbols may yield a null image; this review does not call that an unconditional
  crash.

The font checker parsed all declared cmap4/6/12 tables it encountered: all 1,322
constants resolve to nonzero font glyph IDs; there are 1,274 nonzero Unicode cmap
mappings in total. The sample catalogue has exactly the 1,322 constants, unique
display names and no invalid references. Its nine category counts are General404,
Communication90, Objects147, Editing149, Shapes137, Media94, Devices48, Nature79,
Arrows174. These counts include escaped Kotlin identifiers correctly. They do not
validate glyph shape, semantic meaning, tint, antialiasing, accessibility, layout
or Apple runtime availability. Preserve the MIT license with distributed assets;
source-tree remediation is not packaged-artifact verification.

## Sample common application: entry and shared state

All common sample paths are under
`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/`.

`App.kt:11-21 -> CalfTheme -> setSingletonImageLoaderFactory -> remembered Adaptive
controller -> Material Surface -> AppNavGraph` is the entry flow. Theme names stay
compatible while the project identity changes. `navigation/Screen.kt` defines
four categories and **24 live Screen entries including Home**. Map and expandable
FAB entries are commented out. `ProfilePicture` deliberately routes to
`FileSaverScreen`. `AppNavGraph.kt:34-224` registers each live destination and
passes `popBackStack` callbacks; it does not use typed arguments. `HomeScreen`
groups these entries into a lazy categorized list, with `SectionHeader`,
`ShowcaseBanner` and `FeatureListItem` helpers; grouping each composition is a small
list operation, not a measured performance problem.

`components/SampleScreenScaffold.kt:20-54` centralizes a Material back button and
native iOS `UIKitUIBarButtonItem`, then passes scaffold padding to content. It is
an app sample wrapper, not a platform navigation lifecycle owner.

`coil/ImageLoader.kt:15-50` installs a Coil singleton factory. `newImageLoader`
registers `KmpFileFetcher.Factory`, reserves a **25%** memory-cache fraction and
enables crossfade; a debug logger is commented out. Ktor engines are Android/JVM
OkHttp, iOS Darwin, JS and Wasm-specific clients from the source-set dependencies.
The factory/global cache is intentionally wider-lived than a screen. File
fetching/native resource behavior is covered by the I/O/Coil reviewer; no network
load or cache-memory benchmark was completed here.

`ui.theme/Color.kt` holds Blue/Teal/Purple and light/dark surface constants;
`Theme.kt` defines DarkColorScheme, LightColorScheme, AppShapes and CalfTheme,
choosing the system dark-theme branch; `Typography.kt` supplies Material text
styles. The switches that say dark mode in illustrative screens do not rewire
the global theme. `Platform.kt` declares Android/iOS/Desktop/Web; five actuals
provide the corresponding values. Only the iOS actual uses `UIDevice`'s major
version >=26 to enable glass; all other actuals report false. This runtime check
is not a substitute for compiling against the required iOS SDK.

### Every sample screen and important helper

Ranges below identify the whole meaningful flow, not a claim that the demonstrated
native behavior was exercised on a device.

| File/symbol/ranges | Execution, state and review conclusions |
|---|---|
| `AdaptiveClickableScreen:20-68` | Demonstrates `adaptiveClickable` with local click-count feedback; common visual feedback is delegated to UI module; test semantics/keyboard parity in that module |
| `AlertDialogScreen:25-338` | Basic and single-button dialogs, iOS complex actions/text fields, action sheet; local `remember` flags drive presentation. The secure field logs values (`NAV-012`). Multiple platform slots describe equivalent examples, not shared UIKit/Compose text-field state. Non-scrolling content may crop on small/high-font-scale displays |
| `BottomSheetScreen:37-158` | `rememberSaveable` open state, `allowHide`/confirm-state gate, hide coroutine and completion visibility check; nested alert + 100-row LazyColumn. Review interactive dismissal and nested modal ownership on iOS; do not assume Android sheet behavior proves UIKit behavior |
| `ButtonScreen:40-229`, `SectionCard:205` | Counter; normal/disabled/filled/outlined/text buttons, icon examples and iOS26 glass branches. Several icon callbacks are intentionally no-op visual demonstrations, not wired product commands |
| `SwitchScreen:26-112`, `SwitchSettingItem:74` | Three local state toggles, including descriptive system-setting labels; does not change real Wi-Fi/notifications/theme |
| `SliderScreen:24-100`, `SliderSettingItem:69` | Three normalized slider states displayed in reusable setting rows; no actual volume/brightness settings integration |
| `ProgressBarScreen:21-84` | Three size/style variants, no background task or progress estimator |
| `DatePickerScreen:55-285` | `RangeOption` options; `WeekdaysOnly` UTC day predicate; remembered local today normalized to UTC midnight; inline/compact/range/wheels and selectable-date updates. NextThirtyDays endpoint is inclusive (today plus30 gives31 calendar dates). Today does not refresh at midnight without recreation. Helpers SectionDivider/SectionTitle/sampleDatePickerColors/toDateLabel format/present data; native date validation is reviewed by UI |
| `TimePickerScreen:22-66` | State initialized19:20, displays padded minutes; underlying 12/24-hour and timezone behavior requires UI/native tests |
| `DropDownScreen:41-287` | Top-bar menu, basic and sectioned menu data, expand/dismiss and action callbacks; native item descriptors versus Material content slots. Destructive metadata does not automatically style custom Material slots |
| `CameraPickerScreen:33-119` | Read platform context -> check/request Camera permission -> launcher after grant -> show path/image from callback. No assumption that desktop/browser no-op camera is functional; camera lifecycle/failure cases are in native-feature audit |
| `FilePickerScreen:52-345` | FileTypeOption/fileTypeOptions and PickedFileInfo; selected type/title/image representation, single/multiple/files/directory/initial-directory controls. Web directory control disabled. Selection updates display info, cancels previous streaming job and counts bytes; `describeStreaming`, `toPickedFileInfo`, `countBytes` detailed under `NAV-014`. Paths are displayed locally. `use` closes source and CancellationException is rethrown, but the inner loop is not cooperative |
| `ImagePickerScreen:37-138` | Separate single/multiple launchers, compatible/current image-representation controls, AsyncImage previews; `files.forEach` in scrollable Column eagerly composes every image (`NAV-013`) |
| `FileSaverScreen:71-245`, `circleCropImage:214` | Pick image -> preview and edit base name -> read all bytes -> full decode -> centered square circular clipping -> PNG encode -> saver launcher -> saved/cancelled status. No job serialization, input bounds or exception UI (`NAV-013`). A suspend read signature does not imply off-main I/O |
| `ShareScreen:36-175` | Editable text/URL/file selection -> remembered native share launcher -> Shared/Cancelled/Failed labels; wildcard MIME example. This is actual API exercise, unlike Showcase's fake clipboard status; native result accuracy belongs to native-feature audit |
| `PermissionScreen:53-207`, `MultiplePermissionsItem:119`, `PermissionItem:157` | 25 per-permission entries plus combined Camera/RecordAudio request, status/rationale UI and settings for notification case. Logs permission status, not credentials. Call/menu/manifest mismatch and unrelated broad declarations are `NAV-015`; iOS usage-key and registry behavior are in permissions audit |
| `WebViewScreen:28-239` | INITIAL_URL switches to Wikipedia for Web and an upstream GitHub demo otherwise; DUMMY_HTML is locally authored. Remembers state/navigator, enables JavaScript in an effect, displays loading overlay and back/forward/reload/stop/loadUrl/loadHtml actions with native/Compose toolbars. Remote-page trust, platform callback/state and embedded-view lifecycle are separate native-feature findings; a spinner is not proof of successful load |
| `NavigationBarScreen:74-942` | HomeTabContent74-362 (two dialog flags,30 lazy rows); FavoriteTabContent365-573 (static favorites); ProfileTabContent576-819 (sample profile and fixed-state switches); main824-942 initializes Favorite(index1), three tab items and300ms AnimatedContent. No per-tab saveable holder: local tab state can reset when content leaves composition, separately from navigation host retention |
| `ScaffoldDemoScreen:50-156` | Three tabs initial0, native SF names and Material vectors,300ms AnimatedContent; demonstrates composed top/bottom bars rather than a nested navigation stack |
| `TopBarDemoScreen:37-150`, `InfoCard:121` | iOS prefersLargeTitles, Material large title, two illustrative action callbacks, explanatory cards; nested scroll/collapse behavior delegated to UI |
| `ToolbarScreen:39-189` | SpacingPattern enumerates six native item-spacing arrangements; native items versus four Material action buttons; responsive FlowRow selection. Layout spacing is not native screenshot verified |
| `ShowcaseScreen:81-788` | Three local tabs Controls/Pickers/Overlays. `ShowcaseControlsTab:338` local counters/switches/sliders; `ShowcasePickersTab:546` dropdown/date/time; `ShowcaseOverlaysTab:681` alert/sheet triggers; `ShowcaseSectionHeader:743` and `ShowcaseCard:763` shared presentation. Topbar native and Material share callbacks only toggle a false-success clipboard dialog (`NAV-017`) |
| `CupertinoIconsCatalogScreen:53-248`, `IconGridItem:209` | Search/category filter via derived state, selected-icon panel, 72dp lazy grid keyed by unique name, small 8sp labels and content descriptions; data in CupertinoIconsCatalogData (1,322 entries/9 categories). Exhaustive identifier/font-data checks passed; search and render accessibility require UI tests |
| `MapScreen:24-67` | Unregistered placeholder unexpectedly requests Camera permission and contains no map integration. Screen enum route is commented out. **Not a supported map demonstration** |
| `ExpandableFABScreen:1-122` | Entire implementation commented out; no active function/route. Do not describe the file's existence as working expandable-FAB support |

### Image encoding actuals

`utils/ImageBitmapExt.kt:5` expects `ImageBitmap.toByteArray`.
Android (`ImageBitmapExt.android.kt:8-13`) obtains the Android Bitmap, encodes PNG
into ByteArrayOutputStream, ignores the encoder Boolean and returns a copy.
Non-Android (`ImageBitmapExt.nonAndroid.kt:8-16`) creates a Skia Image, encodes PNG,
force-unwraps encoded data and takes bytes; no deterministic Image/Data close
appears. Managed/native ownership and peak memory need inspection/profiling before
claiming a measured leak. These implementations are used by the saver sample,
not a promised streaming image-transformation API.

## Every platform shell and supporting resource

| Files | Implementation and limitations |
|---|---|
| `sample/android/build.gradle.kts` | Application plugin, Compose, namespace/application ID, SDK levels, Java compatibility, packaging exclusions and common project dependency; identity edits separately recorded by lead |
| `MainActivity.kt:1-25` | AppCompatActivity -> edge-to-edge -> Compose Material wrapper -> App; lifecycle/window behavior relies on Android host |
| `PermissionScreenPreview.kt:1-13` | Compose preview of PermissionScreen, not an instrumented runtime-permission test |
| `AndroidManifest.xml:1-68` | Camera hardware optional, network/media/location/Bluetooth/contacts/calendar/Wi-Fi/SMS declarations, backup disabled, exported launcher Activity, predictive-back setting, **nonexported** FileProvider with URI grants; permission matrix mismatch `NAV-015` |
| `res/xml/filepaths.xml:1-6` | Grants a cache path root (`.`) through the FileProvider; not world-readable storage by itself. Correct least privilege depends on which individual URIs are granted by camera/share code |
| `sample/desktop/build.gradle.kts` | Compose desktop JVM app, current-host runtime, DMG/MSI/DEB packaging; naming and OS icon/runtime expectations are configuration, not verified native installers |
| `sample/desktop/src/jvmMain/kotlin/Main.kt:1-20` | Enables interop blending, starts Compose Window, provides it through `ProvideFilePickerParentWindow`, calls App; correct ownership hook for modal desktop picker parent |
| `sample/web-js/build.gradle.kts`, `Main.kt:1-20` | JS browser executable; waits for Skia `onWasmReady` before ComposeViewport |
| JS `index.html:1-67`, `webpack.config.d/fs.js` | Host container/styles and compiled script reference; fs.js is empty, not an implemented filesystem shim |
| `sample/web-wasm/build.gradle.kts`, `Main.kt:1-17` | Wasm browser executable -> ComposeViewport directly |
| Wasm `index.html:1-99` | Host container/script and fallback warning/error handlers for unsupported Wasm compilation; no browser navigation/history bridge |
| `sample/common/src/iosMain/kotlin/Main.ios.kt:1-32` | `MainViewController` returns ComposeUIViewController{App}; UINavigationController experiment is commented out |
| `Second.ios.kt:1-101` | Entire older example commented; no active second host behavior |
| `sample/ios/Calf/CalfApp.swift:1-29` | SwiftUI App/WindowGroup -> UIViewControllerRepresentable -> shared MainViewController; no-op updateUIViewController; ignoresSafeArea at host |
| `sample/ios/Calf/ContentView.swift:1-26` | Unused Hello-world SwiftUI view/preview, not the shared application's implementation |
| `sample/ios/Calf.xcodeproj/project.pbxproj:1-404` | Gradle `:sample:common:embedAndSignAppleFrameworkForXcode` script, framework search/link/config settings and auto-signing references. Project settings name iOS26, **target settings override to18.5** at baseline314/361; do not report26 as the app minimum. Compile-SDK requirement differs from deployment target |
| iOS `Info.plist:1-32` | App identity and test-purpose privacy descriptions; newer calendar/Bonjour mismatches audited by permission reviewer, not inferred correct from key presence |
| `Assets.xcassets/**/Contents.json`, Preview assets | Asset catalogue metadata; app icon definition has no actual icon image filenames. Not a production-ready app icon set |
| Xcode workspace/check plist | IDE workspace metadata only; no iOS unit/UI-test target or scripted device evidence included |

Every Platform actual and both image actuals are covered above. The sample
framework's explicit `export(projects.calfUi)` is annotated upstream as necessary
for some iOS interop features; preserve it until an executable interop test proves
otherwise. Upstream developer signing identifiers are migration configuration,
not secrets to duplicate or evidence that the new owner can sign the app.

## Maintenance boundaries and next changes

1. Keep navigation unpublished; choose its API/lifecycle contract before a rewrite.
2. Fix arguments and entry identity together, then stale graph/route validation;
   preserve #542's two positive scenarios and add the uncovered cases.
3. Make bundle/type APIs honest and testable independently of Compose.
4. Keep font and derived-source licenses self-contained, verify artifact notices,
   and add deterministic catalogue generation and accessibility tests.
5. Remove sensitive demo logging and fake success text; make file demos bounded,
   cancellable and truthful about browser/native limitations.
6. Test platform shells on actual supported hosts/devices. Source inspection and
   ten pure JVM assertions do not establish release readiness.
