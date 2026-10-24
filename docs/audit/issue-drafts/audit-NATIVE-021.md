# [Medium][NATIVE-021] Camera API silently drops unsupported, cancelled and failed operations

<!-- nativecmpkit-item:audit:NATIVE-021 -->
## Classification
- **Finding:** NATIVE-021
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-camera-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt:7-14`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt#L7-L14) — `CameraPickerLauncher and onResult contract`
- [`calf-camera-picker/src/desktopMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.desktop.kt:8-19`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/desktopMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.desktop.kt#L8-L19) — `Desktop no-op launcher`
- [`calf-camera-picker/src/webMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.web.kt:8-19`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/webMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.web.kt#L8-L19) — `Web no-op launcher`
- [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:30-49`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L30-L49) — `launch/handleResult`
- [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:57-76`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L57-L76) — `finish/cancel delegate`

## Root cause
Only a non-null KmpFile success callback is modeled. Desktop/Web launch are Unit no-ops; Android no-camera/cancel returns nothing; iOS cancel, image-conversion and write failures all disappear without an outcome. Other launch exceptions escape instead.

## Impact and preconditions
Callers cannot reliably clear busy UI, distinguish denial/cancellation/unavailable from a pending picker, or feature-detect desktop/web. Common availability is misleading despite compilation succeeding.

## Supporting evidence
- Desktop/Web launch bodies are literally Unit; error/cancel paths in mobile have no callback.
- Upstream request288 is source-satisfied for basic mobile capture, not desktop/web.

## Recommended solution
Add a result/capability API covering success, cancellation, unavailable and categorized failure, while keeping the legacy success-only callback as an adapter. Do not pretend unsupported platforms captured an image. Document permission requirements and iOS photo-library fallback.

## Risks and compatibility
Adding cases to existing public sealed types can break exhaustive callers; this API currently has no result type, so use an additive overload/type and migration guidance. Do not silently implement a major camera engine during this audit.

## Required tests / acceptance criteria
- Every platform produces one defined terminal outcome for cancel/unavailable/error.
- No camera app, feature absent, permission denied and iOS simulator library fallback.
- Desktop/Web capability checks align with launcher behavior.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/28
- https://github.com/MohamedRejeb/Calf/issues/288
- https://github.com/MohamedRejeb/Calf/pull/274
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
