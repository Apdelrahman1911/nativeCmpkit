---
render_macros: true
---
<!-- Modified for nativeCmpkit migration (2026-10-24): independent coordinates / project references; inherited APIs retained. -->
# Permissions

> **nativeCmpkit migration:** new coordinates are **unpublished**. See [installation](installation.md) and the [source audit](audit/README.md). Historical Calf version claims are preserved, not certified as nativeCmpkit releases.

nativeCmpkit Permissions provides a Compose Multiplatform API for requesting and observing runtime permissions on Android and iOS.

## Why Modular Permissions?

Calf Permissions is split into **individual modules per permission type** instead of shipping as a single monolithic library. This architecture offers several important benefits:

### iOS App Store Compliance

Apple's App Store review process is strict about permission usage. If your app binary links against a permission framework (e.g., `CoreBluetooth`, `EventKit`, `CoreLocation`) but never actually uses it, **Apple may reject your app** or require you to add a usage description for a permission your app doesn't need.

With a monolithic permissions library, your iOS binary would include code for *every* permission type — camera, bluetooth, contacts, calendar, etc. — even if your app only uses the camera. This leads to:

- **App Store rejections** for unused permission frameworks linked in the binary
- **Unnecessary privacy usage descriptions** in your `Info.plist`

By using modular permissions, you **only include the permissions your app actually needs**, so your iOS binary only links against the relevant native frameworks, and you only need to declare the usage descriptions that apply.

## Installation


### Option 1: Individual Modules (Recommended)

Add only the permission modules your app actually needs to your module `build.gradle.kts` file:

```kotlin
// Core (required — provides the base API)
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-core:{{ nativecmpkit_version }}")

// Add only the permissions you need:
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-camera:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-microphone:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-gallery:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-location:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-background-location:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-bluetooth:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-contacts:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-calendar:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-notifications:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-wifi:{{ nativecmpkit_version }}")
```

For example, if your app only needs camera and location permissions:

```kotlin
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-core:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-camera:{{ nativecmpkit_version }}")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-location:{{ nativecmpkit_version }}")
```

### Option 2: Umbrella Module

If you want all permissions at once (not recommended for iOS App Store submissions):

```kotlin
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions:{{ nativecmpkit_version }}")
```

!!! warning
    The umbrella module includes **all** permission modules. On iOS, this means your binary will link against all native permission frameworks, which may cause App Store review issues if you don't use all of them.

## Module Architecture

The permissions library is organized as follows:

```
calf-permissions/
├── build.gradle.kts          ← umbrella module (includes all)
├── core/                     ← calf-permissions-core (base API + permissions that don't require adding keys to `Info.plist`)
├── camera/                   ← calf-permissions-camera
├── microphone/               ← calf-permissions-microphone
├── gallery/                  ← calf-permissions-gallery
├── location/                 ← calf-permissions-location
├── background-location/      ← calf-permissions-background-location
├── bluetooth/                ← calf-permissions-bluetooth
├── contacts/                 ← calf-permissions-contacts
├── calendar/                 ← calf-permissions-calendar
├── notifications/            ← calf-permissions-notifications
└── wifi/                     ← calf-permissions-wifi
```

Each module depends on `calf-permissions-core`, which provides the shared API (`Permission`, `PermissionState`, `rememberPermissionState`, etc.). The platform-specific permission handling is implemented in each individual module.

Permissions that don't require adding a reason in the iOS `Info.plist` (because they are always granted on iOS) are included directly in the **core** module. This includes storage permissions (`ReadStorage`, `WriteStorage`), `ReadAudio`, and `Call`.

## Usage

### Single Permission

Use `rememberPermissionState(permission: Permission)` to request a single permission and observe its status:

```kotlin
// Camera permission state
val cameraPermissionState = rememberPermissionState(
    Permission.Camera
)

if (cameraPermissionState.status.isGranted) {
    Text("Camera permission Granted")
} else {
    Button(
        onClick = { cameraPermissionState.launchPermissionRequest() }
    ) {
        Text("Request permission")
    }
}
```

### Multiple Permissions

Use `rememberMultiplePermissionsState(permissions: List<Permission>)` to request a group of permissions. iOS prompts are serialized, not presented concurrently:

```kotlin
val multiplePermissionsState = rememberMultiplePermissionsState(
    permissions = listOf(
        Permission.Camera,
        Permission.FineLocation
    )
)

if (multiplePermissionsState.allPermissionsGranted) {
    Text("All permissions granted")
} else {
    Button(
        onClick = { multiplePermissionsState.launchMultiplePermissionRequest() }
    ) {
        Text("Request permissions")
    }
}
```

