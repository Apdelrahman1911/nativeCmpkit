# [Low][UI-008] No-selectable-day fallback is intentional but requires an explicit caller-visible validation policy

<!-- nativecmpkit-item:audit:UI-008 -->
## Classification
- **Finding:** UI-008
- **Priority:** Low
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/SelectableDays.kt:92-115,124-133,152-160`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/SelectableDays.kt#L92-L115) — `nearestSelectableDay / resolvePickedDay / snapSelectionToSelectable`
- [`calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBoundsTest.kt:91-108`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBoundsTest.kt#L91-L108) — `no selectable day tests`
- [`calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerStateMaterialTest.kt:122-129`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerStateMaterialTest.kt#L122-L129) — `selection is kept when no selectable day is within reach`

## Root cause
Nearest-date search is bounded to366 days in each direction. If no valid day is found, resolvePickedDay returns the original rejected pick and rule-change snapping keeps the previous selection. Existing tests deliberately specify this behavior; no validity result is exposed.

## Impact and preconditions
Consumers may assume a SelectableDates-constrained picker guarantees a valid selected value. Sparse rules can have a valid day beyond the search window while the state retains an invalid day; the picker must not be used as sole business/security validation.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- The retained invalid-selection behavior is explicitly asserted by two existing tests.
- nearestSelectableDay defaults maxDistanceDays to366; resolvePickedDay falls back with ?: pickedMillis.

## Recommended solution
Document the bounded search, later-day tie break and keep-selection fallback prominently. Consider an additive validity/result API or configurable no-valid-date policy instead of silently changing established behavior.

## Risks and compatibility
This is not classified as an accidental bug or vulnerability. Clearing the value could break compatibility and is an owner/API decision.

## Required tests / acceptance criteria
- NoDates, valid day367+ days away, tie between previous/next, changing effective bounds.
- Tests for chosen explicit validity/empty-selection policy and its accessibility announcement.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/541
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
