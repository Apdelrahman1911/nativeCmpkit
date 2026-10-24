# Native features implementation audit

**Baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6` · **review date:** 2026-10-24 · **scope:** all 47 tracked files in camera-picker, share, webview, maps, media and notifications.

This is a source/behavioral audit, not certification that the library builds or runs on every advertised platform. No production/native implementation was changed by this reviewer. [Module/API/execution-flow knowledge](../modules/native-features.md), [reproduction procedures](../testing/native-features.md), and [machine-readable findings](findings/NATIVE.json) accompany this report. Shared build/dependency/publishing issues belong to the build audit; IO and permission contracts are covered by their reviewers.

## Executive assessment

There are **39 actionable findings: 0 Critical, 6 High, 29 Medium, 4 Low**. Evidence classification: **8 confirmed-test**, **22 confirmed-source**, **7 conditional risks**, **2 improvements**. “Confirmed-test” includes deliberately isolated exact Kotlin method bodies or real-browser DOM primitives, **not** end-to-end Kotlin Multiplatform/device tests; each record states its limits.

Most urgent work:

1. **NATIVE-001:** Desktop StopLoading is an asynchronous feedback loop, not a native stop call. Exact Kotlin handlers reproduced 100 scheduled turns with another still queued and zero native cancellations.
2. **NATIVE-013:** Desktop cookie access can replace the existing JavaFX/application-global cookie handler, losing the active store and changing unrelated networking behavior.
3. **NATIVE-019:** Android camera pending output URI disappears on Activity/process recreation even when the ActivityResult registry later reports success.
4. **NATIVE-002/006:** native/browser view disposal does not consistently release resources/references or invoke callbacks.
5. **NATIVE-010/027:** trust-boundary decisions are implicit: JavaScript-enabled inline browser HTML has the host origin, and desktop “sharing” can open untrusted files/URL handlers. These are **conditional design risks**, not demonstrated unauthenticated remote exploits.
6. Repair truthful outcome/cookie contracts before building more features on them: invalid browser expiry/HttpOnly/logout behavior, false clipboard/share success, replayed navigation and callback double delivery.

No usable maps, media player, or notification-delivery API exists in the examined scaffolds. Android/iOS camera support exists, but Desktop/Web camera stubs are no-ops. Native macOS sharing is materially different from Windows/Linux opening/copying behavior. Web iframe limitations cannot be “fixed” by bypassing browser origin or cookie security.

## Evidence and verification method

* Read all platform actuals, common APIs/defaults, native FFI/loader code, resources/cinterop and module build files. The [file/symbol ledger](../modules/native-features.md#6-complete-filesymbol-review-coverage) accounts for all 47 files, including declaration-only and excluded files.
* Followed state/content effects, event replay, factory ownership, native delegate callbacks, UI/IO dispatch, failure/timeout paths and result mapping across each target.
* Followed supporting KmpFile/provider/sample/privacy setup and native packaging workflows. These contextual files are not falsely counted as wholly reviewed by this area; their owners cover them separately.
* Compared relevant Git changes and all title-matched upstream feature issues/PRs plus archived comments; the historical matrix below distinguishes fixes present in source from unresolved reports.
* Compiled exact baseline `WebViewNavigator`, desktop navigation handler and Desktop CookieManager method bodies with a cached Kotlin2.4.20 compiler. UI state/FX queue/engine were explicit doubles; the cookie backend was real JDK. The harness uses cached coroutines1.8.0, not a resolved project integration build.
* Executed the exact Wasm clipboard JavaScript body under Node with a deliberately rejected writeText Promise. Used real Chrome153 on loopback, with a disposable browser profile, for cookie/srcdoc/sandbox primitives that mirror baseline DOM operations.
* Checked the exact JavaFX19 source JAR for WebEngine public APIs and default CookieHandler installation. Checked Apple documentation for WKWebView configuration-copy and activity-item subject semantics. Source URLs, SHA256 and reviewed entries are in [dependency evidence](../testing/native-features-probes/dependency-evidence.json); no external binaries were committed.

### Executed results

| Probe | Inspected result | Meaning / limit |
|---|---|---|
| Exact Kotlin stop-handler + navigator, fake FX queue | `steps=100 queued=1 nativeCancels=0` | Receiver resolution/self-emission demonstrated; no running native WebEngine |
| Exact navigator, two subscriptions | `Back` then `Back` after one command | replay=1 semantics demonstrated; lifecycle manifestation requires Compose integration |
| Exact Desktop CookieManager/JDK | custom handler replaced | Process-global ownership bug demonstrated without loading JavaFX GUI |
| Exact Desktop CookieManager/JDK | `/private` cookie returned for `/public/` | API query-path mismatch demonstrated; not native WebKit outbound-cookie leakage |
| Exact Desktop CookieManager/JDK | expiry advanced 1201ms after ~1.2s | incorrect lifetime→absolute-expiry mapping demonstrated |
| Exact Wasm clipboard body + rejected promise | `Success`, unhandled rejection | asynchronous fallback error is lost; not a real clipboard permission-dialog run |
| Chrome153 cookies | past numeric expires retained cookie; HttpOnly assignment rejected; root deletion missed `/private` | real browser behavior for mirrored cookie operations |
| Chrome153 iframe transition | state URL retained srcdoc; navigator-style remove loaded URL | browser precedence rule validates source mismatch |
| Chrome153 inline child script | host DOM attribute changed | host-origin exposure under explicit JS/untrusted-inline-content preconditions, not default-mode XSS |

Full sanitized output: [`results-baseline.json`](../testing/native-features-probes/results-baseline.json). The probe script's exit0 means **expected defective behavior was reproduced**, not that nativeCmpkit passes release acceptance.

### Not verified here

* Android external-camera Activity recreation, actual recipient URI grants, WebView popup/SSL/HTTP behavior, memory-profiler retention or release ordering.
* iPhone/iPad picker, photo encoding/memory, scoped URL lifetime, WK configuration effects, KVO teardown timing, web input-camera issue34, popovers or UIKit/Swift/ObjC threading.
* macOS AppKit sharing, ObjC/Rust lifetime under Instruments/ASan, picker self-retention, selected-service completion, timeout/cancellation or FFI panic recovery.
* Windows DLL file locking, custom URI handlers, desktop rendering prerequisites/classifier packaging, live FX session cookies and first-panel reentry on affected GPUs.
* A compiled Kotlin/JS or Wasm Compose sample, Firefox/WebKit clipboard/browser behavior or secure-context/permissions-policy matrices.
* Cargo dependency vulnerabilities or complete Gradle/toolchain matrix; see build review and its actual command logs. Source stubs/absent tests do not count as a passing platform suite.

## Security and resource interpretation

### Positive checks

* Common JavaScript defaults **off**. Android safe browsing defaults on with API guards; no code overrides SSL errors to proceed or enables universal access from file URLs. The presence of `@JavascriptInterface` on evaluation alone does not publish a bridge; no addJavascriptInterface registration occurs.
* Android sample provider is exported=false and uses grants, and sharing requests read rather than write access. A whole-cache FileProvider path is a narrowing opportunity, not automatic public exposure of all files.
* iOS share configures iPad popover source/anchor. Camera strongly retains its weak native delegate while its owner survives. WK KVO registration has corresponding removal in a DisposableEffect.
* JNI string-array loop deletes local refs; normal nullable inputs are guarded; current Kotlin supplies parentWindow=0 instead of an arbitrary native pointer. Native sharing does not execute interpolated shell commands.
* macOS AppKit operations are dispatched to the main queue while waiting occurs on an IO worker. Stream extraction uses `use`, a temporary file and atomic replacement where supported, so partial-byte exposure is reduced (but version races remain).
* Browser share Promise rejects distinguish AbortError from other failure; ordinary navigator.share is called synchronously from the launcher, not after a coroutine that would unnecessarily lose user activation.

### Boundaries that remain application-sensitive

* Native URL/HTML/script inputs are not origin-filtered. Enabling JavaScript, local file/content access, popups or autoplay expands capabilities. Use an explicit trusted-content policy; do not call all unrestricted API use a vulnerability.
* Native library search/cache locations execute code. System.loadLibrary-first is an intentional package-manager compatibility fix. Version/content identity and directory trust must be tightened without breaking trusted external native extraction. Same-user path control alone is not a proven privilege escalation.
* The sharer's caller retains responsibility for file readability/lifetime; success-at-selection must not authorize early deletion. iOS external scoped URLs and Android raw file URIs are not automatically made transferable by wrapping them in KmpFile.
* CookieManagers operate on default/global stores. No per-WebView private/incognito session API exists. Returned metadata is not consistently authoritative; cookie value logging can expose credentials even though this audit uses only synthetic local values.
* FFI `unwrap`, dynamically registered ObjC class names and unsafe Send/retained-pointer assumptions need macOS stress review. No concrete panic/UAF exploit was demonstrated. “Kotlin catches Throwable” is not recovery from native process abort/segfault.

## Historical decisions, previous fixes and unresolved reports

Upstream URLs are identifiers, not runtime dependencies. Full archived issue/PR/comment records are under [`docs/migration/upstream-metadata`](../migration/upstream-metadata/); consult them if upstream disappears. Exact Git objects are retained. Reported behavior is not automatically a current confirmed defect.

| Source history | Evidence and current disposition |
|---|---|
| Issues2/6/10; PR15/16, initial Desktop/JS support | Source now provides desktop JavaFX, settings and evaluateJavascript. Earlier lack of these APIs is resolved; current cross-platform error/result semantics remain NATIVE-015. Do not reproduce signed/private-looking example URLs from issue bodies in new docs/tests. |
| PR46, PR93; commits2b9a0f3/2d3b626 | WebView split from general UI to avoid pulling JavaFX/coroutines into all UI consumers. Preserve separate module boundary. StopLoading defect survived this history rather than arising from migration. |
| Issue77, WebView in adaptive sheet | Closed after maintainer could not reproduce with0.5.3. Current iOS interop/resize behavior was not device-tested. Do not present it as a newly confirmed bug. |
| Issue34, camera inside iOS WebView | Still-open separate report: dismissing web camera closes WebView. Only simulator advice is archived. No confirmed causal link to `calf-camera-picker`; retain as unverified device reproduction work. |
| Issues39/151, Desktop renderer/Linux startup | Archived QuantumRenderer/no-pipeline failures. Current JavaFX19/classifier/environment risks need real host tests; no single root cause proven from these reports alone. Build findings own dependency packaging. |
| PR203 /9dba4fd | Sets FX implicitExit(false), moves initialization into DisposableEffect to allow navigation away/back. Teardown still only invokes user callback (NATIVE-002); stop command still recursively queues itself (NATIVE-001). |
| Issue344, AWT-thread settings error | **Source-addressed:** applySettings now wraps engine writes in Platform.runLater. It is not reported as an active confirmed wrong-thread setting bug. Verify current regression on GUI hardware. |
| Issue346, JFXPanel.initFx nested event loop | Source retains JFXPanel construction during remember; risk NATIVE-018. Current Compose/host reproduction unavailable; historical stack is not a current test. |
| Issue240, PR425/ee359ce; PR427 docs | Cookie API implemented; feature request closed. Independent correctness problems in store ownership/filtering/expiry/browser support are NATIVE-011–014, not a claim the feature was never added. |
| PR426/03fdb40 | Desktop progress/title/load-state listeners added, source present. Error reset and later-document updates remain incomplete. |
| PR428/3d4a2b6/a2f15c5 | LaunchedEffect-based content updates, iOS request headers/navigation and FX thread navigation fixes present. Capture-back overrides/StopLoading still need fixes; do not undo recomposition-loop repair. |
| PR429/431/3e3b9db/666bdd0 | Browser iframe support added, not an actual native browser engine. Cookies are now host document operations despite stale no-op docs. State srcdoc/disposal/capability gaps tracked separately. |
| PR412/7e1cac6 | Documentation heading correction only; **not** a runtime page-title fix. Do not infer implementation changes from this PR title. |
| Commit942bca0; PR466/c178f5e | iOS loaded-URL and KVO progress/title/history enhancements present. KVO observers have balanced removal; provisional error/reset and lifecycle still require device coverage. |
| Issue28, PR274/c19a41f/ed5d243, PR302/ae3c1ab | Mobile camera feature added; originally unsupported desktop/web paths became no-ops during refactor. Provider setup lives in PR274 and sample. Permission logic moved to sample permission state; library does not request automatically. |
| PR311 versus PR326/7898be3 | Prior proposal described JPEG/original image; accepted baseline uses UIImageOriginalImage→PNG temp, strong delegate, main-queue presentation and simulator/photo-library fallback. Do not reintroduce invalid MediaURL/ImageURL assumptions for newly captured photos. |
| Issue288 | Basic Android/iOS capture request is source-satisfied, although camera API lacks robust lifecycle/result coverage. Recreate only a focused verification/remaining-gap task, not a duplicate request to invent an existing module. |
| PR508/4a14aa2 | Sharing introduced with Rust/macOS backend and platform fallbacks. Existing experimental marker permits API evolution, but semantics/side effects must be documented for compatibility. |
| Commit6331db2 | Both loaders learned system-library-path first for Conveyor-style extracted natives. Preserve this packaging compatibility when hardening cache. |
| Commitbefc455 | File-picker received content-hashed immutable cache and locked-DLL fallback; **share loader did not**. NATIVE-031 should adapt that existing tested implementation instead of duplicating another cache. |
| Issues27/245 | Maps and custom media data source requests remain unimplemented. Maps included-empty, media excluded-empty, notification excluded-experiment are explicitly documented in NATIVE-035. |

## Prioritization and implementation dependencies

**Phase1, correctness containment:** NATIVE-001 and013 (small focused tests first),019/020 (camera request ownership),002/006/037 (view lifecycle/rebind),004/005/008/009 (consistent navigation/state),026/032 (truthful callback boundaries). Audit findings do not authorize package/release publication.

**Phase2, security/contract clarity:** NATIVE-010/027 explicit trust/fallback policies;011/012/014 cookie scope and metadata;025/028 share outcomes/URI transfer;015/016/017/038 WebView API capability/configuration. Keep old entry points as documented adapters where viable.

**Phase3, native operation robustness:** NATIVE-029 before030 (ownership before cancellation);031 adapt existing picker cache;023/024 after020;033 UI-thread and presentation contract;018 actual toolkit startup reproduction. These need Android/macOS/iOS device-specific CI, not only Linux unit tests.

**Phase4, polish/new scope:** NATIVE-021/022 public capability/setup documentation,034/036 metadata/default reset,039 measured optimization,035 explicit future-feature design with upstream links. Maps/media/delivery are new subsystems, not audit-time rewrites.

Every item below includes exact location, root cause, impact, recommendation, risks, tests, effort and dependencies. IDs are stable and match the issue-import input; the repository-wide roadmap integrates them with other reviewers' areas.

<!-- GENERATED_FINDINGS_BEGIN -->

## Finding index

| ID | Priority | Evidence | Finding |
|---|---|---|---|
| NATIVE-001 | High | confirmed-test | [Desktop stopLoading re-enqueues itself instead of cancelling WebEngine loading](#native-001) |
| NATIVE-002 | High | confirmed-source | [Android and Desktop WebViews retain live native views after composition disposal](#native-002) |
| NATIVE-003 | Medium | confirmed-source | [Android and iOS onCreated run before the advertised native WebView reference exists](#native-003) |
| NATIVE-004 | Medium | confirmed-test | [Web state-driven URL loading does not clear existing iframe srcdoc](#native-004) |
| NATIVE-005 | Medium | confirmed-source | [WebView request state is not reset consistently on Desktop, iOS and Web](#native-005) |
| NATIVE-006 | Medium | confirmed-source | [Web WebView never invokes onDispose and retains iframe/listener references](#native-006) |
| NATIVE-007 | Medium | confirmed-source | [Non-Android saveable WebView state restores metadata but no content](#native-007) |
| NATIVE-008 | Medium | confirmed-test | [Replay-one navigation flow replays transient back/forward/stop commands on reattachment](#native-008) |
| NATIVE-009 | Medium | confirmed-source | [iOS captureBackPresses=false is overridden by settings and URL loads](#native-009) |
| NATIVE-010 | High | risk | [Enabling Web JavaScript removes all iframe isolation for inline HTML](#native-010) |
| NATIVE-011 | Medium | confirmed-test | [Browser CookieManager silently misrepresents URL, expiry, HttpOnly and deletion support](#native-011) |
| NATIVE-012 | Medium | confirmed-test | [Desktop and iOS getCookies do not implement full request-URL cookie matching](#native-012) |
| NATIVE-013 | High | confirmed-test | [Desktop CookieManager overwrites JavaFX and application-global cookie handlers](#native-013) |
| NATIVE-014 | Medium | confirmed-test | [Desktop cookie expiry is recalculated from read time and drifts into the future](#native-014) |
| NATIVE-015 | Medium | confirmed-source | [JavaScript evaluation has inconsistent failure, result and thread semantics](#native-015) |
| NATIVE-016 | Medium | confirmed-source | [Common WebContent options are silently ignored on several targets](#native-016) |
| NATIVE-017 | Medium | confirmed-source | [iOS inline-media configuration is changed only after WKWebView construction](#native-017) |
| NATIVE-018 | Medium | risk | [Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes](#native-018) |
| NATIVE-019 | High | confirmed-source | [Android camera loses its output URI across Activity/process recreation](#native-019) |
| NATIVE-020 | Medium | confirmed-source | [Camera callback/lifetime handling is unstable across recomposition](#native-020) |
| NATIVE-021 | Medium | confirmed-source | [Camera API silently drops unsupported, cancelled and failed operations](#native-021) |
| NATIVE-022 | Medium | confirmed-source | [Android camera hardcodes a host FileProvider authority without public setup or validation](#native-022) |
| NATIVE-023 | Medium | risk | [iOS camera has no in-flight presentation guard or lifecycle-bound cleanup](#native-023) |
| NATIVE-024 | Medium | risk | [Camera capture does synchronous full-resolution PNG work and has no temporary-file ownership policy](#native-024) |
| NATIVE-025 | Medium | confirmed-source | [ShareResult.Success means chooser launch/service selection rather than completed sharing on some targets](#native-025) |
| NATIVE-026 | Medium | confirmed-test | [Web clipboard fallback reports success before its promise resolves](#native-026) |
| NATIVE-027 | High | risk | [Desktop share fallback opens arbitrary files/URLs instead of offering an explicit sharing fallback](#native-027) |
| NATIVE-028 | Medium | confirmed-source | [Android file sharing forwards file:// URIs without FileProvider conversion](#native-028) |
| NATIVE-029 | Medium | confirmed-source | [macOS share leaks both the Objective-C delegate and its Arc completion state on every presented picker](#native-029) |
| NATIVE-030 | Medium | confirmed-source | [macOS sharing blocks a coroutine worker for up to five minutes without cancellation integration](#native-030) |
| NATIVE-031 | Medium | risk | [Desktop native share extraction uses one mutable filename across versions, architectures and processes](#native-031) |
| NATIVE-032 | Medium | confirmed-source | [Share callbacks can be delivered twice when application result handling throws](#native-032) |
| NATIVE-033 | Medium | risk | [Public mobile launch/evaluation operations lack an explicit main-thread contract or enforcement](#native-033) |
| NATIVE-034 | Low | confirmed-source | [Share subject is not delivered consistently and iOS assigns controller title instead of item subject](#native-034) |
| NATIVE-035 | Low | improvement | [Maps, media and notification scaffolds must not be represented as implemented features](#native-035) |
| NATIVE-036 | Low | confirmed-source | [Desktop customUserAgent cannot be reset to its documented default using null](#native-036) |
| NATIVE-037 | Medium | confirmed-source | [Replacing WebViewState or native lifecycle callbacks at the same composable identity is not safely rebound](#native-037) |
| NATIVE-038 | Medium | confirmed-source | [Android enables multiple WebView windows but supplies no window-creation handler](#native-038) |
| NATIVE-039 | Low | improvement | [WebView settings changes and error accumulation perform avoidable full updates](#native-039) |

## Detailed findings

<a id="native-001"></a>

### NATIVE-001 — Desktop stopLoading re-enqueues itself instead of cancelling WebEngine loading

**High · confirmed-test · effort S** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:225-248`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L225) — `WebViewNavigator.handleNavigationEvents / StopLoading`
* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt:248-249`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt#L248) — `WebViewNavigator.stopLoading`

**Root cause:** Inside with(webView.engine), unqualified stopLoading() has no matching WebEngine member and resolves to the enclosing WebViewNavigator.stopLoading(). That emits another StopLoading event, which queues another Platform.runLater callback.

**Impact:** One stop request produces an unbounded coroutine/FX event feedback loop while the collector lives, consumes CPU, and does not stop the network/page load. Replayed commands can restart it after attachment.

**Recommended solution:** Call webView.engine.loadWorker.cancel() explicitly on the FX thread. Use explicit native receivers for each branch and ensure stop produces no new navigation event.

**Risks / limits:** Probe replaces the FX engine and queue, not a running JavaFX GUI; the exact handler and navigator bodies were compiled. Public JavaFX19 source confirms absence of stopLoading. Do not describe this as a passed Desktop integration test.

**Evidence**

* docs/testing/native-features-probes/results-baseline.json: STOP_FEEDBACK steps=100 queued=1 nativeCancels=0.
* Dependency evidence identifies JavaFX19 WebEngine private stop(), reached by loadWorker.cancel(), not a public stopLoading API.
* git log -S stopLoading() traces the call back to the initial separate webview artifact; later FX-thread fixes retained it.

**Required tests**

* Assert a single stop request calls the native worker cancel once and emits no further commands.
* Run slow-page loading, stop, detach/reattach, and repeated-stop cases in an actual JavaFX/Compose window.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/203, https://github.com/MohamedRejeb/Calf/pull/428

<a id="native-002"></a>

### NATIVE-002 — Android and Desktop WebViews retain live native views after composition disposal

**High · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:194-215,405-408`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L194) — `AndroidView.factory/onRelease and WebViewState.webView`
* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:52-108,211-212`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L52) — `DisposableEffect/onDispose and WebViewState.webView`

**Root cause:** Android onRelease only calls the user callback; it neither stops/destroys the WebView nor clears state.webView/clients. Desktop onDispose only calls the user callback; it leaves scene, engine load, listeners and state.webView connected, with implicit FX exit disabled.

**Impact:** When callers retain WebViewState, it retains the Android Activity/view or the entire Desktop WebView/scene and callbacks after the UI is removed. Loading, audio/timers and native resources may outlive the screen; old views can be observed during remount.

**Recommended solution:** Define ownership and teardown ordering: save state first, cancel load, detach clients/listeners, remove scene/native references, destroy Android WebView after removal, and clear state.webView if it still denotes that instance. Put cleanup in finally so a throwing user onDispose cannot skip it. Manage FX runtime lifetime independently rather than exiting per view.

**Risks / limits:** Missing teardown and retained references are source-confirmed; actual retained heap size, active playback and host process shutdown depend on engine/application behavior. Do not invoke private JavaFX dispose APIs without support analysis.

**Evidence**

* Android line209 stores state.webView; line213 is the sole onRelease action.
* Desktop line101 stores state.webView and lines60-98 register strong closures; lines105-107 do not undo either.

**Required tests**

* Retain state, mount/unmount repeatedly and verify Activity/native view collectability with weak references/profilers.
* Verify teardown cancels a slow request and media and does not clear a replacement instance.
* Test onDispose throwing, delayed Platform.runLater initialization, process-state save and multiwindow operation.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/203, https://github.com/MohamedRejeb/Calf/pull/426

<a id="native-003"></a>

### NATIVE-003 — Android and iOS onCreated run before the advertised native WebView reference exists

**Medium · confirmed-source · effort S** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:47-48,194-209`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L47) — `WebView factory/onCreated`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:48-49,111-125`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L48) — `UIKitView.factory`

**Root cause:** Both mobile factories call the public zero-argument onCreated callback before assigning state.webView. Documentation explicitly directs callers to that property inside onCreated. Android additionally applies settings and replaces clients after the callback.

**Impact:** First creation callbacks see null and silently fail to customize the native view; remount can expose a stale old Android view. Cross-platform configuration code works on Desktop/Web but not the advertised mobile hook.

**Recommended solution:** Assign the native instance before invoking the public callback and document settings/client ordering. Prefer an additive platform-typed customization hook if native callbacks must remain internally owned.

**Risks / limits:** Reordering may alter applications relying on current settings precedence; lock down behavior rather than simply moving callbacks past every configuration write.

**Evidence**

* Android invokes onCreated at197 then assigns state.webView at209.
* iOS invokes onCreated at114 then assigns state.webView at123.

**Required tests**

* Assert native reference identity inside onCreated on all targets.
* Configure a native setting and verify whether common settings intentionally override it.
* Retain state across remount and verify callback never observes the previous instance.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/428

<a id="native-004"></a>

### NATIVE-004 — Web state-driven URL loading does not clear existing iframe srcdoc

**Medium · confirmed-test · effort S** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:50-59,220-226`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L50) — `state.content collector versus navigation LoadUrl`

