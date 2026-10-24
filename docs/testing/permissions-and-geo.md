# Permissions and geo: testing and verification record

Baseline: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; audit date2026-10-24. See the [implementation reference](../modules/permissions-and-geo.md), [findings/coverage](../audit/permissions-and-geo.md) and [structured findings](../audit/findings/PERM.json).

## What was actually verified

| Procedure | Inspected outcome | What it does **not** establish |
|---|---|---|
| Full source review |132 baseline files read:119 permissions +13 geo; no scoped test sources found | Successful compilation or platform behavior |
| Isolated Kotlin2.4.20 JVM compilation | Exit0, using original baseline files/declarations and explicit platform adapters | Android/iOS library build, Kotlin/Native linkage, Compose compiler behavior |
| Deterministic logic checks | **16 total**, all expected observations passed:11 permission/mapping/helper checks +5 coordinate checks | That every tested observation is correct behavior; some intentionally reproduce defects |
| Seeded antipodal math search |5,000,000 pairs, Kotlin Random(483), no NaN found on this JVM | A proof over all valid coordinates or over JS/Wasm/Native math |
| Persisted reproduction re-run | Runnable repository script compiled and executed with exit0; exact output preserved | Real OS prompt order, native framework authorization, memory/lifetime safety |
| Gradle/device tests by this area reviewer | **Not run**; resource-intensive Gradle verification coordinated with the build reviewer | Any native/device pass claim |

There is no `commonTest`, Android test, iOS test, desktop test, JS test or Wasm test source under either module tree at the baseline. The permission sample's interactive screen is not an automated test suite. Consult the build audit's final command evidence for any subsequently executed project-wide Gradle checks; this document deliberately does not turn planned/other-agent work into a claimed local pass.

## Preserved, runnable baseline reproduction

- Script: [`reproductions/permissions_geo.py`](reproductions/permissions_geo.py).
- Inspected output: [`evidence/permissions-geo-baseline.txt`](evidence/permissions-geo-baseline.txt).
- Invocation from repository root:

```bash
python3 docs/testing/reproductions/permissions_geo.py
```

Optional `--repo /path/to/repository` and `--cache /path/to/gradle/modules-2/files-2.1` select explicit local inputs. It performs **no dependency downloads**, Gradle invocation, Git mutation, network access, release or package publication. It extracts the preserved baseline through `git show`, prints full SHA256 for each source input, compiles in a fresh temporary directory, executes, and deletes its own temporary directory. A missing/multiple cached compiler dependency fails with a diagnostic instead of choosing an arbitrary version.

Requirements: Python3, a Java runtime (the audit used OpenJDK21 with the Kotlin2.4.20 compiler), the preserved Git baseline, and these cached jars:

