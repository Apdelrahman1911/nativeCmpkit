# Geolocation correctness work — PERM-018 through PERM-023

Current [direct acceptance](checkpoint-direct-closures-20261027.md): PERM-018/#24
and PERM-022/#117 are verified/closed against both original criteria each.
Immutable Android-host40414284598 passes88/88 geo executions/five fresh XML;
current geo/test/dependencies unchanged except two exact display strings. Real
LocationResult/measurement flags/Composition/Recomposer with injected GMS transport,
not physical/GPS/rendered UI. Other geo/device/provider/consumer/ABI/security/release
gates remain; older partial/failed observations below retain their own dates.

This is a **current-source implementation and regression record**, not a rewrite
of the frozen baseline findings or their defect-reproducing probes. Baseline:
`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. Work began only after the lead verified
the current-open-upstream synchronization on 2026-10-24 at 18:43:24Z.

Scope: `calf-geo` only. No source/package rename, publishing plugin, new native
backend, sample substitution, GitHub mutation, or permission prompt was added.
The module remains unpublished. Shared Gradle/dependency edits are integrated by
the build owner, not this area reviewer.

## Contract and compatibility

The original data-class constructors, `LocationTracker` property signatures,
`suspend startTracking(): Unit`, `stopTracking(): Unit`, Android `(interval,
priority)` constructor and three-argument `bind` signature remain. The unused
`FragmentManager` overload is deprecated and forwards to a two-argument overload.
Android still extends `LocationCallback`; the library now registers a fresh
callback for each subscription, never the shared tracker callback identity.

Additive public APIs:

- `createLocationTracker()` is callable from common code. Android starts unbound
  and still requires platform lifecycle/context binding. Other targets explicitly
  declare `LocationTrackingCapability.Unsupported`.
- `snapshotState: State<LocationTrackingSnapshot>` is the single source of truth:
  phase, nullable fix, observed permission granularity, transient native provider
  availability, current error, and removal/cleanup error. A `Tracking` phase means
  registration succeeded, not that a fix exists or is fresh.
- `fixState: State<LocationFix?>` is a derived view. Individual measurements and
  each accuracy field are independently nullable, including an accuracy flag set
  without its associated measurement flag.
- `startTrackingWithResult()` awaits native registration and returns `Started`,
  `AlreadyStarted`, `InProgress`, `Cancelled`, `Unsupported`, or a typed failure.
  Coroutine cancellation cancels **that request's** ownership; it cannot cancel
  a new owner/session after rebinding. External stop/rebind completes a pending
  start with `Cancelled` rather than leaving its caller suspended.
- `close()` removes ownership and is terminal; Android `unbind()` permits a later
  explicit rebind. Repeated stop/close can explicitly retry a failed removal;
  there is no automatic unbounded retry loop.

Intentional observable corrections, despite preserving signatures:

1. The legacy non-null location views no longer fabricate `(0,0)` or perfect-zero
   measurements before a fix. Missing coordinates/numeric measurements use
   documented **NaN** compatibility sentinels; absent legacy timestamp is `0` and
   nullable accuracy remains null. New code should use the nullable fix API. An
   actual supplied `(0,0)` or zero speed/altitude/course is preserved as real zero.
2. Android bind/stop/close/unbind are explicitly main-thread operations and reject
   an incorrect thread. Suspending start supports any coroutine dispatcher and
   moves registration to `Dispatchers.Main.immediate` with an explicit main Looper.
3. Only an owner currently at least `STARTED` may start foreground updates. An
   inactive owner reports `OwnerInactive`; rebinding an active tracker to an
   inactive owner removes the old subscription and **does not** auto-start a new
   one. `ON_STOP` stops delivery; returning to foreground requires an explicit
   start. `ON_DESTROY` detaches the observer and unbinds. No background tracking
   service or background-permission escalation is implied.
4. `LatLng` constructor/equality/copy remain unchecked and unchanged. New factories
   opt into validation or longitude normalization. Distance returns NaN for
   invalid inputs (nullable counterpart available); legacy bearing now returns
   NaN for invalid/non-unique bearings, rather than an arbitrary apparent course.
   Its existing default 10-degree rounding is retained.

## Android execution and ownership

```text
bind(active owner, application context)
  detach old observer; install new owner identity
  controller.bind(new backend, restartAllowed = owner >= STARTED)
  invalidate/remove old subscription; restart only if previously requested AND allowed

startTrackingWithResult [any coroutine dispatcher]
  -> Main.immediate -> validate bound owner is STARTED/RESUMED
  -> check coarse OR fine grant (never request permissions)
  -> create subscription; publish Starting with fix=null
  -> recheck permission immediately before native request
  -> requestLocationUpdates(request, per-session callback, main Looper)
  -> observe Task on explicit main executor
      failure/security/cancel -> typed error, rollback, cleanup
      success -> recheck permission -> Tracking; resume Started

LocationResult callback [main]
  empty lastLocation -> no fabricated fix
  invalid coordinates -> fail/cleanup
  native has* flags -> nullable measurements, original clocks/mock metadata
  active-generation + current permission check + nondecreasing-clock check
  -> ONE snapshot update -> derived simple/extended/fix views

stop/cancel/rebind/owner destruction
  invalidate current callback identity BEFORE provider removal or caller completion
  remove the exact old callback; observe completion/error
  if registration was pending: remove promptly AND once after registration terminates
  ignore stale position/availability/registration events