**Root cause:** WebContent.Data sets iframe.srcdoc. A later WebContent.Url only sets src; HTML iframe srcdoc takes precedence over src until the attribute is removed. The navigator LoadUrl branch already removes srcdoc but the state branch does not.

**Impact:** Switching from inline HTML to a URL through state/content recomposition leaves old HTML displayed and can expose stale authenticated or sensitive content despite the host believing a new URL was loaded.

**Recommended solution:** Use one shared content loader for navigator and state paths and remove srcdoc before assigning src for every URL transition.

**Risks / limits:** Chrome DOM reproduction mirrors exact source operations rather than compiling Compose Web; verify JS and Wasm integration after correction. Preserve inline HTML reload semantics.

**Evidence**

* Real Chrome153 probe stateUrlLeavesSrcdoc=true; navigatorUrlClearsSrcdoc=true.

**Required tests**

* Data→Url→Data transitions via direct state assignment and remembered-state updates.
* Navigator and state loaders produce the same iframe attributes and page.
* Cross-origin destination with CSP/X-Frame-Options failure does not leave old content falsely reported as new.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/429, https://github.com/MohamedRejeb/Calf/pull/431

<a id="native-005"></a>

### NATIVE-005 — WebView request state is not reset consistently on Desktop, iOS and Web

