# Native features: current implementation and verification ledger

Area owner: `audit_native_features`. This additive development record covers
**NATIVE-001–039**: WebView, camera, share, and the empty/excluded maps, media and
notification experiments. The baseline [findings](../audit/findings/NATIVE.json),
[review](../audit/native-features.md), [module guide](../modules/native-features.md)
and archived upstream discussions remain historical evidence, not rewritten
descriptions of fixed code. The current machine-readable dispositions are in
[resolutions/NATIVE.json](resolutions/NATIVE.json).

**Checkpoint: 38 source implementations, one unresolved deny-only popup policy;
zero verified finding closures.** The latest focused JVM rerun, beginning
22:22:54Z on 2026-10-24, exited **0** after 19s: **WebView desktop 36/36 and
camera Android host 14/14**, including all seven actual JavaFX scenarios and
five Activity lifecycle fixtures. See
[the independently checked receipt](evidence/native/third-native-focused-verification.json).
The untouched WebView host/share desktop/share host/camera desktop suites retain
**86 passes + 1 exact Linux N/A** from the preceding broader batch, not this run.

That [second JVM batch](evidence/native/second-native-jvm-diagnostic.json)
remains **failed** (exit 1, 91.02s): its native-area 137 slots contained 134
passes, two fixture failures and one Linux N/A. The two failures were FX
throwable identity after suspension and camera remount readiness. Camera/share
iOS production/common-test KLIBs also compiled in four tasks, with **zero Apple
links or executed tests**; WebView was excluded. Do not relabel that older
batch all-green or count repeated common assertions as new authored tests.

After preserving those failures and the lead's 688 unchanged input hashes,
exactly two **test-only** corrections were refrozen at **22:22:29Z**:
[fixture corrections and all 73 scoped hashes](evidence/native/second-jvm-fixture-corrections.json).
The JavaFX fixture now uses a non-copyable exception sentinel while retaining
strict identity/type checks. Camera's helper idles the Robolectric framework
before remount polling, preserving the 5s timeout and all assertions. The focused
rerun matched those hashes and passed the complete two affected suites. No
production behavior changed.
Earlier failed receipts, source checkpoints, Rust checks and limitations remain
below. A host shadow, cross-check or passing subset is not native-device or
release certification.

**Latest inspected browser results (2026-10-25):** both complete-requested
**Wasm004 and JS004 passed: 290/290 cases, 19/19 modules and 48 fresh XML reports
per target**, with zero skips/errors/failures. Wasm ran 01:25:19Z–01:27:22Z
(exit 0/123.02s); JS ran 01:28:05Z–01:30:15Z (exit 0/130.03s).
Each target executed **WebView 30/30, camera 3/3 common cases and share 17/17**:
50 native-area cases in nine reports, or 100 target executions of 50 authored
functions across the two targets. All 693 selected input hashes were unchanged
within each run; all 75 held native inputs match both runs and the source freeze.
The new native-listener-detachment regression, opaque-iframe isolation and all
nine controlled-navigator Promise cases passed on **both** Kotlin targets.
See [the independently checked browser004 receipt](evidence/native/browser-004-native-verification.json).
This establishes bounded Chrome153/Linux regression execution, **not** real OS
sharing/camera, other browser engines, GC, popup/security, Apple/native-device,
consumer/ABI or release clearance. All prior failures remain below; all 39
finding statuses and all 115 original required tests are retained.

**Preserved focused browser result:** the focused JS command (23:17:59Z–
23:19:19Z on 2026-10-24) still **failed overall**, exit 1/80.01s, because of
an unrelated navigation test. Both affected native-area suites passed:
**WebView 29/29 and share 17/17**, zero skips/errors/failures, across eight fresh
reports. All 691 selected hashes and 73 scoped native hashes matched the fixture
freeze. The actual opaque-iframe isolation case now completes all assertions;
regenerated JS uses native `===`. All nine controlled-navigator Promise scenarios
execute successfully, alongside eight share common cases. See the
[independently checked focused receipt](evidence/native/second-native-js-verification.json).
Camera was not rerun. These are ChromeHeadless153/Linux results, not Wasm,
other-browser, real OS sharing/permission, device or release clearance.

**Preserved first browser result:** the first full JS command (23:00:48Z–
23:10:28Z on 2026-10-24) **failed**, exit 1/580.12s. WebView executed **29
cases: 28 passed, one fixture failure**; camera's three common cases passed;
share test compilation failed and **zero share cases executed**. The WebView
failure is a test's structural equality reading the opaque WindowProxy's
forbidden `equals` property, confirmed in emitted JS—not a demonstrated sandbox
escape. Its isolation assertions were not completed. Share's three homogeneous
expected lists failed type inference. The [pre-repair diagnostic](evidence/native/first-native-js-diagnostic.json)
preserves exact failures, generated-code excerpts and seven fresh report hashes.
After archival, precisely two test files were corrected and **73 scoped inputs
refrozen at 23:16:52Z**: [JS fixture receipt](evidence/native/first-js-fixture-corrections.json).
The source guard now uses `===`; three expected lists explicitly use
`listOf<ShareOutcome>`. All assertions, timeouts and production code are
unchanged. Their receipt describes the pre-rerun checkpoint; the subsequent
focused JS result above verifies the two affected suites without rewriting the
original failed run. Equivalent Wasm execution was still required at that
checkpoint; browser004 supplies later execution against separately frozen inputs.

**Latest inspected device result:** the third Android device batch exited 1
after 821.17s. On its API35 software emulator, WebView executed **25 cases: 24
common-contract passes and one actual-history fixture failure**. The test-only
`INTERNET` permission is verified in the merged host, correcting the second
run's setup defect. The unchanged history fixture now times out at initial
readiness, before any JavaScript history creation/assertions. WebView 124 reports
abnormal renderer termination, alongside long UI/runtime intervals; the available
event ordering does **not** establish its cause or that it caused the timeout.
That device evidence does not justify changing its production path, fixture or timeout.
Its 73 scoped native input hashes were held throughout that run; later attribution
and JVM-fixture-only deltas are recorded separately. Native-history/device gates stay open.
See [the third-run scoped receipt](evidence/native/third-webview-device-diagnostic.json)
and the preserved [second-run receipt](evidence/native/second-webview-device-diagnostic.json).

## Scope and ordering

The lead confirmed current upstream issue reconciliation before implementation
at 18:43:24Z on 2026-10-24. Existing packages, project paths, original API entry
points, `ShareResult` sealed cases, JNI/crate names and attribution are retained.
Shared Gradle/JavaFX/native-packaging changes belong to the build owner. The
native owner did not commit, push, publish, enable automation, or change GitHub
issue state.

Old upstream requests 288/344 being source-addressed do not resolve the distinct
callback/lifecycle findings in destination issues 77/75. Upstream 34 concerns a
camera **inside WKWebView**, not the standalone camera picker; it still needs an
actual WKWebView/device reproduction. Upstream 346's macOS cold-start crash is
not proved fixed by moving `JFXPanel()` out of composition. Maps 27 and media 245
remain scoped roadmap topics, not newly implemented subsystems.

## WebView ownership and execution contracts

### Native lifetime / state replacement (002, 003, 006, 037)

