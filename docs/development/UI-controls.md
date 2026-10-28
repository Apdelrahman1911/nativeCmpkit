# UI controls development — UI-027 through UI-045

## Important UI direct closures — 2026-10-28

[UI-043/#163 and UI-044/#164](evidence/ui-important-20261028/README.md) close directly after both original criteria
each pass: immutablefe75ac86 **7/7**, then ca349b19 **3/3** focused actual Linux
Compose/Skia methods,0fail-error-skip. Seven authored names/ten executions, not
ten unique tests;744 unchanged inputs justify not replaying accepted indicator4.
Exact20/40ms/current-press pixels/same-node pending-release detach/reattach, full
spinner cycle/opacity/RGBA/progress semantics accepted.35 closures confirmed;
ledger57implemented/68partial/31verified/8unresolved. Initial zero-test offline/
fixture failures retained. Tests only, no production/API rewrite, subagents,
unrelated replay or native/legal/dependency/ABI/consumer/release waiver.


## Baseline and scope

Work starts after the lead's upstream synchronization at 2026-10-24 18:43:24 UTC,
commit `243cf1df`. At that starting point, the relevant UI production sources
matched the audit baseline `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. Original findings, source
probes and their historical results remain unchanged.

This work owns interactive Cupertino/Liquid controls, button parameter forwarding,
image conversion, the internal expandable FAB, animation/highlight/indicator/theme
helpers and the global UI-040 coverage assessment. UI-001–026/native date, dialog,
sheet, bars and dropdown work is owned by the separate native UI workstream.

## Scoped implementation decisions

- Retain public signatures, defaults and packages. Share only an **internal slider
  input/layout contract** between existing Cupertino and Liquid renderers; this is
  not a replacement of the library/native ownership architecture.
- Move the platform-neutral, internal Cupertino renderer to commonMain so real
  desktop Compose tests execute the same code invoked on iOS. This does not prove
  VoiceOver/device integration. Add direct iOS control/UIImage/UIKit tests too.
- Do not delegate negative snapping to the pinned Material3 slider: its own
  semantics implementation initializes distance with the signed target value.
  Use constant-space normalized snapping for pointer, semantics and keyboard.
- A tap requests its final value once; visual animation must never continue
  writing caller state after a new drag/cancel. Range/steps/geometry/direction/source
  changes cancel active gestures; callback and externally owned values stay fresh.
- Preserve controlled switch state: local motion is only a drag preview, never an
  independent accepted value. Cancel and read-only/disabled input cannot commit.
- UI-040 and device/performance gates remain unresolved until their actual required
  evidence exists. New tests or successful compilation alone do not close them.

## Implementation map

| Finding | Owning code / execution path | Change |
|---|---|---|
| UI-027–034 | `ui/slider/SliderValueDomain.kt`, `SliderInput.kt`, `SliderLayout.kt` in commonMain; existing Cupertino and iOS Liquid renderers | A single internal numeric/input/layout contract; current callbacks, complete geometry/range/step/direction/source keys, atomic tap proposals, normal Foundation horizontal arbitration, disabled guards, progress semantics and keyboard input. |
| UI-030/031 | common `ui/toggle/ControlledSwitchDragState.kt`, iOS `LiquidGlassSwitch.kt` | External `checked` is authoritative. A nullable drag preview is discarded on end/cancel; only a successful changed proposal invokes the callback. Full-track Foundation toggleable handles taps/semantics/keyboard. Read-only is state-only. |
| UI-035 | iOS `AdaptiveButton`, `AdaptiveIconButton`, `AdaptiveSlider`, `AdaptiveSwitch` actuals and existing Liquid renderers | Forward shape, padding, container/content/disabled/track/tick colors, icon/thumb content and supplied interaction sources. Internal overloads accommodate adapter-only values without breaking public signatures/color constructors. |
| UI-036 | common `ui/utils/ImageRasterization.kt` plus iOS `ImageUtils.kt` | Render every vector group/path with transforms, clips, per-path brushes/fill/stroke/alpha/trim, root tint and RTL auto-mirror. Native callers pass their owning layout direction. |
| UI-037/038 | common `ui/utils/PremultipliedRgba.kt`, iOS `ImageUtils.kt` | Explicit sRGB premultiplied RGBA byte conversion; CoreGraphics-owned storage populated while the source bytes are pinned; checked allocations and nested release scopes. Internal allocation boundary permits real-native failure/release tests. |
| UI-039 | iOS `ui/fab/ExpandableFABManager.kt`, `AdaptiveExpandableFAB.ios.kt` | Reapply current expansion after model rebuild, use parent bounds/safe-area/RTL placement, pass empty-overlay hits through, clear animation/handler ownership, reject stale model actions, expose supplied accessibility titles, remove content logging. Still internal. |
| UI-041/042 | iOS `ui/utils/InteractiveHighlight.kt`, `DampedDragAnimation.kt`, `DragGestureInspector.kt`, `LiquidGlassButton.kt` | Lazy optional highlight shader, explicit shader/job disposal, cancellable value/feedback job lanes, no per-frame coroutine launch, monotonic normalized velocity. Observer cancellation never invokes commit callbacks. No measured GPU/frame-time claim. |
| UI-043/044/045 | common `CupertinoIndication.kt`, `CupertinoCircularProgressIndicator.kt`; iOS `ThemeUtils.kt` | Cancel obsolete indication release jobs, honor active press ownership; draw eight unique spokes multiplying caller alpha; restrict UIView theme mutation to the receiver. |

All paths above are below `calf-ui/src/<sourceSet>/kotlin/com/mohamedrejeb/calf/`.
The original Cupertino renderer notices/attribution are retained when moving its
internal implementation from iosMain to commonMain. Public packages and existing
public method/color-constructor signatures are retained. Internal helper methods
are not a new supported API. `DampedDragAnimation.cancel()` and
`InteractiveHighlight.dispose()` are additive lifecycle operations.

### Numeric and interaction policy

- Values and endpoints must be finite; endpoints ordered; `steps >= 0`.
  Out-of-range finite values are clamped. Equal endpoints produce an inert fixed
  slider; zero/narrow widths cannot divide by zero. Unbounded horizontal layout
  uses a bounded 144dp preferred width, subject to parent constraints.
- Double intermediates avoid overflow for opposite finite Float extremes.
  Nearest-step snapping is constant-space; exact ties choose the greater value.
  Dense discrete domains still snap and expose steps but omit visually
  indistinguishable tick guides above 1,000 steps rather than allocate per step.
- Taps request a final value once; animations never write caller state afterward.
  Success emits `Stop`/completion; cancellation emits `Cancel` without completion.
  A callback replacement stays current without restarting input. A contract or
  geometry/source change cancels obsolete input. Horizontal gestures retain
  Foundation pointer-type slop, pointer handoff and parent-consumption behavior.
- Liquid switch release discards preview even if its owner rejects/delays the
  proposal; null callback cannot create an accepted local value. A gesture is not
  a license to mutate externally owned state after cancellation.
- Damped animation outputs remain in the caller's domain; normalized internal
  state keeps span/velocity finite. Press/value animation jobs have explicit
  ownership. This changes the old independent/smoothed velocity animation into
  monotonic measured normalized velocity; hardware visual tuning is unverified.

### Parameter support matrix

| Public input | Cupertino / older iOS branch | Liquid / iOS26+ branch |
|---|---|---|
| Button shape/contentPadding | Forwarded | Forwarded; minimum rather than fixed height lets supplied padding expand |
| Button/icon Material container/content and disabled colors | Forwarded | Translated to explicit glass surface/content; caller disabled colors are not dimmed twice |
| Explicit `liquidGlassColors` | Existing platform-only behavior | Preserved; own documented disabled alpha applies |
| Slider range/steps/value/completion | Shared contract | Same shared contract; existing public Liquid signature remains continuous, adaptive steps use internal overload |
| Slider thumb/track/tick and disabled colors | Forwarded | All Material-selected colors forwarded to the glass renderer |
| Switch checked/callback/enabled | Existing controlled Cupertino implementation | Controlled preview plus full-track toggleable; null callback is read-only |
| Switch thumb content/icon colors/borders/disabled colors | Existing forwarding retained | Content and selected colors/borders now forwarded; public Liquid color constructor unchanged |
| Supplied interaction source | Foundation/indication interactions | Foundation press and explicitly paired drag interactions drive visuals |

Colors are rendered through their platform's existing visual effects; forwarding
is not a promise of identical cross-platform pixels. System effects,
reduced-transparency policy, high contrast and old/current Apple GPU cost still
require verification. The RGB-only `isDark(Color)` heuristic is not redesigned by
UI-045; transparent color/theme policy remains a follow-up gate.

## Evidence ledger — inspected, not inferred

Execution is scheduled by the lead. The first diagnostic compiled changed common
UI production but could not compile all UI tests; **no UI test ran** in that
attempt (pre-existing XML was stale). The second and third diagnostics each ran
**126 UI cases, 125 passed, one failed**, in 24 fresh reports. All 15 new scalar
common cases and 18 of the 19 then-new desktop cases passed. These are selected,
owner-held working-tree diagnostics, **not immutable release verification**.

- [First command/output](evidence/gradle/first-library-desktop.log).
- [Second command/output](evidence/gradle/second-library-desktop.log) and
  [hashes/results](evidence/gradle/second-library-desktop.summary.json):
  shared scalar/switch-preview/RGBA logic, real Cupertino pointer/semantics/
  keyboard, Compose VectorPainter comparisons, actual indicator pixels and
  indication pixels ran. UI test compilation did not imply iOS compilation.
- [Third command/output](evidence/gradle/third-desktop-ui-nav-geo-icons.log) and
  [hashes/results](evidence/gradle/third-desktop-ui-nav-geo-icons.summary.json):
  same UI cancellation failure; selected inputs unchanged during execution.
- [Fourth command/output](evidence/gradle/second-io-perm-and-fourth-ui.log) and
  [hashes/results](evidence/gradle/second-io-perm-and-fourth-ui.summary.json):
  **128/128 UI cases passed** in 24 fresh reports, including all **36 owned
  common/desktop cases** and the corrected scene-cancel/disposal/parent-consumption
  checks. All 283 selected inputs stayed unchanged during execution. The combined
  command still exited 1 for an unrelated picker Android-host test compile error.
  Inspected control-specific report hashes/counts are recorded
  [separately](evidence/ui-controls/fourth-desktop-results.json).
- [First iOS KLIB compile attempt](evidence/gradle/first-ui-ios-klib.log)
  failed main compilation at three FAB `frame` assignments and one separately
  owned native bar assignment; tests did not compile/run. Kotlin's imported
  UIView protocol exposes a readonly property, so owned FAB writes now use the
  actual typed `UIView.setFrame` method. This Linux-host KLIB check cannot
  link/run an iOS binary or substitute for Apple verification.
- [Third-named iOS KLIB diagnostic](evidence/gradle/third-ui-ios-klib.log) and
  [result/input verification](evidence/gradle/third-ui-ios-klib.verification.json):
  **UI production KLIB compiled**, but the iOS test KLIB failed. All 247 selected
  inputs remained unchanged. Errors were missing UIKit containment imports in
  `ThemeOwnershipTest`, the `NativeRuntimeApi` opt-in for real `GC.collect()` in
  `UIImageConversionTest`, and two separately owned native bar test assignments.
  The owned imports/opt-in have been repaired **without changing test bodies or
  assertions**; the [exact-reversal hash receipt](evidence/ui-controls/third-ios-klib-test-repairs.json)
  ties these edits to the failed diagnostic inputs. Overall command exit 1,
  **zero native runtime tests**, no native link.
- [Fourth-named iOS KLIB diagnostic](evidence/gradle/fourth-ui-ios-and-android-nav.log)
  and [input/result summary](evidence/gradle/fourth-ui-ios-and-android-nav.summary.json):
  **UI production and test KLIB compilation passed**, with no compiler errors.
  All 366 selected source/build inputs and conditional source-directory presence
  remained unchanged. The combined command still exited 1 for a separate picker
  Android-host test failure. **Zero iOS runtime tests**, no native linking and no
  Android instrumentation were performed. The [owned review receipt](evidence/ui-controls/fourth-ios-klib-results.json)
  verifies the log hash and scoped result; no finding status was upgraded merely
  for successful compilation.

### JS/browser diagnostic — common policy, not native UI

The lead's [complete-requested JS diagnostic](evidence/js-full-001/receipt.json)
exited **1** after **580.12 seconds**: navigation and WebView tests failed and
share test compilation failed. Independently, `:calf-ui:jsBrowserTest` actually
executed **64/64 passing cases in 11 fresh reports** on Chrome 153/Linux. No UI
case failed or skipped. The [owned source/XML review](evidence/ui-controls/first-js-results.json)
checks all 11 raw and sanitized XML hashes, exact source/test names, raw report
timestamps and the fresh UI task marker. All **691** captured library/build inputs
were unchanged during execution, and all **182** captured UI inputs still matched
at review. The broader 703-file bootstrap inventory is not this run's input count.

The controls workstream contributes **15** of those cases in three classes:

| Executed class | Passed | Actual JS boundary |
|---|---:|---|
| `SliderValueDomainTest` | 8 | Snapping, finite/degenerate domains, geometry arithmetic and bounded tick-list policy; no composed slider, dispatched pointer/keyboard or accessibility event |
| `ControlledSwitchDragStateTest` | 4 | Preview/finish/cancel/threshold policy; no actual switch gesture or visual thumb |
| `PremultipliedRgbaTest` | 3 | Byte order, rounded premultiplication and allocation-dimension validation; no native raster/UIImage/CoreGraphics ownership |

The other **49** cases are common date/time/dialog/dropdown/presentation-policy
tests, not UIKit executions despite some native-oriented class names. These are
additional **target executions** of existing functions, not 64 new tests or a
browser control-rendering suite. This run contains no controls DOM/visual/input
integration, iOS runtime/linking, VoiceOver or GPU/allocation profile. Chrome used
the recorded root-container `--no-sandbox`/`--disable-dev-shm-usage` launcher; that
does not change production sandbox policy or prove a hermetic dependency graph.

All earlier failures and native acceptance gates remain. Finding statuses are
unchanged; UI-040/041 remain unresolved. The held dirty base revision is a local
diagnostic, not an immutable candidate, whole-matrix pass or release authority.

### Full Wasm004 and JS004 — fresh common-test target executions

The later [Wasm004](evidence/wasm-full-004/archive.json) and
[JS004](evidence/js-full-004/archive.json) commands each exited **0** and passed
**290/290 cases across 19 requested modules and 48 reports**. These are separate
local diagnostics, not a reinterpretation of the earlier failed commands. The
[independent UI review](evidence/ui-controls/browser-004-results.json) verifies:

| Target | Command elapsed | UI executed/passed | Controls subset | Other UI common policies |
|---|---:|---:|---:|---:|
| WasmJS | 123.02 s | 64/64 in 11 reports | 15/15 | 49/49 |
| JS | 130.03 s | 64/64 in 11 reports | 15/15 | 49/49 |

Both runs have zero UI failures, errors or skips. All **693** captured inputs were
stable before/after each command and still matched at review, including **182**
UI inputs. Each of the 22 UI reports has matching raw/archive identities, exact
source-method correspondence and a raw timestamp inside its command interval.
The actual UI test tasks emitted fresh execution markers; their compilation
tasks were up-to-date and are not counted as new test execution by themselves.

The same slider 8, switch-preview 4 and RGBA 3 functions ran on both targets:
**30 executions of 15 functions**, not 30 newly authored tests. These are common
policy/helper tests, not composed browser controls, real pointer/keyboard or
accessibility events, visual rendering, UIKit or CoreGraphics lifetime tests.

The [Wasm launcher review](evidence/wasm-full-004-context/context-review.json)
and [JS launcher review](evidence/js-full-004-context/context-review.json) bind
the fresh UI Karma configurations to their selected local tooling paths. Wasm
used the requested prepared tooling home; JS used project `build/js` tooling.
Selected launcher/tooling hashes and the root-container Chrome flags do not prove
dependency closure, provenance, hermetic execution or release readiness.

All statuses and earlier failure evidence remain unchanged. Native linking/device,
visual/performance and immutable-integration gates remain open. These held dirty
sources at base `94d2492e99d5cbc060409d94d9f88febd06222d5` are not an immutable
candidate; a successful local browser matrix does not lift containment.

### Cancellation harness diagnosis (do not conceal the failed runs)

`pointerCancellationNeverFinishesAndPairsTheInteraction` failed because
`TouchInjectionScope.cancel()` in the pinned **ui-test 1.12.2 Skiko dispatcher
delivers no cancel event**. It only clears injector bookkeeping. This dispatcher
is also shared by iOS Compose tests. No production recognizer can observe an
event the harness never sends. The failure is real evidence of an invalid test
assumption, not evidence that the stock Foundation detector lost an actual cancel.

The attempted custom horizontal detector was removed after that discovery;
there was no justification for keeping a copied Foundation gesture fork. The
test-only `internal/PointerCancellation.kt` now additionally calls the actual
`SkikoComposeUiTest.scene.cancelPointerInput()` path used by the iOS mediator.
The original no-completion assertion remains, and interaction pairing is tightened
to **exactly one matching Cancel and no Stop**. Separate tests now exercise actual
node disposal, disabling during drag and ancestor event consumption. Nothing
fabricates control callbacks or InteractionSource events for these tests.

Exact dependency URLs, source jar/file hashes, source line excerpts and reasoning:
[cancellation source evidence](evidence/ui-controls/compose-pointer-cancellation-source.json).
Scene access uses a test-only `InternalComposeUiApi` opt-in. It must be revisited
when upgrading Compose. It does not prove physical UIKit cancellation delivery.
The corrected tests passed in the fourth diagnostic. They remain
**partially verified**: the development policy reserves `verified` for
lead-reviewed required-scope evidence at an immutable integration revision.

## Authored regression inventory

Counts are **source functions**, not executed results. The current owned source
inventory has 15 common + 21 desktop + 36 iOS tests. Common tests execute within
target test tasks, not as a separate additional native execution.

| Source | Cases | Actual boundary exercised / current limitation |
|---|---:|---|
| `commonTest/.../slider/SliderValueDomainTest` | 8 | Real finite-domain/snapping/geometry helpers; passed on desktop, JS and WasmJS, not dispatched browser input |
| `commonTest/.../toggle/ControlledSwitchDragStateTest` | 4 | Actual preview lifecycle; passed on desktop, JS and WasmJS, not a native switch gesture |
| `commonTest/.../utils/PremultipliedRgbaTest` | 3 | Actual byte conversion/allocation bounds; passed on desktop, JS and WasmJS, not a CoreGraphics test |
| `desktopTest/.../slider/CupertinoSliderInteractionTest` | 12 | Actual shared Cupertino control; all 12 passed fourth diagnostic, including corrected scene cancel and added disposal/ancestor-consumption |
| `desktopTest/.../utils/ImageRasterizationTest` | 4 | Real Canvas raster against real Compose VectorPainter; nested groups/clips/brushes/strokes/even-odd/trim/tint/RTL/2x/3x; all passed |
| `desktopTest/.../button/CupertinoIndicationTest` | 2 | Real button pixels under rapid re-press/multiple press cancellation; passed |
| `desktopTest/.../cupertino/CupertinoActivityIndicatorDrawingTest` | 3 | Real production painter pixels, alpha and all eight animation frames; passed |
| `iosTest/.../controls/LiquidGlassControlTest` | 8 | Actual iOS Compose Liquid controls, not sample/stub widgets; range/state/callback refresh, controlled rejection, semantic/pointer cancellation |
| `iosTest/.../controls/AdaptiveControlForwardingTest` | 4 | Actual adaptive iOS APIs, padding/shape/colors/content/source; only the executing OS's chosen branch is covered |
| `iosTest/.../utils/UIImageConversionTest` | 9 | Real CoreGraphics/UIImage pixels, black/white compositing, vector-vs-Compose, 2x/3x scale, invalid inputs, GC retention; injected failures use real successful native allocations/releases |
| `iosTest/.../utils/DragAnimationAndHighlightTest` | 8 | Real helpers, Compose frame clock and owned jobs; rapid re-press, 1,000 updates, interrupted tap animation, constant/wide ranges, cancel-not-stop, lazy shader/disposal |
| `iosTest/.../utils/ThemeOwnershipTest` | 3 | Actual UIView/UIViewController parent/sibling ownership |
| `iosTest/.../fab/ExpandableFABManagerTest` | 4 | Actual UIButton hierarchy/targets, rebuild/empty model, hit testing, RTL/resize, labels and detach |

**iOS production and test KLIB compilation passed; no new iOS tests have run.**
Test presence and Linux-host KLIB compilation do not close a native finding.
Apple linking, real-runtime failures, unsupported renderer behavior and pixel
tolerance still need inspection.
Other native-UI owners' date/time/presentation tests are recorded separately.

## Remaining release gates

1. Corrected desktop cases passed; execute every changed test on an immutable
   integration revision. No stale XML, `NO-SOURCE` or skipped target substitutes.
2. Apple compile + simulator execution of native conversion, managers and iOS
   Compose controls; before/after GC, failure injection and correct main thread.
3. Old and current iOS branches, iPad safe areas/split view/rotation and physical
   input cancellation, two-pointer handoff, VoiceOver, Switch Control, hardware
   keyboard and large Dynamic Type. Scene injection alone does not cover these.
4. Native Instruments/ASan where supported, allocation/frame/GPU measurements,
   background scrolling and reduced motion/transparency policy. Structural job
   counts are not a profiler or proof that effects meet a frame budget.
5. Internal FAB long-menu overflow and genuine safe-area/tab-bar/device layouts;
   no public API promotion. Mixed transparent-theme/native-sheet hosting remains
   a distinct integration check.

UI-040 remains **unresolved** until the actual cross-platform/native/visual/
performance program is executed. UI-041's measured effects/reduced-effects policy
is likewise incomplete. The per-finding [resolution records](resolutions/UI-controls.json)
retain both executed evidence and outstanding requirements; historical audit
records and old defect probes are untouched. Original migration CI is not evidence
for any changed development source.