**Medium · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:60-90`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L60) — `loadWorker state listener`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:208-247,345-383`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L208) — `WKNavigationDelegate and KVO`
* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:50-65,76-95,183-228`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L50) — `content/navigation loaders and iframe listeners`

**Root cause:** Desktop RUNNING does not clear errorsForCurrentRequest. iOS clears errors only at didCommitNavigation, so consecutive provisional failures accumulate old errors. Web never sets Loading when changing src/srcdoc and never clears prior errors/title; its cross-origin load handler cannot read URL/title and leaves old values. Web navigation capability flags are unconditionally false.

**Impact:** A successful retry can retain an old error, a new request can appear Finished, and cross-origin content may display a previous page title/URL. Consumers deriving loading/error/security UI from common state receive inconsistent or stale signals.

**Recommended solution:** Centralize begin-request state reset and terminal-state handling; separate requested URL from observable final URL; explicitly represent unknown cross-origin title/history. Clear errors at provisional request start on iOS and RUNNING on Desktop. Do not infer iframe load success from the load event alone.

**Risks / limits:** Browser deliberately hides many iframe errors and cross-origin metadata; do not promise reliable progress/final URL or bypass same-origin policy. History capability may need an explicit unsupported state rather than invented booleans.

**Evidence**

* Android onPageStarted resets errors/title, providing the existing comparison behavior.
* Desktop writes errors only on FAILED; iOS reset is didCommit only; Web event source has no Loading assignment anywhere.

**Required tests**

* Fail→success, fail→fail, reload, stop and redirects on every target.
* Browser same-origin→cross-origin→inline transitions; blocked framing and offline destination.
* iOS provisional DNS/TLS failure before commit resets the previous request errors.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/426, https://github.com/MohamedRejeb/Calf/pull/466, https://github.com/MohamedRejeb/Calf/issues/39

<a id="native-006"></a>

### NATIVE-006 — Web WebView never invokes onDispose and retains iframe/listener references

**Medium · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:35-42,69-106,162-166`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L35) — `WebView lifecycle and WebViewState.iframe`
* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.web.kt:7-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.web.kt#L7) — `CalfWebElementView signature`

**Root cause:** The public onDispose parameter is never used. The wrapper exposes only factory/update, with no release callback/effect that clears state.iframe or unregisters its load/error listeners.

**Impact:** Caller cleanup is skipped on JS/Wasm and retained WebViewState keeps a detached DOM node plus captured state/navigator closures. A remount can briefly operate on an old node; lifecycle behavior differs from every native implementation.

**Recommended solution:** Add a disposal path using the supported Compose Web interop lifecycle or an explicit DisposableEffect bound to the node. Remove listeners, stop/detach as appropriate, clear only the matching node and deliver onDispose once.

**Risks / limits:** Compose WebElementView removes its own rendered element; this finding does not claim the DOM remains mounted. The retained state reference and missing user callback are the library defects.

**Evidence**

* No occurrence of onDispose in the function body after its declaration.
* factory assigns state.iframe at97 and no branch clears it.

**Required tests**

* Mount/unmount with a callback counter; verify exactly one onDispose.
* Retained state no longer references the old iframe after removal.
* Queued load/error events after disposal do not update a replacement view.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/429, https://github.com/MohamedRejeb/Calf/pull/431

<a id="native-007"></a>

### NATIVE-007 — Non-Android saveable WebView state restores metadata but no content

**Medium · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt:319-331`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt#L319) — `rememberSaveableWebViewState`
* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:251-268`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L251) — `WebStateSaver`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:388-405`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L388) — `WebStateSaver`
* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:232-250`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L232) — `WebStateSaver`

**Root cause:** Desktop, iOS and Web savers store title and lastLoadedUrl but restore WebContent.NavigatorOnly. No native history or pending load is restored, and no platform factory consumes lastLoadedUrl to initiate a load. NavigatorOnly is explicitly a no-op.

**Impact:** After restoration the visible native/browser view is blank while metadata still describes the former page. Saved history/scroll/form state are not portable despite the common saveable helper.

**Recommended solution:** Define an honest per-platform persistence contract. Restore at least a safe requested URL with an explicit reload policy where native history is unavailable; document lost POST/form/history/scroll state and protect sensitive URL serialization. Keep full Android Bundle restore separate.

**Risks / limits:** The current common comment mentions activity recreation; non-Android full session restore is not promised in detail. A change that automatically reloads URLs could repeat side effects or leak secrets, so expose/document the policy.

**Evidence**

* All three non-Android restorers construct WebViewState(WebContent.NavigatorOnly) and only assign metadata.

**Required tests**

* Save/restore URL, HTML, navigator-only, redirect and null URL states on each target.
* Check restored content actually loads and title/history do not falsely describe a blank view.
* Ensure form submissions and one-time URLs are not automatically repeated without intended semantics.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

<a id="native-008"></a>

### NATIVE-008 — Replay-one navigation flow replays transient back/forward/stop commands on reattachment

**Medium · confirmed-test · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt:159-179,227-249`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt#L159) — `NavigationEvent and navigationEvents`
* [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:157-160`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L157) — `navigation collector`
* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:112-115`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L112) — `navigation collector`

**Root cause:** All navigation commands share MutableSharedFlow(replay=1). A new collector receives the last command even after it was already consumed by an old native view; no acknowledgement/reset distinguishes retained content from one-shot actions.

**Impact:** Recreating/rebinding a WebView can repeat Back, Forward, Reload or StopLoading unexpectedly. With NATIVE-001, a retained StopLoading can restart the feedback loop. Sharing a navigator across views broadcasts commands to both without an ownership contract.

**Recommended solution:** Separate persistent desired content from one-shot commands, or add an explicit owner/acknowledgement strategy. Choose and document what happens to commands sent before attachment rather than replacing replay=1 blindly.

**Risks / limits:** Changing to replay=0 without buffering breaks pre-attachment loadUrl/loadHtml calls, including saveable-state patterns. Preserve these intentionally with tests.

**Evidence**

* Exact common Navigator compiled in standalone probe; first() subscriptions observed Back twice after one navigateBack call.

**Required tests**

* Consume Back then replace collector; second collector must not repeat it.
* A load sent before first attachment is processed exactly once.
* Two WebViews with one navigator are either rejected/documented or have deliberate broadcast behavior.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

<a id="native-009"></a>

### NATIVE-009 — iOS captureBackPresses=false is overridden by settings and URL loads

**Medium · confirmed-source · effort S** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:83-92,111-124,251-258`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L83) — `URL load, factory and applySettings`
* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:140-146`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L140) — `IosSettings.allowsBackForwardNavigationGestures`

**Root cause:** Factory first assigns allowsBackForwardNavigationGestures=captureBackPresses, then applySettings assigns the independent setting whose default is true. Every state-driven URL load also unconditionally sets the property true.

**Impact:** Disabling captureBackPresses cannot reliably disable swipe navigation; setting the iOS flag false is undone by subsequent URL content changes. Applications with sensitive/special back navigation may unexpectedly leave a page.

**Recommended solution:** Define precedence (for example captureBackPresses AND the iOS option), apply it from a single update path, and remove the unconditional URL-load assignment. Observe captureBackPresses changes on recomposition.

**Risks / limits:** Fixing precedence changes behavior for consumers accidentally relying on the override; document the intended combined contract.

**Evidence**

* Default true settings overwrite captureBackPresses at factory time; line91 forces true again.

**Required tests**

* All combinations of captureBackPresses and iOS setting at creation, mutation, URL load and recomposition.
* Swipe-back/forward test on real iPhone/iPad confirms false actually disables gestures.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/428

<a id="native-010"></a>

### NATIVE-010 — Enabling Web JavaScript removes all iframe isolation for inline HTML

**High · risk · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:57-58,169-176,225-226`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L57) — `HTML content and iframe.applySettings`

