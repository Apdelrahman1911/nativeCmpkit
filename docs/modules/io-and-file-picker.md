# IO, file picker/saver, and Coil — implementation knowledge base

Reviewed baseline: **`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`**. Paths and line
references in the findings refer to this imported commit, not later migration
edits. Scope is all **62 tracked files / 5,360 physical lines** in `calf-io`,
`calf-file-picker`, and `calf-file-picker-coil`: 51 production Kotlin files,
one Rust file, three Kotlin test files, and seven build/resource/auxiliary files.
This is source-review coverage, **not executed platform coverage**.

Related: [audit](../audit/io-and-file-picker.md),
[machine-readable findings](../audit/findings/IO.json),
[testing](../testing/io-and-file-picker.md),
[architecture](../architecture/README.md).

## 1. Boundaries and dependency graph

```text
calf-file-picker-coil ──api──> calf-io ──api──> calf-core
        │                       └──api──> kotlinx-io-core
        └──implementation──> Coil 3 / its Okio integration

calf-file-picker ──api──> calf-io
        ├──implementation──> Compose foundation
        ├──Android──> activity-compose / AndroidX ActivityResult contracts
        ├──Desktop──> JVM IO + embedded Jodd MIME data
        │                └──JNI──> Rust DialogConfig + rfd + raw-window-handle
        └──Web──> kotlinx-browser + DOM File/Input/Blob
```

**Coil does not depend on the file-picker module.** Its fetcher accepts any
`KmpFile`, including manually constructed or camera-produced ones. IO exposes
`RawSource` publicly and therefore exports kotlinx-io as an API dependency. IO
also uses AndroidX DocumentFile on Android and browser bindings on Web.

Baseline dependency declarations: Kotlin 2.4.20, Compose 1.12.0, AGP 9.4.0,
kotlinx-io 0.9.1, kotlinx-browser 0.5.0, DocumentFile 1.1.0, Coil 3.6.2,
activity-compose 1.13.0, coroutines 1.11.0. Root/convention build analysis owns
resolution and compatibility verification; a version declaration alone is not a
successful build. `calf-file-picker-coil` declares Coil as `implementation` while
its public types implement Coil interfaces: consumers need compatible Coil APIs
on their own compile classpath; publication/API exposure deserves binary tests.

All three modules apply the shared target conventions: Android, JVM `desktop`,
browser JS, browser WasmJS, `iosArm64`, and `iosSimulatorArm64`. No `iosX64`,
Kotlin macOS, Kotlin Linux, or Kotlin Windows target is declared here. macOS,
Windows, and Linux are **desktop JVM hosts with Rust sidecar libraries**, not
additional Kotlin/Native variants. Android library minSdk is 23; sample settings
are not the library's compatibility guarantee. PHPicker and UniformTypeIdentifiers
are iOS-14-era APIs; runtime/deployment compatibility must be tested rather than
inferred from the sample's newer deployment target.

The compatibility packages remain `com.mohamedrejeb.calf.io` and
`com.mohamedrejeb.calf.picker[.coil]`. Retaining project paths and JNI symbols
does not imply a dependency on the upstream repository at runtime.

## 2. `calf-io`: representations and contracts

### Public API inventory

`KmpFile` is an expected opaque class in common code, with platform constructors
and conversion extensions. Context-taking extensions are `exists`,
`readByteArray`, `getName`, `getPath`, `isDirectory`, and `source`; `isFile` is a
common implementation. Each also has a context-free overload. There is no
baseline common constructor from a path/URI, length/MIME accessor, bookmark,
owned-temp-file disposal, write API, stable identity, or directory traversal API.

| Platform | Actual representation / constructors | Content and metadata behavior |
|---|---|---|
| Android | `KmpFile(uri: Uri)`; `Uri.toKmpFile()`; `java.io.File.toKmpFile()` converts via `Uri.fromFile` | Resolver stream for read/source; `DocumentFile.fromSingleUri` for name/kind; getPath returns a URI string; exists opens/closes a stream and catches any `Exception`. |
| Desktop | `KmpFile(file: java.io.File)`; `File.toKmpFile()` | `File.exists/isDirectory/name/path/readBytes`; source opens `SystemFileSystem.source(Path(file.absolutePath))`. Path may be relative for getPath but source uses an absolute path. |
| iOS | Public `KmpFile(url: NSURL)` / `NSURL.toKmpFile()`; two-URL constructor marked `InternalCalfApi` | `url` is the readable copy for picker-produced nonfolders; `originalUrl` is metadata identity. Exists/read/source use `url`, but name/path/kind inspect `originalUrl`. A manually wrapped URL is not automatically copied or granted access. |
| JS/Wasm | Shared `KmpFile(file: org.w3c.files.File)`; `File.toKmpFile()` | exists always true, name/path both File.name, directory guessed from absence of a dot; read uses platform FileReader implementation; source is a filled in-memory kotlinx-io Buffer. |

**Do not treat getPath as a portable filesystem path.** It is a URI on Android
and iOS, a basename on Web, and a filesystem path on desktop. `source()` is the
portable content route. IO-010, IO-014, and IO-019 detail metadata defects.

### Internal context resolution

