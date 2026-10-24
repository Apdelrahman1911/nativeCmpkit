# [High][UI-012] Presented iOS alerts update their text but retain original action and text-field callbacks

<!-- nativecmpkit-item:audit:UI-012 -->
## Classification
- **Finding:** UI-012
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt:54-96,112-123,209-215`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt#L54-L96) — `dialogUIViewController / updateDialogProperties / toUIAlertAction`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.ios.kt:66-94,118-133`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.ios.kt#L66-L94) — `AdaptiveAlertDialog / AdaptiveBasicAlertDialog`

## Root cause
UIAlertAction handlers and text-field targets are constructed once and capture original immutable action/textField objects. Recomposition replaces iosProperties and updates title/message/enabled by index, but never replaces or redirects callbacks.

## Impact and preconditions
An alert can display newly supplied recordB text while its confirm handler still mutates/deletes recordA. Form edits may reach an obsolete handler. This is more serious than merely stale labels because visible user intent and performed action can differ.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- updateDialogProperties assigns title/message and enabled only.
- toUIAlertAction invokes the onClick captured from its extension receiver; textFieldDidChange captures textFieldState.
- Upstream#519 fix77eeaeb2d249ee559debf82dd2535b4dad733ec8 addressed display updates but not live callbacks.

## Recommended solution
Use latest callback holders addressed by stable action/field identity. Define which structural properties can change during presentation and recreate safely when unsupported structure changes; do not rely solely on list index if actions can reorder.

## Risks and compatibility
Changing action counts during presentation is already documented as unsupported and is not the sole defect. Do not reintroduce the previously fixed weak-target lifetime problem.

## Required tests / acceptance criteria
- Keep alert open, swap title/data/callback fromA toB, then confirm; onlyB callback executes.
- Swap text-field callback without replacing controller, reorder actions safely, change enabled flag.
- Confirm/cancel callback cardinality and full modal lifecycle tests.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/519
- https://github.com/MohamedRejeb/Calf/issues/525
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