**Root cause:** javaScriptEnabled=true removes the sandbox attribute entirely. srcdoc then inherits the host origin; scripts in supplied inline HTML can access the parent DOM, same-origin storage and host-page capabilities. There is no separate sandbox/origin policy in the common API.

**Impact:** If an application renders untrusted HTML with JavaScript enabled, content that would be isolated inside a native WebView instead obtains the browser host application origin. A browser probe changed the host DOM using only child script; exploitation requires attacker-controlled HTML and the explicit JS opt-in.

**Recommended solution:** Expose a distinct sandbox/trusted-content policy with safe defaults; for untrusted HTML use an opaque-origin sandbox allowing only needed capabilities and a validated postMessage bridge. Warn that enabling scripts is not merely toggling execution in an isolated native container.

**Risks / limits:** This is not an unconditional XSS or sandbox bypass: default JavaScript is false, normal cross-origin pages still have same-origin restrictions, and browser CSP may constrain effects. allow-scripts plus allow-same-origin for same-origin/srcdoc content is not robust isolation.

**Evidence**

* Real Chrome153 probe unsandboxedSrcdocCanModifyHost=true using a local harmless parent attribute change.
* Disabled mode sets sandbox without allow-scripts; enabled mode removes every sandbox restriction.

**Required tests**

* Untrusted inline script cannot read/mutate parent DOM or storage under isolated mode.
* Trusted mode preserves deliberate integration and is explicitly opted into.
* Test popups/forms/top navigation, nested frames, postMessage origin validation and CSP.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/431

<a id="native-011"></a>

### NATIVE-011 — Browser CookieManager silently misrepresents URL, expiry, HttpOnly and deletion support

**Medium · confirmed-test · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.web.kt:12-45`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.web.kt#L12) — `setCookie/getCookies/removeAllCookies`
* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/Cookie.kt:10-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/Cookie.kt#L10) — `Cookie contract`

**Root cause:** Web setters append numeric epoch milliseconds directly as expires, whereas cookies require an HTTP date. URL parameters are ignored in favor of host document.cookie. JavaScript cannot set HttpOnly; the implementation appends that attribute anyway. Deletion always uses path=/ and has no original domain/path.

**Impact:** An already-expired cookie can become a session cookie, requested HttpOnly writes can be rejected, cross-origin URL queries return host cookies, and logout-style removeAllCookies leaves non-root-path/domain/HttpOnly cookies. Callers receive Unit/normal lists rather than capability/error information.

**Recommended solution:** Format expiry as UTC HTTP date or valid Max-Age; reject unsupported foreign-origin/HttpOnly operations explicitly; scope browser cookie APIs to the actual document context; document that complete domain/path/HttpOnly clearing requires server cooperation and/or tracked cookie identities.

**Risks / limits:** Chrome rejected the entire HttpOnly assignment; do not claim it created an insecure non-HttpOnly cookie. Browsers may vary. Reading HttpOnly cookies via JavaScript is intentionally impossible and must not be bypassed.

**Evidence**

* Chrome153: invalidExpiresRetainsExpiredCookie=true; httpOnlyAttemptRejected=true; rootOnlyDeletionLeavesPathCookie=true.
* Both url parameters are unused. Common CookieManager documentation still says Web is no-op, while source actively writes host cookies.

**Required tests**

* Past/future expiry and session cookies in Chromium/Firefox/WebKit.
* Verify HttpOnly requests surface unsupported status rather than silent success.
* URL mismatch, path-specific/domain cookies and server-set HttpOnly logout cases.
* Cookie names/values containing delimiters are validated rather than changing attributes.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/425, https://github.com/MohamedRejeb/Calf/pull/429

<a id="native-012"></a>

### NATIVE-012 — Desktop and iOS getCookies do not implement full request-URL cookie matching

**Medium · confirmed-test · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt:42-57`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt#L42) — `getCookies`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt:75-103`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt#L75) — `getCookies domain-only filtering`

**Root cause:** Desktop returns CookieStore.get(uri), which does not apply request-path matching performed by CookieManager.get. iOS fetches all cookies and filters only on host/domain suffix, ignoring path and secure scheme, and cannot express host-only scope in the public Cookie model.

**Impact:** Returned cookies may not be applicable to the requested URL. Callers copying results into request headers can leak a path-restricted token or, on iOS, a Secure cookie into a non-HTTPS request. This API does not itself send the cookie or alter WebKit request filtering.

**Recommended solution:** Specify whether the method lists storage metadata or cookies applicable to a request. If request matching is intended, implement RFC6265 host-only/domain/path/secure/expiry rules or use the native request-cookie API; otherwise rename/add a scoped method and document restrictions.

**Risks / limits:** Desktop path mismatch was executed; iOS matching was source-reviewed only. Native browser cookie enforcement itself is not shown to be broken. Cookie path is not a general same-origin security boundary, but callers still must not forward inappropriate credentials.

**Evidence**

* Actual Desktop CookieManager standalone probe returned a cookie restricted to /private for https://audit.invalid/public/.
* iOS filter at86-92 uses only host/domain; no scheme/path predicates occur.

**Required tests**

* Domain exact/subdomain/host-only, /private versus /public, /foo versus /foobar paths.
* Secure cookie queried over HTTP versus HTTPS and expiry boundary.
* Compare returned set with actual native HTTP request headers, including duplicate names on different paths.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/425

<a id="native-013"></a>

### NATIVE-013 — Desktop CookieManager overwrites JavaFX and application-global cookie handlers

**High · confirmed-test · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt:13-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt#L13) — `cookieManager getter`

**Root cause:** Any default CookieHandler not deriving from java.net.CookieManager is replaced by a new empty java.net.CookieManager. JavaFX19 WebPage normally installs com.sun.webkit.network.CookieManager, which extends CookieHandler directly, so even a first read can replace the active WebKit cookie store. Application custom handlers are likewise replaced.

**Impact:** Cookie operations can discard access to existing login cookies and change networking behavior for every component using the process-global handler. JavaFX uses special javascript/javascripts schemes for document.cookie filtering, so substituting an unrelated handler also requires semantic compatibility review.

**Recommended solution:** Do not mutate global state during a getter. Establish explicit cookie-store ownership at toolkit initialization, preserve/adapt compatible handlers, or expose a deliberate application-supplied backend. Handle JavaFX’s store and concurrent access without silently replacing it.

**Risks / limits:** A custom-handler replacement was executed against the actual Kotlin cookie class. JavaFX default installation/type were verified in the exact 19 source archive; loss of a real logged-in JavaFX session remains a required GUI integration test. No private com.sun API adoption without maintenance assessment.

**Evidence**

* Standalone actual CookieManager probe COOKIE_HANDLER_REPLACED true.
* JavaFX19 WebPage.java141-146 installs com.sun.webkit.network.CookieManager; that class extends CookieHandler, not java.net.CookieManager.

**Required tests**

* Login in a real WebEngine, call getCookies, then ensure session and handler identity remain valid.
* Install a custom CookieHandler before creation and verify library does not overwrite it.
* Two managers accessed concurrently and secure/HttpOnly document.cookie behavior under the chosen backend.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/425

<a id="native-014"></a>

### NATIVE-014 — Desktop cookie expiry is recalculated from read time and drifts into the future

