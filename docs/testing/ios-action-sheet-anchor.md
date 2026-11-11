# iOS action-sheet popover anchor (UI-013)

## Status

Source-only implementation for `#29 / UI-013`. No Kotlin/Native compile, link,
simulator run or manual app exercise was performed while adding this change. The
source still needs the normal iOS test/production compiler verification. Nothing in this document closes `#29`
or establishes real iPad regular-width, split-view, rotation or physical-device
behavior.

## Additive API

The common `AdaptiveAlertDialog` / `AdaptiveBasicAlertDialog` signatures,
`AlertDialogIosProperties` constructor and existing public action types are
unchanged. The following iOS-only API is additive in
`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosPopoverAnchor.kt`:

- `AlertDialogIosPopoverAnchor.ViewRect(sourceView, sourceRect, permittedArrowDirections)`
  - `sourceRect` is in `sourceView`'s local coordinate space.
  - `null` means "read the source view's current bounds at presentation and on every
    UIKit reposition request".
- `AlertDialogIosPopoverAnchor.BarButton(barButtonItem, permittedArrowDirections)`
  - The item must already be installed in the presenter's navigation bar, toolbar
    or other bar. UIKit owns its private geometry.
- `LocalAlertDialogIosPopoverAnchor` (a `CompositionLocal`)
  - Wrap either adaptive dialog with
    `CompositionLocalProvider(LocalAlertDialogIosPopoverAnchor provides anchor)`.
  - `null` (the default) is supported for existing callers and resolves to a
    one-point presenter-center rectangle with no arrow.

`Alert` style ignores the local; only `ActionSheet` assigns the owned popover
delegate. Alert presentation delegation remains UIKit-owned.

Minimal usage (iOS source set):

```kotlin
CompositionLocalProvider(
    LocalAlertDialogIosPopoverAnchor provides AlertDialogIosPopoverAnchor.ViewRect(
        sourceView = anchorView,
        sourceRect = CGRectMake(8.0, 8.0, 24.0, 24.0),
    ),
) {
    AdaptiveBasicAlertDialog(
        onDismissRequest = { shown = false },
        iosProperties = rememberAlertDialogIosProperties(
            style = AlertDialogIosStyle.ActionSheet,
        ),
        materialContent = {},
    )
}
```

For a `UIBarButtonItem`, use
`AlertDialogIosPopoverAnchor.BarButton(installedItem)` instead. The anchor view or
bar item must be in the presenter's current window when the dialog is presented.

## Resolution and lifecycle policy

Before `presentViewController`, `AlertDialogManager` configures the action-sheet
`UIPopoverPresentationController` with either `sourceView` + `sourceRect` or
`barButtonItem`. Requested geometry is accepted only when:

- the source view is non-null and in the presenter's current window;
- the rectangle is finite, non-empty and fully inside the source view's bounds;
- the arrow-direction mask contains only `UIPopoverArrowDirection` flags.

Missing, detached, foreign-window, non-finite, empty or out-of-bounds view geometry
resolves to the documented presenter-center fallback. A missing bar button also
falls back. For bar buttons, installation is a caller precondition: public UIKit
APIs do not expose a reliable installation check. A system item without a custom
view is accepted, and even a custom view in the window does not prove its item is
installed. Use a view-rect anchor if installation cannot be guaranteed. The manager refreshes its owned popover after property updates and in
`popoverPresentationController:willRepositionPopoverToRect:inView:`, which is the
public UIKit hook used for layout/orientation repositioning. For a `ViewRect` with
`sourceRect == null`, the current bounds are re-read on each reposition so the
anchor follows the source view. Explicit rectangles remain in the same local
coordinate space; UIKit repositions relative to the source view. Source removal
alone does not trigger a refresh; the next property update or UIKit reposition
request revalidates the source.

The owned delegate also re-resolves the anchor in
`prepareForPopoverPresentation`, immediately before UIKit shows the popover.
This closes the gap between the initial presentation request and UIKit's actual
preparation: changed bounds or a source detached in that interval are not reused
as the original anchor. A callback for another popover cannot mutate either
controller's anchor.

The reposition callback writes the rectangle/in-view pointer pair only when both
UIKit-owned pointers are present. It never invents a system bar item's private
view. On dismissal completion the manager clears only its own source/bar/delegate
references. A UIKit-initiated action-sheet dismissal notifies the dialog-level
dismiss callback once; a chosen action keeps its own callback and does not also
emit a synthetic dismiss callback. Alert actions preserve the existing dialog-level
callback on dismissal. The manager installs an adaptive presentation delegate for
ActionSheet even when there is no popover, refreshes that attachment after UIKit's
presentation completion, and sets `modalInPresentation` from
`DialogProperties.dismissOnClickOutside`. These public hooks wire the intended
outside/swipe policy; actual compact UIAlertController behavior remains a native
acceptance requirement. The owned outside-tap gesture stays scoped to Alert style.
When an ActionSheet action is chosen, the manager clears the modal interaction
restriction before invoking the user's callback, matching the delegate's selected-
action policy. Later property updates preserve that selected-action policy.

## Tests added (not executed)

`calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativePopoverAnchorGeometryTest.kt`
constructs real `UIWindow`, `UIView`, `UIToolbar`, `UIBarButtonItem`,
`UIAlertController` and `UIPopoverPresentationController` objects and covers:

