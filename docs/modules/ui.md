# calf-ui: implementation and maintainer map

## Scope, evidence and compatibility

Reviewed source baseline: **`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`**.
This report covers every handwritten production and test file in `calf-ui`, its
build file, native ownership paths, algorithms and important helpers. The
7,006-line deprecated generated `sf/symbols/SFSymbol.kt` table is covered by the
[icons reviewer](navigation-core-icons-sample.md), not claimed as a second
independent symbol-table audit here. No library source was changed by this review.

Read together with the [UI audit](../audit/ui.md), [machine-readable findings](../audit/findings/UI.json)
and [test plan/evidence](../testing/ui.md). `UI-NNN` references below are stable
finding IDs. Native defects identified by source are **not** claims of successful
iOS execution. Linux cannot run UIKit, VoiceOver, Apple Instruments or native
simulator tests. [Architecture](../architecture/README.md) and
[platform matrix](../platforms/README.md) explain the surrounding project.

The independent nativeCmpkit identity does not rename the compatibility-sensitive
`:calf-ui` project or `com.mohamedrejeb.calf.ui` packages. Public signatures expose
Compose/Material types, so Kotlin/Compose/Material version compatibility is part
of the API contract, not merely an implementation detail. `ExperimentalCalfUiApi`
is a warning-level opt-in; some native manager/helper classes are public in the
iOS source set with internal constructors or an `InternalCalfApi` marker, while
others such as `DampedDragAnimation`, `InteractiveHighlight`, `LocalBackdrop` and
color/keyboard helpers are public without a uniform internal boundary. Review
that surface before stabilizing/reorganizing it; do not silently break binaries.

### Baseline inventory

Counts use `git show BASE:path` decoded text split into physical lines, including
comments/blank lines; they are not complexity or passing-test measures.

| Source set | Kotlin files | Lines | `@Test` annotations |
|---|---:|---:|---:|
| commonMain (including generated symbols) | 50 | 9,749 | 0 |
| iosMain | 52 | 6,598 | 0 |
| materialMain | 21 | 1,115 | 0 |
| androidMain | 2 | 11 | 0 |
| desktopMain | 1 | 6 | 0 |
| jsMain | 1 | 6 | 0 |
| wasmJsMain | 1 | 5 | 0 |
| nonAndroidMain | 1 | 5 | 0 |
| commonTest | 5 | 361 | 32 |
| desktopTest | 6 | 730 | 37 |
| **Total** | **140** | **18,586** | **69** |

There are **128 handwritten production files (10,489 lines)**, **11 test/fixture
files (1,091 lines)**, the generated symbol table, and one 39-line Gradle file.
There are no other tracked resources in this module. The exhaustive file/symbol
ledger at the end distinguishes implementation review from target execution.

## Build and source-set boundaries

`calf-ui/build.gradle.kts` applies `compose.multiplatform` and
`module.publication`, and calls `withBrowserTestBundling()` so browser common
tests can receive the Skiko runtime. The shared conventions declare Android,
desktop JVM, browser JS, browser WasmJS, iOS Arm64 and Arm64 simulator. No Intel
simulator implementation or macOS-native actual is declared by this module.
Desktop is the JVM renderer on supported host OSes, not an AppKit/WinUI widget set.

| Dependencies declared here | Purpose / review consequence |
|---|---|
| common: `calf-core`, Compose foundation/Material3, coroutines | Public types, state, effects, gestures and Material implementation; core opt-in/context facilities |
| commonTest: `kotlin-test` | Assertions and target test annotations |
| desktopTest: Compose UI test, `compose.desktop.currentOs` | Material composable tests with desktop Skiko; requires a usable graphical/headless environment |
| Android: activity-compose, coroutines-android | Host/activity and main-dispatcher integration |
| desktop: coroutines-swing | UI dispatcher for JVM Compose environment |
| iOS: Kyant Backdrop and Shapes | Raster backdrop/lens/blur/shadow Liquid Glass effects and Capsule geometry; **not UIKit controls** |

