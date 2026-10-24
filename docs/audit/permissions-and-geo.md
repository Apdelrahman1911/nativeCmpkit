# Technical audit: permissions and geolocation

## Scope and confidence

Reviewed baseline: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. No production source was changed by this reviewer. References always address baseline paths/lines even if migration later edits documentation or identity. This report complements the [implementation reference](../modules/permissions-and-geo.md) and [verification record](../testing/permissions-and-geo.md).

The entire `calf-permissions/` tree (umbrella +11 child projects) and `calf-geo/` were read: **132 tracked files**, including every common expect/API declaration, every platform actual, native helper, build file and manifest. All named classes/functions are catalogued in the coverage appendix; execution/ownership details are in the module reference. Supporting reads included target/Android conventions, versions, permissions documentation, sample permission screen, Android manifest and iOS plist/deployment settings. Source and selected historical diffs, issue bodies and comments were cross-checked; GitHub closure or historical success reports were never treated as current test evidence.

**24 findings:**8 High,15 Medium,1 Low; no Critical finding.17 are source-confirmed,3 are confirmed by isolated Kotlin logic tests,2 are explicitly risks,2 are improvements. “confirmed-test” here describes a JVM harness with controlled platform adapters, not permission-dialog/device tests. No native memory leak, data exfiltration, privilege bypass or valid-input antipodal math failure was demonstrated. Numerical hardening and Bluetooth lifetime concerns remain appropriately qualified.

### Executive state

- **Permissions Android:** meaningful implementation, but wrong logical aliases in bulk callbacks, incomplete location workflow orchestration, callback-contract gaps and state lifecycle issues prevent a blanket reliability claim.
- **Permissions iOS:** real native helpers, but BackgroundLocation blocks WhenInUse-to-Always upgrades, calendar API/purpose strings are mismatched, multi-request dispatch has no coordinator, and Wi-Fi observation performs an active network probe. Completion threading, request lifetime and capability granularity require work.
- **Permissions Desktop/Web:** denied/no-op stubs, not runtime permission implementations. Existing feature docs restrict their promise to Android/iOS; KMP target presence is not parity.
- **Geo Android:** cannot emit a usable location through its public State; produced values go into unconsumed private channels. Lifecycle, permissions and metadata handling are also incomplete.
- **Geo other targets:** print-only stubs with fabricated default coordinates. Baseline geo has no publication plugin. Treat as an internal prototype until explicitly completed and verified; do not publish it as supported functionality.

## Evidence ledger and checks actually executed

1. Read every one of the132 scoped baseline files in full with line numbers, including36 nonmobile permission registration files whose bodies are all Unit.
2. Followed registration from all28 public Permission getters through platform mappings/factories and every helper status/request branch.
3. Inspected state construction, recomposition keys, callback capture, ActivityResult setup/disposal, lifecycle effects, iOS callback queues, manager/delegate retention, Wi-Fi timer/probe cleanup, and geo update/state flow.
4. Queried Git history and reviewed relevant diffs (registry/modularization, background, calendar, iOS batching/lifecycle, Bluetooth, APNs, empty-string filtering). Checked archived metadata referenced in the history table below.
5. Built isolated **actual baseline Kotlin**: `LatLng`, `AndroidPermissionRegistry`, extracted unmodified `Permission`/Android mapping functions, common status definitions/shared iOS helper gate, actual foreground/background iOS helper files, and minimal explicit Android/CoreLocation/annotation adapters. Kotlin2.4.20 compilation and JVM execution both exited0.16 deterministic checks passed; several assert a known defect rather than its absence.
6. Tested LatLng normal cases and5,000,000 deterministic antipodal pairs on JVM; no NaN found. This does not establish numerical behavior for all inputs/targets.
7. No Gradle build or device execution was independently performed by this area reviewer. The build reviewer owns shared resource-intensive verification; use its final evidence for project-wide compilation/test status. Do not substitute the small harness for an Android/iOS build.

There are **no test source files** in either audited subtree at the baseline. Permission-screen UI is a demonstration, not a test suite. No actual Android dialog, iOS simulator/device, macOS TCC, browser permission request, APNs delivery, Instruments run, battery profile or network-capture test was performed here.

## Positive safeguards and non-findings

- Modular feature dependencies and separately named camera/microphone helper classes are a useful response to privacy/framework coupling and duplicate native class problems.
- Name equality/hashCode agree, companion singleton registration is straightforward, and the Android missing-Activity exception is explicit. Android state is refreshed before the ordinary ActivityResult user callback.
- DisposableEffect removes lifecycle observers/launcher references correctly in the permission facade (the separate geo lifecycle binding does not share that design).
- API guards avoid requesting POST_NOTIFICATIONS before33, background location before29, Bluetooth scan/connect/advertise before31 and new media/Wi-Fi permissions before33. These mappings express runtime applicability, not unrestricted capability.
- Android bulk filtering fixes a real empty-string crash from #386/#413; preserve that guard when repairing callback completeness.
- iOS core refresh assigns snapshot state on Main, and foreground/background location strongly retain delegates. Wi-Fi cleanup invalidates timers, clears native delegates/stops services and uses a one-shot guard and identity check.
- Bluetooth uses proper structured OS version comparison and a callbackFired guard; common grant/deny flows were reported tested in historical #339. This audit does not label all BT behavior broken.
- RemoteNotification always-granted Android behavior is intentionally documented and confirmed in upstream #191; it is not by itself a newly discovered permission bypass. Use Notification for Android notification permission.
- No automatic package/release publication was executed. Geo's lack of a publication plugin is a boundary, not permission to publish it now.

## Finding index

