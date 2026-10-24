# calf-ui technical audit

**Baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6` (imported upstream main).
**Audit date:** 2026-10-24. **Area:** all handwritten `calf-ui` implementation and
tests; generated deprecated SF symbol catalog delegated to the icons reviewer.

Authoritative structured findings: [`findings/UI.json`](findings/UI.json).
Implementation/ownership guide: [`../modules/ui.md`](../modules/ui.md).
Execution evidence and required platform matrix: [`../testing/ui.md`](../testing/ui.md).
Machine-checkable full-file coverage: [`ui-source-coverage.json`](ui-source-coverage.json).

## Executive assessment

The module is a useful, moderately layered adaptive UI toolkit, not one uniformly
native widget set. It combines thin Material wrappers, UIKit managers and custom
Compose Cupertino/Liquid Glass controls. The most serious remaining defects are
at the boundaries between remembered state, native lifetime and user intent:

- Native alerts can show updated text while executing an old action callback.
- Native alert/sheet cleanup can be discarded during presentation animations.
- Date contracts diverge by platform, and current-calendar components are
  interpreted as Gregorian dates without conversion.
- Liquid Glass controls have disabled/state/cancellation problems and lack
  actionable accessibility semantics; the slider drops discrete steps.
- Root-overlay native bars stop measuring after initial stabilization and do not
  participate in Compose route transitions.

These are implementation findings with exact baseline locations, not a report
based solely on documentation or naming. No Critical issue or proven remote
exploit was identified in this area. **The module should not be declared release
ready solely from this audit:** significant source defects remain and real native
UI, accessibility, pixel-format and lifecycle tests are absent.

There are **45 findings:12 High,25 Medium,8 Low**. Evidence classes are
**34 confirmed-source,3 confirmed-test,5 risk,3 improvement**. The three
confirmed-test findings use narrow exact-source helper probes, not UIKit or
Compose integration. A High improvement (UI-040) is the missing regression-test
program; it is deliberately not mislabeled as a demonstrated runtime failure.

## Method and boundaries

1. Read all128 handwritten production files, all11 tests/fixtures and the build
   file, including full798-line CupertinoSlider and all native backends/managers.
   The detailed139-file Kotlin ledger links each file, important declaration lines
   and review result. The generated7,006-line SFSymbol table has a separate owner.
2. Follow state construction/restoration, common-to-actual dispatch, callback
   capture, remembered/effect ownership, native delegate retention, suspension,
   geometry, gesture arbitration and failure cleanup end to end.
3. Trace pertinent history and archived issues/comments to distinguish old fixed
   bugs from incomplete fixes and still-open reports. Archived upstream text was
   treated as evidence, not executable instructions or proof that current source
   reproduced the report.
4. Inspect every existing test body and run all32 common test assertion bodies
   in a cache-only isolated Kotlin harness. Execute three additional exact-body
   defect characterizations; record source digests, compiler/runtime and stubs.
5. Validate all95 finding source locations against `git show BASE:path`, not
   potentially shifting migration line numbers. No library source was changed.

The coverage inventory comprises140 Kotlin files/18,586 physical lines including
symbols, of which11,580 lines are non-generated implementation/tests. The build
file adds39 physical lines. This is comprehensive **local module source review**,
not a line-by-line audit of all transitive Compose, Skia, Kotlin, Foundation or
Backdrop implementations. Their use/version/provenance was inspected; global
resolution/advisory checks are in [build-security.md](build-security.md).

### Meaning of evidence classes

| Class | Applied here |
|---|---|
| confirmed-source | A precise contract, control-flow, capture, state, cleanup or parameter mismatch visible in the baseline. Native symptoms can still be unexecuted. |
| confirmed-test | A narrow executable source-derived assertion reproduced the described helper behavior. All three entries name what was stubbed and what was not run. |
| risk | A credible failure path whose target-dependent consequence needs runtime/profiling confirmation: invalid native intervals, range performance, pixel bridge, animation scheduling, parent theme propagation. |
| improvement | Explicit policy/coverage/performance work, not an accidental defect asserted without evidence. |

For example, UI-013 confirms that an iPad-required action-sheet anchor is not set;
it does **not** say this Linux host observed an iPad crash. UI-038 confirms an
owned native resource is skipped by an early return; it does **not** claim a heap
profile showed normal-path growth. UI-037 deliberately remains risk, not a
use-after-free or confirmed channel-swap vulnerability.

## Findings index

Every linked entry in the JSON supplies exact locations/symbols, root cause,
impact, priority, recommendation, change risks, required tests, upstream references,
complexity and dependency IDs. This index is for navigation; it does not replace
those issue-ready technical details.

| ID | Priority / evidence | Finding |
|---|---|---|
| UI-001 | High / confirmed-source | iOS date state and native calendars do not enforce the documented UTC-day/year-range contract |
| UI-002 | High / confirmed-source | Native date conversion treats user-calendar components as Gregorian dates |
| UI-003 | Medium / confirmed-source | Replacing iOS date state can skip initialization effects for the new native picker |
| UI-004 | Medium / risk | Empty or reversed date-bound intersections reach native interval APIs without a defined policy |
| UI-005 | Low / confirmed-source | Single-date state loses displayed-month intent on iOS and save/restore |
| UI-006 | Medium / confirmed-source | Compact Material date dialog can commit stale or newly forbidden scratch selections |
| UI-007 | Medium / risk | Native range highlighting eagerly allocates every day of a selected range on the UI path |
| UI-008 | Low / improvement | No-selectable-day fallback is intentional but requires an explicit caller-visible validation policy |
| UI-009 | Medium / confirmed-test | Time-state constructor checks the hour twice and never validates the minute on iOS |
| UI-010 | Medium / confirmed-source | Remembered native time picker keeps writing to the original state after replacement |
| UI-011 | Low / confirmed-source | Native time picker ignores the public is24Hour preference |
| UI-012 | High / confirmed-source | Presented iOS alerts update their text but retain original action and text-field callbacks |
| UI-013 | High / confirmed-source | iOS action sheets are presented without an iPad popover anchor |
| UI-014 | High / confirmed-source | Alert dismissal during presentation is dropped and cleanup shares user-dismiss callbacks |
| UI-015 | Low / confirmed-source | rememberAlertDialogIosProperties does not remember changes to textFields |
| UI-016 | Medium / confirmed-source | iOS sheet programmatic transitions bypass confirmValueChange and skipHiddenState |
| UI-017 | Medium / confirmed-source | iOS sheet state never tracks partial detents or interactive dismissal and uses reversed detent order |
| UI-018 | High / confirmed-source | Sheet operation cancellation and disposal can leave native presentation and retained owners behind |
| UI-019 | Medium / confirmed-source | Changing the sheet confirmation callback recreates remembered sheet state |
| UI-020 | High / confirmed-source | Native bar measurement permanently stops after several stable frames |
| UI-021 | High / confirmed-source | Native bars live outside the Compose layout/transition hierarchy |
| UI-022 | Medium / confirmed-source | Clearing native navigation-bar items leaves the previous tabs visible |
| UI-023 | Medium / confirmed-source | iOS toolbar does not implement its documented Material fallback |
| UI-024 | Medium / confirmed-test | Dropdown availability check rejects later iOS major versions and selects a private-gesture fallback |
| UI-025 | Medium / confirmed-source | Native dropdown reports dismissal immediately after opening and cannot follow expanded=false |
| UI-026 | Medium / confirmed-source | Material dropdown silently drops most public popup and styling parameters |
| UI-027 | High / confirmed-source | Liquid Glass slider retains stale enabled, range, geometry and direction inside drag callbacks |
| UI-028 | Medium / confirmed-source | AdaptiveSlider drops discrete steps on the iOS26 Liquid Glass branch |
| UI-029 | High / confirmed-source | Liquid Glass slider and switch lack actionable accessibility and keyboard semantics |
| UI-030 | Medium / confirmed-source | Liquid Glass switch can visually diverge from its controlled checked value |
| UI-031 | High / confirmed-source | Cancelled pointer gestures can commit a Liquid Glass switch toggle |
| UI-032 | Medium / confirmed-source | Liquid Glass slider arithmetic does not guard zero-length or invalid numeric ranges |
| UI-033 | Medium / confirmed-test | Cupertino slider accessibility snapping fails for negative target values |
| UI-034 | Medium / confirmed-source | Cupertino slider gesture state has incomplete keys and uncancelled competing tap animations |
| UI-035 | Medium / confirmed-source | Several iOS adaptive visual and interaction parameters are accepted but unused |
| UI-036 | Medium / confirmed-source | ImageVector-to-UIImage conversion discards vector paints, transforms and clipping |
| UI-037 | Medium / risk | Bitmap-to-UIImage bridge has unverified byte-order, premultiplication and buffer-lifetime assumptions |
| UI-038 | Medium / confirmed-source | Native image conversion leaks CoreGraphics resources on the image-creation failure path |
| UI-039 | Low / confirmed-source | Internal expandable FAB loses expanded items on model updates and is not ready for public exposure |
| UI-040 | High / improvement | calf-ui test coverage omits all native managers and most interactive control families |
| UI-041 | Low / improvement | Liquid button eagerly builds an unused highlight shader and lacks a measured effects budget |
| UI-042 | Medium / risk | Damped drag animation launches overlapping jobs per update and tracks velocity with wall-clock time |
| UI-043 | Low / confirmed-source | A delayed Cupertino button release animation can clear the next press highlight |
| UI-044 | Low / confirmed-source | Cupertino activity indicator ignores input alpha and draws the first spoke twice |
| UI-045 | Medium / risk | Applying a native view theme also mutates its parent view style |

## Highest-impact paths and concrete failure scenarios

### Native callback intent and modal ownership

**UI-012:** keep an alert in composition, replace the record and onConfirm callback,
and update its title from recordA to recordB. `updateDialogProperties` updates
controller text but UIAlertAction still holds the old action receiver. Confirm
can act onA. `rememberUpdatedState` or stable handler indirection is needed at the
native target, not merely updating a manager's data class. Text-field targets have
the same callback capture issue. Strongly retaining a stale target fixes garbage
collection but does not make the callback current.

**UI-014/UI-018:** present an alert/page sheet and leave composition before the
completion callback. `isAnimating=true`, `isPresented=false`; hide/dismiss returns
without recording the desired terminal state. Disposal does not retry. The native
present completion can then run after the Compose owner is gone. A single
isPresented Boolean cannot represent requested state, actual state, animation and
terminal disposal. Tests must cover owner/controller/state replacement and cancel
an in-flight suspension, not only normal open/close.

For sheets, deferreds are fields reset after await rather than operation-owned
completion objects. Cancelling the awaiting coroutine before reset can leave a
completed deferred for a later operation. State retains its manager after disposal,
which retains content and controllers. Actual retained heap size is unmeasured.
Programmatic show/hide ignore policy while interactive dismissal consults it
(UI-016), and shared state never observes native partial/Hidden transitions
(UI-017). A safe repair sequence is policy definition, state-event mapping,
per-operation ownership/cancellation, then user callback cardinality.

### Native date calendar identity and constraints

**UI-001/UI-002:** the common contract promises UTC day selection and a year range.
Material delegates canonicalization/year validation to its state; iOS only
canonicalizes its constructor value. Native min/max derive from DateBounds, not
yearRange, and both native selection predicates ignore `isSelectableYear`.
A native range backend updates its local selection before invoking common state
validation, so a rejected result can also leave local/shared state different.

On a Buddhist calendar, year numbers are offset from Gregorian; Japanese era years
and Hebrew leap months are different coordinate systems. `NSCalendar.currentCalendar`
components are supplied directly to Gregorian LocalDate, while outgoing Gregorian
components are passed to UICalendarView configured with currentCalendar. That is
an explicit incompatible conversion regardless of whether the Linux host can
instantiate Foundation. Choose either consistently Gregorian native calendars or
real calendar-to-instant conversion. Preserve the correct local-day DST endpoint
logic already in `localStartOfDay`/`localEndOfDay`.

**UI-004/UI-008:** an empty intersection is a legitimate rule outcome; it must not
be turned into an invalid native interval or silently changed to all dates.
Conversely the existing bounded nearest-date fallback intentionally retains a
rejected date when no valid day is found. Tests explicitly say so. Do not call that
an accidental bug or change it to clearing selection without a compatibility/API
decision. Expose/document validity independently of native visual selection.

### iOS26 control regression rather than native limitation

**UI-027–034:** Liquid Glass controls are custom Compose input/animation logic.
There is no UIKit semantic action automatically rescuing them. A disabled flag
captured at first composition can permit slider changes after disabling; dynamic
range/width/RTL values are also stale. Switch visual fraction mutates even with a
null or rejecting callback, so accessibility reports checked=false while the
thumb appears checked. The same drag-stop callback is invoked for cancellation
and successful completion, allowing state changes when scrolling wins a gesture.

The slider has no setProgress/progress semantics; the switch provides a role and
state description but no click action. The iOS26 slider also omits steps entirely.
These are functional/accessibility regressions relative to the pre26 Cupertino and
Material implementations, not subjective differences in appearance. A semantic
contract test suite should be shared across adaptive branches before refining
glass effects. For the pre26 slider, the exact negative-value snapping error was
executed with a capture-only semantics stub; its custom drag/tap arbitration still
requires a real pointer-event test.

### Native overlays and responsive layout

**UI-020/UI-021:** top/bottom bars are attached to root UIViewController views,
with independent constraints and only a placeholder/padding relationship to the
Compose scaffold. A stable-frame measurement loop exits permanently; rotation,
Dynamic Type, split view and safe-area changes can invalidate it afterward.
Open upstream#548 describes the matching rotation symptom. Root attachment also
means Compose route visibility/clip/transition does not own the native bar; open
#530 describes early/persistent bars during route transitions/back gestures.

Do not make a large navigation rewrite just because an upstream comment proposes
per-screen UIViewControllers. First pin down intended owner and reproduction,
add tests, then evaluate changes to attachment/visibility/layout observations.
The current inset merge using max rather than adding both full paddings, retained
native targets, and cleanup of removed bar subviews are positive mechanisms to
preserve.

## Executed evidence and non-evidence

Command inspected:

```sh
python3 docs/testing/ui-source-probes.py \
  > docs/testing/evidence/ui-source-probes.txt 2>&1
