# Testing camera, sharing and WebView

## 2026-10-29: scoped WebView lifetime regression results

The [current development evidence](../development/evidence/webview-lifetime-important-20261029/README.md)
closes NATIVE-002/#10 after reviewing its three original criteria. Actual current
Android3/3 in40808466133/b3831693 (exit0/70.03s,831 held own-Git inputs/JDK17,
owned Enforcing API35 emulator) plus20 reused desktop executions and3 fresh host
ownership methods are accepted. Native collection while Activity remains RESUMED,
real decoded media/network/timer shutdown, retained-state repeated collection,
public Saver/Parcel restoration, throwing disposal/replacement and delayed FX
creation/multiwindow are exercised. Eight authored native methods yield23 target
executions, not23 distinct methods. Previous failed runs remain failed; no local
Android device run, Apple/physical/minimum/OS-process-death/native-allocation/
API-ABI/full-consumer/security/release certification follows. Baseline probes
below deliberately remain historical defect reproductions, not current tests.

## What was actually run

Reviewed source: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6` (2026-10-24 audit). There are **no baseline Kotlin test sources or Rust test functions in these six modules**. A Kotlin-test dependency or empty Gradle test task is not behavioral coverage. Repository-wide build attempts and limitations are recorded by the build reviewer in [testing overview](README.md) and `docs/testing/evidence/`; this reviewer did not run a competing Gradle or Cargo build.

Executed locally:

```sh
python3 docs/testing/native-features-probes/run.py
```

**Exit0** and inspected [JSON output](native-features-probes/results-baseline.json). This command asserts **known baseline defects are present**. It is a reproduction harness, **not a passing regression suite**. A correct future fix should change/remove the corresponding defect assertion and gain a real acceptance test.

Environment for these small probes: Linux, Python3.12.3, OpenJDK21.0.12, cached Kotlin compiler2.4.20, harness coroutines1.8.0, Node24.20.0, Chrome153.0.8010.36. The project dependency catalog uses a different coroutine version; no claim is made that project dependency resolution or the platform build passed. Browser tests used only ephemeral loopback HTTP pages and a disposable Chrome profile, not external pages, OS file associations, real share recipients or existing clipboard contents.

| Test body | Assertions observed | Findings |
|---|---|---|
| Exact baseline `WebViewNavigator` and Desktop command collector; Compose state/FX engine/queue doubles | After one stop command,100 queued work steps still leave1 queued; native cancel calls0 | NATIVE-001 |
| Exact `MutableSharedFlow(replay=1)` navigator | Two later subscribers each receive the single Back command | NATIVE-008 |
| Exact Desktop CookieManager class with `actual` keywords removed, real JDK store | Replaces a custom CookieHandler on read; returns `/private` cookie for `/public/`; expiry advances1201ms during1200ms wait | NATIVE-012/013/014 |
| Exact Wasm `jsCopyToClipboard` JS body; mocked rejected Promise | Caller reports Success, then unhandled rejection occurs | NATIVE-026 |
| Real Chrome cookie APIs mirroring source operations | Invalid numeric expiry retains already-expired cookie; HttpOnly assignment rejected; deleting root cookies leaves `/private` cookie | NATIVE-011 |
| Real Chrome iframe APIs mirroring source operations | Changing src does not override srcdoc; removing srcdoc first works | NATIVE-004 |
| Real Chrome JS-enabled inline iframe | Un-sandboxed srcdoc script modifies parent document attribute | NATIVE-010 risk precondition demonstration |

### Reproducing and understanding the harness

`run.py` reads source using `git show <baseline>:<path>`, so later source edits do not erase the audit evidence. It compiles copied method/class bodies rather than trusting a hand-reimplementation of Kotlin receiver resolution. The fake FX engine only supplies the **public methods actually used**; it intentionally has no stopLoading, matching [JavaFX19 API source evidence](native-features-probes/dependency-evidence.json). Browser operations are hand-mirrored small DOM sequences, clearly not generated Kotlin/JS/Wasm. Node extracts the literal Wasm JS function and mirrors the small synchronous fallback boundary.

```sh
# Each independent group, without new downloads:
python3 docs/testing/native-features-probes/run.py --only kotlin
python3 docs/testing/native-features-probes/run.py --only node
python3 docs/testing/native-features-probes/run.py --only browser