| ID | Priority | Confidence | Finding |
|---|---|---|---|
| [PERM-001](#perm-001) | Medium | confirmed-source | Android silently treats an unregistered Permission as granted |
| [PERM-002](#perm-002) | High | confirmed-test | Android bulk results are assigned to the first global permission alias, not the requested permissions |
| [PERM-003](#perm-003) | Medium | confirmed-source | Android bulk/child permission requests do not consistently deliver completion callbacks |
| [PERM-004](#perm-004) | High | confirmed-source | Android location requests do not orchestrate fine/coarse and foreground/background prerequisites |
| [PERM-005](#perm-005) | Medium | confirmed-source | Remembered permission objects retain obsolete result callbacks after recomposition |
| [PERM-006](#perm-006) | Medium | confirmed-source | Permission lifecycle refresh skips previously granted permissions, leaving revocations stale |
| [PERM-007](#perm-007) | Medium | confirmed-source | iOS result callbacks are not main-thread/disposal safe and run before status refresh |
| [PERM-008](#perm-008) | High | confirmed-source | iOS multi-permission launch is concurrent and returns singleton results rather than a complete batch |
| [PERM-009](#perm-009) | High | confirmed-test | iOS BackgroundLocation cannot upgrade an existing WhenInUse grant to Always |
| [PERM-010](#perm-010) | Medium | confirmed-test | iOS location delegates consume pending requests on nonterminal events and overwrite overlapping callbacks |
| [PERM-011](#perm-011) | High | confirmed-source | iOS calendar uses the iOS17 full-access API without availability gating or matching usage descriptions |
| [PERM-012](#perm-012) | Medium | confirmed-source | iOS WriteCalendar requests full read/write access and rejects write-only authorization |
| [PERM-013](#perm-013) | High | confirmed-source | iOS Wi-Fi status observation publishes a Bonjour service and conflates timeout/cancellation with denial |
| [PERM-014](#perm-014) | Medium | risk | iOS Bluetooth request lifetime and completion need device-backed hardening |
| [PERM-015](#perm-015) | Medium | confirmed-source | iOS RemoteNotification skips APNs registration when notification authorization already exists |
| [PERM-016](#perm-016) | Medium | improvement | PermissionStatus loses partial capability, precision and requestability distinctions |
| [PERM-017](#perm-017) | Medium | confirmed-source | Desktop, JS and Wasm permissions are nonfunctional stubs with silent callbacks |
| [PERM-018](#perm-018) | High | confirmed-source | Android LocationTracker never updates its public location states |
| [PERM-019](#perm-019) | Medium | confirmed-source | Non-Android geolocation trackers only print messages and report fabricated zero coordinates |
| [PERM-020](#perm-020) | Medium | confirmed-source | Android LocationTracker rebinding has no ownership boundary or coroutine cleanup |
| [PERM-021](#perm-021) | High | confirmed-source | Android LocationTracker suppresses missing-permission checks and ignores provider failures |
| [PERM-022](#perm-022) | Medium | confirmed-source | Android geo data treats missing accuracy/speed/bearing/altitude as real zero measurements |
| [PERM-023](#perm-023) | Low | improvement | Specify and test the numerical domain and undefined-bearing policy of LatLng |
| [PERM-024](#perm-024) | Medium | risk | Storage guidance asks for all-files access that WriteStorage never requests or verifies |

## Implementation-level findings

The JSON source of truth is [findings/PERM.json](findings/PERM.json). Each entry below includes exact baseline locations, cause, impact, remediation tradeoffs and required tests. Nothing in the recommendation column is claimed implemented.

<a id="perm-001"></a>
### PERM-001 — Android silently treats an unregistered Permission as granted

**Medium · confirmed-source · effort M**

**Locations:**
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/PermissionsUtil.android.kt:101-111` — `toAndroidPermission/isAlwaysGranted`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt:86-99,118-126` — `launchPermissionRequest/getPermissionStatus`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt:24-38` — `register/getMapping/findByAndroidString`

**Root cause:** No mapping and a deliberately out-of-SDK-range mapping both become the empty string. The state interprets either as Granted and calls onPermissionResult(true). The public open Permission class permits custom permissions without an Android registration.

**Impact:** Missing custom integration is indistinguishable from real authorization and differs from the explicit missing-delegate error on iOS. Consumers may attempt protected operations and fail at the OS boundary. This is not an OS permission bypass.

**Recommended solution:** Distinguish Registered, NotApplicable, and Unknown mapping results; fail clearly for Unknown, preserve explicitly documented no-op permissions, and validate custom names/ranges. Define main-thread registration or synchronize/freeze the registry.

**Risks / limits:** Existing callers may rely on custom unknown permissions being no-ops. RemoteNotification on Android is intentionally iOS-only and documented as Granted; do not silently redefine that compatibility contract as part of this fix. Concurrent registry mutation is a risk, not an observed exploit.

**Evidence:**
- Exact toAndroidPermission logic returned empty for Permission("Unregistered") in the isolated JVM harness. Source then returns Granted for empty.
- iOS PermissionDelegateRegistry.getDelegate throws for missing registration.
- Upstream #191 explicitly confirms RemoteNotification was intentionally iOS-specific.

**Required regression tests:**
- Custom unknown permission on Android/iOS gives a consistent diagnostic.
- Out-of-range mappings remain explicit not-applicable, including Notification below33.
- Custom registration/name collision and concurrent registration/lookup tests.

**Dependencies:** None.

**History:** https://github.com/MohamedRejeb/Calf/issues/191, https://github.com/MohamedRejeb/Calf/commit/7d382c69ba93e218a210239ed9dfc99a34660be0

<a id="perm-002"></a>
### PERM-002 — Android bulk results are assigned to the first global permission alias, not the requested permissions

**High · confirmed-test · effort M**

**Locations:**
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt:34-38` — `findByAndroidString`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt:40-49,144-151` — `bulk callback/updatePermissionsStatus`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt:5-12` — `registerReadStoragePermission`
- `calf-permissions/gallery/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/GalleryPermissions.android.kt:5-12` — `registerGalleryPermission`

**Root cause:** Reverse mapping selects firstOrNull from the global registry. Gallery and ReadStorage both map to READ_EXTERNAL_STORAGE on API<=32. Registration order is unrelated to the active request; updatePermissionsStatus only refreshes the matching logical permission.

**Impact:** Requesting Gallery after ReadStorage was initialized can report ReadStorage instead, omit Gallery, and leave its status stale. Requesting both refreshes only one alias; custom aliases have the same problem.

**Recommended solution:** Convert each result using the request-scoped logical-permission-to-native-string mapping; fan a native result out to every requested logical alias, deduplicate native strings, and never substitute an unrelated global alias.

**Risks / limits:** Callback maps may expand for callers that accidentally depended on one alias. Include SDK ranges and empty/not-applicable permissions without reintroducing empty launcher inputs.

**Evidence:**
- Compiled unmodified AndroidPermissionRegistry plus extracted original Permission and mapping helpers with a Build.VERSION stub; at SDK32 a result for requested Gallery became {ReadStorage=true}.
- This test validates Kotlin mapping, not an Android permission dialog.

**Required regression tests:**
- Initialize ReadStorage then request only Gallery; reverse the initialization order.
- Request both aliases and assert both state objects and callback entries.
- Run SDK28/32/33 and custom aliases; ensure only requested keys are returned.

**Dependencies:** PERM-001.

**History:** https://github.com/MohamedRejeb/Calf/commit/7d382c69ba93e218a210239ed9dfc99a34660be0, https://github.com/MohamedRejeb/Calf/pull/263

<a id="perm-003"></a>
### PERM-003 — Android bulk/child permission requests do not consistently deliver completion callbacks

**Medium · confirmed-source · effort M**

**Locations:**
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt:70-95,130-140` — `rememberMutablePermissionsState/launchMultiplePermissionRequest`

**Root cause:** The empty-string safeguard returns without invoking onPermissionsResult when all permissions are filtered; mixed batches omit not-applicable keys. A child state within a multiple state has a RequestPermission callback that only refreshes status and never invokes the supplied parent result callback; its always-granted fast path does invoke it.

**Impact:** Callback-driven workflows can wait forever for a batch containing only out-of-range permissions, and child request behavior varies by native applicability. This survives the historical crash fix.

**Recommended solution:** Define and implement one completion contract: return a complete logical result map even for empty/not-applicable batches; route child launcher results to the current child/parent callback; document whether an empty input completes with an empty map.

**Risks / limits:** Do not remove the filter added for Android10: passing empty permission strings was an actual historical crash. Callback normalization can reveal code relying on silence.

**Evidence:**
- The only callback in bulk path is inside ActivityResult launcher; line136 guards launcher execution with no else.
- Child launcher lines85-89 refresh state but do not invoke its onPermissionResult.

**Required regression tests:**
- Empty input, all-inapplicable input, mixed real/inapplicable input on API29/33.
- Launch a child state with a runtime permission and an always-granted permission; assert exactly one callback.
- Lifecycle disposal/recreation must not deliver duplicate callbacks.

**Dependencies:** PERM-002.

**History:** https://github.com/MohamedRejeb/Calf/issues/386, https://github.com/MohamedRejeb/Calf/pull/413

<a id="perm-004"></a>
### PERM-004 — Android location requests do not orchestrate fine/coarse and foreground/background prerequisites

**High · confirmed-source · effort L**

**Locations:**
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt:90-99` — `launchPermissionRequest`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt:130-138` — `launchMultiplePermissionRequest`
- `calf-permissions/location/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/LocationPermissions.android.kt:5-21` — `registerFineLocationPermission/registerCoarseLocationPermission`
- `calf-permissions/background-location/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/BackgroundLocationPermissions.android.kt:5-12` — `registerBackgroundLocationPermission`
- `docs/permissions.md:113-120,291-329` — `location examples`

**Root cause:** A logical permission maps to exactly one string; FineLocation alone requests only ACCESS_FINE_LOCATION. Bulk dispatch sends all strings together without separating background location from foreground permissions or checking prerequisites.

**Impact:** Android12+ requires requesting FINE together with COARSE for precise access; requesting fine alone may be ignored. Android11+ foreground and background location cannot be requested together; background requires an already-granted foreground path and settings-oriented UX. Common single-fine/sample bulk patterns do not implement these rules.

**Recommended solution:** Add a tested location request strategy (fine+coarse in one foreground step, then a separate background step with target-SDK-appropriate education/settings); or explicitly reject/document unsupported combinations until that API exists. Preserve approximate grants rather than treating coarse-only as total failure.

**Risks / limits:** OS and target-SDK dependent; precise dialog/device behavior was not executed in this Linux audit. Never silently escalate a coarse-only request to precise/background access.

**Evidence:**
- Source sends one native string for FineLocation and an unpartitioned array for all bulk permissions.
- Android platform guidance: https://developer.android.com/develop/sensors-and-location/location/permissions/runtime and /background.

**Required regression tests:**
- API23,29,30,31,33+ with both current and legacy targetSdk: fine alone, coarse alone, fine+coarse, foreground+background.
- Accept approximate, deny precise, deny background and return from Settings.
- Verify manifest omissions and location services disabled are distinguished.

**Dependencies:** PERM-003.

**History:** https://github.com/MohamedRejeb/Calf/issues/281, https://github.com/MohamedRejeb/Calf/pull/298

<a id="perm-005"></a>
### PERM-005 — Remembered permission objects retain obsolete result callbacks after recomposition

**Medium · confirmed-source · effort S**

**Locations:**
- `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt:39-45,63-81` — `rememberMutablePermissionState/MutablePermissionStateImpl`
- `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.ios.kt:45-53` — `rememberMutablePermissionsState`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt:39-45,79-94` — `rememberMutablePermissionState/fast path`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt:70-78` — `rememberMutablePermissionsState`

**Root cause:** Objects remembered only by permission/list capture onPermissionResult in a constructor val. Later recompositions with a new callback do not update it. Android ActivityResult callbacks use the recomposed lambda, but the direct always-granted path uses the old constructor callback; iOS uses it for every result.

**Impact:** A permission result can invoke stale navigation, state, or business logic after recomposition. Android behavior differs for runtime vs not-applicable permissions.

**Recommended solution:** Use rememberUpdatedState for callback delegation or update an internal callback holder every composition without recreating native helper state. Include context/lifecycle ownership in remembrance decisions.

**Risks / limits:** Recreating the permission helper on every callback change would introduce native request churn and lose in-flight callbacks; preserve request identity while updating the callback reference.

**Evidence:**
- The remembered objects have immutable private callback fields, and remember keys omit callback identity.

**Required regression tests:**
- Recompose callback A to B, request same permission, assert only B is called.
- Repeat for iOS, Android runtime and empty-mapping fast paths, and child states within a batch.

**Dependencies:** None.

<a id="perm-006"></a>
### PERM-006 — Permission lifecycle refresh skips previously granted permissions, leaving revocations stale

**Medium · confirmed-source · effort M**

**Locations:**
- `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionsUtil.ios.kt:22-29,53-61` — `PermissionLifecycleCheckerEffect/PermissionsLifecycleCheckerEffect`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/PermissionsUtil.android.kt:29-36,60-68` — `PermissionLifecycleCheckerEffect/PermissionsLifecycleCheckerEffect`

**Root cause:** ON_RESUME refresh is conditional on cached status not being Granted. The comment assumes revocations cause process restart; that is not a valid blanket guarantee across iOS permission types or notification settings.

**Impact:** When the app survives a settings change from granted to denied, the state remains granted until a later explicit request/recreation. Notification settings are an especially important iOS scenario. Cache status must not be treated as authorization enforcement.

**Recommended solution:** Refresh all tracked permissions on resume, with lightweight per-type status queries and asynchronous generation ordering. Remove the process-restart assumption; avoid re-triggering Wi-Fi prompts while fixing refresh.

**Risks / limits:** Unconditional refresh currently invokes the intrusive Wi-Fi status getter; fix PERM-013 or exempt side-effecting probes first. Revocation process behavior differs by OS and permission and needs devices.

**Evidence:**
- Both platform observers explicitly guard refresh with status != Granted.
- Archived #313/#331 added iOS resume support; #411 later reports settings-return staleness, not proof of this exact grant-to-deny path.

**Required regression tests:**
- Granted notification/camera/location toggled off in Settings then resume without process death.
- Denied-to-granted, one-time grant expiry, repeated resumes, batched permissions and lifecycle disposal.

**Dependencies:** PERM-013.

**History:** https://github.com/MohamedRejeb/Calf/issues/313, https://github.com/MohamedRejeb/Calf/pull/331, https://github.com/MohamedRejeb/Calf/issues/411

<a id="perm-007"></a>
### PERM-007 — iOS result callbacks are not main-thread/disposal safe and run before status refresh

**Medium · confirmed-source · effort L**

**Locations:**
- `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt:77-83,106-110` — `launchPermissionRequest/refreshPermissionStatus`
- `calf-permissions/camera/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/AVCameraPermissionHelper.kt:18-24` — `launchPermissionRequest`
- `calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocalNotificationPermissionHelper.kt:22-32` — `authorization callback`

**Root cause:** Native completion callbacks directly invoke the application onPermissionResult, then refresh status. Only status assignment is launched on Dispatchers.Main. The composition scope does not own or cancel native callbacks and there is no disposed/request-generation guard.

**Impact:** UI/navigation callbacks can run on native completion queues, observe the old denied state despite result=true, and execute after the composable was disposed. Callback exceptions also prevent the subsequent refresh.

**Recommended solution:** Marshal callback and status application onto the active main scope, refresh/apply a coherent result before notifying, and add request IDs/disposal cancellation or suppression. Define exactly-once completion/error semantics and ensure cleanup in finally.

**Risks / limits:** Do not assume all Apple completion handlers are delivered on main. Queue/lifecycle integration is unverified on-device; source confirms the absence of dispatch and callback-before-refresh order, not a demonstrated UI crash.

**Evidence:**
- AVCaptureDevice, PHPhotoLibrary, CNContactStore, EventKit and UNUserNotificationCenter callbacks are forwarded directly; only refresh assignment uses Dispatchers.Main.
- Past #150 concerned snapshot threading, and #177/#179 discussed callback shape; a Boolean callback was retained for compatibility.

**Required regression tests:**
- Deliver a helper result from a background queue and assert callback main thread and matching status.
- Dispose while native prompt remains active; no stale UI callback/state publication.
- Throw from user callback and verify cleanup/status recovery; race two asynchronous status queries.

**Dependencies:** PERM-005.

**History:** https://github.com/MohamedRejeb/Calf/issues/150, https://github.com/MohamedRejeb/Calf/issues/177, https://github.com/MohamedRejeb/Calf/pull/179

<a id="perm-008"></a>
### PERM-008 — iOS multi-permission launch is concurrent and returns singleton results rather than a complete batch

**High · confirmed-source · effort L**

**Locations:**
- `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.ios.kt:45-53,88-91` — `rememberMutablePermissionsState/launchMultiplePermissionRequest`

**Root cause:** launchMultiplePermissionRequest loops synchronously over helpers that start asynchronous native requests. Each helper invokes onPermissionsResult(mapOf(permission to result)); there is no queue, deduplication by native domain, batch map, or completion barrier.

**Impact:** Clients cannot consume one complete batch like on Android. Different native prompts contend, location prerequisite order is lost, and aliases create multiple simultaneous helpers for the same OS domain. Empty batches never invoke a callback.

**Recommended solution:** Serialize prompt-producing requests, deduplicate equivalent native authorizations, aggregate results keyed by every requested logical permission, and define empty/cancelled batch completion. Keep progress callbacks separate if desired.

**Risks / limits:** Source confirms concurrent dispatch and singleton callbacks. Exact prompt collision behavior varies by Apple API and needs device verification. Callback-contract changes should be documented as a behavioral correction.

**Evidence:**
- Commit9a33931/#422 replaced the previous unimplemented launch with this loop, resolving #248 only partially at the orchestration level.

**Required regression tests:**
- Camera+microphone, fine+coarse, foreground+background, Gallery+ReadImage and Notification+RemoteNotification batches.
- One complete callback, prompt ordering, repeated taps, empty list, disposal and OS denial.

**Dependencies:** PERM-003, PERM-007, PERM-009.

**History:** https://github.com/MohamedRejeb/Calf/issues/248, https://github.com/MohamedRejeb/Calf/pull/422

<a id="perm-009"></a>
### PERM-009 — iOS BackgroundLocation cannot upgrade an existing WhenInUse grant to Always

**High · confirmed-test · effort M**

**Locations:**
- `calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BackgroundLocationPermissionHelper.kt:25-50` — `launchPermissionRequest/getPermissionStatus`
- `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionHelper.kt:20-29` — `handleLaunchPermissionRequest`

**Root cause:** AuthorizedWhenInUse falls through to Denied(shouldShowRationale=true). The shared handler interprets that as permanently denied and immediately invokes false; requestAlwaysAuthorization is only reached for NotDetermined.

**Impact:** The normal staged foreground-to-background authorization upgrade is blocked by library logic, independently of OS dialog scheduling. Existing foreground grants can never request Always through this helper.

**Recommended solution:** Model authorizedWhenInUse as eligible for upgrade (not denied/restricted); invoke requestAlwaysAuthorization through a dedicated background state machine with the required usage keys and documented iOS staged/provisional semantics.

**Risks / limits:** Changing the generic rationale convention for every permission would reintroduce historical iOS denial bugs. Fix the background state transition specifically and keep owner-visible disclosure before background access.

**Evidence:**
- The actual baseline BackgroundLocationPermissionHelper compiled against a controlled CoreLocation adapter returned false and made zero requestAlwaysAuthorization calls for AuthorizedWhenInUse.
- This is a deterministic Kotlin control-flow reproduction, not an iOS runtime test.

**Required regression tests:**
- WhenInUse -> Always upgrade, NotDetermined -> staged authorization, denied/restricted, Allow Once, deferred Always dialog.
- Test exact callback count and app resume after a settings upgrade.

**Dependencies:** PERM-007.

**History:** https://github.com/MohamedRejeb/Calf/commit/292f66f41c63bdb2da1fbebc232758797fa1d626, https://github.com/MohamedRejeb/Calf/pull/421

<a id="perm-010"></a>
### PERM-010 — iOS location delegates consume pending requests on nonterminal events and overwrite overlapping callbacks

**Medium · confirmed-test · effort M**

**Locations:**
- `calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocationPermissionHelper.kt:16-20,28-34,67-79` — `pending callback/LocationManagerDelegate`
- `calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BackgroundLocationPermissionHelper.kt:14-18,26-32,62-71` — `pending callback/BackgroundLocationManagerDelegate`

**Root cause:** Every delegate status except accepted authorization is treated as final false, including NotDetermined. The enclosing delegate closure clears the single pending callback after invoking it. A new request overwrites the previous callback, and a reentrant callback can install a new one that is then cleared by the old completion.

**Impact:** An initial/in-progress authorization event arriving while a request is pending completes it as denied and drops the later grant; rapid/reentrant requests lose results. Apple schedules initial authorization callbacks when a manager initializes, making event ordering important.

**Recommended solution:** Ignore nonterminal status events, correlate callbacks to request generation, clear/take the old callback before invocation, coalesce or reject overlap explicitly, and cancel pending work at owner disposal.

**Risks / limits:** The adapter test deliberately injects NotDetermined after launch; frequency and timing on actual iOS devices are not established. Permission UI cannot be reliably cancelled, so disposal should suppress delivery without claiming OS revocation.

**Evidence:**
- Actual LocationPermissionHelper + LocationManagerDelegate with a controlled manager produced [false] for NotDetermined then AuthorizedWhenInUse, dropping the grant.

**Required regression tests:**
- Initial NotDetermined followed by grant/deny produces one terminal result.
- Double tap, reentrant launch in callback, status event after disposal, multiple helper instances.

**Dependencies:** PERM-007, PERM-009.

**History:** https://github.com/MohamedRejeb/Calf/issues/229, https://github.com/MohamedRejeb/Calf/pull/244

<a id="perm-011"></a>
### PERM-011 — iOS calendar uses the iOS17 full-access API without availability gating or matching usage descriptions

**High · confirmed-source · effort M**

**Locations:**
- `calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionHelper.kt:14-19` — `launchPermissionRequest`
- `docs/permissions.md:507-514` — `calendar Info.plist example`
- `sample/ios/Calf/Info.plist:27-28` — `legacy NSCalendarsUsageDescription`

**Root cause:** requestFullAccessToEventsWithCompletion is called unconditionally. That API is iOS17+, and modern full-access requests require NSCalendarsFullAccessUsageDescription; documentation and sample only declare NSCalendarsUsageDescription. Library target setup does not explicitly constrain consumers to17+.

**Impact:** Older supported consumer deployments can reach an unavailable selector; modern fresh-grant flows lack their required purpose string and cannot be relied on to authorize correctly (exact failure mode requires a device). The sample min18.5 masks older-OS availability, not the missing modern key.

**Recommended solution:** Gate iOS17+ full-access API and provide legacy requestAccessToEntityType below17, or explicitly raise/document minimum supported iOS. Correct Info.plist docs/sample with modern and legacy keys as appropriate and validate a consuming native binary.

**Risks / limits:** Do not infer a library iOS minimum from the sample target. Native availability/linking and purpose-string failure were source-reviewed, not executed on Apple hardware.

**Evidence:**
- CalendarPermissionHelper line18 invokes the modern method; no version condition exists in the file.
- Commit275e7d3 fixed always-granted status but left this request path unchanged.

**Required regression tests:**
- iOS16 and17+ fresh installs with legacy key only, full-access key, denied/restricted, and grant from Settings.
- Native linker/availability checks at the documented lowest iOS deployment target.

**Dependencies:** None.

**History:** https://github.com/MohamedRejeb/Calf/pull/208, https://github.com/MohamedRejeb/Calf/pull/233, https://github.com/MohamedRejeb/Calf/pull/421

<a id="perm-012"></a>
### PERM-012 — iOS WriteCalendar requests full read/write access and rejects write-only authorization

**Medium · confirmed-source · effort M**

**Locations:**
- `calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/CalendarPermissions.ios.kt:6-15` — `registerReadCalendarPermission/registerWriteCalendarPermission`
- `calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionHelper.kt:18,27-41` — `requestFullAccessToEventsWithCompletion/getPermissionStatus`

**Root cause:** ReadCalendar and WriteCalendar construct the same full-access helper. Modern EKAuthorizationStatusWriteOnly is not handled and falls through to Denied(true), preventing an app with legitimate write-only authorization from being represented as granted for WriteCalendar.

**Impact:** Write-only consumers are prompted for unnecessary read access and can be blocked even when the OS permits their required operation; this violates least privilege and cross-platform logical naming.

**Recommended solution:** Pass a requested access mode into the helper. On iOS17+ use write-only event authorization and recognize WriteOnly for WriteCalendar; keep legacy behavior below17 with explicit documentation.

**Risks / limits:** Callers relying on WriteCalendar to read events will need ReadCalendar/full access explicitly. This is a capability-contract change requiring migration notes and correct purpose strings.

**Evidence:**
- Both registration functions instantiate CalendarPermissionHelper() without a mode. The status switch has no WriteOnly branch.

**Required regression tests:**
- Fresh WriteCalendar requests only write access.
- WriteOnly grants WriteCalendar but not ReadCalendar; full access grants both; restricted/denied remain denied.

**Dependencies:** PERM-011.

**History:** https://github.com/MohamedRejeb/Calf/pull/421

<a id="perm-013"></a>
### PERM-013 — iOS Wi-Fi status observation publishes a Bonjour service and conflates timeout/cancellation with denial

**High · confirmed-source · effort L**

**Locations:**
- `calf-permissions/wifi/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/WifiPermissionHelper.kt:15-52,67-89,92-117` — `getPermissionStatus/startCheck/cleanupAndComplete/cancel`
- `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt:73-75,106-110` — `init/refreshPermissionStatus`
- `docs/permissions.md:537-544` — `Wi-Fi Info.plist example`
- `sample/ios/Calf/Info.plist:29-30` — `local-network description`

**Root cause:** getPermissionStatus constructs/publishes _lnp._tcp. NSNetService and is called while remembering the state, before a user request. A fixed three-second timer, inactive app, publication errors and cancelling an older check all complete false/Denied(true). The required Bonjour service declaration is absent from docs/sample.

**Impact:** Merely observing permission state can trigger a local-network prompt/advertisement. Slow consent or lifecycle changes look permanently denied; overlapping refreshes can complete a user request falsely. Local-network publication does not establish general Wi-Fi configuration/SSID privileges for all three logical Wi-Fi names.

**Recommended solution:** Separate passive status/unknown from explicit user-triggered local-network probing, report timeout/unavailable/cancelled separately, declare NSBonjourServices [_lnp._tcp] and the usage string, serialize probes and clean up on disposal. Document that Wi-Fi access/configuration capabilities are distinct from local-network privacy.

**Risks / limits:** Apple exposes no universal passive local-network authorization query; do not replace this with another undocumented heuristic presented as authoritative. Whether this exact publish operation prompts on each OS/device needs verification.

**Evidence:**
- init immediately calls refresh -> helper.getPermissionStatus -> publish(); no observational/interactive separation.
- cancel() routes through cleanupAndComplete(false); timeout unconditionally false.
- Docs/sample specify NSLocalNetworkUsageDescription only, not NSBonjourServices.

**Required regression tests:**
- Remember state without clicking: no network probe/prompt.
- Consent delayed beyond3s, inactive app, publish error, missing Bonjour declaration, denied and granted on real iOS.
- Concurrent refresh/request, three Wi-Fi aliases, disposal and network unavailable; verify cleanup/no advertisement leakage.

**Dependencies:** PERM-007.

**History:** https://github.com/MohamedRejeb/Calf/issues/315, https://github.com/MohamedRejeb/Calf/pull/316

<a id="perm-014"></a>
### PERM-014 — iOS Bluetooth request lifetime and completion need device-backed hardening

**Medium · risk · effort M**

**Locations:**
- `calf-permissions/bluetooth/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BluetoothPermissionHelper.kt:25,51-94` — `centralManager/resolveAndCleanup/centralManagerDidUpdateState`

**Root cause:** The central manager is retained, but its delegate is an inline anonymous object with no explicit strong field (CoreBluetooth delegate is weak). A single 2s check does nothing if authorization remains NotDetermined; there is no outer deadline/cancellation. Repeated requests replace centralManager, and old cleanup can clear a newer request. User callback executes before stopScan/cleanup.

**Impact:** Depending on Kotlin/Native ObjC retention and callback ordering, results may never arrive or scans/helpers may survive longer than intended. Callback exceptions/reentrancy can bypass or misdirect cleanup. These are source-supported risks, not a measured leak or confirmed device failure.

**Recommended solution:** Strongly retain a per-request delegate/context, serialize requests, clear by identity before notifying, stop scan in finally, and provide disposal/timeout as explicit non-denial outcomes. Only scan in a powered-on state.

**Risks / limits:** The historical PR reports device tests passing common flows; preserve those fixes. Kotlin/Native GC/ObjC lifetime behavior must be measured before claiming the weak delegate is the actual cause of a production failure.

**Evidence:**
- Explicit callbackFired guard and manager retention are positive existing safeguards; delegate retention and request disposal are absent.
- #339 and commit527cb35 fixed earlier API selection/NotDetermined handling, but do not prove these remaining edge paths.

**Required regression tests:**
- Force Kotlin/Native GC while permission dialog waits, consent after >2s, powered-off/resetting hardware, unsupported BT.
- Repeated/reentrant requests, throwing callbacks, composition disposal; Instruments/leak and scan activity inspection.

**Dependencies:** PERM-007.

**History:** https://github.com/MohamedRejeb/Calf/issues/205, https://github.com/MohamedRejeb/Calf/pull/339

<a id="perm-015"></a>
### PERM-015 — iOS RemoteNotification skips APNs registration when notification authorization already exists

**Medium · confirmed-source · effort M**

**Locations:**
- `calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/RemoteNotificationPermissionHelper.kt:22-42,46-64` — `launchPermissionRequest/getPermissionStatus`
- `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionHelper.kt:20-29` — `handleLaunchPermissionRequest`

**Root cause:** registerForRemoteNotifications is inside only the fresh requestAuthorization success closure. The shared handler short-circuits Granted (including provisional/ephemeral) with true, so it never registers on later launches or when local notifications authorized first.

**Impact:** The helper-added APNs registration side effect is missing for already-authorized users; apps depending on it may not obtain refreshed tokens. A Boolean permission grant is also not APNs token/registration success.

**Recommended solution:** If APNs registration remains part of this API contract, call it on main after any eligible authorized result, including the short-circuit path; explicitly separate permission from registration/token state. Document aps-environment entitlement, app delegate token/error handling and background mode only when needed.

**Risks / limits:** Some apps already register independently, so avoid duplicate callback/token assumptions. No entitlement/token delivery was tested, and a permission callback must not promise successful APNs connectivity.

**Evidence:**
- Commit4644603/#523 added registration only inside requestAuthorization success.
- Isolated original shared-handler test confirms Granted bypasses the native launch closure.

**Required regression tests:**
- Fresh permission, already authorized at launch, local then remote, provisional/ephemeral, denied; assert registration call count/main thread.
- Valid/missing APNs entitlement and native registration success/failure callbacks on device.

**Dependencies:** PERM-007.

**History:** https://github.com/MohamedRejeb/Calf/pull/523

<a id="perm-016"></a>
### PERM-016 — PermissionStatus loses partial capability, precision and requestability distinctions

**Medium · improvement · effort L**

**Locations:**
- `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionsUtil.kt:9-20` — `PermissionStatus`
- `calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocationPermissionHelper.kt:39-57` — `getPermissionStatus`
- `calf-permissions/gallery/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/GalleryPermissionHelper.kt:17-18,25-44` — `legacy Photos authorization`
- `calf-permissions/contacts/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/ContactPermissionHelper.kt:25-35` — `getPermissionStatus`
- `calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocalNotificationPermissionHelper.kt:41-55` — `authorization mapping`

**Root cause:** Two status variants collapse not-determined, restricted, permanently denied, limited and unsupported states. Fine/Coarse share a location helper that never checks accuracyAuthorization; contacts limited falls into denial; Photos uses legacy APIs that may report limited access as Authorized; provisional notifications count as Granted without delivery capability detail.

**Impact:** A granted FineLocation does not prove precise location on iOS, a limited contacts grant is unusable through the abstraction, and callers cannot distinguish partial gallery access or provisional alerts. Android shouldShowRationale=false means both first-use and permanent denial, while iOS true often means settings-only.

**Recommended solution:** Add a capability/result model alongside the compatibility Boolean API: requestability/denial reason, limited scope, iOS accuracy level and notification delivery modes. Use modern access-level APIs with availability guards. Document old Granted as a coarse permission signal, never full resource access.

**Risks / limits:** A new sealed variant can break exhaustive when expressions; prefer additive API or a deliberate major migration. Photos limited behavior differs between legacy and modern query APIs, so do not assert legacy query currently denies every limited grant.

**Evidence:**
- No partial/unsupported/requestability state exists. Native status switches expose the listed collapsing behavior.
- Historical #154/#229/#258/#284 show repeated confusion around the Boolean rationale convention.

**Required regression tests:**
- iOS reduced/full accuracy and temporary full accuracy, limited/full contacts, selected/all photos, provisional/ephemeral notifications.
- Android14 selected media, approximate location, first deny/second deny/never asked and unsupported targets.

**Dependencies:** None.

**History:** https://github.com/MohamedRejeb/Calf/issues/154, https://github.com/MohamedRejeb/Calf/issues/175, https://github.com/MohamedRejeb/Calf/issues/229, https://github.com/MohamedRejeb/Calf/issues/258, https://github.com/MohamedRejeb/Calf/issues/284, https://github.com/MohamedRejeb/Calf/issues/177

<a id="perm-017"></a>
### PERM-017 — Desktop, JS and Wasm permissions are nonfunctional stubs with silent callbacks

**Medium · confirmed-source · effort L**

**Locations:**
- `calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.desktop.kt:22-28,44-54` — `rememberMutablePermissionState/MutablePermissionStateImpl`
- `calf-permissions/core/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.js.kt:22-28,43-52` — `MutablePermissionStateImpl`
- `calf-permissions/core/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.wasmJs.kt:22-28,43-52` — `MutablePermissionStateImpl`
- `calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.desktop.kt:69-71` — `launchMultiplePermissionRequest`

**Root cause:** Nonmobile factories discard callbacks; all states start Denied(false), and request, refresh and settings methods are empty. All nonmobile feature registration actuals are Unit. Multiple launch is also empty.

**Impact:** Shared UI compiles but can be permanently blocked by a denied permission gate even where the OS/browser operation is possible; callback consumers wait indefinitely. Existing docs correctly describe permissions as Android/iOS, so this is a capability gap rather than proof that advertised browser dialogs regressed.

**Recommended solution:** Explicitly surface Unsupported/NotRequired and complete requests deterministically. Implement browser permission/service-specific requests only for supported capabilities, respecting user gestures/secure contexts; define desktop OS-specific policy instead of blindly granting everything.

**Risks / limits:** Global desktop Granted would be wrong for macOS TCC and sandbox permissions. Browser APIs differ substantially and cannot emulate every mobile permission.

**Evidence:**
- Read all desktop/js/wasm state implementations and all feature registration actuals; no native/browser service call exists.
- Upstream #31 has a 2024 comment identifying desktop perpetual-denial behavior; the closed issue is not proof of completion.

**Required regression tests:**
- Desktop/macOS sandbox behavior; browser camera/microphone/location/notifications with unavailable API, insecure context and denial.
- Every stub path completes once with a documented unsupported result rather than silently doing nothing.

**Dependencies:** PERM-016.

**History:** https://github.com/MohamedRejeb/Calf/issues/31

<a id="perm-018"></a>
### PERM-018 — Android LocationTracker never updates its public location states

**High · confirmed-source · effort M**

**Locations:**
- `calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:37-39,58-108,124-148` — `onLocationResult/locationState/extendedLocationState`

**Root cause:** onLocationResult constructs data and sends it to two private conflated channels. Neither channel is consumed/exposed, and the two MutableState fields are only initialized, never assigned after construction.

**Impact:** Even when the OS delivers real fixes, public locationState stays (0,0) and extended state remains all-zero with timestamp0. Tracking wastes work without producing a usable result; initial coordinates also masquerade as a real location.

**Recommended solution:** Route validated updates into public observable state (prefer a single coherent source for simple/extended views), represent no-fix explicitly, remove unused channels or implement a lifecycle-owned consumer, and add regression tests before publishing geo.

**Risks / limits:** The module has no publication plugin and appears to be a prototype. Changing non-null State types requires an additive state/result API or compatibility bridge; do not advertise ready geolocation until verified.

**Evidence:**
- Search of all geo source finds channel sends but no receives and no _locationState.value/_extendedLocationState.value assignments.
- The Android file is unchanged since commit2492c2a (2023-12-02); historical #26/#40 are not evidence of a complete implementation.

**Required regression tests:**
- Inject one and multiple Android LocationResult values and assert both observable states update consistently.
- No-fix/null lastLocation, stop/dispose, no duplicate emissions, initial unavailable state and recomposition observation.

**Dependencies:** None.

**History:** https://github.com/MohamedRejeb/Calf/issues/26, https://github.com/MohamedRejeb/Calf/pull/40

<a id="perm-019"></a>
### PERM-019 — Non-Android geolocation trackers only print messages and report fabricated zero coordinates

**Medium · confirmed-source · effort XL**

**Locations:**
- `calf-geo/src/iosMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt:7-40` — `LocationTracker`
- `calf-geo/src/desktopMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:7-40` — `LocationTracker`
- `calf-geo/src/jsMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.js.kt:7-40` — `LocationTracker`
- `calf-geo/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.wasmJs.kt:7-40` — `LocationTracker`
- `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt:6-14` — `expect LocationTracker`

**Root cause:** All four actual implementations have println-only start/stop and constant all-zero states. The common expect class declares no constructor/factory for shared-code creation or binding.

**Impact:** Compilation is not platform support: no CoreLocation, navigator.geolocation or desktop provider runs, and consumers cannot distinguish unsupported/no-fix from a position at0,0. Shared initialization is also incomplete.

**Recommended solution:** Mark geo experimental/unavailable, provide a common lifecycle/factory and explicit unavailable result, then implement target backends in planned increments or remove unsupported target claims until complete.

**Risks / limits:** Do not add a fake always-success default to satisfy a multiplatform type. A portable desktop location source may not exist; Unsupported can be the correct result.

**Evidence:**
- All four files were read in full and are equivalent except file/source-set path; startTracking/stopTracking contain only println.
- No geo publication plugin is applied in baseline build.gradle.kts.

**Required regression tests:**
- Compile a common-code usage sample; verify supported/unsupported outcome on every target.
- iOS usage keys/denial/accuracy, browser secure contexts/watch cancellation, desktop provider absence.

**Dependencies:** PERM-018.

**History:** https://github.com/MohamedRejeb/Calf/issues/26, https://github.com/MohamedRejeb/Calf/pull/40

<a id="perm-020"></a>
### PERM-020 — Android LocationTracker rebinding has no ownership boundary or coroutine cleanup

**Medium · confirmed-source · effort M**

**Locations:**
- `calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:31-55,105-121` — `bind/lifecycle observer/trackerScope/stopTracking`

**Root cause:** Every bind replaces a shared client and adds an observer to the supplied lifecycle without removing previous observers. Old observers dereference the current client on destruction. isStarted survives destruction; scope/channels are never cancelled/closed and callbacks do not check active generation.

**Impact:** Destroying an old lifecycle after rebinding can stop/null the new client. Repeated binds and in-flight callbacks can retain tracker/owner references or deliver after stop; scope work has no explicit shutdown contract.

**Recommended solution:** Have one bound-owner token/observer/client at a time, detach/remove old updates on rebind, use a cancellable lifecycle-owned scope, clear active state on destruction and reject late callbacks by generation. Remove unused fragmentManager argument through a compatibility deprecation.

**Risks / limits:** Source proves cross-owner interference; actual leak duration depends on FusedLocation callbacks and Android lifecycle GC. Do not close reusable channels without defining restart semantics.

**Evidence:**
- Observer at lines49-54 captures the tracker and uses mutable locationProviderClient, not the client/owner it was created for.
- trackerScope has no cancel call and channels no close/consume calls anywhere in geo.

**Required regression tests:**
- Bind A,start,bind B,destroy A: B continues; destroy B stops exactly once.
- Repeated bind/start/stop, queued callback after stop, destruction/restart, weak-reference/leak checks.

**Dependencies:** PERM-018.

**History:** https://github.com/MohamedRejeb/Calf/pull/40

<a id="perm-021"></a>
### PERM-021 — Android LocationTracker suppresses missing-permission checks and ignores provider failures

**High · confirmed-source · effort L**

**Locations:**
- `calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:41-46,111-121` — `bind/startTracking/stopTracking`
- `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt:7-10` — `permission placeholder/startTracking`

**Root cause:** startTracking is suspend but performs no permission request/check, ignores the returned Google Task and sets isStarted before registering. bind repeats the unchecked request when started. Null/unbound clients silently do nothing; null Looper assumes a suitable caller thread.

**Impact:** Missing/revoked permissions can throw or fail, unavailable Play Services/settings go unreported, and a successful return does not mean tracking started. A caller using a background coroutine can violate the null-Looper precondition.

**Recommended solution:** Inject/check permissions explicitly, await/map registration success/failure, require/main-dispatch an explicit Looper, validate bind/start order and expose unavailable/permission/error states. Roll back active state on failure; handle cancellation without leaking an update subscription.

**Risks / limits:** Permission checks are still subject to TOCTOU revocation, so catch native security failures as well. Introducing automatic background permission escalation would be inappropriate; start should request only documented foreground capabilities.

**Evidence:**
- Both registration sites suppress MissingPermission; the comment saying permission failures stop execution has no implementation.
- No await or Task success/failure listener exists in the file.

**Required regression tests:**
- Denied/revoked/coarse-only permissions, unbound client, no Play Services/location settings off, failed registration/removal Task.
- Start from main/background, cancellation during registration, duplicate starts and recovery after errors.

**Dependencies:** PERM-018, PERM-020.

**History:** https://github.com/MohamedRejeb/Calf/pull/40

<a id="perm-022"></a>
### PERM-022 — Android geo data treats missing accuracy/speed/bearing/altitude as real zero measurements

**Medium · confirmed-source · effort M**

**Locations:**
- `calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:61-103` — `onLocationResult`
- `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/ExtendedLocation.kt:3-8` — `ExtendedLocation`
- `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/Location.kt:9-11` — `Location`

**Root cause:** Accuracy nullability is chosen only by SDK>=26; hasSpeedAccuracy/hasBearingAccuracy/hasVerticalAccuracy are never consulted. hasAccuracy, hasSpeed, hasBearing and hasAltitude are also ignored; Android getter defaults can become false physical measurements.

**Impact:** Consumers can interpret absent metadata as0 error/perfect accuracy, stationary speed, north bearing or sea-level altitude. This becomes externally visible once PERM-018 wires state delivery.

**Recommended solution:** Check every native has* flag; preserve absence in a versioned/additive measurement model, distinguish course/bearing from device heading, and document timestamp, units and stale-fix policy.

**Risks / limits:** Making currently non-null values nullable can break callers. Avoid simply substituting NaN without a documented contract; keep API26 guards for newer getters.

**Evidence:**
- API-level guards exist for three new getters, but no has* method appears anywhere in onLocationResult.

**Required regression tests:**
- Construct Android Locations with each metadata flag independently absent/present on API23/26+.
- True zero vs missing value, coarse/stale/mock fixes, negative altitude, unit and epoch checks.

**Dependencies:** PERM-018.

**History:** https://github.com/MohamedRejeb/Calf/pull/40

<a id="perm-023"></a>
### PERM-023 — Specify and test the numerical domain and undefined-bearing policy of LatLng

**Low · improvement · effort S**

**Locations:**
- `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LatLng.kt:11-34,44-79` — `LatLng/distanceTo/getAngleTo`

**Root cause:** Coordinates accept nonfinite/out-of-range values, the haversine intermediate is not explicitly clamped, and bearing of coincident/antipodal points has no undefined policy. Distance is spherical kilometers while Location accuracy uses meters; rounding defaults to10 degrees.

**Impact:** Invalid input propagates NaN or misleading coordinates and callers can misuse distance/bearing units/meaning. A numerical domain violation from valid antipodes was NOT reproduced in5,000,000 seeded JVM cases; this is contract hardening, not a confirmed valid-input NaN bug.

**Recommended solution:** Document valid ranges, unit distinctions, spherical model error and undefined bearings; add validated/normalized factories and finite/domain checks as compatible additions, consider clamping the haversine intermediate, and benchmark before changing math.

**Risks / limits:** Constructor validation/normalization changes existing data-class behavior and equality. Do not claim geodesic-grade WGS84 accuracy from the6371km spherical approximation.

**Evidence:**
- Actual LatLng passed zero-distance, quarter-equator, north/east bearing and dateline tests on JVM;5,000,000 seeded antipodal trials found no NaN.

**Required regression tests:**
- Identical/cardinal/dateline/poles/antipodes, very close points, nonfinite/out-of-range data.
- Properties symmetry/distance bounds, rounded0..350 vs unrounded[0,360), precision across JVM/JS/Wasm/Native.

**Dependencies:** None.

<a id="perm-024"></a>
### PERM-024 — Storage guidance asks for all-files access that WriteStorage never requests or verifies

**Medium · risk · effort S**

**Locations:**
- `docs/permissions.md:162-174` — `Write Storage Android example`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt:15-22` — `registerWriteStoragePermission`
- `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt:118-126` — `getPermissionStatus`

**Root cause:** Docs add MANAGE_EXTERNAL_STORAGE with a ScopedStorage lint suppression, but WriteStorage only maps WRITE_EXTERNAL_STORAGE through API28. On newer OS versions it becomes an empty mapping/Granted; special all-files settings and Environment.isExternalStorageManager are not used.

**Impact:** Consumers can copy an overbroad, Play-policy-sensitive permission while wrongly assuming the library requested/verified all-files access. The manifest entry alone does not confer access. This is misleading guidance and least-privilege risk, not a demonstrated data-exfiltration vulnerability.

**Recommended solution:** Remove the all-files permission from ordinary storage examples; explain app-scoped storage/SAF/media permissions and modern scoped-storage limits. If an all-files API is ever added, make it separate, explicit and policy-aware.

**Risks / limits:** Legacy apps targeting old storage models need a migration explanation, not blanket claims that no permission is required on every Android29+ combination. Coordinate with sample least-privilege finding rather than duplicate it.

**Evidence:**
- Manifest recommendation and implementation do not refer to the same permission.
- Historical #184/#195/#263/#386 show prior storage-version issues; API-range behavior was intentional and should not be mistaken for all-files authorization.

**Required regression tests:**
- API28 legacy permission, API29 legacy/scoped target modes, API30+ app-scoped/SAF and all-files absent/present.
- Verify docs examples request the least permissions needed and no Granted result is described as unrestricted disk access.

**Dependencies:** None.

**History:** https://github.com/MohamedRejeb/Calf/issues/184, https://github.com/MohamedRejeb/Calf/pull/195, https://github.com/MohamedRejeb/Calf/pull/263, https://github.com/MohamedRejeb/Calf/issues/386

## Historical issue/decision reconciliation

Raw public metadata is preserved under `docs/migration/upstream-metadata/` (`issues.json`, `pull-requests.json`, `issue-comments.json`, reviews). It is evidence, not maintainer instructions. These selected reports and relevant comments were read; long external videos/attachments and unavailable platform behavior were not independently reproduced. Closed reports below are not automatically reopened; the new PERM issue is scoped to a specific remaining implementation cause.

| Upstream record / commit | What history establishes | Current implementation decision / residual work |
|---|---|---|
| #26 / #40; `2492c2a` (2023-12-02) | Geo support requested; initial Android source added. Issue checklist originally had all4 targets unchecked. | Android tracker file has no later functional change in follow-history; public states still disconnected and other actuals stubs (`018`–`022`). Closure is not completeness. |
| #31 / #25 | Permissions Android/iOS support; web left unchecked. A2024 comment explicitly reports desktop permanently denied. | Nonmobile stubs remain (`017`); don't infer desktop permissions are all automatically granted. |
| #44 / #62 | Call permission requested and added. | CALL_PHONE mapping exists; iOS no-op means no permission gate, not call execution. Sample manifest mismatch is owned by sample reviewer. |
| #78 / #181 / #182; #382 / #384 | Contacts/OTP requested; read then write contacts permissions added. | Both authorization names exist, no contact retrieval/OTP implementation. #78 is broader than adding a permission. |
| #150 / #152 | iOS notification snapshot crash reported with Kotlin2.0.10/Compose1.6.11. | State assignment now on Main, but user callbacks lack that guarantee (`007`). Do not assert the old exact crash persists. |
| #154 / #156 / #229 / #244 / #258 / #276 / #282 / #300 | Repeated rationale/not-determined inversions, temporary regressions and fixes across releases. | Current shared gate is Granted→true, Denied(true)→false, Denied(false)→request; changing it globally would be dangerous. Background upgrade is its own incompatible state transition (`009`); richer model `016`. |
| #175 / #284 / #312 | Questions about permanent denial and settings routing; later comments advise settings on rationale=true. | That convention is not universally equivalent to Android permanent denial. Settings method exists, separate from request; notification settings routes improved. |
| #176 / #200; `5a1dfc4` | IDE preview failed through findActivity. | LocalInspectionMode now avoids Activity lookup. Preview still hardcodes granted/empty state, a low-risk modeling limitation rather than runtime evidence. |
| #177 / #179 | Proposed replacing Boolean callback with PermissionStatus; maintainer explicitly rejected an unnecessary breaking change. | Keep compatibility callback while adding a richer optional API (`007`,`016`). Current user callback precedes refresh on iOS. |
| #168 / #171; #191 | Pre33 notification behavior and RemoteNotification's iOS-only semantics clarified. | API33 guard and documented Android RemoteNotification no-op are intentional; status does not verify notification channel switches or delivery. |
| #184 / #195 / #263; `ea8145e` | Storage reported granted incorrectly; mappings changed by SDK. | Legacy read through32/write through28 is intentional. Do not treat it as MANAGE_EXTERNAL_STORAGE authorization (`024`) or remove crash guards. |
| #205 / #339; `0788c1a`,`527cb35` | CoreBluetooth authorization/hardware distinction, iOS13 detection and delayed NotDetermined fix; author reported common real-device scenarios working. | Preserve structured version check/guard. Delegation/request lifetime edge cases remain risks needing GC/device tests (`014`). |
| #248 / #422; `9a33931` | iOS multi-state previously threw NotImplementedError; launch loop added in2026. | The throw is no longer present, but concurrent singleton-result semantics remain (`008`). |
| #281 / #298; `e2a5622`,`f329c3a` | Android background mapping added with API29 guard. | Mapping alone is not correct fine/coarse/background request orchestration (`004`). |
| #313 / #331 / #411; `083dafa` | iOS lacked resume state refresh, later report still notes returning from settings. | Observer exists but only refreshes cached denial; grant→revoke cases must be handled (`006`). #411's denied→grant report does not alone prove this exact residual cause. |
| #315 / #316; `003803b` | Wi-Fi names and iOS local-network probe added. | Names now exist; probe is not a passive authorization query or Wi-Fi-control entitlement (`013`). |
| #325 | Consumer expected a singular multiple-state status. | Existing aggregate/per-member API is intentional and works as a structural model; no new duplicate bug issue. |
| #352 | Native IrLinkageError after incompatible dependency update; comments recommend compatibility table. | Consumer Compose/Kotlin compatibility is a build/integration risk; old stack is not evidence baseline versions currently fail. |
| #382 | Contributor used a mismatched system Gradle; advised to use wrapper. | New docs must make wrapper/toolchain setup explicit; build reviewer owns verification. |
| #386 / #413; `9c35fa2` | Android10 empty-string bulk array crash with ReadStorage+WriteStorage. | Filtering is present; all-filtered callback silently omitted (`003`). |
| #398 / #401 / #432; `f3bf64a` | SMS permission names added. | Read/Receive deny on iOS; Send has no gate. There is no arbitrary SMS read or silent send functionality on iOS. |
| #421; `2ba4d5b`,`7d382c6`,`03e2f2b`,`292f66f`,`275e7d3` | Modularization, enum→open class singletons, background split, calendar status fix. | Preserve naming/dependency history. Registry alias ambiguity (`002`), WhenInUse upgrade (`009`) and calendar request keys (`011`) remain. Native helper duplicate-class fixes `5eac9b9`/`f7d7cb1` explain separate AV classes. |
| #522 / #523; `93b6af2`,`4644603` | Android notification manifest merge documented; APNs registration added. | One actual notification manifest is present. Already-granted APNs path is incomplete (`015`). |

## Remediation sequence and dependency notes

1. **Regression harness and safety disclosure:** explicitly label nonmobile permissions/geo as incomplete; preserve the original baseline. Add adapter tests for registry aliasing, callback completion, iOS status gates and geo update routing. Don't publish a release/package as a side effect of this audit.
2. **High-confidence, bounded correctness:** `PERM-002` result mapping, `003` completion, `005` callback freshness, `009` background transition and `011` calendar availability/keys. Test Android native permission prerequisites (`004`) in parallel on a device matrix.
3. **Request lifetime foundation:** `007` main/disposal behavior and `010` terminal callback semantics; `013` Wi-Fi passive-vs-interactive separation. Only then make lifecycle refresh unconditional (`006`) and build a serial/aggregate iOS coordinator (`008`). Add strict BT lifetime tests (`014`) without replacing working flows blindly.
4. **Capability/API compatibility:** richer additive state (`016`) supports partial contacts/photos/accuracy, deliberate nonmobile unsupported behavior (`017`), least-privilege calendar (`012`) and registration transparency (`015`). Clean up misleading storage docs (`024`).
5. **Separate geo completion project:** first wire observable updates (`018`), then ownership/error/cancellation (`020`,`021`) and valid metadata (`022`). Establish a common creation/availability API before implementing other targets (`019`). Numerical contract/tests (`023`) are lower priority. Require fresh product-level authorization before any release/package publication.

Effort labels are planning estimates (S bounded change, M moderate integration, L cross-platform state work, XL new backends), not time promises. Native-platform access is an external test dependency, not a reason to claim fixes verified from source alone.

## Complete baseline file review coverage

Each row means the **entire file** was read, not only the listed declaration. Ranges are1..final logical line. For registration files, every singleton/getter/expect/actual function is included. The declaration list is an index, not a substitute for the module execution-flow review. Build scripts are reviewed for all plugins/dependencies; the only manifest is reviewed in full. Comment-only umbrella source is intentionally recorded. SHA256 prefixes identify the exact content; Git history preserves the full blobs.

| Baseline file | Lines | SHA256 prefix | Reviewed declarations / role |
|---|---:|---|---|
| `calf-geo/build.gradle.kts` |1–14| `06213339a729` | compose convention; foundation implementation; Android appcompat/lifecycle-extensions/Play Services; NOT published |
| `calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt` |1–150| `c149b3406b9e` | LocationTracker:27; bind:41; onDestroy:51; onLocationResult:58; startTracking:112; stopTracking:119; locationState:125; extendedLocationState:148 |
| `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/Altitude.kt` |1–6| `93e50d1948fd` | Altitude:3 |
| `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/Azimuth.kt` |1–6| `2ea1ac122525` | Azimuth:3 |
| `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/ExtendedLocation.kt` |1–9| `ccc1693e770a` | ExtendedLocation:3 |
| `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LatLng.kt` |1–81| `a115448ca95c` | LatLng:11; distanceTo:22; getAngleTo:44; toRadians:70; toDegree:74 |
| `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/Location.kt` |1–12| `1ad48420a0cd` | Location:9 |
| `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt` |1–15| `f97e623f47b0` | LocationTracker:6; startTracking:9; stopTracking:10; locationState:12; extendedLocationState:14 |
| `calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/Speed.kt` |1–6| `1972cd52c399` | Speed:3 |
| `calf-geo/src/desktopMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt` |1–41| `4ae34b9b6e72` | LocationTracker:7; startTracking:8; stopTracking:12; locationState:17; extendedLocationState:40; println-only tracker / constant State |
| `calf-geo/src/iosMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt` |1–41| `4ae34b9b6e72` | LocationTracker:7; startTracking:8; stopTracking:12; locationState:17; extendedLocationState:40; println-only tracker / constant State |
| `calf-geo/src/jsMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.js.kt` |1–41| `4ae34b9b6e72` | LocationTracker:7; startTracking:8; stopTracking:12; locationState:17; extendedLocationState:40; println-only tracker / constant State |
| `calf-geo/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.wasmJs.kt` |1–41| `4ae34b9b6e72` | LocationTracker:7; startTracking:8; stopTracking:12; locationState:17; extendedLocationState:40; println-only tracker / constant State |
| `calf-permissions/background-location/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/background-location/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/BackgroundLocationPermissions.android.kt` |1–13| `f8d72d503c2f` | registerBackgroundLocationPermission:5 |
| `calf-permissions/background-location/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/BackgroundLocationPermissions.kt` |1–12| `01c5e52d1399` | Permission.Companion.BackgroundLocation:3; registerBackgroundLocationPermission:6; PermissionBackgroundLocation:8 |
| `calf-permissions/background-location/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/BackgroundLocationPermissions.desktop.kt` |1–3| `39a890438216` | registerBackgroundLocationPermission:3; all register bodies Unit |
| `calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/BackgroundLocationPermissions.ios.kt` |1–10| `c465cff4dcfa` | registerBackgroundLocationPermission:6 |
| `calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BackgroundLocationPermissionHelper.kt` |1–74| `5f395408105a` | BackgroundLocationPermissionHelper:13; launchPermissionRequest:26; getPermissionStatus:37; status:38; getCurrentAuthorizationStatus:55; BackgroundLocationManagerDelegate:59; locationManager:62 |
| `calf-permissions/background-location/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/BackgroundLocationPermissions.js.kt` |1–3| `39a890438216` | registerBackgroundLocationPermission:3; all register bodies Unit |
| `calf-permissions/background-location/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/BackgroundLocationPermissions.wasmJs.kt` |1–3| `39a890438216` | registerBackgroundLocationPermission:3; all register bodies Unit |
| `calf-permissions/bluetooth/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/bluetooth/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/BluetoothPermissions.android.kt` |1–42| `b8b0d764bbe3` | registerBluetoothLePermission:5; registerBluetoothScanPermission:14; registerBluetoothConnectPermission:24; registerBluetoothAdvertisePermission:34 |
| `calf-permissions/bluetooth/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/BluetoothPermissions.kt` |1–45| `cc5562c8e53f` | Permission.Companion.BluetoothLe:3; Permission.Companion.BluetoothScan:6; Permission.Companion.BluetoothConnect:9; Permission.Companion.BluetoothAdvertise:12; registerBluetoothLePermission:15; registerBluetoothScanPermission:17; registerBluetoothConnectPermission:19; registerBluetoothAdvertisePermission:21; PermissionBluetoothLe:23; PermissionBluetoothScan:29; PermissionBluetoothConnect:35; PermissionBluetoothAdvertise:41 |
| `calf-permissions/bluetooth/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/BluetoothPermissions.desktop.kt` |1–9| `f5983fa9ab19` | registerBluetoothLePermission:3; registerBluetoothScanPermission:5; registerBluetoothConnectPermission:7; registerBluetoothAdvertisePermission:9; all register bodies Unit |
| `calf-permissions/bluetooth/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/BluetoothPermissions.ios.kt` |1–28| `e117cb063532` | registerBluetoothLePermission:6; registerBluetoothScanPermission:12; registerBluetoothConnectPermission:18; registerBluetoothAdvertisePermission:24 |
| `calf-permissions/bluetooth/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BluetoothPermissionHelper.kt` |1–130| `f35887cb574c` | BluetoothPermissionHelper:24; launchPermissionRequest:36; resolveAndCleanup:53; centralManagerDidUpdateState:65; getPermissionStatus:100 |
| `calf-permissions/bluetooth/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/BluetoothPermissions.js.kt` |1–9| `f5983fa9ab19` | registerBluetoothLePermission:3; registerBluetoothScanPermission:5; registerBluetoothConnectPermission:7; registerBluetoothAdvertisePermission:9; all register bodies Unit |
| `calf-permissions/bluetooth/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/BluetoothPermissions.wasmJs.kt` |1–9| `f5983fa9ab19` | registerBluetoothLePermission:3; registerBluetoothScanPermission:5; registerBluetoothConnectPermission:7; registerBluetoothAdvertisePermission:9; all register bodies Unit |
| `calf-permissions/build.gradle.kts` |1–20| `416a1071e662` | compose + publication; API exports core and10 feature projects |
| `calf-permissions/calendar/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/calendar/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/CalendarPermissions.android.kt` |1–21| `185680572edc` | registerReadCalendarPermission:5; registerWriteCalendarPermission:14 |
| `calf-permissions/calendar/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/CalendarPermissions.kt` |1–23| `3c7179267cd5` | Permission.Companion.ReadCalendar:3; Permission.Companion.WriteCalendar:6; registerReadCalendarPermission:9; registerWriteCalendarPermission:11; PermissionReadCalendar:13; PermissionWriteCalendar:19 |
| `calf-permissions/calendar/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/CalendarPermissions.desktop.kt` |1–5| `5e6a89b64584` | registerReadCalendarPermission:3; registerWriteCalendarPermission:5; all register bodies Unit |
| `calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/CalendarPermissions.ios.kt` |1–16| `980f0541b624` | registerReadCalendarPermission:6; registerWriteCalendarPermission:12 |
| `calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionHelper.kt` |1–45| `bfd1cd2d5326` | CalendarPermissionHelper:13; launchPermissionRequest:14; getPermissionStatus:26; status:27 |
| `calf-permissions/calendar/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/CalendarPermissions.js.kt` |1–5| `5e6a89b64584` | registerReadCalendarPermission:3; registerWriteCalendarPermission:5; all register bodies Unit |
| `calf-permissions/calendar/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/CalendarPermissions.wasmJs.kt` |1–5| `5e6a89b64584` | registerReadCalendarPermission:3; registerWriteCalendarPermission:5; all register bodies Unit |
| `calf-permissions/camera/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/camera/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/CameraPermissions.android.kt` |1–12| `7dcffe95d854` | registerCameraPermission:5 |
| `calf-permissions/camera/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/CameraPermissions.kt` |1–12| `4bb15ceeee87` | Permission.Companion.Camera:3; registerCameraPermission:6; PermissionCamera:8 |
| `calf-permissions/camera/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/CameraPermissions.desktop.kt` |1–3| `f55cfa73b271` | registerCameraPermission:3; all register bodies Unit |
| `calf-permissions/camera/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/CameraPermissions.ios.kt` |1–11| `36fb8443d879` | registerCameraPermission:7 |
| `calf-permissions/camera/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/AVCameraPermissionHelper.kt` |1–52| `2eaaf912ad9e` | AVCameraPermissionHelper:14; launchPermissionRequest:18; getPermissionStatus:30; status:31; getCurrentAuthorizationStatus:49 |
| `calf-permissions/camera/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/CameraPermissions.js.kt` |1–3| `f55cfa73b271` | registerCameraPermission:3; all register bodies Unit |
| `calf-permissions/camera/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/CameraPermissions.wasmJs.kt` |1–3| `f55cfa73b271` | registerCameraPermission:3; all register bodies Unit |
| `calf-permissions/contacts/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/contacts/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/ContactPermissions.android.kt` |1–21| `157c99e2c24f` | registerReadContactsPermission:5; registerWriteContactsPermission:14 |
| `calf-permissions/contacts/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.kt` |1–23| `adbc0d28045a` | Permission.Companion.ReadContacts:3; Permission.Companion.WriteContacts:6; registerReadContactsPermission:9; registerWriteContactsPermission:11; PermissionReadContacts:13; PermissionWriteContacts:19 |
| `calf-permissions/contacts/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/ContactPermissions.desktop.kt` |1–5| `dcc9c6635180` | registerReadContactsPermission:3; registerWriteContactsPermission:5; all register bodies Unit |
| `calf-permissions/contacts/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.ios.kt` |1–16| `b70a1d325e67` | registerReadContactsPermission:6; registerWriteContactsPermission:12 |
| `calf-permissions/contacts/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/ContactPermissionHelper.kt` |1–43| `a7fd66518e61` | ContactPermissionHelper:12; launchPermissionRequest:13; getPermissionStatus:25; getCurrentAuthorizationStatus:40 |
| `calf-permissions/contacts/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.js.kt` |1–5| `dcc9c6635180` | registerReadContactsPermission:3; registerWriteContactsPermission:5; all register bodies Unit |
| `calf-permissions/contacts/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.wasmJs.kt` |1–5| `dcc9c6635180` | registerReadContactsPermission:3; registerWriteContactsPermission:5; all register bodies Unit |
| `calf-permissions/core/build.gradle.kts` |1–14| `0b0a2bbb882a` | compose + publication; foundation API; Android activity-compose implementation |
| `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt` |1–39| `37d5fabdbee9` | AndroidPermissionMapping:11; AndroidPermissionRegistry:24; register:27; getMapping:31; findByAndroidString:34 |
| `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt` |1–154| `d4b1a6121275` | rememberMutableMultiplePermissionsState:27; rememberMutablePermissionsState:63; MutableMultiplePermissionsState:111; permissions:115; revokedPermissions:117; allPermissionsGranted:121; shouldShowRationale:126; launchMultiplePermissionRequest:130; updatePermissionsStatus:144 |
| `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt` |1–144| `e59fea17d541` | rememberMutablePermissionState:34; MutablePermissionStateImpl:79; status:88; launchPermissionRequest:90; openAppSettings:104; refreshPermissionStatus:114; getPermissionStatus:118; createAppNotificationsIntent:130; supportsNotificationSettings:135; createAppSettingsIntent:138 |
| `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/PermissionsUtil.android.kt` |1–114| `befd665f5b91` | PermissionLifecycleCheckerEffect:22; PermissionsLifecycleCheckerEffect:53; Context.findActivity:83; Context.checkPermission:92; Activity.shouldShowRationale:97; Permission.toAndroidPermission:101; Permission.isAlwaysGranted:110; getPermissionFromAndroidPermission:113 |
| `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/SmsPermissions.android.kt` |1–30| `5d5dceaa370a` | registerReadSmsPermission:5; registerReceiveSmsPermission:14; registerSendSmsPermission:23 |
| `calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt` |1–42| `0cc9bb16daea` | registerReadStoragePermission:5; registerWriteStoragePermission:15; registerReadAudioPermission:25; registerCallPermission:35 |
| `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/MultiplePermissionsState.kt` |1–88| `ddd5bfa3b0ad` | rememberMultiplePermissionsState:20; rememberPreviewMultiplePermissionState:34; permissions:36; revokedPermissions:37; allPermissionsGranted:38; shouldShowRationale:39; launchMultiplePermissionRequest:40; MultiplePermissionsState:54; permissions:59; revokedPermissions:64; allPermissionsGranted:69; shouldShowRationale:74; launchMultiplePermissionRequest:87 |
| `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.kt` |1–46| `ffe9bb3e7959` | rememberMutableMultiplePermissionsState:18; MutableMultiplePermissionsState:32; permissions:35; revokedPermissions:37; allPermissionsGranted:39; shouldShowRationale:41; launchMultiplePermissionRequest:43; updatePermissionsStatus:45 |
| `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.kt` |1–36| `c3c7f7adfe05` | rememberMutablePermissionState:18; MutablePermissionState:34; refreshPermissionStatus:35 |
| `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionState.kt` |1–110| `39ed62ebbe44` | rememberPermissionState:20; rememberPreviewPermissionState:34; status:39; launchPermissionRequest:40; openAppSettings:41; PermissionState:55; status:64; launchPermissionRequest:77; openAppSettings:85; Permission:96; equals:97; hashCode:101; toString:105 |
| `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionsUtil.kt` |1–54| `9bae3e8880ae` | ExperimentalPermissionsApi:7; PermissionStatus:15; Granted:16; Denied:17; shouldShowRationale:18 |
| `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.kt` |1–34| `28c021fbf32d` | Permission.Companion.ReadSms:3; Permission.Companion.ReceiveSms:6; Permission.Companion.SendSms:9; registerReadSmsPermission:12; registerReceiveSmsPermission:14; registerSendSmsPermission:16; PermissionReadSms:18; PermissionReceiveSms:24; PermissionSendSms:30 |
| `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/StoragePermissions.kt` |1–45| `50b084d7f5c0` | Permission.Companion.ReadStorage:3; Permission.Companion.WriteStorage:6; Permission.Companion.ReadAudio:9; Permission.Companion.Call:12; registerReadStoragePermission:15; registerWriteStoragePermission:17; registerReadAudioPermission:19; registerCallPermission:21; PermissionReadStorage:23; PermissionWriteStorage:29; PermissionReadAudio:35; PermissionCall:41 |
| `calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.desktop.kt` |1–83| `763107ffb6d7` | rememberMutableMultiplePermissionsState:22; MutableMultiplePermissionsState:50; permissions:54; revokedPermissions:56; allPermissionsGranted:60; shouldShowRationale:65; launchMultiplePermissionRequest:69; updatePermissionsStatus:73 |
| `calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.desktop.kt` |1–55| `a3e5bfd25366` | rememberMutablePermissionState:22; MutablePermissionStateImpl:40; status:44; launchPermissionRequest:46; openAppSettings:48; refreshPermissionStatus:50; getPermissionStatus:52 |
| `calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/SmsPermissions.desktop.kt` |1–7| `eafb4f3f611d` | registerReadSmsPermission:3; registerReceiveSmsPermission:5; registerSendSmsPermission:7; all register bodies Unit |
| `calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.desktop.kt` |1–9| `63ee7a8d11e8` | registerReadStoragePermission:3; registerWriteStoragePermission:5; registerReadAudioPermission:7; registerCallPermission:9; all register bodies Unit |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.ios.kt` |1–104| `5d136f3d672a` | rememberMutableMultiplePermissionsState:18; rememberMutablePermissionsState:39; MutableMultiplePermissionsState:69; permissions:73; revokedPermissions:75; allPermissionsGranted:79; shouldShowRationale:84; launchMultiplePermissionRequest:88; updatePermissionsStatus:94 |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt` |1–113| `6f1ee660ffbe` | rememberMutablePermissionState:33; MutablePermissionStateImpl:63; status:71; launchPermissionRequest:77; openAppSettings:86; isIOS16OrAbove:100; refreshPermissionStatus:106 |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionsUtil.ios.kt` |1–71| `7fba3fac4ff4` | PermissionLifecycleCheckerEffect:15; PermissionsLifecycleCheckerEffect:46 |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.ios.kt` |1–23| `9a31503a5825` | registerReadSmsPermission:7; registerReceiveSmsPermission:13; registerSendSmsPermission:19 |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/StoragePermissions.ios.kt` |1–28| `39e75e6f2ea1` | registerReadStoragePermission:6; registerWriteStoragePermission:12; registerReadAudioPermission:18; registerCallPermission:24 |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/GrantedPermissionHelper.kt` |1–14| `fbfda761520d` | GrantedPermissionHelper:6; launchPermissionRequest:7; getPermissionStatus:12 |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/NotGrantedPermissionHelper.kt` |1–14| `54b75e196f80` | NotGrantedPermissionHelper:6; launchPermissionRequest:7; getPermissionStatus:12 |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionDelegateRegistry.kt` |1–19| `62f529836ba8` | PermissionDelegateRegistry:5; register:8; getDelegate:12 |
| `calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionHelper.kt` |1–32| `d97d94cb5ddf` | PermissionHelper:6; launchPermissionRequest:7; getPermissionStatus:10; PermissionHelper.handleLaunchPermissionRequest:16 |
| `calf-permissions/core/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.js.kt` |1–82| `f7c9f55ea195` | rememberMutableMultiplePermissionsState:21; MutableMultiplePermissionsState:49; permissions:53; revokedPermissions:55; allPermissionsGranted:59; shouldShowRationale:64; launchMultiplePermissionRequest:68; updatePermissionsStatus:72 |
| `calf-permissions/core/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.js.kt` |1–54| `5a2afe5939d6` | rememberMutablePermissionState:22; MutablePermissionStateImpl:40; status:43; launchPermissionRequest:45; openAppSettings:47; refreshPermissionStatus:49; getPermissionStatus:51 |
| `calf-permissions/core/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.js.kt` |1–7| `eafb4f3f611d` | registerReadSmsPermission:3; registerReceiveSmsPermission:5; registerSendSmsPermission:7; all register bodies Unit |
| `calf-permissions/core/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/StoragePermissions.js.kt` |1–9| `63ee7a8d11e8` | registerReadStoragePermission:3; registerWriteStoragePermission:5; registerReadAudioPermission:7; registerCallPermission:9; all register bodies Unit |
| `calf-permissions/core/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.wasmJs.kt` |1–82| `282429b16b0f` | rememberMutableMultiplePermissionsState:21; MutableMultiplePermissionsState:50; permissions:53; revokedPermissions:55; allPermissionsGranted:59; shouldShowRationale:64; launchMultiplePermissionRequest:68; updatePermissionsStatus:72 |
| `calf-permissions/core/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.wasmJs.kt` |1–54| `5a2afe5939d6` | rememberMutablePermissionState:22; MutablePermissionStateImpl:40; status:43; launchPermissionRequest:45; openAppSettings:47; refreshPermissionStatus:49; getPermissionStatus:51 |
| `calf-permissions/core/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.wasmJs.kt` |1–7| `eafb4f3f611d` | registerReadSmsPermission:3; registerReceiveSmsPermission:5; registerSendSmsPermission:7; all register bodies Unit |
| `calf-permissions/core/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/StoragePermissions.wasmJs.kt` |1–9| `63ee7a8d11e8` | registerReadStoragePermission:3; registerWriteStoragePermission:5; registerReadAudioPermission:7; registerCallPermission:9; all register bodies Unit |
| `calf-permissions/gallery/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/gallery/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/GalleryPermissions.android.kt` |1–33| `9a18e40de4a9` | registerGalleryPermission:5; registerReadImagePermission:15; registerReadVideoPermission:25 |
| `calf-permissions/gallery/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/GalleryPermissions.kt` |1–34| `e3f53cff676b` | Permission.Companion.Gallery:3; Permission.Companion.ReadImage:6; Permission.Companion.ReadVideo:9; registerGalleryPermission:12; registerReadImagePermission:14; registerReadVideoPermission:16; PermissionGallery:18; PermissionReadImage:24; PermissionReadVideo:30 |
| `calf-permissions/gallery/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/GalleryPermissions.desktop.kt` |1–7| `6fb0543dd4c1` | registerGalleryPermission:3; registerReadImagePermission:5; registerReadVideoPermission:7; all register bodies Unit |
| `calf-permissions/gallery/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/GalleryPermissions.ios.kt` |1–22| `b1cb66085164` | registerGalleryPermission:6; registerReadImagePermission:12; registerReadVideoPermission:18 |
| `calf-permissions/gallery/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/GalleryPermissionHelper.kt` |1–46| `3bc3ec5adcdc` | GalleryPermissionHelper:11; launchPermissionRequest:13; getPermissionStatus:25; status:26; getCurrentAuthorizationStatus:43 |
| `calf-permissions/gallery/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/GalleryPermissions.js.kt` |1–7| `6fb0543dd4c1` | registerGalleryPermission:3; registerReadImagePermission:5; registerReadVideoPermission:7; all register bodies Unit |
| `calf-permissions/gallery/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/GalleryPermissions.wasmJs.kt` |1–7| `6fb0543dd4c1` | registerGalleryPermission:3; registerReadImagePermission:5; registerReadVideoPermission:7; all register bodies Unit |
| `calf-permissions/location/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/location/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/LocationPermissions.android.kt` |1–21| `39a659460201` | registerFineLocationPermission:5; registerCoarseLocationPermission:14 |
| `calf-permissions/location/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/LocationPermissions.kt` |1–24| `c7734004b71f` | Permission.Companion.FineLocation:3; Permission.Companion.CoarseLocation:6; registerFineLocationPermission:9; registerCoarseLocationPermission:11; PermissionFineLocation:13; PermissionCoarseLocation:19 |
| `calf-permissions/location/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/LocationPermissions.desktop.kt` |1–5| `762e7f2966bd` | registerFineLocationPermission:3; registerCoarseLocationPermission:5; all register bodies Unit |
| `calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/LocationPermissions.ios.kt` |1–17| `32db863a8f40` | registerFineLocationPermission:6; registerCoarseLocationPermission:12 |
| `calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocationPermissionHelper.kt` |1–82| `e387532e825e` | LocationPermissionHelper:15; launchPermissionRequest:28; getPermissionStatus:39; status:40; getCurrentAuthorizationStatus:60; LocationManagerDelegate:64; locationManager:67 |
| `calf-permissions/location/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/LocationPermissions.js.kt` |1–5| `762e7f2966bd` | registerFineLocationPermission:3; registerCoarseLocationPermission:5; all register bodies Unit |
| `calf-permissions/location/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/LocationPermissions.wasmJs.kt` |1–5| `762e7f2966bd` | registerFineLocationPermission:3; registerCoarseLocationPermission:5; all register bodies Unit |
| `calf-permissions/microphone/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/microphone/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MicrophonePermissions.android.kt` |1–12| `75fc0e1fc12a` | registerRecordAudioPermission:5 |
| `calf-permissions/microphone/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/MicrophonePermissions.kt` |1–12| `61a2b8536bf3` | Permission.Companion.RecordAudio:3; registerRecordAudioPermission:6; PermissionRecordAudio:8 |
| `calf-permissions/microphone/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MicrophonePermissions.desktop.kt` |1–3| `4530b5c06b8a` | registerRecordAudioPermission:3; all register bodies Unit |
| `calf-permissions/microphone/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MicrophonePermissions.ios.kt` |1–11| `35cbfa36a72e` | registerRecordAudioPermission:7 |
| `calf-permissions/microphone/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/AVMicrophonePermissionHelper.kt` |1–52| `7e7176e8b04b` | AVMicrophonePermissionHelper:14; launchPermissionRequest:18; getPermissionStatus:30; status:31; getCurrentAuthorizationStatus:49 |
| `calf-permissions/microphone/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/MicrophonePermissions.js.kt` |1–3| `4530b5c06b8a` | registerRecordAudioPermission:3; all register bodies Unit |
| `calf-permissions/microphone/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/MicrophonePermissions.wasmJs.kt` |1–3| `4530b5c06b8a` | registerRecordAudioPermission:3; all register bodies Unit |
| `calf-permissions/notifications/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/notifications/src/androidMain/AndroidManifest.xml` |1–4| `23571e3bfcca` | POST_NOTIFICATIONS consumer-manifest merge |
| `calf-permissions/notifications/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/NotificationPermissions.android.kt` |1–19| `a6995c07caa3` | registerNotificationPermission:5; registerRemoteNotificationPermission:15 |
| `calf-permissions/notifications/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/NotificationPermissions.kt` |1–23| `97284a22f347` | Permission.Companion.Notification:3; Permission.Companion.RemoteNotification:6; registerNotificationPermission:9; registerRemoteNotificationPermission:11; PermissionNotification:13; PermissionRemoteNotification:19 |
| `calf-permissions/notifications/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/NotificationPermissions.desktop.kt` |1–5| `4bff7a716e66` | registerNotificationPermission:3; registerRemoteNotificationPermission:5; all register bodies Unit |
| `calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/NotificationPermissions.ios.kt` |1–17| `fbae90758088` | registerNotificationPermission:7; registerRemoteNotificationPermission:13 |
| `calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocalNotificationPermissionHelper.kt` |1–63| `556c494cf160` | LocalNotificationPermissionHelper:15; launchPermissionRequest:18; getPermissionStatus:38; getCurrentNotificationCenter:60 |
| `calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/RemoteNotificationPermissionHelper.kt` |1–71| `bf7b888ab5ee` | RemoteNotificationPermissionHelper:19; launchPermissionRequest:22; getPermissionStatus:46; getCurrentNotificationCenter:68 |
| `calf-permissions/notifications/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/NotificationPermissions.js.kt` |1–5| `4bff7a716e66` | registerNotificationPermission:3; registerRemoteNotificationPermission:5; all register bodies Unit |
| `calf-permissions/notifications/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/NotificationPermissions.wasmJs.kt` |1–5| `4bff7a716e66` | registerNotificationPermission:3; registerRemoteNotificationPermission:5; all register bodies Unit |
| `calf-permissions/src/commonMain/kotlin/Permission.kt` |1–1| `520555194b14` | Comment-only publication placeholder; no declarations |
| `calf-permissions/wifi/build.gradle.kts` |1–10| `7e2b0eb4139b` | compose + publication; API exports permissions-core |
| `calf-permissions/wifi/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/WifiPermissions.android.kt` |1–31| `403cb73b982e` | registerWifiAccessStatePermission:5; registerWifiChangeStatePermission:14; registerWifiNearbyDevicesPermission:23 |
| `calf-permissions/wifi/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/WifiPermissions.kt` |1–34| `ef76c4ce1db5` | Permission.Companion.WifiAccessState:3; Permission.Companion.WifiChangeState:6; Permission.Companion.WifiNearbyDevices:9; registerWifiAccessStatePermission:12; registerWifiChangeStatePermission:14; registerWifiNearbyDevicesPermission:16; PermissionWifiAccessState:18; PermissionWifiChangeState:24; PermissionWifiNearbyDevices:30 |
| `calf-permissions/wifi/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/WifiPermissions.desktop.kt` |1–7| `6f92857dd095` | registerWifiAccessStatePermission:3; registerWifiChangeStatePermission:5; registerWifiNearbyDevicesPermission:7; all register bodies Unit |
| `calf-permissions/wifi/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/WifiPermissions.ios.kt` |1–22| `1d5e81b7e68d` | registerWifiAccessStatePermission:6; registerWifiChangeStatePermission:12; registerWifiNearbyDevicesPermission:18 |
| `calf-permissions/wifi/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/WifiPermissionHelper.kt` |1–118| `f51188b651b4` | WifiPermissionHelper:12; launchPermissionRequest:15; getPermissionStatus:35; status:39; LocalNetworkPermissionDelegate:59; startCheck:67; cleanupAndComplete:92; netServiceDidPublish:107; netService:111; cancel:115 |
| `calf-permissions/wifi/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/WifiPermissions.js.kt` |1–7| `6f92857dd095` | registerWifiAccessStatePermission:3; registerWifiChangeStatePermission:5; registerWifiNearbyDevicesPermission:7; all register bodies Unit |
| `calf-permissions/wifi/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/WifiPermissions.wasmJs.kt` |1–7| `6f92857dd095` | registerWifiAccessStatePermission:3; registerWifiChangeStatePermission:5; registerWifiNearbyDevicesPermission:7; all register bodies Unit |

### Supporting source reviewed outside the assigned tree

- `docs/permissions.md`: entire reference, native purpose strings, examples and compatibility claims.
- `sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/PermissionsScreen.kt`:28-permission API set compared with25 listed demo items, single request/Settings UI and camera+microphone bulk demo; not counted as a test.
- `sample/android/src/main/AndroidManifest.xml`; `sample/ios/Calf/Info.plist`; deployment overrides in `sample/ios/Calf.xcodeproj/project.pbxproj`.
- `settings.gradle.kts`; `gradle/libs.versions.toml`; `convention-plugins/src/main/kotlin/{Targets.kt,Android.kt,compose.multiplatform.gradle.kts,kotlin.multiplatform.gradle.kts}` for module inclusion, targets, SDKs and dependency/plugin behavior. Shared build/publishing/security review is owned by its dedicated report.
