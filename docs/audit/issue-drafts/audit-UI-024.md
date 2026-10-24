# [Medium][UI-024] Dropdown availability check rejects later iOS major versions and selects a private-gesture fallback

<!-- nativecmpkit-item:audit:UI-024 -->
## Classification
- **Finding:** UI-024
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.ios.kt:120-136,197-202`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.ios.kt#L120-L136) — `isPerformPrimaryActionAvailable / expanded effect`

## Root cause
Availability is tested as major>=17 && minor>=4 instead of lexicographic version comparison. iOS18.0 and26.0 therefore use the older workaround, which looks up a private UITouchDownGestureRecognizer class and fabricates touchesBegan(emptySet(),UIEvent()).

## Impact and preconditions
Menus on supported newer OS versions take an unnecessary fragile path and may fail as private recognizer internals change. Store-review/platform-compatibility exposure is a risk, not an observed rejection.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- The literal return expression requires minor>=4 even when major>17.
- Fallback matches NSStringFromClass(...)=UITouchDownGestureRecognizer and invokes touchesBegan.
- Executed the exact extracted comparator under a UIDevice string stub:17.3=false,17.4=true,17.10=true,18.0=false,26.0=false,26.4=true. This reproduces the comparator defect, not native menu presentation. Script and log: docs/testing/ui-source-probes.py, docs/testing/evidence/ui-source-probes.txt.

## Recommended solution
Use major>17 || (major==17 && minor>=4), preferably a shared tested version helper, and replace the private-gesture technique with a supported presentation fallback or explicitly limited platform behavior.

## Risks and compatibility
Do not conflate the already fixed systemVersion.toDouble crash in other widgets with this separate comparator. Native performPrimaryAction behavior still requires execution.

## Required tests / acceptance criteria
- Version cases17.3,17.4,17.10,18.0,26.0,26.4 and malformed components.
- Programmatic open on supported OS and documented behavior on older OS.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/commit/0fe18423425011a6fb212eaffe5aa4eee081f041
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