* Each target keys the native owner by `WebViewState`. Replacing the state means
  disposing that owner's view and creating a new one, rather than binding a null
  replacement state to a still-visible old view. A state is not a multiwindow
  view pool. Keep separate state/navigator instances for separate mounted views.
* `rememberUpdatedState` supplies current creation/disposal callbacks and the
  current navigator without replacing a running owner for an ordinary callback
  recomposition. The library installs its native reference, settings and
  listeners **before** invoking `onCreated`. Application customization therefore
  sees the actual view; future common settings can intentionally reapply values.
* Android `releaseAndroidWebView` saves the matching owner's native Bundle,
  stops loading, detaches clients/parent, destroys the view and clears matching
  state in `finally`, including a throwing application disposal callback. Old
  client callbacks check native identity before updating state.
* Desktop `DesktopWebViewOwner` owns its worker/progress/title listeners and
  native Scene/WebView. An atomic disposed guard rejects queued initialization
  and settings work. Disposal removes listeners, cancels the worker, unloads the
  document, clears the scene and matching state on FX. It does not exit the
  process-global JavaFX toolkit.
* Browser `BrowserWebViewOwner` removes its own listeners and navigates to an
  inert sandboxed `about:blank`, then clears its matching iframe/state in
  `finally`. A browser may still finish platform work asynchronously; DOM
  detachment is not a heap-profiler proof of collectability.
  The internal `browserEventListener` expect/actual creates one native
  `{ handleEvent: handler }` object retained for both add/remove calls. This is
  necessary because Wasm's external `EventListener : JsAny` cannot be implemented
  by a Kotlin anonymous object. The fresh JS/Wasm detachment regression checks
  native callback identity and delivery before disposed guards, not just quiet
  state after disposal; it does not establish GC or real-page lifetime.
* iOS records successfully registered KVO keys, disconnects its navigation
  delegate and stops the matching WKWebView on UIKit release. Partial creation
  and independent teardown stages preserve primary failures rather than skipping
  all later cleanup. Apple compilation, Instruments ownership,
  late callbacks and replacement during native presentation remain acceptance
  tests, not Linux-verified behavior.

### Navigation / loading (001, 004, 005, 007, 008, 016)

`WebViewNavigator` now has a bounded 64-command channel rather than a replay-one
broadcast flow. A command sent before attachment is consumed once; an already
consumed Back/Forward/Reload/Stop is not replayed on reattachment. There is one
active consumer; a second concurrent consumer is rejected. A full queue throws
explicitly rather than silently dropping a command. Calls after the navigator's
owning coroutine scope is cancelled are ignored. Header maps are copied at the
call boundary. Applications must not intentionally flood a detached navigator.

After successfully acquiring the single-consumer guard, Android/iOS attachment
snapshots `canGoBack` and `canGoForward` directly from the matching native view.
Replacing only a navigator therefore does not wait for another history event;
a rejected second owner cannot overwrite capabilities through the initializer.
The new Android host test mounts the production Compose/WebView binding but uses
explicitly Robolectric-supplied history. A separate device test builds real
WebView history with local inline HTML and JavaScript `history.pushState`. Its
first executed attempt failed during provider settings from the missing test-host
INTERNET permission, before that history. The next run verifies the narrow
host-manifest fix, but times out at `state.webView != null &&
state.loadingState == LoadingState.Finished` (test lines 38–40). No native history
is created or asserted. The fixture records neither the separate conjunct values
nor native callback timestamps, so it cannot identify which readiness condition
remained false. Increasing its timeout without a diagnosis is not a repair.

The Desktop stop branch calls `engine.loadWorker.cancel()` directly; it cannot
call `WebViewNavigator.stopLoading()` recursively. State and navigator loads
share platform loaders. Browser URL loads always remove `srcdoc`; inline loads
remove `src`. Every new accepted request clears old errors/title/final URL and
starts `Loading(0f)`. `requestedUrl` is distinct from observed `lastLoadedUrl`.
An iframe load event cannot prove network success, authentication, or successful
framing under CSP/X-Frame-Options. Opaque/cross-origin metadata/history are
unavailable rather than a stale same-origin title presented as current content.
Internal links, redirects, provisional failures and stop/reload transitions need
the target-specific tests in the original ledger. Desktop now takes the fresh
`engine.location` at `Worker.State.SCHEDULED` instead of the previous request's
URL. JavaFX 21.0.13 worker bytecode was inspected for location-before-SCHEDULED
ordering; that static check is not runtime proof. The new actual-engine local
HTTP test separately asserts A → native link B → redirect C, pending versus
completed saver URLs, reload and back/forward. Its C responses are gated;
unrelated requests (for example favicon) return 404 without consuming those gates.
This actual Linux JavaFX scenario passed in the second JVM batch; it does not
validate equivalent Chromium, WKWebView or iframe behavior.

Unsupported content options now produce a request error (code `-2`) instead of
silently loading different content:

| Option | Android | iOS | Desktop | Browser |
|---|---|---|---|---|
| Initial URL headers | Native initial load only | Initial request only | Rejected | Rejected |
| HTML `baseUrl` | Native | Native HTML base URL | Rejected | Rejected |
| HTML encoding | Native options | UTF-8/UTF8 only | UTF-8/UTF8 only | UTF-8/UTF8 only |
| Non-HTML MIME / `historyUrl` | Native options | Rejected | Rejected | Rejected |

No implementation promises credential headers on subsequent links/subresources
or across redirects. Automatic cross-origin forwarding is deliberately not a
compatibility workaround. iOS state and navigator HTML both use the same Unicode
HTML loader, without incorrectly labeling UTF-8 bytes as another encoding.

Android keeps its native Bundle saver. The non-Android saver explicitly restores
only an HTTP(S) URL as a **new GET**; it does not preserve native history, forms,
scroll position, headers or inline HTML. It accepts the old `lastloaded` key but
never restores a stale title over `NavigatorOnly`. Applications with one-time
URLs, POST-based flows or sensitive authentication should choose explicit state
restoration rather than assume browser-session persistence. URL selection is now
explicit: initializing state may use its declarative URL; an accepted pending
load uses `requestedUrl`; a finished load uses the nonblank observed
`lastLoadedUrl`, falling back to its request only if no final URL was observed.
Validation occurs after choosing that candidate. A known non-HTTP final page
does not revive an old HTTP URL, and navigator HTML cannot restore stale
declarative URL content. Three new common tests cover these rules and passed on
the API35 emulator in the failed second and third device batches. The actual
Linux JavaFX link/redirect/reload/history regression also passed in the second
JVM batch. Equivalent Android/iOS/browser regressions remain unverified.

### JavaScript / browser isolation (010, 015)

`BrowserSandboxPolicy.Isolated` is the new browser default. JavaScript opt-in adds
`allow-scripts` but **never** `allow-same-origin`. Inline HTML therefore has an
opaque origin and cannot simply read/mutate the host DOM or storage. Optional
popups remain sandboxed; this is not an origin-validation policy for application
`postMessage` handlers. `BrowserSandboxPolicy.Trusted` is a separate deliberate
escalation for fully host-controlled content; with JS enabled it removes the
sandbox. Do not select Trusted for remote/user/AI-provided HTML to restore old
behavior. Sandbox changes have next-navigation semantics; changing an attribute
does not revoke script capabilities already granted to a running document.