`resolveContext` is expected internally. Non-Android actuals return
`PlatformContext.INSTANCE`. Android returns the application context from
`AndroidContextHolder`, a volatile singleton initialized through
`initializeKmpFileContext` (`InternalCalfApi`). The Android file-picker composable
initializes it. A context-free call made earlier throws a descriptive error;
the saver alone does **not** initialize it. Standalone IO users should pass a
context instead of depending on a UI initialization side effect.

The stored value is `context.applicationContext`, not an Activity, avoiding an
obvious static Activity leak. The check-then-set initializer is not atomic, but
normal competing initialization uses the same application context; no independent
cross-application race defect was established. Tests should reset/substitute
this global carefully rather than let one test initialize another accidentally.

### Reads and ownership

* Android read-all opens a resolver stream, calls `readBytes`, and closes only
  on success (IO-020). Its `source` wraps the stream in `asSource`; the caller owns
  closing it. A null opened stream becomes `FileNotFoundException`.
* Desktop read-all delegates to Kotlin's `File.readBytes`. `source` is streaming
  and caller-owned. The six desktop source tests exercise content, chunking,
  context-free delegation, missing/empty files and closure.
* iOS read-all loads the entire `NSData`, returns an empty array if loading
  failed, allocates a Kotlin byte array and calls `memcpy`. Its size/empty-buffer
  handling is unsafe (IO-001). `source` instead opens the readable URL's path
  through kotlinx-io and throws if no path is present. Security scope must last
  through consumption, not only opening (IO-008).
* JS/Wasm read-all starts FileReader and resumes in `onloadend`. Both allocate a
  typed-array view then copy element by element into ByteArray. Neither handles
  failure/cancellation correctly (IO-009). Web `source()` adds a Buffer copy;
  it is not a true browser stream, explicitly documented as such in common IO.

`suspend` does not imply a dispatcher switch. Native/JVM reads and source
consumption block the caller's thread; use a background dispatcher. Browser IO
is asynchronous but conversion/copy work still runs on the JS event loop.

## 3. Picker API and configuration semantics

`rememberFilePickerLauncher(type, selectionMode, settings, onResult)` returns a
stable launcher with `launch()`. Common output is a list: empty conventionally
means cancel, but baseline implementations also use it for unsupported folder
picking, provider/load errors, and some caught application errors. There is no
common error callback or busy/readiness signal.

`FilePickerFileType` is sealed and marked immutable:

* Image, Video, ImageVideo, Audio and Text contain corresponding MIME wildcards.
* Document means **`application/*`**, not every file commonly called a document.
* Presentation = ODP/PPT/PPTX MIME types; Spreadsheet = ODS/XLS/XLSX;
  Word = ODT/DOC/DOCX; Pdf is `application/pdf`.
* Folder uses the internal string sentinel `folder`, not a standard MIME type.
* All is `*/*`; Custom stores MIME strings; Extension stores suffixes. Lists and
  strings are not normalized/validated consistently across backends. Filters are
  chooser hints, **not content-security checks**.

`FilePickerSelectionMode.Single` is an object. `Multiple(maxItems: Int? = null)`
is open, with its companion extending `Multiple(null)` to preserve source syntax
`FilePickerSelectionMode.Multiple`. This compatibility detail matters when
adding validation or changing its representation. Limits are currently invalid
for some native values and inconsistent for zero/negative values (IO-018).

`FilePickerSettings` is an interface with title, initialDirectory, and a default
Compatible `imageRepresentationMode`. Common `FilePickerSettingsImpl` is a data
class, constructed by the same-name factory, `defaultFilePickerSettings`, or
`rememberFilePickerSettings`. The remember helper correctly keys all its inputs.
The desktop overload adds a `ComposeWindow?`; the extension `parentWindow`
returns nonnull only for its concrete `DesktopFilePickerSettings` implementation.

| Setting/capability | Android | iOS | Desktop | JS/Wasm |
|---|---|---|---|---|
| title | Ignored in picker/saver | Ignored in picker/saver | Used, with default picker title only | Ignored |
| initialDirectory | Used only for folder picker (parsed as Uri); saver/file picker ignore it | Ignored in baseline picker/saver | Used; per-save override takes precedence | Ignored |
| imageRepresentationMode | Ignored | PHPicker Compatible/Current only; capture can become stale | Ignored | Ignored |
| parent window | Platform ActivityResult host | LocalUIViewController host | Explicit settings > composition local; picker also has FrameWindowScope overload | Browser host |
| folder selection | One tree URI, even in Multiple | UIDocumentPicker folder URLs, possibly multiple | One folder via rfd | Unsupported, immediate empty result |
| limited multiple | Native media UI + some post-truncation | PHPicker native limit; document post-truncation | File result post-truncation | File result post-truncation |
| save completion | Callback after coroutine copy, subject to defects | Export delegate, subject to dismissal/access defects | Callback after filesystem write/copy | No callback: download only |

## 4. Android execution flows

### Open

1. Initialize the application-context holder, branch on Single/Multiple and type.
2. Image/Video/ImageVideo use PickVisualMedia or PickMultipleVisualMedia. The
   request mapper selects ImageOnly, VideoOnly or ImageAndVideo. An
   `ActivityNotFoundException` launches a separately registered OpenDocument /
   OpenMultipleDocuments fallback with visual MIME types.
