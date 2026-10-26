# Independent WebView cross-review

Reviewer: `audit_permissions_geo` (not the WebView implementation owner).

## Scope, revision and limits

This is an **independent read-only review of the pre-repair working-tree
snapshot**, not a release clearance. The snapshot was captured at
**2026-10-24T19:54:18.692291+00:00**, on base commit
`94d2492e99d5cbc060409d94d9f88febd06222d5`, with uncommitted implementation
changes. The commit alone does **not** identify the reviewed implementation.

* [Input manifest](webview-independent-inputs.json): all 27 files under
  `calf-webview/src`, the module build script and `DesktopJavaFx.kt` — **29
  files / 3,471 lines**, including every production, test and interop file.
* [Independent verification receipt](webview-independent-verification.json):
  all 29 hashes still matched at **20:02:30Z**; exact inspected command, input
  comparisons, receipt/XML hashes and individual executed case results.
* The reviewer did not edit production/test/build sources, launch a build/test,
  change GitHub state or publish anything. Only review documentation/evidence
  was written. Later owner-authorized repairs are not retrospectively covered
  by this snapshot; they need an additive review/result.
* Baseline findings remain immutable in
  [NATIVE.json](../../../audit/findings/NATIVE.json). `WV-XR-*` identifiers below
  identify review observations, **not new baseline findings or duplicate GitHub
  issues**. Reconcile them with the existing NATIVE issues/resolution ledger.

The lead and native owner received the concrete mobile navigator-rebinding
defect and Desktop evaluation/disposal result mismatch. The owner subsequently
reported authorization to repair mobile history rebinding. This report preserves
the **pre-repair** evidence; an authorization/message is not proof of a fix.

## Source map and execution-flow coverage

Paths in this table are exact. Later references use its short source labels;
line numbers refer only to the hashed snapshot above.

| Label | File | Reviewed symbols / execution flow |
|---|---|---|
| Common | `calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt` | Public expect API, `WebContent`, loading/state/error contracts, navigator queue/attachment mutex, all commands, remembered URL/HTML inputs and saveable state |
| Contracts | `calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebViewContracts.kt` | JS quoting/string envelope/decoder, request reset, content option validation, event conversion, URL-only saver, exception-preserving cleanup |
| Settings | `calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt` | Every setting/default/setter, nested batching, Android/native creation-only options, independent iframe trust policy |
| Android | `calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt` | Public/internal composables, factory/restore/configure/onCreated order, release stages, Main dispatch, shared loader, both clients, mutable errors, evaluator, navigation consumer and Bundle saver |
| Desktop | `calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt` | Runtime preflight, deferred AWT toolkit startup, FX dispatch, owner creation/listeners/scene/release, settings coalescing, history, loaders/commands, both evaluators and saver |
| iOS | `calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt` | UIKit factory/update/release, preconstruction configuration, Main dispatch, URL/HTML loader, navigation delegate, KVO registration/unregistration, both evaluators and saver |
| Browser | `calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt` | Compose/DOM owner, load/error listeners, creation failure/disposal, state/navigator loader, history/stop/reload limitations, sandbox application and both evaluators |
| Cookie API/rules | `calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/{Cookie.kt,CookieManager.kt,CookieRules.kt}` | Public metadata contract, token/value/domain/path/expiry/prefix checks, host applicability, request matching, cookie-header parsing and serialization |
| Android cookies | `calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/CookieManager.android.kt` | Main-confined native writes/acknowledgment/flush, request-cookie reads, full-store deletion and HTTP-date serialization |
| Desktop cookies | `calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt` | Existing/default/explicit handler selection, JDK versus generic handler branches, identity-bound expiry metadata, synchronization/filtering/deletion |
| iOS cookies | `calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt` | Foundation response-header parsing, Main-confined WK cookie store operations, host/path/secure/expiry filtering and snapshot deletion |
| Browser cookies | `calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.web.kt` | Exact host-document origin/path capability, HttpOnly rejection, date writer, owned-identity deletion versus unsupported complete logout |

Also read completely: JS/Wasm `PlatformUtils.*.kt` and `WebElementView.*.kt`,
their two web expect declarations, `iosMain/cinterop/nskeyvalueobserving.def`,
all six test files, `calf-webview/build.gradle.kts` and
`convention-plugins/src/main/kotlin/DesktopJavaFx.kt`. The input manifest names
each expanded path and hash. This review also consulted the original affected
NATIVE findings and current [implementation ledger](../../NATIVE.md) /
[resolution records](../../resolutions/NATIVE.json), without treating their
claims as executable evidence.

### Lifecycle paths inspected

