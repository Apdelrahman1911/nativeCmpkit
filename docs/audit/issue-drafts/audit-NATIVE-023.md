# [Medium][NATIVE-023] iOS camera has no in-flight presentation guard or lifecycle-bound cleanup

<!-- nativecmpkit-item:audit:NATIVE-023 -->
## Classification
- **Finding:** NATIVE-023
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-camera-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:29-32,49-95`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L29-L32) — `launch, delegate storage and presentation`

## Root cause
Each launch replaces the single pickerDelegate field and schedules another presentation without checking an already-presented controller or active request. Delegate completion calls onResult before dismissal/clearing; a reentrant launch or throwing callback can skip cleanup or overwrite the new operation delegate. Composition disposal is not handled.

## Impact and preconditions
Rapid/reentrant launch can cause UIKit presentation rejection, lost/weak delegates or results; leaving the screen can leave a controller/work active. A throwing callback can leave the original picker undismissed. These cases are not safely serialized.

## Supporting evidence
- launch unconditionally overwrites pickerDelegate at88; completion invokes onResult at64 then clears shared field at70.
- No DisposableEffect/close/in-flight flag exists in the iOS launcher.

## Recommended solution
Represent an explicit active request with a single-flight guard and stable owner, dismiss/clear in finally using instance identity, and define cancellation on owner disposal. Deliver user callbacks after internal lifecycle cleanup when appropriate.

## Risks and compatibility
UIKit/device timing and GC outcomes were not reproduced. The source shows missing guards/order, not guaranteed crash for every double tap. Coordinate callback ownership with NATIVE-020.

## Required tests / acceptance criteria
- Double tap launch, callback launches again, callback throws, owner navigates away.
- Denied permissions, camera unavailable, simulator fallback and presentation over another modal.
- Exactly one active picker and no old delegate cleanup clears a replacement operation.

## Dependencies
- NATIVE-020

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/326
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
