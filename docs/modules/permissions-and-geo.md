# Permissions and geolocation: implementation reference

Baseline reviewed: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6` (Calf main imported into nativeCmpkit). Public packages and `calf-*` module paths below are intentionally retained for compatibility. Line references are to that commit, not to later migration edits.

Related: [findings and complete source coverage](../audit/permissions-and-geo.md), [machine-readable findings](../audit/findings/PERM.json), [verification and runnable reproduction](../testing/permissions-and-geo.md).

## 1. Scope, module boundaries and dependencies

There are **12 permissions Gradle projects**, not 12 child modules: the umbrella project, `core`, and 10 feature projects. Together with geo, the review covers **132 tracked files**. All were read, including registration-only actuals and build files. The file-by-file coverage appendix is in the audit report.

| Project | Responsibility | Baseline build dependency surface |
|---|---|---|
| `calf-permissions` | Compatibility umbrella; a comment-only `Permission.kt` keeps publishing tooling happy | `api` on core and all 10 feature projects; no independent implementation |
| `calf-permissions/core` | Public state API, Android mapping registry, iOS helper registry, lifecycle effects; storage/audio-read/call/SMS permissions | `api(compose.foundation)`; Android `implementation(activity-compose)` |
| `camera` | `Camera` | `api(core)`; iOS AVFoundation video |
| `microphone` | `RecordAudio` | `api(core)`; iOS AVFoundation audio |
| `gallery` | `Gallery`, `ReadImage`, `ReadVideo` | `api(core)`; iOS Photos |
| `location` | `FineLocation`, `CoarseLocation` | `api(core)`; iOS CoreLocation when-in-use |
| `background-location` | `BackgroundLocation` | `api(core)`; separate Always authorization/usage requirement |
| `bluetooth` | `BluetoothLe`, `BluetoothScan`, `BluetoothConnect`, `BluetoothAdvertise` | `api(core)`; iOS CoreBluetooth |
| `contacts` | `ReadContacts`, `WriteContacts` | `api(core)`; iOS Contacts |
| `calendar` | `ReadCalendar`, `WriteCalendar` | `api(core)`; iOS EventKit |
| `notifications` | `Notification`, `RemoteNotification` | `api(core)`; iOS UserNotifications/UIKit; Android manifest merges POST_NOTIFICATIONS |
| `wifi` | `WifiAccessState`, `WifiChangeState`, `WifiNearbyDevices` | `api(core)`; iOS Foundation NSNetService/UIKit |
| `calf-geo` | Coordinate types/math and an incomplete location tracker | Common `implementation(compose.foundation)`; Android AppCompat, lifecycle-extensions, Play Services Location. **No permission-module dependency. No publication plugin.** |

Every permissions project applies `compose.multiplatform` and `module.publication`; geo applies only the former. None declares its own tests, resource processor, cinterop definition, custom compiler flags, or framework binary. Native integrations use Kotlin/Native platform bindings rather than bundled native binaries. Public geo `State` types should have an explicit consumer/API dependency contract before publishing; currently foundation is an implementation dependency.

Shared conventions select Android, JVM `desktop`, JS browser, Wasm-JS browser, iOS arm64 and iOS simulator-arm64; there is no Intel iOS simulator, macOS-native, watchOS or tvOS implementation. Desktop JVM can run on host OSes but that does not provide native permission integration. Baseline versions: Kotlin2.4.20, Compose1.12.0, AGP9.4.0, Java target17, Android min23/compile37, activity-compose1.13.0, AppCompat1.8.0, lifecycle-extensions2.2.0, Play Services Location21.4.0. Version resolution/build availability is documented by the build audit, not assumed here.

The sample target overrides its project-level iOS26 setting with **iOS18.5**. That is not a library-wide declaration of minimum iOS support. In particular, an unguarded iOS17 EventKit method needs an explicit availability decision (`PERM-011`).

## 2. Public API: identity, state and helpers

### Permission identity and registration

`core/commonMain/.../PermissionState.kt:96-110` defines `open class Permission(val name: String)`:

- `equals` compares identity or the `name` of any `Permission`, even a subclass; `hashCode` delegates to `name`; `toString` returns `name`. Names are case-sensitive global identities, not localized UI text.
- The companion object is an extension-property namespace. There are **28** public logical permission properties.
- Each feature common file declares a companion extension getter, an internal singleton (`PermissionCamera`, etc.), and an internal `expect register...Permission`. Accessing the singleton initializes it once and registers the platform mapping/factory.
- Importing a module is not equivalent to initializing every singleton. Constructing `Permission("Camera")` manually before accessing the built-in singleton can miss its registration. Android currently treats that as granted; iOS throws a useful missing-delegate error (`PERM-001`).
- Custom platform registration is possible because `AndroidPermissionRegistry`, `AndroidPermissionMapping`, `PermissionDelegateRegistry` and `PermissionHelper` are public. Registration replaces an existing equal-name key with no conflict check, synchronization, schema validation or removal API. Coordinate custom names and registration threads.

### State facade and preview branch

`rememberPermissionState(permission, onPermissionResult)` returns a stable `PermissionState` with `permission`, **mutable** `status`, `launchPermissionRequest()` and `openAppSettings()`. Request/settings calls are intended for event/side-effect scopes, not composition. The status cache is not an OS enforcement boundary; the caller can even assign it directly. Prefer not to mutate it externally.

`rememberMultiplePermissionsState(permissions, onPermissionsResult)` returns:

- `permissions`: individual state objects, which can also launch requests;
- `revokedPermissions`: a `derivedStateOf` filtered list of states not equal to Granted;
- `allPermissionsGranted`: `all(isGranted) || revokedPermissions.isEmpty()`; the second term is logically redundant when derived from the same states; an empty list is granted by universal quantification;
- `shouldShowRationale`: `any` denied member requesting rationale;
- `launchMultiplePermissionRequest()`: materially different per platform, detailed below.

Neither factory de-duplicates logical input permissions. Mutable list keys changed in place can defeat `remember` invalidation; callers should pass immutable value lists. The Android per-item Compose `key(permission)` also needs unique keys.

In `LocalInspectionMode`, single permission is granted, request/settings are empty, and the preview object is remembered **without `permission` as a key**. Changing a preview permission can retain its original identity. Multiple preview returns empty permission/revoked lists and `allPermissionsGranted=true` regardless of requested input. This intentionally avoids `findActivity` in IDE previews; it is not an OS test or a configurable preview-denial facility. See historical #176/#200.

`PermissionsUtil.kt` defines opt-in `ExperimentalPermissionsApi` and sealed `PermissionStatus.Granted` / `Denied(shouldShowRationale)`. Extension getters are simple and exhaustive: `isGranted` compares Granted; `isNotGranted` negates it; `isDenied` tests Denied; `shouldShowRationale` returns false for Granted or its stored Boolean. The binary model does not express unknown, limited, restricted, unsupported, request-in-flight, failure or cancellation (`PERM-016`). Do not interpret Android rationale=false as “may always request again”: it covers both first-use and permanent denial. iOS uses rationale=true for many settings-only cases.

### Internal expect/actual layer

`MutablePermissionState` is an internal interface adding `refreshPermissionStatus()`. `rememberMutablePermissionState` is an expect factory. `MutableMultiplePermissionsState` is an expect class taking a list of mutable states and declaring all aggregate getters, launch, and `updatePermissionsStatus(Map<Permission,Boolean>)`. Every actual implements these declarations, but nonmobile actuals only satisfy the type contract, not functionality.

`updatePermissionsStatus` loops over map keys, finds the **first** matching logical state and refreshes it; the Boolean is only checked for non-null and not assigned directly. Complexity is O(result-count × permission-count). Duplicate logical states therefore do not all refresh. These are normally small lists; correctness of mapping and callback contracts matters much more than micro-optimization.

## 3. Android core execution flow

```text
Permission extension getter -> singleton.init -> register(native string, SDK range)
rememberPermissionState -> remember(permission) MutablePermissionStateImpl
  -> capture Context + nearest Activity + initial callback
  -> cache permission.toAndroidPermission() and initial OS/rationale status
  -> install lifecycle observer and ActivityResult launcher (DisposableEffect)