* **Android:** state-keyed composition → `AndroidView.factory` → create/configure
  → publish matching native identity → restore Bundle → current `onCreated`;
  then state `snapshotFlow` and navigator consumers target that native view.
  Release attempts save, callback, stop, client detach, parent removal, child
  removal, destroy and matching-state clear independently. Failed factory
  customization unwinds without fabricating a successful `onDispose` lifecycle.
* **Desktop:** composition → coroutine → later AWT event constructs `JFXPanel`
  → disposable owner queues FX creation → settings/listeners/scene/state are
  installed before customization. Atomic disposal prevents pending creation or
  settings work from resurrecting the owner. FX release attempts callback,
  listener removal, cancel, unload, scene clear and state/history clear. Toolkit
  lifetime remains process-global; individual owners do not call `Platform.exit`.
* **iOS:** state-keyed `UIKitView` constructs `WKWebViewConfiguration` before
  the view; publishes identity/delegate and strongly retains the KVO observer
  before registration/onCreated. Release removes recorded registrations,
  disconnects delegate, stops loading and clears matching state. Settings,
  evaluator and cookie-store calls dispatch their native work to Main. This is
  source inspection, **not** proof Kotlin catches Objective-C `NSException`, KVO
  ABI correctness, WebKit runtime ordering or collectability.
* **Browser:** owner creates/records iframe and its listeners, applies sandbox
  before customization, then shared state/command loaders change attributes.
  Dispose is idempotent, removes listeners, reapplies an empty sandbox, removes
  `srcdoc`, requests `about:blank` and clears state even if the application
  callback throws. Actual DOM removal belongs to Compose `WebElementView`; the
  prepared direct-owner tests explicitly remove their own appended element.

## Concrete residual source findings

### WV-XR-001 — Mobile navigator replacement loses existing history capabilities

**Medium · confirmed-source · existing NATIVE-037 · new independent observation.**

* **Locations:** Android `WebView` lines 128–140 / `BackHandler` 129;
  `AccompanistWebViewClient.doUpdateVisitedHistory` 293–298;
  `handleNavigationEvents` 443–456. iOS `WebView` 67–75 and 107–110;
  `handleNavigationEvents` 323–337; `WKWebViewObserver.startObserving` 373–382
  and property callbacks 427–432. Common navigator flags initialize false at
  215–222. Desktop supplies the contrasting correct initialization at 60–62
  and 216–220.
* **Root cause:** the existing native view survives a navigator-only
  recomposition. References/consumers bind to the new navigator, but Android/iOS
  never copy the native view's **already-existing** back/forward state into it.
  Only a future history/delegate/KVO change updates the flags; iOS registers
  KVO with `New`, not `Initial`, and does not re-register on navigator replacement.
* **Impact / source-level reproduction:** load A then B so native history permits
  Back; replace only navigator A with a fresh navigator B at the same composition
  location. Without another navigation, B's flags remain false. Android then
  disables its `BackHandler` and lets system back leave the screen rather than
  navigate the loaded WebView. iOS toolbar/button consumers likewise see false
  capabilities; its separate native swipe setting is not itself disabled.
* **Recommendation:** when the new consumer attaches/rebinds, snapshot native
  `canGoBack` and `canGoForward` on the platform UI thread, only if it still owns
  the same native view. Do not infer history from a URL. Preserve old-consumer
  cancellation and the single-owner navigator rule.
* **Risks / tests:** add a **real stable-composition** navigator replacement
  regression with two native history entries, checking native identity unchanged,
  new flags, old flags cleared, Back interception and subsequent callbacks routed
  only to the new navigator. A Robolectric history shadow can verify wiring but
  cannot certify Chromium history. Repeat on WKWebView with a real back list.
  No such test executed in the inspected receipt.

### WV-XR-002 — Non-Android saver prefers a stale request over the observed final page

**Medium · confirmed-source · existing NATIVE-007 / NATIVE-005 · owner-known gap.**

* **Locations:** Contracts `urlReloadWebStateSaver` 100–108, especially 103;
  Common saveable contract 318–326; Desktop completion 129–133; iOS URL/finish
  updates 261–285 and 423–425; Browser load listener 55–66.
* **Root cause:** saving selects `requestedUrl ?: content.url ?: lastLoadedUrl`.
  It does not prefer the final URL even when that URL is observable. Native
  redirect and browser internal-link updates can change `lastLoadedUrl` without
  changing the earlier requested/content URL.
* **Impact / source-level reproduction:** with `requestedUrl=A` and
  `lastLoadedUrl=B` after an observed redirect/internal navigation, the saver
  restores A. That does not implement the advertised latest-URL reload; it can
  re-enter an old redirect/login/one-time-link flow. Android's separate Bundle
  saver is not affected by this expression. No claim is made that restoring a
  GET repeats the original POST body.
