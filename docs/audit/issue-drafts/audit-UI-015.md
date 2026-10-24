# [Low][UI-015] rememberAlertDialogIosProperties does not remember changes to textFields

<!-- nativecmpkit-item:audit:UI-015 -->
## Classification
- **Finding:** UI-015
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosProperties.kt:16-45`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosProperties.kt#L16-L45) — `rememberAlertDialogIosProperties`

## Root cause
textFields participates in the constructed data class but is omitted from remember keys.

## Impact and preconditions
When all other inputs, including actions, remain equal, a changed list of text-field configurations/callbacks is replaced by the previously remembered list even before native synchronization.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- remember(title,text,style,animated,severity,actions) excludes textFields, which is passed inside the block.

## Recommended solution
Include textFields among the keys or remove unnecessary remembering. Document that initialValue is an initial native value rather than a controlled text property.

## Risks and compatibility
The default actions list may change identity and mask the problem; reproduce with a stable actions list. Fixing this helper alone does not resolve existing native callback capture.

## Required tests / acceptance criteria
- Recompose with stable actions/title/etc and a different textFields list; assert returned properties follow it.
- Same-value stable inputs retain normal behavior.

## Dependencies
- UI-012

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
