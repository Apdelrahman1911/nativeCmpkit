# [Medium][NATIVE-020] Camera callback/lifetime handling is unstable across recomposition

<!-- nativecmpkit-item:audit:NATIVE-020 -->
## Classification
- **Finding:** NATIVE-020
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-camera-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:22-25,59-73`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L22-L25) — `CameraPickerLauncherAndroidImpl and remember factory`
- [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:29-30,100-105`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L29-L30) — `pickerDelegate and remember(viewController,onResult)`

## Root cause
Android remember has no keys and permanently captures the first onResult/context. iOS keys the whole launcher on onResult, so replacing an inline callback replaces the object that owns the strong UIImagePicker delegate reference during an in-flight operation.

## Impact and preconditions
Android can call a stale handler capturing an obsolete item/navigation identity. iOS has a conditional delegate-lifetime risk when old launcher ownership is lost on recomposition; the existing strong-reference fix is only effective while that launcher remains retained.

## Supporting evidence
- Android launcher construction closes over onResult only once at70.
- iOS remember(viewController,onResult) creates a new launcher for changed function identity; UIKit delegate is weak.

## Recommended solution
Remember one launcher per platform host, keep onResult current via rememberUpdatedState, and explicitly retain/clear active operation delegates independent of changing callbacks. Define which callback receives an in-flight request result.

## Risks and compatibility
Android stale capture is source-confirmed. Premature iOS deallocation under Kotlin/Native GC is a risk, not reproduced; do not undo the original strong delegate retention from PR326.

## Required tests / acceptance criteria
- Change callback from A to B while capture is active and assert agreed callback semantics.
- Repeated ordinary recompositions do not replace iOS active operation owner.
- Force Kotlin/Native GC/memory pressure during presentation and verify delegate callbacks still arrive.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/326
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
