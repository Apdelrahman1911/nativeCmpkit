# Native features: camera, sharing, WebView and dormant modules

## Scope and reading guide

Reviewed baseline: **`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`**. This document describes the implementation, not an aspirational API. All **47 tracked files** in `calf-camera-picker`, `calf-share`, `calf-webview`, `calf-maps`, `calf-media`, and `calf-notifications` were read, including build/native/cinterop files and unsupported actuals. Exact baseline file/symbol coverage is at the end. Findings are in [the area audit](../audit/native-features.md) and [`NATIVE.json`](../audit/findings/NATIVE.json); [test procedures and executed probes](../testing/native-features.md) distinguish source evidence from device verification.

Project identity is nativeCmpkit; retained `calf-*` project paths and `com.mohamedrejeb.calf.*` public packages are compatibility decisions. JNI exported symbol names also embed that package; **never rename the Kotlin bridge independently of the Rust exports**. Neither runtime implementation downloads source from upstream GitHub. Dependency repositories, native resource packaging, OS frameworks and host setup remain external requirements.

### Dependency/availability map

| Module | Direct implementation dependencies | API/status |
|---|---|---|
| `calf-camera-picker` | Compose foundation; Android Activity Compose; `api(calf-io)` | Published module, mobile capture; Desktop/Web actuals silently do nothing |
| `calf-share` | Compose foundation; Android Activity Compose; Web kotlinx-browser; `api(calf-io)`; Desktop JNI/Rust | Experimental public launcher; real native share only Android/iOS/macOS; other desktop actions are fallbacks |
| `calf-webview` | Compose foundation/material3, coroutines; Android Activity/coroutines-android; Desktop JavaFX **19** base/graphics/controls/media/web/swing + coroutines-swing; Web kotlinx-browser | Native Android/WK/JavaFX views, browser iframe, common state/navigation/cookies; incomplete parity |
| `calf-maps` | Compose foundation/UI, Kotlin test | Included Gradle module, **zero source/API**, no module-publication plugin |
| `calf-media` | Stale independent Gradle script only | **Excluded** from settings; no implementation |
| `calf-notifications` | Stale independent Gradle script and incomplete iOS experiment | **Excluded** from settings; not notification delivery support; distinct from `calf-permissions:notifications` |

The first four use shared `compose.multiplatform` conventions: Android KMP library, JVM target named `desktop`, browser JS, browser WasmJS, **iOS arm64 device and arm64 simulator**. iOS x64 is **not** a target of those active modules. The old excluded scripts still declare it; that does not add supported binaries. There is no native Linux/macOS/Windows Kotlin target: desktop integration runs on JVM, with a Rust cdylib only for sharing. See [architecture](../architecture/README.md) and [platform matrix](../platforms/README.md).

## 1. Camera picker

### Public API and data ownership

`CameraPickerLauncher` is an interface exposing only `launch(): Unit`. `rememberCameraPickerLauncher(onResult: (KmpFile) -> Unit)` is a composable expect function. There is **no error, dismissal, permission, availability, output-format, quality, resolution, lens, video, lifetime, or cancellation parameter**. A callback means a file wrapper was produced, not that an independent permanent media-library asset was created.

`KmpFile` is the shared IO module's platform wrapper: Android URI, iOS NSURL, Desktop File, Web File. Camera does not read or validate the returned bytes. Successful outputs live in application cache/temporary directories; callers must manage their intended retention. Read [IO/file-picker documentation](io-and-file-picker.md) before using URI paths as filesystem paths or forwarding externally supplied URLs.

### Android execution

1. Composition obtains `LocalContext.current`, remembers a nullable launcher-holder state, registers `ActivityResultContracts.TakePicture()`, and creates one `CameraPickerLauncherAndroidImpl`.
2. `launch()` checks `FEATURE_CAMERA_ANY`; absence is a silent return. This is not an intent-handler availability check.
3. It creates a prospective cache path `photo_<currentTimeMillis>.jpg`. It does not preallocate, check free space, or narrow output into a camera-only subdirectory.
4. API24+ uses `FileProvider.getUriForFile(context, "${context.packageName}.provider", file)`; API23 uses `Uri.fromFile`. The host must supply that provider/path metadata. The **sample**, not the library, declares exported-false, grantable-read FileProvider and a `cache-path path="."`.
5. The instance saves `imageUri` in ordinary Compose mutable state and invokes the registered ActivityResult launcher.
6. Registry completion calls the current holder's `handleResult(Boolean)`; only `success && imageUri != null` calls `onResult(KmpFile(imageUri))`. Failure/cancel do not call back, delete, or clear pending state.

**Important consequences:** output URI is not saveable across Activity recreation; the implementation captures the original callback/context; multiple launches share one mutable URI; hardcoded authority/provider exceptions escape. Provider permission flags supplied by the Android contract should be checked on actual recipient camera apps rather than adding broad grants speculatively. CAMERA runtime permission belongs to the host: external-camera behavior differs when a host has declared CAMERA but not obtained it. The sample separately uses the permissions module before launch. Findings NATIVE-019–024 cover recovery/setup/lifecycle gaps.

