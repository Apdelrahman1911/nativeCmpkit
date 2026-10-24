# [Medium][UI-019] Changing the sheet confirmation callback recreates remembered sheet state

<!-- nativecmpkit-item:audit:UI-019 -->
## Classification
- **Finding:** UI-019
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveSheetState.kt:28-50`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveSheetState.kt#L28-L50) — `rememberAdaptiveSheetState`

## Root cause
confirmValueChange is an input key to rememberSaveable. A newly captured callback instance invalidates the state instead of updating policy through a stable holder; the initialization value is always Hidden.

## Impact and preconditions
Ordinary recomposition with a changing callback capture can reset an active sheet state and, on iOS, trigger another show against an already-presented manager. State-dependent confirmation logic is especially susceptible.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- rememberSaveable explicitly includes confirmValueChange among its inputs.
- Upstream#116/#119 previously addressed state recreation; the former SheetValueHolder workaround is not present at baseline.

## Recommended solution
Keep the remembered state identity stable for callback changes and delegate to rememberUpdatedState, while retaining deliberate reset keys for structural policy changes. Revalidate density-derived thresholds separately.

## Risks and compatibility
Compose may memoize some lambdas, but genuinely changed captures create new callbacks. Do not rely on compiler lambda stability as the API contract.

## Required tests / acceptance criteria
- Open a sheet, change a value captured by confirmValueChange, and assert identity/currentValue remain stable while new policy is used.
- Restore state and change density; structural skip-flag changes follow documented policy.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/116
- https://github.com/MohamedRejeb/Calf/issues/119
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