* **Recommendation:** define pending-request versus completed-page precedence;
  save the correct observed completed URL when available, otherwise a deliberate
  requested-URL fallback. Keep HTTP(S)-only and no-header/HTML/form-history
  guarantees. Unknown cross-origin browser final URLs cannot be fabricated.
* **Risks / tests:** saver tests need distinct request/final URLs, same- and
  cross-origin redirects, internal navigation, pending loads, failed loads,
  inline HTML and null URLs. Then restore through the actual target composition
  and inspect the real requested page. The passing common saver test uses only
  one URL and cannot distinguish this defect.

### WV-XR-003 — Desktop internal navigations retain the previous requested URL

**Medium · confirmed-source · existing NATIVE-005 · owner-known gap.**

* **Locations:** Desktop worker listener 124–140, particularly `SCHEDULED` 127;
  `loadNow` 228–239; Contracts `beginRequest` 52–58.
* **Root cause:** a worker schedule invokes
  `beginRequest(state.requestedUrl ?: engine.location)`. Once an explicit URL
  has populated `requestedUrl`, its non-null old value always wins. A subsequent
  page-initiated internal link/reload does not pass through `loadNow` to set a new
  requested URL.
* **Impact:** request metadata remains attached to the earlier URL even when
  the engine is navigating elsewhere; it also feeds WV-XR-002. State reset itself
  still clears prior title/errors, and successful completion records the current
  engine location — those positive paths do not repair `requestedUrl`.
* **Recommendation:** distinguish explicit requested loads from native internal
  navigation, using trustworthy native location/navigation notifications at the
  appropriate stage. Merely swapping operands without checking JavaFX location
  timing may substitute the previous page's location instead.
* **Risks / tests:** actual engine/local HTTP A→internal B→redirect C, reload,
  Back/Forward and failure before commit. Assert both requested and final metadata
  at each stage, plus saver behavior. No actual JavaFX scenario executed in the
  inspected batch.

### WV-XR-004 — Android evaluation does not complete synchronous native failures

**Medium · confirmed-source omission, native triggering conditions unverified ·
existing NATIVE-015 · owner-known gap.**

* **Locations:** Android legacy `evaluateJavascript` 398–404; typed extension
  459–473. Contracts evaluator promise 14–20.
* **Root cause:** attachment checks and Main dispatch precede the native call,
  but there is no catch around `view.evaluateJavascript(...)` itself. The typed
  callback's catch only decodes a value **after** the native invocation returns
  a result. A synchronous native invocation exception escapes; neither API
  completes its callback on that path.
* **Impact:** conditional on the native operation throwing, typed callers get
  zero results instead of an explicit evaluation failure; off-main dispatch can
  turn it into an uncaught main-loop exception. This review did not reproduce a
  platform-native throw and does not claim every ordinary call fails.
* **Recommendation:** capture native synchronous failure while preserving
  **at-most-once application callback delivery**. Do not wrap a possibly
  synchronous application callback in a broad catch which then invokes it again.
  A result gate or separation of native invocation from application delivery
  must handle both synchronous and asynchronous callback behavior.
* **Risks / tests:** failure-injecting native subclass, synchronous callback
  followed by a native throw, asynchronous completion, throwing application
  callback, disabled JS, before attach/after dispose and off-main invocation;
  supplement with real Chromium behavior. Current Android tests cover none of
  these evaluator paths.

### WV-XR-005 — Desktop disposal/evaluation race reports Error, not Unavailable

**Low · confirmed-source · existing NATIVE-015 · new independent observation.**

* **Locations:** Desktop `dispose` 168–170, queued clear 191–196, `evaluate`
  255–261, typed extension 291–300; Contracts unavailable promise 18.
* **Root cause:** `dispose()` sets the atomic flag immediately but clears
  `state.owner` only in queued FX release. An evaluation between those steps
  captures the non-null owner. Its queued evaluator sees a disposed/null view and
  returns `Result.failure(IllegalStateException("WebView is detached"))`; the
  extension maps **every** failure to `JavascriptResult.Error`.
* **Impact:** a documented unavailable/disposed result instead looks like a
  script failure, inconsistently with evaluation after `state.owner` is cleared.
  This is not an observed crash or a second callback.
* **Recommendation:** represent detached-owner unavailability distinctly when
  mapping the platform result, without parsing error-message text or hiding
  actual script exceptions.
* **Required test:** in one FX turn call `owner.dispose()` then the typed state
  evaluator; drain queued work and assert exactly one `Unavailable`. Also check
  attached script error remains `Error`, and callback exceptions do not cause
  redelivery. Source reasoning is deterministic; the test was not executed here.

## Conditional risks needing targeted tests, not inflated defect claims