3. Other nonfolders use OpenDocument / OpenMultipleDocuments. `toMimeTypes`
   resolves extensions using MimeTypeMap, adds CSV variants, deduplicates each
   extension's variants, and drops unknown mappings (an all-unknown request can
   become empty). Ordinary MIME types pass through directly. `isVisualMedia`
   exists as an internal helper but is not used by this file's branching.
4. Folders use OpenDocumentTree and the latest initial-directory URI. All results
   are wrapped without copying; no grant persistence or content validation runs.

AndroidX `rememberLauncherForActivityResult` handles callback updates and Activity
result registration. `rememberUpdatedState(type)` supplies the latest MIME
selection to retained launch lambdas. Android launcher constructor's type/mode
parameters are unused storage-wise; `launch` only invokes its callback.

### Save

CreateDocument uses the hardcoded `*/*` MIME and suggested `baseName.extension`.
Launch records either a ByteArray, KmpFile or intentional null. The Activity result
callback starts a composition-owned coroutine, copies on `Dispatchers.IO`, then
calls the updated result on the main scope. URI and java.io.File convenience
overloads delegate to KmpFile. Bytes-null implicitly means create-only.

Important constraints: lost pending state after recomposition (IO-002), nullable
stream false-success and no error channel (IO-006), no persistence of pending
in-memory content across process death, and no explicit concurrent-save policy.
The ignored `MimeTypeMap` import in this saver does not set the output MIME.

## 5. iOS execution flows

### Documents/folders

The nonvisual branch remembers a UIDocumentPicker delegate and updated type,
selectionMode and callback. Launch creates a fresh controller on the current
LocalUIViewController. Extensions map with `UTType.typeWithFilenameExtension`,
falling back to UTTypeData when empty. MIME mode maps wildcards explicitly or
uses `typeWithMIMEType`; its Document→UTTypeApplication mapping is incorrect
(IO-025). Nonfolder pickers request `asCopy=true`; folders request `asCopy=false`.

Single and multiple delegate variants are implemented. Document copies run on
Dispatchers.IO; callbacks return on Main. Multiple documents are staged
sequentially and only then truncated. Folders bypass copying. `createTempFile`
extracts an extension from the URL string, creates a UUID filename, invokes
NSFileManager.copyItemAtURL, discards NSError and returns null on failure.
Neither helper nor KmpFile owns eventual cleanup for picked copies (IO-013).

### Photo/video

PHPicker configuration sets images, videos, or their union; Video also includes
Live Photos. Compatible versus Current controls the requested asset
representation. Compatible is intended to improve HEIC interoperability with
Skia; it is not a proof every provider result is decodable. Single uses limit 1;
Multiple uses maxItems or Apple's unlimited sentinel 0.

Delegate completion creates an async task per PHPickerResult and `awaitAll`
preserves their input order. Each item loads through a cancellable
NSItemProvider bridge running on IO. Image requests UTTypeImage; Video requests
UTTypeMovie; mixed mode uses the first registered type or image fallback. Errors
return null and are filtered out rather than surfaced as partial failures.

**Positive lifetime detail:** the provider callback copies the supplied temporary
URL *inside that callback*, before resuming the continuation. Moving that copy
after callback return would reintroduce the historical provider-temp-URL expiry
bug. Cancellation calls NSProgress.cancel; it does not reclaim a copied file
whose coroutine result is later abandoned. The AtomicInt completion guard only
protects empty results, not duplicate nonempty ones (IO-007). A separate adaptive
presentation delegate catches photo swipe-dismissal, unlike document/save paths.

### Save

The ByteArray overload guards empty arrays before pinning (a positive contrast
to IO read-all), builds NSData and dispatches `writeTempFile` to IO. NSData
overloads bypass the Kotlin ByteArray conversion. Staged URLs are added to a
remembered list, then an export controller is presented on Main. KmpFile/NSURL
overloads bypass staging and present the original URL directly. Delegate methods
remove pending temp files and call the current result; cancellation returns null.

The source-move / filename bug (IO-005), unchecked write Boolean (IO-006),
interactive dismissal gap (IO-007) and external destination scope (IO-008) are
separate from the positive guard against empty-array pinning. Cleanup only
exists for the saver list; no automatic cleanup on composition disposal or
failed presentation is installed.

## 6. Desktop execution flows and native ownership

### Compose layer

Top-level picker resolves parent from explicit desktop settings, then
LocalFilePickerParentWindow. `FrameWindowScope.rememberFilePickerLauncher` uses
its window if none is explicit. `ProvideFilePickerParentWindow` supplies a
composition local for nested UI. The internal picker remembers a mutable long
handle, coroutine scope, callback/type state, and Mutex.

LaunchedEffect destroys an old config and creates a new one off-thread when
type/mode/title/directory/parent changes. `launch` acquires the mutex, reads the
handle, shows a dialog on IO, wraps paths as Files/KmpFiles, and truncates results.
If creation is not complete it returns silently. Disposal destroys the raw handle
without acquiring the mutex (IO-003). The maxItems capture is stale (IO-017).

Saver creates one native config per invocation, shows/writes on IO, and destroys
the config in `finally`. It has better allocation pairing than the remembered
picker but still has no error callback or concurrency policy; creation and first
native loading can occur on the main composition coroutine before IO dispatch.
It reads updated title/directory but retains the initial resolved parent window.

### PlatformFilePicker