**Medium · confirmed-test · effort S** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt:30-37,50-54`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt#L30) — `setCookie/getCookies expiresDate mapping`

**Root cause:** HttpCookie.maxAge is a lifetime measured from creation, not remaining time. getCookies converts it to epoch expiry using current time on every read rather than preserving the creation timestamp/original expiry.

**Impact:** Repeated reads report later and later expiration while the Java cookie store still expires at the original time. Code persisting or copying those returned cookies can extend sessions unintentionally and show misleading session lifetime.

**Recommended solution:** Preserve an absolute expiry in controlled metadata or use a backend exposing creation/expiry; otherwise explicitly mark expiry unavailable rather than inventing it. Keep session/maxAge=0 distinctions.

**Risks / limits:** The store itself still expires cookies; this finding concerns exposed metadata and downstream copying. Avoid relying on inaccessible JDK internals to read creation time.

**Evidence**

* Actual Desktop CookieManager probe reported +1201ms expiry drift after ~1.2s without rewriting the cookie.

**Required tests**

* Set a cookie with a known future expiry; reads separated in time remain at the same absolute expiry.
* Roundtrip returned cookie to another store without increasing lifetime.
* Session, already-expired, near-second-boundary and overflow-sized timestamps.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/425

<a id="native-015"></a>

### NATIVE-015 — JavaScript evaluation has inconsistent failure, result and thread semantics

**Medium · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:375-378`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L375) — `evaluateJavascript`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:188-195`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L188) — `evaluateJavascript`
* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:204-208`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L204) — `evaluateJavascript`
* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:152-159`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L152) — `evaluateJavascript`

**Root cause:** Android/iOS call native APIs on the caller thread and silently omit callback when no view exists. Desktop queues to FX but does not catch executeScript exceptions. iOS sends localized error text through the same String channel as success. Android returns native JSON-encoded values while other targets use toString; Web catches errors as null.

**Impact:** Portable client code cannot reliably distinguish null, error text, quoted string and successful string, and may wait forever for callbacks or cause UI-thread violations/uncaught FX exceptions. A callback throwing inside the Web try block can itself trigger a second callback(null).

**Recommended solution:** Add a typed result/error API with documented serialization and exactly-once callback/suspend semantics; route native execution to the correct UI dispatcher, handle absent/disposed views and script errors explicitly. Preserve the old function as a documented compatibility adapter.

**Risks / limits:** Do not expose a universal unsafe bridge to untrusted pages while adding functionality. Existing consumers may depend on Android JSON encoding; changes need additive compatibility treatment.

**Evidence**

* Source methods differ in both dispatch and error handling; no common result normalization exists.
* The Android JavascriptInterface annotation does not itself register a JS bridge; no addJavascriptInterface call exists in the module.

**Required tests**

* Evaluate string, number, object, null, undefined and throwing scripts on all targets.
* Call before attach, after dispose, off main thread and after callback substitution.
* Callback exceptions are not misreported as script failures or delivered twice.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/issues/2, https://github.com/MohamedRejeb/Calf/pull/16

<a id="native-016"></a>

### NATIVE-016 — Common WebContent options are silently ignored on several targets

**Medium · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt:46-58,165-176,264-267`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt#L46) — `WebContent, navigation payloads and header documentation`
* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:120-132,240-243`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L120) — `load/loadContent`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:94-100,272-289`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L94) — `HTML data loaders`
* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:50-59,220-226`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L50) — `iframe loads`

**Root cause:** Desktop drops additionalHttpHeaders, baseUrl, encoding and historyUrl. Web drops URL headers and HTML base/mime/encoding/history entirely. iOS state-driven HTML only calls loadHTMLString, while navigator HTML with a base URL encodes bytes as UTF8 regardless of the requested encoding label. Common documentation claims headers apply to all subsequent requests although mobile code only sets them on the requested load.

**Impact:** Authentication/header-dependent pages or relative HTML resources can fail silently; iOS non-UTF8 labels can mismatch UTF8 data. Applications cannot infer parity from the common signatures. Automatic forwarding of credential headers would itself need an origin policy.

**Recommended solution:** Document and expose capability restrictions; validate/reject unsupported options rather than implying support. Share consistent state/navigator loaders. If implementing headers/base URLs, do not leak authorization across origins; encode bytes consistently with the declared encoding.

**Risks / limits:** Browser cannot attach arbitrary headers to iframe navigation; a proxy/fetch workaround changes origin, cookies, CSP and security and is not a routine fix. Do not promise full web/native parity.

**Evidence**

* Desktop engine.load receives only content.url/event.url. Web assigns only src/srcdoc.
* iOS navigator line275 always dataUsingEncoding(NSUTF8StringEncoding), but line282 uses caller event.encoding.

**Required tests**

* Authenticated URL with custom header, redirect to same/different origin and subsequent links/subresources.
* Inline relative URLs with baseUrl and non-ASCII data under supported encodings.
* State versus navigator content produce the same semantics per platform.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/428, https://github.com/MohamedRejeb/Calf/pull/429

<a id="native-017"></a>

### NATIVE-017 — iOS inline-media configuration is changed only after WKWebView construction

**Medium · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:111-124,251-258`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L111) — `WKWebView factory and applySettings`
* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:149-155`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L149) — `IosSettings.allowsInlineMediaPlayback`

**Root cause:** The factory constructs WKWebView() with default configuration, then sets configuration.allowsInlineMediaPlayback. Apple’s configuration property returns a copy and changing that configuration does not affect the existing web view. Dynamic changes repeat the same ineffective scalar assignment.

**Impact:** The common default/setting can report inline playback enabled while iPhone behavior remains the native default. Consumers cannot reliably opt into inline playback using the exposed API.

**Recommended solution:** Create WKWebViewConfiguration before native view initialization and pass it to WKWebView(frame, configuration). Clearly separate creation-only options from mutable preferences; recreate deliberately or reject unsupported runtime changes.

**Risks / limits:** No iOS playback run was possible. Evidence concerns the scalar configuration field, not an assumption that every nested preferences property is copied or that all JavaScript toggles fail.

**Evidence**

* Apple WKWebView.configuration documentation retrieved2026-10-24: returns a copy; changes do not affect the web view configuration.
* The code uses WKWebView() then configuration.allowsInlineMediaPlayback; no prepared configuration initializer exists.

**Required tests**

* iPhone video with playsinline under true/false initial settings.
* Changing creation-only configuration after mount has explicitly tested documented behavior.
* Ensure initialization order does not regress onCreated, navigation delegate or default website data store.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://developer.apple.com/documentation/webkit/wkwebview/configuration

<a id="native-018"></a>

### NATIVE-018 — Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes

**Medium · risk · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:50-54`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L50) — `remember JFXPanel initialization`

**Root cause:** JFXPanel() is created synchronously inside remember. The first panel can bootstrap JavaFX and enter a nested AWT event loop while Compose is composing/rendering; archived issue346 shows exactly this stack path. There is no coordinated preinitialization or failure UI.

**Impact:** On affected runtime/host combinations first WebView composition may re-enter Compose rendering and throw Reentry into ignoringRedrawRequests. Missing graphics/native prerequisites can also abort toolkit startup, but their exact root causes differ.

**Recommended solution:** Reproduce on current supported hosts/Compose first. Establish a documented toolkit startup stage outside an active composition and an error/capability path; marshal UI objects to their required threads and preserve multiwindow lifecycle.

**Risks / limits:** Historical stack is evidence of a reported prior failure, not proof that current Compose1.12 reproduces it. JavaFX19 classifiers/prerequisites are separately tracked by build findings. Do not blindly move JFXPanel construction to a worker thread.

**Evidence**

* Archived issue346 stack includes SwingInteropContainer reentry via JFXPanel.initFx and library WebView creation.
* Current source retains direct remember { JFXPanel() }. Issue344 setting-thread failure is different and has a source fix (Platform.runLater at215-221).

**Required tests**

* Cold first WebView creation during recomposition with FX initially uninitialized.
* macOS AWT/Metal and Linux X11/Wayland graphics matrices; repeated removal/recreation.
* Explicit unsupported/headless environment result rather than unexplained renderer exception.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/issues/346, https://github.com/MohamedRejeb/Calf/issues/39, https://github.com/MohamedRejeb/Calf/issues/151, https://github.com/MohamedRejeb/Calf/issues/344

<a id="native-019"></a>

### NATIVE-019 — Android camera loses its output URI across Activity/process recreation

**High · confirmed-source · effort M** · modules: `calf-camera-picker`

**Baseline locations**