The first real JS isolation regression exposed a **test-oracle** error: Kotlin
`incoming.source == frame.contentWindow` lowered to `equals(...)`, whose runtime
helper accessed `obj1.equals`. That read is prohibited on an opaque/cross-origin
WindowProxy. The fixture now compares strict reference identity with `===`,
preserving its source guard rather than removing it or weakening the sandbox.
The failed run completed neither the isolation-message nor subsequent parent-DOM/
sandbox assertions. The exact generated witness and original failure remain in
the [first JS diagnostic](evidence/native/first-native-js-diagnostic.json);
the subsequent [focused JS rerun](evidence/native/second-native-js-verification.json)
passes the original isolation-message, parent-DOM and sandbox assertions. Its
emitted comparison is native `===`, not a runtime `equals` call. The later
browser004 JS and Wasm runs both pass the same isolation assertions after the
native-listener factory repair. Other browser engines remain unverified; these
successful origin-boundary fixtures do not certify all sandbox/popup/navigation
security behavior.

The additive `evaluateJavascriptResult` returns `JavascriptResult.Value(json)`,
`Undefined`, `Error(message)` or `Unavailable(reason)`. A string envelope avoids
native `null`/`undefined`/object-string ambiguity; numbers, strings, objects and
JSON null use JSON serialization. Cyclic values/throwing code are errors; the
API does not await JavaScript Promises. Isolated/unattached views report an
explicit unavailable result. The legacy nullable-string evaluation method stays
available with platform-dependent formatting; new portable code should use the
typed result. Callbacks sit outside platform evaluation catches, so an application
exception is not converted into a second result. Android typed and legacy calls
now share an atomic one-settlement boundary: a native invocation failure before
completion yields one Error (legacy null), a synchronous completion followed by
native/application throw preserves that exception without another result, and
a callback queued before a failing invocation is ignored after failure settles.
A callback that actually arrives after its Android native owner was released
yields Unavailable. Desktop uses a distinct detached-owner failure for the
queued disposal/evaluation race, without mapping genuine script failures to
Unavailable. Eight controlled Android callback-boundary tests and one actual-FX
race test passed in the second JVM batch. The Android subclass does **not** execute
Chromium JavaScript. Native destruction can drop an already-pending callback
altogether; the API cannot promise delivery in that case. Mobile off-Main,
real-engine values and Apple callback/lifecycle behavior still need execution.

### Settings and Desktop runtime (009, 017, 018, 036, 038, 039)

* iOS gesture capture is `captureBackPresses && allowsBackForwardNavigationGestures`;
  later URL loads no longer force gestures on. `allowsInlineMediaPlayback` is
  placed in the `WKWebViewConfiguration` **before construction**. Changing a
  creation-only setting after attachment reports an explicit request error;
  recreate state/view for a new configuration. Real iPhone video/swipe behavior
  remains unverified.
* Desktop captures each native engine's original user agent and restores it when
  `customUserAgent` becomes null. Cold `JFXPanel` construction is deferred through
  a coroutine and the next AWT event, outside composition. This reduces the
  known dangerous startup path; it is not a proof against macOS nested-event-loop
  crashes. A headless/missing-JavaFX host gets an explicit configuration failure.
* Shared build changes make the producer's JavaFX dependencies compile-only.
  The application must provide **all six matching JavaFX 21.0.13 modules**:
  base, graphics, controls, media, web and swing, for its own OS/CPU classifier.
  See the build owner's `DesktopJavaFx.kt` helper and consumer instructions. The
  host must not call `Platform.exit()` while a library view remains mounted.
* Android popups are explicitly rejected by `onCreateWindow`; no arbitrary URL
  is opened in another application, and no child WebView is leaked. This is a
  **deny-only policy**, not implementation of multiple windows. The legacy
  `supportMultipleWindows` property is not a promise of a rendered child. Popup
  login/payment flows needing an accept/deny API remain unresolved scope.
* Android hosts using default network-loading settings must declare
  `android.permission.INTERNET`, including an inline-HTML fixture whose settings
  still permit network loading. The real API35 provider threw from
  `setBlockNetworkLoads(false)` in the test host without that permission. The
  fix adds only a **test-host** manifest permission: no production manifest,
  cleartext blanket allowance or network-security/trust override was introduced.
* Equal-value setting assignments do not notify. `settings.batch { ... }` nests
  and sends one notification even when a batch exits by exception. Desktop
  coalesces pending FX settings tasks; Android errors use a single observable
  list rather than copying an ever-growing list for each resource failure. These
  changes are not measured CPU/RSS improvement claims. Treat common settings
  mutation as UI-thread-confined; batching is not a general concurrent transaction.

## Cookie behavior (011–014)

All setters validate HTTP cookie tokens/values, path/domain delimiters, expiry
range, host applicability and `__Host-`/`__Secure-` prerequisites before native
serialization. Cookie names/values containing injection delimiters fail rather
than adding extra attributes. Dates are formatted as HTTP UTC dates, not raw
epoch milliseconds. Returned metadata depends on the actual native API.

| Target/backend | Supported ownership / important limitation |
|---|---|
| Android | Native `android.webkit.CookieManager`; false setter acknowledgment is an error. Request-header reads do not expose complete flags/expiry metadata. |
| iOS | WKHTTPCookieStore calls run on Main; standard Foundation response-header parsing constructs native cookies. Request filtering includes host, path boundary, secure scheme and expiry. Native host-only/domain ambiguity remains: bare domains are conservatively exact-host. |
| Desktop default | Adapts the existing `CookieHandler`; **never replaces the global handler**, including JavaFX's non-`java.net.CookieManager` implementation. |
| Desktop explicit | Platform constructor `CookieManager(handler)` is an opt-in backend without global installation. Java `CookieManager` uses request headers plus path/domain/secure filtering; original expiry is retained for cookies set through that manager. Unknown external creation-time/expiry is null, not invented as `now + maxAge`. |
| Browser | Manages the host document's currently accessible cookies only, not a cross-origin iframe store. URL host/scheme/path must match its supported current document context. HttpOnly and full-store deletion are explicitly unsupported. |

`removeAllCookies()` throws `UnsupportedCookieOperationException` for browser
JavaScript and generic Desktop handlers that cannot enumerate/delete the whole
store. Browser-only `removeCookiesSetByThisManager()` removes only identities
tracked by that instance; it is **not complete logout**. Server-set HttpOnly,
other paths/domains and other browsing partitions need the application's own
logout protocol. Browser policies may reject a write even with syntactically
valid data. A null expiry can mean session **or inaccessible metadata**, and the
old `Cookie` constructor remains compatible. Full real-engine/native request
comparison and browser-engine expiry matrices remain required.

## Camera: additive outcomes and output ownership (019–024, 033)

`rememberCameraPickerResultLauncher(options, onResult)` returns the existing
launcher interface but reports `Captured`, `Cancelled`, `Busy`, `Unavailable` or
`Failed(Configuration/Permission/Io/Launch)`. The existing
`rememberCameraPickerLauncher((KmpFile) -> Unit)` remains a success-only adapter;
it intentionally cannot report failures without changing its callback type.
The latest callback handles a still-active request. Busy is the result of the
rejected second launch, not completion of the original capture. Disposal
abandons owned work and suppresses late application callbacks.

