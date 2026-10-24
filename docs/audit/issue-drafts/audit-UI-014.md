# [High][UI-014] Alert dismissal during presentation is dropped and cleanup shares user-dismiss callbacks

<!-- nativecmpkit-item:audit:UI-014 -->
## Classification
- **Finding:** UI-014
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt:129-184`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt#L129-L184) — `onDismissLambda / dismiss / showAlertDialog`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.ios.kt:66-102,118-140`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.ios.kt#L66-L102) — `remember / DisposableEffect`

## Root cause
dismiss returns while presentation is animating or not yet marked presented. Disposal calls it once and does not queue cleanup. The manager is remembered by controller but DisposableEffect(Unit) is not. Programmatic cleanup invokes the same onDismissRequest callback as an outside tap, while native action auto-dismissal does not reconcile manager flags.

## Impact and preconditions
Removing an alert before presentation completes can leave an orphaned native modal. Controller changes can retain the wrong effect owner. Duplicate dismissal callbacks and inside-tap interception are additional native risks due to shared cleanup and an unfiltered superview tap recognizer.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- show sets isAnimating=true before isPresented becomes true in completion; dismiss returns when !isPresented||isAnimating.
- onDispose calls dismiss once, and onDismissLambda completion always invokes onDismissRequest.
- Both composables use DisposableEffect(Unit) around a controller-keyed manager.

## Recommended solution
Model requested versus actual presentation state, serialize show/dismiss, and honor pending disposal after presentation completes. Key effects by manager/controller and separate cleanup from user-dismiss notification. Use supported presentation delegates/hit-testing for outside dismissal.

## Risks and compatibility
Dropped early cleanup is source-confirmed. Exact double-callback and tap-recognizer behavior requires native reproduction. Do not re-report the fixed NSObject/unrecognized-selector crash.

## Required tests / acceptance criteria
- Remove composition during presentation and during dismissal; immediately reopen.
- Confirm action followed by caller removal invokes each semantic callback at most once.
- Parent controller replacement, inside text-field taps, outside taps and dismissOnClickOutside=false.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/330
- https://github.com/MohamedRejeb/Calf/issues/341
- https://github.com/MohamedRejeb/Calf/issues/381
- https://github.com/MohamedRejeb/Calf/issues/414
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