### iOS execution

1. `remember(viewController, onResult)` creates a launcher owning `UIViewController` and one nullable **strong** `pickerDelegate`.
2. `launch()` checks `SIMULATOR_DEVICE_NAME` and camera source availability. On simulator/no camera it changes semantics to **photo-library selection** rather than returning unsupported.
3. It constructs a `UIImagePickerController`, sets the chosen source and `allowsEditing=false`, constructs an NSObject delegate implementing both picker and navigation protocols, stores it strongly and assigns UIKit's weak delegate.
4. Only presentation is wrapped in `dispatch_async(main_queue)`; construction/configuration occurs on the caller thread.
5. `didFinishPickingMediaWithInfo` reads `UIImagePickerControllerOriginalImage` as UIImage. It ignores media URL and editing metadata. It converts the whole image using `UIImagePNGRepresentation`, writes NSData atomically to `NSTemporaryDirectory()/captured_image_<Random.nextInt>.png`, and calls the result with a file NSURL if every step succeeds.
6. After callback, it dismisses the controller and clears the shared strong delegate. Cancellation dismisses/clears without a result. Conversion/write failures also dismiss silently. A throwing user callback precedes cleanup and can prevent it.

**Host setup:** supply meaningful `NSCameraUsageDescription` and the photo-library usage description when the fallback is possible; request/check authorization through the appropriate host API. Missing privacy strings can terminate an iOS app; these cannot be supplied by a general library on the application's behalf. Full-resolution PNG conversion/writes happen synchronously in the UIKit callback, not an IO worker. There is no single-flight guard, disposal hook or temporary-file cleanup policy.

**Historical decision:** PR326/commit `7898be3` replaced incorrect camera media-URL retrieval with original UIImage→temporary-file conversion and added strong delegate retention/main-queue presentation. Those fixes are present. PR311 proposed JPEG conversion but is not evidence that the baseline uses JPEG: it uses **PNG**. Preserve the original fix while repairing callback/operation ownership.

### Desktop and browser

Both actual remembered launchers instantiate an otherwise empty implementation; `launch() = Unit` and `onResult` is never used. No webcam capture, file chooser, `getUserMedia`, browser `<input capture>`, nor availability API exists. Compilation is not support. The capability/outcome contract should be designed before implementing these targets.

## 2. Content sharing

### Common types

`@ExperimentalCalfApi rememberShareLauncher(onResult)` returns the expect `@Stable ShareLauncher(onLaunch)` class. Every actual's `launch(content)` simply invokes the supplied function; platform work is supplied by the remembered factory. The constructor itself is public, so a custom launcher can be application-defined.

`@Immutable sealed interface ShareContent` has:

* `Text(text, subject?)` and `Url(url, subject?)`;
* `File(file: KmpFile, mimeType, subject?)`;
* `Files(files: List<KmpFile>, mimeType, subject?)`.

The API does not validate empty strings/lists, URI schemes, MIME/actual contents, file existence/readability, or deep immutability of caller-provided lists. No content copy is promised. File ownership stays with the caller; sharing recipients can read after selection, so immediate deletion is unsafe.

`ShareResult` has only `Success`, `Dismissed`, `Unavailable`. **Their practical meanings differ by target**:

| Target | Text / URL | File(s) | When result is delivered |
|---|---|---|---|
| Android | ACTION_SEND, `text/plain`, EXTRA_TEXT, optional EXTRA_SUBJECT | ACTION_SEND or SEND_MULTIPLE; MIME + raw KmpFile URI(s); READ grant | Success immediately after chooser launch; cannot observe dismissal/completion |
| iOS | NSString text or parsed NSURL (invalid URL becomes string) | raw file NSURL(s) as activity items | UIActivity completion boolean; NSError ignored and false called Dismissed |
| macOS JVM | NSString/NSURL | file URLs | Rust delegate marks **service selection**, not delivery, as Success; nil selection→Dismissed |
| Windows/Linux JVM or native failure | text→clipboard; URL→default handler/browser, clipboard on failure | **open each file in default application**, not an actual share | action initiation/copy treated as Success |
| Browser JS/Wasm | navigator.share; if absent, clipboard fallback | navigator.share files; no fallback | Promise resolve→Success; AbortError→Dismissed; other rejection→Unavailable; clipboard currently reports early |

### Android

`rememberUpdatedState(onResult)` prevents stale callbacks; the launcher itself is remembered without the context as a key. `ShareContent.toShareIntent` dispatches to three private builders. Text and URL share exactly the same text intent. Files supply `FLAG_GRANT_READ_URI_PERMISSION`; they do **not** convert `file://` to `content://`, validate a content provider or request write grants. Multi-file intent stores an `ArrayList` of URIs.

