# [Medium][UI-034] Cupertino slider gesture state has incomplete keys and uncancelled competing tap animations

<!-- nativecmpkit-item:audit:UI-034 -->
## Classification
- **Finding:** UI-034
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt:459-475,489-535,609-615,710-761`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt#L459-L475) — `draggableState / drag / pointerInput / cupertinoSliderTapModifier`

## Root cause
remember(valueRange) captures tickFractions without a steps key, and pointerInput(enabled,isRtl) captures range/ticks/interaction source without those keys. The custom horizontal pointer path updates values outside the draggableState MutatorMutex used by tap animations. drag sets isDragging=true but clears it only on normal return, not in finally.

## Impact and preconditions
Changing steps/range can retain old snapping inputs. A drag begun during a tap animation can receive competing value updates, while cancellation of a mutex mutation may leave isDragging=true and suppress later onValueChangeFinished.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Custom pointerInput introduced by d4ee7aa545002939392a20affe2e246287fc5c87 bypasses the draggableState used by the tap helper.
- isDragging=false follows mutateWith with no finally.

## Recommended solution
Use complete keys/latest-state holders and a single mutually exclusive gesture/animation mutation channel. Put isDragging cleanup in finally; cancel obsolete tap animations when new gestures take ownership.

## Risks and compatibility
The capture/cleanup gaps are source-confirmed; visible jitter and exact callback losses require a gesture runtime test. Do not replace the entire slider before targeted tests cover existing behavior.

## Required tests / acceptance criteria
- Change steps and range after initial composition and verify drag/tap/semantic parity.
- Tap then immediately drag/opposite tap; cancel an active mutation and assert isDragging resets.
- Interaction source replacement, RTL, disabled and completion callback counts.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