| Android                                                      | iOS                                                  |
|--------------------------------------------------------------|------------------------------------------------------|
| ![Permission Dialog Android](images/Permissions-android.png) | ![Permission Dialog iOS](images/Permissions-ios.png) |

## Request results, scope and unsupported targets

`PermissionStatus` intentionally still has only `Granted` and `Denied`, preserving
existing exhaustive `when` expressions. Import `com.mohamedrejeb.calf.permissions.details`
and inspect `state.details` when you need `availability`, `access`, `requestability`,
`lastRequest`, or the narrower native `capability`.

- `NotRequired` means this library has no applicable runtime permission for that
  OS version; it **does not** authorize every operation. Unregistered Android or
  iOS custom permissions are `Unsupported`/false, never implicitly granted. Register
  custom mappings before constructing state; an intentionally empty Android
  mapping must explicitly specify `alwaysGranted = true`.
  A registered iOS helper factory that throws remains `Failed`, not `Unsupported`;
  the public `PermissionDelegateRegistry.getDelegate` lookup retains its explicit
  missing-registration error. Missing optional integration and native/helper
  failure are different outcomes.
- Desktop JVM, JS and Wasm backends are explicitly `Unsupported`. Requests finish
  with false (including a complete map for a batch), rather than silently doing
  nothing. Completion is synchronous, with one result per explicit launch; a
  child request reports only that child, and an empty batch reports an empty map.
  `details.lastRequest` is `Unsupported` before the callback. These backends do
  not query/prompt browser camera/microphone/location/notification services or
  infer grants from a desktop/macOS sandbox, TCC, API presence, insecure context,
  or the legacy mutable `status` flag. `openAppSettings()` has no portable route
  and performs no navigation. Use the actual platform/service API separately;
  this is not native/browser feature parity. Inspection-mode previews are visual
  demonstrations, not usable permission-request backends.
- A batch reports one map containing each distinct requested logical permission,
  including aliases and permissions not applicable on that OS. An empty batch
  reports an empty map. A request made through an individual member reports that
  member's result, not a partial batch result masquerading as a complete batch.
- Overlapping launches on the same state/batch share its native request and each
  launch receives a completion. Native callbacks are ignored after composition
  disposal. iOS state/details are updated on Main **before** user callbacks.
- `Denied(false)` is not proof of requestability: Android cannot distinguish
  first-use from permanent denial using rationale alone. User denial, restricted
  access, timeout, configuration failure and unsupported APIs are different.
- Resume refresh includes previously granted states, so revocations can be
  observed. Native permission status is a cache, not an OS enforcement boundary;
  handle errors from the actual protected operation as well.

Callbacks use the latest recomposed function. Keep permission lists immutable;
logical duplicates (same case-sensitive name) are normalized to one member.
Do not launch unrelated states' native requests simultaneously; group related
permissions with `rememberMultiplePermissionsState`.

See [current implementation and verification](development/PERM.md) for platform
test limitations. New tests do not imply physical-device permission flows passed.

## Permissions Reference

### Core Permissions

The following permissions are included in the **core** module (`calf-permissions-core`) because they are always granted on iOS and don't require an `Info.plist` entry.

#### Storage Permissions

##### Read Storage Permission

To request the read storage permission, use `Permission.ReadStorage`.

###### Android

Add the following permission to your `AndroidManifest.xml` file:

```xml
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
```

###### iOS

There is no corresponding runtime gate in this helper (`NotRequired`). iOS sandbox, user-selected URL/security-scope, API and entitlement requirements still apply.

##### Write Storage Permission

To request the write storage permission, use `Permission.WriteStorage`.

###### Android

Add the following permission to your `AndroidManifest.xml` file:

```xml
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />
```

This helper requests the legacy write permission only through Android 9/API 28.
On newer versions it reports `Granted` with `details.availability = NotRequired`,
**not all-files access**. Use app-scoped storage, the Storage Access Framework
(document picker), MediaStore, or the system photo picker as appropriate. Android
10 legacy/scoped behavior also depends on target SDK and the application's storage
mode; the helper does not opt your app into a legacy mode. Android 13 media reads
use the separate `ReadImage`/`ReadVideo`/`ReadAudio` permissions where necessary.