The chooser is created before the try. `context.startActivity()` and the success callback are inside the same try/catch(Exception), which maps any caught exception to Unavailable. Thus a throwing application success callback causes another callback (NATIVE-032). Hosts normally provide an Activity context; an application context without NEW_TASK fails. Suppressed exception causes are unavailable to the caller. The share API does not use ActivityResult to observe a selected target. No file bytes are copied in this module.

### iOS

The remembered launcher is keyed on `LocalUIViewController` and uses updated callback state. `toActivityItems()` maps each content type without eagerly reading bytes: text remains String; a URL is NSURL when parseable; files expose `KmpFile.url`. Subject/MIME are not part of those raw items.

`presentShareSheet()` creates `UIActivityViewController(activityItems, applicationActivities=null)`. It assigns `title=subject`, which is **not** the documented activity item subject hook. Completion reads only `completed`; activity type, returned items and NSError are discarded. Popover sourceView and a zero-size center sourceRect with no arrows are explicitly configured, a positive iPad safety measure. It then presents directly on the caller thread with no busy/current-presentation guard.

Externally provided/security-scoped URLs still require caller-managed access; this module does not start/stop scoped access or snapshot files. Ordinary nonfolder iOS file-picker outputs may already be application-owned copies; do not generalize that to manually wrapped external URLs/folders. See IO findings before copying or releasing these resources. Cancellation of an enclosing composition does not inherently dismiss the sheet.

### Desktop Kotlin → JNI → Rust → AppKit

```text
Compose click
  → ShareLauncher.launch(content)
  → remembered scope.launch
  → withContext(Dispatchers.IO)
  → NativeShareBridge.isNativeShareSupported()
       object initialization loads library once
  → showNativeShare (text,url,filePaths tuple; parentWindow=0)
  → native JNI showShareSheet
  → Rust converts Java strings/local refs
  → AppKit work dispatched to main queue
  → didChooseSharingService sets Mutex<Option<result>> + notifies Condvar
  → JNI worker returns / after timeout returns Dismissed
  → Compose scope delivers current onResult unless cancelled
```

`handleShare()` catches **Throwable** around native support/call and falls back. `showNativeShare()` converts each native result constant (0 Success, 1 Dismissed, other→fallback); additional Exception is caught. A library initialization error poisons the JVM object initialization; subsequent accesses can remain fallback-only. There is no diagnostic callback, capability distinction or retry/reset.

`handleFallbackShare` has separate text, URL, file and list functions. Text uses AWT `Toolkit.systemClipboard` and `StringSelection`. URL tries Desktop.BROWSE, otherwise/exception copies URL. Files call Desktop.OPEN; MIME/subject are ignored. The file-list loop can partially open files and then return Unavailable when a later entry fails. Empty lists can report Success. All fallback errors handled here are Exception, not arbitrary VM errors. These side effects run on the IO worker; result is resumed in the Compose coroutine context.

**Native library loader.** First attempts `System.loadLibrary("calf_share_native")` for packagers that extract natives. On UnsatisfiedLinkError it identifies macOS/Windows/Linux and arm64/x64 aliases, opens a resource under `native/<os>-<arch>/<mapped-name>`, reads all bytes, makes `~/.cache/calf-share`, writes a private temporary file, moves atomically if possible (falls back to replace move), then calls `System.load` on **one fixed filename**. The stream is closed and extraction failure deletes the temporary file. Cache directory creation/ownership are unchecked; full resource buffering is unnecessary overhead; filename/version collision remains (NATIVE-031). File-picker's newer content-addressed cache is an existing remedy, not another defect to copy.

**Bridge ABI.** `NativeShareBridge` defines constants and static external `init`, `isNativeShareSupported`, `showShareSheet(text?,url?,Array<String>?,parentWindow:Long)`. Initialization calls `loadNativeLibrary`; the exported native `init` is otherwise a no-op. Rust exports exact `Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_*` names. `jstring_to_string` maps null or JNI conversion failure to None; `jstring_array_to_vec` uses array length or zero, skips unreadable entries, and **deletes JNI local references** per entry. No shell/process command interpolation occurs in Rust. JNI errors/pending Java exceptions are not surfaced as structured diagnostics.

**macOS Rust details.** It builds retained NSString/NSURL items; an invalid URL may be omitted, and no items returns Unavailable. It uses an `Arc<(Mutex<Option<jint>>,Condvar)>`, `Once` and a global dynamically registered `CalfShareDelegate` ObjC class with `_pairPtr` ivar. The `sharingServicePicker:didChooseSharingService:` method reconstructs the raw Arc, writes the result and notifies, then forgets the Arc. `ShareContext` contains retained NSArray, parent-window integer and Arc and has a manually asserted `unsafe impl Send`; current item types are immutable NSString/NSURL, so this needs deliberate review if item types expand.

