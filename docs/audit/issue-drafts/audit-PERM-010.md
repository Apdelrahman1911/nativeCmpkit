# [Medium][PERM-010] iOS location delegates consume pending requests on nonterminal events and overwrite overlapping callbacks

<!-- nativecmpkit-item:audit:PERM-010 -->
## Classification
- **Finding:** PERM-010
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/location`, `calf-permissions/background-location`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocationPermissionHelper.kt:16-20,28-34,67-79`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocationPermissionHelper.kt#L16-L20) — `pending callback/LocationManagerDelegate`
- [`calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BackgroundLocationPermissionHelper.kt:14-18,26-32,62-71`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BackgroundLocationPermissionHelper.kt#L14-L18) — `pending callback/BackgroundLocationManagerDelegate`

## Root cause
Every delegate status except accepted authorization is treated as final false, including NotDetermined. The enclosing delegate closure clears the single pending callback after invoking it. A new request overwrites the previous callback, and a reentrant callback can install a new one that is then cleared by the old completion.

## Impact and preconditions
An initial/in-progress authorization event arriving while a request is pending completes it as denied and drops the later grant; rapid/reentrant requests lose results. Apple schedules initial authorization callbacks when a manager initializes, making event ordering important.

## Supporting evidence
- Actual LocationPermissionHelper + LocationManagerDelegate with a controlled manager produced [false] for NotDetermined then AuthorizedWhenInUse, dropping the grant.

## Recommended solution
Ignore nonterminal status events, correlate callbacks to request generation, clear/take the old callback before invocation, coalesce or reject overlap explicitly, and cancel pending work at owner disposal.

## Risks and compatibility
The adapter test deliberately injects NotDetermined after launch; frequency and timing on actual iOS devices are not established. Permission UI cannot be reliably cancelled, so disposal should suppress delivery without claiming OS revocation.

## Required tests / acceptance criteria
- Initial NotDetermined followed by grant/deny produces one terminal result.
- Double tap, reentrant launch in callback, status event after disposal, multiple helper instances.

## Dependencies
- PERM-007
- PERM-009

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/229
- https://github.com/MohamedRejeb/Calf/pull/244
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
