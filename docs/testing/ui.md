# calf-ui testing, evidence and regression plan

**Source under audit:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`.
See [module execution flows](../modules/ui.md), [findings](../audit/findings/UI.json),
[UI audit](../audit/ui.md) and the [global command ledger](README.md).

## 1. What actually ran

| Verification | Inspected outcome | Scope / limit |
|---|---|---|
| `python3 docs/testing/ui-source-probes.py` | **Exit0;35/35 checks:**32 existing common test bodies plus3 expected defect characterizations | Exact common algorithm/model code with documented type stubs; selected exact extracted native/helper bodies. Not Gradle/Compose/UIKit. |
| UI baseline source inventory | **139 handwritten/test Kotlin files covered**, generated SFSymbol table delegated; all140 Kotlin files and build file accounted for | Full-file review ledger; not an executable test. |
| UI finding validation | **45 unique IDs,95 baseline locations in range**, required fields and dependency graph checked | Evidence structure/source reference correctness, not runtime correctness. |
| Shared local Gradle desktop attempt including `:calf-ui:desktopTest` | **Exit143 at disk-safety reserve before library tests** | No local full UI Gradle test executed; no test pass or source compilation failure inferred. |
| Local iOS/macOS UIKit/device checks | **Unavailable on this Linux host** | No native view, gesture, VoiceOver, pixel bridge, Instruments or device result. |

The build reviewer also successfully listed `:calf-ui:tasks --all`, confirming
task names. Listing tasks/POM generation is not running tests. A later focused IO
attempt stopped at uncached Compose/Skiko artifacts; it did not exercise UI.
Evidence for those shared commands is under [evidence/](evidence/) and summarized
in [README.md](README.md). The lead's remote checks, if subsequently completed,
must be read from that global ledger with exact revision/run/result/test counts;
they are not preemptively credited here.

### Isolated probe details and reproduction

Files:

- [`ui-source-probes.py`](ui-source-probes.py): reproducible, cache-only harness.
- [`evidence/ui-source-probes.txt`](evidence/ui-source-probes.txt): inspected output,
  including source SHA256 manifest, Java version, commands and every assertion.

Executed command:

```sh
python3 docs/testing/ui-source-probes.py \
  > docs/testing/evidence/ui-source-probes.txt 2>&1
```

For a future rerun, write a new evidence path rather than replacing the audit log.
The script accepts `--cache /path/to/gradle/caches/modules-2/files-2.1`, locates
exact already-cached JAR versions and refuses to download missing dependencies.
All source comes from `git show` at the baseline, not the current edited file.
Temporary Kotlin/JAR output is deleted automatically. JVM compiler and harness
each use `-Xmx256m`; timeout is120s compilation/30s execution. No Gradle daemon,
shared build directory or package/release task is invoked.

Actual toolchain was **OpenJDK21.0.12**, Kotlin compiler/stdlib/kotlin-test**2.4.20**.
Compiler bootstrap libraries include reflect1.6.10 and coroutines1.8.0 because
those are compiler dependencies; **no application coroutine behavior is tested**.
This does not substitute an older library runtime for the project's coroutines1.11.0.

Transformations and doubles, all visible in the script:

| Input | Treatment |
|---|---|
| DateBounds, SelectableDays, DateRangeSelection | Exact entire production files compiled unchanged. |
| AlertDialogIosAction, action-style enum, shared action builder | Exact entire production files compiled unchanged. |
| Four common test classes and TestDates fixture | Existing assertion bodies unchanged; only `kotlin.test.Test` import and `@Test` registration removed; generated main calls each test explicitly. Assertions are real kotlin-test2.4.20. |
| Compose/Material references | Minimal `Immutable` annotation, experimental opt-in marker, `SelectableDates` interface, `DatePickerDefaults.AllDates`; field-only AdaptiveDatePickerState for extension signatures. No Material DatePickerState, Compose state/recomposition or native bridge is loaded. |
| UI-009 | Exact extracted iOS constructor init block in a tiny class; proves guards, not whole iOS state construction or UIDatePicker normalization. |
| UI-024 | Exact extracted private version predicate; UIDevice only supplies a mutable systemVersion string. No menu API is called. |
| UI-033 | Exact extracted Cupertino semantic helper; minimal Modifier/semantics object captures setProgress action. Arithmetic/branch code is unchanged. No semantics tree, accessibility adapter or pointer input is run. |

### Observed results

```text
EXISTING COMMON ASSERTION BODIES:32/32 passed
UI-009: hour24 rejected; minute-1 and60 accepted
UI-024:17.3=false,17.4=true,17.10=true,18.0=false,26.0=false,26.4=true
UI-033:-1..1,steps3,target-0.7 -> -0.7 (should be-0.5)
        positive target0.7 ->0.5 control
