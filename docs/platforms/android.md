# Android implementation guide

Baseline: `af388bd`. Library conventions use `com.android.kotlin.multiplatform.library`,
Java/JVM 17, compileSdk 37, minSdk 23 and an Android host-test source set. The
sample application is minSdk 24 because its separate JetBrains navigation
dependency requires it. This is not permission to raise every library's minSdk.
The new AGP target is not the old KGP `androidTarget()`; preserve the special
Material source-set matching when adjusting build logic.

## Core, file and camera setup

`PlatformContext` is an actual typealias to `Context`, and
`LocalPlatformContext` delegates to Compose's `LocalContext`. File wrappers hold
`Uri`, not a `java.io.File`. `ContentResolver` is the byte/stream boundary;
`DocumentFile` is used for metadata. Provider permissions, virtual documents and
directory URIs require separate tests. Do not turn a content URI into a path by
string stripping.

No-context IO helpers read `AndroidContextHolder`, whose baseline initialization
occurs in the file picker composable. The module has no manifest initializer.
Calling these helpers from a service, a camera-only screen or a share-only flow
before a file-picker composition can fail. Explicit-context overloads avoid that
hidden initialization requirement; see I/O findings.

Camera capture uses ActivityResult `TakePicture` with a URI from
`FileProvider.getUriForFile(context, "${context.packageName}.provider", file)`.
The library does not ship the sample's provider configuration for consumers.
An app needs its own non-exported provider, narrowly scoped paths and temporary
file/grant lifecycle. `sample/android/src/main/AndroidManifest.xml` demonstrates
the authority/configuration but requests a broad catalogue of permissions for
demo purposes; do not copy that entire manifest into production. Cancellation
and absence of a camera activity must be considered separately from capture
success. A camera permission request alone is not capture initialization.

Picker uses system document/media contracts, including a document fallback for
unsupported media selection. A missing handler is still an error path requiring
tests; a device reporting modern SDK level does not guarantee every gallery app
exists. Saver starts `CreateDocument` and later writes content: state must survive
the delay between request and callback, recomposition and activity recreation.
Do not infer persisted read/write grants from an in-process returned URI.

## Permissions and notifications

There are 28 logical permission properties across core/features. Android mappings
vary by API level: legacy storage, new media permissions, Bluetooth runtime
permissions, notification permission and background location do not have identical
request rules. Core flattens logical requests to manifest strings and maps results
back; source-confirmed alias/empty-request cases are in the permission audit.

Only the notifications feature includes its own
`android.permission.POST_NOTIFICATIONS` manifest declaration. Other required
manifest entries remain the app's responsibility. `RemoteNotification` is an iOS
APNs concept and is not Android push registration. Included notification
permissions must not be confused with excluded `calf-notifications`, which is not
a notification scheduling API.

Test both grant and revoke changes across `ON_RESUME`, permanently denied cases,
multiple logical permissions sharing one native permission, Android versions
before/after each permission change, ActivityResult owner availability, and
preview mode. Compose inspection mode intentionally returns inert granted state;
that is not production behavior.

## UI, navigation, WebView and geo

Adaptive UI uses `materialMain` Material3 actuals. UIKit-specific descriptors do
not create native Android UI and should be ignored only where the contract says
so. Android has a real Compose back handler for the adaptive navigation host;
the adaptive controller is still its own stack, not automatically AndroidX's.

WebView embeds `android.webkit.WebView` and cookie APIs. Apps own `INTERNET`,
network-security/cleartext policy, navigation trust and any camera/media request
policy inside web content. Do not expose arbitrary JavaScript or grant page
permissions based solely on a URL supplied by untrusted content. Read native
feature findings for actual settings/error/cookie behavior.

Geo's Android actual uses FusedLocationProviderClient and a lifecycle observer,
but received updates go to private channels rather than the public Compose
states. It remains an unpublished prototype, not functioning cross-platform
tracking. Background entitlement/permission and Play Services availability are
additional constraints, not fixes for that source-level wiring defect.

## Required verification

Use the build report's actual task names and results; old `testDebugUnitTest`
instructions refer to a previous AGP layout. Add host tests for pure algorithms
and ActivityResult state, then emulator/device tests for grants, document
providers, camera, WebView lifecycle and app recreation. Include minSdk and
current-SDK devices, low-memory/process-death scenarios, large files, inaccessible
providers and provider-export/security checks. An Android host test cannot prove
camera hardware, custom OEM document UI or production signing behavior.