`dispatch_async_f` owns a boxed context. On the main queue it obtains supplied NSWindow pointer or, in current Kotlin usage, `NSApp.keyWindow`. Missing window/contentView signals Unavailable before picker/delegate allocation. It creates NSSharingServicePicker via `msg_send_id!`, assigns a retained delegate holding another raw Arc owner, converts current mouse coordinates from screen→window→view, chooses mouse or center anchor, and shows a 1×1 popup near that position. Main-thread marking is unchecked but justified by this dispatch path. A `std::mem::forget(delegate)` prevents weak-delegate loss by permanently leaking it; no later cleanup exists. The local picker is dropped at function exit; **whether AppKit retains it adequately is a device/runtime verification item**, not a demonstrated UAF.

The calling worker waits up to 300 seconds per wait iteration. Late/spurious callbacks, cancellation and overlapping requests have no explicit state machine; Rust unwrap/ClassBuilder/FFI panic paths are not recovered by Kotlin Throwable catches. Current Kotlin always sends parentWindow=0; arbitrary pointer dereference is not an exposed normal application API. Non-macOS `show_share_sheet` simply returns Unavailable and `isNativeShareSupported` false, yet desktop resource processing still builds/loads the cdylib (wasted dependency/setup unless packaging policies need it).

### Browser JS and Wasm

The common Web implementation synchronously routes content without launching a coroutine, preserving the original user gesture for `navigator.share`. Feature detection checks property existence (`'share' in navigator`), not function type, secure context, permissions policy, file support or `navigator.canShare`.

JS actuals construct a plain object, set text/URL and optional title, or File[] for file content. `handleSharePromise` maps fulfilled→true, AbortError→false, other rejection→null. Wasm uses external `@JsFun` functions with three completion lambdas, nullable `JsString` title, and a built `JsArray` for file lists (`jsArrayPush`). Both mechanisms omit file subject/MIME overrides (the browser File has its own metadata). Promise rejection distinguishes cancellation from other error, a positive improvement over treating every error as dismissal, but callback exceptions can enter the trailing catch.

When share is absent, text/URL fallback calls an expect `copyToClipboard(): Unit`. JS/Wasm discard the writeText Promise; the shared caller immediately returns Success. Files immediately report Unavailable. Existing API but unsupported payload/NotAllowedError does **not** trigger clipboard fallback. A browser or embedder may require HTTPS, transient activation, and `web-share` permissions policy. No capability result allows a caller to determine these details without attempting the operation.

### Native build/resources

Cargo builds a `cdylib` with JNI0.21. On macOS it uses objc2/block2 and generated Foundation/AppKit bindings; release uses size optimization, LTO, strip, one codegen unit. Semver ranges are floating and Cargo.lock is ignored; the build audit owns dependency locking/provenance findings. There are no Rust tests in this crate.

The Gradle script skips native compilation if **any** nonempty platform directory exists under desktop resources, otherwise `cargo build --release --target <host>` runs for desktop resource processing and copies the result to build/native-libs/native/<platform>. Local target mappings: macOS arm64/x64, Windows amd64, Linux amd64/arm64. Native published resource completeness is not established by that directory heuristic. Imported CI built macOS arm64/x64, Windows x64 and Linux x64; Linux arm64/Windows arm64 are not equivalent published guarantees. Build scripts/workflows and signing/release gates are reviewed in the build audit; migration must keep publishing disabled pending owner authorization.

## 3. WebView common state/control model

### API graph and state flow

```text
rememberWebViewState(url, headers) / rememberWebViewStateWithHTMLData(...)
  → one remembered WebViewState
  → LaunchedEffect(parameters) sets state.content
WebView(state, navigator)
  → platform factory creates native view and associates state
  → snapshotFlow(state.content) starts a platform load
  → native delegates/listeners update title/loading/url/errors/navigation flags
WebViewNavigator(scope)
  → coroutine emits into MutableSharedFlow(replay=1)
  → attached platform collector dispatches native navigation
WebSettings setter
  → onSettingsChanged callback
  → state's native applySettings (not itself Compose mutable state)
CookieManager
  → platform-global/default cookie store, NOT isolated per WebView
```

`WebContent.Url` carries URL and additional headers. `Data` carries string, optional base URL, encoding default utf-8, MIME and history URL. `NavigatorOnly` suppresses content loads. Internal `withUrl` copies the URL variant (retaining headers) or makes a new URL variant; no current production caller was found in this module, so it is not an active navigation interception mechanism.

`LoadingState` has Initializing, Loading(progress), Finished; **isLoading is true for Initializing** on every platform. `WebViewError` contains only integer code and description; it cannot distinguish request URL/main-frame/resource type/retryability. `errorsForCurrentRequest` is a list, despite a comment describing a singular last error. Android includes subresource errors; other implementations are narrower/different.

All actual `WebViewState`s expose observable content, URL/title/loading/errors and platform view reference (Android also favicon and saved Bundle). Common WebSettings/CookieManager are created once per state, but cookie stores are default/global, not isolated browser sessions. No common WebViewClient/navigation delegate/download handler/permission callback/custom scheme/popup policy/JS bridge API exists. Native instance access is the escape hatch, complicated by `onCreated` ordering on mobile.