Do not add `MANAGE_EXTERNAL_STORAGE` to ordinary storage examples. This library
neither requests nor checks that special, policy-restricted all-files setting.
The manifest declaration alone never establishes that access.

###### iOS

There is no corresponding runtime gate in this helper (`NotRequired`). iOS sandbox, user-selected URL/security-scope, API and entitlement requirements still apply.

#### Read Audio Permission

To request the read audio permission, use `Permission.ReadAudio`.

##### Android

Add the following permission to your `AndroidManifest.xml` file (Android 13+):

```xml
<uses-permission android:name="android.permission.READ_MEDIA_AUDIO" />
```

##### iOS

There is no corresponding runtime gate in this helper (`NotRequired`). iOS sandbox, user-selected URL/security-scope, API and entitlement requirements still apply.

#### Call Permission

To request the call permission, use `Permission.Call`.

##### Android

Add the following permission to your `AndroidManifest.xml` file:

```xml
<uses-permission android:name="android.permission.CALL_PHONE" />
```

##### iOS

There is no corresponding runtime gate in this helper (`NotRequired`). iOS sandbox, user-selected URL/security-scope, API and entitlement requirements still apply.

### Gallery Permissions

**Module:** `calf-permissions-gallery`

To request gallery permissions, use `Permission.Gallery`, `Permission.ReadImage`, or `Permission.ReadVideo`.

#### Gallery Permission

To request the gallery permission, use `Permission.Gallery`.

##### Android

Add the following permission to your `AndroidManifest.xml` file:

```xml
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
```

##### iOS

Add the following key to your `Info.plist` file:

```xml
<key>NSPhotoLibraryUsageDescription</key>
<string>Gallery permission is required to pick images</string>
```

The string value is the message that will be displayed to the user when the permission is requested.

#### Read Image Permission

To request the read image permission, use `Permission.ReadImage`.

##### Android

Add the following permission to your `AndroidManifest.xml` file (Android 13+):

```xml
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
```

##### iOS

Add the following key to your `Info.plist` file:

```xml
<key>NSPhotoLibraryUsageDescription</key>
<string>Photo library permission is required to read images</string>
```

The string value is the message that will be displayed to the user when the permission is requested.

#### Read Video Permission

To request the read video permission, use `Permission.ReadVideo`.

##### Android

Add the following permission to your `AndroidManifest.xml` file (Android 13+):

```xml
<uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
```

##### iOS

Add the following key to your `Info.plist` file:

```xml
<key>NSPhotoLibraryUsageDescription</key>
<string>Photo library permission is required to read videos</string>
```

The string value is the message that will be displayed to the user when the permission is requested.

### Location Permissions

**Module:** `calf-permissions-location`

To request the location permission, use `Permission.FineLocation` or `Permission.CoarseLocation`.

#### Android

Add the following permissions to your `AndroidManifest.xml` file:

```xml
<!-- For fine location -->
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<!-- For coarse location -->
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

On Android 12/API 31 and later a FineLocation request includes both coarse and fine
native permissions, as required by Android. An approximate-only grant does not
satisfy FineLocation; it is visible as `details.access = Approximate`.

#### iOS

Add the following key to your `Info.plist` file:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>Location permission is required to get your location</string>
```

On iOS 14+, FineLocation requires full accuracy; reduced accuracy is exposed as
`Approximate` and does not claim a precise grant. CoarseLocation accepts approximate
access. This API does not request temporary full accuracy with a purpose key; the
app may explain the limitation and offer Settings. Authorization alone does not
mean location services are enabled or that a fix is available.

The string value is the message that will be displayed to the user when the permission is requested.

### Background Location Permission

**Module:** `calf-permissions-background-location`

To request the background location permission, use `Permission.BackgroundLocation`.

!!! note
    This is a separate module from `calf-permissions-location` to avoid requiring `NSLocationAlwaysAndWhenInUseUsageDescription` in your iOS `Info.plist` when you only need foreground location.

#### Android

Add the following permission to your `AndroidManifest.xml` file:

```xml
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
```

Request and explain foreground access first. A background-only request never
silently adds foreground privileges: it completes false with
`details.requestability = PrerequisiteRequired` until foreground is authorized.
On API 29, a group containing foreground/background permissions requests background
in a separate second stage, only after foreground succeeds. On API 30+, a denied
background permission is `SettingsOnly`; present your educational UI and offer an
explicit `state.openAppSettings()` action. The library does not navigate to
settings or escalate privileges automatically. Return/resume refresh checks the
actual grant.

#### iOS

