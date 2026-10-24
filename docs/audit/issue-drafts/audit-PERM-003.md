# [Medium][PERM-003] Android bulk/child permission requests do not consistently deliver completion callbacks

<!-- nativecmpkit-item:audit:PERM-003 -->
## Classification
- **Finding:** PERM-003
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt:70-95,130-140`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt#L70-L95) — `rememberMutablePermissionsState/launchMultiplePermissionRequest`

## Root cause
The empty-string safeguard returns without invoking onPermissionsResult when all permissions are filtered; mixed batches omit not-applicable keys. A child state within a multiple state has a RequestPermission callback that only refreshes status and never invokes the supplied parent result callback; its always-granted fast path does invoke it.

## Impact and preconditions
Callback-driven workflows can wait forever for a batch containing only out-of-range permissions, and child request behavior varies by native applicability. This survives the historical crash fix.

## Supporting evidence
- The only callback in bulk path is inside ActivityResult launcher; line136 guards launcher execution with no else.
- Child launcher lines85-89 refresh state but do not invoke its onPermissionResult.

## Recommended solution
Define and implement one completion contract: return a complete logical result map even for empty/not-applicable batches; route child launcher results to the current child/parent callback; document whether an empty input completes with an empty map.

## Risks and compatibility
Do not remove the filter added for Android10: passing empty permission strings was an actual historical crash. Callback normalization can reveal code relying on silence.

## Required tests / acceptance criteria
- Empty input, all-inapplicable input, mixed real/inapplicable input on API29/33.
- Launch a child state with a runtime permission and an always-granted permission; assert exactly one callback.
- Lifecycle disposal/recreation must not deliver duplicate callbacks.

## Dependencies
- PERM-002

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/386
- https://github.com/MohamedRejeb/Calf/pull/413
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
