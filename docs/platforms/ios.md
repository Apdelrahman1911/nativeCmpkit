# iOS implementation guide

Baseline `af388bd` declares `iosArm64` and `iosSimulatorArm64`, not `iosX64`.
There is no standalone native macOS target. Building/linking/running UIKit and
Objective-C interop requires a suitable macOS/Xcode host. None of this audit's
Linux source inspection establishes simulator/device test success.

## Framework and Objective-C ownership

The sample builds a static `Common` framework from `sample/common`; it explicitly
exports `calf-ui` in `sample/common/build.gradle.kts`. UIKit target/action and
Kotlin-exported selectors have historically produced `unrecognized selector`
failures (#189/#210/#330/#341/#381). Do not remove the framework export or change
Objective-C-visible symbols without an actual consuming-Xcode-app test.

Native object lifetimes differ from Compose lifetimes. UIKit delegate/target
properties can be weak; `remember` and explicit manager fields must keep the
actual callback target alive for as long as the OS uses it. Strong-reference
fixes for dialog text-field targets (#525) do not prove every delegate in the
library is retained. Pair presentation with dismissal and composition disposal;
late native callbacks need cancellation/once-only guards and safe state updates.

## UI availability and layout

- iOS 16+ inline date selection uses `UICalendarView`; older inline paths and
  wheels/compact use `UIDatePicker`. Arbitrary `SelectableDates` rules require
  reconciliation where UIKit only supports a min/max interval.
- iOS 26 glass-specific behavior is gated through `isIOS26OrAbove` in UI helpers,
  but some iOS visuals are custom Compose/backdrop rendering. Circular progress
  is a Compose Cupertino Canvas indicator, not `UIActivityIndicatorView`.
- Native top/tab bars are added to the hosting UIViewController's view. Their
  measured padding is fed into a Compose scaffold; rotation/transition overlap
  requires explicit tests (#548 and #530).
- Material content slots and style objects do not all apply to UIKit. For example
  native alerts use text/actions/descriptors rather than `materialContent`, and
  native bars use `ios*` item models. Toolbars with empty native items do not
  become a Material toolbar on iOS.
- Table cell tint, Dynamic Type, VoiceOver, RTL, popover anchors on iPad, safe-area
  changes and multiple windows need device/SDK-specific coverage.

Do not read the sample's deployment settings as a verified minimum for every
module: its project has iOS 26.0 build settings and target overrides of 18.5.
Some library helpers reference newer APIs without sufficient old-version guards
(for example calendar full-access requests). A full minimum-SDK matrix requires
link/runtime tests, not the existence of a fallback comment.

## File providers, Photos and capture

`KmpFile.url` is intended to be the readable picked copy; `originalUrl` preserves
provider metadata identity. Photos' `loadFileRepresentation` URL is temporary, so
copying must complete before that callback expires. Document URLs can require
balanced security-scoped access. Directories, transient copies and cancellation
have different ownership. Baseline file export can move instead of copy and can
leak UUID-prefixed staging names; proposed fixes/bookmarks in upstream PR #551
are **unmerged**, not existing functionality.

Image representation defaults to compatible mode to help Compose/Skia decode
HEIC-origin assets; callers can request `Current` through `FilePickerSettings`.
This choice is explicit history, not evidence every RAW/live-photo/video variant
is correctly processed. Read and write helpers contain unsafe native buffer
boundaries requiring tests; see the I/O audit before relying on byte-array reads.

Camera uses `UIImagePickerControllerOriginalImage`, PNG staging and a picker
delegate. Physical capture, cancellation, missing hardware and repeated
presentation cannot be validated by assuming simulator behavior equals device
behavior. Sharing is a separate `UIActivityViewController` flow with its own
completion, temporary-file and iPad presentation requirements.

## Permission capabilities and privacy declarations

Prefer feature artifacts rather than the aggregate when only a subset is needed.
Upstream #253 motivated modularization because even referenced native APIs can
trigger App Store privacy-purpose-string requirements. The aggregate still links
all those references. These are relevant keys/areas, not a complete verified App
Store submission recipe:

| API family | Integration responsibility |
|---|---|
| AVFoundation camera / microphone | `NSCameraUsageDescription`, `NSMicrophoneUsageDescription`, appropriate native authorization flow |
| Photos | Photo library purpose/access mode; limited library differs from full access |
| CoreLocation | Foreground and, only if needed, always/background descriptions/capabilities; foreground grant does not mean background authorization |
| CoreBluetooth | Applicable Bluetooth purpose keys and actual OS authorization state; hardware powered off is a different condition |
| Contacts | `NSContactsUsageDescription`; access request is not contact retrieval API |
| EventKit | Version-appropriate calendar full-access/write-only purpose keys and availability guards; baseline docs/sample only showing legacy key are insufficient for newer calls |
| UserNotifications / APNs | Authorization and remote registration/capability are different operations; configure app entitlement/backend separately |
| Local network | `NSLocalNetworkUsageDescription`, correct service declarations/policy for the NSNetService operation; startup timing/timeout is not authoritative authorization |

The sample uses “Just for tests” strings; replace with real purpose descriptions
before an application submission. It is not a production privacy manifest.
Helpers' `Denied(shouldShowRationale)` mapping is a library convention, not a
native iOS rationale flag. Concurrent requests, status refresh after Settings,
restricted/limited/write-only states and background-location upgrades all have
documented audit issues.

## WebKit and native boundaries

WebView uses WKWebView plus KVO observations and navigation callbacks. The
handwritten Objective-C protocol in `calf-webview/src/iosMain/cinterop/
nskeyvalueobserving.def` produces compiler bindings for the KVO receiver. Every
observer attachment needs safe matching removal; the WK cookie store and
JavaScript callback lifetime must stay associated with the correct view.
Historical #34 is about camera UI *inside WebView*, not `calf-camera-picker`;
its exact dismissal behavior still needs a native reproduction.

## Verification needed

Run shared state tests, iOS-specific interop tests and a real consuming Swift app
on the supported SDK range. Include iPad popovers, rotation/multiwindow, real
camera, Photos with HEIC/live photos/iCloud, document providers, permission
revocation, Bluetooth disabled/unknown and multiple simultaneous permission
states. Separate simulator evidence from physical-device and App Store validation.
No source comment or historical PR checklist substitutes for those runs.