Android saves the pending output URI **and** owned path together before external
launch. ActivityResult restoration binds to a new stable owner; result handling
takes/clears that saved request once before callbacks. Terminal cancellation,
failed capture and known launch/configuration failure clean only a canonical file
under `cacheDir/nativecmpkit-camera/` named
`capture-*.jpg`; a forged/stale path outside that directory is not deleted.
Successful capture requires a nonempty owned output. Following independent
review, the owner now checks the **actual Activity**, not a navigation entry's
LifecycleOwner: non-finishing configuration/destruction retains a restorable
request even when Compose disposes before `Activity.isDestroyed` becomes true.
Finishing an Activity or removing a live composition abandons callback ownership.
Neither operation unlinks an in-flight output: unregistering an ActivityResult
callback cannot stop an external camera or revoke its open descriptor. An
abandoned output may therefore remain in app cache until safe host/OS cleanup;
there is no eager orphan deletion while a camera could still write.

A new `LocalContext` wrapper around the same Activity can create a successor
owner sharing the saved request/registry. The old owner's disposal preserves the
successor's request and does not clear its callback holder. Per-launch request
identity also protects synchronous result A → application launches B → application
throws: B stays pending, successful A's bytes remain caller-owned, and no second
failure is synthesized. The first independent review's R1/R2/R3 traces remain
preserved; these are source repairs, not closed runtime findings.

Five Robolectric tests exercise actual ComponentActivity/Compose save,
non-finishing destroy/restore, `ActivityController.recreate()`, live removal,
finishing, and context-wrapper transfer. An additional controlled registry-driver
test covers synchronous callback reentrancy/throw. External file writers/result
codes are explicitly simulated. Four lifecycle fixtures and all six driver
cases passed in the second JVM batch. The live-removal fixture passed its
removal/disposal/output-existence and stale-result suppression assertions, then
timed out while waiting for **remount**. Its second request/cancellation and
final first-output byte readback were not reached. The helper's new pre-poll
framework-idle step and UI-thread read preserve the 5s limit and all assertions.
The subsequent focused run passed **all five lifecycle fixtures**, including
remount, the second non-Busy request, cancellation cleanup and final original-file
byte readback. These remain host lifecycle tests with simulated external writers.
Actual don't-keep-activities, process death, camera applications and API24+ URI
grants remain device gates. No hardware/intent/provider does not silently look
like a successful capture.

iOS owns one request, picker, strong delegate, options snapshot and encoding job
per UIViewController. All UIKit construction/presentation is on Main. Busy,
missing usage strings, no allowed source and occupied/detached presenters have
explicit outcomes. The delegate dismisses before background PNG/JPEG encoding;
PNG is the compatibility default, optional JPEG quality is validated in [0,1].
UUID-named output is known before worker dispatch; cancellation/failure cleanup
is request-specific, including eventual cleanup after synchronous file writing
returns. Successful files are caller-owned cache outputs: copy for persistence;
the OS may evict cache files and the library does not delete a successful result
while its consumer is reading it. Full-resolution encoding still allocates the
encoded image; moving work off Main is not a peak-memory optimization proof.
12/48MP latency/RSS/disk-full tests and real privacy-denial behavior remain open.

Desktop and browser explicitly return Unavailable in the new API. No camera
implementation was invented to make their target declarations look complete.

### Android provider setup for camera and local-file sharing

The host, not the library, chooses a FileProvider authority. Both option types
accept `androidFileProviderAuthority`; null preserves the legacy
`${applicationId}.provider` authority. Do not register two different providers
with the same authority. Configure narrow paths, for example:

```kotlin
class NativeCmpkitFileProvider : androidx.core.content.FileProvider()
```

```xml
<!-- Inside application; replace class name with the host's provider subclass. -->
<provider
    android:name=".NativeCmpkitFileProvider"
    android:authorities="${applicationId}.nativecmpkit.files"
    android:exported="false"
    android:grantUriPermissions="true">
    <meta-data android:name="android.support.FILE_PROVIDER_PATHS"
        android:resource="@xml/nativecmpkit_file_paths" />
</provider>
```

```xml
<paths xmlns:android="http://schemas.android.com/apk/res/android">
    <cache-path name="camera" path="nativecmpkit-camera/" />
    <cache-path name="outgoing" path="outgoing-share/" />
</paths>
```

Pass the **same authority** in `CameraPickerOptions` / `ShareOptions` and copy
other app-owned share files into an intentionally allowed outgoing directory.
Do not use broad root/external/cache `path="."` examples as a production security
policy. The sample XML was narrowed to the two folders above after the NAV and IO
owners confirmed no other sample/picker cache staging needs broad access. A
valid sample host/provider/recipient is still a separate integration check. Camera API23
retains its legacy file-URI path. The new share conversion uses FileProvider on
API23 too; local-file sharing therefore requires the configured provider on all
supported Android versions, an intentional behavior change. Existing grantable
`content://` URIs are forwarded without unnecessary copies. Permission grants
and recipient reads need a real host/recipient device test.

iOS hosts provide `NSCameraUsageDescription`, and
`NSPhotoLibraryUsageDescription` if using the allowed library fallback. The new
launcher preflights strings but cannot make an absent entitlement, OS privacy
denial or hardware capability work. The standalone camera does not configure
WKWebView capture delegates.

## Share: outcomes, safe fallback and native lifetime (025–034)

The new `rememberShareOutcomeLauncher` has stage-aware outcomes: `Presented`,
`Selected`, `Completed`, `CopiedToClipboard`, `Dismissed`, `Busy`, `Unavailable`
and `Failed`. Completed means the **platform reports completion**, never that a
remote recipient read the content. Existing exhaustive `ShareResult` callers
retain exactly their original cases; the adapter maps presented/selected/
completed/copied to legacy Success. Do not use that old Success to decide when
to delete a shared file. `ShareContent.Files` is snapshotted at launch; invalid
empty lists, blank/CRLF MIME and blank URL payloads fail explicitly.

* **Android:** starts the chooser on Main and returns Presented, not Completed.
  Application callback execution is outside the launch catch. Local file URIs
  are converted by the configured FileProvider; existing content URIs retain
  their identity. Every URI is in read-granted ClipData and the stream extras;
  an application context gets NEW_TASK. Unsupported schemes are rejected. No
  claim is made to observe chooser cancellation or recipient completion.
* **Browser:** requires secure-context/function capability checks, `canShare`
  for files and the original user gesture. The launcher does not dispatch before
  `navigator.share`. Both Web Share and clipboard use separate Promise success
  and rejection handlers, not a trailing catch that converts application errors
  into second results. Clipboard success waits for actual Promise settlement.
  The owner token suppresses stale/duplicate/disposed results and preserves the
  active request during a rejected concurrent launch. Real browser permission,
  user-activation and OS share dialogs remain separate tests.
* **Desktop fallback:** only text/URL **clipboard copying**, if explicitly
  allowed by options. Files are Unavailable. The implementation never calls
  `Desktop.open`/`Desktop.browse`; copying a URL cannot invoke its OS handler.
  A native denied/failed/dismissed operation does not automatically copy or
  open content. Native unavailable may use the allowed clipboard fallback.