| Observation | Exact source and root cause | Impact / recommended verification |
|---|---|---|
| **WV-XR-R01 · Medium · risk · NATIVE-005:** superseded requests share one native identity | Android callbacks 279–314 and iOS navigation callbacks 259–312 check only view identity. iOS receives `WKNavigation` identifiers but does not compare them with an active request. | A delayed failure/cancellation/completion from A may update request B on the same view. Establish actual platform callback ordering with slow A immediately replaced by B, stop→load and redirect/cancellation tests. Correlate native navigation identity where available; do not claim the existing **old-view** identity tests cover **old-request** events. |
| **WV-XR-R02 · Medium · risk · NATIVE-015/002/033:** mobile in-flight evaluation has no owned completion registry | Android 398–404 / 459–473 and iOS 237–244 / 339–350 check identity before invocation, then retain plain native callbacks. Release does not settle pending evaluator requests; callbacks do not re-check attachment. | Native teardown may drop a result or deliver a stale result, depending on the actual engine contract. This review did not demonstrate either outcome. Specify pending-call disposal semantics, test evaluation→dispose/remount and process/renderer failure, and provide exactly-once `Unavailable`/cancellation if required by the documented contract. |
| **WV-XR-R03 · Medium · risk / backend contract decision:** explicit JDK writes bypass its normal handler acceptance path | Desktop cookies 30–47 call `java.net.CookieManager.cookieStore.add` directly; generic handler writes instead use `put` at 48–52. Common host validation only checks exact/suffix applicability (CookieRules 30–37), not a public-suffix database. | Do not infer that direct insertion honors a host's configured `CookiePolicy` or browser public-suffix rules. Test a rejecting JDK policy, policy callbacks, disallowed domains and actual outgoing requests; either document privileged direct-store insertion or route through the chosen policy with accurate retained metadata. This is not evidence that JavaFX's distinct native store is replaced or exploitable. |

Additional explicit limits, not new vulnerabilities:

* Browser sandbox changes are next-navigation policy, **not revocation of
  already-running trusted script**. The docs correctly say so. Isolated popups
  remain sandboxed; `postMessage` origin/source validation is the application's
  responsibility. No library origin-validation bridge was found or certified.
* Browser `load` events do not prove HTTP status, CSP/X-Frame-Options acceptance,
  login success or actual content. History operations can be unavailable. The
  cross-origin reload fallback (`Browser` 163–165) reloads `lastContent`, not an
  unknowable internally navigated final URL; this boundary needs a documented
  real-browser scenario, not a claim of full native-browser parity.
* Native API/DOM setter exceptions, including strict Trusted Types/CSP policies,
  require platform-specific testing. General Kotlin cleanup catches are not
  proof of Objective-C exception recovery. No actual KVO registration-failure
  or WebKit-process-termination result was available.
* `Cookie` boolean flags cannot describe unknown metadata separately from false;
  request-header backends expose names/values rather than a full cookie-store
  inventory. Do not treat a returned Android/browser/generic-handler cookie as
  a faithful security-attribute round trip. Browser limited deletion is correctly
  separate from complete server/HttpOnly logout.
* Android still exposes permissive file/content access and media defaults
  (`Settings` 70–82, 133–145); JS defaults off and API-appropriate Safe Browsing
  is enabled. Host untrusted URL/content policy remains necessary. This review
  did not establish an exploit from those compatibility defaults.

## Highest-priority baseline findings: source improvements versus proof

| Baseline | Positive source check | What the available evidence does **not** prove |
|---|---|---|
| **NATIVE-001 High** — stop feedback loop | Desktop 242–251 explicitly invokes `engine.loadWorker.cancel()`; it cannot resolve back to `navigator.stopLoading()`. | The actual-engine slow-request test did not execute. Repeated stop, detach/reattach and real Compose window behavior remain open. |
| **NATIVE-002 High** — native lifetime | Android 185–213 / Desktop 168–200 attempt independent cleanup stages and clear only matching state. Partial creation unwinds. Common cleanup retains the first exception and suppresses later distinct failures. | Common stage-list tests are not native destruction, media shutdown, Activity collection, native listener collection or multiwindow evidence. Android/FX prepared owner tests had no executed scenario in the inspected batch. |
| **NATIVE-010 High** — inline HTML sandbox escape | Browser 179–193: default isolated mode never pairs scripts with `allow-same-origin`. Only a distinct explicit `Trusted` setting removes sandbox when scripts are enabled. | The passing common test checks the setting remains Isolated; it does **not** execute child script. The real browser parent-DOM test was not run in this receipt; popup/form/nested-frame/storage/CSP matrices remain open. |
| **NATIVE-013 High** — cookie-global mutation | No production WebView code calls `CookieHandler.setDefault`. Desktop cookies 24–25 adapt the existing handler; no handler means explicit unsupported, not a newly installed empty store. The custom-handler identity regression passed. | No real WebEngine authenticated-session preservation, JavaFX `javascript`/`javascripts` HttpOnly behavior, or concurrent multi-manager integration passed here. The JDK/custom handler tests must not be relabeled JavaFX login tests. |