user request
  empty/not-applicable or alwaysGranted -> refresh -> original callback(true)
  real mapping -> RequestPermission launcher
    result -> refresh status from OS -> latest composable callback(result)
ON_RESUME (only when currently denied) -> refresh from OS
onDispose -> launcher=null; lifecycle observer removed
```

Important functions:

- `Context.findActivity` (`PermissionsUtil.android.kt:83-90`) unwraps `ContextWrapper` until an Activity and otherwise throws a targeted error. A host must provide an Activity context and an ActivityResult registry owner; this is not a service/background permission API.
- `checkPermission` uses `ContextCompat.checkSelfPermission`; `Activity.shouldShowRationale` uses `ActivityCompat.shouldShowRequestPermissionRationale` (lines92-99).
- `toAndroidPermission` resolves one registry entry, keeps it only inside its inclusive min/max SDK range, otherwise returns `""` (101-108). `isAlwaysGranted` reads an independent registry flag; none of the built-in current mappings sets it. `findByAndroidString` globally returns the first matching active mapping (registry34-38).
- `MutablePermissionStateImpl.getPermissionStatus` uses the cached native string, not a newly resolved one; runtime re-registration can therefore diverge between single and bulk paths. Empty/always-granted returns Granted. Otherwise OS check chooses Granted or Denied(rationale).
- `openAppSettings` selects ACTION_APP_NOTIFICATION_SETTINGS only for logical name `Notification` on API33+, although that intent exists from API26. It supplies EXTRA_APP_PACKAGE but no NEW_TASK flag for that branch; the usual host is an Activity. All other permissions use ACTION_APPLICATION_DETAILS_SETTINGS with `package:` URI and NEW_TASK. No fallback/error callback handles unavailable settings activities.
- `PermissionLifecycleCheckerEffect` and plural equivalent add/remove observers correctly through DisposableEffect. Their deliberate “only refresh denied” condition can leave grants stale (`PERM-006`). The remembered observer captures the initially provided lifecycle event; current public use always defaults to ON_RESUME.

Bulk factory builds remembered state objects **and a separate single launcher for every member**, plus one RequestMultiplePermissions launcher. This is O(n) ActivityResult registrations even when only bulk requests are used. Its bulk launcher returns raw native-string results -> global reverse mapping -> refresh matched states -> user callback. `Gallery`/`ReadStorage` collide (`PERM-002`); unknown results are filtered out. `launchMultiplePermissionRequest` removes blank strings but neither deduplicates aliases nor includes synthetic results for removed entries (`PERM-003`). No serialization/reentrancy guard handles concurrent launches or changes to the requested list while an old launcher result is in flight.

## 4. Complete logical permission map

“None/out-of-range” means the Android implementation reports Granted **because that runtime permission is not represented**, not because the requested operation is guaranteed. iOS “always granted” means no corresponding runtime gate in this API, not unrestricted data access. All Desktop/JS/Wasm rows are the same denied/no-op implementation described in section6.

| Module / property | Android mapping and inclusive SDK restriction | iOS implementation and effective meaning |
|---|---|---|
| core `ReadStorage` | READ_EXTERNAL_STORAGE, through32 | Granted helper; app sandbox/URL access still applies |
| core `WriteStorage` | WRITE_EXTERNAL_STORAGE, through28 | Granted helper; no outside-sandbox rights |
| core `ReadAudio` | READ_MEDIA_AUDIO,33+ | Granted helper; no media-library API or entitlement obtained |
| core `Call` | CALL_PHONE | Granted helper; URL/dialing/user interaction is outside this library |
| core `ReadSms` | READ_SMS | NotGranted helper; iOS arbitrary SMS reading unsupported |
| core `ReceiveSms` | RECEIVE_SMS | NotGranted helper; no receiving/OTP API |
| core `SendSms` | SEND_SMS | Granted helper; not silent sending; native message-composer workflow separate |
| camera `Camera` | CAMERA | AVCameraPermissionHelper(AVMediaTypeVideo) |
| microphone `RecordAudio` | RECORD_AUDIO | AVMicrophonePermissionHelper(AVMediaTypeAudio) |
| gallery `Gallery` | READ_EXTERNAL_STORAGE, through32 | GalleryPermissionHelper, shared Photos authorization |
| gallery `ReadImage` | READ_MEDIA_IMAGES,33+ | Same Photos helper, not image-only authorization |
| gallery `ReadVideo` | READ_MEDIA_VIDEO,33+ | Same Photos helper, not video-only authorization |
| location `FineLocation` | ACCESS_FINE_LOCATION | LocationPermissionHelper, when-in-use; **does not check precision** |
| location `CoarseLocation` | ACCESS_COARSE_LOCATION | Same when-in-use helper |
| background-location `BackgroundLocation` | ACCESS_BACKGROUND_LOCATION,29+ | BackgroundLocationPermissionHelper, Always only; upgrade bug |
| bluetooth `BluetoothLe` | BLUETOOTH, no upper SDK bound | BluetoothPermissionHelper, same central authorization |
| bluetooth `BluetoothScan` | BLUETOOTH_SCAN,31+ | Same central authorization, no service/capability distinction |
| bluetooth `BluetoothConnect` | BLUETOOTH_CONNECT,31+ | Same |
| bluetooth `BluetoothAdvertise` | BLUETOOTH_ADVERTISE,31+ | Same **central** manager, not peripheral operation implementation |
| contacts `ReadContacts` | READ_CONTACTS | ContactPermissionHelper, contacts authorization |
| contacts `WriteContacts` | WRITE_CONTACTS | Same helper, no separate iOS read/write gate |
| calendar `ReadCalendar` | READ_CALENDAR | CalendarPermissionHelper, full event access |
| calendar `WriteCalendar` | WRITE_CALENDAR | Same full-access helper; write-only not supported |
| notifications `Notification` | POST_NOTIFICATIONS,33+ | LocalNotificationPermissionHelper: sound + alert + badge authorization |
| notifications `RemoteNotification` | **No registration**, intentionally iOS-only | RemoteNotificationPermissionHelper: same authorization + fresh-grant APNs registration |
| wifi `WifiAccessState` | ACCESS_WIFI_STATE | WifiPermissionHelper: local-network Bonjour publication heuristic |
| wifi `WifiChangeState` | CHANGE_WIFI_STATE | Same local-network probe; does not authorize changing Wi-Fi |
| wifi `WifiNearbyDevices` | NEARBY_WIFI_DEVICES,33+ | Same local-network probe |

Android BLUETOOTH/ACCESS_WIFI_STATE/CHANGE_WIFI_STATE are not themselves dangerous runtime prompts; they still need the appropriate manifest declarations for applicable operations. Old Android Bluetooth scanning can require location permissions; the scan property's pre31 no-op does not obtain that prerequisite. Android fine/coarse/background requests require version-aware orchestration (`PERM-004`). Android13 media-specific properties do not automatically fall back to READ_EXTERNAL_STORAGE on older OS versions. Android14 selected-photos access is not modeled. Modern Gallery/WriteStorage no-op must not be advertised as unrestricted media/all-files authorization.

Only the notification feature supplies a library AndroidManifest: a single POST_NOTIFICATIONS declaration. Every other Android permission is a consumer manifest responsibility. SMS and background location additionally have store/distribution policy constraints. There is no automatic PermissionController request embedded in any geo path.

## 5. iOS core and native helper implementation details

### Registry, state, lifecycle and settings

`PermissionDelegateRegistry` stores `Permission -> () -> PermissionHelper`; `register` replaces a factory and `getDelegate` creates a **fresh helper per state**, not a singleton helper. Missing registration throws with a dependency hint. Aliased logical permissions therefore create independent objects observing the same OS authorization.

`PermissionHelper` offers callback-style `launchPermissionRequest(Boolean)` and `getPermissionStatus(PermissionStatus)`. `handleLaunchPermissionRequest` calls status first:

```text
Granted       -> callback(true), no native request
Denied(true)  -> callback(false), no native request
Denied(false) -> execute native request closure
```

It contains no thread normalization, timeout, cancellation, error object, lifecycle owner or once-only guard. Keep the distinction between “may request” and Android-style rationale explicit; the historical iOS rationale fixes depend on this convention.

`MutablePermissionStateImpl` initially publishes Denied(false), obtains its helper, and refreshes immediately in `init`. That initial value can briefly flash before an asynchronous status query returns. Refresh forwards final assignment to `scope.launch(Dispatchers.Main)`. A request forwards the helper callback to user code **before** refreshing, without main dispatch or checking whether the remembered scope is cancelled. Callback capture, disposal and ordering findings are `PERM-005`/`007`.

Settings uses UIApplicationOpenNotificationSettingsURLString for both notification names only when `UIDevice.systemVersion.split('.').firstOrNull()?.toIntOrNull() >=16`; otherwise it uses UIApplicationOpenSettingsURLString. URL parsing is nullable, `canOpenURL` guards the open, and completion is ignored. The unused `UIApplicationOpenDefaultApplicationsSettingsURLString` import is not a settings implementation. Opening Settings is not a permission request.

The same denied-only ON_RESUME observer as Android refreshes states; dispose removes observers but does not cancel native helper work. Multiple state creates all helpers, launches all requests in a for loop, and emits one-entry callback maps per helper. It does not use a batch completion coordinator (`PERM-008`).

### Core helpers

- `GrantedPermissionHelper`: immediate true request and Granted status. Used for storage, read-audio, call and send-SMS on iOS. There are no native side effects.
- `NotGrantedPermissionHelper`: immediate false and Denied(false). Used for read/receive SMS. It is functionally unsupported, not a permission the user can eventually grant.

### Camera / microphone

`AVCameraPermissionHelper` and `AVMicrophonePermissionHelper` are identical logic in separately named classes to avoid duplicate native runtime names across modular klibs (history `5eac9b9`/`f7d7cb1`). Each takes an `AVMediaType`, queries `AVCaptureDevice.authorizationStatusForMediaType`, maps Authorized -> Granted, NotDetermined -> Denied(false), Denied/restricted/other -> Denied(true), and requests access only through the shared helper gate. It directly forwards Apple's Boolean completion. No camera/microphone capture is started, no device presence is tested, and no callback dispatch/disposal is added. Usage strings: NSCameraUsageDescription and NSMicrophoneUsageDescription respectively.

### Photos

`GalleryPermissionHelper.launchPermissionRequest` invokes legacy `PHPhotoLibrary.requestAuthorization` and returns whether the returned status equals Authorized. Status queries use legacy `PHPhotoLibrary.authorizationStatus`; Authorized grants, NotDetermined permits request, all other statuses produce settings-only denial. Modern access-level/limited authorization is absent. Legacy APIs can mask limited access as Authorized, so switching to modern APIs requires a capability policy rather than merely adding a Limited case. The helper asks library permission; system photo picker access often does not need broad Photos authorization. Required purpose string: NSPhotoLibraryUsageDescription for this request, not necessarily for every picker implementation.

### Foreground location

`LocationPermissionHelper` constructs one CLLocationManager and **strongly retains** its `LocationManagerDelegate` in a field before assigning the native delegate. Unlike the Bluetooth implementation, that lifetime pattern is explicit. Status uses the class `authorizationStatus()` query: authorized/Always/WhenInUse -> Granted, NotDetermined -> Denied(false), other -> Denied(true). It does not inspect global services enablement or accuracy authorization.

Request stores a single callback field then invokes requestWhenInUseAuthorization. Delegate `locationManager(...didChangeAuthorizationStatus)` emits true for authorized values, false otherwise; outer closure invokes the pending callback and then nulls it. Nonterminal status, repeated and reentrant request problems are in `PERM-010`. No coordinate updates are requested. Required key: NSLocationWhenInUseUsageDescription. FineLocation has no temporary-full-accuracy purpose-key support.

### Background location

Same manager/delegate lifetime pattern; request invokes requestAlwaysAuthorization. Only Always counts as Granted; NotDetermined is requestable and **WhenInUse falls through to settings-only denial**, blocking the typical upgrade (`PERM-009`). Delegate similarly clears the pending callback on any status. Actual background tracking additionally requires application background-mode configuration and a real location-update implementation; granting this permission does not implement that service. Required modern strings: NSLocationWhenInUseUsageDescription and NSLocationAlwaysAndWhenInUseUsageDescription. `UIBackgroundModes=location` is for genuine background updates, not a blanket requirement to call the authorization query.

### Bluetooth

`BluetoothPermissionHelper.iOS13AndHigher` uses NSProcessInfo.isOperatingSystemAtLeastVersion with an NSOperatingSystemVersion cValue, correctly handling patch-version strings. On13+ it reads CBManager.authorization; AllowedAlways grants, NotDetermined is requestable, Denied/restricted is settings-only denial. The older branch creates a transient CBCentralManager and interprets hardware state; it conflates powered-off with permission denial and may see Unknown immediately after initialization. Whether that fallback is within the supported OS floor must be settled explicitly.

Request first uses the shared gate, then re-checks already-determined authorization. It creates/retains a central manager to trigger the OS prompt with an anonymous delegate on the default queue. `centralManagerDidUpdateState` ignores Unknown, then on13+:

- known authorization -> resolve;
- NotDetermined -> scan for any peripherals, schedule **one** 2-second main-queue recheck; if still unknown no resolution/cleanup occurs on that timer, leaving later events to finish;
- old OS -> resolve if powered on.

A per-invocation `callbackFired` Boolean provides once-only protection within that invocation. `resolveAndCleanup` calls user callback first, then stopScan and clears the shared central-manager field. It neither retains a delegate field nor disambiguates a newer request (`PERM-014`). No scan results are exposed. Current key: NSBluetoothAlwaysUsageDescription; older iOS paths can require NSBluetoothPeripheralUsageDescription. Background central/peripheral modes are not implemented by this helper.

### Contacts

`ContactPermissionHelper` queries CNContactStore.authorizationStatusForEntityType(Contacts), then requests through a temporary CNContactStore. It ignores NSError and forwards `granted`. NotDetermined can request, Authorized grants, Denied and all other states deny with rationale. iOS18 Limited falls into denial, and read/write aliases share this helper. No contacts retrieval/write or OTP extraction API exists here. Required key: NSContactsUsageDescription.

### Calendar

`CalendarPermissionHelper` queries event authorization only (not reminders). Authorized/FullAccess grants; NotDetermined can request; Denied/Restricted/WriteOnly/other deny with rationale. Launch uses a temporary EKEventStore and **unguarded** requestFullAccessToEventsWithCompletion; success requires true and no NSError. There is no preserved error reason. ReadCalendar/WriteCalendar both construct this helper. iOS17 method availability, modern NSCalendarsFullAccessUsageDescription and write-only least privilege are `PERM-011`/`012`; legacy NSCalendarsUsageDescription alone is not the modern request contract. A write-only implementation would need NSCalendarsWriteOnlyAccessUsageDescription.

### Notifications

Local and remote helpers query UNUserNotificationCenter.currentNotificationCenter().getNotificationSettingsWithCompletionHandler. Authorized, Provisional, Ephemeral -> Granted; NotDetermined -> requestable; Denied/null/unknown -> Denied(true). They request sound|alert|badge, then return `isOk && error==null`. They do not query the individual alert/sound/badge switches or delivery readiness.

The remote helper additionally dispatches registerForRemoteNotifications to main **only after a newly requested grant**. Already-granted short circuit misses registration (`PERM-015`). Callback true can arrive before that queued registration runs and does not promise an APNs token. No notification Info.plist privacy description is needed for UN authorization; APNs integration still needs the correct aps-environment entitlement/provisioning and native app delegate token/error handling. Background remote-notification mode is required only for relevant background delivery behavior. None of these entitlement/token responsibilities are implemented by the permission helper.

### Wi-Fi / local-network probe

All three iOS Wi-Fi properties use `WifiPermissionHelper`, which does not configure Wi-Fi or inspect SSIDs. `getPermissionStatus` cancels any current delegate (reporting false), allocates another `LocalNetworkPermissionDelegate`, retains it, and starts a probe. Request first calls this status query through the shared gate; since the query returns only Granted or Denied(true), its additional explicit-launch branch is effectively unreachable with the current helper's own statuses.

`LocalNetworkPermissionDelegate.startCheck`:

1. If UIApplication is not Active, immediately complete false.
2. Create NSNetService(domain=`local.`, type=`_lnp._tcp.`, name=`CalfWifiPermissionCheck`, port0); nullable failure -> false.
3. Assign retained delegate, schedule a3-second NSTimer, publish.
4. `netServiceDidPublish` -> true; `didNotPublish`, timer, or cancel -> false.
5. `cleanupAndComplete` checks `isCompleted`, invalidates/releases timer, stops service, clears delegate/service, then invokes completion. This clean-before-callback ordering and identity check before clearing the current delegate are good safeguards.

Still, state observation itself triggers publication/potential privacy UI, arbitrary timeout is not an authorization oracle, and pending probes outlive composition until completion (`PERM-013`). Consumer declarations must include NSLocalNetworkUsageDescription **and** NSBonjourServices containing `_lnp._tcp`; baseline docs/sample lack the latter. Broader Wi-Fi APIs have separate Apple capability/entitlement restrictions.

## 6. Desktop, JS, Wasm implementation truth

All 36 nonmobile registration files (core storage+SMS and ten feature families across3 targets) implement every register function as `Unit`. They do not create a registry or call browser/desktop permissions APIs.

Each nonmobile `MutablePermissionStateImpl` exposes a mutable Compose state initially Denied(false). `getPermissionStatus` always returns that value; launch/settings/refresh do nothing. The factory discards its supplied callback. If a caller manually changes status, even refresh does not restore an OS truth.

Each plural factory creates per-permission state objects in a composition loop and stores them in a remembered aggregate; it has the same derived getters as mobile. Its bulk launch is empty. The map-refresh method traverses keys but invokes no-op child refresh. These platforms are **not implemented**; empty request callbacks are not a valid indication of an in-progress OS prompt. Current public docs describe Android/iOS support, but merely declaring/building a web or desktop target must not expand that promise (`PERM-017`).

## 7. Geo types and computation

These are plain immutable Kotlin data classes with no validation or serialization annotations:

| Type | Fields and semantics |
|---|---|
| `LatLng` | latitude/longitude Double degrees; no finite/range enforcement |
| `Location` | coordinates plus non-null horizontal accuracy meters |
| `Altitude` | meters plus nullable accuracy meters |
| `Azimuth` | degrees plus nullable accuracy degrees; Android populates **course/bearing**, not magnetometer/device heading |
| `Speed` | meters/second plus nullable accuracy meters/second |
| `ExtendedLocation` | Location, Azimuth, Speed, Altitude, timestampMs (Android wall-clock location time) |

`LatLng.distanceTo` (22-35) applies spherical haversine: degree differences -> radians, `a = sin²(dLat/2) + cos(lat1)cos(lat2)sin²(dLon/2)`, central angle `2*asin(sqrt(a))`, EarthRadius6371km. It returns **kilometers**, unlike accuracy fields in meters. `toRadians`/`toDegree` multiply by PI/180 and180/PI. It is not an ellipsoidal WGS84 geodesic solver. Repeated sin calls/boxing are minor compared with tracker correctness; benchmark before optimizing.

`getAngleTo` (44-68) computes initial great-circle bearing with atan2, converts to degrees, normalizes to[0,360), optionally rounds to nearest10 degrees (default **true**, Kotlin round ties-to-even), then maps360 to0. Coincident and exact-antipodal initial bearings are mathematically undefined but not modeled; pole/nonnumeric cases need an explicit contract. Normal cases passed isolated tests; no valid antipodal NaN was observed in5million seeded JVM trials (`PERM-023`).

## 8. Geo tracker execution and ownership

Common `expect class LocationTracker` exposes suspend startTracking, stopTracking, State<LatLng>, State<ExtendedLocation>. Its commented permissions controller is not code. The expect declaration provides no common constructor/factory or bind method, so platform creation/host setup must happen outside this API. It does not advertise failure, initial no-fix, permission, settings, precision or tracking state.

### Android

Constructor takes interval(ms, default1000) and Google priority(default HIGH_ACCURACY), extends LocationCallback, creates legacy mutable LocationRequest, two private CONFLATED channels, and an unowned CoroutineScope(Dispatchers.Main). Input interval/priority are not validated by the library; underlying Google setters may reject them.

`bind(lifecycle,context,fragmentManager)` gets a FusedLocationProviderClient. `fragmentManager` is unused. If isStarted is already true it requests updates immediately with `looper=null`; every bind attaches an annotation-based LifecycleObserver that removes updates and nulls the **current shared** client on ON_DESTROY. It does not remove old observers or reset isStarted (`PERM-020`). Legacy OnLifecycleEvent and lifecycle-extensions dependency are maintenance debt.

`startTracking` sets isStarted and requests updates if bound; it never suspends for permissions or awaits the Google Task despite its signature/comment. Before bind it succeeds silently and bind later auto-starts; permission failure/absent Play Services/incorrect calling Looper have no coherent result (`PERM-021`). `stopTracking` clears isStarted and removes updates if a client exists, ignoring removal failure; late callbacks remain possible.

`onLocationResult` ignores empty results and uses only lastLocation, deliberately discarding any batched intermediate fixes. It builds all six value objects, chooses accuracy nullability solely by API26 availability, then launches a main coroutine that sends extended/simple values to conflated channels. No collector exists. **Neither public State is ever updated** (`PERM-018`). Channel capacity is bounded, so the current bug is not an unbounded queue of positions; allocations/coroutine scheduling still do useless work. Metadata presence flags are ignored (`PERM-022`), and there is no stale/mock-fix policy, clock-monotonic timestamp, or atomic cross-state delivery.

### iOS / desktop / JS / Wasm

All four actuals have identical body logic: startTracking prints `startTracking`, stopTracking prints `stopTracking`, and both State objects retain zeroed values forever. There is no CLLocationManager, navigator.geolocation, sensor API, permission integration or cleanup. `PERM-019` tracks explicit unsupported state/backends; the module is a nonpublished prototype, not a verified cross-platform tracker.

## 9. Maintenance, security and performance rules

- Preserve module selection: it minimizes unnecessary native framework/privacy surface compared with depending on the umbrella. App Store rejection is app/binary/review-dependent, not guaranteed solely by a source import.
- Permission helpers enforce no OS sandbox boundary themselves. A stale or manually assigned Granted does not confer access. Native operations must still handle permission revocation/security exceptions.
- Do not request all permissions as an application startup checklist. Request the minimum capability at the appropriate user gesture, especially background location, contacts/calendar, SMS and network publication.
- Protect purpose strings and entitlements in consumer-app tests. A library cannot supply truthful user-facing usage reasons for every app. The sample's `Just for tests` strings are not production explanations.
- Introduce testable platform adapters before major redesign; keep compatibility callbacks/Permission names while improving the underlying request lifecycle.
- Resolve observer/probe side effects before globally refreshing all grants. Then centralize request queue, callback dispatch and cancellation semantics without flattening OS differences.
- Performance hotspots are native prompt/probe churn, unnecessary bulk helper/launcher creation and the broken geo channel pipeline, not the small map/list operations. There are no measured CPU/memory benchmarks in this audit.
- This area contains no credentials, cryptography, downloaded/executed code, raw file parsing, or custom C pointer arithmetic. Bluetooth cValue creates an OS version value; Wi-Fi publishes a fixed local service (no application data). Absence of an obvious dangerous sink is **not** a complete dependency-vulnerability scan or proof of native memory safety.
- Recheck all callback paths on Kotlin/Native GC and process/lifecycle transitions on devices. A Linux source/stub test cannot prove ObjC retain cycles, OS UI order, APNs delivery, privacy-dialog behavior or App Store acceptability.
