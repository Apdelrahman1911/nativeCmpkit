# [Medium][PERM-006] Permission lifecycle refresh skips previously granted permissions, leaving revocations stale

<!-- nativecmpkit-item:audit:PERM-006 -->
## Classification
- **Finding:** PERM-006
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionsUtil.ios.kt:22-29,53-61`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionsUtil.ios.kt#L22-L29) — `PermissionLifecycleCheckerEffect/PermissionsLifecycleCheckerEffect`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/PermissionsUtil.android.kt:29-36,60-68`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/PermissionsUtil.android.kt#L29-L36) — `PermissionLifecycleCheckerEffect/PermissionsLifecycleCheckerEffect`

## Root cause
ON_RESUME refresh is conditional on cached status not being Granted. The comment assumes revocations cause process restart; that is not a valid blanket guarantee across iOS permission types or notification settings.

## Impact and preconditions
When the app survives a settings change from granted to denied, the state remains granted until a later explicit request/recreation. Notification settings are an especially important iOS scenario. Cache status must not be treated as authorization enforcement.

## Supporting evidence
- Both platform observers explicitly guard refresh with status != Granted.
- Archived #313/#331 added iOS resume support; #411 later reports settings-return staleness, not proof of this exact grant-to-deny path.

## Recommended solution
Refresh all tracked permissions on resume, with lightweight per-type status queries and asynchronous generation ordering. Remove the process-restart assumption; avoid re-triggering Wi-Fi prompts while fixing refresh.

## Risks and compatibility
Unconditional refresh currently invokes the intrusive Wi-Fi status getter; fix PERM-013 or exempt side-effecting probes first. Revocation process behavior differs by OS and permission and needs devices.

## Required tests / acceptance criteria
- Granted notification/camera/location toggled off in Settings then resume without process death.
- Denied-to-granted, one-time grant expiry, repeated resumes, batched permissions and lifecycle disposal.

## Dependencies
- PERM-013

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/313
- https://github.com/MohamedRejeb/Calf/pull/331
- https://github.com/MohamedRejeb/Calf/issues/411
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
