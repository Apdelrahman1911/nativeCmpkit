# [Medium][PERM-024] Storage guidance asks for all-files access that WriteStorage never requests or verifies

<!-- nativecmpkit-item:audit:PERM-024 -->
## Classification
- **Finding:** PERM-024
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`docs/permissions.md:162-174`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/docs/permissions.md#L162-L174) — `Write Storage Android example`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt:15-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/StoragePermissions.android.kt#L15-L22) — `registerWriteStoragePermission`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt:118-126`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt#L118-L126) — `getPermissionStatus`

## Root cause
Docs add MANAGE_EXTERNAL_STORAGE with a ScopedStorage lint suppression, but WriteStorage only maps WRITE_EXTERNAL_STORAGE through API28. On newer OS versions it becomes an empty mapping/Granted; special all-files settings and Environment.isExternalStorageManager are not used.

## Impact and preconditions
Consumers can copy an overbroad, Play-policy-sensitive permission while wrongly assuming the library requested/verified all-files access. The manifest entry alone does not confer access. This is misleading guidance and least-privilege risk, not a demonstrated data-exfiltration vulnerability.

## Supporting evidence
- Manifest recommendation and implementation do not refer to the same permission.
- Historical #184/#195/#263/#386 show prior storage-version issues; API-range behavior was intentional and should not be mistaken for all-files authorization.

## Recommended solution
Remove the all-files permission from ordinary storage examples; explain app-scoped storage/SAF/media permissions and modern scoped-storage limits. If an all-files API is ever added, make it separate, explicit and policy-aware.

## Risks and compatibility
Legacy apps targeting old storage models need a migration explanation, not blanket claims that no permission is required on every Android29+ combination. Coordinate with sample least-privilege finding rather than duplicate it.

## Required tests / acceptance criteria
- API28 legacy permission, API29 legacy/scoped target modes, API30+ app-scoped/SAF and all-files absent/present.
- Verify docs examples request the least permissions needed and no Granted result is described as unrestricted disk access.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/184
- https://github.com/MohamedRejeb/Calf/pull/195
- https://github.com/MohamedRejeb/Calf/pull/263
- https://github.com/MohamedRejeb/Calf/issues/386
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
