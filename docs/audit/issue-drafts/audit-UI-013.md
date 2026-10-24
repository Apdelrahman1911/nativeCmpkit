# [High][UI-013] iOS action sheets are presented without an iPad popover anchor

<!-- nativecmpkit-item:audit:UI-013 -->
## Classification
- **Finding:** UI-013
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt:54-59,161-184,200-206`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt#L54-L59) — `dialogUIViewController / showAlertDialog / toUIAlertControllerStyle`

## Root cause
The ActionSheet style creates and presents UIAlertControllerStyleActionSheet without configuring popoverPresentationController.sourceView/sourceRect or barButtonItem. The public wrapper provides no anchor input.

## Impact and preconditions
The required regular-width/iPad popover presentation precondition is absent. UIKit may raise its missing-anchor exception instead of showing the sheet; this audit confirms the omitted configuration, not a locally executed iPad crash.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- No popoverPresentationController/sourceView/sourceRect/barButtonItem setup exists in the alert manager.
- The same presentation path is used for Alert and ActionSheet.

## Recommended solution
Add a supported anchor mechanism and a safe documented fallback to the presenting view/rect, configured before presentation. Handle adaptive size changes and controller coordinates explicitly.

## Risks and compatibility
A center-of-view fallback differs from a contextually anchored action sheet. Do not assume iPhone-only testing or compact size classes cover iPad behavior.

## Required tests / acceptance criteria
- iPad portrait/landscape regular width and split view; iPhone compact.
- Bar-button and view-rect anchors, missing source view, rotation during presentation.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
