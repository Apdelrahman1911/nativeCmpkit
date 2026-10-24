# [High][PERM-008] iOS multi-permission launch is concurrent and returns singleton results rather than a complete batch

<!-- nativecmpkit-item:audit:PERM-008 -->
## Classification
- **Finding:** PERM-008
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.ios.kt:45-53,88-91`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.ios.kt#L45-L53) — `rememberMutablePermissionsState/launchMultiplePermissionRequest`

## Root cause
launchMultiplePermissionRequest loops synchronously over helpers that start asynchronous native requests. Each helper invokes onPermissionsResult(mapOf(permission to result)); there is no queue, deduplication by native domain, batch map, or completion barrier.

## Impact and preconditions
Clients cannot consume one complete batch like on Android. Different native prompts contend, location prerequisite order is lost, and aliases create multiple simultaneous helpers for the same OS domain. Empty batches never invoke a callback.

## Supporting evidence
- Commit9a33931/#422 replaced the previous unimplemented launch with this loop, resolving #248 only partially at the orchestration level.

## Recommended solution
Serialize prompt-producing requests, deduplicate equivalent native authorizations, aggregate results keyed by every requested logical permission, and define empty/cancelled batch completion. Keep progress callbacks separate if desired.

## Risks and compatibility
Source confirms concurrent dispatch and singleton callbacks. Exact prompt collision behavior varies by Apple API and needs device verification. Callback-contract changes should be documented as a behavioral correction.

## Required tests / acceptance criteria
- Camera+microphone, fine+coarse, foreground+background, Gallery+ReadImage and Notification+RemoteNotification batches.
- One complete callback, prompt ordering, repeated taps, empty list, disposal and OS denial.

## Dependencies
- PERM-003
- PERM-007
- PERM-009

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/248
- https://github.com/MohamedRejeb/Calf/pull/422
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