Other positive checks: every native factory publishes its reference before
`onCreated`; callbacks use updated Compose state; Android/browser URL and HTML
paths share their respective loaders; the browser removes `srcdoc` before URL
loads; mobile native public evaluation/settings/cookie work dispatches to Main;
unsupported content options fail explicitly instead of inventing credential
forwarding; iOS creation-only inline-media options are set before construction;
Desktop custom user-agent null maps to its captured default; cookie date/token/
path/secure/prefix validation and explicit unsupported logout paths exist.
These are source observations, not blanket runtime certifications.

## Independently inspected execution evidence

The reviewer personally read the command receipt, relevant raw Gradle task/error
lines and all seven archived WebView XML reports from:

* [Command](../gradle/first-native-and-third-android-host.log.result.json)
* [Raw log](../gradle/first-native-and-third-android-host.log)
* [Pre-run selected input hashes](../gradle/first-native-and-third-android-host.inputs.json)
* [Lead post-run summary](../gradle/first-native-and-third-android-host.summary.json)

The exact Xvfb Gradle command started **2026-10-24T19:47:22.049634+00:00** and
exited **1** after **50.01 seconds**. The verification JSON preserves its entire
argument array; this reviewer did **not** execute it. The lead's dated post-run
receipt records 207 selected inputs unchanged at 19:48:52Z. The independent
review compared all **16 WebView** entries from that input manifest: 14 still
match; exactly two later harness repairs differ, matching the native owner's
recorded post-repair hashes. This is not a new verification of all 207 current
repository inputs.

| Inspected scope | Actual result |
|---|---|
| WebView Desktop production | `:calf-webview:compileKotlinDesktop` executed successfully in the failed batch |
| WebView Android production | `:calf-webview:compileAndroidMain` executed successfully in the failed batch |
| Common tests executed on Desktop | **20 passed**, five common XML suites: navigator 5, settings 4, content 4, cookie rules 4, cleanup 3 |
| JDK/custom cookie tests | **5 passed**, one XML suite; actual `java.net.CookieManager` and explicit custom/default handler scenarios |
| JavaFX test class | **1 initialization failure**, one XML suite: `javascriptUsesActualEngineAndTypedJsonResults() should be void`. **Zero of the five actual FX scenarios executed.** |
| WebView Android-host | `compileAndroidHostTest FAILED` on two obsolete generic `RuntimeEnvironment.getApplication` calls; **zero tests executed** |
| WebView browser / Apple | No execution or WebView Apple/custom-cinterop compilation evidence in this inspected batch; camera/share/permission KLIB receipts cannot establish WebView compilation |

Total inspected WebView XML: **7 reports, 26 case entries = 25 passed scenarios
and 1 JUnit initialization failure**, zero XML errors/skips. The initialization
placeholder is not a sixth JavaFX scenario. The current snapshot changes the
typed-JS test to `runBlocking<Unit>` and removes Android `getApplication` type
arguments; those repairs had **not** rerun in the inspected evidence.

### Prepared-test coverage, not executed-coverage claims

The reviewed sources declare **43 distinct tests**: 20 common, eight Android
host, five real-FX owner tests, five Desktop-cookie tests and five web tests.
Common tests are reused per target; do not count those declarations as executed
platform cases. Exact paths/counts are in the verification receipt.

* `WebViewContractsTest.kt`: queue capacity/ownership/no replay/header snapshot,
  history clearing on detachment, settings equality/batching/trust default,
  request reset, unsupported options, simple URL saver, JS envelope decoding,
  cookie validation/matching. These do not mount a native view.
* `WebViewCleanupTest.kt`: exception ordering, all stages attempted and no
  self-suppression. These deliberately use lambdas, not native resource handles.
* `AndroidWebViewLifecycleTest.kt`: eight direct helper/client tests use a real
  Robolectric WebView subclass with injected stop/destroy/restore failures.
  They cover partial creation, matching-identity cleanup and stale **view**
  callbacks, not Compose replacement, Chromium loads, JS or cookie behavior.
* `JavaFxWebViewTest.kt`: direct owner/actual WebEngine/Scene tests prepare
  user-agent reset/disposal, typed evaluation, one slow HTTP stop, disposal before
  queued create, and throwing creation callback. The fixture initializes
  `JFXPanel` using AWT `invokeAndWait`, not the production cold Compose startup
  path. It is not NATIVE-018/macOS cold-start proof or an authenticated-cookie test.
