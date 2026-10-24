# [High][PERM-002] Android bulk results are assigned to the first global permission alias, not the requested permissions

<!-- nativecmpkit-item:audit:PERM-002 -->
## Classification
- **Finding:** PERM-002
- **Priority:** High
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`, `calf-permissions/gallery`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt:34-38`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt#L34-L38) — `findByAndroidString`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt:40-49,144-151`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt#L40-L49) — `bulk callback/updatePermissionsStatus`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt:5-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt#L5-L12) — `registerReadStoragePermission`
- [`calf-permissions/gallery/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/GalleryPermissions.android.kt:5-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/gallery/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/GalleryPermissions.android.kt#L5-L12) — `registerGalleryPermission`

## Root cause
Reverse mapping selects firstOrNull from the global registry. Gallery and ReadStorage both map to READ_EXTERNAL_STORAGE on API<=32. Registration order is unrelated to the active request; updatePermissionsStatus only refreshes the matching logical permission.

## Impact and preconditions
Requesting Gallery after ReadStorage was initialized can report ReadStorage instead, omit Gallery, and leave its status stale. Requesting both refreshes only one alias; custom aliases have the same problem.

## Supporting evidence
- Compiled unmodified AndroidPermissionRegistry plus extracted original Permission and mapping helpers with a Build.VERSION stub; at SDK32 a result for requested Gallery became {ReadStorage=true}.
- This test validates Kotlin mapping, not an Android permission dialog.

## Recommended solution
Convert each result using the request-scoped logical-permission-to-native-string mapping; fan a native result out to every requested logical alias, deduplicate native strings, and never substitute an unrelated global alias.

## Risks and compatibility
Callback maps may expand for callers that accidentally depended on one alias. Include SDK ranges and empty/not-applicable permissions without reintroducing empty launcher inputs.

## Required tests / acceptance criteria
- Initialize ReadStorage then request only Gallery; reverse the initialization order.
- Request both aliases and assert both state objects and callback entries.
- Run SDK28/32/33 and custom aliases; ensure only requested keys are returned.

## Dependencies
- PERM-001

## Historical context
- https://github.com/MohamedRejeb/Calf/commit/7d382c69ba93e218a210239ed9dfc99a34660be0
- https://github.com/MohamedRejeb/Calf/pull/263
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