`WebViewNavigator` owns a caller/remembered scope, mutable canGoBack/canGoForward flags, and six command types: Back, Forward, Reload, StopLoading, LoadUrl(headers), LoadHtml(base/MIME/encoding/history). Each public method launches a coroutine to emit. There is no return value, acknowledgement, busy/error state or single-view ownership check. replay=1 mixes persistent initial-load requests with transient commands (NATIVE-008).

Remember helpers intentionally update content in LaunchedEffect, not directly during composition; this is a historical fix for recomposition loops. Saveable state uses platform `WebStateSaver`: Android stores native Bundle; other platforms only metadata and thus do not restore loaded content (NATIVE-007). None restores settings/cookies as part of saved state.

### Settings: every exposed knob

Every setter assigns even an equal value and invokes the same onSettingsChanged callback, which reapplies a full settings bundle. Multiple sequential changes create redundant native work/FX tasks; thread affinity remains the caller's responsibility on mobile.

* Common: `javaScriptEnabled=false`, `javaScriptCanOpenWindowsAutomatically=true`.
* Android: supportZoom=true, textZoom=100, allowContentAccess=true, allowFileAccess=true, blockNetworkImage=false, blockNetworkLoads=false, databaseEnabled=true, domStorageEnabled=true, loadsImagesAutomatically=true, useWideViewPort=true, loadWithOverviewMode=true, mediaPlaybackRequiresUserGesture=false, supportMultipleWindows=true, builtInZoomControls=true, displayZoomControls=false, setGeolocationEnabled=true, isAlgorithmicDarkeningAllowed=true, safeBrowsingEnabled=true.
* iOS: allowsBackForwardNavigationGestures=true, allowsInlineMediaPlayback=true.
* Desktop: customUserAgent=null. Setting a custom value works; resetting to null does **not** restore the default because applySettings uses `?.let` only (NATIVE-036).

Android safe browsing is gated API26+, algorithmic darkening API33+. No mixed-content, universal-file-origin, SSL-error override or addJavascriptInterface is enabled by this module. Allowing local file/content access and autoplay/popups is a **host trust decision**, not proof of a remote exploit. JavaScript is off by default and native default TLS handling is not bypassed. For untrusted content, review these defaults and origin/navigation policy, especially the Web sandbox removal described in NATIVE-010.

### Android implementation

Public WebView remembers Accompanist-named client/chrome-client, uses BoxWithConstraints to choose MATCH_PARENT for fixed axes and WRAP_CONTENT otherwise, and delegates to an internal overload that also accepts native layout params, client/chrome customization and a factory. The common/public API does not expose those internal parameters. Native defaults are redundantly set in the public onCreated wrapper, then common settings are applied again.

The internal overload reads state.webView, installs BackHandler only when captureBackPresses && navigator.canGoBack, launches navigation collection on Dispatchers.Main, and observes content. URL loads pass headers to loadUrl; Data uses loadDataWithBaseURL with all fields. Client state/navigator references are reassigned on composition. AndroidView creates/initializes native view, restores state.viewState when present, sets client/chrome, then stores it. No update callback applies changed layout params or swaps externally replaced WebViewState; arbitrary replacing of state at the same composable identity needs explicit integration tests. Release only calls user onDispose.

`AccompanistWebViewClient` handles start (reset progress/errors/title/favicon/last URL), finish (Finished), history (navigation flags) and modern received-error (append **any** resource error). It does not record HTTP error statuses or SSL errors into the common list, override URL loading, or customize Web permissions; native default behavior applies. `AccompanistWebChromeClient` updates title/favicon and progress unless state already Finished. Copying the full error list after every error is O(n²) over many failures; no bound exists, an optimization item after correctness.

State.applySettings delegates immediately to the native view; evaluateJavascript does the same and its annotation alone does not expose the state to page JavaScript. Saver obtains Bundle by calling WebView.saveState at save time, then restores page title/last URL and Bundle into a NavigatorOnly state. It cannot recover absent native history if no view existed at save time. State may continue retaining an Activity through webView after disposal; repair lifecycle before adding features.

### iOS implementation

WKWebView is created in UIKitView. Interaction mode is **NonCooperative**; semanticContentAttribute maps current Compose LTR/RTL at creation. `captureBackPresses` and defaults both set gesture handling; URL loads also force gestures true (NATIVE-009). Neither layout direction nor captureBackPresses has a UIKitView update callback for later changes.

The native state extends NSObject and `WKNavigationDelegateProtocol`; it is retained by Compose, while native navigationDelegate is weak. A LaunchedEffect sets navigator and collects commands on Dispatchers.Main. Another DisposableEffect creates/retains a `WKWebViewObserver`, registering six KVO keys and **removing all six on effect disposal**. This balanced observer registration is a positive resource check. Content effects build NSMutableURLRequest with extra headers or loadHTMLString for Data.