* `DesktopCookieManagerTest.kt`: JDK path/secure/host-only filtering, retained
  absolute expiry, unknown foreign expiry, custom-handler preservation and no
  default-handler installation. No HTTP server observes actual outgoing cookies.
* `BrowserWebViewTest.kt`: direct DOM owner attribute transitions, late manually
  dispatched error after disposal, real isolated-child parent-access attempt,
  callback/creation failure cleanup, and document-cookie expiry/unsupported
  boundaries. The transition test asserts attributes without awaiting rendered
  URL content. None mounts the public WebView through Compose.

Thus **no prepared test in this snapshot exercises public WebView state/
navigator/callback replacement at a stable composition location on any target**.
There are also no dedicated iOS WebView test sources. A generic cleanup test or
an unrelated permission/camera KLIB does not fill either gap.

## Recommended bounded next steps

1. Preserve this pre-repair snapshot; add the smallest mobile history-rebind
   correction and real composition regression under the native owner's scope.
2. Address/request-track the saver, Desktop internal navigation and evaluator
   findings under their existing NATIVE issues. Preserve compatibility adapters;
   do not start a replacement browser architecture to hide platform limitations.
3. Rerun the corrected Android/FX harnesses with the lead's frozen-input receipt;
   distinguish failed batch status from individual passing suites. Then execute
   the browser isolation test in both JS and Wasm runtimes.
4. Compile the actual iOS WebView **including its custom KVO cinterop** on an
   Apple-capable toolchain, then test WKWebView lifecycle, history and evaluator
   behavior; mobile Main Thread Checker/device work remains a separate gate.
5. Before closing the High findings, obtain actual native stop/disposal/session
   tests and browser security-boundary evidence. No finding is recommended for
   verified closure on the evidence in this report alone.

## Addendum — authorized source repairs refrozen at 20:19:05Z

This additive review concerns the native owner's
[2026-10-24T20:19:05Z checkpoint](../native/post-review-source-checkpoint.json).
The entire preceding report remains an unchanged **pre-repair** record. Its
29,042-byte prefix and SHA-256 are preserved in the
[post-repair input manifest](webview-postrepair-inputs.json); the original input
manifest, command receipt, failed-test evidence and review verification JSON
were not overwritten.

### Re-review scope and evidence level

* At the **20:24:02Z input capture**, independently matched all **72 checkpoint
  input hashes**, without claiming semantic review of the camera/share changes.
  The final hold comparison has one authorized, separately bound build-only
  delta described below; it is not an unchanged whole-checkpoint claim.
  WebView-focused re-review covers
  all **31 WebView source/test/module inputs**, plus the unchanged JavaFX build
  helper: **32 files / 3,967 lines**. Compared with the initial review, eight
  files changed, three test files were added and 21 files remained identical.
* Read all changed WebView implementations and test bodies. Confirmed existing
  Android convention lines 34–53 register device tests when the corresponding
  source directory exists. The module declares device-only test dependencies,
  but the original matching predicate did not apply them. Its later correction
  is assessed below; no publication or runtime permission escalation is added.
* Performed **read-only dependency bytecode inspection**, not a build or test:
  [JavaFX receipt](webview-javafx-loadworker-21.0.13.json) and
  [inspected output](webview-javafx-loadworker-21.0.13.txt).
* No production, test or build source was edited by this reviewer. No Gradle,
  Chromium, JavaFX toolkit, browser, Apple or instrumented test was launched.
  The owner checkpoint explicitly awaits compilation/execution. The original
  25 passing scenarios and one initialization failure are still **dated
  pre-repair results**, not results of these repairs.

Final hash/prefix/link checks for this addendum are recorded in
[webview-postrepair-verification.json](webview-postrepair-verification.json).

### Later authorized build-only delta

After the input capture, the lead authorized the build owner to correct
`calf-webview/build.gradle.kts:11` from
`sourceSets.matching { name == "androidDeviceTest" }` to
`sourceSets.matching { it.name == "androidDeviceTest" }`. The
[build-owner repair receipt](../build/android-device-dependency-matching-repair.json)
records the cause: the old `Spec<KotlinSourceSet>` predicate captured
`Project.getName()` rather than reading the source-set argument. The three
archived `javap` outputs independently inspected for this review contain that
call; their text hashes are recorded separately from the owner's original
classfile hashes.

The first device command was also inspected as negative build evidence:
[command/result](../gradle/first-android-device.log.result.json),
[summary](../gradle/first-android-device.summary.json) and
[log](../gradle/first-android-device.log). It started at **20:22:20.300136Z**, ran
84.02 seconds and exited **1**. WebView's device-test compilation failed on
missing AndroidX test symbols before instrumentation; this command executed
**zero device tests**. It does not establish a failure of the repaired native
history logic, which never ran.

