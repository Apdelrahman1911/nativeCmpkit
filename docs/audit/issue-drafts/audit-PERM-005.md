# [Medium][PERM-005] Remembered permission objects retain obsolete result callbacks after recomposition

<!-- nativecmpkit-item:audit:PERM-005 -->
## Classification
- **Finding:** PERM-005
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt:39-45,63-81`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt#L39-L45) — `rememberMutablePermissionState/MutablePermissionStateImpl`
- [`calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.ios.kt:45-53`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutableMultiplePermissionsState.ios.kt#L45-L53) — `rememberMutablePermissionsState`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt:39-45,79-94`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt#L39-L45) — `rememberMutablePermissionState/fast path`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt:70-78`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt#L70-L78) — `rememberMutablePermissionsState`

## Root cause
Objects remembered only by permission/list capture onPermissionResult in a constructor val. Later recompositions with a new callback do not update it. Android ActivityResult callbacks use the recomposed lambda, but the direct always-granted path uses the old constructor callback; iOS uses it for every result.

## Impact and preconditions
A permission result can invoke stale navigation, state, or business logic after recomposition. Android behavior differs for runtime vs not-applicable permissions.

## Supporting evidence
- The remembered objects have immutable private callback fields, and remember keys omit callback identity.

## Recommended solution
Use rememberUpdatedState for callback delegation or update an internal callback holder every composition without recreating native helper state. Include context/lifecycle ownership in remembrance decisions.

## Risks and compatibility
Recreating the permission helper on every callback change would introduce native request churn and lose in-flight callbacks; preserve request identity while updating the callback reference.

## Required tests / acceptance criteria
- Recompose callback A to B, request same permission, assert only B is called.
- Repeat for iOS, Android runtime and empty-mapping fast paths, and child states within a batch.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
