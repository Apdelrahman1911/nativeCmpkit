# Important WebView native lifetime checks — 2026-10-29

**NATIVE-002 / [#10](https://github.com/Apdelrahman1911/nativeCmpkit/issues/10)
is CLOSED/completed**, after reviewing all three original criteria, source and
actual results, before this documentation update. Original body/title/labels
remain intact; one additive comment and one state-only PATCH were read back.
See [acceptance](android020/closure/acceptance.json) and
[verified closure](android020/closure/verified-readback.json).

Current immutable repair `b3831693d968d6cd8ef80ba2729a000cca0374a6` passes
[40808466133](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40808466133):
**3/3 actual Android methods**, one fresh XML, zero failures/errors/skips,
Gradle exit0/70.03s, 831 own-Git inputs held, JDK17 and a cleanly stopped owned
API35/x64 SELinux-Enforcing emulator. APK assembly exits0/289.08s; no APK is
distributed. All three Android methods reran because native production ownership
changed. [Current review](android020/lead-target-source-results-review.json).

Twenty accepted unchanged desktop executions are reused: Linux x64, Windows x64,
macOS arm64 each5/5 in the original failed matrix; Intel macOS four original
positives plus one repaired media recovery. **23 accepted native target executions
of eight authored native methods**, not one fresh green five-host matrix.
Three new [host ownership regressions](android019-container-host/important-result-review.json)
also pass exit0/56.01s/831 held own-Git inputs; public Android state JVM descriptors
are unchanged. Together26 accepted executions, not26 distinct authored methods.
Zero local Android device executions. No packages, releases, Pages or deployment
are authorized by these tests; independent release/security gates remain.

## Owning defect and scoped repair

Actual desktop heap-root analysis found a disposed native view retained through
`WebViewState.webView`'s **predecessor Compose snapshot record**, even after the
current value was null and the `DesktopWebViewOwner` itself had collected. Both
Android and desktop now store only the current live native handle in a private
`AtomicReference`; an observable primitive attachment version preserves Compose
notifications. The current native handle is intentionally not historical MVCC
state. Desktop owner publication is volatile. Public `WebViewState` JVM
signatures/descriptors match the pre-fix Android and desktop classes exactly;
this is not whole-library ABI certification.

The independent Swing `RepaintManager.paintManager.rootJ` window retention was
also identified. Its cache is not modified. Native-view/engine weak-reference
requirements remain, including collection while the real host and observing
composition remain alive. [Reviewed root paths](owning-heap-root-review.json)
exclude raw heap objects, addresses and private diagnostic payloads. Similar iOS
WKWebView snapshot storage merits separate native review; no Apple lifetime result
is implied by this Android/Desktop finding.

## Executed local results, including failures

[The summary](local-reviewed-summary.json) retains every failed Gradle diagnostic.
Initial desktop001/002 fail 3/3; after the storage repair desktop003 passes 2/3.
Actual media then exposed absent ALSA output. An unclocked ALSA null adapter did
not satisfy the real playback timing test: those failures remain failures.

- **host006 overall FAILED**, even though eight owning Android-host lifecycle
  methods and Android device test compilation pass; its media method fails.
- **desktop007 actual media 1/1**, one fresh XML, exit 0 / 33.01 s / 826 held
  inputs, using an authenticated, clocked, owned PulseAudio software output.
- **local008 final changed fixtures 2/2**, one fresh XML, exit 0 / 85.02 s / 828
  held inputs and JDK17. Real Compose/JavaFX windows, decoded/playing authored WAV,
  real pending HTTP connection, timers/network cancellation, native collection,
  throwing callback and a second real engine are exercised. The unchanged earlier
  native collection success is not replayed locally.
- `:calf-webview:assembleAndroidDeviceTest` also passes in local008. The real APK's
  manifest/resource inspection confirms the same target/test package, a
  **nonexported owned Activity**, global cleartext false, and only the exact
  `127.0.0.1` test exemption. Existing AndroidX instrumentation components remain;
  this is not a claim that the whole test APK has no exported components.
  Production networking is unchanged. **Zero Android device tests run locally.**
- Initial synthetic tooling: 146 methods / 145 passes / one error. Its missing
  source rejection now passes in a one-method recovery, without replaying 145
  successes. Eight changed owned-audio lifecycle/security guards and two final
  source checks pass separately; their counts overlap and are not native tests.

## Focus and limitations

`webview-lifetime` requests five exact desktop methods on Linux x64, macOS
arm64/x64 and Windows x64, plus one lossless Android class containing three exact
methods on an owned SELinux-enforcing API35 emulator: **23 target-method
executions**, not 23 authored functions. Failure-only host profiles avoid repeating
successful hosts. Original full stop/history gates remain and now also require
all new lifetime cases.

Linux's authenticated owned PulseAudio sink substitutes only inaudible hardware
output, not WebKit/GStreamer, decoder, media clock or callbacks. Readiness,
configuration integrity, early exits, signal races and clean owned shutdown must
pass. No audible/physical-output claim. Cookie/configuration/raw audio logs and
heap/parser binaries are local-only and never uploaded. CI artifacts contain
reviewed JSON receipts and test XML, not APKs or native packages.

The Android saver test performs the real public Saver + Parcel round trip and a
new real Activity; **it is not OS process death**. Throwing release is exercised at
the real owning native boundary, not by hiding Compose/Main uncaught exceptions.
The media test unmounts composition while its Activity stays RESUMED, so Activity
pause/finish cannot supply cleanup. Physical/minimum-API, Apple WKWebView,
profiling/sanitizer, complete consumer/API-ABI, dependency/provenance/legal/security
and release gates remain independent.

## Reviewed first immutable matrix and bounded recovery

[40800212182](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40800212182)
is **FAILED**, not a green23-test gate. The independent
[completed review](native001/lead-completed-source-results-review.json) verifies
all828 selected inputs against own Git objects, before/after equality, actual
JDK17 setup/daemons, exact finite commands, API ZIP hashes and real XML counts:
**23 executions,19pass/4fail**. Linux x64, Windows x64 and macOS arm64 each pass
5/5; Intel macOS passes4/5 and Android fails all3. Successful unchanged tests are
preserved, not replayed.

Android actually plays the WAV and cancels the slow connection/timers before the
media method fails native collection. Repeated Activity/native collection fails
before saver restoration. The two-owner method fails before native release:
test-core1.7.0's actual invoker adds NEW_TASK|CLEAR_TASK and destroys the previous
same-affinity task. The fixture now adds MULTIPLE_TASK and verifies distinct live
task IDs. Queue-backed witnesses avoid dereferencing targets in a GC loop, separate
Activity/native lists and calibrate a still-live replacement. **The previous
collection failure's root is not yet proven**, so this is not declared a fixture-
only failure or closed library defect. Held Android009 assembly exits0/35.01s/828
inputs and one source guard passes; zero local device methods.
[40803226346](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40803226346)
at `b443da53fa5e8cf06110fb9b7eb734f18c42b35a` requests only the failed Android class.

Intel macOS's native title proves playback occurred at some point, but the
required current playback/five heartbeats conjunction times out (time0,beats4
at final observation). No missing sound device or native-provider cause is
established. A bounded actual-media timeline and on-screen-host assertion retain
the original playback/cancellation requirements; a new finite one-method focus
avoids replaying four successful Intel methods. Compilation exits0/32.01s/828
held inputs;42 focused synthetic tooling methods pass, not native tests.
[40803663234](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40803663234)
at `7f93116419beb61896b368f2907d015d730d2123` fails **before Gradle**, because the
CLI omitted the planner's new focus: zero library methods/XML. Its empty plan JSON
is explicitly rejected in the [failure review](macos012/failed-before-runtime-review.json),
not substituted with fabricated evidence. Exact CLI choice repair `36917fc2`
passes one new real-CLI regression plus positive planning;42 unchanged methods
are not rerun locally. The recovery requests only that one media method.

## Accepted recovery results; one Android failure still open

The [Android-only review](android010/lead-target-source-results-review.json) for
[40803226346](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40803226346)
at `b443da53fa5e8cf06110fb9b7eb734f18c42b35a` is **FAILED overall: 2/3 pass**,
one fresh XML, Gradle exit 1 / 99.05 s, all 828 selected inputs equal own Git and
held. Repeated genuine Activity/native-view collection, the public Saver/Parcel
round trip and throwing release/live replacement pass. Composition-only media
unmount still leaves the native WebView uncollected while its Activity stays
RESUMED, despite passing playback, real slow-connection cancellation and stopped
timer/network assertions. Clean unforced owned emulator shutdown is verified.
These two passed methods may be reused; the failed method is not accepted.

The [Intel macOS review](macos014/lead-target-source-results-review.json) for
[40804208284](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40804208284)
at `36917fc2f41526e919b72c7960e5495e6759e974` passes **1/1**, one fresh XML,
Gradle exit 0 / 443.29 s, all 828 own-Git inputs held and JDK17. Genuine native
media decoding/clock, actual on-screen host, unchanged authored WAV and original
predicate, slow-connection cancellation and collection pass. The four unchanged
successful Intel methods are not replayed. No missing-audio/provider cause is
established for the original failed conjunction.

Together **22 of the required 23 scoped target executions have accepted passing
results**, not 22 distinct authored methods or a passing whole original matrix.
Current production bytes for common/Android/desktop WebView, its build and shared
toolchain are unchanged from `5923d651`; later changes are scoped fixture/finite
selection repairs. `20048c55` additionally gives each ActivityScenario a unique
Intent action/exact fixture-owner check. Bytecode confirms action/data/type
matching rather than extras; this is isolation hardening, not a demonstrated
cause of the remaining media failure.

## Failure-only Android root diagnostic

Commit `1735ab8c6775b6243bc567fec76efa58023605d6` and
[40806868678](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40806868678)
requested **only the failed media method**, not the two accepted Android cases or
any successful desktop host. It remains **FAILED:0/1**, Gradle exit1/77.03s,
831 own-Git inputs held. The actual private ART conversion/parser succeeds and
identifies a strong owning root; profiler GC never reclassifies its failed test.

- On collection failure only, retain the original AssertionError and dump only
  the owned test process into private app cache. Atomic completion marker,
  exact app/path/size/hash, live name-verified owned API35 AVD and clean monitor/
  emulator shutdown are required. Never reclassify a failed assertion after the
  dump's additional GC.
- Raw/converted heaps, parser jars/classes and parser caches stay in the private
  runner build directory and are **never uploaded or committed**. The official
  Android converter and exact VisualVM2.2 registry-observed parser bytes are used;
  that hash is observed-byte integrity, not independent trust or release clearance.
  Only bounded class/field/root-kind identities may appear in public receipts;
  nearest paths are not all strong roots or native-allocation evidence.
- [Local synthetic tooling](android016-heap-tooling/) passes 58 methods. The
  expanded size/hash/redirect/capacity guard separately passes one **overlapping**
  method, not a 59th distinct test. Actual Java17 profiler compilation and earlier
  desktop-heap calibration pass, but find zero Android targets: **not ART
  conversion, Android roots or native tests**.
- [APK compilation](android017-failure-heap-compile/compile-outcome.json) exits
  0 / 37.01 s with 831 held inputs and a fresh APK, one source guard pass,
  **zero local Android device executions**.
- Source review finds structured `consumeNavigationEvents`/cancellation-finally,
  not a launch in the longer-lived navigator scope. The unstructured-collector
  hypothesis is not established; real heap evidence must identify the owner.

No issue was closed by those failed/pending results. The lead's rejected
nonexistent-ref dispatch argument is preserved as a lead selection error
(HTTP422, no run), not a library or successful CI result.

## Second owning root and current Android repair

The [actual ART root review](android018-private-root-diagnostic/lead-heap-owning-root-review.json)
shows an expected-to-live Compose/accessibility owner retaining cached LayoutNode
vectors, then `interopViewFactoryHolder`, `ViewFactoryHolder.typedView` /
`AndroidViewHolder.view`, then the destroyed native WebView. The still-RESUMED
Activity is expected to live; this is not an Activity leak or every possible heap
root. Raw heaps/parser payloads remain private and absent from these archives.

`AndroidView` now owns only a private `AndroidWebViewContainer : FrameLayout`.
Release severs its nullable native owner and actual child independently, even
after exceptions; failed creation unwinds once. State, settings, callbacks and
JavaScript still expose/address the original or custom native WebView. Native
save/stop/client-detach/destroy and matching-state-clear contracts remain.
No Compose cache reflection, accessibility disabling or relaxed collection.
See [ADR0010](../../../decisions/0010-detachable-android-webview-owner.md).

Current Android3/3 proves repeated real Activity/native collection with retained
state, public Saver/Parcel/native-history restoration in a new Activity, real
media/slow-request/timer shutdown, native collection after composition-only
unmount while its Activity remains RESUMED, actual filled child bounds and
throwing release leaving a distinct live replacement untouched. Desktop evidence
additionally covers delayed actual FX creation and multiwindow cleanup. This
satisfies the three original scoped criteria, not OS process death, physical/
minimum devices, Apple WKWebView, accessibility/IME/custom native animations,
sustained native allocation/sanitizer, whole API/ABI/consumer, dependency/
provenance/legal/security or release gates. All prior failed evidence remains.
