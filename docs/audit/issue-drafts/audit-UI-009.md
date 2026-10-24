# [Medium][UI-009] Time-state constructor checks the hour twice and never validates the minute on iOS

<!-- nativecmpkit-item:audit:UI-009 -->
## Classification
- **Finding:** UI-009
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.ios.kt:28-43`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.ios.kt#L28-L43) — `AdaptiveTimePickerState.init`
- [`calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.material.kt:25-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.material.kt#L25-L40) — `AdaptiveTimePickerState.init`

## Root cause
The second require uses initialHour in0..59 instead of initialMinute. iOS stores the invalid minute directly; the Material wrapper happens to delegate to another TimePickerState which may independently reject it.

## Impact and preconditions
iOS accepts initialMinute=-1 or60 and may normalize unexpectedly when constructing NSDateComponents/UIDatePicker. Public validation differs by target.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- The two guards are require(initialHour in0..23) and require(initialHour in0..59).
- Commit8b60a6063229e754253cdf6b2e58e604fa01e85a fixed the initial hour/minute swap, not this guard.
- Executed python3 docs/testing/ui-source-probes.py with cached Kotlin2.4.20/JDK21; the exact extracted init guard accepted minute-1 and60 while rejecting hour24. Material/iOS full classes were not loaded. See docs/testing/evidence/ui-source-probes.txt.

## Recommended solution
Validate initialMinute in0..59 in both actual constructors, with common contract tests including Saver restoration.

## Risks and compatibility
Previously fixed hour/minute initialization swap is a different bug and is not being reopened. A source-derived guard probe can validate this typo, but native time normalization still requires iOS.

## Required tests / acceptance criteria
- Minute-1,0,59,60; hour-1,0,23,24 on both actuals.
- Save/restore valid values and corrupted saved inputs.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/264
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