* **iOS:** a stable Main-confined owner validates presenter/in-flight state,
  retains security-scope leases through completion, anchors iPad popovers and
  clears its delegate/block/leases before application completion. It reports
  native cancellation/error distinctly. Subject comes from UIActivityItemSource
  `subjectForActivityType`, not merely the controller's window title. All
  Objective-C signatures, Mail integration and security-scope receiver lifetime
  need Apple compilation/device evidence.

Subjects are now supplied for all web payload kinds and to native macOS services.
A clipboard has no mail-subject channel. Individual services may ignore optional
metadata; integration tests must distinguish supplied data from OS delivery.

### Desktop JNI and AppKit

Existing exports including the old blocking `showShareSheet` remain for ABI
compatibility. New Kotlin uses ABI version 1 and nonblocking `beginShareSheet`,
`takeShareResult`, `cancelShare`, plus count-only diagnostics. JNI validates whole
input arrays and releases each local reference; it does not silently omit a
failed string element. A borrowed nonzero `parentWindow` address is rejected:
the async implementation acquires/retains the focused native window on Main.
This is an intentional behavioral safety restriction on the old optional handle.

`operation.rs` is a mutex-guarded, bounded (64 unconsumed results), single-flight
registry of numeric IDs and Rust Arc completion values. First terminal result
wins. An old callback cannot clear a new active identity. Cancellation removes
the registry's Arc but holds the active slot until Main cleanup acknowledges
finish. No Arc owning raw pointer crosses the delegate boundary.

`macos.rs` dispatches **Rust Send values only** through libdispatch. Main creates
and owns picker, delegate, selected service, subject, item array, focused window
and anchor view in a thread-local table. The delegate ivar is only an integer ID.
Callback cleanup is deferred to another Main turn so the callback receiver is
not destroyed while executing. It clears service/picker weak delegates, closes
the picker, drops native owners, then publishes the registry result. A selected
service is not success: `didShareItems` is success and `didFailToShareItems` is
failure. There is no `mem::forget`/raw-Arc retention scheme or unsafe Send wrapper
around AppKit objects. A runtime without picker `close` support is unavailable.

Kotlin polls asynchronously at 25ms with a finite configured timeout (1–600s);
it does not occupy an IO worker waiting five minutes. Cancellation schedules
Main cleanup in `finally`. That scheduling is asynchronous: a timeout/disposal
can return before Main has physically closed the picker, and the native registry
will reject a new request as Busy until cleanup completes. Cancellation cannot
retract external effects already handed to a selected service. The old ABI
adapter still blocks non-Main callers, with one absolute 300-second deadline;
new application code must use the new launcher rather than that legacy bridge.

Native availability/presentation depends on a real focused application window
and AppKit run loop. The documented AppKit user-gesture requirement, actual
cancel responsiveness, service completion/failure and thousands of cycles under
Instruments/ASan are **not** established by Rust unit tests or cross compilation.
Rust panic recovery at dispatch boundaries does not claim to catch Objective-C
exceptions.

### Native extraction cache

The cache uses the full SHA-256 digest in the immutable filename, separates
version/architecture contents, checks bytes before reuse and loading, rejects
symlink components, validates directories and applies private POSIX permissions.
Atomic installation and verified unique-file fallback do not replace another
loaded DLL. Corrupt existing entries fail rather than being trusted. The
`System.loadLibrary`-first route remains for explicitly managed packager paths;
external native code is trusted according to the host's loader configuration,
not falsely certified by the extraction hash. Same-user attackers can still
modify their own process/files; content addressing is not a sandbox. Windows
loaded-DLL races, read-only/symlinked homes and cross-process stress still require
actual tests. The root-owned native payload manifest binds sources/lock/toolchain
and JNI declarations separately from this runtime extraction mechanism.

## Incomplete modules (035)

`calf-maps` remains included but has **no implementation/API** and no publication
plugin. `calf-media` and `calf-notifications` remain excluded experiments; their
stale Gradle/scripts are not turned into release artifacts. Notification
permission modules are a separate supported code path, not a scheduler. Enabling
these experiments requires fresh design, build configuration, actual platform
implementations, privacy/setup documentation and tests. Documenting that status
resolves a representation problem, not the upstream feature requests themselves.

## Executed evidence and remaining tests

The initial bounded Rust command receipts record exact working-tree source/lock/
toolchain hashes, exit status, log digest and limitations:

* [Linux Rust tests](evidence/native/share-rust-linux-tests.json):
  `CARGO_BUILD_JOBS=2 cargo test --locked --manifest-path calf-share/native/Cargo.toml`,
  **6 passed, 0 failed, 0 ignored**. Tests exercise the real Rust registry, including
  10,000 ownership cycles; they do not instantiate a picker/delegate or invoke JNI.
* [Linux Clippy](evidence/native/share-rust-linux-clippy.json):
  `CARGO_BUILD_JOBS=2 cargo clippy --locked --manifest-path calf-share/native/Cargo.toml --all-targets -- -D warnings`,
  exit 0; **not a test suite** and not macOS source compilation.
* [Apple Rust cross-check](evidence/native/share-rust-apple-cross-check.json):
  `CARGO_BUILD_JOBS=2 cargo check --locked --manifest-path calf-share/native/Cargo.toml --target aarch64-apple-darwin`,
  exit 0. The first inspected run compiled/checked actual objc2/AppKit bindings
  and module source in 34.79s; the recorded repeat reused that cache and waited
  for a Cargo package-cache lock. **Zero Apple links, executed tests or UI checks.**
* [Camera/share iOS KLIB compilation](evidence/native/camera-share-ios-klib.json):
  the lead's `first-ios-klib` command began at 19:40:54Z on 2026-10-24 and exited
  **1** after 85.01s because navigation and Bluetooth/Wifi permission sources
  failed to compile. Within that batch, both `compileKotlinIosSimulatorArm64`
  and `compileTestKotlinIosSimulatorArm64` **executed successfully** for camera
  and share, rather than being skipped/cached. The post-run receipt checked all
  222 selected input hashes unchanged. This checks actual Kotlin/Native UIKit
  signatures and common tests against iOS KLIBs on Linux, **not** Apple linking,
  simulator/device execution, main-thread behavior, delegates or memory lifetime.
  There were **zero test executions**. WebView and its custom Apple cinterop were
  not in this command; its iOS source compilation remains outstanding. These
  were held working-tree sources, not immutable release/consumer evidence.
* [First desktop/Android diagnostic](evidence/native/first-desktop-android.json):
  the lead's Xvfb `first-native-and-third-android-host` batch began at 19:47:22Z
  on 2026-10-24 and exited **1** after 50.01s. All 207 selected input hashes were
  unchanged during the run. All three libraries' Android and desktop production
  compilation tasks executed successfully. Fresh WebView XML has **25 passing
  common/JDK-cookie cases and one failed class-initialization result**, not an
  executed JavaFX scenario; the typed-JS test inferred a non-void JVM return.
  Camera XML has **2 passes, 1 failure**: the empty-state test incorrectly
  force-unwrapped `listSaver`'s null empty-save result. Share desktop test and all
  three Android host test compilations failed on harness type/API mistakes;
  **zero share/JNI or native-area Android tests executed**. The subsequent six
  test-file corrections preserve assertions, explicitly exercise empty-save
  initializer/empty-list restoration, and initially awaited rerun. The camera
  common-test correction also postdated the first iOS KLIB receipt; its updated
  iOS compilation is recorded in the second JVM/iOS batch below. Those six harness
  repairs alone changed no production
  source; the later source checkpoint below deliberately does, so the earlier
  successful production tasks cannot certify the current tree.
