# [Medium][NAV-015] Android sample permission menu and manifest disagree and declare unrelated broad permissions

<!-- nativecmpkit-item:audit:NAV-015 -->
## Classification
- **Finding:** NAV-015
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `sample:android`, `sample:common`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/PermissionsScreen.kt:53-80`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/PermissionsScreen.kt#L53-L80) — `PermissionScreen requested permissions`
- [`sample/android/src/main/AndroidManifest.xml:9-37`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/android/src/main/AndroidManifest.xml#L9-L37) — `uses-permission declarations`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt:37-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt#L37-L40) — `Permission.Call mapping`

## Root cause
The menu requests Permission.Call, mapped to CALL_PHONE, but the sample manifest never declares CALL_PHONE. Conversely it declares MANAGE_EXTERNAL_STORAGE and READ/SEND/RECEIVE_SMS without a corresponding special-access workflow/SMS demo in this sample.

## Impact and preconditions
The Call permission example cannot demonstrate a normal grant for the declared app. Broad/unrelated declarations mislead integrators and can impose distribution-policy scrutiny; a declaration alone does not grant access or establish a security vulnerability.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Permission.Call is the first menu row at line56; no CALL_PHONE declaration occurs in sample manifest lines9-37.
- StoragePermissions.android.kt maps Permission.Call to Manifest.permission.CALL_PHONE.
- MANAGE_EXTERNAL_STORAGE is declared at14-15 and SMS at35-37. iOS calendar/Bonjour mismatches are assigned to the separate permissions audit.
- Cross-review boundary: PERM-024 owns the broad-storage documentation/WriteStorage special-access mismatch. NAV-015 primarily fixes Call/menu/manifest consistency; unrelated broad declarations are context, not a duplicate all-files-access issue.

## Recommended solution
Align explicit demonstration scenarios and merged manifests; remove unrelated permissions or split narrowly scoped demo variants. Teach special-access APIs separately from ordinary runtime permissions. Keep Android SDK/version constraints and iOS usage keys in the permission module's test matrix.

## Risks and compatibility
Do not add sensitive permissions to a general sample merely to make all status rows turn green. FileProvider is nonexported and uses grantUriPermissions; its cache path is not evidence of universally exposed storage.

## Required tests / acceptance criteria
- Inspect the merged manifest and map every menu permission to its expected declaration/status for supported API levels.
- Test Call on a fresh installation under an explicitly approved demo variant.
- Verify file/image picker operation without MANAGE_EXTERNAL_STORAGE and unrelated SMS permissions.
- Run permission denial/permanent-denial and Android13/14 media-selection scenarios.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