The final comparison still matches **71 of 72 owner inputs** and **31 of 32
WebView review inputs**. All listed production and test bodies remain unchanged;
only this module build script differs. Reversing exactly the one `it.` insertion
reproduces the checkpoint SHA-256
`64502aed44793dbb76caf79725cc4db7fcebd078f29d6cc6035ec464ce41b4a0`.
The current SHA-256 is
`c8992924bfdec2285ec1719926e85a7a5eeaafbd522b348eee19d93642c6063b`,
matching the build-owner correction receipt. The original owner checkpoint and
post-repair input manifest are preserved, not silently updated to the new build
bytes. No later device command, successful APK build or runtime result is
assessed in this addendum; any such evidence requires its own bound receipt.

### Assessment of the five concrete review findings

| Observation | Current source repair and independent assessment | Remaining evidence requirement |
|---|---|---|
| **WV-XR-001 / NATIVE-037** | **Source-addressed.** Common `consumeNavigationEvents` now accepts `onAttached` and invokes it at `WebView.kt:201–215` **after** successfully acquiring the single-owner mutex. Android `WebView.android.kt:444–463` and iOS `WebView.ios.kt:323–342` snapshot both native history capabilities inside that hook, on Main and only for matching view identity. The hook precedes the first command; a rejected competing mobile consumer cannot run its snapshot. An exception from the hook still clears flags/unlocks through `finally`. | Execute the new stable-composition Android host and separate real-WebView device fixtures. Apple compilation/native history checks, actual Back interception, old-navigator callback isolation, state replacement and callback-lambda replacement remain separate acceptance cases. |
| **WV-XR-002 / NATIVE-007** | **Source-addressed.** `WebViewContracts.kt:102–125` introduces `urlForGetRestoration`: Initializing may use declarative content, Loading uses the accepted requested URL, Finished prefers a nonblank observed final URL then the requested URL. HTTP(S) filtering happens **after** selecting the candidate, so a known non-HTTP final page does not revive an older HTTP request. HTML navigation with null requested/final URLs cannot fall back to stale declarative content after initialization. | Execute the three new common precedence regressions and actual target restoration. This remains URL-as-new-GET persistence, not native session/history/form/scroll preservation or permission to store sensitive URLs. Old-request/native event ordering remains WV-XR-R01. |
| **WV-XR-003 / NATIVE-005** | **Source-addressed, with independent dependency-order corroboration.** Desktop `WebView.desktop.kt:127–139` now resets from current nonblank `engine.location` at SCHEDULED instead of the old `requestedUrl`. In the cached **JavaFX 21.0.13 Linux** `WebEngine$LoadWorker.dispatchLoadEvent`, `PAGE_STARTED=0` invokes `updateLocation(url)` at bytecode offset **172**, before SCHEDULED is published at **181/184**, then RUNNING at **188/191**. The prior concern about merely swapping operands without checking native location timing is therefore addressed for this inspected artifact. | Execute the new actual-engine link→redirect→reload→Back/Forward test. Bytecode inspection is not an actual navigation, Compose cold-start, cross-version or cross-host runtime pass. Failed-before-commit, same-document navigation and Apple/browser ordering still require their platform cases. |
| **WV-XR-004 / NATIVE-015** | **Source-addressed for normal `Exception` failures.** Android `WebView.android.kt:399–405,465–513` routes legacy and typed APIs through one `AtomicBoolean` settlement gate. Native synchronous failure before settlement becomes one result; later duplicate callbacks cannot redeliver. A synchronous callback which throws application code has already settled, so the invocation catch **rethrows**, rather than reporting a second failure. A native throw after successful settlement likewise remains observable. Completion is routed to Android Main and rechecks current view identity; a supplied late callback after release yields typed Unavailable / legacy null. | Execute eight controlled evaluator tests, then real Chromium/off-main/disabled/pre-attach/remount cases. The controlled subclass supplies callbacks and throws itself; it does not run page JavaScript or prove the native engine always completes callbacks. Fatal `Error` recovery is not established by the `Exception` catch. |
| **WV-XR-005 / NATIVE-015** | **Source-addressed.** Desktop `WebView.desktop.kt:93–94,261–268,297–313` uses a private detached-owner exception type and maps **only that type** to Unavailable; actual script/native evaluator errors still become Error. Application callback delivery remains outside the native execution `runCatching`. The exact queued-disposal/live-state-owner interval is exercised by a new prepared test. | Execute that FX race test and preserve real script-error/callback behavior assertions. No FX test has a new execution result in this re-review. |