`warmup` calls the JNI init no-op; no module caller invokes warmup in the reviewed
sources. `createFilePickerHandle` resolves MIME extensions and passes parent
windowHandle, `createDirectoryPickerHandle` has no extension filter, and
`createSaveDialogHandle` supplies suggested filename and one extension.

The three show paths call JNI on Dispatchers.IO. File/directory results become
`java.io.File` wrappers. Save-bytes writes with File.writeBytes or createNewFile;
save-file invokes File.copyTo(overwrite=true). JNI does **not** write files: all
desktop data writes occur in this JVM layer. That distinction makes IO-004
testable without a native dialog. `destroyDialog` forwards the handle unchanged.

### Loader/cache

1. NativeFilePickerBridge object initialization loads the library once per class
   loader. The external `init` symbol itself does no work.
2. Try System.loadLibrary(`calf_filepicker_native`) first for external packagers.
3. Determine OS (`macos`, `windows`, `linux`) and arch (`arm64`, `x64`) from system
   properties, find `native/<os>-<arch>/<libname>` in classpath resources, read
   all bytes, and hash with SHA-256 truncated to 16 hex characters.
4. Use `~/.cache/calf-filepicker/<library>-<hash>.<extension>`. Reuse an existing
   same-length/same-hash file unchanged; otherwise create a unique temp file,
   write bytes, try atomic replacement and then plain replacement. If both fail,
   load the unique temp file and schedule deletion on exit.
5. System.load the selected absolute path. A missing resource or unsupported
   host is a hard initialization error; load/extraction errors are not a picker
   cancellation. Multiple custom classloaders and different external native ABI
   versions require integration tests.

Positive: the picker cache is content-addressed and specifically avoids replacing
identical Windows-loaded DLLs; all lightweight cache characterizations passed.
Do not confuse it with any older constant-name cache elsewhere in the repository.
Remaining hardening is deployment-dependent IO-022, not a demonstrated remote
execution vulnerability.

### Rust helpers and exports (entire `native/src/lib.rs`)

| Lines / symbols | Implementation and reviewed invariants |
|---|---|
| 16–21 `jstring_to_string` | Null→None; JNI get_string failure→None. It suppresses a Rust result, not necessarily a pending JVM exception; callers should not assume every None is a null input. |
| 24–37 `jstring_array_to_vec` | Length read or zero, preallocated Vec, iterate JNI elements, convert strings, explicitly delete each element local reference. Successful local-reference cleanup avoids exhausting JNI refs on large lists. Errors may be silently skipped. |
| 40–58 `paths_to_jstring_array` | Find String class, allocate Java array, convert each path/string, set element, delete temporary string ref; returns JNI Result. Path count casts to i32 without a bound check, but billions of chooser results are not a realistic demonstrated input. |
| 61–69 `path_to_jstring` | Single path conversion returns null on new_string failure; both path helpers use lossy Unicode fallback (IO-024). |
| 72–99 `throw_runtime_exception`, `catch_panic_and_throw` | Catch Rust unwind and throw Java RuntimeException, returning a sentinel. Raw JNIEnv pointer is used inside catch_unwind. OOM aborts, invalid memory dereferences and stale raw window pointers are not cured by panic catching. Exception translation when a JVM exception is already pending needs JNI fault-injection tests. |
| 107–129 `ParentWindow`, Send/Sync, handle trait implementations | Raw window/display storage, unsafe borrowed handles; safety depends on external lifetime/thread contracts (IO-023). |
| 134–199 `ParentWindow.from_raw_ptr` | Zero→None. macOS interprets pointer as NSWindow, temporarily retains it, gets contentView and stores NSView pointer. Windows uses nonzero HWND; Linux uses Xlib window ID and no display pointer; unsupported OS→None. The Linux comment assumes GTK, but archived rfd 0.15.4 resolution selects xdg-portal + async-std; backend operation remains unverified. |
| 206–219 `DialogKind`, `DialogConfig` | PickFiles stores multiple flag, PickDirectory stores no count, SaveFile stores optional default name. Config owns title/directory/extension Strings and optional raw parent, not a persistent native dialog object. |
| 223–251 `DialogConfig.build` | Construct a **fresh** rfd FileDialog for every show; set title/directory, build extension-ref list for `Selected types`, optional default save name and parent. Reusing a handle reuses config, not UI state or a thread-safe native dialog session. |
| 255–272 `box_config`, `ref_config`, `drop_config` | Box into raw pointer-as-jlong, unchecked dereference to static reference, and reconstruct/drop Box. No type/generation registry, zero check in show, ownership counter or use-after-destroy protection. |
| 281–285 JNI `init` | No-op, primarily exists for eager loader invocation. |
| 291–316 JNI `createFileDialog` | Convert title/directory/extensions and JNI_TRUE multiple flag, construct parent, box config; panic fallback 0. |
| 322–339 JNI `createDirectoryDialog` | Directory kind, empty extensions, optional parent; panic fallback 0. |
| 345–367 JNI `createSaveDialog` | Save kind, default filename and optional nonempty one-extension list; panic fallback 0. |
| 374–397 JNI `showFileDialog` | Unchecked borrow, build fresh rfd dialog, choose pick_files or pick_file by kind; cancellation→empty Vec; wrong kind→empty Vec. Array conversion errors throw RuntimeException. |
| 403–417 JNI `showDirectoryDialog` | Unchecked borrow/build, pick_folder; null for cancel or string creation failure. Does not verify config kind. |
| 423–437 JNI `showSaveDialog` | Unchecked borrow/build, save_file; returns **path only**, does not create/write destination. Does not verify config kind. |
| 443–453 JNI `destroyDialog` | Ignores zero; every nonzero value is assumed an owned, not-yet-freed Box. Repeated destruction is invalid. |

