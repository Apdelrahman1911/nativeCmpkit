# [High][NATIVE-019] Android camera loses its output URI across Activity/process recreation

<!-- nativecmpkit-item:audit:NATIVE-019 -->
## Classification
- **Finding:** NATIVE-019
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-camera-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:28,35-48,59-73`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L28) — `imageUri and rememberCameraPickerLauncher`

## Root cause
The pending image URI is stored only inside a newly remembered CameraPickerLauncherAndroidImpl. ActivityResultRegistry can deliver a restored TakePicture Boolean, but the recreated instance has imageUri=null and drops the successful result.

## Impact and preconditions
Capturing a photo while the host Activity is recreated or process is reclaimed loses the application result and leaves the camera-created file orphaned. The most important user action can appear to succeed in the camera app but disappear on return.

## Supporting evidence
- imageUri initializes null at28; only launch assigns it at42; handleResult requires non-null at47.
- remember rather than rememberSaveable is used for both holder and launcher.

## Recommended solution
Persist the pending output URI/request state with saveable state or an explicit saved-state owner before launching. Restore it before result delivery, clear it after terminal completion and handle interrupted requests deliberately.

## Risks and compatibility
This is a source-traced lifecycle defect; no Android device/emulator Activity recreation test was run by this reviewer. Do not persist a granted URI longer than its actual access lifetime without an ownership policy.

## Required tests / acceptance criteria
- Enable dont-keep-activities, launch camera, capture, return and receive exactly one readable KmpFile.
- Rotate/recreate and simulate process death while external camera is foreground.
- Cancelled/restored requests remove only library-owned temporary files and do not deliver stale URI.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/274
- https://github.com/MohamedRejeb/Calf/pull/302
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