* [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:28,35-48,59-73`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L28) — `imageUri and rememberCameraPickerLauncher`

**Root cause:** The pending image URI is stored only inside a newly remembered CameraPickerLauncherAndroidImpl. ActivityResultRegistry can deliver a restored TakePicture Boolean, but the recreated instance has imageUri=null and drops the successful result.

**Impact:** Capturing a photo while the host Activity is recreated or process is reclaimed loses the application result and leaves the camera-created file orphaned. The most important user action can appear to succeed in the camera app but disappear on return.

**Recommended solution:** Persist the pending output URI/request state with saveable state or an explicit saved-state owner before launching. Restore it before result delivery, clear it after terminal completion and handle interrupted requests deliberately.

**Risks / limits:** This is a source-traced lifecycle defect; no Android device/emulator Activity recreation test was run by this reviewer. Do not persist a granted URI longer than its actual access lifetime without an ownership policy.

**Evidence**

* imageUri initializes null at28; only launch assigns it at42; handleResult requires non-null at47.
* remember rather than rememberSaveable is used for both holder and launcher.

**Required tests**

* Enable dont-keep-activities, launch camera, capture, return and receive exactly one readable KmpFile.
* Rotate/recreate and simulate process death while external camera is foreground.
* Cancelled/restored requests remove only library-owned temporary files and do not deliver stale URI.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/274, https://github.com/MohamedRejeb/Calf/pull/302

<a id="native-020"></a>

### NATIVE-020 — Camera callback/lifetime handling is unstable across recomposition

**Medium · confirmed-source · effort M** · modules: `calf-camera-picker`

**Baseline locations**

* [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:22-25,59-73`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L22) — `CameraPickerLauncherAndroidImpl and remember factory`
* [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:29-30,100-105`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L29) — `pickerDelegate and remember(viewController,onResult)`

**Root cause:** Android remember has no keys and permanently captures the first onResult/context. iOS keys the whole launcher on onResult, so replacing an inline callback replaces the object that owns the strong UIImagePicker delegate reference during an in-flight operation.

**Impact:** Android can call a stale handler capturing an obsolete item/navigation identity. iOS has a conditional delegate-lifetime risk when old launcher ownership is lost on recomposition; the existing strong-reference fix is only effective while that launcher remains retained.

**Recommended solution:** Remember one launcher per platform host, keep onResult current via rememberUpdatedState, and explicitly retain/clear active operation delegates independent of changing callbacks. Define which callback receives an in-flight request result.

**Risks / limits:** Android stale capture is source-confirmed. Premature iOS deallocation under Kotlin/Native GC is a risk, not reproduced; do not undo the original strong delegate retention from PR326.

**Evidence**

* Android launcher construction closes over onResult only once at70.
* iOS remember(viewController,onResult) creates a new launcher for changed function identity; UIKit delegate is weak.

**Required tests**

* Change callback from A to B while capture is active and assert agreed callback semantics.
* Repeated ordinary recompositions do not replace iOS active operation owner.
* Force Kotlin/Native GC/memory pressure during presentation and verify delegate callbacks still arrive.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/326

<a id="native-021"></a>

### NATIVE-021 — Camera API silently drops unsupported, cancelled and failed operations

**Medium · confirmed-source · effort M** · modules: `calf-camera-picker`

**Baseline locations**

* [`calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt:7-14`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt#L7) — `CameraPickerLauncher and onResult contract`
* [`calf-camera-picker/src/desktopMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.desktop.kt:8-19`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/desktopMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.desktop.kt#L8) — `Desktop no-op launcher`
* [`calf-camera-picker/src/webMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.web.kt:8-19`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/webMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.web.kt#L8) — `Web no-op launcher`
* [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:30-49`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L30) — `launch/handleResult`
* [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:57-76`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L57) — `finish/cancel delegate`

**Root cause:** Only a non-null KmpFile success callback is modeled. Desktop/Web launch are Unit no-ops; Android no-camera/cancel returns nothing; iOS cancel, image-conversion and write failures all disappear without an outcome. Other launch exceptions escape instead.

**Impact:** Callers cannot reliably clear busy UI, distinguish denial/cancellation/unavailable from a pending picker, or feature-detect desktop/web. Common availability is misleading despite compilation succeeding.

**Recommended solution:** Add a result/capability API covering success, cancellation, unavailable and categorized failure, while keeping the legacy success-only callback as an adapter. Do not pretend unsupported platforms captured an image. Document permission requirements and iOS photo-library fallback.

**Risks / limits:** Adding cases to existing public sealed types can break exhaustive callers; this API currently has no result type, so use an additive overload/type and migration guidance. Do not silently implement a major camera engine during this audit.

**Evidence**

* Desktop/Web launch bodies are literally Unit; error/cancel paths in mobile have no callback.
* Upstream request288 is source-satisfied for basic mobile capture, not desktop/web.

**Required tests**

* Every platform produces one defined terminal outcome for cancel/unavailable/error.
* No camera app, feature absent, permission denied and iOS simulator library fallback.
* Desktop/Web capability checks align with launcher behavior.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/issues/28, https://github.com/MohamedRejeb/Calf/issues/288, https://github.com/MohamedRejeb/Calf/pull/274

<a id="native-022"></a>

### NATIVE-022 — Android camera hardcodes a host FileProvider authority without public setup or validation

**Medium · confirmed-source · effort M** · modules: `calf-camera-picker`

**Baseline locations**

* [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:35-43`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L35) — `launch FileProvider URI creation`
* [`sample/android/src/main/AndroidManifest.xml:58-66`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/android/src/main/AndroidManifest.xml#L58) — `sample FileProvider registration`
* [`sample/android/src/main/res/xml/filepaths.xml:2-6`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/android/src/main/res/xml/filepaths.xml#L2) — `whole-cache provider path`

**Root cause:** API24+ requires ${context.packageName}.provider and a provider path covering cacheDir, but the library ships no manifest/provider contract or dedicated camera setup guide. getUriForFile and launcher.launch are outside error handling. A device camera feature does not ensure an installed intent handler.

**Impact:** A host adding only the artifact can crash on first launch with missing provider metadata or unmatched path. Authority collisions or host-custom providers cannot be selected. Copying the sample exposes the whole cache tree as grantable rather than a camera-only subdirectory.

**Recommended solution:** Document/validate a configurable authority/output provider, reserve a narrow camera cache subdirectory, and return explicit configuration/launch failure. If a manifest provider is bundled later, use a namespaced authority and preserve host override/backward compatibility.

**Risks / limits:** The sample provider is exported=false with temporary grants: whole-cache path is not proof all cache files are publicly readable. Treat narrowing as defense in depth, not an existing unauthenticated data leak.

**Evidence**

* No camera AndroidManifest.xml exists in the baseline.
* Setup details survive in upstream PR274 body, while the current sample is the only in-repository provider example.

**Required tests**

* Minimal consuming app with correct/missing/wrong provider setup on API23 and24+.
* Host with its own provider authority and no installed camera intent handler.
* Only camera-owned files can be granted through recommended provider configuration.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/274

<a id="native-023"></a>

### NATIVE-023 — iOS camera has no in-flight presentation guard or lifecycle-bound cleanup

**Medium · risk · effort M** · modules: `calf-camera-picker`

**Baseline locations**

* [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:29-32,49-95`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L29) — `launch, delegate storage and presentation`

**Root cause:** Each launch replaces the single pickerDelegate field and schedules another presentation without checking an already-presented controller or active request. Delegate completion calls onResult before dismissal/clearing; a reentrant launch or throwing callback can skip cleanup or overwrite the new operation delegate. Composition disposal is not handled.

**Impact:** Rapid/reentrant launch can cause UIKit presentation rejection, lost/weak delegates or results; leaving the screen can leave a controller/work active. A throwing callback can leave the original picker undismissed. These cases are not safely serialized.

**Recommended solution:** Represent an explicit active request with a single-flight guard and stable owner, dismiss/clear in finally using instance identity, and define cancellation on owner disposal. Deliver user callbacks after internal lifecycle cleanup when appropriate.

**Risks / limits:** UIKit/device timing and GC outcomes were not reproduced. The source shows missing guards/order, not guaranteed crash for every double tap. Coordinate callback ownership with NATIVE-020.

**Evidence**

* launch unconditionally overwrites pickerDelegate at88; completion invokes onResult at64 then clears shared field at70.
* No DisposableEffect/close/in-flight flag exists in the iOS launcher.

**Required tests**

* Double tap launch, callback launches again, callback throws, owner navigates away.
* Denied permissions, camera unavailable, simulator fallback and presentation over another modal.
* Exactly one active picker and no old delegate cleanup clears a replacement operation.

**Dependencies:** NATIVE-020

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/326

<a id="native-024"></a>

### NATIVE-024 — Camera capture does synchronous full-resolution PNG work and has no temporary-file ownership policy

**Medium · risk · effort M** · modules: `calf-camera-picker`

**Baseline locations**

* [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:57-83`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L57) — `UIImagePNGRepresentation and saveTempImageFile`
* [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:35-49`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L35) — `cache output and handleResult`

**Root cause:** The iOS delegate synchronously encodes the original full-resolution UIImage as PNG and atomically writes the whole NSData before dismissing/calling success. iOS random-named and Android timestamp-named temporary files have no cleanup/ownership contract; cancelled/abandoned Android captures are not deleted.

**Impact:** Large photos can stall the main thread and temporarily retain decoded image plus PNG buffer plus file-write resources. Repeated captures can accumulate sensitive photos/cache space until external cleanup; callers do not know when returned files may disappear.

**Recommended solution:** Measure representative large images, move safe encoding/file work off the UI thread, offer bounded format/quality/resolution policy, and define explicit ownership/TTL for returned files. Delete only failed/cancelled library-owned outputs; successful files must remain valid for documented consumption.

**Risks / limits:** Latency/OOM/disk growth magnitude is workload/device-dependent and was not benchmarked. Temporary directories are OS-managed but not immediate guaranteed cleanup. JPEG/HEIF choices affect transparency, quality, orientation and metadata.

**Evidence**

* UIImagePNGRepresentation, NSData writeToFile and callback all execute inside the UIKit result delegate synchronously.
* Neither platform has a delete/close/TTL path for capture outputs.

**Required tests**

* Real-device 12/48MP capture latency, peak resident memory and UI responsiveness.
* Disk-full/write-failure/cancel/repeated capture and cache eviction.
* File remains readable for expected consumer lifetime; cleanup never deletes another request file.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/311, https://github.com/MohamedRejeb/Calf/pull/326

<a id="native-025"></a>

### NATIVE-025 — ShareResult.Success means chooser launch/service selection rather than completed sharing on some targets

**Medium · confirmed-source · effort M** · modules: `calf-share`

**Baseline locations**

* [`calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt:26-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt#L26) — `rememberShareLauncher result callback`
* [`calf-share/native/src/lib.rs:136-162`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/native/src/lib.rs#L136) — `did_choose delegate`
* [`calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareResult.kt:11-19`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareResult.kt#L11) — `Success/Dismissed semantics`

**Root cause:** Android reports Success immediately after startActivity(chooser), before user selection or cancellation. macOS returns Success when NSSharingServicePicker didChooseSharingService reports a non-null service, not when that service completes or fails.

**Impact:** Consumers may erase source files, show false success, count completed shares or navigate away even if a user cancels or a service later fails. Android Dismissed cannot be produced by this implementation; macOS success is only service selection.

**Recommended solution:** Make result semantics explicit per platform and distinguish Presented/Selected from Completed where native APIs permit. Android cannot generally prove a recipient delivered content; macOS should observe the service delegate for actual completion if claiming it. Preserve existing API through a documented additive result model.

**Risks / limits:** Do not promise actual delivery through share targets that expose no completion API. A compatibility change to Success meaning requires migration notes. Files must remain available while the recipient/service still reads them.

**Evidence**

* Android callback at28 follows startActivity immediately.
* Rust chosen=!service.is_null() directly maps to RESULT_SUCCESS.
* iOS completionWithItemsHandler uses the completed flag, illustrating nonuniform semantics.

**Required tests**

* Dismiss Android chooser and cancel/fail a selected macOS service without reporting completed share.
* Verify callbacks occur at documented stages and exactly once.
* Delay recipient file reads past chooser selection to validate file lifetime.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/508

<a id="native-026"></a>

### NATIVE-026 — Web clipboard fallback reports success before its promise resolves

**Medium · confirmed-test · effort S** · modules: `calf-share`

**Baseline locations**

* [`calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt:58-93`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt#L58) — `shareText/shareUrl clipboard fallback`
* [`calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt:35-37`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt#L35) — `copyToClipboard`
* [`calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt:80-81,126-128`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt#L80) — `jsCopyToClipboard`

**Root cause:** copyToClipboard discards navigator.clipboard.writeText Promise and returns Unit. The caller immediately reports Success in a synchronous try/catch; asynchronous permission/insecure-context rejections bypass that catch and have no rejection handler.

**Impact:** Unsupported native sharing can falsely report a successful copy while nothing reaches the clipboard and an unhandled rejection is emitted. The user loses a fallback action without useful feedback.

**Recommended solution:** Return/await clipboard completion via callback/promise/suspend interop and map rejection to a real unavailable/failure outcome. Check secure context/API support and preserve user activation requirements.

**Risks / limits:** The Node proof uses the exact Wasm JS body with a mocked rejection, not real clipboard permission UI. Browser integration must test both JS/Wasm and real activation. Never read unrelated clipboard contents in tests.

**Evidence**

* Standalone Node result outcomes=[Success], unhandledRejection=true for a rejected writeText promise.

**Required tests**

* Rejected NotAllowedError promise produces no Success and no unhandled rejection.
* Resolved promise produces one Success only after completion.
* Missing clipboard API, insecure context, denied permission and direct user gesture.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/508

<a id="native-027"></a>

### NATIVE-027 — Desktop share fallback opens arbitrary files/URLs instead of offering an explicit sharing fallback

**High · risk · effort M** · modules: `calf-share`

**Baseline locations**

* [`calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt:51-64,108-155`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt#L51) — `handleShare/shareUrlFallback/shareFileFallback/shareFilesFallback`

**Root cause:** On Windows/Linux or any native-share failure, URLs are sent to Desktop.browse and files to Desktop.open with no MIME, URI-scheme or executable/handler policy. This occurs automatically after swallowed native errors, not after a separate open/preview decision.

**Impact:** A user asking to share can instead launch a registered URL handler or open an untrusted file in an associated application. Depending on OS associations, opening executable/script/shortcut content can run code; many files can launch many apps. No code execution exploit was demonstrated and user-supplied content/control of the call are required.

**Recommended solution:** Make fallback behavior explicit/opt-in. Prefer Unavailable, copying shareable data, or a documented export/open-location action over automatically opening content. Validate supported URL schemes and avoid executing/previewing untrusted files as an incidental share operation.

**Risks / limits:** Current docs disclose opening default apps on Windows/Linux, so this is a safety/design risk rather than hidden malicious behavior. Removing it can be a user-visible compatibility change; offer a policy parameter and deprecation path.

**Evidence**

* shareFileFallback calls desktop.open(file) at132; Files repeats it at147.
* MIME type passed in ShareContent.File/Files is not used by Desktop fallback.

**Required tests**

* With OS open/browse calls mocked, file share does not execute/open without chosen policy.
* Native-loader failure follows the same safe fallback as unsupported OS.
* Untrusted file extensions/custom URI schemes and multi-file partial failure produce a truthful result without unintended handlers.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/508

<a id="native-028"></a>

### NATIVE-028 — Android file sharing forwards file:// URIs without FileProvider conversion

**Medium · confirmed-source · effort M** · modules: `calf-share`, `calf-io`

**Baseline locations**

* [`calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt:65-85`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt#L65) — `createFileShareIntent/createMultipleFilesShareIntent`
* [`calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt:8-10,59-62`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt#L8) — `KmpFile constructor/File.toKmpFile`

**Root cause:** Sharing forwards KmpFile.uri directly into EXTRA_STREAM with a read flag. Public KmpFile accepts arbitrary Uri and java.io.File.toKmpFile explicitly constructs Uri.fromFile; that file:// path is not made shareable by FLAG_GRANT_READ_URI_PERMISSION.

**Impact:** A natural File.toKmpFile→ShareContent.File path fails on modern Android with file URI exposure or an unreadable recipient path, instead of sharing. Android catch usually reduces the launch failure to Unavailable with no diagnostic.

**Recommended solution:** Require/validate content URIs or convert library-owned local files through an explicitly configured FileProvider before launching. Preserve document-provider URI grants and avoid granting write/all-cache access unnecessarily; surface meaningful failure.

**Risks / limits:** The API also correctly supports content:// KmpFiles. Do not blanket-copy arbitrary provider files or broaden grants merely to support file://. Device intent behavior still requires instrumented validation.

**Evidence**

* KmpFile.android.kt File.toKmpFile returns Uri.fromFile(this).
* Share construction does no URI scheme check/conversion before creating ACTION_SEND/ACTION_SEND_MULTIPLE.

**Required tests**

* Internal File.toKmpFile on API24+ produces a recipient-readable content URI.
* SAF photo/document URIs retain least-privilege read access and correct multi-file ClipData/extra grants.
* Revoked/ungrantable URI, empty list, mixed MIME and provider exceptions.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/508

<a id="native-029"></a>

### NATIVE-029 — macOS share leaks both the Objective-C delegate and its Arc completion state on every presented picker

**Medium · confirmed-source · effort M** · modules: `calf-share`

**Baseline locations**

* [`calf-share/native/src/lib.rs:148-162,255-259,294-295`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/native/src/lib.rs#L148) — `did_choose, Arc::into_raw and mem::forget(delegate)`

**Root cause:** A cloned Arc is converted into a raw pointer in the delegate ivar, but no dealloc or completion cleanup ever consumes that owning raw reference. did_choose reconstructs it and immediately forgets it. The Objective-C delegate itself is mem::forget-ed permanently with no owner to release it.

**Impact:** Each picker that reaches delegate creation leaks a native object and its Rust mutex/condition-variable allocation, including dismissal and timeout. The source leak is definite, while the per-request memory size is not measured.

**Recommended solution:** Use an explicit retained operation owner and balanced lifetime/teardown. Release the raw Arc exactly once from delegate dealloc or a safely synchronized completion path, clear the pointer, and release delegate/picker after callbacks can no longer occur. Handle late callbacks after timeout without use-after-free.

**Risks / limits:** Naively dropping the delegate immediately or Arc after the waiting thread wakes risks a weak-delegate loss or use-after-free. ObjC callback lifetime, picker retention and duplicate callbacks require a real macOS design/test, not a one-line mem::forget removal.

**Evidence**

* Arc::into_raw(ctx.pair.clone()) increments ownership at256; no matching owning drop exists.
* std::mem::forget(delegate) at295 has no later Retained::from_raw/release counterpart.

**Required tests**

* Thousands of share/cancel cycles show stable allocations under Instruments/leaks.
* Success, cancellation, timeout, no-window and late/duplicate callbacks drop each owner exactly once.
* ASan/native stress with concurrent requests validates no UAF or double-free after cleanup.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/508

<a id="native-030"></a>

### NATIVE-030 — macOS sharing blocks a coroutine worker for up to five minutes without cancellation integration

**Medium · confirmed-source · effort L** · modules: `calf-share`

**Baseline locations**

* [`calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt:24-35,74-85`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt#L24) — `rememberShareLauncher/showNativeShare`
* [`calf-share/native/src/lib.rs:180-198,298-324`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/native/src/lib.rs#L180) — `dispatch_async_f and Condvar wait`

**Root cause:** The JNI function schedules AppKit work then synchronously waits on Condvar with a 300-second timeout. withContext(Dispatchers.IO) does not make this native blocking call cancellable. There is no native cancellation handle or single-flight request guard; spurious wakes restart a full timeout window.

**Impact:** Leaving composition cancels the coroutine result delivery but cannot close the picker or immediately release the worker. Repeated launches can occupy many workers and show overlapping native UI. Missing/late callbacks turn into Dismissed after a long delay unrelated to actual user dismissal.

**Recommended solution:** Expose asynchronous native completion or a cancellable operation handle, serialize appropriate UI requests, and use an absolute deadline with a distinct timeout/error outcome. Keep all AppKit calls on main and ensure completion-state lifetime handles cancellation/late callbacks.

**Risks / limits:** The existing implementation correctly keeps the blocking wait off the ordinary Compose UI thread. No macOS missing-callback event was reproduced; the non-cancellable wait and timeout behavior are source-confirmed. Avoid waiting on the AppKit main queue through any new entry point.

**Evidence**

* Rust uses Duration::from_secs(300) and wait_timeout in a loop; Kotlin wraps it only with Dispatchers.IO.

**Required tests**

* Cancel scope while picker open and verify prompt cleanup without occupying an IO worker until timeout.
* Repeated requests, unavailable keyWindow/contentView, timeout, spurious wake and late callback.
* Stress a bounded pool and assert exactly-once terminal result with balanced native lifetime.

**Dependencies:** NATIVE-029

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/508

<a id="native-031"></a>

### NATIVE-031 — Desktop native share extraction uses one mutable filename across versions, architectures and processes

**Medium · risk · effort M** · modules: `calf-share`

**Baseline locations**

* [`calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibLoader.kt:47-84`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibLoader.kt#L47) — `cache directory/extraction/System.load`

**Root cause:** Resources are OS/architecture-specific but every version/architecture extracts into the same per-user basename. Atomic move prevents partially written files, but there is no lock or immutable content-addressed identity between move and System.load. mkdirs results/ownership/symlink constraints are not validated.

**Impact:** Concurrent JVMs or versions may load the other process artifact; architecture changes can collide. Windows can refuse replacing a DLL already loaded by another process, forcing a fallback. A writable/redirected cache/system library path is a trust boundary, but same-user control alone is not a demonstrated privilege escalation.

**Recommended solution:** Use version/OS/architecture/content-digest immutable filenames in a verified private cache directory; validate bytes/path, extract atomically without overwriting loaded versions, and document cleanup. Preserve intentional System.loadLibrary-first support for external packagers as an explicit trusted override. Reuse/adapt the content-addressed NativeLibCache already implemented in calf-file-picker rather than duplicating a new extraction design.

**Risks / limits:** No wrong-binary or arbitrary-code execution was performed. The move-to-load race and Windows replacement outcome depend on concurrent launches/platform rules; cache and native library trust should be tested without claiming an exploitable CVE.

**Evidence**

* ResourcePath includes osPart/archPart at47; targetFile uses only libFileName at60.
* Source performs mutable rename then loads path at84 with no intervening identity check.
* calf-file-picker has a newer immutable content-hashed NativeLibCache (commit befc455); the equivalent share loader was not migrated to that cache strategy.

**Required tests**

* Two versions/architectures race between extraction and loading and each receives its own digest.
* Concurrent Windows process with loaded DLL does not lose native functionality.
* Read-only home, failed mkdirs, symlinked cache, interrupted extraction, no resource and trusted external packager library.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/commit/6331db22d2018c1a1ea2b52a291da2d8ee78138d, https://github.com/MohamedRejeb/Calf/commit/befc455

<a id="native-032"></a>

### NATIVE-032 — Share callbacks can be delivered twice when application result handling throws

**Medium · confirmed-source · effort S** · modules: `calf-share`

**Baseline locations**

* [`calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt:26-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt#L26) — `share launch try/catch`
* [`calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt:45-55`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt#L45) — `handleSharePromise`
* [`calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt:10-18,29-37,48-54,64-70`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt#L10) — `then/catch chains`

**Root cause:** Android includes currentOnResult(Success) inside the try that handles startActivity; a callback exception is caught as a launch failure and the callback is invoked again with Unavailable. Browser promise.then invokes the callback before a trailing catch that treats the callback exception as a share rejection and invokes another outcome.

**Impact:** One operation can produce conflicting duplicate results; user bugs are hidden as platform failures and destructive callback side effects can repeat. A second throwing invocation may escape in a different place as an unhandled error.

**Recommended solution:** Catch only platform operation errors, then invoke user callbacks outside that catch boundary. Use promise.then(onFulfilled,onRejected) or equivalent separate settlement handling so result callback exceptions are not remapped to share outcomes.

**Risks / limits:** Application callbacks are normally expected not to throw, but library error boundaries must not manufacture a second terminal platform event. Preserve crash reporting for the original application exception.

**Evidence**

* Android currentOnResult at28 lies inside catch Exception. JS/Wasm append catch after then handlers that invoke callbacks.

**Required tests**

* Callback deliberately throws after recording Success; exactly one callback invocation is observed.
* Platform start/share rejection invokes one failure and is distinct from callback failure.
* JS/Wasm resolved/rejected promises and Android ActivityNotFoundException paths.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/508

<a id="native-033"></a>

### NATIVE-033 — Public mobile launch/evaluation operations lack an explicit main-thread contract or enforcement

**Medium · risk · effort M** · modules: `calf-camera-picker`, `calf-share`, `calf-webview`

**Baseline locations**

* [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:32-36,92-95`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L32) — `camera construction/presentation`
* [`calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt:49-100`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt#L49) — `presentShareSheet`
* [`calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt:20-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt#L20) — `context.startActivity`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt:35-65,75-83,110-123`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt#L35) — `WKHTTPCookieStore access`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:184-195`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L184) — `settings/JavaScript calls`

**Root cause:** Only iOS camera presentation is dispatched to main; it still constructs/configures UIImagePickerController before dispatch. iOS sharing and WebView settings/evaluation/cookie-store access run on the caller coroutine/thread. Public launch functions and suspend cookie API do not document/enforce UI affinity.

**Impact:** Calls from background application coroutines can violate UIKit/WebKit expectations, produce warnings/failures or missing completion. Most normal Compose click handlers are already on UI, so this is conditional rather than a failure of ordinary usage.

**Recommended solution:** Document required affinity and marshal the entire native UI operation to the proper main dispatcher where safe. For suspend APIs, use withContext(Main) around thread-confined native calls; avoid dispatching just the final present call while constructing UI off-thread.

**Risks / limits:** No mobile thread sanitizer/device run was available. Confirm each underlying native API requirement individually; do not claim all Foundation or all cookie processing must execute on main. Ensure result callbacks have a stable documented dispatcher.

**Evidence**

* Camera comment says Always present controller on main, but UIImagePickerController is constructed earlier outside dispatch.
* Share presentShareSheet calls UIActivityViewController creation/present directly without any dispatch or caller check.

**Required tests**

* Call supported public APIs from Dispatchers.Default/IO and main; observe deterministic safe dispatch/result.
* UIKit Main Thread Checker and Kotlin/Native concurrency tests.
* Cancellation before dispatch, after presentation and before callback cannot orphan work.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/326, https://github.com/MohamedRejeb/Calf/pull/508

<a id="native-034"></a>

### NATIVE-034 — Share subject is not delivered consistently and iOS assigns controller title instead of item subject

**Low · confirmed-source · effort M** · modules: `calf-share`

**Baseline locations**

* [`calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt:61-70`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt#L61) — `subject mapping`
* [`calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareContentExt.ios.kt:9-24`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareContentExt.ios.kt#L9) — `activity item conversion`
* [`calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt:96-109`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt#L96) — `web file sharing`
* [`calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt:66-80,91-96`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt#L66) — `native/fallback content conversion`

**Root cause:** iOS assigns activityViewController.title rather than supplying an activity item subject. Raw items do not implement UIActivityItemSource subjectForActivityType. Desktop drops all subject fields; web text/URL use title but file/multiple-file subject is discarded.

**Impact:** Apps relying on the advertised optional email subject do not get consistent mail/share metadata. This is a functional parity gap rather than a security defect.

**Recommended solution:** Supply native item-source subject where supported, pass file title/subject to Web Share where applicable, and document which platforms cannot honor the field. Avoid implying MIME override support on systems deriving file type from the URL.

**Risks / limits:** Email target behavior varies; UIActivityViewController title is not documented as the mail subject API. Verify actual mail/service integrations rather than assuming one native workaround works universally.

**Evidence**

* Apple UIActivityItemSource subjectForActivityType documentation identifies the supported subject hook; no item source exists here.
* Desktop tuple conversion and browser file helpers accept no subject.

**Required tests**

* iOS Mail subject for text, URL, single and multiple files.
* Web payload inspection verifies title/file fields; unsupported metadata is documented.
* Desktop native/fallback subject behavior is explicit and tested where implementable.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/pull/508, https://developer.apple.com/documentation/uikit/uiactivityitemsource/activityviewcontroller(_:subjectforactivitytype:)

<a id="native-035"></a>

### NATIVE-035 — Maps, media and notification scaffolds must not be represented as implemented features

**Low · improvement · effort L** · modules: `calf-maps`, `calf-media`, `calf-notifications`

**Baseline locations**

* [`calf-maps/build.gradle.kts:1-13`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-maps/build.gradle.kts#L1) — `empty maps module`
* [`calf-media/build.gradle.kts:1-47`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-media/build.gradle.kts#L1) — `excluded stale build script`
* [`calf-notifications/build.gradle.kts:1-47`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-notifications/build.gradle.kts#L1) — `excluded stale build script`
* [`calf-notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/notifications/Main.kt:1-26`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/notifications/Main.kt#L1) — `uncompilable notification experiment`
* [`settings.gradle.kts:28-61`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/settings.gradle.kts#L28) — `included project list`

**Root cause:** Maps is included but contains no source/API. Media has only an excluded old build script. Notifications is excluded and contains a top-level experiment with missing imports/undefined scope; both excluded scripts reference a removed androidLibrary plugin alias and old Android DSL.

**Impact:** Directory presence or stale roadmap checkboxes can imply usable functionality that does not exist. Enabling excluded modules without review will not simply produce functioning published libraries. Notification permissions are implemented in a different module and should not be confused with scheduling/delivery.

**Recommended solution:** Mark availability explicitly in docs/artifact matrices; preserve these historical stubs as such. Open scoped design/discovery work for maps, media and notification delivery with target/provider/licensing/privacy decisions before implementation.

**Risks / limits:** No requirement to implement these major new subsystems during the audit. Keep imported history; removal/reorganization needs a maintainer decision and should not turn old scaffolds into silently published artifacts.

**Evidence**

* 47-file native feature baseline inventory includes one build-only maps file and no media source.
* Notification Main.kt references scope, Dispatchers and UN symbols without definitions/imports; settings does not include media/notifications.

**Required tests**

* Source/module inventory verifies empty/excluded status and published artifacts exclude incomplete APIs.
* Future enabling requires fresh supported Gradle configuration, actual API contract, platform privacy/provider setup and device tests.
* Roadmap links maps27 and media245 without claiming they are fixed.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

**Historical / external references:** https://github.com/MohamedRejeb/Calf/issues/27, https://github.com/MohamedRejeb/Calf/issues/245

<a id="native-036"></a>

### NATIVE-036 — Desktop customUserAgent cannot be reset to its documented default using null

**Low · confirmed-source · effort S** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:162-169`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L162) — `DesktopSettings.customUserAgent`
* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:215-221`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L215) — `WebView.applySettings`

**Root cause:** The nullable setting documents null as the default user agent, but applySettings only assigns engine.userAgent inside customUserAgent?.let. After a custom value is installed, assigning null notifies settings but never restores the original value.

**Impact:** A state reused across pages/accounts continues advertising an obsolete custom user agent despite its public setting being null. Host-specific authentication/content negotiation behavior can persist unexpectedly.

**Recommended solution:** Capture the engine default user agent at creation or use a supported reset strategy and assign that value when the public setting becomes null. Document initial versus runtime semantics.

**Risks / limits:** This is a source-confirmed missing reset, not a measured JavaFX integration behavior. Changing null behavior is a corrective API change but can affect applications accidentally relying on stale headers.

**Evidence**

* DesktopSettings documentation says If null, the default user agent is used; native setter has no else branch.

**Required tests**

* Set custom A, change to B, reset null and inspect actual request User-Agent/default engine value.
* Multiple WebView instances preserve their individual defaults.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

<a id="native-037"></a>

### NATIVE-037 — Replacing WebViewState or native lifecycle callbacks at the same composable identity is not safely rebound

**Medium · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:151-162,190-215`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L151) — `state reference, client rebind and AndroidView factory`
* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:50-108,110-141`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L50) — `Unit-keyed DisposableEffect and factory captures`
* [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:63-80,111-135`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L63) — `state reference and UIKitView factory`
* [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:43-50,69-105`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L43) — `state reference and iframe factory listeners`

**Root cause:** Native view creation occurs once in interop factories/effects; effects read the native reference from the currently supplied state, but a replacement WebViewState starts with null. Factories do not rerun or transfer the native view when state changes. Several listeners/onCreated/onDispose lambdas capture the original state/navigator/callback because effects are Unit-keyed or factories are one-shot.

**Impact:** Passing a new state object to an existing WebView composition can leave the rendered old view attached while new content/navigation/evaluation has no native target. Desktop/iOS/Web listeners can keep updating the old state or navigator; callback substitution is not consistently observed.

**Recommended solution:** Either explicitly key the native view lifecycle on its state owner, with proper disposal, or implement safe rebinding/update callbacks and rememberUpdatedState for callbacks. Document one-state-per-native-view ownership and behavior of navigator replacement.

**Risks / limits:** The normal rememberWebViewState helper retains one state, so ordinary URL recomposition is not this failure. This is a source-traced edge case requiring Compose interop tests, not a claim every recomposition breaks WebView.

**Evidence**

* Android updates client.state on each composition but assigns state.webView only in factory; Desktop initialization effect is keyed Unit.
* iOS factory installs navigationDelegate=state once; browser event listeners close over initial state/navigator.

**Required tests**

* At a stable composition location replace stateA with stateB and verify content, native identity, observed state and disposal semantics.
* Replace navigator and callback lambdas without recreating the screen; only current owners receive updates.
* Rapid replacement during queued FX initialization/navigation does not resurrect stale state.

**Dependencies:** NATIVE-002, NATIVE-006

<a id="native-038"></a>

### NATIVE-038 — Android enables multiple WebView windows but supplies no window-creation handler

**Medium · confirmed-source · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:99-103`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L99) — `AndroidSettings.supportMultipleWindows default`
* [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:104-106,233-239,309-328`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L104) — `settings and AccompanistWebChromeClient`

**Root cause:** supportMultipleWindows defaults true and is applied to Android WebSettings, but the installed WebChromeClient implements only title, icon and progress callbacks. It never overrides onCreateWindow; Android defaults reject creation. The public common WebView API also does not accept a custom chrome client.

**Impact:** Pages using target=_blank or window.open can request a new window that is never displayed, even with javaScriptCanOpenWindowsAutomatically=true. Browser/payment/login flows depending on popup navigation can silently fail.

**Recommended solution:** Choose and document a safe popup policy: reject explicitly, load allowed same-view requests, or expose/manage child windows with a trusted host callback. Do not enable multiple-window support without a handler and do not automatically open untrusted external schemes.

**Risks / limits:** Source confirms the missing handler/configuration mismatch; exact Android link fallback behavior is WebView/version/content-dependent and needs device reproduction. Creating windows adds origin, lifecycle and phishing concerns; policy must be explicit.

**Evidence**

* AccompanistWebChromeClient overrides only onReceivedTitle, onReceivedIcon, onProgressChanged.
* AndroidSettings defaults supportMultipleWindows=true; native applySettings calls setSupportMultipleWindows.

**Required tests**

* target=_blank link and user-initiated/scripted window.open with JavaScript/settings combinations.
* Accepted and denied popup origins/schemes yield documented outcomes.
* Child window closure, back navigation and dispose release all resources.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

<a id="native-039"></a>

### NATIVE-039 — WebView settings changes and error accumulation perform avoidable full updates

**Low · improvement · effort M** · modules: `calf-webview`

**Baseline locations**

* [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:6-169`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L6) — `all property setters`
* [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:221-245,292-296`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L221) — `full applySettings and error snapshots`
* [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:187-221`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L187) — `applySetting/runLater`

**Root cause:** Every setter invokes a full native settings reapply even when assigning the same value; Desktop queues one FX task per setter and each task reads the whole live settings object. Android records each resource error by copying the entire accumulated list with toList().

**Impact:** Configuration batches cause redundant native/JNI/FX work; many failed resources allocate quadratically many error-list elements over a request. No benchmark demonstrates a user-visible slowdown yet, so this is an optimization candidate rather than a release-blocking defect.

**Recommended solution:** Skip equal-value notifications, batch/transaction settings changes or apply field deltas on the correct UI thread, and choose a bounded/batched immutable error reporting strategy that preserves diagnostics. Measure before and after.

**Risks / limits:** Coalescing updates may alter observable timing; mutable collections must not leak through supposedly immutable UI state. Bounded diagnostics need an explicit truncation/count indicator rather than silently discarding errors.

**Evidence**

* All setters call onSettingsChanged unconditionally. Android onReceivedError calls mutableErrorsForCurrentRequest.toList after each addition.

**Required tests**

* Assign identical settings repeatedly and apply a multi-setting batch; assert bounded native/FX calls.
* Thousands of resource failures: benchmark allocation/time and preserve required error metadata.
* Concurrent/UI-thread application still sees a coherent settings snapshot.

**Dependencies:** None required; coordinate shared APIs/lifecycle changes.

<!-- GENERATED_FINDINGS_END -->
