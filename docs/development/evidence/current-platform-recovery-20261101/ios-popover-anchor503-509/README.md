# iOS action-sheet anchor batch503–509 — prepared, not native-verified

## Owning production fix for #29/UI-013

Existing common dialog signatures, manager constructor and legacy namespaces are
unchanged. New **iOS-only additive** `AlertDialogIosPopoverAnchor` and
`LocalAlertDialogIosPopoverAnchor` provide view-local `ViewRect` or supported
`UIBarButtonItem` input to both adaptive dialogs. No private backing-view lookup.
Null rectangles read current bounds. Missing/detached/foreign-window sources,
invalid finite bounds/rectangles and missing bar items use a documented one-point
presenter-center fallback with no arrow. System bar items must be installed by
the caller in the current toolbar/navigation bar; this is not privately inspected.

`AlertDialogManager` updates the anchor on public recomposition and again **inside
the queue-granted callback, before presentation**, avoiding a stale queued bounds
snapshot. Supported native repositioning checks Main/exact controller/popover/
delegate ownership and nonterminal presentation. View coordinates are written
only with a complete UIKit-owned rect/view pointer pair, synchronously. Bar-item
geometry remains UIKit-owned. Disposal drops the descriptor and completed cleanup
clears only matching owned native view/bar/delegate references. UIKit's Alert
presentation delegation remains untouched.

```kotlin
// iosMain only; sourceView is an attached UIView belonging to this presenter.
CompositionLocalProvider(
    LocalAlertDialogIosPopoverAnchor provides
        AlertDialogIosPopoverAnchor.ViewRect(sourceView)
) {
    AdaptiveBasicAlertDialog(
        onDismissRequest = onDismiss,
        iosProperties = AlertDialogIosProperties(style = AlertDialogIosStyle.ActionSheet),
        materialContent = {}
    )
}
```

Explicit rectangles are **source-view local**, not screen coordinates. Replace
the provided value when explicit geometry changes; anchors are Main-confined,
native objects, not saveable state. Public API/ABI/packaged compatibility still
requires its independent distribution gate.

## Actual important tests and compilation

-504: original production compiler FAILED1/45.01s on the missing interop `value`
  import. The sole actual diagnostic is repaired; no native test executes.
-506: changed production compiles, then test compiler FAILED1/53.01s/six errors.
  Repair only the two public `setBounds` calls and public popover-delegate cast.
-507: only failed test compilation recovers **Gradle0/32.01s**, fresh test KLIB,
  production UP-TO-DATE. Each compiler has1,289 held before/after inputs. Three
  final test warnings remain, including the unchanged helper's BetaInterop warning.
  **ZERO Apple link, launch or native test executions.**
-508: **22/22 important Python controls pass once/0.645s** (wrapper0.644981993s):
  13 new source/route/receipt controls, two changed historical-reader methods and
  seven production-affected Alert guards. Synthetic receipt input is not UIKit.
-509:34 corrected passive checks accept exact source/results custody, eight
  owning paths/29 reversible fragments/seven added inputs. All1,293 library inputs
  hold;1,279 other existing inputs are unchanged. Seven existing library paths
  change; the eighth owning path is a **Git-only workflow**, not a library input.
  The first reviewer domain-count refusal remains preserved; no accepted tests or
  compilers are replayed. `licensing-scope-addendum.json` clarifies the last named
  common-source check and separately verifies unchanged LICENSE/NOTICE Git bytes;
  this is not artifact licensing/release certification.

Every old modal manifest/pin stays unchanged. The exact new current reader rejects
old, partial, drifted or foreign bytes. Offline ancestor peeling removes only the
complete new afterimage and leaves old images to their old pinned readers. Live
native selectors never import an inverse or replace current source with history.

## Five fresh native methods and finite CI

`NativePopoverAnchorTest` covers public local-rect/live input without controller
rebuilding; installed custom bar and detached/missing fallback; queue refresh and
disposal; controlled owned/partial/foreign reposition pointers; and invalid
rectangles with unchanged UIKit Alert delegation. `ios-popover-anchor` and
`ios-popover-anchor-ipad` each select exactly those five cases on one actual
macos-26/Arm64 iPhone or iPad, never accepted modal populations. Their exact four
compiler sources are recorded and a fresh source-hash-bound receipt is mandatory
alongside original application/Worker/XML/runtime/binary/owned-cleanup gates.
Both source-only CLI plans and Actionlint1.7.12 pass; shellcheck was not executed.

**#29 is NOT closed.** The two original criteria additionally require actual iPad
portrait/landscape regular width and split view, iPhone compact, and rotation
during presentation. Controlled bounds/delegate calls are not real OS rotation
or split-view proof; even five green native methods alone cannot close the issue.
Original acceptance, earlier failed runs and other platform/physical/minimum-OS/
consumer/API–ABI/dependency/legal/security/readiness gates remain.

Counts remain103closed/69open/172;22implemented/36partial/101verified/five unresolved.
SOLO, development only, serial local8GiB and maximum2 hosted-heavy INCLUDINGqueued.
Actions all allowed/no mandatory SHA pinning/minimum read-only permissions. No
package, release, deployment, Pages or main/history mutation is authorized here.