The baseline version catalog selected Kotlin **2.4.20**, Compose **1.12.0**,
Material3 **1.12.0-alpha03**, coroutines **1.11.0**, datetime **0.8.0**,
Backdrop **2.0.1** and Shapes **1.2.1**. These are baseline selections, not a claim
that every coordinate resolved or every combination built. See the
[build audit](../audit/build-security.md) and testing evidence for command
outcomes and migration edits. `ImageUtils` uses Skia/CoreGraphics; date conversion
uses kotlinx-datetime (available through the project's Compose/dependency graph).
No network service, storage database or background worker is owned by `calf-ui`.

## Renderer and feature matrix

| Public family | Android / desktop / JS / Wasm | iOS below26 | iOS26+ |
|---|---|---|---|
| `AdaptiveButton`, `AdaptiveIconButton` | Material3 button/icon button | **Compose** Cupertino button | **Compose** Liquid Glass button |
| `AdaptiveSwitch` | Material3 Switch | **Compose** Cupertino switch | **Compose** Liquid Glass switch |
| `AdaptiveSlider` | Material3 Slider, including steps | **Compose** Cupertino slider | **Compose** Liquid Glass slider; steps currently dropped |
| `adaptiveClickable` | foundation combinedClickable | **Compose** combinedClickable with press scale | Same |
| Circular progress | Material3 CircularProgressIndicator | **Compose** CupertinoActivityIndicator | Same |
| Single inline date | Material3 DatePicker | Native UICalendarView on16+; UIDatePicker inline earlier | Native UICalendarView |
| Wheels / compact date | Material3 date picker / outlined field + transactional dialog | Native UIDatePicker wheels/compact | Same native modes |
| Date range | bounded Material3 DateRangePicker | Material fallback below16, native UICalendarView multi-selection on16+ | Same native range adapter |
| Time | Material3 TimePicker | Native UIDatePicker wheels | Same |
| Alerts | Material3 AlertDialog/BasicAlertDialog | Native UIAlertController | Same, OS renders appearance |
| Bottom sheet | Material3 ModalBottomSheet | Native page-sheet UIViewController hosting Compose content | Same native controller |
| Top / bottom navigation bars | M3 TopAppBar/NavigationBar | Native UINavigationBar/UITabBar overlay | Same, OS26-specific size/styling branches |
| Toolbar | M3 HorizontalFloatingToolbar | **Actual:** native UIToolbar if iosItems exist, otherwise nothing | Same; documented Material fallback is missing |
| Dropdown | Material3 DropdownMenu from required `materialContent` | Native UIButton/UIMenu trigger | Same; version predicate/fallback defects |
| Expandable FAB (**internal**) | Compose Material-style expansion | Material-style fallback | Native experiment when iosItems nonempty, otherwise Material fallback |

Native-looking does not mean native-backed. In particular there is no UISlider,
UISwitch or UIActivityIndicator behind these adaptive APIs. Source guards for16
and26 do not prove all older deployment targets can link/run: Apple SDK/API
availability must be checked in a real Apple build. Not all shared arguments can
be represented by every renderer; the detailed support notes below separate
intentional adaptation from silent discarded parameters.

## Date subsystem: state, rules and execution

### Common contract and algorithms

`rememberAdaptiveDatePickerState` uses `rememberSaveable` with a rule-aware Saver.
Initial selection/month/year/modes initialize once; changing an `initial*` argument
is not a request to replace existing state. The helper explicitly reapplies the
current `selectableDates` on recomposition. Use a stable rule identity (an object,
data class, or remembered value); recreating anonymous rules can cause redundant
work. Setting a new single-date rule invokes `snapSelectionToSelectable`.

The public state exposes selected UTC-day millis, display mode and selectable
rules; Material also exposes `datePickerState`. `UIKitDisplayMode` is an inline
value class with Picker/Wheels values mapped to inline versus wheels by the
native facade. Unknown stored mode values fall back through the conversion
helpers; Savers retain old five-item input compatibility. iOS has a stricter
ERROR deprecation on `setSelection` than the Material warning, a small source/API
inconsistency worth preserving in compatibility notes until deliberately changed.

`DateBounds` itself implements `SelectableDates`; bounds are inclusive **UTC
calendar days**, not exact instants. `floorDiv(MILLIS_PER_DAY)` is used rather than
truncating integer division, correctly handling negative epoch milliseconds.
`isYearWithinBounds` uses a proleptic Gregorian days-to-civil algorithm, not a
platform time zone. `and` composes date and year predicates. Bounds extraction
only understands `DateBounds` and nested `CombinedSelectableDates`; it cannot
infer endpoints from an arbitrary predicate. Intersection takes the tighter min
and max, including an empty intersection (UI-004).

`nearestSelectableDay` first clamps into known bounds, then checks the current
day and up to366 later/earlier day pairs, **later first on ties**. It calls
`isSelectableDate`, not `isSelectableYear`. `resolvePickedDay` keeps a valid pick,
otherwise substitutes the nearest accepted day or the original pick if none is
found. Single-state snapping similarly retains the old date on failure. This
behavior has explicit existing tests: do not relabel it as a newly discovered
unintentional bug (UI-008). A picker is not a business-rule validation authority.
Neither native single nor native range helper checks `isSelectableYear`; a rule
rejecting a whole year but accepting individual dates does not block native taps
(UI-001).

### Material single/compact date flow

```text
remembered AdaptiveDatePickerState
    ├─ Material DatePickerState: selected date/month/mode/year validation
    ├─ mutable current rule
    └─ RuleTrackingDatePickerState(delegate, rule provider)
          └─ DatePicker sees latest rule object rather than cached old identity
rule assignment → nearest-date snap → underlying selectedDateMillis setter
```

The wrapper delegates all Material methods but overrides `selectableDates`. The
explicit `this.selectableDates` in its provider avoids accidentally closing over
the constructor parameter; this is an important positive correction. The plain
Material facade forwards formatter/title/headline/mode toggle/colors.

Compact Material mode has a saveable `isDialogOpen` and an OutlinedButton label
formatted using the platform calendar locale. Opening creates a scratch Material
state. Editing changes only scratch; confirm assigns its selected millis to the
hoisted state; cancel/disposal of the dialog discards it. The normal transaction
is covered by seven desktop tests. Dynamic rule or state replacement is not:
scratch is unkeyed and confirm does not revalidate (UI-006). Disabled prevents
opening, but the existing dialog's confirm is not a rule-validation boundary.

Single-date Savers store selection, year endpoints, Material mode and UIKit mode;
they restore the displayed month from selection rather than preserving month
navigation (UI-005). Range state, in contrast, saves its displayed month.

### iOS single-date ownership

```text
AdaptiveDatePicker / AdaptiveCompactDatePicker
    → rememberDatePickerManager(state)
    → DatePickerManager
        ├─ Inline and iOS>=16 → CalendarDatePickerBackend → CalendarViewHost
        │    └─ retained UICalendarSelectionSingleDate delegate
        └─ Otherwise → UIDatePickerBackend
             └─ retained NSObject valueChangedTarget (onDateChanged:)
    → UIKitView(key(manager), NonCooperative interaction)
    → callback converts native date → state.selectedDateMillis
```

The manager owns its backend and publishes aspect ratio/compact intrinsic size.
Inline layout fills available width and uses the measured ratio or a stock
UIDatePicker fallback. Compact mode uses measured size and remeasures after
selection changes. This avoids hardcoding a date-label width. `setSelectedDate`
short-circuits equivalent values; compact remeasurement remains explicit.

`CalendarDatePickerBackend` supports null selection and native per-day rejection.
It selects and scrolls to the initial chosen day, retains its delegate strongly,
updates selectability and refreshes nearby cells. `UIDatePickerBackend` can only
apply minimum/maximum dates, so custom forbidden dates snap on change rather than
appear individually disabled. Its wheels cannot show an empty date: setting null
intentionally leaves the displayed wheel date, while the model can remain null.
The retained target and correct Objective-C selector prevent the old weak-delegate
callback failure.

`CalendarViewHost` configures current calendar/locale/timezone, native bounds,
tint/background, interaction enabled flag, and a retained decoration delegate.
`refresh` constructs days from previous/current/next months, reloads decorations
and requests layout. That is limited visible-window work, unlike full-range
highlighting. `DatePickerManager.applyDateBounds` already calls backend update;
`SyncNativeDatePicker` then calls update again, an avoidable duplicated refresh
worth profiling rather than a standalone high-priority defect.

iOS state canonicalizes only the initial value; later assignments do not enforce
UTC midnight/yearRange. The native effective bounds omit yearRange, and neither
predicate checks `isSelectableYear` (UI-001). The initial displayed month is never
passed to the native manager (UI-005). Manager recreation correctly keys callbacks
to new state, but its sibling synchronization effects omit manager identity and
may skip initialization of equal-valued new managers (UI-003).

### Calendar and time-zone boundary

`KotlinxDatetimeCalendarModel` canonicalizes milliseconds through a UTC date and
records year/month/day/start millis. `DateConversions` translates that civil day
to device-local start/end using kotlinx-datetime; end is the next local day start
minus1ms, **not start+24h**, so normal DST day-length differences are accommodated.
Conversely native date/components are converted to UTC start-of-day. The critical
mismatch is calendar identity: current NSCalendar components are interpreted as
Gregorian LocalDate, and Gregorian components are supplied to a non-Gregorian
calendar (UI-002). Locale selection is platform-specific: Android uses current
Material calendar locale; desktop Java locale; browser locale actuals; iOS current
NSLocale. Locale and calendar are not interchangeable.

### Range picker

`AdaptiveDateRangePickerState` is common and uses Material's DateRangePickerState
even on iOS. It exposes selected start/end, mode, rules and `setSelection` through
a `RuleTrackingDateRangePickerState`. It does not run the single-date snap helper
on every rule assignment. Its documented normalization clears invalid starts,
drops invalid ends and clears reversed ranges; actual native callback interaction
with those state normalizations needs tests.

`DateRangeSelection.afterTap` defines a two-tap state machine: empty/completed
range starts over; tapping before an open start moves the start; equal start
makes a one-day range; a later tap closes it. `days()` enumerates inclusive day
starts. On iOS16+, native select **and deselect** both feed `onTap`, which updates
local range, renders, then calls shared `setSelection`. Rendering highlights
selectable days from the entire interval, not necessarily a gap-free visual band.
The backend stores its local range before shared state validation; rejecting an
out-of-range pick without a changed shared value can leave divergence (UI-001).
Rule updates call `updateSelectableDates` and reload visible decorations but do
not explicitly rerender the highlight list; exact UIKit response remains a
required test, not a proven additional defect.

Long ranges allocate all days/NSDateComponents synchronously (UI-007). On older
iOS and Material platforms, `BoundedMaterial3DateRangePicker` supplies a568dp
height only when the parent height is unbounded, preventing infinite constraints
when placed in a scrolling column. Existing desktop tests cover that safeguard.

## Time subsystem

`rememberAdaptiveTimePickerState` saves hour/minute/is24Hour. Material delegates
to TimePickerState; iOS stores hour/minute as Compose state. The common public
hour/minute are read-only; native callbacks mutate internal holders. Both actual
constructors accidentally validate initialHour twice (UI-009); the older swapped
hour/minute assignment bug was fixed and is not reopened here.

The iOS facade creates UIDatePicker and TimePickerManager with unkeyed remember,
embeds the view, and synchronizes theme/direction. The manager constructs an
NSDate from hour/minute, sets current locale/wheels/time mode and retains an
NSObject target with `onTimeChanged:`. Native change extracts both components and
updates the two state holders. Native dimensions are read from the initial frame
once; dynamic locale/font/size changes have no explicit remeasurement path.
Replacing state leaves callbacks on the old state (UI-010), and is24Hour is an
unused constructor argument (UI-011). No time tests exist at baseline.

## Alerts: model to presentation and callback lifetime

The shared `adaptiveAlertDialogIosActions` constructs confirm first and includes
a dismiss action only for a nonblank dismiss label. `dismissLabelOrNull` makes
null/blank equivalent. Four pure tests and four Material rendering tests protect
single-button support added for upstream#536/#539. Custom Material dismissal
content can still appear when the shared label is absent; Material tests cover it.

`AlertDialogIosAction` contains title/style/callback/preferred/enabled. Properties
contain title/text/animated/style/severity/actions/textFields. Text fields carry
initial value, placeholder, keyboard type, secure entry and callback. The12-case
`IosKeyboardType` mapping is exhaustive; secure fields set `secureTextEntry`
without logging their contents. These APIs do not make arbitrary Compose content
render inside UIAlertController: `materialContent` is intentionally Material-only
(open upstream#259 is a feature request, not an implemented native progress slot).
`rememberAlertDialogIosProperties` omits textFields from its keys (UI-015).

```text
Composable → manager remembered by presenting UIViewController
  → lazy UIAlertController(title/message/style)
  → once-created UIAlertActions and retained text-field NSObject targets
  → DisposableEffect(Unit) calls present
  → LaunchedEffect updates manager model, title/message/action enabled
  → native action calls captured action callback; UIKit auto-dismisses
  → composition removal calls manager.dismiss
```

The manager now extends NSObject (fixing the old dismiss-selector crash) and
strongly retains text-field targets (fixing the old editing callback loss).
These are positive fixes. Remaining boundaries are significant: callbacks still
capture initial actions/fields while title/message can change (UI-012); action
sheet lacks a regular-width popover anchor (UI-013); dismissal while presenting
is discarded and cleanup callbacks are not differentiated from user dismissal
(UI-014). An unfiltered tap recognizer on the alert superview needs inside/outside
hit tests. Native action count/style changes are not advertised as fully live;
index-based enabled updates do not establish stable action identity. The common
facade initially supplies onConfirm as onDismissRequest before an asynchronous
effect changes it to onDismiss; there is an early-event race to test, not an
assertion that it occurs in every presentation.

## Bottom sheet: native controller and suspended state

Material is a thin ModalBottomSheet/SheetState adapter forwarding most arguments.
`rememberAdaptiveSheetState` derives positional/velocity pixel thresholds from
density, uses initial Hidden, and creates a Saver. Callback identity is wrongly a
rememberSaveable reset key (UI-019).

On iOS, `BottomSheetManager` lazily owns a page-sheet ComposeUIViewController.
The composable retains latest content, modifier, colors, callback and confirmation
policy via `rememberUpdatedState`. It passes outer composition locals into the
sheet but then restores the sheet's own local context inside, so nested native
controls see the correct sheet UIViewController. Do not remove that nested local
propagation while fixing lifecycle; historical scrolling/embedded content bugs
make this path regression-sensitive.

A LaunchedEffect attaches the manager to hoisted state; another invokes show.
`show` asks manager to present, sets target Expanded, awaits a CompletableDeferred,
then sets current Expanded. `hide` mirrors that to Hidden. The native delegate can
veto interactive dismissal and reports actual dismissal to the owner callback.
The state does not observe native partial-detent changes or interactive Hidden;
large/medium detents are supplied in reverse order (UI-017). Programmatic policy
checks and skipHidden enforcement are absent (UI-016). Native facade uses only
whether dragHandle is null, not its composable content; sheetMaxWidth/shape/scrim/
contentWindowInsets/properties have no equivalent implementation here.

State holds a strong manager reference, which owns parent controller and captured
content. It is never cleared on disposal. A single hide attempt can be dropped
while presenting; state is nevertheless forced Hidden. Cancellation can leave
shared deferreds completed and reused (UI-018). These are ownership/operation
bugs; sustained heap growth remains unprofiled. Suspend does not imply background
safety: UIKit calls are made on the caller context, so host callers must stay on
Main until an explicit confinement policy is implemented.

## Native navigation bars, scaffold and toolbar

Material top/bottom/scaffold are conventional Material3 wrappers; native-only
models are ignored there and composable slots render instead. Native `TopBarManager`
builds UINavigationItems and left/right UIBarButtonItems, retaining action-handler
objects so UIKit weak targets remain alive. `UIKitUIBarButtonItem` can represent
title/image/system item/fixed or flexible spacing and attached menus; converters
map every declared system enum. Menu items/sections become UIActions/UIMenus with
enabled/destructive behavior and image conversion. No network link is followed by
these converters. Image-only items lack a dedicated common accessibility-label
field; native VoiceOver behavior is a test requirement, not a blanket claim that
UIKit is inaccessible.

`TabBarManager` converts indexed items, assigns selectedItem, retains its delegate
and routes selection to the latest facade callback. Empty items incorrectly leave
old content in place (UI-022). Configuration supports selected tint and pre26
unselected tint; unspecified values restore appropriate native behavior. The code
explicitly says iOS26 unselected tint is unsupported. Title color styling was
added, but typography control and remaining iOS26 limitations from upstream#471
are not all solved. Do not close that request as fully fixed.

The facades attach UINavigationBar/UITabBar directly to the root controller view,
not through a UIView in their Compose node. Auto Layout uses root/safe-area anchors
and OS-specific native height/position heuristics. Their Box placeholders publish
padding through `LocalIosTopBarPadding`/`LocalIosTabBarPadding`. `AdaptiveScaffold`
provides those holders and `LocalBackdrop`, takes max(Material padding,native
padding), animates top/bottom changes and forwards start/end from Material.
This avoids simply adding two full bar paddings, but independent hierarchies mean
Compose transitions/clipping/modifiers do not own the bar (UI-021).

`IosBarHeightCache` holds process-global estimated/measured small/large navigation
and tab heights. Frame observation stops after seven stable readings and never
responds to later rotation/safe-area/large-title changes (UI-020; open#548).
Disposal removes native subviews and clears supplied padding holders, a positive
cleanup path; transition overlap can occur while multiple composables still live.

`ToolbarManager` similarly attaches a UIToolbar to root safe-area bottom, reuses
the bar-item converter/strong handlers, and removes constraints/view on detach.
Unlike the documented adaptive API it has no26+ check and no Material fallback
when iosItems is empty (UI-023); it does not report a Compose size/inset. Multiple
bottom native overlays therefore require explicit coordination.

## Dropdown and internal expandable FAB

`AdaptiveDropDown` is a BoxScope API. Material requires materialContent; it does
**not** synthesize items from iosItems/iosSections despite older documentation.
Most popup/style parameters are dropped by its actual (UI-026).

Native dropdown remembers a mutable delegate, updates current models and uses a
transparent UIButton inserted at index0 of the root view. A matchParentSize Box
tracks positionInWindow/size, divided by density into point-like frame values.
Those are window coordinates, not necessarily the local coordinates of a nested
controller; a nonzero host origin is an unverified positioning risk. The button
is removed on disposal. Direction/frame/menu effects are not keyed to a replaced
button/controller, so equal-valued reattachment also needs tests.

Opening calls performPrimaryAction when the version helper approves; the helper
incorrectly requires minor>=4 even for major>17 (UI-024). The fallback identifies a
private UITouchDownGestureRecognizer class by name and fabricates touches. It then
immediately calls onDismissRequest and has no programmatic close path (UI-025).
Actions are built from current list data on list changes, unlike the alert's
never-rebuilt callback objects. Captured action references still require owners
to supply changed models for changed callbacks.

Expandable FAB APIs and item models are **internal**, not a shipped public widget
contract. Material-style fallback draws a column of action buttons and expanded
labels. The iOS facade has a real >=26 and nonempty-items guard; its native manager
owns a UIView container, main/option UIButtons and retained targets. It calculates
fixed geometry, springs alpha/scale/positions, dispatches selected items and
collapses. `detach` removes view/constraints and handler lists. Updating models
while expanded recreates invisible buttons but unchanged expanded state prevents
reanimation (UI-039). Hardcoded right/bottom offsets, no custom pass-through hit
query, image-only options and NSLog item titles are reasons to keep it internal.

## Compose buttons, switches, sliders, gestures and progress

### Buttons and clicking

`CupertinoButton` is common Compose code:44dp minimum height, configurable filled/
bordered/plain color sets, shape, border and padding; `clickable` supplies Button
role, enabled behavior and interaction source. `CupertinoIndication` is an
IndicationNodeFactory collecting press/release/cancel events and drawing content
with animated alpha. It ensures a100ms minimum highlight but a delayed old release
can clear a later held press (UI-043). Its node coroutine scope gives disposal
cancellation; there is no claim that this helper leaks forever.

The adaptive facade drops some customization even though the underlying Compose
widget supports it (UI-035). Pre26 AdaptiveIconButton maps to CupertinoButton and
ignores supplied colors;26+ maps to LiquidGlassButton, translating content colors
but not all container colors. Accessible labels are the application's content
responsibility, as for normal icon buttons.

`LiquidGlassButton` is public experimental iOS Compose code. It obtains a supplied
Backdrop or creates a local layer backdrop, builds InteractiveHighlight, uses
press-driven glass blur/lens/highlight/shadow, draws a filled surface, then lays
out content in a fixed48dp-height row. A shared backdrop works best when the host
actually records the background; a locally created fallback may have no outside
content to sample. Fixed height/shape and no reduced-effects policy need large
text/reduced-motion/transparency checks. Only InteractiveHighlight.gestureModifier
is consumed; its eagerly compiled drawing shader is unused (UI-041).

Both adaptiveClickable actuals use combinedClickable, forwarding click/long click/
double click/labels/role/enabled/haptic options. iOS applies a0.96 press scale and
no indication; Material uses the caller indication. Six desktop tests exercise
click/long/double, null-handler fallback and disabled behavior. They do not run
the iOS scaling path or native haptics.

### Switches

Common `CupertinoSwitch` animates track color, thumb alignment/aspect ratio and
press response inside51x31dp geometry, forwards thumb content, and uses toggleable
when onCheckedChange exists. Track/thumb color helpers handle enabled/checked
combinations. Null callback means read-only, unlike the Liquid implementation.

`LiquidGlassSwitch` renders64x28dp track and40x24dp glass thumb with separate
fraction state and DampedDragAnimation. Latest checked/callback/enabled/RTL values
are remembered (a positive contrast with Liquid slider), but fraction is mutated
independently of controlled checked. A null/rejecting callback leaves visual state
wrong (UI-030), semantic actions are absent (UI-029), and cancellation goes through
a committing stop callback (UI-031). Current colors use only enabled track colors;
disabled appearance is overall alpha, not declared disabled/thumb/border colors.
Supplied thumbContent and interactionSource are unused (UI-035). Track area has no
own toggle gesture. These are implementation gaps, not unavoidable native limits.

### Slider: pre26

The798-line CupertinoSlider is a Compose implementation adapted from Compose
Cupertino. It validates nonnegative steps, coerces value for display, builds tick
fractions and an active-range holder, and measures thumb/track in a custom Layout.
The thumb is centered relative to the track; placement is relative for RTL.
`calcFraction` handles equal endpoints. Track draws active/inactive lines and
discrete ticks; grouping tick points inside draw allocates transient collections.
Thumb collects interactions into a list that does not affect its current visuals,
an optimization opportunity after profiling.

Three input routes exist: pointer tap animation, custom horizontal drag, and
semantic setProgress. Raw pixel offset scales to/from user value and tick snapping;
onValueChange is filtered against current value through an updated callback holder.
`CupertinoSliderDraggableState` uses MutatorMutex for its own drag operations, but
the newer custom pointer path bypasses it. Incomplete remember/pointer keys,
tap-animation arbitration and missing finally cleanup are UI-034. Semantic
snapping initializes a distance from a potentially negative value (UI-033).
`focusable`, progress semantics and setProgress are otherwise present, an
important accessibility feature that must be retained when fixing the26+ branch.

### Slider:26+ and shared damped helpers

LiquidGlassSlider draws track plus a separate active-track layout, then translates
a glass thumb from DampedDragAnimation.progress. Tap maps track position into
valueRange and triggers animate/callback/completion. Thumb drag uses a remembered
initial touch offset to compensate for animated thumb coordinate changes (the
upstream#517 fix); it then normalizes against trackWidth. callbacks are updated,
but enabled/range/geometry/RTL inputs are stale captures (UI-027), steps do not
exist (UI-028), and zero span yields NaN progress (UI-032). Caller colors and
interaction source do not drive the rendering (UI-035).

`DragGestureInspector` receives first down in Initial/Main passes, immediately
starts and calls onDrag with zero offset, then follows movement/up including a
pointer handoff. Consumption by another recognizer returns cancellation. It is
not a full drag-slop/scroll-arbitration replacement. `DampedDragAnimation` calls
the same stop callback for cancel and normal end (UI-031), springs value/velocity/
press/scale via multiple Animatables, and exposes a pointer modifier. Its mutex
covers only one entry point; repeated updates and frame-velocity updates launch
new jobs, release jobs outlive a new press and wall-clock timestamps are used
(UI-042). Animatable cancellation limits some overlap; no unbounded job-leak or
frame-rate claim was measured.

### Circular progress

Material forwards stroke/track/cap/gap options to Material3. iOS deliberately maps
to the common CupertinoActivityIndicator, using only modifier/color; it is an
indeterminate **Compose** spinner, not UIActivityIndicator. It exposes progress
semantics and animates quantized alpha over a one-second cycle. The intended
eight-spoke drawing uses a0..360 inclusive loop, duplicating one spoke; it replaces
input color alpha instead of multiplying it (UI-044). No accessibility label is
invented; host context should describe what is loading.

## Image, theme, color and native helper boundaries

`UIKitImage` is a sealed common model: SF Symbol system name, ImageVector with
optional dimensions, or ImageBitmap. `toUIImage` dispatches to UIImage.systemImageNamed,
vector rasterization or a CoreGraphics bitmap bridge. Unknown system symbol names
return null. Images can enter bars, menus and the internal FAB, so a shared bug
has multiple visible callers.

Vector rasterization now multiplies dp sizes by density (upstream#520), but combines
all path geometry and draws a solid black fill, ignoring transforms/paint/clips
(UI-036). The bitmap bridge copies PixelMap ARGB words into UIntArray and supplies
an external pointer to CGBitmapContext configured premultiplied-last, then creates
a UIImage snapshot. Byte order/premultiplication/pinning need real Apple pixel
checks (UI-037). The failure path before releasing context/color space is a
source-confirmed leak (UI-038); normal conversion does release CGImage/context/
color space. Skia Surface/Paint lifetime and invalid dimensions also require
failure/pressure tests.

`ColorHelper.toUIColor` transfers RGBA components. Tonal elevation is applied only
when the color equals the Material surface and LocalTonalElevationEnabled allows
it, matching the intended Material surface rule. `ThemeUtils` sets interface style
and semantic content attributes, but its UIView theme helper also mutates the
superview (UI-045). `isDark` is a simple RGB heuristic, not WCAG contrast or an
alpha-aware theme contract. Native view theme, composable color scheme and OS
appearance can legitimately differ; test their ownership explicitly.

`SystemUtils.isIOSVersionAtLeast` parses only the major integer safely, and
`isIOS26OrAbove` delegates to it. It avoids the historical decimal-version parse
failure fixed for native bars. Dropdown uses a separate faulty major/minor
comparison; do not assume all availability checks share the safe helper.

Imported helpers have documented Compose Cupertino/AndroidLiquidGlass provenance;
see [third-party notices](../../THIRD_PARTY_NOTICES.md) for observation pins and
license copies. A pin observed during audit does not establish the exact original
vendoring revision. Public source comments and upstream Git history remain intact.

## Maintainer rules derived from the review

1. Add tests before changing native state/ownership. Most reproducible source gaps
   are small, but modal coordination and root overlays cross lifecycle boundaries.
2. Keep current callbacks separate from once-created native targets, and retain
   Objective-C targets/delegates as long as native controls need them.
3. When a native manager is replaced, all synchronization and disposal effects must
   identify that same owner. Equal parameter values do not initialize a new view.
4. Define UTC civil-day, device-calendar and local-time semantics independently.
5. A platform-neutral parameter must be forwarded, explicitly adapted or documented
   unsupported; do not silently accept unused arguments.
6. User interaction means successful completion, not cancellation. Controlled values,
   visual state and semantic state must agree, including rejected/null callbacks.
7. Keep internal experiments internal and distinguish Material emulation from UIKit.
8. Test native memory/byte format/availability on Apple before making release claims.

## Complete file-level review ledger

The following ledger is generated from the pinned baseline filenames and explicit
review notes, not from a keyword-only defect scan. **Reviewed** means full source
inspection plus the subsystem flow analysis above; it does not mean compiled or
executed. Paths are relative to `calf-ui/src/<sourceSet>/kotlin/com/mohamedrejeb/calf/ui/`
unless explicitly marked. Line ranges identify important declarations (not every
local variable); full files were read. Fixtures and tests are included.

### androidMain

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`datepicker/AdaptiveDatePickerState.android.kt`](../../calf-ui/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.android.kt) / 6 | getCalendarLocalDefault (5) | Platform calendar locale actual; no native picker implementation here. |
| [`dropdown/AdaptiveDropDown.android.kt`](../../calf-ui/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.android.kt) / 5 | Top-level configuration/property | DefaultPopupProperties actual uses focusable=true; same policy on Android/non-Android. |

### commonMain

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`ExperimentalCalfUiApi.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/ExperimentalCalfUiApi.kt) / 14 | ExperimentalCalfUiApi (14) | Warning-level opt-in; not a stability guarantee. |
| [`button/AdaptiveButton.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveButton.kt) / 24 | AdaptiveButton (14) | Expect contract; parameter parity UI-035. |
| [`button/AdaptiveIconButton.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveIconButton.kt) / 19 | AdaptiveIconButton (11) | Expect contract; content-owned label; color parity UI-035. |
| [`button/CupertinoButton.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/button/CupertinoButton.kt) / 181 | CupertinoButton (47); CupertinoButtonColors (95); CupertinoButtonDefaults (105); filledButtonColors (138); borderedButtonColors (154); plainButtonColors (170) | Role/Button clickable,44dp minimum; filled/bordered/plain defaults and color model reviewed. |
| [`button/CupertinoIndication.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/button/CupertinoIndication.kt) / 131 | CupertinoIndication (33); CupertinoIndicationNodeFactory (37); create (41); equals (45); hashCode (51); CupertinoIndicationNode (54); onAttach (64); ContentDrawScope.draw (116) | Node factory equality, interaction collection, draw alpha; delayed release race UI-043. |
| [`button/LiquidGlassButtonColors.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButtonColors.kt) / 48 | LiquidGlassButtonColors (13); copy (19); equals (31); hashCode (41) | Immutable copy/equality/hashCode; color configuration value semantics reviewed. |
| [`cupertino/CupertinoCircularProgressIndicator.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/cupertino/CupertinoCircularProgressIndicator.kt) / 114 | CupertinoActivityIndicator (27); ActivityIndicatorTokens (111) | Progress semantics, infinite animation, spoke painting; UI-044. |
| [`datepicker/AdaptiveCompactDatePicker.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveCompactDatePicker.kt) / 49 | AdaptiveCompactDatePicker (38) | Expect compact contract; Material-specific placeholder/buttons/content slots. |
| [`datepicker/AdaptiveDatePicker.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.kt) / 26 | AdaptiveDatePicker (15) | Expect date picker, formatter/title/headline/mode/colors contract. |
| [`datepicker/AdaptiveDatePickerState.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.kt) / 161 | rememberAdaptiveDatePickerState (27); AdaptiveDatePickerState (76); setSelection (107); Saver (134); displayModeFromValue (148); uiKitDisplayModeFromValue (154); getCalendarLocalDefault (161) | Remember/save state, rule updates, public expect state and enum restoration helpers; UI-001/005/008. |
| [`datepicker/AdaptiveDateRangePicker.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePicker.kt) / 109 | AdaptiveDateRangePicker (40); MaterialDateRangePicker (60); BoundedMaterial3DateRangePicker (83) | Expect API plus shared Material renderer and bounded568dp unbounded-height fallback. |
| [`datepicker/AdaptiveDateRangePickerState.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePickerState.kt) / 178 | rememberAdaptiveDateRangePickerState (34); AdaptiveDateRangePickerState (76); setSelection (139); isDaySelectable (143); Saver (152) | Common Material-backed range state; rule wrapper and Saver including displayed month; native limits UI-001. |
| [`datepicker/DateBounds.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBounds.kt) / 76 | DateBounds (17); isSelectableDate (21); isSelectableYear (24); SelectableDates.and (30); CombinedSelectableDates (35); isSelectableDate (39); isSelectableYear (42); SelectableDates.dateBoundsOrNull (51); DateBounds.intersect (59); intersectOrNull (65); tighterMin (72); tighterMax (75) | Date/year predicates, composition and nested bounds intersection; empty interval UI-004. |
| [`datepicker/DateRangeSelection.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateRangeSelection.kt) / 27 | DateRangeSelection (8); afterTap (12); days (22) | Two-tap selection state machine and eager inclusive-day list; UI-007. |
| [`datepicker/RuleTrackingDatePickerState.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/RuleTrackingDatePickerState.kt) / 22 | RuleTrackingDatePickerState (16) | Delegate with live rule identity, avoiding stale Material selectable-date cache. |
| [`datepicker/RuleTrackingDateRangePickerState.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/RuleTrackingDateRangePickerState.kt) / 18 | RuleTrackingDateRangePickerState (12) | Range delegate with live rule identity; all other methods delegated. |
| [`datepicker/SelectableDays.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/SelectableDays.kt) / 161 | isDayWithinBounds (22); isYearWithinBounds (37); clampDayIntoBounds (53); utcYearOf (72); nearestSelectableDay (92); isSelectable (99); resolvePickedDay (124); AdaptiveDatePickerState.isDaySelectable (138); AdaptiveDatePickerState.snapSelectionToSelectable (152) | UTC bounds/civil-year/clamp/nearest/resolve/state extensions; UI-001/004/008. |
| [`datepicker/UIKitDisplayMode.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/UIKitDisplayMode.kt) / 22 | UIKitDisplayMode internal constructor (8); toString (17) | Inline value class, two mode constants and toString/fallback expectations. |
| [`dialog/AdaptiveAlertDialog.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.kt) / 122 | AdaptiveAlertDialog (65); AdaptiveBasicAlertDialog (113) | Two expect APIs, shared/native-specific parameters; arbitrary Compose body is Material-only. |
| [`dialog/AdaptiveAlertDialogActions.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialogActions.kt) / 44 | dismissLabelOrNull (12); adaptiveAlertDialogIosActions (22) | Blank-label normalization and confirm-first action builder; four tests. |
| [`dialog/uikit/AlertDialogIosAction.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosAction.kt) / 21 | AlertDialogIosAction (15) | Immutable callback/title/style/preferred/enabled model; live identity UI-012. |
| [`dialog/uikit/AlertDialogIosActionStyle.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosActionStyle.kt) / 21 | AlertDialogIosActionStyle (8) | Default/Cancel/Destructive mapping contract. |
| [`dialog/uikit/AlertDialogIosProperties.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosProperties.kt) / 78 | rememberAlertDialogIosProperties (16); AlertDialogIosProperties (59) | Properties plus remember helper; missing textFields key UI-015. |
| [`dialog/uikit/AlertDialogIosSeverity.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosSeverity.kt) / 19 | AlertDialogIosSeverity (10) | Default/Critical enum; native availability needs Apple toolchain. |
| [`dialog/uikit/AlertDialogIosStyle.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosStyle.kt) / 18 | AlertDialogIosStyle (8) | Alert versus ActionSheet presentation; iPad contract UI-013. |
| [`dialog/uikit/AlertDialogIosTextField.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosTextField.kt) / 23 | AlertDialogIosTextField (17) | Initial text, placeholder, keyboard, secure entry, change callback; no arbitrary composable. |
| [`dropdown/AdaptiveDropDown.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.kt) / 56 | BoxScope.AdaptiveDropDown (39) | BoxScope expect API and default properties declaration; forwarding UI-026. |
| [`dropdown/AdaptiveDropDownItem.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDownItem.kt) / 34 | AdaptiveDropDownItem (14); AdaptiveDropDownSection (31) | Item/section models, optional images and enabled/destructive/action behavior. |
| [`fab/AdaptiveExpandableFAB.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/fab/AdaptiveExpandableFAB.kt) / 45 | AdaptiveExpandableFAB (34) | Internal expect API; not public support promise; UI-039. |
| [`fab/UIKitExpandableFABItem.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/fab/UIKitExpandableFABItem.kt) / 17 | UIKitExpandableFABItem (14) | Internal title/image/callback model. |
| [`gesture/AdaptiveClickable.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/gesture/AdaptiveClickable.kt) / 26 | Modifier.adaptiveClickable (14) | Expect combined-click contract including long/double/haptic options. |
| [`navigation/AdaptiveNavigationBar.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.kt) / 50 | AdaptiveNavigationBar (39) | Material slot versus native items/selection/configuration contract. |
| [`navigation/AdaptiveScaffold.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.kt) / 37 | AdaptiveScaffold (26) | Expect scaffold slots, colors, insets and padding callback. |
| [`navigation/AdaptiveTopBar.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.kt) / 54 | AdaptiveTopBar (41) | Material slots versus native title/bar items/configuration; UI-020/021. |
| [`navigation/UIKitNavigationBarConfiguration.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitNavigationBarConfiguration.kt) / 22 | UIKitNavigationBarConfiguration (18) | Native bar title/tint configuration; typography not exposed. |
| [`navigation/UIKitTabBarConfiguration.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitTabBarConfiguration.kt) / 24 | UIKitTabBarConfiguration (20) | Native selected/unselected tints; iOS26 unselected limitation explicitly documented. |
| [`navigation/UIKitUIBarButtonItem.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitUIBarButtonItem.kt) / 122 | UIKitUIBarButtonItem (22); title (38); image (49); systemItem (60); flexibleSpace (71); fixedSpace (76); withMenu (82); UIKitUIBarButtonSystemItem (105) | Factory overloads for title/image/system/space/menu; system-item enum exhaustively mapped. |
| [`navigation/UIKitUITabBarItem.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitUITabBarItem.kt) / 18 | UIKitUITabBarItem (14) | Native item title/image/callback value model. |
| [`progress/AdaptiveCircularProgressIndicator.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/progress/AdaptiveCircularProgressIndicator.kt) / 21 | AdaptiveCircularProgressIndicator (14) | Expect Material-rich progress appearance; native-looking Compose iOS mapping. |
| [`sheet/AdaptiveBottomSheet.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.kt) / 33 | AdaptiveBottomSheet (19) | Expect modal sheet and state contract; native argument limitations UI-016. |
| [`sheet/AdaptiveSheetState.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveSheetState.kt) / 98 | rememberAdaptiveSheetState (16); AdaptiveSheetState (56); show (73); hide (80); Saver (86) | Remember, density thresholds, expect state/Saver; callback reset UI-019. |
| [`slider/AdaptiveSlider.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSlider.kt) / 21 | AdaptiveSlider (11) | Value/range/steps/callback/interaction expect API; UI-027–034. |
| [`timepicker/AdaptiveTimePicker.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePicker.kt) / 17 | AdaptiveTimePicker (12) | Expect state/modifier time control. |
| [`timepicker/AdaptiveTimePickerState.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.kt) / 54 | rememberAdaptiveTimePickerState (10); AdaptiveTimePickerState (39); Saver (52) | Remember/expect hour-minute-format/Saver contract; UI-009–011. |
| [`toggle/AdaptiveSwitch.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/toggle/AdaptiveSwitch.kt) / 20 | AdaptiveSwitch (12) | Controlled nullable callback/checked/enabled/thumb/colors/interaction contract. |
| [`toggle/CupertinoSwitch.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/toggle/CupertinoSwitch.kt) / 92 | CupertinoSwitch (32); SwitchColors.trackColor (79); SwitchColors.thumbColor (87) | Compose toggleable, animated thumb/track, color helpers and null-callback read-only behavior. |
| [`toolbar/AdaptiveToolbar.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbar.kt) / 38 | AdaptiveToolbar (31) | Native>=26/Material-fallback documentation is inconsistent with actual; UI-023. |
| [`uikit/IosKeyboardType.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/uikit/IosKeyboardType.kt) / 69 | IosKeyboardType (8) | All12 keyboard cases reviewed and mapped. |
| [`uikit/UIKitImage.kt`](../../calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/uikit/UIKitImage.kt) / 49 | UIKitImage (18); SystemName (24); Vector (35); Bitmap (48) | SystemName/Vector/Bitmap union; requested vector dimensions; UI-036–038. |

### commonTest

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`datepicker/DateBoundsSelectableDatesTest.kt`](../../calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBoundsSelectableDatesTest.kt) / 70 | DateBoundsSelectableDatesTest (12) | 6 tests: day/year bounds, open bounds, and rules, extracted intersection, unknown predicate. |
| [`datepicker/DateBoundsTest.kt`](../../calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBoundsTest.kt) / 110 | DateBoundsTest (12) | 16 tests: pre-epoch/civil-year/leap boundaries, clamp, nearest/no-valid and resolve policies. |
| [`datepicker/DateRangeSelectionTest.kt`](../../calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateRangeSelectionTest.kt) / 57 | DateRangeSelectionTest (6) | 6 tests: first/later/equal/earlier/completed taps and inclusive-day enumeration. |
| [`datepicker/TestDates.kt`](../../calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/TestDates.kt) / 42 | WeekdaysOnly (30); NoDates (40) | UTC fixture days and WeekdaysOnly/NoDates predicates. |
| [`dialog/AdaptiveAlertDialogActionsTest.kt`](../../calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialogActionsTest.kt) / 82 | AdaptiveAlertDialogActionsTest (9) | 4 tests: null/blank dismiss, action order and distinct callbacks. |

### desktopMain

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`datepicker/AdaptiveDatePickerState.desktop.kt`](../../calf-ui/src/desktopMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.desktop.kt) / 6 | getCalendarLocalDefault (5) | Platform calendar locale actual; no native picker implementation here. |

### desktopTest

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`datepicker/AdaptiveCompactDatePickerMaterialTest.kt`](../../calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveCompactDatePickerMaterialTest.kt) / 123 | AdaptiveCompactDatePickerMaterialTest (22) | 7 tests: placeholder/format/open, scratch isolation, confirm/cancel and disabled opening. |
| [`datepicker/AdaptiveDatePickerStateMaterialTest.kt`](../../calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerStateMaterialTest.kt) / 172 | AdaptiveDatePickerStateMaterialTest (22) | 11 tests: current rules/identity/UI, min/max and weekday snap/no-valid, Saver/legacy format/recomposition. |
| [`datepicker/AdaptiveDateRangePickerStateTest.kt`](../../calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePickerStateTest.kt) / 168 | AdaptiveDateRangePickerStateTest (28) | 9 tests: range/reversal/rules/identity/UI/Saver/year predicate/month/unbounded-height layout. |
| [`datepicker/DayCells.kt`](../../calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DayCells.kt) / 21 | Top-level configuration/property | Localized date-description matcher for Compose semantics day cells. |
| [`dialog/AdaptiveAlertDialogMaterialTest.kt`](../../calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialogMaterialTest.kt) / 93 | AdaptiveAlertDialogMaterialTest (16) | 4 tests: null/blank dismiss, custom material dismiss and two-button rendering. |
| [`gesture/AdaptiveClickableMaterialTest.kt`](../../calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/gesture/AdaptiveClickableMaterialTest.kt) / 153 | AdaptiveClickableMaterialTest (19) | 6 tests: click/long/double, disabled and null-handler fallbacks. |