JNI symbol names encode the retained Kotlin package/object name. Namespace
renaming requires coordinated Kotlin, Rust and packaged-library changes plus
binary tests; a search-and-replace rename alone is unsafe. The bridge object is
internal API, but raw-pointer misuse can still originate from library lifecycle
bugs; it need not be an external caller passing malicious addresses.

## 7. Browser picker/saver and bitmap conversion

JS and Wasm picker files contain nearly identical DOM implementations, with
platform binding differences rather than a different selection algorithm.
Every launch creates a hidden input, sets accept/multiple, attaches change/cancel
handlers, appends to body and clicks synchronously (important for user activation).
Selection lists are truncated and wrapped; a fresh input permits reselecting the
same file. Cleanup removes the node after events. Unsupported Folder immediately
returns an empty list. No input is retained for disposal and `fileDialogVisible`
is never set true (IO-026).

Web saver uses `createBlob` for ByteArray, existing File directly for KmpFile, or
a native Blob overload. JS copies bytes into Int8Array then takes an unsigned
view; Wasm converts ByteArray→UByteArray→Uint8Array. The bit patterns are preserved
by signed/unsigned byte representation, but copies are not free. MIME selection
is a small `extensionToMimeType` switch (PDF/text/CSV/JSON/XML/HTML/images/MP3/MP4/
ZIP/Office) with octet-stream fallback. It creates an object URL, clicks a hidden
download anchor and revokes immediately. Completion and lifetime limits are
IO-011/IO-012; no true browser save picker exists in baseline.

`ByteArray.toImageBitmap()` is an expect API supplied by all five platform source
sets. Android `toAndroidBitmap` delegates to BitmapFactory.decodeByteArray and
requires a nonnull decode result with a useful exception message. Desktop/iOS/
JS/Wasm use Skia Image.makeFromEncoded→toComposeImageBitmap. These are synchronous
full-image decodes with no requested dimensions or streaming path. Invalid data,
oversized encoded images and unsupported HEIC need platform decoder tests; a
ByteArray conversion helper is not an image validator, and no memory benchmark
or decoder CVE assessment was inferred from these wrappers alone.

## 8. Jodd utilities and resources

The embedded Jodd code/resources retain a two-clause BSD-style notice. Keep that
notice in source and binary redistributions in addition to Calf's Apache-2.0
attribution. The code is internal but remains compiled as `jodd.*` JVM classes;
classpath collision tests are prudent for applications also using Jodd.

* `IOUtil.close` accepts null, flushes Flushable first, ignores IOException from
  flush, then always tries close and ignores close IOException. Runtime exceptions
  are not swallowed; this is only used for the MIME resource in the scope.
* `MimeTypes` eagerly loads its `.properties` on first object use, expands short
  MIME prefixes and fills an extension→MIME LinkedHashMap, rejecting duplicate
  extensions. Missing/unreadable resources are hard initializer failures, not
  silently unfiltered pickers. Every one of **763 records / 981 extensions** was
  parsed by the execution probe without a duplicate-extension initialization
  failure. Property order is not a stable semantic ordering promise.
* `registerMimeType` mutates the map without normalization/synchronization;
  `getMimeType` provides octet-stream fallback; `lookupMimeType` lowercases with
  default locale; `isRegisteredExtension` uses exact case. No production caller
  of register/isRegistered was found in this module.
* `findExtensionsByMimeTypes` lowercases with default locale, splits only on
  comma-space, scans all extensions, invokes an unused findAnyOf, and selects
  either Wildcard.matchOne or indexOf. This explains both IO-015 and IO-016.
* `Wildcard.match` supports `*`, `?`, escaped wildcard literals and treats `**`
  like `*`. Private recursive matching backtracks from the end for every star;
  `matchOne` returns the first matching pattern index or -1. It does not have a
  distinct deep-directory separator algorithm despite the class comment's path
  language. Ordinary current MIME patterns are short; pathological custom
  wildcard complexity is a bounded-input testing/optimization concern, not a
  demonstrated exposed denial-of-service vulnerability.

## 9. Build/native-resource boundary

`calf-io` and Coil apply the Kotlin/publication conventions; picker additionally
applies Compose. Only IO/picker declare test dependencies here. No Android, iOS,
JS, Wasm, Coil or Rust test source exists in these three baseline modules.

Picker Gradle checks whether **any** nonempty platform resource directory exists;
if not, desktopProcessResources depends on copyNativeLib→buildNativeLib. Cargo is
invoked for the current supported host in release mode and always considered
out-of-date. Native output is attached as a resource root. When prebuilt content
exists, the local build is skipped without verifying every required target.

Cargo package version is 0.14.0, edition 2021, cdylib. Dependencies are jni 0.21,
rfd 0.15, raw-window-handle 0.6, and macOS objc2 0.6 / objc2-app-kit 0.3. Release
uses size optimization, LTO, stripping and one codegen unit; unwinding is not
explicitly disabled. Cargo.lock is ignored, so a future build can resolve
different compatible transitive versions. Neither library availability nor a
known vulnerability can be decided from these declarations alone.