* [First WebView device diagnostic](evidence/native/first-webview-device-diagnostic.json):
  the lead's `first-android-device` command began at 20:22:20Z and exited **1**
  after 84.02s. The updated `:calf-webview:compileAndroidMain` executed
  successfully; `compileAndroidDeviceTest` failed and **zero device tests ran**.
  All 12 captured WebView inputs match the native source checkpoint. The shared
  `matching { name == "androidDeviceTest" }` predicate accidentally referenced
  `Project.name`, so required AndroidX/Compose test dependencies were absent.
  The build owner verified that bytecode cause and changed only `name` to
  `it.name` in this module at 20:24:43Z. The native
  [build-delta receipt](evidence/native/post-review-build-delta.json) reconstructs
  the old hash from that one substitution, confirms the other 71 checkpoint
  inputs unchanged, and matches all 72 updated inputs to the lead's next global
  snapshot. The first collector's omitted 19 shared files have an explicit
  prior-snapshot-bound supplement, not an overwritten input capture. No APK,
  real-history success or camera/share test result is implied.
* [Second WebView device diagnostic](evidence/native/second-webview-device-diagnostic.json):
  the lead's `second-android-device` batch began at 20:25:33Z and exited **1**
  after 727.14s. The complete 687-input snapshot stayed unchanged during the
  run. WebView device-test compilation and APK assembly executed successfully;
  its production compilation was UP-TO-DATE from the first device diagnostic.
  Personally inspected XML contains **25 executed, 24 passed, 1 failed, 0 skipped**
  on the task-owned software Android15/API35 x86_64 emulator. All passes are
  common-contract cases, including the new three saver-precedence cases and
  exclusive attachment-initializer case. The real Compose/WebView history case
  failed during provider `setBlockNetworkLoads(false)` because the merged test
  manifest lacked INTERNET. No history assertions passed. The subsequent
  `src/androidDeviceTest/AndroidManifest.xml` declares only INTERNET; XML/static
  checks passed at that checkpoint; the corrected host was then built/run in the
  third diagnostic below. No Kotlin production/test body changed. Cameras are disabled on this
  emulator, and this run selected no camera/share/Android-host/JavaFX tests.
* [Third WebView device diagnostic](evidence/native/third-webview-device-diagnostic.json):
  the lead's `third-android-device` batch began at 20:42:41Z and exited **1**
  after 821.17s. Its 688 global input hashes stayed unchanged, including all
  **73 personally matched native inputs**. Test-host manifest merging, resource
  processing and APK packaging executed; WebView production/test compilation
  reused previous outputs. The archived merged test manifest contains INTERNET.
  Inspected XML again has **25 executed, 24 passed, 1 failed, 0 skipped**. All
  passes are common contracts; the real fixture fails at its unchanged
  15,000ms initial-readiness wait (whole test: 60.474s). No JavaScript history
  creation or native-history assertion was reached.
  A narrowly inspected, test-specific runtime log identifies System WebView
  **124.0.6367.219** and reports a 13,812ms frame, 607 skipped frames and
  concurrent GC lasting 10.971s with roughly 107/111ms pauses—not a 10.971s
  stop-the-world pause. The renderer's abnormal termination is logged after
  Activity destruction, while a Crashpad process starts earlier. Matched
  Chromium source shows the reported `code 5` is `crash_signo`, not an ordinary
  process exit status; the separate Zygote clean-exit line does not nullify that
  provider report. Exact crash onset, causality, EGL fallback significance and
  any memory-pressure cause remain unproved. Only 19 selected nonsensitive
  diagnostic events are preserved, not full logcat/crash dumps. No new source
  or fixture defect is demonstrated. Keep assertions/timeouts unchanged and
  native gates open; separately authorized bounded state/callback diagnostics
  and an adequately resourced real/accelerated-device run are the next options.
* [Second native JVM / iOS diagnostic](evidence/native/second-native-jvm-diagnostic.json):
  the lead's `second-native-and-fifth-ios` batch began at 22:14:30Z and exited
  **1** after 91.02s. Its 688 global input hashes, including all 73 scoped native
  inputs, stayed unchanged. A separate, reversible
  [attribution-only insertion](evidence/attribution-notices-20261024T2210.json)
  preceded this run; prior source hashes are not silently relabelled as current.
  All six native JVM tasks ran: **134 passes, 2 failures, 1 exact Linux N/A**
  in 137 slots/25 reports. WebView desktop: **35/36**; WebView host: **41/41**;
  share desktop: **26 passes + 1 macOS-only N/A**; share host: **16/16**;
  camera desktop: **3/3**; camera host: **13/14**. All seven real JavaFX scenarios
  executed, with six passes and one throwable-identity failure; no headless skip
  was counted as a pass. The JNI ABI, borrowed-pointer rejection and Linux
  unsupported-host lifecycle cases passed; AppKit was not executed. The seven
  actual-filesystem cache cases, including POSIX permissions, passed.
  Camera/share iOS production and common-test KLIB compilation executed in four
  tasks; **zero Apple links or test executions**. This refreshes the earlier
  camera empty-saver test compilation but not WebView's unavailable Apple cinterop.
  The failed FX identity assertion precedes all failed-creation cleanup checks.
  The camera failure is the remount barrier, not first Activity creation or the
  already-reached removal assertions. The
  [dependency-bytecode witness](evidence/native/second-jvm-harness-bytecode.json)
  records coroutine exception-copy behavior and the distinction between
  `waitUntil`'s test-clock advancement and Robolectric framework idling. Those
  paths motivate the two narrow corrections below, not a production rewrite or
  a claim that all cleanup/remount gates passed.
* [Third focused native verification](evidence/native/third-native-focused-verification.json):
  the lead's `third-native-focused` command began at 22:22:54Z and exited **0**
  after 19s. Both changed test compilations executed. Independently checked
  before/after input maps are equal for **688 inputs**, and all 73 scoped native
  hashes match the correction freeze. Ten archived XML reports are fresh within
  the command interval and retain exactly the preceding tasks' case inventories:
  **WebView desktop 36/36, camera Android host 14/14**, zero skips/errors/failures.
  All seven real JavaFX scenarios and five host Activity lifecycle scenarios ran.
  The strict non-copyable exception sentinel now reaches and passes the failed-
  creation native state/owner/Scene cleanup and no-extra-disposal checks. The
  camera fixture reaches and passes remount, unique second request, no inherited
  Busy, cancellation cleanup and original-output byte readback. The earlier
  failed receipts remain unchanged. Other native suites were not rerun; their
  successful second-batch results keep that provenance. No iOS/Chromium/device,
  AppKit, browser, recipient-process or artifact consumer gate is cleared here.
