# UI native/date/time/modal development — UI-001…UI-026

This is a **post-audit implementation record**, not a replacement for the immutable
[baseline UI findings](../audit/findings/UI.json). The root authorized this repair
phase after the 2026-10-24 upstream reconciliation. Existing public packages and
`calf-ui` project identity remain unchanged. The machine-readable disposition is
[`resolutions/UI-native.json`](resolutions/UI-native.json).

## Verification state

Latest [current UIKit/original acceptance](checkpoint-uikit-acceptance-20261027.md):
immutable40540209480 /ea79ab8c completes123/123 methods in25 fresh XML, zero skips,
all16 required native cases/six sources, real runner/Worker/console and owned cleanup.
Original UI-015/UI-022 scopes pass exact acceptance; GitHub closure waits for pushed
evidence/readback. Earlier running/failed observations below remain historical.
Physical/gesture/assistive/minimum-platform/profiling/consumer/security gates remain.

Current [original UI-009 acceptance](checkpoint-gc-diagnostics-navgeo-20261027.md#navigationgeo-matrix-and-original-time-state-acceptance)
covers constructor/Saver only: three methods on both actuals at immutable6eb7c66
pass on Linux desktop/Android host/macOS desktop/iOS simulator,12 repeated target
executions with four owning files still byte-identical. Later UI-build differences
are exact additive test-only imports/binary/task, not an unchanged whole build.
Prior remaining notes/reviewer reds remain; issue #123 still needs pushed evidence,
current held preflight and closure readback. Native state-owner/rendering/locale/
accessibility/ABI/release scopes stay separate. The latest actual UIKit run passes
all12 native application methods and three time-state methods, but fails an
interrupted image-GC case (120pass/1fail of121), not a completed native suite.

Latest [exact native-identity follow-up](native-ui-application-host.md#exact-native-object-identity-after-the-persistent-startup-timeout)
preserves40460102044's simulator-migration and later startup-timeout failures:
active/key/visible true, wrapper identity false, native equality true, zero tests.
Test-only nonnull-pointer ownership retains all native/cleanup gates and adds a
mandatory equal-content/distinct-object/null-owner native method. Fresh full-test
KLIB/model compile0/37.01s and226 Python CI guards pass at712 held inputs after a
preserved compile failure. No Apple/runtime pass; native findings stay open.

Earlier [UIKit application follow-up](native-ui-application-host.md#actual-activation-attachment-failure-and-bounded-startup-repair)
preserves actual attempt2 atbe32a7d6: native link/sign/install/owned cleanup pass,
but eager activation attachment checking crashes before any testcase/XML.
Bounded main-loop startup/exactly-once admission retains all native assertions;
full-test KLIB/model compile and synthetic source/transport checks pass, **not
Apple execution**. Native-only findings stay open; a new immutable `ios-ui` run
is required. Earlier observations below deliberately retain their original scope.

Current evidence is **scoped diagnostic verification**, not release certification:

- `git diff --check -- calf-ui` completed with exit 0.
- The lead's first Linux desktop build compiled UI production sources, but UI test
  compilation failed because the newly added common version helper was written
  after that run had captured its main inputs. Its test source was seen later in
  the same run. The helper is in **commonMain**, not iOS-only. See
  [`first-library-desktop.log`](evidence/gradle/first-library-desktop.log) and its
  `.result.json`. **No UI test execution is claimed for that failed run**, and old
  XML files are not new evidence.
- The lead's second and third desktop runs executed all **23 newly added functions
  in this area** (17 common and six desktop Compose functions), with zero failures,
  errors or skips in those eight classes in each run. The archived XML and its
  stored SHA256s were inspected. Both whole UI runs still failed: **126 executed,
  125 passed, one slider-cancellation failure**, and each encompassing Gradle
  command exited 1. The fourth UI run subsequently passed **128/128** across the
  whole desktop UI suite, including the same 23 functions in this area; its
  encompassing multi-module command still exited 1 because picker Android-host
  test compilation failed. The three runs contain **69 repeated executions of
  23 unique functions** in this area, not 69 unique tests. See the
  [scoped receipt](evidence/ui-native/desktop-scoped-20261024.json),
  [run 2 summary](evidence/gradle/second-library-desktop.summary.json) and
  [run 3 summary](evidence/gradle/third-desktop-ui-nav-geo-icons.summary.json), and
  [run 4 summary](evidence/gradle/second-io-perm-and-fourth-ui.summary.json).
- Those receipts describe selected, hash-stable **uncommitted inputs** based on
  `94d2492e99d5cbc060409d94d9f88febd06222d5`, not an immutable release revision.
  Common date/time tests ran against Material desktop actuals; pure presentation
  tests do not execute a UIKit controller. The cancellation failure belongs to
  the separate UI-controls area and its original evidence is preserved.
- There are also 16 new iOS UIKit/Compose test functions. They have **not run**.
  The first actual module KLIB attempt failed production compilation on four
  frame assignments (NativeBarHost plus three in the other owner's FAB), before
  test compilation. The input verifier confirmed all 247 selected hashes held.
  NativeBarHost now uses the typed `UIView.setFrame` member. The second actual
  attempt cleared the setter errors but failed during native lowering because
  the calendar subclass called the non-designated `UICalendarView()` initializer.
  All 263 selected hashes held. It now calls designated `initWithFrame`, without
  suppressing native constructor validation. The third attempt then **compiled
  the complete production KLIB**, but test compilation failed on two native-bar
  frame assignments and the other owner's theme/GC test bindings. Native-bar
  tests now call `setFrame` while retaining all assertions; their recompile is
  pending. No test execution or Apple binary linking occurred. See the
  [first failed actual compile
  receipt](evidence/gradle/first-ui-ios-klib.verification.json) and
  [second attempt](evidence/gradle/second-ios-klib.verification.json),
  [third attempt](evidence/gradle/third-ui-ios-klib.verification.json), and the
  [production KLIB file hashes](evidence/ui-native/production-klib-20261024.json).
  A direct Kotlin 2.4.20 `konanc -produce library -target ios_simulator_arm64`
  signature probe on Linux reached real UIKit compiler diagnostics, exposing a
  category-override error in the new dropdown implementation. Failed category,
  category-alias and protocol-super probes are preserved in
  [the binding review](evidence/ui-native/bindings-review-20261024.json).
  The source now uses explicit public delegate-protocol configuration instead.
- Linux KLIB-only compilation is distinct from Apple binary linking or execution.
  The earlier blanket statement that Linux cannot compile Apple sources was too
  broad for Kotlin 2.4.20. Production KLIB compilation is now confirmed; test KLIB
  compilation, genuine hosted simulator execution, and device/VoiceOver/performance
  checks remain separate gates.
- Fourteen records with actual common/desktop evidence are `partially-verified`;
  the twelve native-only records remain `implemented`. None is fully verified or
  closed by these results. Compile-only evidence does not count as a native test.

## Date state and calendar contract (UI-001…UI-008)

### UTC day and immutable year range

`canonicalDateInYearRange` is shared by the iOS and Material single-date actuals.
Construction and later property assignment canonicalize to UTC midnight and reject
out-of-range years, matching the documented exception contract. Empty year ranges
are rejected explicitly. This validation is **not** application business-rule
validation: programmatically assigning a date rejected by `SelectableDates` is
still allowed. A selected day and a displayed month are separate state.

The new common `yearRange` property exposes an existing actual property. The new
`displayedMonthMillis` property is additive. Material delegates month state to
Material3. iOS stores a canonical month; its native calendar forwards month
navigation back to this state. Both Savers append the month as a sixth element
and continue accepting historical five-element lists (whose selection supplies
the historical month fallback).

`yearRange.dateBounds()` builds Gregorian January-1/December-31 endpoints with a
checked pure calendar calculation. Native effective bounds intersect these with
bounds extracted from `DateBounds`/`and`. Both native calendars and the snapping
algorithm check **both** `isSelectableYear` and `isSelectableDate`. An out-of-range
native result is not written into a state with a different year range.

### Gregorian presentation; localized text/time zone

`gregorianCalendar()` is used by `UICalendarView`, `UIDatePicker`, and NSDate day
extraction. Date components carry an explicit Gregorian calendar/era. The locale
still controls language and the device time zone controls local display of the
corresponding civil day. Buddhist/Japanese/Hebrew preferred calendars no longer
silently reinterpret Gregorian API years. This is an explicit Gregorian API
policy, not a claim of localized alternative-calendar support.

Roundtrip tests cover Gregorian leap/pre-epoch days and UTC-12/UTC/UTC+14 calendar
instances. They do **not** replace a preferred-calendar settings matrix, era
boundary/DST device testing, or certification of extreme native supported years.

### Empty sets and rejected selections

`DateBounds.isEmpty` compares UTC days, so reversed endpoints within the **same**
day are not empty. Disjoint intersections remain representable. `UICalendarView`
keeps its previous valid interval and disables interaction for an empty set;
`UIDatePicker` clears both old native endpoints before applying a new pair and
combines empty-set disablement with the caller's enabled flag. Returning to valid
bounds does not override an explicitly disabled control.

The existing bounded snap policy is intentional and preserved: clamp first to
effective bounds, examine at most 366 days on either side, prefer later days on a
tie, and retain the previous selection when no candidate is found. The additive
`AdaptiveDatePickerState.isSelectionSelectable` property is false for null or
currently rejected selections. Callers must validate business operations; this
API does not silently invent a permitted date when none exists.

### Native ownership and bounded range rendering

Every date synchronization effect is keyed by its manager/backend as well as its
input. Manager identity includes presentation. An equal-valued replacement state
therefore still initializes bounds, selection, layout direction, colors, enabled
state and visible month. UIDatePicker wheels/compact cannot independently display
a month without changing their shown date; only UICalendarView implements separate
month navigation, and this limitation remains explicit.

Range state still holds the whole range, but UIKit highlights only the visible
month and its two neighbours, at most about 92 days. `DateRangeSelection.contains`
is constant-time. Rule and native visible-month changes rebuild this bounded
window, rather than enumerating decades on the UI thread. The iOS 16.2 delegate
notification is supplemented by native layout observation for 16.0/16.1. No CPU,
allocation or device-frame-time benchmark has been claimed.

### Material compact transactions

Replacing the owning state cancels an open dialog transaction. A dialog scratch
state remains independent until confirmation, follows current selectable rules,
and is revalidated **again in the confirm handler**, not merely when drawing an
enabled button. A rejected scratch day disables confirmation. Null remains a
valid clear operation, and cancel/reopen semantics are unchanged. Confirmation
also preserves the dialog's displayed month in the owner state.

## Time state (UI-009…UI-011)

Both actual constructors now validate `initialMinute`, not `initialHour` a second
time. Common tests cover invalid/boundary hours and minutes, Saver roundtrip and
invalid saved minutes. The UIKit view, manager, synchronization and theme/direction
effects belong to the current state. Replacing a state cannot retain callbacks
that write to its predecessor. Native time initialization uses today's calendar
components rather than an unspecified ancient date, and native controls are sized
before embedding.

UIKit has no independent supported hour-cycle property. The public `is24Hour`
value remains stored/restored, but **iOS follows the system locale/hour-cycle
setting**. No `en_US`/`en_GB` or private locale override is introduced. Material
continues to honour the explicit preference. This documented native policy is an
API limitation, not proof of a 12/24-hour native override or locale/accessibility
matrix coverage.

## Native modal ownership (UI-012…UI-019)

### Shared requested-versus-actual state

`internal/NativePresentationState` is a small deterministic state machine with
Hidden/Presenting/Presented/Dismissing phases and generation-tagged completions.
A desired hide or terminal dispose remains pending during a show animation.
Stale completions do not revive a dismissed owner. Pure common tests exercise
queueing, repeated requests, reopen-during-dismiss and terminal disposal. These
are state-machine tests, **not substitutes for UIKit lifecycle tests**.

`NativePresentationQueue` coordinates only nativeCmpkit alerts and sheets sharing
a parent controller. A replacing owner waits for actual native dismissal, not
just removal from Compose. It never dismisses another library's/application's
controller. It does not promise arbitration with unrelated native presenters.
The dictionaries contain only active/waiting owners and release those entries on
native completion or queued-owner cancellation.

### Alerts

Action title/style/order and text-field structural descriptors identify the
native structure. Callback-only replacements use the **latest** descriptor at
the event boundary. Structural changes queue an orderly controller replacement;
an old visible action cannot invoke a newly reordered descriptor. Fields retain
in-progress text for callback-only changes; `initialValue` is an initial value,
not a controlled text property. `rememberAlertDialogIosProperties` now includes
`textFields` in its remember keys.

The iPad action-sheet fallback anchor is a one-point rectangle in the presenting
view's center, in that view's coordinate system. This is not a new bar-button
anchor API. Adaptive/rotation-specific placement still needs iPad testing.

Owner disposal queues cleanup but never calls the semantic dismissal callback.
Action dispatch is guarded against repeated invocation and likewise does not
manufacture a cancel callback. Outside taps are hit-tested against the actual
alert bounds; inside field/button taps are not treated as outside dismissal. The
presentation delegate enforces the outside-dismiss policy. Real UIKit test source
presents alerts, exercises callback replacement/native field target delivery,
checks the popover source and replaces an owner during animation. Action tests
call the production dispatch entrypoint, **not synthesized physical touches**.

### Sheets

Public show/hide operations switch to `Dispatchers.Main.immediate` and serialize
through a per-state mutex. The native manager gives each invocation a new
completion token. Cancelling a suspended caller removes that waiter while the
native completion still synchronizes actual state. It cannot complete a later
show/hide invocation using a recycled deferred.

Show/hide and native delegate events use the state's transition policy, including
skip flags. `hide()` rejects `skipHiddenState=true`. Forced owner disposal is a
separate terminal cleanup operation and intentionally bypasses application vetoes.
Disposal clears only its own state-manager reference, cancels its waiters, queues
any necessary native dismissal, then releases controller/content/delegate ownership.

Detents are ordered medium then large, and show selects medium unless partial is
skipped or a visible/restored value says otherwise. The native sheet delegate
updates current/target state before dismissal callbacks. UIKit exposes notification
**after** a detent change, not a pre-drag veto; a rejected changed detent is restored
to the prior allowed identifier. Tests still need real drag and iPad adaptation.

`ModalBottomSheetProperties.shouldDismissOnClickOutside` governs native adaptive
interactive dismissal (UIKit's delegate does not distinguish all drag/outside
origins). Android back-key policy has no equivalent hardware-back operation on
this native sheet. Native visual slots/geometry stay native; Material shape,
maximum width, scrim and custom drag-handle content are not suddenly supported by
this patch. Their platform-specific nature needs clear consumer guidance.

`rememberAdaptiveSheetState` keeps its identity when confirmation callbacks change
and invokes the latest callback via `rememberUpdatedState`. Structural skip keys
still reset state deliberately, and density-derived thresholds read current density.

## Bars and toolbar (UI-020…UI-023)

`NativeBarHost` embeds each UINavigationBar/UITabBar/UIToolbar inside `UIKitView`
in the **owning Compose layout**, not directly in `LocalUIViewController.view`.
There is no invisible proxy translated back to a root overlay. Native layout,
safe-area and trait callbacks continue to measure bar content after initial
stabilization; there is no six-frame stop condition or perpetual frame poll.
Caller modifiers and bar window insets belong to that Compose node. Scaffold
uses the node's measured dimensions and ordinary padding, not a second global
native padding channel. Existing cache/local source files are no longer read by
these components. This is a localized ownership repair, not a navigation-stack
rewrite.

Consequences/compatibility considerations:

- A native bar is now located where its composable is placed. Code that relied on
  the previous undocumented root-screen overlay must place it in a scaffold slot
  or explicit layout. Separate screens/nested scaffolds no longer deliberately
  attach their bars to the same root view.
- This does not certify every Compose graphics-layer alpha/clipping/transition
  combination, cancelled interactive back gesture, UIKit scroll-edge integration,
  keyboard layout, multiwindow behavior or accessibility traversal order.
- Native appearance/items remain controlled by `ios*` configuration rather than
  Material title/actions/content. Image conversion now receives density and layout
  direction through the coordinated image-owner change.
- Empty tab lists clear native items and selection. Nonempty selected indices
  remain clamped to the nearest valid index; programmatic changes do not fabricate
  selection callbacks.
- Toolbar uses the documented Material3 Expressive fallback on pre-26 iOS or
  empty native items. On 26+ with native items it is layout-scoped, honours its
  modifier, and leaves placement/insets to the caller. `expanded`, leading and
  trailing Material content still have no native UIToolbar analogue.

## Dropdown (UI-024…UI-026)

A shared pure version comparison is lexicographic (17.4, 17.10, 18.0 and 26.0 are
supported). Before 17.4, the existing `materialContent` supplies a supported
Material3 fallback. No private recognizer name, fake touch or private presentation
entrypoint remains.

On supported iOS versions, a transparent `UIButton` anchor is owned/measured by
UIKitView in the actual Compose hierarchy. `performPrimaryAction` requests its
menu; public context-menu `willDisplay`/`willEnd` callbacks track native lifecycle,
and `contextMenuInteraction.dismissMenu()` handles `expanded=false` and disposal.
Kotlin 2.4.20 imports UIControl's category callback methods as final extensions,
not overridable UIButton members. Direct override, aliased category-super calls
and protocol-super calls all failed isolated real-binding compilation. The
button now explicitly adopts `UIContextMenuInteractionDelegateProtocol` and
returns a configuration containing its current public `menu`. It implements the
lifecycle callbacks directly; it does **not** fabricate a superclass call, cast
an Objective-C IMP or use private selectors. This typed bridge is part of the
successfully compiled production KLIB, but still needs native open/close tests;
compilation does not establish correct UIKit runtime behavior.
Opening no longer fires the dismissal callback. Programmatic false does not
invent a user dismissal; native dismissal requests the caller update its expanded
state after the native completion. Requests made before attachment/layout wait
for native attachment/layout callbacks. Invisible anchors are not separate
accessibility elements.

Material forwards every supported argument: offset, scroll state, popup policy,
shape, container color, tonal/shadow elevations and border. The required
`materialContent` remains the content source; documentation no longer promises
that `iosItems`/`iosSections` auto-render on Material. Native menu styling remains
UIKit-controlled; Material shape/color/elevation/popup flags do not all map to
native UIMenu. The controlled-native-menu test still needs actual simulator
execution, including its UIKitView anchor interaction configuration.

## Test/source index and remaining gates

- `commonTest/datepicker/DateStateContractTest.kt` — nine shared contract functions.
- `commonTest/timepicker/TimePickerStateContractTest.kt` — three functions.
- `commonTest/internal/NativePresentationStateTest.kt` — four pure lifecycle functions.
- `commonTest/dropdown/DropDownAvailabilityTest.kt` — one version-table function.
- `desktopTest/datepicker/CompactDateTransactionRegressionTest.kt` — three functions.
- `desktopTest/dialog/RememberAlertPropertiesTest.kt` — one remember-key function.
- `desktopTest/sheet/RememberSheetPolicyTest.kt` — one latest-policy/identity function.
- `desktopTest/dropdown/MaterialDropDownForwardingTest.kt` — one real long-menu/scroll function.
- `iosTest/datepicker/NativeDateControlsTest.kt` — five UIKit configuration/selection functions.
- `iosTest/timepicker/NativeTimePickerTest.kt` — two UIKit target/Compose owner functions.
- `iosTest/navigation/NativeBarOwnershipTest.kt` — two UIKit ownership/clear functions.
- `iosTest/dialog/NativeAlertLifecycleTest.kt` — three real presentation functions.
- `iosTest/sheet/NativeSheetLifecycleTest.kt` — three policy/presentation functions.
- `iosTest/dropdown/NativeDropDownLifecycleTest.kt` — one real menu lifecycle function.

Scheduled commands belong to the lead: `:calf-ui:desktopTest` under Xvfb, shared
Android-host/JS/Wasm suites where configured, KLIB-only
`:calf-ui:compileTestKotlinIosSimulatorArm64` (which also compiles main), Apple linking and
`:calf-ui:iosSimulatorArm64Test` on a supported, genuinely hosted UIKit simulator.
The new UICalendarView tests require iOS 16+, and the native-menu lifecycle test
explicitly requires 17.4+; older-version fallback tests remain separate gaps,
not tests silently skipped by these helpers.
Compile failures and native-host/runner constraints must be recorded, not bypassed
by pretending an unexecuted test is passing. Native tests intentionally do not
certify device-only behavior, VoiceOver, private user settings or instrumented leak
and performance characteristics.

## Additive browser execution evidence

The [independently reviewed first JS run](evidence/ui-controls/first-js-results.json)
executed all 64 UI common/Material policy cases successfully. Of these, 49 concern
the families discussed here: date policies (37), dialog policy (4), dropdown
availability (1), presentation state (4), and time state (3). The remaining 15
controls cases are documented in [UI-controls.md](UI-controls.md). The first
**overall command still failed elsewhere**; this is not a retroactive passing
full-library run.

The subsequent [full JS run 003](evidence/js-full-003/archive.json) separately
passed 286 cases across all 19 requested test-bearing modules, including the same
64 UI cases. Its 691 library/shared inputs were unchanged during execution.
These are repeated executions of the same UI methods, not 128 distinct tests.
Neither run exercises UIKit presenters, native calendar/menu interaction,
CoreGraphics drawing, accessibility, Apple linking, or physical-device behavior.
Both use held dirty source rather than an immutable release candidate; every
native acceptance requirement above remains in force.

### Independently reviewed Wasm004 and JS004 handoff

The later [Wasm004](evidence/wasm-full-004/archive.json) and
[JS004](evidence/js-full-004/archive.json) local commands each passed **290/290**
cases in 19 requested modules/48 reports, exiting **0** after 123.02 s and
130.03 s respectively. The [independent source/XML/context review](evidence/ui-controls/browser-004-results.json)
confirms **64/64 UI cases in 11 reports on each target**, with no errors, failures
or skips. All 693 captured inputs were unchanged throughout each run and matched
at review; 182 of these inputs belong to UI. Every UI raw/sanitized report hash,
source method, fresh timestamp and actual test-task marker was checked.

On **each** target the native workstream's common-policy families contribute:

| Common policy family | Passed |
|---|---:|
| Date bounds/range/state (four classes) | 37 |
| Alert action construction/callback routing | 4 |
| Dropdown version comparison | 1 |
| Presentation transition state | 4 |
| Time state/validation/Saver | 3 |
| **Total** | **49** |

The other 15 controls cases are documented in [UI-controls.md](UI-controls.md).
Across these two diagnostics this is **98 executions of 49 existing common
functions**, not 98 new tests. Date/time cases use the configured browser-target
actuals; `NativePresentationStateTest` drives only a common transition model.
No UIKit controller, native date/menu presentation, native callback replacement,
sheet drag, safe-area bar, VoiceOver, CoreGraphics or physical device was exercised.
Browser popup/focus/visual checks required by UI-006/026 are not supplied by these
scalar/state tests either.

The [Wasm](evidence/wasm-full-004-context/context-review.json) and
[JS](evidence/js-full-004-context/context-review.json) context receipts additionally
bind selected fresh UI Karma paths. Prepared Wasm tooling and the explicit local
root-container Chrome launcher are not proof of the full dependency closure or
hermetic execution. Compilation was up-to-date; fresh test tasks and XML, not
compilation, establish the browser executions.

The additive ledger entries preserve every status and prior failure record. Apple
linking/hosted UIKit execution, older/current native branches, device/accessibility,
native ownership, visual/performance, compatibility and immutable-revision gates
remain. Browser success does not complete those gates or lift containment.
