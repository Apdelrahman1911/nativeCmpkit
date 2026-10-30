<!-- nativecmpkit-upstream-sync:674932206:288 -->
<!-- source-fingerprint:50a3daf3dcdac0b9c5087045f601516b2c64bad6c5371ad4fadfe3fb6903c4b0 -->
## Current upstream context: Calf #288

Original: [Request this library can take camera](https://github.com/MohamedRejeb/Calf/issues/288) — [hafizkloudius014](https://github.com/hafizkloudius014); created `2025-05-08T01:19:11Z`, updated `2025-05-14T01:33:13Z`; upstream state **open**.
Original IDs: `3047538206` / `I_kwDOKDql7s61pb4e`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Source-addressed historical request; not a new confirmed bug, and not evidence of a device/runtime pass.

Android and iOS camera capture code exists in the baseline (PR274 and later PR326). The feature request is source-satisfied, but capture has separately tracked correctness/setup/lifecycle risks; no device pass is claimed.

**Next step:** Point documentation to existing camera API/setup and native camera findings; do not recreate a duplicate request to add the already existing Android/iOS module.

Primary tracking: #77. Related existing tickets: #13, #76, #78, #79, #80.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt:1-15`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt#L1-L15) — `rememberCameraPickerLauncher`
- [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:22-74`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L22-L74) — `Android camera launcher`
- [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:24-106`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L24-L106) — `iOS camera launcher`

### Original issue description (verbatim Markdown)
````markdown
Hi I would like to request if this library could take camera pictures for ios and android. Thanks.
````

### Original public discussion (1 comments)

**[hafizkloudius014](https://github.com/hafizkloudius014)** — created `2025-05-14T01:33:12Z`, updated `2025-05-14T01:33:12Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/288#issuecomment-2878374001); IDs `2878374001` / `IC_kwDOKDql7s6rkIBx`.
````markdown
@MohamedRejeb is this library can take photo camera for ios and android?
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/288/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/288/comments.json)
- [Full public timeline: 4 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/288/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:19:19Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/288)); [[Medium][NATIVE-021] Camera API silently drops unsupported, cancelled and failed operations](https://github.com/Apdelrahman1911/nativeCmpkit/issues/77).
