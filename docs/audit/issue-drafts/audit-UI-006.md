# [Medium][UI-006] Compact Material date dialog can commit stale or newly forbidden scratch selections

<!-- nativecmpkit-item:audit:UI-006 -->
## Classification
- **Finding:** UI-006
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveCompactDatePicker.material.kt:50-66,100-108`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveCompactDatePicker.material.kt#L50-L66) — `AdaptiveCompactDatePicker / newDialogState`

## Root cause
The scratch DatePickerState is remembered without the hoisted state as a key. Its rule follows the original state, but its selection is not reconciled when that rule changes. Confirm writes the scratch selection directly to whichever state is currently passed, without revalidation.

## Impact and preconditions
A date chosen before bounds tighten can still be committed afterward; replacing the hoisted state during an open dialog transfers a selection governed by the old state into the new one.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- remember { state.newDialogState() } is not remember(state).
- keepSelection unconditionally assigns dialogState.selectedDateMillis and confirm TextButton is always enabled.

## Recommended solution
Key the edit transaction to the owning state, explicitly reconcile or reject a selected date when effective rules change, and validate at commit time. Specify whether state replacement cancels or restarts an open transaction.

## Risks and compatibility
The normal cancel/confirm transaction is sound and already tested. The issue concerns dynamic inputs, not every programmatic selection; preserve documented null selection and no-selectable-date policies.

## Required tests / acceptance criteria
- Open March15, choose March16, tighten maximum to March15, then confirm.
- Replace state/rules/yearRange while dialog is open.
- Rule rejects all days, null selection, cancel and reopening remain correct.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/543
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
