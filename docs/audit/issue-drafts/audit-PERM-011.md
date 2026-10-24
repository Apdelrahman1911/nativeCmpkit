# [High][PERM-011] iOS calendar uses the iOS17 full-access API without availability gating or matching usage descriptions

<!-- nativecmpkit-item:audit:PERM-011 -->
## Classification
- **Finding:** PERM-011
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/calendar`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionHelper.kt:14-19`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/calendar/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionHelper.kt#L14-L19) — `launchPermissionRequest`
- [`docs/permissions.md:507-514`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/docs/permissions.md#L507-L514) — `calendar Info.plist example`
- [`sample/ios/Calf/Info.plist:27-28`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/ios/Calf/Info.plist#L27-L28) — `legacy NSCalendarsUsageDescription`

## Root cause
requestFullAccessToEventsWithCompletion is called unconditionally. That API is iOS17+, and modern full-access requests require NSCalendarsFullAccessUsageDescription; documentation and sample only declare NSCalendarsUsageDescription. Library target setup does not explicitly constrain consumers to17+.

## Impact and preconditions
Older supported consumer deployments can reach an unavailable selector; modern fresh-grant flows lack their required purpose string and cannot be relied on to authorize correctly (exact failure mode requires a device). The sample min18.5 masks older-OS availability, not the missing modern key.

## Supporting evidence
- CalendarPermissionHelper line18 invokes the modern method; no version condition exists in the file.
- Commit275e7d3 fixed always-granted status but left this request path unchanged.

## Recommended solution
Gate iOS17+ full-access API and provide legacy requestAccessToEntityType below17, or explicitly raise/document minimum supported iOS. Correct Info.plist docs/sample with modern and legacy keys as appropriate and validate a consuming native binary.

## Risks and compatibility
Do not infer a library iOS minimum from the sample target. Native availability/linking and purpose-string failure were source-reviewed, not executed on Apple hardware.

## Required tests / acceptance criteria
- iOS16 and17+ fresh installs with legacy key only, full-access key, denied/restricted, and grant from Settings.
- Native linker/availability checks at the documented lowest iOS deployment target.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/208
- https://github.com/MohamedRejeb/Calf/pull/233
- https://github.com/MohamedRejeb/Calf/pull/421
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