- configured `ViewRect` source/rect and later rectangle changes;
- installed custom-view and system `BarButton` setup, and source view;
- detached source, missing view, missing bar item and fallback center;
- non-finite, empty, negative and out-of-bounds rectangles;
- disallowed arrow-direction masks;
- the null-anchor fallback recentering after presenter bounds change;
- controlled reposition pointer pairs, partial pairs and a foreign popover;
- bar-button reposition without fabricated private geometry;
- Alert style refusing an explicitly supplied controlled popover delegate;
- controlled compact presentation policy, duplicate native-dismissal signals,
  owned-anchor cleanup, ActionSheet action suppression and Alert callback preservation;
- source removal followed by a controlled reposition request.
- changed bounds/source detachment between configuration and the controlled
  prepare callback, an ignored foreign prepare callback, and a foreign-window view.

The tests explicitly construct public presentation controllers, including a popover,
so their geometry does not depend on an iPad idiom or regular-width test host. The
fixture window has a root view controller but no application window scene. No alert
is presented. Direct calls to lifecycle, action and delegate entry points are
controlled inputs; they do not prove UIKit supplies those events or that an action
button invokes its handler. Run these tests on Main on both compact and regular
hosts; actual OS presentation, rotation, split view and composition-local wiring
remain separate requirements.

There are now 16 prepared UIKit methods, including three additional controlled
regressions for the November 11, 2026 adaptation. None has been compiled or
executed as part of that adaptation. The original 13 prepared methods and their
unexecuted status are retained, not replaced by a native-pass claim.

## Focused source contracts

`scripts/ci/test_ios_action_sheet_anchor.py` checks only the five explicit dialog,
anchor, native-test and manual-matrix leaves used by this proposal. It never
discovers other source paths. It checks request/prepare/reposition ordering,
window/geometry guards, selected-action modal policy, Alert isolation, both
composition-local consumers, and retention of the original manual matrix.

Run with `python3 scripts/ci/test_ios_action_sheet_anchor.py -v`. These nine
stdlib source-contract checks do not compile, link or execute Kotlin or UIKit,
and cannot satisfy the native/manual acceptance criteria. No workflow, task
catalog or documentation index is changed by this proposal. The check is available
for focused local use; no standalone source-contract CI dispatch or new required
gate is requested.

A read-only Kotlin/Native 2.4.20 metadata follow-up verified the public member
getters `UIView.bounds()` / `UIView.frame()` and setter `UIView.setFrame(...)`.
The resolver and fixture use those verified accessors instead of relying on
unimported geometry extension properties. The same inspection verified that
`UIView.window` and `UIBarButtonItem.customView` are member properties and that
the popover protocol declares `prepareForPopoverPresentation` with the implemented
controller parameter. This is declaration inspection, not compilation or execution.
The nine source checks passed on the preceding source revision; the accessor
correction and matching expected-source literal were not rerun, as instructed.

## Manual app exercise required for original acceptance

Use a sample or test app that presents `AdaptiveBasicAlertDialog` with
`AlertDialogIosStyle.ActionSheet`, an explicit bar-button anchor and an explicit
view-rect anchor. Repeat on real iPad and iPhone simulators/devices:

| Host | Layout/orientation | Required observation |
|---|---|---|
| iPad | Portrait, regular width | Sheet opens without the missing-anchor exception; arrow points at the configured bar button or view rect. |
| iPad | Landscape, regular width | Same anchor remains valid; rotate while presented and verify the arrow follows the source or stays at the same explicit local rect. |
| iPad | Split View (half, one-third, two-thirds) and Slide Over | Re-run both anchors at each actual width/trait; no stale screen-coordinate anchor, no crash, sheet remains usable. |
| iPhone | Portrait and landscape, compact width | Action sheet uses its compact presentation; anchor configuration does not break presentation, actions or outside dismissal. |
| Both | Missing/detached source | Remove the source view then trigger a property update or actual reposition, or provide `ViewRect(null)`/`BarButton(null)`; verify the documented center fallback and no crash. |
| Both | Action/callback behavior | Use Confirm-only (no Cancel) and Confirm+Cancel sheets with both `dismissOnClickOutside` values; test outside tap/swipe, each action and disposal. Verify callbacks once and cleanup; compare Alert action callbacks too. |

Also exercise both adaptive dialog composables through the composition local and
update the anchor while presented. Test an installed system bar item and the zero
arrow fallback; inspect delegate/source/bar cleanup after dismissal.

Record the actual simulator/device model, OS version, orientation, size class,
split-view fraction, screenshot/video and pass/fail per row. A simulator result is
not a physical-device, accessibility, minimum-OS, packaged-consumer or ABI result.

## Pending API and verification checks

- Run the repository's standard source/API compatibility checks after integration;
  this change adds only iOS source-set symbols and changes no common constructor or
  expected declaration.
- Compile the iOS production and test KLIBs, then link and execute the iOS test
  binary on a real simulator host. The geometry test file is in the ordinary
  `iosTest` source set; no new source set or build task was added.
- Execute the manual matrix above. Until then `#29` remains open for genuine
  portrait/landscape regular-width, split-view and compact-width evidence.