### iosMain

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`button/AdaptiveButton.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveButton.ios.kt) / 58 | AdaptiveButton (15) | Version routing to Compose Cupertino/Liquid buttons; shape/padding omission UI-035. |
| [`button/AdaptiveIconButton.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveIconButton.ios.kt) / 57 | AdaptiveIconButton (16) | Version routing and color translation/omission UI-035. |
| [`button/LiquidGlassButton.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButton.kt) / 251 | LiquidGlassButton (60); LiquidGlassButtonDefaults (174); filledButtonColors (206); borderedButtonColors (224); plainButtonColors (240) | Glass rendering/effects/defaults, clickable role, fixed height, unused shader path; UI-035/041. |
| [`datepicker/AdaptiveCompactDatePicker.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveCompactDatePicker.ios.kt) / 53 | AdaptiveCompactDatePicker (18) | Native Compact manager/view, measured wrap size, enabled and shared sync effects; UI-003. |
| [`datepicker/AdaptiveDatePicker.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.ios.kt) / 147 | AdaptiveDatePicker (31); rememberDatePickerManager (84); SyncNativeDatePicker (106) | State-keyed manager, UIKitView/interaction/layout and unkeyed sync effects; UI-001/003/005. |
| [`datepicker/AdaptiveDatePickerState.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.ios.kt) / 121 | AdaptiveDatePickerState actual constructor (35); setSelection (69); Saver (96); getCalendarLocalDefault (121) | Initial UTC canonicalization, raw setter, rule snap, plain displayMode/Saver; UI-001/005. |
| [`datepicker/AdaptiveDateRangePicker.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePicker.ios.kt) / 115 | AdaptiveDateRangePicker (27) | Pre16 bounded Material fallback;16+ state-keyed native backend/effects; UI-001/003. |
| [`datepicker/CalendarDatePickerBackend.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarDatePickerBackend.kt) / 84 | CalendarDatePickerBackend (18); dateSelection (28); dateSelection (36); setSelectedDate (59); applyDateBounds (67); updateSelectableDates (71); setEnabled (76); applyColors (80) | Retained single-date delegate; null selection, per-day predicate, show-month and refresh. |
| [`datepicker/CalendarRangePickerBackend.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarRangePickerBackend.kt) / 107 | CalendarRangePickerBackend (19); multiDateSelection (30); multiDateSelection (38); multiDateSelection (46); multiDateSelection (52); onTap (74); render (80); setSelectedRange (87); applyDateBounds (94); updateSelectableDates (99); applyColors (104) | Select/deselect-to-tap state machine, full highlight materialization, bounds and rule refresh; UI-001/007. |
| [`datepicker/CalendarViewHost.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarViewHost.kt) / 108 | CalendarViewHost (33); calendarView (44); showMonth (54); applyDateBounds (58); refresh (68); applyColors (77); setEnabled (83); daysAroundVisibleMonth (88) | Current calendar/locale/timezone, retained decoration delegate, three-month refresh; UI-002/004/045. |
| [`datepicker/DateConversions.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateConversions.kt) / 76 | utcDayToLocalDate (27); localStartOfDay (37); localEndOfDay (45); NSDate.toUtcDayMillis (54); NSDateComponents.toUtcDayMillis (63); utcDayToDateComponents (69) | UTC Gregorian civil day to local day endpoints and reverse native components; UI-002. |
| [`datepicker/DatePickerManager.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DatePickerManager.kt) / 156 | IosDatePickerPresentation (26); DatePickerManager internal constructor (46); applyColors (95); applyTheme (107); applyDateBounds (111); updateSelectableDates (116); setSelectedDate (120); remeasureCompactView (125); setEnabled (131); IosDatePickerPresentation.toUIDatePickerStyle (136); UIView.currentSize (143); UIView.aspectRatioOrZero (146); inlineDatePickerAspectRatio (152) | Backend routing at16, compact remeasurement, aspect fallback, theme/bounds/selection forwarding. |
| [`datepicker/IosDatePickerBackend.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/IosDatePickerBackend.kt) / 30 | IosDatePickerBackend (10); setSelectedDate (15); applyDateBounds (18); updateSelectableDates (21); setEnabled (23); applyColors (25); applyTheme (27) | View/selection/bounds/rules/enabled/colors/theme native boundary. |
| [`datepicker/UIDatePickerBackend.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/UIDatePickerBackend.kt) / 88 | UIDatePickerBackend (25); onDateChanged (37); setSelectedDate (64); applyDateBounds (71); updateSelectableDates (76); setEnabled (80); applyColors (84) | Retained target, local date conversion, min/max, snap rejected picks and null-display limitation. |
| [`dialog/AdaptiveAlertDialog.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.ios.kt) / 143 | AdaptiveAlertDialog (21); createIosDialogProperties (49); AdaptiveBasicAlertDialog (108) | Both alert composables; controller-keyed manager, live model update and Unit disposal; UI-012–014. |
| [`dialog/AlertDialogManager.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt) / 219 | AlertDialogManager internal constructor (24); textFieldDidChange (78); updateDialogProperties (112); dismiss (151); showAlertDialog (161); AlertDialogIosActionStyle.toUIAlertActionStyle (188); AlertDialogIosStyle.toUIAlertControllerStyle (200); AlertDialogIosAction.toUIAlertAction (209) | Lazy native actions/fields, strong targets, show/dismiss flags and callbacks; UI-012–014. |
| [`dropdown/AdaptiveDropDown.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.ios.kt) / 202 | BoxScope.AdaptiveDropDown (55); DropDownMenuDelegate (156); buildMenu (163); AdaptiveDropDownItem.toUIAction (181); isPerformPrimaryActionAvailable (197) | Hidden button ownership/frame, native menu/actions, expansion trigger and version helper; UI-024/025. |
| [`fab/AdaptiveExpandableFAB.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/fab/AdaptiveExpandableFAB.ios.kt) / 178 | AdaptiveExpandableFAB (45); LiquidGlassExpandableFAB (83); MaterialStyleExpandableFAB (125) | Internal >=26 nonempty native branch and Material-style fallback, backdrop/native owner effects. |
| [`fab/ExpandableFABManager.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/fab/ExpandableFABManager.kt) / 315 | ExpandableFABManager (40); attachTo (56); detach (82); updateItems (93); applyLayoutDirection (134); setExpanded (138); handleMainButtonTap (145); handleItemButtonTap (150); createMainButton (156); createItemButton (179); layoutButtons (203); updateContainerPosition (229); animateExpansion (255); MainFABActionHandler (292); mainButtonTapped (297); ItemFABActionHandler (306); itemButtonTapped (312) | Root container, retained action targets, button layout/expansion, diagnostics and detach; UI-039. |
| [`gesture/AdaptiveClickable.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/gesture/AdaptiveClickable.ios.kt) / 54 | Modifier.adaptiveClickable (17) | Press scale0.96 plus combinedClickable with long/double/haptic propagation. |
| [`navigation/AdaptiveNavigationBar.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt) / 204 | AdaptiveNavigationBar (53) | Root tab bar attach/constraints, stable-frame measurement/padding/cleanup; UI-020/021. |
| [`navigation/AdaptiveScaffold.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.ios.kt) / 85 | AdaptiveScaffold (25) | Local backdrop/bar padding ownership, Material scaffold and animated max-insets merge. |
| [`navigation/AdaptiveTopBar.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt) / 203 | AdaptiveTopBar (55) | Root native navigation attach, OS/large-title sizing, measurement/padding/cleanup; UI-020/021. |
| [`navigation/IosBarHeightCache.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/IosBarHeightCache.kt) / 61 | IosBarHeightCache (17); updateNavBarHeight (46); updateTabBarHeight (56) | Process-global estimated/measured bar dimensions; invalidation UI-020. |
| [`navigation/LocalIosTabBarPadding.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/LocalIosTabBarPadding.kt) / 20 | LocalIosTabBarPadding (18) | Mutable composition-local padding holder used by scaffold/native bar. |
| [`navigation/LocalIosTopBarPadding.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/LocalIosTopBarPadding.kt) / 20 | LocalIosTopBarPadding (18) | Mutable composition-local padding holder used by scaffold/native bar. |
| [`navigation/TabBarManager.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TabBarManager.kt) / 105 | TabBarManager (20); setItems (40); updateConfiguration (62); UIKitUITabBarItem.toUITabBarItem (88); UITabBarDelegate (98); tabBar (101) | Item creation, selectedItem/configuration cache, retained delegate; empty list UI-022. |
| [`navigation/TopBarManager.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TopBarManager.kt) / 267 | TopBarManager (37); update (55); BarButtonActionHandler (125); handleAction (130); UIKitUIBarButtonItem.toUIBarButtonItem (136); buildUIMenu (205); AdaptiveDropDownItem.toUIAction (226); UIKitUIBarButtonSystemItem.toUIBarButtonSystemItem (242); NavigationBarDelegate (263); positionForBar (264) | Native items, retained handlers, dropdown sections/actions, image conversion, system-item and bar-position mapping. |
| [`progress/AdaptiveCircularProgressIndicator.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/progress/AdaptiveCircularProgressIndicator.ios.kt) / 23 | AdaptiveCircularProgressIndicator (11) | Maps to Compose CupertinoActivityIndicator; Material stroke/track/gap parameters do not apply. |
| [`sheet/AdaptiveBottomSheet.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.ios.kt) / 147 | AdaptiveBottomSheet (30) | Current content/callback/local holders, manager attachment/show/disposal; UI-016–018. |
| [`sheet/BottomSheetManager.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt) / 167 | BottomSheetManager (29); applyTheme (75); applyContainerColor (82); show (92); hide (133); BottomSheetControllerDelegate (154); presentationControllerShouldDismiss (159); presentationControllerDidDismiss (163) | Lazy Compose page-sheet controller/delegate, detents, effects, flags/show/hide; UI-016–018. |
| [`sheet/SheetState.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/SheetState.ios.kt) / 127 | AdaptiveSheetState @OptIn (16); show (61); hide (85); Saver (106) | Policy/init, current/target values, manager ref, deferred waits/Saver; UI-016–018. |
| [`slider/AdaptiveSlider.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSlider.ios.kt) / 44 | AdaptiveSlider (10) | Pre26 Cupertino versus26+ Liquid mapping; discrete steps absent in new branch UI-028. |
| [`slider/CupertinoSlider.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt) / 798 | CupertinoSlider (94); CupertinoSliderColors (139); thumbColor (152); trackColor (156); tickColor (166); equals (175); hashCode (191); CupertinoSliderDefaults (213); colors (218); Thumb (246); Track (280); CupertinoSliderPositions (378); equals (388); hashCode (396); CupertinoSliderImpl (408); scaleToUserValue (433); scaleToOffset (436); CupertinoSliderDraggableState (597); dragBy (604); drag (609); dispatchRawDelta (618); CupertinoSliderComponents (627); snapValueToTick (636); stepsToTickFractions (648); scale (652); calcFraction (655); Modifier.cupertinoSliderSemantics (662); Modifier.cupertinoSliderTapModifier (710); cupertinoAnimateToTarget (763); ViewConfiguration.pointerSlop (791) | All798 lines: models/defaults, draw/layout, drag/mutex/tap helpers, semantic snapping and animation; UI-033/034. |
| [`slider/LiquidGlassSlider.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt) / 336 | LiquidGlassSlider (65); LiquidGlassSliderColors internal constructor (270); equals (275); hashCode (284); LiquidGlassSliderDefaults (301); colors (327) | All336 lines: constraints, remembered gestures, layers, thumb effects and color/default models; UI-027–029/032/035. |
| [`timepicker/AdaptiveTimePicker.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePicker.ios.kt) / 96 | AdaptiveTimePicker (30) | Unkeyed UIDatePicker/manager and theme/direction/view embedding; UI-010. |
| [`timepicker/AdaptiveTimePickerState.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.ios.kt) / 67 | AdaptiveTimePickerState actual constructor (28); Saver (50) | Hour/minute state, duplicated guard, format and Saver; UI-009. |
| [`timepicker/TimePickerManager.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/TimePickerManager.kt) / 68 | TimePickerManager internal constructor (15); onTimeChanged (25) | Retained time target, component conversion, locale/wheels setup and frame snapshot; UI-010/011. |
| [`toggle/AdaptiveSwitch.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/AdaptiveSwitch.ios.kt) / 40 | AdaptiveSwitch (10) | Cupertino versus Liquid routing, missing color translation on26+; UI-035. |
| [`toggle/LiquidGlassSwitch.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt) / 355 | LiquidGlassSwitch (69); LiquidGlassSwitchColors (242); LiquidGlassSwitchColors.trackColor (258); LiquidGlassSwitchColors.thumbColor (266); LiquidGlassSwitchColors.trackBorderColor (274); LiquidGlassSwitchColors.thumbBorderColor (282); LiquidGlassSwitchDefaults (292); colors (328) | All355 lines: fraction/controlled state, gesture/semantics, effects/colors/defaults; UI-029–031/035. |
| [`toolbar/AdaptiveToolbar.ios.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbar.ios.kt) / 62 | AdaptiveToolbar (31) | Native-only/nonempty path contradicts fallback docs; UI-023. |
| [`toolbar/ToolbarManager.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/ToolbarManager.kt) / 77 | ToolbarManager (22); attachTo (35); detach (51); applyLayoutDirection (57); update (61) | Root safe-area toolbar attach/detach, constraints, strong bar-action handlers; UI-023. |
| [`utils/Backdrop.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/Backdrop.kt) / 13 | LocalBackdrop (13) | Public nullable LocalBackdrop; host must supply/record useful background. |
| [`utils/ColorHelper.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ColorHelper.kt) / 35 | Color.toUIColor (13); surfaceColorAtElevation (23); ColorScheme.applyTonalElevation (28) | RGBA conversion; tonal elevation gated by surface equality and local policy. |
| [`utils/DampedDragAnimation.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt) / 142 | DampedDragAnimation (20); press (86); release (95); updateValue (113); animateToValue (120); updateVelocity (134) | Five Animatables, press/release/value/velocity, pointer modifier/mutex; UI-031/032/042. |
| [`utils/DragGestureInspector.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DragGestureInspector.kt) / 85 | PointerInputScope.inspectDragGestures (15); AwaitPointerEventScope.drag (42); AwaitPointerEventScope.awaitDragOrUp (64) | First down, no slop, consumption cancellation, pointer handoff/up; UI-031. |
| [`utils/ImageUtils.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt) / 118 | UIKitImage.toUIImage (36); ImageVector.toUIImage (43); ImageVector.toImageBitmap (49); ImageBitmap.toUIImage (71); ImageVector.toPath (103); traverseNodes (107) | System symbols, vector rasterization/traversal, raw bitmap CoreGraphics bridge; UI-036–038. |
| [`utils/InteractiveHighlight.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlight.kt) / 123 | isRuntimeShaderSupported (22); InteractiveHighlight (24) | Shader constructor/drawing, gesture press/offset animation; public support stub and unused modifier UI-041. |
| [`utils/IosKeyboardTypeUtils.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/IosKeyboardTypeUtils.kt) / 37 | IosKeyboardType.toUIKeyboardType (22) | Exhaustive12-case IosKeyboardType-to-UIKit constants. |
| [`utils/SystemUtils.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/SystemUtils.kt) / 12 | isIOSVersionAtLeast (6); isIOS26OrAbove (12) | Safe major parser and26+ predicate; separate dropdown comparator is not this helper. |
| [`utils/ThemeUtils.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ThemeUtils.kt) / 47 | UIViewController.applyTheme (11); UIView.applyTheme (19); UIView.applyLayoutDirection (29); UIViewController.applyLayoutDirection (36); isDark (40) | Interface style/direction plus luminance heuristic; parent mutation UI-045. |
| [`utils/datetime/KotlinxDatetimeCalendarModel.kt`](../../calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/datetime/KotlinxDatetimeCalendarModel.kt) / 52 | KotlinxDatetimeCalendarModel (11); getCanonicalDate (12); Instant.toCalendarDate (22); CalendarDate (44); compareTo (50) | UTC canonical date via kotlinx-datetime, CalendarDate ordering/value fields. |

### jsMain

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`datepicker/AdaptiveDatePickerState.js.kt`](../../calf-ui/src/jsMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.js.kt) / 6 | getCalendarLocalDefault (5) | Platform calendar locale actual; no native picker implementation here. |

### materialMain

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`button/AdaptiveButton.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveButton.material.kt) / 36 | AdaptiveButton (15) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`button/AdaptiveIconButton.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveIconButton.material.kt) / 29 | AdaptiveIconButton (12) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`datepicker/AdaptiveCompactDatePicker.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveCompactDatePicker.material.kt) / 109 | AdaptiveCompactDatePicker (24); AdaptiveDatePickerState.newDialogState (100) | Outlined field plus scratch DatePickerDialog transaction; live-rule/owner replacement UI-006. |
| [`datepicker/AdaptiveDatePicker.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.material.kt) / 28 | AdaptiveDatePicker (10) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`datepicker/AdaptiveDatePickerState.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.material.kt) / 143 | AdaptiveDatePickerState actual constructor (37); setSelection (98); Saver (120) | Material state delegation with live rule holder, snap and five-item Saver; UI-005/008. |
| [`datepicker/AdaptiveDateRangePicker.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePicker.material.kt) / 29 | AdaptiveDateRangePicker (11) | Shared Material range renderer with bounded-height safeguard. |
| [`dialog/AdaptiveAlertDialog.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.material.kt) / 99 | AdaptiveAlertDialog (20); AdaptiveBasicAlertDialog (86) | M3 rendering/default slots; null/blank/custom dismiss handling and BasicAlertDialog. |
| [`dropdown/AdaptiveDropDown.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.material.kt) / 41 | BoxScope.AdaptiveDropDown (19) | DropdownMenu forwards only four arguments; popup/style omissions UI-026. |
| [`fab/AdaptiveExpandableFAB.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/fab/AdaptiveExpandableFAB.material.kt) / 91 | AdaptiveExpandableFAB (35) | Internal Compose expansion/labels, main-item fallback and collapse callbacks. |
| [`gesture/AdaptiveClickable.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/gesture/AdaptiveClickable.material.kt) / 39 | Modifier.adaptiveClickable (13) | combinedClickable including indication/long/double/haptic parameters; desktop test coverage. |
| [`navigation/AdaptiveNavigationBar.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.material.kt) / 40 | AdaptiveNavigationBar (20) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`navigation/AdaptiveScaffold.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.material.kt) / 38 | AdaptiveScaffold (14) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`navigation/AdaptiveTopBar.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.material.kt) / 47 | AdaptiveTopBar (23) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`progress/AdaptiveCircularProgressIndicator.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/progress/AdaptiveCircularProgressIndicator.material.kt) / 27 | AdaptiveCircularProgressIndicator (11) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`sheet/AdaptiveBottomSheet.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.material.kt) / 46 | AdaptiveBottomSheet (16) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`sheet/AdaptiveSheetState.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveSheetState.material.kt) / 90 | AdaptiveSheetState actual constructor (13); show (52); hide (61); Saver (69) | Material SheetState wrapper, show/hide/current/target/isVisible and Saver. |
| [`slider/AdaptiveSlider.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSlider.material.kt) / 32 | AdaptiveSlider (10) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`timepicker/AdaptiveTimePicker.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePicker.material.kt) / 21 | AdaptiveTimePicker (9) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`timepicker/AdaptiveTimePickerState.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePickerState.material.kt) / 66 | AdaptiveTimePickerState actual constructor (25); Saver (49) | Material TimePickerState wrapper/Saver; own guard typo UI-009. |
| [`toggle/AdaptiveSwitch.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/toggle/AdaptiveSwitch.material.kt) / 28 | AdaptiveSwitch (10) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |
| [`toolbar/AdaptiveToolbar.material.kt`](../../calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbar.material.kt) / 36 | AdaptiveToolbar (20) | Thin Material3 actual; corresponding public arguments/callback flow reviewed; native-only slots intentionally not rendered. |

### nonAndroidMain

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`dropdown/AdaptiveDropDown.nonAndroid.kt`](../../calf-ui/src/nonAndroidMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.nonAndroid.kt) / 5 | Top-level configuration/property | DefaultPopupProperties actual uses focusable=true; same policy on Android/non-Android. |

### wasmJsMain

| File / physical lines | Important declarations (baseline line) | Review result / flow |
|---|---|---|
| [`datepicker/AdaptiveDatePickerState.wasmJs.kt`](../../calf-ui/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.wasmJs.kt) / 5 | getCalendarLocalDefault (5) | Platform calendar locale actual; no native picker implementation here. |

### Build and delegated generated table

| File | Review responsibility |
|---|---|
| `calf-ui/build.gradle.kts:1-39` | UI dependency/source-set/test intent reviewed here; shared Gradle, resolution, supply-chain and publication checks owned by build reviewer. |
| `calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/sf/symbols/SFSymbol.kt:1-7006` | Deprecated generated table delegated to navigation/core/icons reviewer; excluded from the128 handwritten-file count. |

**Ledger validation:**139 handwritten/test Kotlin files have explicit entries; all140 module Kotlin files are accounted for including the delegated table. No source file was excluded because it lacked a finding.