Add the following keys to your `Info.plist` file:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>Location permission is required to get your location</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Background location permission is required to track your location in the background</string>
```

A WhenInUse authorization remains explicitly requestable for an Always upgrade.
Apple controls when an upgrade prompt is shown and may defer it; lack of an
immediate authorization change is not proof of permanent denial. Requests are
bounded to 60 seconds and expose `TimedOut` separately, with no late callback after
disposal. Recheck on resume; verify the full Always flow on a physical device.

You also need to enable the **Location updates** background mode in your Xcode project under **Signing & Capabilities → Background Modes**, or add the following to your `Info.plist`:

```xml
<key>UIBackgroundModes</key>
<array>
    <string>location</string>
</array>
```

### Notification Permissions

**Module:** `calf-permissions-notifications`

#### Post Notifications Permission

To request the post notifications permission, use `Permission.Notification`.

##### Android

The `android.permission.POST_NOTIFICATIONS` permission is automatically included via manifest merger when you add the `calf-permissions-notifications` dependency. No manual manifest entry is needed.

This runtime permission applies to Android API 33 and up. On older versions the helper is `NotRequired`; app/channel settings can still disable notifications.

##### iOS

No `Info.plist` entry is required. iOS notifications are requested at runtime via the `UNUserNotificationCenter` API.

#### Remote Notification Permission

To request the remote notification permission, use `Permission.RemoteNotification`.

This permission is **iOS-only**. It requests authorization for remote (push) notifications via `UNUserNotificationCenter`. On Android, remote notifications (e.g. via FCM) do not require a separate permission — the `POST_NOTIFICATIONS` permission covers both local and remote notifications. Using `Permission.RemoteNotification` on Android returns `Granted`/`NotRequired`; this is not a substitute for requesting `Permission.Notification` on API 33+.

##### iOS

No `Info.plist` entry is required.

### Camera Permission

**Module:** `calf-permissions-camera`

To request the camera permission, use `Permission.Camera`.

#### Android

Add the following permission to your `AndroidManifest.xml` file:

```xml
<uses-permission android:name="android.permission.CAMERA" />
```

#### iOS

Add the following key to your `Info.plist` file:

```xml
<key>NSCameraUsageDescription</key>
<string>Camera permission is required to take pictures</string>
```

The string value is the message that will be displayed to the user when the permission is requested.

### Record Audio Permission

**Module:** `calf-permissions-microphone`

To request the record audio permission, use `Permission.RecordAudio`.

#### Android

Add the following permission to your `AndroidManifest.xml` file:

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

#### iOS

Add the following key to your `Info.plist` file:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Record audio permission is required to record audio</string>
```

The string value is the message that will be displayed to the user when the permission is requested.

### Bluetooth Permissions

**Module:** `calf-permissions-bluetooth`

To request bluetooth permissions, use `Permission.BluetoothLe`, `Permission.BluetoothScan`, `Permission.BluetoothConnect`, or `Permission.BluetoothAdvertise`.

#### Android

Add the following permissions to your `AndroidManifest.xml` file:

```xml
<!-- For Bluetooth LE -->
<uses-permission android:name="android.permission.BLUETOOTH" />
<!-- For Bluetooth Scan (Android 12+) -->
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
<!-- For Bluetooth Connect (Android 12+) -->
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<!-- For Bluetooth Advertise (Android 12+) -->
<uses-permission android:name="android.permission.BLUETOOTH_ADVERTISE" />
```

#### iOS

Add the following key to your `Info.plist` file:

```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>Bluetooth permission is required to use Bluetooth</string>
```

The string value is the message that will be displayed to the user when the permission is requested.

### Contacts Permissions

**Module:** `calf-permissions-contacts`

To request contacts permissions, use `Permission.ReadContacts` or `Permission.WriteContacts`.

#### Android

Add the following permissions to your `AndroidManifest.xml` file:

```xml
<!-- For Read Contacts -->
<uses-permission android:name="android.permission.READ_CONTACTS" />
<!-- For Write Contacts -->
<uses-permission android:name="android.permission.WRITE_CONTACTS" />
```

#### iOS

Add the following key to your `Info.plist` file:

```xml
<key>NSContactsUsageDescription</key>
<string>Contacts permission is required to access user's contacts</string>
```

The string value is the message that will be displayed to the user when the permission is requested.

### Calendar Permissions

**Module:** `calf-permissions-calendar`

To request calendar permissions, use `Permission.ReadCalendar` or `Permission.WriteCalendar`.