Navigation callbacks: didFinish sets Finished/title/history flags; didCommit sets Loading/lastURL, resets errors and flags; didFailNavigation and didFailProvisionalNavigation append NSError code/description and set Finished. No didStartProvisional reset, navigation policy delegate, process-termination handler, Web UI delegate/file-upload/geolocation/permission adapter, download policy or explicit native stop-on-release exists. UIKitView release calls user onDispose then clears state.webView; an exception in user callback can prevent clearing.

KVO keys and updates: estimatedProgress→Loading(progress) only while isLoading; loading→Loading or Finished; title→pageTitle; URL→lastLoadedUrl; canGoBack/Forward→current navigator flags. Observer ignores non-WK objects/unknown keys and uses no KVO initial option. The custom Objective-C cinterop protocol only exposes observeValueForKeyPath; it imports Foundation and declares no implementation/ownership by itself.

State navigation HTML with a base URL creates UTF8 NSData and passes caller MIME/encoding; with no base it uses loadHTMLString. URL navigation builds a new NSMutableURLRequest; back/forward/reload/stop invoke native methods explicitly. Encoding mismatch and configuration-copy rules are separate findings. JavaScript result errors become localized strings rather than a typed error. Saver only keeps title/URL metadata.

### Desktop JVM implementation

WebView remembers JFXPanel directly during composition, sets global Platform.setImplicitExit(false), and queues setup through Platform.runLater. Setup creates JavaFX WebView, queues settings, attaches Worker state/progress listeners, assigns Scene to panel, stores native view and calls onCreated **on FX thread**, not the Compose/AWT thread.

Worker transitions: RUNNING resets progress/title and stores location; SUCCEEDED sets Finished/title/URL/history flags; FAILED sets Finished and a singleton exception error when present; CANCELLED sets Finished. Progress is clamped to [0,1] only while loading. It does not clear previous errors at new load, observe later SPA title/history mutations or update URL on every redirect/location event. Setup/queued native calls are not cancelled when composition disappears or supplied state/navigator changes; DisposableEffect is keyed Unit.

Content loads runLater then engine.load(URL) or loadContent(data, optional MIME). Headers/base/encoding/history are dropped. Navigator commands runLater: guarded history.go(±1), engine.reload, **unqualified stopLoading feedback bug**, loadContent(html,mime), load(url). A null MIME from navigator is passed to the two-argument Java API rather than the state path's default overload; HTML/default-MIME parity needs regression coverage without assuming every WebKit version rejects null.

Settings are now correctly marshalled to FX, addressing historical issue344 at source level. All setters queue a full reapply and read live settings when the queue executes; there is no batching snapshot. executeScript is also queued, but exceptions are uncaught and return values use toString. All teardown is left to user callback and state remains populated (NATIVE-002). Runtime startup/reentry/rendering prerequisites are not fully tested here; see historical issue346 and build/platform docs.

### Browser implementation

Both JS and Wasm use a tiny actual adapter over Compose `WebElementView`. A generic expected CalfWebElementView exposes only factory/modifier/update. Common WebView creates an iframe, border none, width/height attributes 100%, registers load/error lambdas, stores it, then calls onCreated. Update applies the sandbox setting; it is not a per-content reset hook.

URL content sets src; HTML content sets srcdoc. Native-looking headers/base URL/MIME do nothing. Load always sets Finished, attempts title/location read (same-origin only), then forces both history capabilities false. Cross-origin access exceptions are swallowed. Browser iframe load fires even for many error pages; error events cannot establish native-equivalent network status. No started/progress event is implemented.

Navigator Back/Forward use contentWindow.history inside try; Reload calls location.reload, falling back to clearing/reassigning src on cross-origin error; Stop uses window.stop inside try; LoadUrl removes srcdoc then sets src; LoadHtml sets srcdoc. Same-origin history may interact with joint browser history; browser Back/Forward semantics are not an isolated native WebView guarantee. URL/HTML transitions differ between state and navigator until NATIVE-004 is fixed.

evaluateJavascript calls an expected Window.evaluateScript: JS `asDynamic().eval(script)`; Wasm a small JS-interoperable `window.eval(script)`. Errors become callback(null). This is intentional code execution of caller-supplied script, not string interpolation into a shell; use only trusted scripts. Same-origin/CSP restrictions apply. Removing sandbox when enabling JS gives srcdoc full host origin, not a security-isolated WebView.

## 4. Cookie manager contract and implementation

`Cookie` stores name/value plus nullable domain/path/expiry millis and secure/HttpOnly booleans. It has no SameSite, host-only flag, creation time, partition key or validation. All CookieManagers expose suspend set/get/removeAll but no success/error result or per-profile data store. All removeAll operations are broad for their underlying shared store.