# For development: source-derived Kotlin/Node portions may be tried against edits.
# Browser tests always model baseline DOM primitives and are NOT worktree regression tests.
python3 docs/testing/native-features-probes/run.py --rev WORKTREE --only kotlin
```

Kotlin jars are located in the existing Gradle cache; absent tools/dependencies produce explicit `skipped`, not a fabricated pass. This is intentionally not a bootstrapper downloading a compiler/Rust SDK onto a space-limited host. The runner creates/removes its own temporary directory and browser profile. It does not kill unrelated processes, purge caches, invoke OS file opening, connect to upstream services, or publish anything. Chrome runs with `--no-sandbox` solely because the audit container is root; the fixture is controlled local HTML, not a browsing workload.

`results-baseline.json` preserves the successful defect reproductions, source excerpt SHA256s and limits. `dependency-evidence.json` records the JavaFX19 source artifact SHA256 and Apple API references used for call/configuration semantics. No JavaFX executable was downloaded/executed for these source probes. **Fake queue/engine tests cannot validate AppKit/UIKit/JavaFX resource cleanup or threading.**

## Required regression layers

### Common/API tests (fast, all feasible targets)

1. Introduce a testable boundary for navigation dispatch and request-state resets without rewriting architecture first. Back/forward/reload/stop are one-shot commands; initial load sent before view attachment is retained intentionally, not by replaying every old command.
2. Content Url/Data/NavigatorOnly transitions must behave consistently between state and navigator. Document unsupported parameters; do not make a browser iframe header test pass by injecting a secret-bearing proxy.
3. Define separate operational outcomes for chooser presented/service selected/share completed/fallback action/cancel/error. Exactly one terminal callback per documented operation; callback exceptions must not become a second platform failure.
4. Nullable script result versus successful JSON/string versus native error must be distinguishable. Evaluate before attach/after dispose has an explicit terminal behavior rather than a silent callback loss.
5. Camera availability/cancel/error and stable callback ownership must be additive compatibility APIs. Avoid breaking existing onResult(KmpFile) consumers just to add failure outcomes.
6. Cookie conversion tests: valid token/value encoding, domain/host-only/path/secure/expiry/SameSite limitations, metadata fidelity and no lifetime drift. An expired cookie remains expired after any roundtrip.
7. State/callback/navigator replacement at the same composition identity, save/restore and multi-view sharing must have intentional ownership rather than silently updating an old state.

These should become actual `commonTest` and platform test source sets. The audit probes under docs are not a substitute. Browser Compose tests require executable/test bundling through the shared convention helper; confirm Gradle task/source configuration with the build reviewer before adding costly targets.

### Android instrumentation / actual recipient tests

**Prerequisites:** compatible Android SDK/JDK/Gradle, emulator plus at least one real camera-capable device, test-host manifest/privacy/provider configuration, grantable output under a narrow cache path, Android System WebView versions representative of support. Use only synthetic images/content/cookies.

| Area | Required cases / acceptance |
|---|---|
| Camera lifecycle (019/020/023) | Launch external camera, enable “Don't keep activities”, rotate/recreate and separately simulate host process death while camera is foreground; result returns once with original pending URI and readable data; cancelled requests clear their own state |
| Provider/setup (022/028) | Correct/missing/wrong authority/path; API23 and24+; CAMERA declared-but-denied; camera feature but no intent handler; content URI and File.toKmpFile paths; recipient can read only intended files |
| Sharing outcome (025/032) | Dismiss chooser; select recipient then cancel; launch failure; throwing callback; late recipient stream read; no false completed-delivery claim and no duplicate callback |
| WebView lifecycle (002/003/037) | Native reference exists in onCreated; retain state while unmounting and verify WeakReference/heap cleanup; old Activity collected; queued events do not update replacement state; view destruction after save/remove |
| Navigation/popups (001/005/008/038) | Slow request stop, back/forward restoration, request errors versus subresource/HTTP/TLS; target=_blank/window.open/user gesture and origin policy; no stuck loading or silent implied support |
| Cookies (011–014 context) | Set callback false, flush behavior, repeated writes, cancellation, metadata unavailable from getCookie; actual outgoing headers with domain/path/secure rules; global clear impacts only documented stores |

Do not claim new URI grant flags are necessary without inspecting Android's TakePicture/chooser intent behavior on supported SDKs; several contracts already populate ClipData/grants. Instrument a harmless receiver app to prove readable bytes and least privilege rather than inferring from flags alone.

### iOS device/simulator and Instruments

**Prerequisites:** macOS/Xcode with actual supported SDKs; arm64 simulator for ordinary WebView/share and a **real iPhone/iPad for camera/media**, declared privacy usage strings. Linux cannot perform these checks.

| Area | Required cases / acceptance |
|---|---|
| Camera completion/ownership (020–024/033) | Original UIImage→readable file on real device; photo-library fallback on simulator/no camera; cancellation, denied authorization, callback mutation, reentrant/double launch, callback throw, navigation away and forced GC while picker active |
| Image performance (024) |12/48MP captures; measure main-thread time, peak memory, PNG output size, cache growth; disk-full failure and temp-file eviction; preserve orientation/transparency/needed metadata under any format change |
| Share sheet (025/030/033/034) | iPhone/iPad, popover source validity, present over existing modal, background-thread call, selected service cancellation/error, actual Mail subject, external security-scoped URL and file lifetime |
| WK configuration (003/009/017) | Native reference inside onCreated; gesture false remains false after all URL/settings/recomposition paths; inline video playsinline on physical iPhone using prepared config; document creation-only properties |
| WK lifecycle/KVO (002/005/007/037) | Repeated mount/unmount/state swaps; six KVO keys added/removed exactly once; native callbacks after dispose; provisional fail→success/fail reset; saveable state does not misrepresent blank content |
| Script/cookies (012/015/016/033) | Main Thread Checker; result types/errors/missing view; requested header scope, UTF8 versus caller encoding; real HTTP request cookie matching, scoped website store and cancellation |
| Historical issue34 | In-page camera input opens/closes without unexpectedly removing enclosing WKWebView; keep this distinct from calf-camera-picker. Current causal mechanism must be established before a fix. |

Use Instruments Allocations/Leaks and Main Thread Checker; retain/release sequencing needs real native runtime evidence. “Observer removal appears balanced in source” is not proof of zero leaks. Validate subject via an actual service or test item-source consumer, not the view-controller title label.

### Desktop JVM / Rust JNI

**Prerequisites:** graphical Linux/macOS/Windows hosts, documented GTK/graphics/runtime dependencies, matching JavaFX classifier libraries, and native library artifacts from a reproducible toolchain. Headless success of the Kotlin probe says nothing about QuantumRenderer. JVM version and GPU backend belong in failure evidence, without environment/credential dumps.

| Area | Required cases / acceptance |
|---|---|
| Stop command (001) | Actual JavaFX slow HTTP load stops through loadWorker.cancel, emits no command, and leaves event queue idle; cancel/remove view mid-request |
| FX initialization (018) | Cold first JFXPanel during Compose rendering, preinitialized toolkit, repeated windows, macOS Metal/AWT and Linux renderer; historical reentry346 tested on current dependencies before claiming fixed |
| View ownership (002/003/005/037) | Disposal clears scene/listeners/state, cancels load/media and stale setup runLater; callbacks always correspond to active state/navigator; remember that process-global FX lifetime is not per-view |
| Cookie ownership (012–014) | JavaFX login→getCookies preserves custom handler and session; app-installed CookieHandler not replaced; request-path filtering; fixed absolute expiry; document.cookie HttpOnly/Secure compatibility |
| Evaluation/settings (015/036/039) | Script throw/object/null/string; queued callback disposal; custom agent→null restores default; equal/batched setters generate bounded updates; error list allocation benchmark |
| Fallback safety (025/027) | Mock Desktop.open/browse; no actual unsafe file execution in tests; unsupported/native failure does not unexpectedly run content; partial multi-file failure and empty file list have explicit outcomes |
| Share cache (031) | Two JVMs/versions/architectures concurrent; verify loaded digest, no mutable-target race; Windows DLL lock, read-only/symlink cache, missing resource; system-extracted native lib path still works |
| JNI generic | Missing native library, wrong ABI/symbol/package, null/empty text/URL/file list, many Java local references, Unicode paths; report load/argument errors accurately rather than silently opening a fallback |

**macOS-only Rust acceptance:** use Instruments/leaks and preferably sanitizer-enabled native test builds to cover thousands of success/cancel/timeout cycles, balanced delegate+Arc ownership, duplicate/late callbacks, no keyWindow/contentView, off-main native invocation, selected-service success/failure, navigation away and concurrent requests. Prove picker retention while the local Retained object goes out of scope; it was not established by this audit. Do not remove mem::forget without a replacement lifetime owner. Native panic/ObjC exception cannot safely be “caught” by Java try/catch.

Proposed commands, **not recorded here as successful**:

```sh
# Discover exact task names for the installed Gradle/Kotlin/AGP combination first.
./gradlew :calf-webview:tasks --all :calf-share:tasks --all
# Standard desktop compile tasks, subject to the build review's dependency/disk blockers:
./gradlew :calf-webview:compileKotlinDesktop :calf-camera-picker:compileKotlinDesktop :calf-share:compileKotlinDesktop
# Native build/check with an approved pinned toolchain and a committed lockfile once adopted:
cargo check --manifest-path calf-share/native/Cargo.toml --locked
cargo test --manifest-path calf-share/native/Cargo.toml --locked
```

The baseline ignores Cargo.lock and has no Rust tests; `--locked` may deliberately fail on a fresh checkout until reproducibility work is done. Do not claim cargo test exercises AppKit simply because the crate compiled. The build reviewer manages actual expensive build runs; avoid duplicate downloads or deleting unrelated caches on this host.

### Browser compiled JS/Wasm integration

**Prerequisites:** serve test apps over loopback/HTTPS, generated JS and Wasm bundles, supported real browser versions and embedding policies, no existing user profile. Test both targets; common Web source does not make JS/Wasm interop identical.

* Data→Url→Data through state and navigator; cross-origin destination blocked by CSP/X-Frame-Options; same-origin and cross-origin title/history/loading status are honest.
* `onDispose` exactly once; iframe reference/listeners released; callbacks after removal/state swap cannot mutate old or new unrelated screen.
* JavaScript/sandbox policy before load and during mutation. Untrusted srcdoc cannot access parent storage/DOM in isolation mode; do not use allow-scripts+allow-same-origin as false isolation for same-origin content.
* navigator.share supported/absent, file support via canShare, invalid data, busy share, user AbortError, permission NotAllowedError, embedder permissions policy and lost transient activation. Assert exact outcome count.
* Clipboard resolved/rejected/missing API/denied permission, without reading unrelated clipboard contents; result follows promise settlement.
* Server-set HttpOnly cookie and path/domain/secure/session/expiry scenarios. Client API must report unsupported operations truthfully; complete HttpOnly/logout may require server actions.
* Script return values under JS and Wasm, CSP eval restrictions, absent iframe, callback throw and cross-origin access; distinguish error from successful null.

## Coverage-to-finding mapping

Each of the39 records in [`NATIVE.json`](../audit/findings/NATIVE.json) contains its own required_tests array and dependencies. Use those as issue acceptance criteria; the platform matrices above supply fixture/host requirements. Detailed symbol coverage is in [module documentation](../modules/native-features.md#6-complete-filesymbol-review-coverage), not inferred from passing a grep or a missing test task.

**Minimum next release gate after fixes:** actual compilation and smoke tests on all published target families; Android external-camera recreation and URI receiver tests; iPhone/iPad WK/picker/share tests; macOS JNI ownership/cancellation tests; JavaFX GUI tests across supported OS classifiers; compiled JS+Wasm tests; reproducible native/dependency verification. No release/package publication is authorized by this checklist.