SUMMARY35/35 checks passed:32 existing tests +3 expected defect characterizations
```

A passing **defect characterization** means the undesirable baseline behavior was
observed, not repaired. UI-009/024/033 therefore have `confirmed-test` status with
explicit limited scope. No library source fix was made. Do not count the three
characterizations as pre-existing project tests or interpret35 as a platform
integration test total.

## 2. Existing coverage inventory

There are **69 `@Test` methods in calf-ui**, in nine classes. Two additional files
are fixtures. This is source inventory, not a passing-test count.

| Baseline file under `calf-ui/src` | Tests | Existing behavior covered |
|---|---:|---|
| `commonTest/.../datepicker/DateBoundsSelectableDatesTest.kt` | 6 | Inclusive/open day and year bounds, `and`, nested bounds extraction, unknown rules. |
| `commonTest/.../datepicker/DateBoundsTest.kt` | 16 | Day granularity, Gregorian year/leap boundaries, pre-epoch arithmetic, clamp, nearest day and no-valid fallback, accepted/rejected pick resolution. |
| `commonTest/.../datepicker/DateRangeSelectionTest.kt` | 6 | First/later/equal/earlier/completed range taps and inclusive list. |
| `commonTest/.../dialog/AdaptiveAlertDialogActionsTest.kt` | 4 | Null/blank dismiss label, confirm/dismiss order and distinct callbacks. |
| `desktopTest/.../datepicker/AdaptiveCompactDatePickerMaterialTest.kt` | 7 | Placeholder/format/open; scratch edit isolation; confirm/cancel; disabled opening. |
| `desktopTest/.../datepicker/AdaptiveDatePickerStateMaterialTest.kt` | 11 | Rule delegation/identity/rendered disabled days; bounds/weekday snap; intentional no-valid keep; Saver/legacy list; remembered live rule. |
| `desktopTest/.../datepicker/AdaptiveDateRangePickerStateTest.kt` | 9 | Start/end/reversal; bounds/rule/identity/rendered disabling; Saver; year rejection; selected-month display; unbounded-height scrolling parent. |
| `desktopTest/.../dialog/AdaptiveAlertDialogMaterialTest.kt` | 4 | Null/blank dismissal; custom dismiss composable despite null label; two buttons. |
| `desktopTest/.../gesture/AdaptiveClickableMaterialTest.kt` | 6 | Click, long click, double click, null-handler fallback and disabled behavior. |
| `commonTest/.../datepicker/TestDates.kt`, `desktopTest/.../datepicker/DayCells.kt` | 0 | UTC date/rule fixtures and localized semantic day-cell lookup. |
| **Total** | **69** | **32 common +37 desktop.** |

No tracked calf-ui tests exercise UIKit targets/delegates, native sheet/alert
presentation, time picker, native bars/toolbars/menus, image conversion, sliders,
switches, glass rendering or animation ownership. No calf-ui Android instrumentation,
iOS-specific UI, performance benchmark, screenshot/golden or binary compatibility
suite exists in the baseline. Common tests on an iOS target still do not
instantiate every iOS actual; platform task success must name what it exercised.

## 3. Real project commands to run when resources are available

**Procedures, not additional executed results.** Coordinate with the lead before
shared Gradle runs. Preserve other projects/caches and the documented disk reserve.
Use the committed toolchain; do not downgrade Kotlin/Compose to manufacture a pass.
Use the resource guard in the global testing guide. No command below publishes.

```sh
# Real existing UI tests on desktop; Linux typically needs a display/Xvfb.
xvfb-run -a ./gradlew --no-daemon --max-workers=2 \
  -Pkotlin.compiler.execution.strategy=in-process :calf-ui:desktopTest

# AGP KMP Android host unit tests and compilation (not on-device UI tests).
./gradlew :calf-ui:testAndroidHostTest :calf-ui:compileAndroidMain

# Browser source compilation and common algorithm tests.
./gradlew :calf-ui:compileKotlinJs :calf-ui:compileKotlinWasmJs \
  :calf-ui:jsBrowserTest :calf-ui:wasmJsBrowserTest