| Compiler/runtime input | Version |
|---|---|
| org.jetbrains.kotlin:kotlin-compiler-embeddable |2.4.20|
| org.jetbrains.kotlin:kotlin-stdlib |2.4.20|
| org.jetbrains.kotlin:kotlin-script-runtime |2.4.20|
| org.jetbrains.kotlin:kotlin-daemon-embeddable |2.4.20|
| org.jetbrains.kotlin:kotlin-reflect |1.6.10 (compiler runtime dependency)|
| org.jetbrains.kotlinx:kotlinx-coroutines-core-jvm |1.8.0 (compiler runtime dependency, not the library's resolved runtime)|
| org.jetbrains:annotations |13.0|

The compiler uses `-Xmx512m`, `K2JVMCompiler -no-stdlib -no-reflect -classpath <stdlib> -d <temp>/out <sources>`. Execution uses `-Xmx128m` with output classes and stdlib. It does not resolve the app/library dependency graph; the coroutine compiler-runtime jar does **not** establish that nativeCmpkit uses version1.8.0 at runtime.

### Actual source under test

Unmodified full baseline files:

- `calf-geo/.../commonMain/.../LatLng.kt`.
- `calf-permissions/core/.../AndroidPermissionRegistry.kt`.
- Common `PermissionsUtil.kt` (status/annotation extensions).
- iOS common helper `PermissionHelper.kt` (contains no native imports).
- Actual iOS `LocationPermissionHelper.kt` and `BackgroundLocationPermissionHelper.kt`.

Unmodified declarations extracted from larger files to exclude unrelated Compose/Android UI dependencies:

- Entire `Permission` class from common `PermissionState.kt:96-110`.
- `toAndroidPermission`, `isAlwaysGranted`, `getPermissionFromAndroidPermission` from Android `PermissionsUtil.android.kt:101-114`.

Explicit test adapters, inspectable inside the script:

- A trivial `@Stable` annotation only for compilation; no Compose runtime/recomposition is simulated.
- `android.os.Build.VERSION.SDK_INT`, a mutable integer for SDK32/33 lookup tests.
- `platform.CoreLocation` manager/protocol/constants with manually controlled status, request counters and delegate event delivery.
- Empty `platform.darwin.NSObject` superclass.

These adapters **do not** test iOS API availability, Objective-C dispatch, weak/strong reference rules, UIKit, Android ActivityResult contracts or real runtime permissions. They make otherwise native-dependent **Kotlin control flow** reproducible. In particular, the test can prove how the actual delegate handles an injected initial NotDetermined event, but cannot prove how often a real OS schedules that event after a user request.

### Deterministic check ledger

| # | Assertion in preserved harness | Expected observation / significance |
|---:|---|---|
|1|Permission name equality|Two objects with the same name compare equal; positive invariant|
|2|Unknown mapping|Unregistered permission maps to empty string; input to source-confirmed false-grant path (`PERM-001`)|
|3|Gallery mapping at SDK32|READ_EXTERNAL_STORAGE is active; positive version mapping|
|4|ReadStorage registered first, result intended for Gallery|Original reverse lookup returns ReadStorage and omits Gallery; **defect reproduced** (`PERM-002`)|
|5|Gallery mapping at SDK33|Legacy mapping intentionally becomes empty, not a modern media grant|
|6|Shared gate Denied(true)|Returns false without native request; verifies requestability convention|
|7|Shared gate Granted|Returns true without native launch; explains APNs fast-path omission (`PERM-015`), not an actual APNs test|
|8|Shared gate Denied(false)|Invokes native request closure; positive first-request control flow|
|9|Actual Background helper with WhenInUse authorization|False result, zero Always requests; **upgrade defect reproduced** (`PERM-009`)|
|10|Actual foreground helper with NotDetermined|Calls requestWhenInUseAuthorization once; positive initial request behavior|
|11|Actual foreground delegate receives NotDetermined then WhenInUse|Only `[false]` is delivered; later grant lost; **nonterminal-event defect reproduced** (`PERM-010`)|
|12|Same-point distance|Exactly0km|
|13|Quarter equator distance|6371π/2km within1e-8km|
|14|Initial north bearing|0degrees|
|15|Initial east bearing|90degrees|
|16|Dateline crossing distance|Short2degree arc, not358degrees; within1e-8km|

After these checks,5million seeded antipodal pairs were evaluated using the **actual** `LatLng.distanceTo`. Result was `null` (no failing example found). The audit therefore records numerical-domain hardening as a Low improvement, not a confirmed valid-input NaN defect.

**Important:** this script is an immutable-baseline defect reproduction. Its `PASS` messages mean the observed baseline behavior matched assertions, including known bugs. Do not use it as a green release gate for corrected implementations. New regression tests must assert the **desired** behavior, run current code and avoid the native adapters where actual OS integration is required.

## Regression suite to add before fixes are considered verified

The requested audit did not authorize a major architectural rewrite. The following are test designs, not tests claimed implemented. Prefer small injectable authorization/provider adapters behind current APIs, then common JVM logic tests plus platform integration fixtures. Preserve public Permission names and compatibility callbacks while making control flow testable.

### Shared logic and Compose state

| Finding | Required tests / oracle |
|---|---|
|PERM-001|Unknown vs NotApplicable vs Registered; same-name collision validation; callback false/diagnostic rather than false authorization; registry threading policy|
|PERM-002|Both alias registration orders; request only second alias; request both; only requested keys returned, both states refreshed|
|PERM-003|Empty batch, all-not-applicable, mixed batch, child launches, exactly-one complete logical callback; preserve empty-string crash guard|
|PERM-005|Recompose with callback A→B for same permission/list; onlyB invoked on runtime and fast paths; stable helper retained|
|PERM-006|Granted→revoked and denied→granted on resume, one-time expiry, out-of-order query completions, observer removal|
|PERM-007|Background completion marshalled to main; coherent status before result; callback after disposal suppressed; callback exception cannot skip cleanup|
|PERM-008|Serial order, native-domain deduplication, complete map, empty batch, cancellation, reentrancy and duplicate logical permissions|
|PERM-016|Explicit requestability/partial/unsupported behavior while legacy Boolean compatibility remains defined; Android rationale=false ambiguity documented|
|PERM-017|No supported-looking silent request on unsupported targets; deterministic callback/outcome even when no OS API exists|

Also verify preview behavior intentionally chosen for initial permission identity, grant/deny visualization and requested list membership. Introduce immutable-list expectations or defensive snapshots; recomposition after list replacement and in-place mutation must not silently retain wrong states. Test launcher disposal/recreation and old results arriving after the requested permission changes.

### Android runtime integration matrix

Minimum library Android API is23 at the baseline; sample minimum is24. A sample-only test therefore cannot prove the library's API23 floor.

| Device/API cohort | Scenarios |
|---|---|
|23 and28|Manifest-present/absent dangerous permissions; first denial/rationale/permanent denial; read/write storage before range boundaries; library consumer below sample minimum|
|29|ReadStorage+WriteStorage historical empty-string crash reproduction; scoped and legacy-storage target modes; background location introduction|
|30|Foreground/background requests separated; background settings flow; all-files special-access is not WriteStorage|
|31/32|Fine+coarse request pairing, approximate selection, Bluetooth new permissions and old Bluetooth/location prerequisites|
|33|POST_NOTIFICATIONS denied/granted; RemoteNotification remains documented iOS-only; media/audio/Nearby Wi-Fi mappings|
|34 and latest available target/runtime|Selected media/partial access; auto-reset/one-time grants; modern foreground/background restrictions|

Run both current targetSdk and any legacy targetSdk claimed supported. Verify that requested manifest strings are nonblank, deduplicated and restricted to appropriate batch stages; returned logical maps must include only requested permissions. Never grant fake OS permissions in a test and then call that an integration pass. Treat disabled global location, absent hardware, limited user/profile policy and denied authorization as different conditions.

For callbacks, instrument ActivityResult with a consumer fixture and assert main-thread delivery, state-update ordering, configuration recreation and composable removal while the system dialog is open. The baseline has no such instrumented test consumer in these modules; Gradle tasks cannot manufacture this coverage merely by being green.

### iOS native/device matrix

Test at the actual documented library minimum (still a decision), below17 **only if that deployment remains supported**,17,18/18.5 and current supported iOS. The sample's18.5 target hides older EventKit availability. Use fresh installations/reset privacy state so a pre-existing grant does not skip the important request path.

| Area / finding | Required native evidence |
|---|---|
|Location009/010|NotDetermined/AllowOnce/WhenInUse/Always/restricted/denied, deferred Always upgrade, initial delegate event ordering, precise toggle, services off, repeated/reentrant launch|
|Calendar011/012|Legacy/full/write-only usage keys, missing-key failure, below17 selector availability if supported, FullAccess vs WriteOnly mapping and least-privilege prompt|
|AV/contacts/photos007/016|Real completion queues, disposal during prompt, restricted/limited contacts, selected/full photos, legacy-vs-modern Photos status behavior|
|Bluetooth014|Physical BT hardware; powered-off/resetting/unsupported, consent after>2s, Kotlin/Native GC while prompt waits, delegate lifetime, repeated/throwing callbacks, scan stop and Instruments retention|
|Notifications015/016|Fresh/local-first/already-authorized/provisional/ephemeral flows; APNs registration main-thread calls; real aps-environment provisioning, token/error callbacks; permission true is not registration success|
|Wi-Fi013|Passive observation must not prompt/publish; explicit probe with NSBonjourServices `_lnp._tcp`; absent key, inactive app, network unavailable, consent>3s, repeated aliases, cancellation, timer/native-service teardown|
|Lifecycle006/007|Settings return in both directions without assuming process death; state and callback ordering after resume/recreation; cancellation prevents obsolete UI actions|

A simulator alone cannot prove Bluetooth, APNs delivery, physical location behavior or background power use. Purpose-string/entitlement availability is a consuming-application property; build/run small feature-specific apps, not only the umbrella sample with every native framework linked. Include static binary/framework/link inspection and privacy declarations where a native platform permits it. Instruments/device logs should be summarized without committing user locations, device identifiers, tokens or private transcripts.

### Desktop and browser contracts

Current behavior is source-confirmed no-op/denied. Before implementing new backends, decide Unsupported vs NotRequired semantics by permission/OS. macOS TCC can deny camera/microphone even in desktop JVM applications; globally mapping every permission to Granted is not a safe general solution. Browser implementations must distinguish Permissions API support from the actual user-gesture-triggered media/geolocation/notification request, secure context requirements, iframe permissions policy and rejected promises. Add JS and Wasm browser tests separately, not just a common target compile check.

### Geo regression plan

| Finding | Required assertion |
|---|---|
|PERM-018|A supplied Android LocationResult changes both public observable states coherently; no-fix is explicit; channels either consumed or removed|
|PERM-019|A common-code factory/sample compiles; unsupported target reports unavailable, not0,0; real backends deliver updates and release subscriptions|
|PERM-020|BindA/start/bindB/destroyA does not stopB; destroyB cleans up exactly once; repeated start/stop/rebind and late callbacks are generation-safe|
|PERM-021|Unbound/denied/revoked/no-GMS/provider-error/incorrect-thread/cancelled registration returns a defined result and rolls back subscription state|
|PERM-022|Each native has* measurement/accuracy flag is independently represented; true0 is distinct from missing; correct units and timestamps|
|PERM-023|Distance symmetry/bounds, equator/dateline/poles/close/antipodal cases, invalid inputs and undefined bearing policy, rounded0..350 vs unrounded[0,360)|

Use a fake FusedLocationProvider adapter for deterministic failure/order/cancellation tests, then an Android fixture with real Play Services and location permission. Verify no state updates after stop/disposal, no duplicate observers/subscriptions, stale/mock-fix policy, and no location persistence/logging unless the caller explicitly requires it. Run math properties on Native/JS/Wasm as well as JVM before claiming equivalent numeric behavior.

## Coverage and evidence maintenance

- The [audit coverage appendix](../audit/permissions-and-geo.md#complete-baseline-file-review-coverage) enumerates all132 file paths, logical line ranges, hashes and declarations. It is a **review** inventory, not a code-coverage percentage.
- Every structured finding specifies exact baseline locations, priority, confidence, cause, impact, solution, risks, effort, dependencies and required tests. Source-confirmed findings require an actual positive regression test before closing their future issue.
- Keep immutable-baseline reproductions separate from current-code regression suites. Record command, toolchain, target/runtime, source revision and inspected exit/result, not merely that a tool was invoked.
- No percentage coverage, load/performance benchmark, dependency-vulnerability result, native memory safety or device success is inferred from this small suite.
- Do not publish packages/releases or enable automatic publication while adding tests; owner authorization remains required.

## Final audit-artifact validation

The completed artifacts were checked against the preserved baseline after the reproducible harness re-run:

- All24 JSON findings have the complete required schema, valid confidence/priority/effort values and unique IDs.
- Every finding location exists at the baseline and every cited line/range is in bounds; referenced upstream issue/PR IDs exist in the archived metadata and commit IDs resolve in preserved Git history.
- Finding dependencies form an acyclic graph with no missing IDs.
- The coverage appendix has exactly132 unique scoped paths, matching the baseline tree; every logical line count and SHA256 prefix matches its Git blob.
- The persisted Python reproduction parses, and the preserved execution record contains compiler exit0, execution exit0,16 PASS assertions and no antipodal failing example.
- Local document links resolve and the six owned documentation/reproduction/evidence files have no trailing whitespace.

These checks validate the **audit artifacts**, not runtime platform correctness or resolved GitHub issue state. No source fix, commit, GitHub mutation, package or release was performed by this reviewer.