| Target | set | get | removeAll / limitations |
|---|---|---|---|
| Android | On Main, build Set-Cookie string, callback→resume, flush | On Main, split `getCookie` header at semicolons/first `=` | removeAllCookies callback + flush; metadata unavailable on read; set Boolean ignored |
| iOS | Build NSHTTPCookie properties, URL-host default domain, `/` path, NSDate millis conversion, Secure/HttpOnly; invalid native cookie silently returns | Fetch every cookie, filter domain only, map metadata | Enumerate then delete sequentially; concurrent insertions after enumeration survive; default WKWebsiteDataStore only |
| Desktop | Build HttpCookie, path `/`, domain host default, lifetime or session -1, direct cookieStore.add | Direct store.get(uri); maxAge added to **current read time** | Global handler may be replaced; store.removeAll; path matching/expiry defects |
| Browser | Set document.cookie from string; URL ignored, numeric expiry invalid, HttpOnly unsupported | Host document.cookie only; metadata lost | Expires name at root path only; no cross-origin/HttpOnly/all-path access |

Android flush can block caller Main with storage work; batching/persistence policy should be measured before optimizing. Cancellation of suspend wrappers does not cancel already-issued native cookie operations; they may still mutate global state. Single native callbacks are expected; neither module wraps callback duplication in defensive tryResume. iOS store accesses are not explicitly dispatched; per-API UI-affinity and cancellation tests remain required. No password/cookie values should be logged in diagnostics; upstream sample prints returned cookie data and must not be copied into production logging practices.

Input delimiters in name/value/domain/path are not validated in Android/browser string serialization; unsafe values can alter cookie attributes. The caller normally supplies trusted values, so this is an input-contract/security-hardening item rather than a confirmed remote exploit. Browser-specific inability to guarantee HttpOnly/logout is intentional platform security, not a feature to bypass. Cross-platform authentication storage should not be built on presumed metadata fidelity without fixing/documenting NATIVE-011–014.

## 5. Dormant maps/media/notifications

* **Maps:** one 13-line build script, no classes/functions/resources/native providers/tests. Common foundation/UI and Kotlin-test declarations do not implement mapping. Upstream issue27 remains an unsatisfied feature request. Choices include provider licensing/keys, native map SDK parity, clustering/markers, offline/privacy and desktop/browser fallback; no choice is recorded by implementation.
* **Media:** one 47-line excluded build script, old Android plugin alias/DSL, JVM11, iOS x64/arm64/simulator, Web commented out, incorrectly copied sf.symbols namespace. No player, media session, decoder, custom data source or AVAsset resource loader exists. Upstream issue245 requests custom sources for a future feature, not a patchable existing function.
* **Notifications:** same stale excluded build script/namespace. The only source is an un-packaged main experiment: get UNUserNotificationCenter, request alert|badge|sound, on granted try `scope.launch(Dispatchers.Main)`, construct title/body/sound, add immediate `hello` request. It lacks imports, defined scope, dependency/target integration, error handling, denied result, delegate/delivery/lifecycle, permission state and public API. It is **not buildable notification scheduling support**. Permissions helpers elsewhere are real but independent.

Do not include/publish these modules simply to make an artifact matrix appear complete. Preserve the experiments/history; add explicit discovery/design tasks and realistic acceptance tests before future implementation.

## 6. Complete file/symbol review coverage

Paths below are relative to each module root, with Kotlin package-path spelling preserved (some directories literally contain dots). Ranges are baseline lines, not promises about later migration edits. Declaration-only DTOs/default getters and native external prototypes were reviewed as well as executable functions.

### `calf-camera-picker` — 6 files

| File | Lines / reviewed symbols and behavior |
|---|---|
| `build.gradle.kts` | 1–21: conventions/publication, IO API, foundation, Kotlin test, Activity Compose; no actual tests |
| `src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt` | 7–14: launcher interface/launch and remember expect; success-only callback |
| `src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt` | 21–74: Android implementation constructor/state, launch, handleResult, remembered activity result glue |
| `src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt` | 24–106: launcher/delegate field, launch/source choice, finish/cancel delegate, saveTempImageFile, remembered factory |
| `src/desktopMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.desktop.kt` | 8–20: Desktop implementation/launch stub/remember actual |
| `src/webMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.web.kt` | 8–20: Web implementation/launch stub/remember actual |

### `calf-share` — 17 files