No additional blocking implementation defect was established in these scoped
repairs. This is an independent **source review**, not approval to close NATIVE
issues or lift release containment.

### Newly prepared tests: what each proves if executed

The snapshot now has **59 distinct `@Test` declarations**, not 59 test passes:
24 common, 17 Android-host, one Android-device, seven JavaFX, five Desktop-cookie
and five web tests. The increase is exactly **16 declarations**. Full path/count
inventory is in the post-repair manifest.

* `commonTest/.../WebViewContractsTest.kt:33–48`: one new admission-hook test
  checks snapshot-before-command ordering and that a rejected second consumer
  cannot call its hook. It exercises the common helper, not platform UI history.
* The same file at `159–193`: three new saver cases cover completed redirects,
  initial/pending/failed precedence and HTML/non-HTTP final URLs. These inspect
  state/saver values, not real redirects or navigation restoration.
* `androidHostTest/.../AndroidJavascriptEvaluationTest.kt:13–112`: eight cases
  cover invocation failure, synchronous completion then native throw, queued
  completion after failure, synchronous/asynchronous application exceptions,
  asynchronous throw after completion, late callback after release and legacy
  null-on-failure. The fixture asserts it is on Android Main, and the controlled
  WebView subclass is clearly labeled **not Chromium evaluation**. It does not
  test a call initiated from a background dispatcher.
* `androidHostTest/.../AndroidWebViewCompositionTest.kt:20–63`: the public
  composable is actually mounted at a stable location; the test supplies three
  history entries explicitly through Robolectric, moves to the middle, replaces
  only the navigator and checks both capabilities, native identity and one
  creation/zero disposal. This meaningfully adds previously missing composition
  wiring coverage **if it executes**, while disclosing synthetic history.
* `androidDeviceTest/.../AndroidWebViewHistoryDeviceTest.kt:18–70`: a separate
  instrumented fixture loads local HTML with a base/history URL, runs real
  `history.pushState`, navigates back and waits for a native middle-of-history
  position before replacing the navigator. It checks real native capabilities
  and retained view identity. It needs an actual device/emulator/WebView provider;
  compiling or merely discovering this source is not a pass.
* `desktopTest/.../JavaFxWebViewTest.kt:117–204`: a real local HTTP fixture serves
  A, redirects B to C and gates exactly the first two **`/c`** responses. The
  exact-path branch deliberately excludes incidental favicon requests from the
  gate. The test checks pending B request/reset/saver state, completed final C,
  reload C, Back A and Forward C. Network/cache/native ordering can only be
  established by executing it; the existing direct-owner fixture still does not
  mount a Compose `SwingPanel`.
* The same FX file at `218–230` queues disposal followed immediately by typed
  evaluation while `state.owner` is deliberately still non-null, then expects
  Unavailable. Both new FX methods explicitly return `Unit`, preserving the fix
  for the earlier JUnit non-void class-initialization failure.

The Android composition/device tests do **not** yet assert hardware Back-handler
dispatch, clearing of the previous navigator, replacement of callback lambdas
or replacement of the state object. In the device fixture, also confirm that no
late native history event after replacement can make a pre-fix implementation
pass accidentally. The shadow-based composition test is the more controlled
wiring regression, not a substitute for real history behavior.

### Risks and limits after the repairs

* **WV-XR-R01 remains:** matching native view identity is still not an active
  request-generation check. No old-request failure/cancellation interleaving
  was executed by this re-review.
* **WV-XR-R02 is only partially mitigated:** Android now classifies a callback
  which **arrives** after release and prevents duplicate settlement. It does
  not settle a callback which the platform never delivers. iOS pending-result
  handling did not change. Common evaluator KDoc at `WebViewContracts.kt:14–22`
  now explicitly discloses native callback loss during destruction. That is
  honest limitation disclosure, **not a demonstrated fix for dropped results**.
* **WV-XR-R03 and the cookie-native/session tests are unchanged.** No cookie
  source changed between these two snapshots. No new claim is made about JDK
  CookiePolicy/public-suffix enforcement or JavaFX authenticated sessions.
* The admission-hook regression should not be generalized to all platform
  duplicate-owner side effects: Desktop still calls `owner.updateHistory()`
  before `consumeNavigationEvents` at `WebView.desktop.kt:60–62`. Sharing one
  navigator is unsupported and rejected, but that existing pre-admission update
  is not protected by the new mobile hook. Treat atomic rejection/flag isolation
  on Desktop as a separate low-priority verification case, not a supported
  multi-owner feature or a newly demonstrated runtime vulnerability.
* The High NATIVE-001/002/010/013 native-lifetime/security acceptance gates in
  the pre-repair report remain open. These source repairs, extra test bodies and
  bytecode inspection do not add executable security/device/consumer evidence.