#### Android

Add the following permissions to your `AndroidManifest.xml` file:

```xml
<!-- For Read Calendar -->
<uses-permission android:name="android.permission.READ_CALENDAR" />
<!-- For Write Calendar -->
<uses-permission android:name="android.permission.WRITE_CALENDAR" />
```

#### iOS

For iOS 17 and later, declare only the access modes your app actually requests:

```xml
<!-- ReadCalendar requests full event access. -->
<key>NSCalendarsFullAccessUsageDescription</key>
<string>Read your calendar events for the selected feature</string>
<!-- WriteCalendar requests write-only event access, not read access. -->
<key>NSCalendarsWriteOnlyAccessUsageDescription</key>
<string>Add the events you choose to your calendar</string>
<!-- Include this only if supporting iOS 16 or earlier (legacy shared access). -->
<key>NSCalendarsUsageDescription</key>
<string>Access calendar events for the selected feature</string>
```

The helper guards the iOS 17 APIs and uses the legacy request on older systems.
`WriteCalendar` accepts write-only or full access; `ReadCalendar` requires full
access and can explicitly request an upgrade from write-only. On older systems,
EventKit cannot grant only writes, so the legacy request obtains shared access.

The string value is the message that will be displayed to the user when the permission is requested.

### Wi-Fi Permissions

**Module:** `calf-permissions-wifi`

To request Wi-Fi permissions, use `Permission.WifiAccessState`, `Permission.WifiChangeState`, or `Permission.WifiNearbyDevices`.

#### Android

Add the following permissions to your `AndroidManifest.xml` file:

```xml
<!-- For Wi-Fi Access State -->
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
<!-- For Wi-Fi Change State -->
<uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />
<!-- For Wi-Fi Nearby Devices (Android 13+) -->
<uses-permission android:name="android.permission.NEARBY_WIFI_DEVICES" />
```

#### iOS

These historical names probe local-network access on iOS, **not Wi-Fi
configuration, SSID access or network scanning**. An explicit probe requires both
of the following entries, and does not run while merely reading state:

```xml
<key>NSLocalNetworkUsageDescription</key>
<string>Discover nearby devices for the feature you selected</string>
<key>NSBonjourServices</key>
<array><string>_lnp._tcp.</string></array>
```

See the limitations and error/timeout distinctions below before using this probe.

## Partial access and local-network caveats

- iOS Photos uses access-level-aware APIs on iOS 14+. Limited photo-library and
  iOS 18+ limited contacts access remain usable `Granted` results with
  `details.access = Limited`; they are **not** full-library/full-address-book
  access. Do not assume every item is readable. Picker-only workflows often avoid
  broad library authorization entirely.
- Notification `Provisional` and `Ephemeral` scope is retained in details.
  RemoteNotification attempts APNs registration on Main for both freshly granted
  and already authorized/provisional/ephemeral requests. Success means an
  authorization/registration attempt, **not** a device token, entitlement check,
  delivery guarantee, or a promise that sound/alerts are enabled. Integrate the
  application delegate's APNs success/failure callbacks separately.
- iOS Bluetooth status reads are passive. A live request retains its manager and
  delegate until completion/disposal; unresolved authorization times out at 60
  seconds without pretending the user denied it. The passive class authorization
  API requires iOS 13.1+. Powered-off hardware is distinct from permission denial.
- The historical iOS `WifiAccessState`, `WifiChangeState`, and `WifiNearbyDevices`
  names are compatibility aliases for a **local-network Bonjour probe**, not
  permission to configure Wi-Fi, read the SSID, or scan Wi-Fi networks. See
  `details.capability = "local-network-probe"`. This is a bounded heuristic, not a
  documented passive authorization-query API. A successful publication only
  observes that probe; physical-device verification is still required.

For that explicit iOS local-network probe, declare **both**:

```xml
<key>NSLocalNetworkUsageDescription</key>
<string>Discover nearby devices for the feature you selected</string>
<key>NSBonjourServices</key>
<array><string>_lnp._tcp.</string></array>
```

Reading state or resuming the app never publishes a service or opens a permission
prompt. Passive local-network status starts Unknown and is invalidated on resume
because iOS offers no definitive passive query. Only an explicit request while the
app is active starts the probe. Missing configuration, inactivity, publication
failure and a 60-second timeout are separate `lastRequest` outcomes, not permanent
user denial; native service/timer ownership is cleaned before callbacks and on
composition disposal. Privacy usage text must explain the app's actual purpose.