# On a compatible macOS/Xcode Arm64 simulator host only.
./gradlew :calf-ui:iosSimulatorArm64Test
./gradlew :sample:common:linkDebugFrameworkIosSimulatorArm64
```

Browser tests need Kotlin/JS dependencies, webpack/Skiko and a usable Chrome/Karma
environment. Framework linking exercises more exported/native interop surface
than an arithmetic common test. It still does not launch a native UI. The sample's
higher deployment target does not verify older guarded library branches; a
separate compatible host is needed for those. No Intel simulator target is declared.

After a real test task, inspect the command exit code, full failure stage, JUnit
XML test counts/skips and target logs. After a successful compile/link, do not say
UI behavior passed unless a test or manual protocol was actually performed.

## 4. Regression fixtures to add

These are **proposed tests/fixtures**, not files already implemented. Use common
algorithm tests where possible, real Compose tests for recomposition/semantics/
gestures, and an iOS test host/XCTest/native fixture for UIKit ownership. Any
resource/duration/visual thresholds must be measured on named hardware.

### A. Dates and time (UI-001–011)

| Scenario | Required assertion |
|---|---|
| UTC canonical selection | Construct/assign intraday, null and pre-epoch values; accepted selectedDateMillis equals the declared UTC-day contract on both actuals. |
| Year domain | Selected/displayed date at/outside yearRange; native taps must not offer an invalid year then diverge from shared state. Test a rule whose `isSelectableYear=false` but `isSelectableDate=true`. |
| Calendar identity | Gregorian/Buddhist/Japanese/Hebrew device calendar: same civil day roundtrips correctly through single/range/compact/wheels, including era/leap-month boundaries. |
| Time zones | UTC, far-negative/far-positive offsets and named DST zones; min/max local-day endpoints include the intended whole day, including23/25-hour days. |
| Bounds | Open, equal-day, reversed and disjoint `and` intervals; empty allowed set never becomes all dates or an invalid native interval. Recovery to a valid interval works. |
| No selectable day | Preserve documented keep-selection behavior unless intentionally changed; cover valid day beyond366-day search, equal-distance tie and noDates. Expose validity separately. |
| State replacement | Replace native state by equal-valued new state and verify bounds/colors/RTL/disabled/view ownership update. Compare callback owner identities. |
| Compact transaction | Open, select date, change rule or replace owner, confirm/cancel. Newly forbidden scratch value is not silently committed under the new rule. |
| Restoration/month | Selected month differs from displayed month; null selection; old five-item single Saver; range displayed-month restoration. |
| Range | First/equal/earlier/completed taps, disabled gaps, native deselection, external setter normalization and rule change while range remains selected. |
| Large range | One day/year/default maximum span: record UI thread duration/native allocation. Require a bounded strategy before allowing arbitrary large custom ranges. |
| Time guards/format | Minute-1/0/59/60 and hour-1/0/23/24;12/24-hour preference versus device locale; replace state and verify edits update only new state. |

### B. Alerts and sheets (UI-012–019)

- Present recordA alert; while visible update title/callback toB. Confirm invokesB
  once, notA. Repeat for text-field callback replacement, action enabled changes
  and documented structural-change limits. Secure field remains secure.
- Present ActionSheet on iPad regular width and split view, using a real bar-item
  and view/rect anchor. Rotate while visible. Missing-anchor policy must be explicit.
- Remove composition at controlled points before/after presentation completion,
  during dismissal, and immediately reopen. No orphaned UIViewController remains;
  cleanup does not emit a second user dismissal or old callback.
- Confirm versus cancel versus outside tap versus programmatic hide: each invokes
  the intended semantic callback at most once. Taps inside text fields do not
  become outside-dismiss events. Test dismissOnClickOutside=false.
- Replace LocalUIViewController/state owner without changing other parameters.
  Only the current owner retains native views/targets; all manager-keyed effects
  initialize the new owner and clean the old one.
- Veto Hidden/Expanded for both interactive and programmatic sheet operations;
  check skipHidden/skipPartial invariants. Disposal still safely releases ownership
  without pretending a business veto permits leaked UI.
- Observe medium/large detent changes and interactive dismissal while keeping the
  composable alive. `currentValue`, `targetValue`, `isVisible` match native state.
- Cancel coroutine awaiting show/hide, deliver completion, then repeat. The second
  call must not return against the first operation's completed deferred. Test two
  callers and opposite operations during animation.
- Change a captured confirmation-policy value while open. Remembered sheet state
  identity stays stable while behavior uses the new callback.
- Include LazyColumn, TextField/keyboard, nested native picker/WebView and bottom
  sheets within sheets. Verify correct local UIViewController/context propagation,
  gesture scrolling and safe areas against historical#37/#77/#408 reports.
- Use weak references/Instruments after repeated removal and forced collection to
  examine controller/content retention. Record whether manager attachment is
  cleared; absence of visible UI alone is not proof of release.

### C. Bars, toolbar and dropdown (UI-020–026)

- Let initial bar measurement stabilize, then rotate repeatedly, change Dynamic
  Type/large-title setting, enter split view and change safe area. Check native
  frame **and** Compose scaffold padding, not just a screenshot of one.
- Push/pop two differently configured screens; cancel/complete an interactive back
  gesture. Outgoing/incoming root bars follow intended owner transition and do not
  overlap or appear prematurely. Test screens with no bar and nested scaffolds.
- Change populated tabs to empty, reorder/repopulate and use an invalid selected
  index. Removed tabs cannot invoke old callbacks; tints restore correctly.
- Toolbar with empty/populated iosItems on pre26/26+; material content counters
  prove whether a fallback actually renders. Combine toolbar, bottom bar,
  keyboard and custom modifier/insets.
- Dropdown version matrix17.3/17.4/17.10/18.0/26.0/26.4; native open/actual dismiss/
  item selection/programmatic close event order. No private recognizer dependence
  should be needed on a supported primary-action OS.
- Move the trigger inside a nonzero-origin nested controller; verify menu origin
  and frame after controller reattachment with otherwise equal parameters.
- Material dropdown: nondefault offset/shape/color/elevations/border/scrollState and
  target-supported PopupProperties. Confirm which native-only slots are intentionally
  ignored, rather than assuming iosItems synthesize Material content.

### D. Controls and animation (UI-027–035,041–044)

- Shared semantics contracts across all adaptive renderers: role, enabled/read-only,
  current value/range/steps, toggle/setProgress action, keyboard focus, callback
  cardinality. Then run VoiceOver/Switch Control/hardware keyboard on iOS26+.
- Change slider enabled both directions, then drag; change range/density/RTL/width
  with equal enabled. Values use current input and stop when disabled. Reset
  gesture-local didDrag on every new gesture/cancellation.
- For all sliders, steps0/1/3, negative/nonzero ranges, equal endpoints, finite
  out-of-range values, invalid nonfinite/reversed ranges and zero/unbounded width
  follow an explicit safe policy. Tap/drag/accessibility snapping agree.
- Switch callback null/rejects/accepts/delays: final visual and semantic checked
  equal controlled input. Entire intended track target responds;44pt minimum
  accessible/touch area and localized state labels are validated.
- Parent scroll consumes a pointer after down on slider/switch; gesture cancels
  without committing. Test multi-pointer handoff, disposal and disabling mid-gesture.
- Pre26 slider tap then immediately drag/retap: no competing stale animation or
  stuck isDragging; completion action occurs as specified after cancellation.
- Supply conspicuous nondefault colors, shape, padding, thumbContent and a monitored
  MutableInteractionSource. Snapshot/interaction assertions expose dropped inputs.
- Rapid Cupertino press/release/repress under a virtual clock keeps the later
  press highlighted. Delayed releases do not reset newer interactions.
- Spinner transparent/half-alpha colors and exact eight spoke positions; semantic
  progress remains present after visual fixes.
- Glass controls: measured creation/allocation/frame budgets for dense lists,
  transparent/opaque backgrounds, reduce motion/transparency and large text.
  Record backdrop contents; a blank unrecorded fallback is not equivalent to a
  provided backdrop. Shader capability should be checked, not hardcoded.

### E. Images, theme and internal experiments (UI-036–039,045)

- Compare source ImageVector and resulting UIImage for transforms/clips/strokes/
  even-odd fill/alpha/multicolor/RTL and2x/3x density. A monochrome SF-symbol-like
  vector is not a sufficient fidelity test.
- Known one-pixel red/blue/green/transparent/half-alpha bitmaps: inspect pixel bytes
  and compositing over black/white. Pin CoreGraphics byte-order and premultiplication
  flags to the observed representation. Stress GC during external-buffer lifetime.
- Inject color-space/context/image allocation failures and invalid dimensions;
  verify every owned native allocation releases, no exception escapes an API that
  promises nullable failure without documentation, and normal images still render.
- Two native controls with opposing theme overrides share a parent; configuring
  one must not unintentionally change its sibling or surviving host on removal.
- Internal FAB: change items while expanded, clear/repopulate, test collapsed
  transparent hit area, layout direction/safe areas and option labels. Keep it
  internal until these work; do not log titles in production diagnostics.

## 5. Platform/device matrix and release evidence

Use at least an iPhone compact presentation and an iPad regular-width presentation;
simulator-only phone tests will miss popover and multiwindow requirements. Exercise
an older supported pre26 path and26+ glass path. Where the claimed deployment range
includes pre16, test that actual range fallback in a compatible host rather than
assuming the sample's higher deployment minimum covered it.

Orthogonal axes: system locale/calendar/timezone; LTR/RTL; normal/accessibility text;
light/dark/mixed per-control theme; hardware keyboard/VoiceOver/Switch Control;
rotation/split-view/safe-area/keyboard; foreground/background/route disposal;
accepted/rejected/null callbacks; dynamic state/controller replacement;
slow/interrupted animations and allocation pressure.

For every real verification record: commit/source identity, command or exact
manual steps, OS/SDK/device/renderer, dependency versions, expected versus observed
result, failure stage, artifacts/test counts and unresolved limits. Screenshots
support layout observations, not callback/resource correctness. A compile/link
success supports build compatibility only. No release/package publishing is part
of this test plan or authorized by a passing check.
