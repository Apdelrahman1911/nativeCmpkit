# [Medium][PERM-012] iOS WriteCalendar requests full read/write access and rejects write-only authorization

<!-- nativecmpkit-item:audit:PERM-012 -->
## Classification
- **Finding:** PERM-012
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/calendar`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/CalendarPermissions.ios.kt:6-15`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/CalendarPermissions.ios.kt#L6-L15) — `registerReadCalendarPermission/registerWriteCalendarPermission`
- [`calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionHelper.kt:18,27-41`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionHelper.kt#L18) — `requestFullAccessToEventsWithCompletion/getPermissionStatus`

## Root cause
ReadCalendar and WriteCalendar construct the same full-access helper. Modern EKAuthorizationStatusWriteOnly is not handled and falls through to Denied(true), preventing an app with legitimate write-only authorization from being represented as granted for WriteCalendar.

## Impact and preconditions
Write-only consumers are prompted for unnecessary read access and can be blocked even when the OS permits their required operation; this violates least privilege and cross-platform logical naming.

## Supporting evidence
- Both registration functions instantiate CalendarPermissionHelper() without a mode. The status switch has no WriteOnly branch.

## Recommended solution
Pass a requested access mode into the helper. On iOS17+ use write-only event authorization and recognize WriteOnly for WriteCalendar; keep legacy behavior below17 with explicit documentation.

## Risks and compatibility
Callers relying on WriteCalendar to read events will need ReadCalendar/full access explicitly. This is a capability-contract change requiring migration notes and correct purpose strings.

## Required tests / acceptance criteria
- Fresh WriteCalendar requests only write access.
- WriteOnly grants WriteCalendar but not ReadCalendar; full access grants both; restricted/denied remain denied.

## Dependencies
- PERM-011

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/421
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