The shell build-all-targets helper builds macOS arm64/x64, Windows x64 and Linux
x64 into source resources. Host Gradle also recognizes Linux arm64, while loader
path selection generically recognizes arm64 Windows. Shipped resource matrix,
incremental builds, deterministic locks, ABI checks and artifact provenance are
owned by the [build audit](../audit/build-security.md) when integrated; do not
duplicate its packaging issues here. No releases/packages were published for
these probes.

## 10. Complete per-file review ledger

The table below is part of this review, not a filename-only enumeration: each
entry identifies the actual symbols/behavior inspected. All paths are relative
to the repository root and refer to the baseline. Detailed failure evidence and
required tests live in `docs/audit/findings/IO.json`.

| Baseline file | Reviewed range | Symbols, flow and review result |
|---|---|---|
| `calf-file-picker-coil/build.gradle.kts` | 1–12 | KMP/publication; API core+IO; implementation Coil exposes fetcher interfaces through public types; no picker dependency or tests. |
| `calf-file-picker-coil/src/androidMain/kotlin/com.mohamedrejeb.calf/picker/coil/KmpFileFetcher.android.kt` | 1–6 | toCalfPlatformContext actual returns Android Coil context unchanged; it does not depend on global AndroidContextHolder initialization. |
| `calf-file-picker-coil/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/coil/KmpFileFetcher.kt` | 1–44 | toCalfPlatformContext expect, KmpFileFetcher.fetch, nested Factory.create: unconditional readByteArray→Okio Buffer→ImageSource, null MIME, MEMORY source; size/caching/close implications (IO-021). |
| `calf-file-picker-coil/src/nonAndroidMain/kotlin/com.mohamedrejeb.calf/picker/coil/KmpFileFetcher.nonAndroid.kt` | 1–6 | toCalfPlatformContext actual uses singleton PlatformContext.INSTANCE across desktop/iOS/web; no native context conversion side effect. |
| `calf-file-picker/build.gradle.kts` | 1–103 | API IO + Compose/Activity/browser/test dependencies; host target mapper; any-prebuilt bypass; buildNativeLib/copyNativeLib/resources task wiring. Build audit owns lock/matrix/reproducibility findings. |
| `calf-file-picker/native/.gitignore` | 1–2 | Both /target and Cargo.lock ignored; output hygiene positive but ignored lock prevents reproducible cdylib transitive resolution. |
| `calf-file-picker/native/Cargo.toml` | 1–22 | cdylib package0.14.0, edition2021; jni/rfd/raw-window-handle and macOS objc2 dependencies, size/LTO/strip/codegen profile; no explicit lock/toolchain or native tests. |
| `calf-file-picker/native/build-all-targets.sh` | 1–66 | set-euo-pipefail; build_target cargo→copy→size; all/macos/windows/linux selectors; macOSarm64+x64, Windowsx64, Linuxx64 only; cross-toolchain prerequisite not installed by helper; unknown selector not rejected. |
| `calf-file-picker/native/src/lib.rs` | 1–453 | All helpers, parent handle impls, DialogKind/DialogConfig, box/ref/drop and seven JNI exports plus init reviewed individually in section6 table; ownership/UTF-8/exception/threading findings IO-003/023/024. |
| `calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/ComposeResource.android.kt` | 1–14 | toImageBitmap→toAndroidBitmap→BitmapFactory.decodeByteArray; requireNotNull rejects corrupt/unsupported data with explicit message; synchronous full decode. |
| `calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.android.kt` | 1–321 | All seven composable entry/helper paths; ActivityResult callbacks/fallbacks; type/mode routing; CSV MIME map; toMimeTypes/toVisualMediaMimeTypes/toPickVisualMediaRequest/isVisualMedia; launcher delegation. IO-018/019. |
| `calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt` | 1–146 | remember saver; pendingSource capture, CreateDocument callback/coroutines, ByteArray/KmpFile/Uri/File overloads; null stream handling/ignored settings/MIME; IO-002/006. |
| `calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/ComposeResource.kt` | 1–5 | ByteArray.toImageBitmap expected synchronous conversion API; no error/size/context policy specified. |
| `calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.kt` | 1–171 | rememberFilePickerLauncher expect; every FilePickerFileType object/MIME constant, Custom/Extension, selection Single/Multiple(maxItems) companion compatibility, FilePickerLauncher constructor/launch; IO-018/025. |
| `calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerSettings.kt` | 1–112 | FilePickerSettings interface/default representation, ImageRepresentationMode enum, FilePickerSettingsImpl, same-name factory/default/remember helper; helper keys complete, backend support differs. |
| `calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.kt` | 1–62 | Experimental rememberFileSaverLauncher and both launch overloads, bytes-null empty-file and streaming-file contracts, result/cancellation docs; IO-004/006/011 compare implementations. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/ComposeResource.desktop.kt` | 1–8 | toImageBitmap actual uses Skia Image.makeFromEncoded→toComposeImageBitmap; synchronous full decode, runtime codec/heap limits remain unverified on this target. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt` | 1–187 | Top-level and FrameWindowScope parent resolution, internal LaunchedEffect handle replacement, DisposableEffect free, Mutex show, readiness early-return, stale maxItems, launcher delegation. IO-003/017. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerParentWindow.kt` | 1–39 | LocalFilePickerParentWindow nullable static local and FrameWindowScope.ProvideFilePickerParentWindow scoped provider; explicit settings override in callers; no global native pointer ownership. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerSettings.desktop.kt` | 1–57 | DesktopFilePickerSettings data class; factory and remember overload include representation+parent; parentWindow cast extension returns null for other implementations; parent lifetime belongs to caller. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.desktop.kt` | 1–119 | Remembered byte/file launch paths allocate per-call handle, show/write then finally destroy; updated callback/settings but stale parent; File overload delegates; initial native load may run on UI scope. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeFilePickerBridge.kt` | 1–86 | Object initialization→loader; static JNI init/createFile/createDirectory/createSave/showFile/showDirectory/showSave/destroy signatures reviewed against Rust exports; internal raw Long contract. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCache.kt` | 1–71 | nativeLibraryContentHash, filename insertion, extractNativeLibrary, hasIdenticalContent, moveReplacing; short SHA cache naming, identical reuse, unique temp/atomic+plain move/fallback deletion. Original six tests and additional probes passed. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibLoader.kt` | 1–70 | loadNativeLibrary system-first/classpath fallback/hash/cache/System.load; bundledLibraryLocation OS/arch mapping; userCacheDir fixed fallback; init error policy, IO-022 hardening. |
| `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt` | 1–146 | warmup; three handle factories; picker/directory/save byte/save file show functions; destroy; resolveExtensions. Real file-write/filter code executed with fake JNI selection (IO-004/015). |
| `calf-file-picker/src/desktopMain/kotlin/jodd/io/IOUtil.kt` | 1–56 | BSD notice; IOUtil.close handles null, flush-before-close and IOException suppression while still closing after flush IOException; no broader shutdown/resource owner. |
| `calf-file-picker/src/desktopMain/kotlin/jodd/net/MimeTypes.kt` | 1–168 | BSD notice; constant set and eager Properties→extension map; duplicate-extension reject; register/get/lookup/find/isRegistered functions; 981-entry initialization passed; IO-015/016. |
| `calf-file-picker/src/desktopMain/kotlin/jodd/util/Wildcard.kt` | 1–142 | BSD notice; public/private match recursion and matchOne first-index behavior, star/question/escape/double-star/empty matching; positive probe and recursive complexity review. |
| `calf-file-picker/src/desktopMain/resources/jodd/net/MimeTypes.properties` | 1–789 | All763data records/981extensions parsed; abbreviated MIME expansion, no duplicate extensions, legacy media/Office categories and missing AVIF/HEIC/HEIF identified; original BSD resource notice retained. |
| `calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCacheTest.kt` | 1–103 | Six original tests: filename insertion, deterministic16hexhash, new extraction, reuse timestamp unchanged, changed-byte replacement, nonempty-directory blocked-target temp fallback; Before/After temp isolation; all executed. |
| `calf-file-picker/src/desktopTest/kotlin/jodd/net/MimeTypesTest.kt` | 1–77 | Three original tests: scalar/fallback lookups, exact/multi-type extensions, wildcard image set; no locale/unknown-format/adversarial cases; all executed unchanged. |
| `calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/ComposeResource.ios.kt` | 1–8 | toImageBitmap actual uses Skia Image.makeFromEncoded→toComposeImageBitmap; synchronous full decode, runtime codec/heap limits remain unverified on this target. |
| `calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt` | 1–374 | All document/photo entrypoints and delegates, settings/state capture, AtomicInt guard, adaptive photo dismissal, NSItemProvider suspension/progress cancel/copy, UTI/controller builders, launcher. IO-007/008/013/017/018/025. |
| `calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt` | 1–228 | All byte/file/NSData/NSURL paths, launchWithData, remembered delegate/list, writeTempFile, cleanUpTempFiles, presentExportPicker, overload forwarding; empty pin guard positive; IO-005/006/007/008. |
| `calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/TempFile.kt` | 1–26 | NSURL.createTempFile copies synchronously into UUID+extension NSTemporaryDirectory and returns null on NSError-discarded failure; original-name/ownership/cancel-copy limitations (IO-013/014). |
| `calf-file-picker/src/jsMain/kotlin/com.mohamedrejeb.calf.picker/ComposeResource.js.kt` | 1–8 | toImageBitmap actual uses Skia Image.makeFromEncoded→toComposeImageBitmap; synchronous full decode, runtime codec/heap limits remain unverified on this target. |
| `calf-file-picker/src/jsMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.js.kt` | 1–107 | remember picker and launcher delegation; updated type/mode/result, unsupported folder, new hidden input/accept/multiple, limit and event conversion, callback+catch/cancel cleanup, DOM click; IO-026 completion/disposal gap. |
| `calf-file-picker/src/jsMain/kotlin/com.mohamedrejeb.calf.picker/WebBlob.js.kt` | 1–18 | createBlob copies signed Kotlin bytes into JS Int8Array then unsigned view, Blob MIME options; bit patterns preserved but allocation is full-buffer. |
| `calf-file-picker/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/picker/ComposeResource.wasmJs.kt` | 1–7 | toImageBitmap actual uses Skia Image.makeFromEncoded→toComposeImageBitmap; synchronous full decode, runtime codec/heap limits remain unverified on this target. |
| `calf-file-picker/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.wasmJs.kt` | 1–104 | remember picker and launcher delegation; updated type/mode/result, unsupported folder, new hidden input/accept/multiple, limit and event conversion, callback+catch/cancel cleanup, DOM click; IO-026 completion/disposal gap. |
| `calf-file-picker/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/picker/WebBlob.wasmJs.kt` | 1–15 | createBlob ByteArray→UByteArray→Uint8Array and JsArray Blob parts; opt-ins and MIME options inspected; full-buffer conversion with browser-specific interop unexecuted. |
| `calf-file-picker/src/webMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.web.kt` | 1–160 | createBlob expect, saver byte/File/Blob paths, triggerDownload DOM/objectURL lifetime, extensionToMimeType allswitch branches, platform overloads; onResult/settings unused (IO-011/012). |
| `calf-io/build.gradle.kts` | 1–27 | KMP/publication plugins; API core+kotlinx-io; DocumentFile/browser platform dependencies and desktop coroutines test dependency reviewed. |
| `calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/AndroidContextHolder.kt` | 1–40 | AndroidContextHolder.context/initialize and initializeKmpFileContext: volatile app-only reference, fail-fast missing initialization, benign repeated app-context initialization; saver-only initialization gap documented. |
| `calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/InternalContext.android.kt` | 1–5 | resolveContext actual: read AndroidContextHolder.context; missing initialization propagates. |
| `calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt` | 1–62 | Uri wrapper; exists open/close+catch; readByteArray close-only-on-success; DocumentFile single-URI name/kind; URI path; Uri/File adapters. IO-019/020 and file:// interoperability. |
| `calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFileSource.android.kt` | 1–10 | source opens ContentResolver input stream, wraps as RawSource, null→FileNotFoundException; returned resource is caller-owned, not eagerly closed. |
| `calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/InternalContext.kt` | 1–10 | resolveContext expect and the context-free delegation contract. |
| `calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt` | 1–126 | Opaque KmpFile expect; context and context-free exists/readByteArray/getName/getPath/isDirectory/source-adjacent contracts; both isFile negations reviewed (IO-010), no common construction/equality/persistence API. |
| `calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.kt` | 1–40 | source(context)/source() expect/delegation; explicit blocking dispatcher, caller-close, native streaming versus web eager-buffer documentation reviewed; positive ownership guidance. |
| `calf-io/src/desktopMain/kotlin/com/mohamedrejeb/calf/io/InternalContext.desktop.kt` | 1–5 | resolveContext actual: return PlatformContext.INSTANCE; no IO or native state. |
| `calf-io/src/desktopMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.desktop.kt` | 1–23 | File wrapper; exists/readBytes/name/path/isDirectory direct delegates and File.toKmpFile; blocking and relative-path semantics inspected. |
| `calf-io/src/desktopMain/kotlin/com/mohamedrejeb/calf/io/KmpFileSource.desktop.kt` | 1–9 | source opens absolute Path through SystemFileSystem; no hidden dispatcher or memory copy; covered by six original tests. |
| `calf-io/src/desktopTest/kotlin/com/mohamedrejeb/calf/io/KmpFileSourceTest.kt` | 1–104 | Six tests: full 100003-byte content, 4096-byte chunks, context-free source, missing file, empty EOF, use closes stream; fixture @AfterTest delete. Executed unchanged in extracted-source run. |
| `calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/InternalContext.ios.kt` | 1–5 | resolveContext actual: return PlatformContext.INSTANCE; no IO or native state. |
| `calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt` | 1–63 | Two-URL/internal and single-URL constructors, exists, NSData read+unsafe memcpy, original-URL name/path/kind, NSURL adapter. IO-001/008/014; no security-scope or ownership disposer. |
| `calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.ios.kt` | 1–12 | source validates url.path then opens SystemFileSystem source; readable-copy path is used, security scope not acquired; caller-close contract. |
| `calf-io/src/jsMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.js.kt` | 1–28 | readFileAsBytes JS actual uses FileReader/onloadend, Uint8Array and byte copy; DONE/error conflation and noncancellable suspension (IO-009). |
| `calf-io/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.wasmJs.kt` | 1–34 | readFileAsBytes Wasm actual and getReadyState/getResult JS helpers: same FileReader state machine, copies and cancellation/error gap as JS (IO-009). |
| `calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/InternalContext.web.kt` | 1–5 | resolveContext actual: return PlatformContext.INSTANCE; no IO or native state. |
| `calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.web.kt` | 1–26 | Shared File wrapper/adapter; exists=true; asynchronous byte read; name/path=filename; dot-heuristic isDirectory; expect readFileAsBytes. IO-009/010/014. |
| `calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.web.kt` | 1–8 | source eagerly reads full browser File and writes into kotlinx-io Buffer; documented nonstreaming exception, plus copied allocation and inherited read errors. |

Ledger completeness check: **62/62 baseline scope paths**, including all tests, resources and native build auxiliaries. Supporting `calf-core` PlatformContext expect/nonAndroid actual were also read and compiled for the original-test harness; their main audit ownership remains with core.