* [First full JS native-area diagnostic](evidence/native/first-native-js-diagnostic.json):
  the lead's complete-requested JS command ran from 23:00:48Z to 23:10:28Z,
  **exit 1/580.12s**. All **691 helper input hashes** matched before/after,
  including all 73 personally checked native hashes. The lead's broader 703-input
  freeze additionally covers notices/identity/license files; it is not the helper's
  count. Seven native-area reports are fresh and match their archived testcase
  statuses. ChromeHeadless153/Linux executed WebView **28 passes + 1 failure**
  (24 common contracts, four actual browser passes, one browser fixture failure)
  and camera **3 common passes**. Share failed `compileTestKotlinJs` at
  `WebSharePromiseTest.kt:66,73,99`: **zero share tests executed**. The other
  full-suite failure belongs to navigation and is outside this area's diagnosis.
  The WebView `SecurityError` names the forbidden WindowProxy `equals` property;
  generated `commons.js:164042` invokes structural equality and its helper at
  line113098 reads that property. It is not a production-origin escape or a
  completed isolation assertion. The four successful browser scenarios cover
  both URL-load paths removing `srcdoc`, disposal despite application throw,
  failed-creation owner cleanup, and real cookie expiry/explicit unsupported
  boundaries. No other browser engine, real sharing UI or camera capture ran.
  The [immutable full-suite archive](evidence/js-full-001/archive.json) retains
  the overall failed result and original report evidence. The two subsequent
  test-only repairs below do not turn it into a passing run.
* [Focused JS native verification](evidence/native/second-native-js-verification.json):
  the lead's explicit navigation/share/WebView subset ran from 23:17:59Z to
  23:19:19Z, **exit 1/80.01s**. The complete command still failed its unrelated
  navigation controller test: **83 cases = 82 passed + 1 failed**. Its native-area
  suites passed **46/46**: WebView **29/29** (24 common + five browser scenarios)
  and share **17/17** (eight common + nine controlled-navigator Promise scenarios).
  Both test and executable JS compilations actually ran. All 691 selected input
  hashes matched before/after; all 73 native hashes match the fixture freeze.
  Eight raw/archived XML reports have personally matched hashes, testcase
  statuses and timestamps within the command interval. WebView retains the
  original 29-case inventory, and share's 17 cases match its authored common/web
  functions. The actual opaque iframe reports `isolated`, leaves no parent escape
  attribute and retains `allow-scripts` without `allow-same-origin`. The generated
  test now emits `incoming.source === frame.contentWindow` without reading the
  foreign WindowProxy's properties. Share's original callback/order assertions
  pass: delayed success, rejection/abort, text subject/file metadata, callback
  exceptions, disposal, busy ownership, unsupported payload and synchronous
  failure. Navigator methods are controlled; real OS clipboard/share permission,
  transient activation, dialogs and recipient completion are not tested.
  Camera was not selected and retains its earlier three common JS passes.
  The local root-container Chrome runner uses `--no-sandbox`/`--disable-dev-shm-usage`;
  these process-runner flags neither change production iframe settings nor
  certify a production browser's security. At that checkpoint there was no
  Wasm result; other-browser, native-device, Apple, artifact/consumer, remote-CI
  and release gates were not cleared. Both original failed JS command archives
  remain failed and unchanged.
* **Preserved Wasm failures:** [Wasm001](evidence/wasm-full-001/archive.json)
  exited **1/418.94s**, with **zero native-area executions**. The shared WebView
  anonymous `EventListener` implementation failed production compilation;
  [the native diagnostic](evidence/native/first-native-wasm-diagnostic.json)
  preserves its source/binding evidence. After the seven-file portability repair,
  [Wasm002](evidence/wasm-full-002/archive.json) still exited **1/181.03s**:
  WebView **30/30** and camera **3/3 common** cases passed, but share executed
  **zero tests** because `WebSharePromiseTest.kt:139` returned Unit where the
  Wasm `setTimeout` handler requires `JsAny?`. The final-null correction below
  was applied only after that archive was sealed. The next
  [Wasm003](evidence/wasm-full-003/archive.json) exited **1/65.01s** with
  WebView **30/30**, but again **zero camera/share executions**. The separate
  [IO compiler supplement](evidence/wasm-full-003-io-compiler/failure-review.json)
  records a missing Compose runtime on IO's compiler classpath, before dependent
  tests could run. None of these zero-execution modules counts as a pass, and
  later repairs do not rewrite any failed command.
* **Full JS004/Wasm004 native verification:**
  [independent scoped receipt](evidence/native/browser-004-native-verification.json),
  [Wasm archive](evidence/wasm-full-004/archive.json) and
  [JS archive](evidence/js-full-004/archive.json).
  Both complete commands exited **0**, in **123.02s / 130.03s** respectively,
  with **290/290 full-library cases per target**. Native-area counts per target
  are WebView **24 common + 6 actual DOM**, camera **3 common**, and share
  **8 common + 9 actual-browser/controlled-navigator** cases. All 18 native raw
  and archived report hashes, their fresh timestamps/testcase statuses and one
  execution marker per target/module were checked. Each run's 693 input hashes
  were unchanged; all 75 held native hashes match both. The fresh generated
  Karma configurations and selected launcher/tooling context were also checked;
  they are not a complete dependency/process attestation. Earlier JS 29-case
  results predate the new listener factory and cannot substitute for these fresh
  30-case results. The two current runs verify the final-null timer fixture and
  native-listener regression without clearing actual native/window, GC/security,
  recipient, cross-engine or immutable-release gates.

### Post-review source repair checkpoint — not execution evidence

[The 20:19:05Z checkpoint](evidence/native/post-review-source-checkpoint.json)
records 72 native-area production/test/module input hashes and the exact new
test inventory. Whitespace checks and both module XML parses succeeded; these
are not Kotlin compilation, Android resource merging or test execution. The
source repairs cover camera Activity/ownership defects and WebView attachment,
saver, native requested URL and typed-evaluator boundaries described above.
[Camera/share independent review](evidence/review/native-share-camera-independent.md)
and [WebView independent review](evidence/review/webview-independent.md) preserve
their pre-repair findings and separately identify post-repair inspection. No
earlier log, failed XML or input receipt is replaced. The lead owns coordinated
builds. The later authorized module-build selector, attribution and test-fixture
deltas are recorded explicitly rather than treated as unchanged old inputs.
The later test-host INTERNET manifest is a separately recorded additive input;
its hash is in the second-device scoped receipt. All 72 prior native inputs plus
that manifest matched the third device run snapshot. The
[prior JVM rerun plan](evidence/native/next-native-jvm-rerun-plan.json) records
six desktop/Android-host tasks and per-class/method expectations at its own
checkpoint; its hashes must not substitute for the later attribution-bound run.

The previous [22:22:29Z source freeze](evidence/native/second-jvm-fixture-corrections.json)
preserves 73 scoped hashes after exactly two test-file corrections. Reversing
its recorded patches reproduces the failed run's original source hashes; the
other 71 inputs match that run. `CreationCallbackFailure` opts out of coroutine
copying through `CopyableThrowable.createCopy() = null`. The test still requires
the exact same sentinel, without unwrapping a production wrapper or disabling
diagnostics; all subsequent cleanup checks remain. Camera's `awaitComposition`
now invokes framework idling before its unchanged 5s condition and reads the
launcher on UI. No production, build, trust, scenario or timeout change was made.
The lead's subsequent focused tasks passed WebView desktop (36 slots) and camera
Android host (14 slots); other successful suites retain their second-batch
provenance. That source freeze held through the first full JS command.