```

`LocationTrackingController.kt` is the main-confined production state machine.
`AndroidLocationTrackingBackend.kt` owns GMS integration; its narrow injectable
client boundary returns real Google `Task<Void>` values. There are no private
unconsumed channels or permanent, unowned coroutine scopes. Native callbacks are
cleared when stopping; the default backend retains application context rather
than the supplied Activity/FragmentManager.

An old removal failure is recorded as `cleanupError` without stopping a different
current owner. A stopped subscription with a failed removal is retained only for
an explicit cleanup retry. Closing suppresses subsequent observable callbacks;
it still attempts native cleanup. A provider that rejects/hangs removal cannot be
made to release its underlying OS resource by Kotlin state changes alone. Such a
failure is not reported as successful cleanup.

## Measurements, freshness and math

- Coordinates: finite degrees, latitude `[-90,90]`, longitude `[-180,180]`.
- Horizontal/vertical uncertainty and altitude: meters. Android altitude refers
  to the WGS84 reference ellipsoid, not necessarily mean sea level.
- Speed and uncertainty: m/s. Course and uncertainty: degrees clockwise from true
  north, **not device compass heading**. Uncertainty retains Android's native
  meaning, not an invented confidence guarantee.
- Every `hasAccuracy/hasSpeed/hasBearing/hasAltitude` flag is checked. Each API26+
  accuracy getter is guarded by both the SDK boundary and its own `has*Accuracy`
  flag. Nonfinite/negative uncertainty is absent, never substituted with zero.
- Positive native epoch milliseconds and monotonic elapsed-realtime nanoseconds
  are kept independently; zero/unset clocks remain null. No current time is
  invented. The mock-provider flag is retained with the API31 compatibility guard.
- Older fixes within a subscription are ignored using monotonic time when both
  fixes have it, otherwise epoch time when both have it. Identical fixes do not
  trigger extra structural-state updates. No arbitrary maximum age, precision,
  cached-fix exclusion, or mock rejection policy is imposed; callers must choose
  those policies. A new start/rebind clears the previous fix; stop retains the
  last accepted fix under a non-tracking phase.
- `distanceTo` is a spherical great-circle approximation in **kilometers**, radius
  6371 km, not geodesic-grade ellipsoidal distance. Haversine input is clamped to
  `[0,1]`; identical poles and dateline-equivalent points are handled explicitly.
- `validated` rejects out-of-domain input; `normalized` only wraps finite longitude
  into `[-180,180)` and requires an already-valid latitude. It does not silently
  fold a latitude across a pole. Tiny longitude deltas are not destroyed by adding
  a large normalization constant.
- `initialBearingToOrNull` returns null for coincident points, exact antipodes,
  invalid coordinates, or a start exactly at a pole. Near-antipodal courses can
  remain numerically ill-conditioned. Valid unrounded results are `[0,360)`;
  rounded results are `0,10,...,350`, never 360.

## Regression sources and evidence boundary

| Source | Actual code exercised | Deliberate test boundary |
|---|---|---|
| `calf-geo/src/commonTest/.../LocationTrackingControllerTest.kt` | Production state machine, real Compose snapshots/derived-state observation, cancellation, ownership, removal failures, permissions, stale fixes | Injected provider events; not Android/GMS/device execution |
| `calf-geo/src/commonTest/.../LatLngTest.kt` | Current production coordinate math/factories, 500 seeded symmetry/bounds cases | Spherical model, not GPS accuracy or a benchmark |
| `calf-geo/src/nonAndroidTest/.../UnsupportedLocationTrackerTest.kt` | Actual desktop/iOS/JS/Wasm tracker and common factory on each executed target | Does not implement or test a native location backend |
| `calf-geo/src/androidHostTest/.../AndroidLocationFixTest.kt` | Real Android `Location` via Robolectric; API23/26/34 flag semantics, units, clocks, mock flag | Host simulation, not GPS hardware |
| `calf-geo/src/androidHostTest/.../AndroidLocationSubscriptionTest.kt` | Actual adapter, real GMS Tasks/LocationResult/callbacks/main Looper; late registration/removal race, cancellation, security/API errors | Injected provider transport, not installed Play Services |
| `calf-geo/src/androidHostTest/.../AndroidLocationTrackerTest.kt` | Actual Android wrapper, real LifecycleRegistry/main Looper, lifecycle gating, coroutine dispatch, end-to-end native LocationResult→public states; added real Compose-runtime composition/recomposition | Provider injection; Compose test uses a deterministic frame clock and SideEffect-only composition, no rendered UI or physical lifecycle/permission dialog test |

No test compiles fake Android/iOS platform classes, extracts baseline declarations,
or calls a substituted sample API. The original frozen audit probe is unchanged;
its earlier PASS assertions sometimes demonstrated defects and are not used as
the regression oracle for these fixes.

### Reproduction commands and pending targets

```sh
./gradlew :calf-geo:desktopTest :calf-geo:testAndroidHostTest \
  --max-workers=2 --no-configuration-cache
./gradlew :calf-geo:jsBrowserTest :calf-geo:wasmJsBrowserTest \
  --max-workers=2 --no-configuration-cache
