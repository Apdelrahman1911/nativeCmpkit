# [High][PERM-021] Android LocationTracker suppresses missing-permission checks and ignores provider failures

<!-- nativecmpkit-item:audit:PERM-021 -->
## Classification
- **Finding:** PERM-021
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-geo`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:41-46,111-121`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt#L41-L46) — `bind/startTracking/stopTracking`
- [`calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt:7-10`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt#L7-L10) — `permission placeholder/startTracking`

## Root cause
startTracking is suspend but performs no permission request/check, ignores the returned Google Task and sets isStarted before registering. bind repeats the unchecked request when started. Null/unbound clients silently do nothing; null Looper assumes a suitable caller thread.

## Impact and preconditions
Missing/revoked permissions can throw or fail, unavailable Play Services/settings go unreported, and a successful return does not mean tracking started. A caller using a background coroutine can violate the null-Looper precondition.

## Supporting evidence
- Both registration sites suppress MissingPermission; the comment saying permission failures stop execution has no implementation.
- No await or Task success/failure listener exists in the file.

## Recommended solution
Inject/check permissions explicitly, await/map registration success/failure, require/main-dispatch an explicit Looper, validate bind/start order and expose unavailable/permission/error states. Roll back active state on failure; handle cancellation without leaking an update subscription.

## Risks and compatibility
Permission checks are still subject to TOCTOU revocation, so catch native security failures as well. Introducing automatic background permission escalation would be inappropriate; start should request only documented foreground capabilities.

## Required tests / acceptance criteria
- Denied/revoked/coarse-only permissions, unbound client, no Play Services/location settings off, failed registration/removal Task.
- Start from main/background, cancellation during registration, duplicate starts and recovery after errors.

## Dependencies
- PERM-018
- PERM-020

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/40
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