```

**Exit0.** Kotlin compiler/stdlib/kotlin-test2.4.20 and OpenJDK21.0.12 were used with
256MiB heaps. The script only reads already-cached JARs and immutable baseline
source; copied source/JAR output lives in a temporary directory and is deleted.
The checked-in [log](../testing/evidence/ui-source-probes.txt) records the source
manifest, transformations, Java version and all assertion names.

- **32/32 existing common assertion bodies passed:**6 DateBoundsSelectableDates,
  16 DateBounds,6 DateRangeSelection,4 alert action-builder tests. `@Test` import/
  registration alone was removed. Minimal Compose/Material type definitions stand
  in for annotations, SelectableDates, AllDates and state fields. This demonstrates
  the algorithms/action model, not the actual Material/Compose integration.
- **3 expected defect characterizations passed:**UI-009 guard accepts invalid
  minutes; UI-024 comparator incorrectly rejects18.0/26.0; UI-033 negative semantic
  target-0.7 remains unsnapped in a-1..1,steps3 domain. A positive target0.7 snaps to
  0.5 as a control. These checks succeeding means the baseline defect exists,
  **not that it was fixed**.
- **Zero local full Gradle UI test executions were established.** The shared
  desktop invocation included `:calf-ui:desktopTest` but was terminated at the disk
  reserve (exit143) before library tests. Missing cached dependencies also blocked
  a later focused IO build. No library source compilation error was inferred from
  those infrastructure stops. See the [global ledger](../testing/README.md).

The lead may append real remote results with exact commit/run/test counts to the
global ledger. Successful unrelated Rust builds, task listing or Maven POM
creation are not UI tests. This area report does not preemptively claim any later
remote Compose/UIKit result.

## Historical fixes versus remaining work

References are preserved upstream IDs/links; records/comments are also archived
under `docs/migration/upstream-metadata/`. Issue state alone does not prove a fix.

| History | Baseline interpretation |
|---|---|
| [#548](https://github.com/MohamedRejeb/Calf/issues/548), open | Rotation/padding matches UI-020 source path; no local device reproduction claimed. |
| [#530](https://github.com/MohamedRejeb/Calf/issues/530), open | Root-overlay transition/back-gesture behavior matches UI-021; proposed per-screen controller architecture was not adopted. |
| [#471](https://github.com/MohamedRejeb/Calf/issues/471), open | Partial styling improvement: selected tint, pre26 unselected tint and title color exist; iOS26 unselected styling/typography remain limited. Preserve as an improvement, do not create a duplicate bug claiming all styling is absent. |
| [#259](https://github.com/MohamedRejeb/Calf/issues/259), open | Native arbitrary Compose/progress content is not implemented by UIAlertController. Material-only composable content is an explicit architectural constraint/feature request. |
| [#519](https://github.com/MohamedRejeb/Calf/issues/519), commit`77eeaeb2d249ee559debf82dd2535b4dad733ec8` | Title/message/enabled now update; callbacks remain captured, UI-012. |
| [#525](https://github.com/MohamedRejeb/Calf/issues/525), commit`f71d472` | Text-field target retention present; do not report the old weak-target loss as unfixed. Live callback capture is separate. |
| [#414](https://github.com/MohamedRejeb/Calf/issues/414), commit`f1f2752855de0afd017f725c6685e4193f87eb02`; older#330/#341/#381 | Alert manager is now NSObject with ObjCAction selector. Old unrecognized-dismiss-selector issue is not reissued. Modal coordination remains UI-014. |
| [#264](https://github.com/MohamedRejeb/Calf/issues/264), commit`8b60a6063229e754253cdf6b2e58e604fa01e85a` | Initial hour/minute assignment swap fixed; duplicated-hour validation guard remains UI-009. |
| [#116](https://github.com/MohamedRejeb/Calf/issues/116)/[#119](https://github.com/MohamedRejeb/Calf/pull/119), commit`cc037ffd78c8079db838cce87ba1ccbc80d0eb16` | Historical sheet-state holder workaround is absent in baseline; current callback remember key again permits recreation, UI-019. |
| Sheet commits`764edd576d7839a39bf2b2c4577de13905e5b78f`,`ecf81868aa95c2d336b56a52785a630272a3e4c9` | Detent objects replaced old identifiers; later partial support uses current large-before-medium order, UI-017. |
| [#517](https://github.com/MohamedRejeb/Calf/issues/517), commit`17965c8` | Liquid slider animated-touch-offset compensation exists; current enabled/range/geometry capture remains UI-027. |
| Slider commit`d4ee7aa545002939392a20affe2e246287fc5c87` | Custom horizontal pointer handler replaced draggable path; tap animation and drag no longer share one mutation owner, UI-034. |
| [#520](https://github.com/MohamedRejeb/Calf/issues/520), commit`9a47e53` | Native vector rasterization uses density now; transformed/stroked/multicolor vector fidelity is still lost, UI-036. |
| [#536](https://github.com/MohamedRejeb/Calf/issues/536)/[#539](https://github.com/MohamedRejeb/Calf/pull/539), commit`248fd08` | Single-button/null/blank dismiss support implemented and covered by common/desktop tests. No duplicate defect. |
| [#541](https://github.com/MohamedRejeb/Calf/pull/541),`645b806`; [#543](https://github.com/MohamedRejeb/Calf/pull/543),`1518374`; [#544](https://github.com/MohamedRejeb/Calf/pull/544),`5d31147` | Live selectable rules, compact/date range features are present; rule delegates and bounded Material range layout are positive checks. New dynamic/calendar gaps are UI-001–008. |
| [#549](https://github.com/MohamedRejeb/Calf/pull/549),`249a079`,`18fdcc6`,`805010d`,`a59c512` | Click/long/double/haptic capability and tests exist; not an unimplemented feature. |
| Native version parse commit`0fe18423425011a6fb212eaffe5aa4eee081f041` | Decimal-version parsing fixed in native bars; separate dropdown major/minor comparator remains UI-024. |
| [#408](https://github.com/MohamedRejeb/Calf/issues/408); older#9/#37/#75/#77 | Historical page-sheet/LazyColumn/embedded-content scrolling reports are regression targets. No assertion that those closed symptoms still reproduce on the current toolchain. |
| [#172](https://github.com/MohamedRejeb/Calf/issues/172),#189/#210,#328,#397,#476 | Date timezone/selector/selectability/tint and native padding history informs tests. Current targets are strongly retained and tint is mapped; calendar-identity/state issues are separately evidenced. |
| [#72](https://github.com/MohamedRejeb/Calf/issues/72),#169/#358/#361 | Older browser focus/version/ABI reports retained as historical context, not confirmed current vulnerabilities or failures. |

### Source provenance

CupertinoSlider acknowledges Compose Cupertino. At observed commit
`f66875aa6f3848b30c38e42a89fc99c9ac24a585`, the corresponding source header says
Copyright(c)2023-2024 Compose Cupertino project/open-source contributors with
Apache2.0 terms. Original upstream import in Calf (`fce1638c011f1d5528cbf0c833bee44b64a97e90`)
does not by itself establish the exact source revision copied.

Liquid button/slider defaults credit Kyant AndroidLiquidGlass; animation helpers
were imported around`01a070e`. Against observed AndroidLiquidGlass`kmp` commit
`65ab177e90e5c1d8c62e70cf7755841982da65f6`, package-stripped DragGestureInspector is
an exact match and DampedDragAnimation/InteractiveHighlight are close derivatives.
This is evidence of origin, not proof that the observed later snapshot was the
original vendoring revision. Vendored backdrop/shapes were subsequently replaced
with dependencies in`3d4b53e`.

[THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) and accompanying license copies
are maintained by the attribution reviewer. No source headers/history were
rewritten by this UI audit. Generated SF symbols/font legal distribution questions
are not duplicated under UI IDs.

## Security, performance and reliability interpretation

### Security-relevant boundaries

- No hardcoded credential, network client, command execution or untrusted file
  parser was found in this module. This is a scope observation, not a whole-project
  secrets/advisory guarantee; global scans and dependency caveats live elsewhere.
- Secure native alert fields enable secureTextEntry. Their text is not logged by
  the alert implementation. Internal FAB NSLog includes item titles/geometry;
  remove or gate it before exposing that experiment to sensitive app content.
- UI-012 can execute an action inconsistent with visible intent. It deserves high
  priority even without a remote attacker or a CVE classification.
- UI-037 is a native byte-format/ownership risk requiring Apple diagnostics, not a
  fabricated proven memory corruption. UI-038 is a concrete failure-path cleanup
  problem. Avoid translating either into a blanket claim that all images leak.
- UI-024 depends on private UIKit gesture internals on an unnecessarily wide OS
  range. Fragility/store review are risks, not an actual rejection or exploit.
- Passing a SelectableDates rule or disabling a widget is not authorization or
  business validation. Applications should validate the action/data at their own
  trusted boundary while the UI implementation is corrected.

### Performance paths worth measuring

| Path | Source cost / expected investigation |
|---|---|
| Native range highlight | O(selected days) list/filter/native components and setSelectedDates on UI callback; UI-007. |
| Calendar refresh | Approximately three months of components/layout work; duplicate refresh in single-date sync may be eliminated after behavior tests. |
| Glass rendering | Multiple layers, blur/lens/shadow operations; eager unused shader setup in button; UI-041. GPU/CPU cost was not measured. |
| Damped animation | Jobs on external value updates and each velocity frame, uncancelled delayed release, wall-clock timestamps; UI-042. |
| Cupertino slider | Tick arrays scale with steps; draw-time grouping and unused interaction list. Normal step counts may be cheap; bound pathological inputs and profile before optimizing. |
| Native images/items | Repeated full vector rasterization and pixel copies when item models rebuild; correct fidelity/cleanup before introducing caches keyed by incomplete density/RTL/theme identity. |
| Native bars | Current observer stops too soon; replacing it with an unbounded frame loop would fix one symptom by adding waste. Prefer native layout/trait events. |

There are no captured allocation traces, energy measurements, Instruments leaks,
GPU timings or long-duration native stress results. Source complexity and ownership
paths support the listed tests, not invented benchmark numbers.

## Prioritized implementation sequence

The machine-readable dependency graph avoids cycles. This plan groups related
work for maintainers; it does not authorize publication or a major rewrite.

1. **Add regression harnesses (UI-040, L)** with actual iOS/iPad/Compose controls.
   Preserve the lightweight exact-source probes as diagnostic evidence, not a
   replacement for real target tests. Start callback intent and terminal cleanup
   scenarios before modifying modal code.
2. **Correct user-intent and interaction defects (S–L):**UI-009/012/013,UI-027–034.
   Small guard/comparator/snapping fixes are low-complexity; modal/gesture ownership
   changes require cancellation tests. Accessibility actions and discrete range
   behavior precede further appearance polish.
3. **Repair date and modal contracts (M–L):**UI-001–006,UI-014–019. Define calendar,
   empty-bound/invalid-selection policy and programmatic-vs-user transition policy
   explicitly. Keep historical saved-state formats and current strong targets.
4. **Restore platform layout/API predictability (S–L):**UI-020–026,UI-035. Address
   measurement/reactive input first; evaluate overlay architecture only with a
   documented route/controller ownership design and visual/gesture tests.
5. **Harden resource/fidelity and measure performance (S–L):**UI-007/036–038/041/042/045.
   Verify exact CoreGraphics representation on Apple, test allocation failure,
   then profile ranges/glass/jobs and optimize measured hot paths.
6. **Finish polish and explicitly scoped experimental work (S–M):**UI-005/008/039/043/044;
   preserve#471/#259 as feature/improvement decisions rather than duplicate bugs.

**Release gates:** no important callback/cleanup/accessibility regressions; tested
calendar/range contract; real target builds and representative iPhone/iPad runs;
verified image ownership/pixels; compatible public packages/Savers; complete
attribution; owner authorization for any release/package. None of these is waived
by a successful migration, static review or35-check isolated harness.
