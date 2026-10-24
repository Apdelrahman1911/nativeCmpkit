# [Medium][NATIVE-024] Camera capture does synchronous full-resolution PNG work and has no temporary-file ownership policy

<!-- nativecmpkit-item:audit:NATIVE-024 -->
## Classification
- **Finding:** NATIVE-024
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-camera-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:57-83`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L57-L83) — `UIImagePNGRepresentation and saveTempImageFile`
- [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:35-49`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L35-L49) — `cache output and handleResult`

## Root cause
The iOS delegate synchronously encodes the original full-resolution UIImage as PNG and atomically writes the whole NSData before dismissing/calling success. iOS random-named and Android timestamp-named temporary files have no cleanup/ownership contract; cancelled/abandoned Android captures are not deleted.

## Impact and preconditions
Large photos can stall the main thread and temporarily retain decoded image plus PNG buffer plus file-write resources. Repeated captures can accumulate sensitive photos/cache space until external cleanup; callers do not know when returned files may disappear.

## Supporting evidence
- UIImagePNGRepresentation, NSData writeToFile and callback all execute inside the UIKit result delegate synchronously.
- Neither platform has a delete/close/TTL path for capture outputs.

## Recommended solution
Measure representative large images, move safe encoding/file work off the UI thread, offer bounded format/quality/resolution policy, and define explicit ownership/TTL for returned files. Delete only failed/cancelled library-owned outputs; successful files must remain valid for documented consumption.

## Risks and compatibility
Latency/OOM/disk growth magnitude is workload/device-dependent and was not benchmarked. Temporary directories are OS-managed but not immediate guaranteed cleanup. JPEG/HEIF choices affect transparency, quality, orientation and metadata.

## Required tests / acceptance criteria
- Real-device 12/48MP capture latency, peak resident memory and UI responsiveness.
- Disk-full/write-failure/cancel/repeated capture and cache eviction.
- File remains readable for expected consumer lifetime; cleanup never deletes another request file.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/311
- https://github.com/MohamedRejeb/Calf/pull/326
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