| File | Lines / reviewed symbols and behavior |
|---|---|
| `build.gradle.kts` | 1–90: dependencies, prebuilt detection, nativeLibProps, buildNativeLib/copyNativeLib, resources/task wiring |
| `native/.gitignore` | 1–2: target and Cargo.lock ignored |
| `native/Cargo.toml` | 1–22: crate identity, cdylib, JNI/macOS features, release profile |
| `native/src/lib.rs` | 1–337: result constants; three JNI exports; nullable/array conversion helpers; macOS/non-macOS show_share_sheet; did_choose; ClassBuilder/ivar/Once; ShareContext; execute_on_main; Condvar wait; all unsafe ownership/dispatch blocks |
| `src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareContent.kt` | 9–59: sealed content, Text/Url/File/Files, MIME/subject contracts and list ownership |
| `src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareResult.kt` | 8–26: Success/Dismissed/Unavailable and documented semantics |
| `src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.kt` | 7–41: remember expect, experimental constructor/launch contract, platform comments |
| `src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt` | 12–86: remember factory, actual launcher, toShareIntent, text/single/multiple intent builders, grants/errors/results |
| `src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareContentExt.ios.kt` | 9–24: all four toActivityItems branches, URL parse fallback |
| `src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt` | 17–100: remember factory/actual launcher, presentShareSheet, subject/completion/iPad anchor |
| `src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt` | 19–162: remember/actual launcher; handleShare, showNativeShare, handleFallbackShare, four fallback helpers, copyToClipboard |
| `src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibLoader.kt` | 8–85: LIB_NAME, whole loadNativeLibrary path/OS/arch/cache extraction/load/fallback |
| `src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeShareBridge.kt` | 10–49: static init, constants, init/isNativeShareSupported/showShareSheet native signatures |
| `src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt` | 10–114: remember/actual launcher, handleShare, tri-state map, text/URL/file/list paths |
| `src/webMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.kt` | 3–49: all six expect functions and result/clipboard contract |
| `src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt` | 5–56: support detection, four payload helpers, clipboard, handleSharePromise |
| `src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt` | 7–131: jsIsShareSupported; four jsShare* externals; jsCopyToClipboard; all actual wrappers; jsArrayPush |

### `calf-webview` — 20 files

| File | Lines / reviewed symbols and behavior |
|---|---|
| `build.gradle.kts` | 1–54: OS/arch classifier, Apple cinterop configuration, common/native/browser dependencies |
| `src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/Cookie.kt` | 3–23: all Cookie fields/defaults and millis/HttpOnly documentation |
| `src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.kt` | 3–33: default constructor and three suspend expect operations, outdated web-no-op comment |
| `src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt` | 3–171: every common/Android/iOS/Desktop setter/default and notification callback |
| `src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt` | 18–331: WebView expect; content variants/withUrl; loading variants; state expect; error DTO; navigator/events/all public commands; remember helpers; saveable helper/saver expect |
| `src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt` | 32–459: both composables/layout/factory/back; applySettings; both Accompanist client classes and all callbacks; state/all fields/applySettings/evaluateJavascript; navigation collector; Bundle saver |
| `src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/CookieManager.android.kt` | 12–98: manager getter/set/get/remove; buildCookieString/parseCookies; dispatch/callback/flush |
| `src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt` | 36–406: composable/effects/interop/release; state/delegate callbacks; applySetting/evaluateJavascript; native applySettings; collector; KVO observer keys/start/stop/observe; metadata saver |
| `src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt` | 24–125: default store getter, all three operations, property conversion/domain filter and sequential deletion |
| `src/iosMain/cinterop/nskeyvalueobserving.def` | 1–14: generated helper package, Objective-C Foundation protocol selector and pointer types |
| `src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt` | 25–269: composable/JFXPanel/lifecycle/listeners/content; state/applySetting/evaluateJavascript; native applySettings; command collector; metadata saver |
| `src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt` | 11–64: global getter/replacement, HttpCookie setter, metadata getter, removal |
| `src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt` | 19–250: composable/iframe content+listeners; state/settings/evaluation; sandbox; all commands; metadata saver |
| `src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.web.kt` | 11–47: document setter/getter/deletion and unsupported field behavior |
| `src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/PlatformUtils.web.kt` | 5–9: expected Window.evaluateScript |
| `src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.web.kt` | 7–12: generic expected interop adapter/signature |
| `src/jsMain/kotlin/com.mohamedrejeb.calf/ui/web/PlatformUtils.js.kt` | 5–6: dynamic Window eval actual |
| `src/jsMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.js.kt` | 9–21: Compose generic WebElementView adapter |
| `src/wasmJsMain/kotlin/com.mohamedrejeb.calf/ui/web/PlatformUtils.wasmJs.kt` | 6–12: windowEval JS intrinsic and expected extension actual |
| `src/wasmJsMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.wasmJs.kt` | 9–21: Compose generic WebElementView adapter |

### Scaffolds — 4 files

| File | Lines / reviewed symbols and behavior |
|---|---|
| `calf-maps/build.gradle.kts` | 1–13: only declarations; empty implementation |
| `calf-media/build.gradle.kts` | 1–47: excluded legacy plugin/targets/dependencies/namespace/JVM11 |
| `calf-notifications/build.gradle.kts` | 1–47: same excluded legacy scaffold |
| `calf-notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/notifications/Main.kt` | 1–26: unbuildable main, request authorization callback, undefined coroutine scope, sample notification request |

Also inspected as dependency/context, not claimed as complete ownership: `settings.gradle.kts`, shared target/convention helpers, version catalog, imported Gradle/deploy/native workflows, sample camera/share screens, Android manifest/provider paths, iOS privacy plist, IO KmpFile wrappers, improved file-picker cache, upstream `docs/webview.md`/`docs/share.md`, relevant archived issues/PRs/comments and original history. Full-repository coverage resides in [source inventory](../architecture/source-inventory.md).