The previous [23:16:52Z source freeze](evidence/native/first-js-fixture-corrections.json)
records exactly two later **web-test-only** corrections and all 73 scoped hashes.
The WindowProxy guard uses `===`; three share expected lists use the explicit
`ShareOutcome` element type rather than inferred singleton types. The before
hashes and reversible diffs reproduce the failed JS inputs. All other 71 native
inputs, 117 test declarations, script/DOM/sandbox assertions, expected outcomes,
callback-count checks and 5s waits remain unchanged. Production/build files are
untouched. The lead's subsequent focused JS command verified all 29 WebView and
17 share cases against these hashes; the overall command still failed outside
this area. No Gradle/browser rerun was performed by the native owner. Wasm was
still pending at that checkpoint; the later source freeze and executions follow.

The [seven-file listener repair](evidence/native/first-wasm-listener-repair.json)
replaces only WebView's listener construction/interop and adds a test-only native
DOM probe. The production handler bodies, public API, sandbox rules, source `===`
guard, timeouts and prior test assertions are retained. Both actuals create one
native listener object, stored by the owner for exact add/remove identity.
The new regression instruments only the tracked iframe's prototype load/error
operations in a synchronous `try/finally`. It wraps `handleEvent` **in place**,
counts before owner guards and demonstrates that removing a **different object**
does not stop delivery. Actual disposal must remove both registered objects with
matching capture flags; later events cannot deliver, including when the
application's disposal callback throws. It restores original descriptors and
forcibly detaches retained registrations on failure. This is real detached-DOM
listener evidence, not GC, collectability or complete page-navigation cleanup.

The final [single-line share timer repair](evidence/native/first-wasm-share-timer-correction.json)
adds only `; null` to the real `setTimeout(..., 0)` callback. Cancellation's
`clearTimeout`, the `isActive` guard, `resume(Unit)` and all nine Promise tests'
assertions remain byte-for-byte unchanged. Its complete **75-input** freeze
contains 74 unchanged native inputs and the six-byte timer change. It supersedes
neither the earlier failures nor their preimages/patches. Browser004 then executed
the complete native-area JS/Wasm suites against this freeze. Native sources and
shared build files were not edited during the documentation/readback work.

Prepared Kotlin tests at the current source freeze: **118 declarations** (WebView 60,
camera 14, share 44). This is an inventory, **not passed counts**:

| Library/source set | Methods | Actual coverage / limitation |
|---|---:|---|
| WebView commonTest | 24 | Channel ownership/non-replay/queue/attachment ordering; settings batching/equality; saver pending/final/HTML precedence; content/result/cookie rules; independent cleanup stages/primary failures. |
| WebView desktopTest: cookies | 5 | Actual JDK CookieManager, request matching/expiry and custom global handler preservation; not real WebEngine login. |
| WebView desktopTest: JavaFX | 7 | Real Scene/Engine, slow local HTTP stop, typed JS/disposal race, native link/redirect/reload/history/saver, UA reset/release, cancelled queued creation and failed creation callback. Requires display/Xvfb; headless tests **skip**. |
| WebView webTest | 6 | All six passed on JS004 and Wasm004: actual DOM iframe transitions/isolation/cleanup/failed creation, cookie behavior and native listener identity/removal with a negative control. Other engines, network matrices and GC remain open. |
| WebView androidHostTest | 17 | Robolectric SDK34 native-reference/client/error-list ownership, partial creation/multi-stage teardown, production Compose navigator replacement with shadow history, and eight controlled invocation/callback timing cases. Not real Chromium/device rendering. |
| WebView androidDeviceTest | 1 | Production Compose binding and actual provider history.pushState/back; navigator-only replacement should preserve native view and read existing flags. Second batch failed from missing test-host INTERNET; third verifies permission but times out before history at initial readiness. No history pass. |
| Camera commonTest | 3 | Pending-request save/restore/consume and image-option validation; all three passed on JS004 and Wasm004. Not a camera or unsupported-launcher execution. |
| Camera androidHostTest | 11 | Six driver cases with actual cache files/provider failures/busy/cancel/reentrant-throw and five real Activity/Compose/registry lifecycle cases. External camera/writers/results are simulated; not OS process death or real capture. |
| Share commonTest | 8 | Real common gate, legacy stage mapping, validation/snapshot and launcher callback exception boundaries. |
| Share desktopTest: owner/fallback | 8 | Actual desktop owner/cancellation/gate with injected operation and clipboard transport, file-list snapshot, invalid MIME and safe no-open fallback. Not OS clipboard permission/native delivery. |
| Share desktopTest: cache | 7 | Actual filesystem digest/immutability/concurrent writers/symlink/private permissions using generated bytes. POSIX checks skip on other filesystems; not loaded Windows DLL proof. |
| Share desktopTest: JNI | 4 | Real native ABI/counts and borrowed-pointer rejection on every host; unsupported-host lifecycle only on non-macOS; actual AppKit cancel only on macOS with GUI/opt-in. Applicability and unacceptable missing-GUI skips are detailed below. |
| Share androidHostTest | 8 | Actual FileProvider/intents/readable cache bytes/ClipData plus controlled launch errors under Robolectric API23/34; not separate recipient or real chooser lifecycle. |
| Share webTest | 9 | All nine passed on JS004 and Wasm004, executing production Promise handling with controlled navigator functions: delayed clipboard success, rejection, abort, subject/files, callback throw, busy/disposal, unsupported payload and sync failure. Real OS permission/activation and recipient lifetime remain open. |

JNI applicability for `com.mohamedrejeb.calf.share.platform.NativeShareBridgeTest`:
`nativeAbiAndDiagnosticsLoadOnTheActualHost` and
`borrowedNativeWindowPointersAreRejectedWithoutDereference` apply everywhere.
`unsupportedHostRequestsAndCancellationNeverRetainNativeOwners` applies only to
non-macOS; `macOsPickerCancellationReleasesRealMainThreadOwners` applies only to
macOS. The exact opposite-host case is **N/A**, not passed. The designated macOS
job must provide a graphical session and `NATIVECMPKIT_NATIVE_UI_TESTS=true`
(or worker property `nativecmpkit.test.nativeUi=true`); a skip from missing GUI
or opt-in is **not** an acceptable native check. The three applicable Linux JNI
cases passed in the second JVM batch; the exact macOS-only case was N/A. This
does not execute AppKit or prove the macOS ownership/cancellation path.

The controlled browser harness observes downstream application Promise errors
without reclassifying them in production or allowing an intentional test error
to escape the runner. Real browser turns, not virtual test-clock timeouts, drive
these cases. The tests contain no production fake/stub fallback. The inventory
is not an execution count: only the dated command receipts above establish which
tests actually ran. Other-browser/Apple/device scenarios and the uncovered Wasm
network/native-integration cases still need their specified target results;
the selected local fixture passes do not replace those checks.
Every original finding's required tests remain listed in its resolution row;
the six passing registry tests do not automatically mark NATIVE-029/030 verified.
Next steps are coordinated target compilation, fix actual compiler/test failures,
add the missing library/native suites, and only then immutable CI/consumer runs.
Release gates include real devices/hosts, native memory profiling, full published
dependency/ABI/native-slot verification and recipient lifetime tests. Publication
must remain blocked until the lead verifies applicable gates, not merely because
the files in this document now exist. The owner's containment instruction also
now permits verification Actions (2026-10-26 owner update), without subagents;
publishing, deployments and Pages remain gated regardless of a local result.