# macOS/Xcode host only:
./gradlew :calf-geo:iosSimulatorArm64Test --max-workers=2 --no-configuration-cache
```

The build owner coordinates execution. The desktop and Android-host tasks have
run in the separately recorded multi-module commands below; the combined example
above was not itself executed. Browser and Apple target execution remain pending.
Only inspected command/exit/report counts are recorded below and in
`docs/development/resolutions/PERM-geo.json`.

All six resolutions are **partially-verified**: the scoped passing tests below do
not establish all original required native/device/target checks or an immutable
release revision. This status is not an instruction to close their GitHub issues.

### Inspected diagnostic: 2026-10-24 19:13 UTC

The lead's second selected-library desktop diagnostic compiled geo desktop
production sources, then failed `:calf-geo:compileTestKotlinDesktop` on three
`assertEquals` expected-list generic-inference errors. **Zero geo tests executed**;
this is not a passing geo suite. The combined command exited 1, and the captured
input hashes were unchanged during that run. Its full command, log and summary:

- `docs/development/evidence/gradle/second-library-desktop.log.result.json`
- `docs/development/evidence/gradle/second-library-desktop.log`
- `docs/development/evidence/gradle/second-library-desktop.summary.json`

The three common assertions now explicitly use `listOf<LocationStartResult>`;
equivalent nullable-list assertions in the Android Task tests were also made
explicit. Production source was not changed for this correction. Source/tests
were refrozen for the lead's rerun, whose measured result is recorded separately
below. The later success does not erase this failed diagnostic.

### Verified Android-host scope: 2026-10-24 19:17–19:20 UTC

The lead ran `:calf-geo:testAndroidHostTest --rerun` as part of a coordinated
multi-module command. Geo production and host tests compiled; **86 geo test-case
executions passed in five XML reports, zero failures/errors/skips**. The combined
command exited 1 because other selected modules failed; this is **not** a claim
that the whole command/repository passed. All 173 selected captured input hashes
were unchanged during the run.

| Geo XML suite | Executions |
|---|---:|
| `AndroidLocationFixTest` | 22 (seven methods on API23/26/34 plus one API34 mock-flag method) |
| `AndroidLocationSubscriptionTest` | 14 |
| `AndroidLocationTrackerTest` | 14 |
| `LocationTrackingControllerTest` | 25 |
| `LatLngTest` | 11 |
| **Total** | **86** |

The report counts, individual `<testcase>` elements and absence of failure/error/
skipped nodes were inspected, and all five SHA256 values matched the lead's
summary. The earlier 83-case planning estimate preceded three additional
regressions; it is superseded by these measured XML counts, not counted as another
execution.

Receipts (full command, target log, summary and per-report hashes):

- `docs/development/evidence/gradle/first-android-host.log.result.json`
- `docs/development/evidence/gradle/first-android-host.log`
- `docs/development/evidence/gradle/first-android-host.summary.json`
- XML directory:
  `docs/development/evidence/gradle/first-android-host/reports/calf-geo/build/test-results/testAndroidHostTest/`

This verifies the described Android-host/Robolectric/current-controller behaviors,
including the actual wrapper's lifecycle gate, injected native transport Task
races, native Location metadata mapping, and LocationResult-to-public-state path.
It does **not** verify a physical location provider, installed/live Play Services,
device permissions/settings, Android process restoration, iOS, or browser runtime.
Desktop and its nonAndroid actual have the separate execution record below.

### Verified desktop scope: 2026-10-24 19:22–19:23 UTC

The lead ran `:calf-geo:desktopTest --rerun` in the third coordinated desktop
command under Xvfb. **38 geo test-case executions passed in three XML reports,
zero failures/errors/skips**. `compileTestKotlinDesktop` and `desktopTest` actually
executed; the production compilation task was `UP-TO-DATE` from the earlier
successful compilation. Test-task execution is not inferred from a cached report
or `NO-SOURCE`. The combined command exited 1 because a UI test failed, not a geo
test. The lead's receipt records all 183 selected input hashes unchanged during
the command.

| Geo XML suite | Executions |
|---|---:|
| `LocationTrackingControllerTest` | 25 |
| `LatLngTest` | 11 |
| `UnsupportedLocationTrackerTest` (desktop actual) | 2 |
| **Total** | **38** |

All three report SHA256 values, individual `<testcase>` counts and absence of
failure/error/skipped nodes were independently inspected against the summary.
This verifies current common-controller/math behavior on the desktop JVM and the
desktop actual's explicit unsupported/no-fix contract. It does not turn desktop
into a working native location provider or establish Apple/browser behavior.

Receipts:

- `docs/development/evidence/gradle/third-desktop-ui-nav-geo-icons.log.result.json`
- `docs/development/evidence/gradle/third-desktop-ui-nav-geo-icons.log`
- `docs/development/evidence/gradle/third-desktop-ui-nav-geo-icons.inputs.json`
- `docs/development/evidence/gradle/third-desktop-ui-nav-geo-icons.summary.json`
- XML directory:
  `docs/development/evidence/gradle/third-desktop-ui-nav-geo-icons/reports/calf-geo/build/test-results/desktopTest/`

The recorded source base was `94d2492e99d5cbc060409d94d9f88febd06222d5` with
uncommitted held diagnostic changes, **not an immutable release revision**.
Across those first successful Android-host and desktop runs, **86 + 38 = 124 target/host
executions** at that checkpoint. Common tests execute on both targets and Robolectric repeats seven
native-mapping methods on three API levels; 124 is neither a unique-test count nor
a physical-device test count. No failed compilation was counted as test execution.

### Added Android regressions after the first held diagnostic runs

The lead granted an Android-test-only edit window; geo production, common and
browser sources remained unchanged. `AndroidLocationTrackerTest` now has 16
methods, versus the 14 that actually executed in the first Android-host receipt:

- The existing `realLocationResultFlowsThroughNativeAdapterIntoBothPublicStates`
  now also delivers a second actual native callback containing a multi-fix batch,
  verifies the latest fix/measurements in both views, and rejects identical, empty,
  older and post-stop native callbacks.
- New `nativeFixesRecomposeBothPublicViewsWithoutDuplicateOrDisposedDelivery`
  runs a real `Composition`/`Recomposer`, observes both public views in committed
  `SideEffect`s across actual native callback deliveries, verifies no no-fix or
  duplicate recomposition, and proves a disposed composition stops observing
  while the tracker can still update. Its empty UI applier does not substitute
  for Compose state/runtime; it explicitly creates no visual nodes. Robolectric
  and a controlled `BroadcastFrameClock` are not device UI/rendering proof.
- New `destroyedOwnerCanBeReplacedAndExplicitlyRestartedWithANewNativeSubscription`
  drives actual LifecycleRegistry destruction, a new owner/bind/explicit start,
  two real native adapter subscriptions, and late old-provider cleanup/callbacks
  without cross-owner mutation. It makes no forced-GC or physical leak claim.

These additions were unexecuted at the source handoff; the next run below executed
88 cases, including one failure. The previous **86** measured Android-host cases
remain historical evidence and are not silently replaced with a larger pass count.

### Android rerun: 2026-10-24 19:47–19:48 UTC — 87 passed, 1 failed

The lead's `first-native-and-third-android-host` command compiled and executed
**88 geo cases in five XML reports: 87 passed, one failed, zero errors/skips**.
The full multi-module command exited 1. All 207 selected inputs were unchanged
during the run; all five geo XML hashes and testcase counts were independently
checked against its summary. The extended consecutive native/batched-result test
and new destroy→rebind test passed. The new Compose-runtime test failed at its
**initial** observation count, before starting the tracker or delivering any fix:
`expected:<1> but was:<2>` at then-current test line 152.

This exposed a **test harness startup ordering problem**, not evidence that native
fixes are duplicated. The actual `androidx.compose.runtime:runtime-android:1.12.1`
dependency's `Recomposer$recompositionRunner$2` bytecode registers its apply
observer and then invokes `ControlledComposition.invalidateAll()` on known
compositions when the runner starts. The test queued that runner, immediately
called `setContent`, then first ran the scheduler; both initial composition and
runner startup invalidation therefore committed the same initial content.

Read-only dependency inspection used `javap -p -c` on the AAR's `classes.jar`;
AAR SHA256: `1701a61d06d2f6144f2cd8b015abbc5ad6952eacb70c24c208cdfd2bb188dde7`.
In `recompositionRunner$2`, bytecode offset 74 registers the apply observer and
offset 150 invokes `invalidateAll` while traversing known compositions. This is
dependency inspection, not an additional test or an assertion about device UI.

The **test-only** correction sends prior apply notifications and runs the queued
runner **before `setContent`**. No production code or exact observation-count
assertion changed: initial=1, registration-only=1, first fix=2, duplicate fix=2,
second fix=3, disposed=3. At that checkpoint the corrected test was refrozen for
a coordinated rerun; its downstream assertions had not yet executed. The later
88/88 record below establishes their bounded host result. No prior failure was
removed or converted into an expected pass.

Receipts:

- `docs/development/evidence/gradle/first-native-and-third-android-host.log.result.json`
- `docs/development/evidence/gradle/first-native-and-third-android-host.log`
- `docs/development/evidence/gradle/first-native-and-third-android-host.inputs.json`
- `docs/development/evidence/gradle/first-native-and-third-android-host.summary.json`
- XML directory:
  `docs/development/evidence/gradle/first-native-and-third-android-host/reports/calf-geo/build/test-results/testAndroidHostTest/`

### Corrected Android rerun: 2026-10-24 20:11–20:14 UTC — 88 passed

The lead's `fourth-ui-ios-and-android-nav` command executed
`:calf-geo:compileAndroidMain`, `:calf-geo:compileAndroidHostTest` and
`:calf-geo:testAndroidHostTest --rerun`. **88 actual geo test-case executions in
five fresh XML reports passed, with zero failures/errors/skips**. The test task
was executed, not `UP-TO-DATE`, `FROM-CACHE` or `NO-SOURCE`; resource tasks with
those outcomes are not counted as tests. The full multi-module command still
exited **1** because the picker host suite failed its inconclusive-identity
fixture case. This is a scoped geo pass, not a whole-command pass.

| Geo XML suite | Executions |
|---|---:|
| `AndroidLocationFixTest` (API23/26/34 mapping) | 22 |
| `AndroidLocationSubscriptionTest` | 14 |
| `AndroidLocationTrackerTest` | 16 |
| `LocationTrackingControllerTest` | 25 |
| `LatLngTest` | 11 |
| **Total** | **88** |

The corrected
`nativeFixesRecomposeBothPublicViewsWithoutDuplicateOrDisposedDelivery` case
now passed all its unchanged exact committed-observation assertions:
initial=1, registration-only=1, first fix=2, duplicate fix=2, second fix=3,
disposed=3. It uses actual Compose `Composition`/`Recomposer`/`SideEffect` with
a controlled frame clock and no visual nodes. This verifies the stated
snapshot/recomposition/disposal contract on the host, **not Android rendering,
physical location delivery or UI behavior on a device**. The consecutive/batched
native `LocationResult` test and destroy→new-owner/rebind test also passed again.

The log SHA256 and all five report hashes/testcase nodes were independently
checked. XML timestamps are 20:13:51–20:13:59 UTC within the recorded command.
The lead's post-run receipt records all **366 selected input hashes unchanged**;
this reviewer additionally matched all **20 captured geo input files** to the
held receipt. The tracker test has the already-refrozen test-only startup-order
correction SHA256
`e47c9d2784ed6c7e9e381d90d92b0ffe1d18c09db7c410dbe09de4797371e8ba`.

Receipts:

- `docs/development/evidence/gradle/fourth-ui-ios-and-android-nav.log.result.json`
- `docs/development/evidence/gradle/fourth-ui-ios-and-android-nav.log`
- `docs/development/evidence/gradle/fourth-ui-ios-and-android-nav.inputs.json`
- `docs/development/evidence/gradle/fourth-ui-ios-and-android-nav.summary.json`
- XML directory:
  `docs/development/evidence/gradle/fourth-ui-ios-and-android-nav/reports/calf-geo/build/test-results/testAndroidHostTest/`

Source base is still `94d2492e99d5cbc060409d94d9f88febd06222d5` plus held
uncommitted changes. These 88 executions repeat shared tests and API-matrix
methods; do not add previous runs as new unique tests. The prior 87/88 failure
and its diagnostic correction remain above. All six findings remain
**partially-verified**: no physical device/live GMS, process restart, native/browser
runtime, ABI/packaged consumer or immutable release verification follows from
this rerun. No source was edited or Gradle command run by this documentation
reviewer during this evidence update.

### iOS KLIB compilation — zero native test executions

The lead's first iOS KLIB command executed
`:calf-geo:compileKotlinIosSimulatorArm64` and
`:calf-geo:compileTestKotlinIosSimulatorArm64` successfully. The combined command
failed in other modules. Its verification receipt records 222 selected inputs
unchanged and the inspected log hash matches. This establishes source/test KLIB
compilation, **not linking, simulator execution, a native-provider implementation,
or a passing Apple runtime suite**. Geo iOS still explicitly reports unsupported.

- `docs/development/evidence/gradle/first-ios-klib.log.result.json`
- `docs/development/evidence/gradle/first-ios-klib.log`
- `docs/development/evidence/gradle/first-ios-klib.verification.json`

## Original required-test disposition

This maps the unchanged `required_tests` in the six baseline findings to the
current executed suites. A common-controller assertion does not silently stand
in for an Android transport, a real composition, or a device/provider check.
Suite/method names below refer to the source table above; overlapping coverage is
not counted as additional executions.

| Finding | Executed coverage | Still outside that coverage |
|---|---|---|
| **PERM-018** | The first Android-host run of `AndroidLocationTrackerTest.realLocationResultFlowsThroughNativeAdapterIntoBothPublicStates` delivers one real Android `LocationResult`; later runs pass its additional consecutive/batched/duplicate/stale/post-stop assertions. The corrected 20:11–20:14 run also passes `nativeFixesRecomposeBothPublicViewsWithoutDuplicateOrDisposedDelivery` with all exact observation counts unchanged. `LocationTrackingControllerTest.nativeFixUpdatesAllViewsFromOneSnapshot` delivers multiple controller fixes; its no-fix, duplicate/older-fix, stop/close and real `SnapshotStateObserver` tests pass. `AndroidLocationSubscriptionTest.nullLastLocationDoesNotInventAZeroFix` covers empty native input. | The earlier initial-count harness failure remains recorded, not erased. Actual host Compose-runtime assertions are not physical-device UI/rendering or live-provider proof. |
| **PERM-019** | `UnsupportedLocationTrackerTest` compiles the common factory use in shared nonAndroid test code and executes the desktop actual's unsupported/no-fix/close behavior. `AndroidLocationTrackerTest.commonFactoryCreatesAnExplicitlyUnboundAndroidTracker` executes the Android factory contract. | Browser/iOS actual execution remains pending; no standalone common consumer compilation fixture was run for this unpublished module. iOS usage keys/denial/accuracy and browser secure-context/watch cancellation are deferred with their unimplemented acquisition backends, not passed by an unsupported result. |
| **PERM-020** | The Android `bindAStartBindBDestroyADoesNotStopB` test verifies observer removal and exactly one removal for B's destruction. Repeated binding, foreground restart, cancellation/rebind, stale callbacks, terminal close and late/failed native removal are covered by wrapper/controller/transport suites. The actual-wrapper/native-adapter destroy-then-bind-new-owner test passed in the later 88-case run. | Actual Activity/process restoration, weak-reference/GC checks and physical leak/power profiling were not executed. |
| **PERM-021** | Host tests cover denied/coarse/fine permission reading, preflight/native-boundary revocation, resume/fix revocation, unbound/inactive starts, main/background dispatch, canceled/failed registration and removal Tasks, duplicate starts and controller recovery after errors. | Injected `ApiException`/availability events do not establish missing/outdated Play Services, disabled device settings or real OS permission/background policy behavior. |
| **PERM-022** | `AndroidLocationFixTest` exercises independent presence/accuracy flags, missing vs true zero, units/clocks, negative altitude and the native mock flag across its declared Robolectric API matrix. Controller tests cover stale-fix ordering and permission granularity without inventing precision. | No hardware coarse-fix/accuracy/freshness characterization, provider mock policy, device matrix or power/privacy measurement was performed. |
| **PERM-023** | All 11 `LatLngTest` methods execute on desktop JVM and Android host: unchecked compatibility, validation/normalization, identical/cardinal/dateline/poles/antipodes/tiny deltas, spherical units, rounded ranges and seeded symmetry/bounds. | JS/Wasm/Native precision execution and numerical/performance benchmarking remain pending. This is contract hardening; the historical 5,000,000-case baseline probe did not reproduce a valid-input NaN bug. |

All six also lack an immutable-commit release-verification receipt for these
changes. The passing held-input diagnostic runs are useful evidence, not an ABI
certification, publishing gate approval or issue-closure instruction.

## Remaining checks and release boundaries

1. Android device/OS/GMS matrix: real coarse/fine grants, revocation while active,
   disabled location settings, unavailable/outdated GMS, denied/background policy,
   Activity/process recreation, start/cancel/destroy races, and resource/power
   profiling. Host Task tests do not establish OS prompt or hardware behavior.
2. Native Tasks have no library-imposed timeout. The suspending start can be
   bounded with caller `withTimeout`; cancellation suppresses delivery and begins
   cleanup, but cannot force a hung provider Task to acknowledge removal.
3. iOS, desktop and web remain deliberately **unsupported** for actual location
   acquisition. Implementing CoreLocation, browser geolocation/secure-context
   policy, or a desktop provider is a separately scoped roadmap item, not a pass
   inferred from expect/actual compilation.
4. Retained signatures are a compatibility strategy, not an ABI certification.
   Legacy zero→NaN and lifecycle/undefined-bearing behavior changes require release
   notes and downstream review before this prototype is ever published.
5. No performance benchmark, physical leak check, privacy/power certification,
   successful package build, or release-readiness claim follows from these edits.


## Addendum — historical JVM constant compatibility (22:37 UTC source freeze)

The first real candidate JVM comparison exposed a development-introduced
compatibility regression in `LatLng.EarthRadius`. This is a **confirmed-test
failure of the pre-repair candidate**, not a new baseline math finding and not
a claim that the entire library's ABI is certified. Geo remains **unpublished**.

At baseline `af388bd...` (also unchanged in the `94d2492e...` source used for the
compiled baseline), `LatLng.kt:78–80` has a private companion but a public
`const val EarthRadius = 6371.00`. The JVM compiler nevertheless emitted
`LatLng.EarthRadius` as a **public static final primitive double**, descriptor
`D`. During validation/factory hardening the companion became public and the
constant itself became private. That removed the previously exposed JVM field
from the public surface. Kotlin source visibility alone had not captured this
historical Java contract.

The inspected, preserved
[JVM delta](evidence/jvm-diagnostic-20261024T223018Z/jvm-delta.json) and separate
[Java characterization](evidence/jvm-diagnostic-20261024T223018Z/earth-radius-characterization/result.json)
record four commands against actual baseline/candidate JARs:

| Existing characterization command | Inspected result |
|---|---|
| Compile the Java source against the baseline | Exit 0 |
| Run that class against the baseline | Exit 0; both the constant and public reflection lookup equal 6371.0 |
| Run the **unchanged baseline-compiled class** against the pre-repair candidate | Exit 1; `Class.getField("EarthRadius")` throws `NoSuchFieldException` |
| Compile the same Java source against the pre-repair candidate | Exit 1; `EarthRadius has private access in LatLng` |

The unchanged class still prints `inlined_radius=6371.0` before its reflective
failure: javac inlined the old constant. Thus a test which only reads an inlined
constant would miss this regression. These observations establish Java source
and public-reflection incompatibility; they are not a demonstrated
`NoSuchFieldError` from a non-inlined field instruction or a whole-ABI verdict.

After the consumer's 22:34:30Z postcheck released its 700-source/23-JAR hold, the
lead authorized exactly two source files:

- `LatLng.kt` keeps the existing companion and restores the same-name,
  same-value `const val` with visible `@Deprecated(level = WARNING)`.
  **Do not use HIDDEN or JVM-synthetic visibility** to preserve only a nominal
  binary field while breaking Java source access. This exposes a deprecated
  Kotlin property too; no coordinate algorithm, numerical model, constructor,
  tracker behavior, units or publication configuration changes.
- [LatLngJvmCompatibilityTest.kt](../../calf-geo/src/desktopTest/kotlin/com/mohamedrejeb/calf/geo/LatLngJvmCompatibilityTest.kt)
  adds one Desktop test using public `getField`, with no accessibility override.
  It requires the original declaring class, primitive double type, exact
  PUBLIC/STATIC/FINAL flags, a non-synthetic field and runtime value 6371.0.
  Its block-bodied test method returns Unit; it does not merely inspect an
  inlined reference or accept a private `getDeclaredField` result.

The two files were refrozen at **22:37:41Z**; all other 22 geo source/build inputs
were unchanged. Exact before/after hashes, original negative command/output
hashes and additive-document checks are in
[GEO-EarthRadius-jvm-compatibility-repair.json](evidence/GEO-EarthRadius-jvm-compatibility-repair.json).
The resolution ledger adds this follow-up to PERM-023 without modifying the
original audit finding or deleting earlier evidence.

At that source freeze the new test was **prepared, not executed**. There are now
39 prepared Desktop declarations: 36 common, two nonAndroid and one JVM-field
test; this is not 39 passes. Required verification is a lead-coordinated geo
`desktopTest` plus `desktopJar` rebuild, inspection of the emitted field and
ConstantValue, then the same Java source compile and **unchanged original
baseline-compiled class** against the rebuilt JAR with all third-party inputs
held. Earlier 38-case Desktop passes cannot verify this new field test.

No Gradle, javac or Java runtime command was launched by this repair reviewer.
The historical failing receipts remain unchanged. This source checkpoint does
not close PERM-023 or another issue, prove Android/KLIB/Swift ABI, certify a
standalone Maven consumer or lift containment/release gates.


### Additive executed follow-up — 22:38–22:42 UTC

The source-only checkpoint above was followed by the lead's actual
[second candidate JAR/geo build](evidence/gradle/second-candidate-jars-geo-regression.summary.json):
**exit 0 in 11 seconds, 39/39 GEO desktop tests in four fresh XML reports**,
including `legacyEarthRadiusRemainsAJavaVisiblePublicStaticFinalDouble`.
All 23 requested desktop JAR tasks freshly executed; the 701 captured inputs
were unchanged. Only the two authorized geo source files differ from the first
candidate. These are repeated existing scenarios plus one new reflection
regression, not 39 new independent tests.

The consumer reviewer then replayed **the same original failing baseline class
bytes**, rather than silently recompiling the old binary, against the rebuilt
geo JAR. That run and a separate unchanged Java-source compilation/runtime
all passed. The preserved [replay receipt](evidence/jvm-diagnostic-20261024T224234Z-geo-repair/earth-radius-replay/result.json)
binds the original class SHA256, dependencies, JARs and all four commands.
The [second diagnostic](evidence/jvm-diagnostic-20261024T224234Z-geo-repair/result.json)
verifies that only geo's JAR changed. The narrow public-field Java source and
reflection regression is resolved in those tested bytes.

The raw whole-JVM comparator still exits **1** with 18 individually classified
removals (modifier-only, Kotlin-internal and generated/private-local records);
it is not converted into a green ABI gate. The strict Maven consumer remains
unexecuted, geo remains unpublished and the original failed diagnostics remain
untouched. The lead subsequently rechecked all four XML hashes/39 cases and
all 101 files bound by the two consumer evidence checksum inventories; see
[GEO execution review](evidence/GEO-EarthRadius-execution-lead-review.json).
Finding status stays **partially-verified**, with device, native, whole-API,
immutable-candidate and distribution gates unchanged.


## Current-source JS browser execution — 23:00–23:10 UTC

**Scoped geo result: 38/38 actual JS browser cases passed in three fresh XML
reports; the complete requested library command still failed.** The
[full command receipt](evidence/js-full-001/receipt.json) records
2026-10-24 23:00:48.233382Z–23:10:28.351892Z, 580.12 seconds, exit **1**.
The [archive](evidence/js-full-001/archive.json) preserves the overall 267 cases
(265 passes, navigation/WebView failures) and share's test-compilation failure
with zero share executions. Passing geo tests do not erase those failures.

| Geo JS suite | Executed cases | What ran |
|---|---:|---|
| `LatLngTest` | 11 | Current coordinate validation/normalization and spherical math, including 500 seeded pairs inside one test method |
| `LocationTrackingControllerTest` | 25 | Production common state machine, Compose snapshot observation, missing/true-zero values, ownership/cancellation/stale events and cleanup with injected provider callbacks |
| `UnsupportedLocationTrackerTest` | 2 | Real JS actual/common factory, explicit Unsupported/no-fix/NaN compatibility contract and terminal close |
| **Total** | **38** | **Three XML reports; zero failures/errors/skips** |

The runtime is **Google Chrome 153.0.8010.36 on Linux x64**, with JDK17.0.20;
XML identifies ChromeHeadless153.0.0.0. The reviewer independently verified all
three archived XML hashes, their producer/raw-report bindings, 38 testcase names
and statuses, current source method names, a fresh `:calf-geo:jsBrowserTest` task
marker and report timestamps within the run. These repeat existing methods on a
new executed target; neither the 500 generated coordinate pairs nor the earlier
Desktop/Android repetitions are counted as additional unique tests.

The JS actual remains deliberately **unsupported for location acquisition**.
The two actual/factory cases call `createLocationTracker()` and the real JS
implementation; they do not call `navigator.geolocation`, acquire coordinates,
show permission UI or test secure-context/accuracy/watch cancellation. The 25
controller cases use injected provider events and the JS event loop, not real
Android/GMS transport, native main-thread races or visual Compose rendering.
Wasm/Apple execution, native/device/provider/privacy matrices and profiling
remain separate gates. The JVM-only EarthRadius reflection case is **not part
of these 38 JS cases**; its already-recorded 39-case Desktop/unchanged Java
consumer verification remains above, unchanged and separately scoped.

The helper's 691-file before/after snapshots are identical; the archive reports
an unchanged broader 703-input notice/identity/license-inclusive freeze. This
area review independently matched **all 24 captured geo source/build inputs**
to their held hashes, including the two EarthRadius repair files. Hashing the
JVM test does not imply it executed on JS. See the combined
[PERM/GEO JS verification receipt](evidence/PERM-GEO-js-first.json).
Chrome's local root-container wrapper used `--no-sandbox` and
`--disable-dev-shm-usage`; this is a disclosed test environment limitation, not
a production trust-policy change or security certification.

This supersedes the earlier pending **JS** math/controller/unsupported-actual
checks only. Wasm and Apple target execution remain pending; unsupported browser
acquisition is not counted as an implemented provider. All six geo findings
remain **partially-verified**. The earlier test/compilation failures, original
EarthRadius incompatibility and lead's execution/consumer addendum are preserved.
No new runtime was launched or source/build/GitHub state changed by this reviewer,
and no complete ABI/Maven/immutable-release or publication clearance is implied.


## Latest paired Wasm/JS004 verification — 2026-10-25

**Geo scope: 38/38 cases passed on each browser target in three fresh XML
reports.** Both complete-requested library commands passed **290/290 cases,
48 reports and 19 test-bearing modules per target**:
[Wasm004 command](evidence/wasm-full-004/receipt.json) ran at
01:25:19–01:27:22 UTC (123.02 s, exit 0);
[JS004 command](evidence/js-full-004/receipt.json) ran at
01:28:05–01:30:15 UTC (130.03 s, exit 0).
Neither command is an immutable candidate or a release verification.

| Geo suite | Wasm004 | JS004 | Actual scope |
|---|---:|---:|---|
| `LatLngTest` | 11 | 11 | Validation/normalization, units, poles/dateline/antipodes/bearings and seeded spherical-distance properties |
| `LocationTrackingControllerTest` | 25 | 25 | Production common state/snapshot/ownership/cancellation/error/nullability behavior with injected provider events |
| `UnsupportedLocationTrackerTest` | 2 | 2 | Public factory and the real target actual: explicit Unsupported/no-fix/NaN and terminal-close contracts |
| **Total** | **38** | **38** | **Three reports per target; zero failures/errors/skips** |

These are **76 target executions of the same 38 source methods**, not 76 new
tests. The seeded 500-pair loop remains one math method. The JVM-only
`LatLngJvmCompatibilityTest` is not inherited by either browser suite: it
contributes **zero** to these counts.

The [independent paired review](evidence/PERM-GEO-browser-004.json) matched every
geo testcase to its annotated source and the producer receipt, rehashed available
raw and archived reports, and reconstructed the sanitized XML byte-for-byte.
It also checked all 58 archive and 24 context checksum entries per target,
fresh task markers and report/configuration timestamps. The full-run integrity
recount confirms the recorded 290 outcomes; it does not expand this review's
semantic scope beyond permissions and geo.

All **24 geo source/build inputs** (23 Kotlin files and the build file) match
both runs' identical **693-input** before/after maps and current bytes. Both
EarthRadius repair files remain held. Snapshot content digests and JSON file
hashes were checked separately. The earlier, broader 703-input bootstrap
snapshot has explicitly recorded later drift; it is not retrospectively
relabelled an unchanged current freeze.

[Wasm's generated Karma context](evidence/wasm-full-004-context/context-review.json)
uses the requested prepared tooling home;
[JS's context](evidence/js-full-004-context/context-review.json) uses `build/js`.
The actual runtime receipt identifies Chrome **153.0.8010.36**, Linux x64,
JDK **17.0.20**; both targets used the disclosed
`--no-sandbox --disable-dev-shm-usage` wrapper. Selected fresh configuration
and file hashes are not a hermetic dependency/runtime attestation or a browser
security clearance.

Browser acquisition remains deliberately **Unsupported**. The two factory cases
exercise each real JS/Wasm actual through `createLocationTracker()`, but do not
call `navigator.geolocation`, acquire coordinates, display privacy UI or validate
secure-context/watch/accuracy policy. The 25 controller cases use common injected
events rather than real GMS, Apple delegates, native thread races or rendered
Compose UI. Android host/device, iOS runtime and acquisition backends remain
distinct acceptance requirements.

The earlier EarthRadius Java-source/public-reflection regression and
[39-case JVM repair verification](evidence/gradle/second-candidate-jars-geo-regression.summary.json),
[unchanged original Java-bytecode/source replay](evidence/jvm-diagnostic-20261024T224234Z-geo-repair/earth-radius-replay/result.json)
and [lead readback](evidence/GEO-EarthRadius-execution-lead-review.json)
remain intact and separately scoped. Browser passes neither rerun that JVM test
nor turn the raw whole-JVM comparator's exit 1 / 18 classified removals into an
ABI pass. Geo remains **unpublished**.

This addendum supersedes only earlier dated pending **Wasm math/controller/
unsupported-actual** checks. iOS execution, native/device/GMS/privacy and
power/GC matrices, public/packaged-consumer compatibility, immutable-candidate
and release gates remain. All six geo statuses stay **partially-verified**.
The earlier [JS001 failure](evidence/js-full-001/archive.json) and failed/incomplete
[Wasm001](evidence/wasm-full-001/archive.json),
[Wasm002](evidence/wasm-full-002/archive.json) and
[Wasm003](evidence/wasm-full-003/archive.json), as well as the original EarthRadius
failure, are preserved. No runtime/build, source/test/script change, GitHub
operation, commit or publication was performed by this documentation reviewer.
