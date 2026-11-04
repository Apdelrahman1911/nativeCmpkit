# Adaptive controls: related #133 / #138 / #129 test patch

Baseline: `ac487941316626cc4b19546ab70f939d98c1c52d` (2026-11-04).
This is an independent implementation/test patch, not a native acceptance or
release receipt. Original audit requirements and accepted older results remain.

## Owning correction (#138 / UI-035)

`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/toggle/CupertinoSwitch.kt`
invoked caller `thumbContent` under the inherited `LocalContentColor`. The iOS26
actual already translated all four supplied Material icon colors; the pre26
Cupertino renderer did not. A non-null custom thumb must instead receive its
**current** enabled/disabled + checked/unchecked caller icon color, scoped only to
that thumb. Do not cache this color or rewrite parent/sibling content locals.

The change preserves the public signature, caller track/thumb colors, layout,
animation, pointer handling, default-null thumb and all previous test bodies.
The default-null case need not allocate an additional local-provider group.
This is intentional correction of ignored customization, not a package/API rename.

## New library cases and real host admission

Files under `calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/`:

| Class | Exact pre26 method | Exact iOS26+ method |
| --- | --- | --- |
| `slider.AdaptiveSliderNativeMatrixTest` | `pre26PublicStepsTapDragAndAccessibilityMatrix` | `ios26PublicStepsTapDragAndAccessibilityMatrix` |
| Same | `pre26PublicNegativeStepsAreRejected` | `ios26PublicNegativeStepsAreRejected` |
| `controls.AdaptiveControlCustomizationMatrixTest` | `pre26CustomColorsContentAndInteractionsSurviveDarkAndLargeText` | `ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText` |
| `toolbar.AdaptiveToolbarFallbackNativeTest` | `pre26EmptyAndPopulatedItemsRenderMaterialSlotsAndCallerPlacement` | `ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement` |

The classname prefix is `com.mohamedrejeb.calf.ui.`. Select four methods on
**each** real OS branch, not all eight on one runtime. Admission reads actual
`UIDevice.currentDevice.systemVersion` on application Main, requires the existing
active/key/attached owned application window, refuses malformed/nonpositive
versions, and asserts `<26` or `>=26`. Wrong or unavailable hosts fail; they are
not skips, a version override, or direct Cupertino execution disguised as pre26.

Use the genuine `:calf-ui:iosSimulatorArm64ApplicationTest` and its original
Worker/native-XML/runtime/source-custody/owned-cleanup protocol. The lead must
qualify finite routing for these **new** selectors before dispatch. The standalone
init below currently admits compilation, not arbitrary/new native execution.
No accepted first-eight `LiquidGlassControlTest` methods are selected or replayed.

### #133 / UI-028: twelve rows per host, plus invalid steps

`AdaptiveSliderNativeMatrixTest` invokes the **public** `AdaptiveSlider` for
`steps=0,1,3` × `range=-2..2,4..12` × `LTR,RTL`. Every row asserts:

- Actual progress current/range/step semantics; endpoint and center taps.
- The first interval's exact halfway tie rounds upwards for discrete values;
  `steps=0` keeps the `.375` fractional proposal continuous.
- Real `SetProgress` proposals, unchanged/NaN/infinity refusal, lower/upper
  clamps, exact change/completion counts and current semantics.
- A completed physical Compose swipe across the actual measured control.
  Positive caller value changes and the **supplied** source's `Drag.Start` and
  same-object `Drag.Stop` are mandatory; cancellation cannot count as success.
- Every callback is finite/in-range and every discrete tap/drag/semantic callback
  belongs to the independently calculated `steps+1`-interval grid.

Gesture injections finish before assertions: no no-op injector `cancel()` or
held-pointer teardown workaround. Separate negative-input methods require
`IllegalArgumentException` with exactly `steps should be >= 0`; an unrelated
host/setup failure cannot satisfy the expectation. Native execution must still
prove asynchronous invalid-composition teardown on both real hosts.

### #138 / UI-035: public customization in four environments per host

`AdaptiveControlCustomizationMatrixTest` executes light/dark Material schemes ×
font scales 1/2, using the real platform density. It renders all four public
Button/IconButton/Slider/Switch APIs with distinctive explicit enabled/disabled
colors; button Rectangle shape/asymmetric padding; actual text and custom thumb.

Each row checks actual captured surface/track/glyph pixels, content locals,
measured padding and text height, caller press/release pairs and a positive
slider drag pair/completion. All four switch icon-color states are observed.
Disabled clicks cannot call the owners or emit enabled source interactions.
The fontScale2 button label must actually grow relative to that theme's scale1
layout. Opaque disabled surfaces are checked on the actual light/dark background,
not inferred from color configuration alone. This is pixel/contrast forwarding
coverage; it does not promise pixel-identical Cupertino and Liquid design.

These are Compose-rendered snapshots and real Compose input on actual iOS
branches, **not** changes to OS Accessibility Settings or spoken VoiceOver/Switch
Control/hardware-keyboard acceptance. Do not attach those unrelated gates to #133
or claim these cases close original assistive-device requirements elsewhere.

### #129 / UI-023: limited, positive public Material fallback

`AdaptiveToolbarFallbackNativeTest` positively proves real Material main/leading/
trailing slots and composition counters: pre26 empty **and populated** native
items, and iOS26+ empty items. Expanded→collapsed→expanded updates use current
slot content. Explicit padding/width allocates measured space above a separately
owned caller bottom row; this is not a absence-only “native toolbar passed” test.

**Still missing:** positively witnessed populated native UIToolbar on iOS26+,
real OS safe-area/keyboard changes, genuine orientation, and simultaneous native
bottom-bar/scaffold integration. The static caller bottom box is not a substitute
for those original tests. Do not close #129 from this subset.

## Owning Desktop regression and compiler scope

`toggle.CupertinoSwitchThumbContentColorTest` has two **new** real Compose cases:

1. `currentCallerIconColorsFollowEveryStateAndDoNotLeakToSiblingContent`:
   four states, replacing caller colors, unchanged inherited sibling local.
2. `disabledCustomThumbInDarkLargeTextActuallyDrawsTheSuppliedIconColor`:
   actual dark/fontScale2 disabled custom glyph pixels, not only configuration.

Execute only those exact new methods on `:calf-ui:desktopTest` (Linux Xvfb),
preserve the real red, then run the failed/owning affected subset after the fix.
`scripts/ci/adaptive_controls_compile.init.gradle.kts` admits this exact Desktop2
request or `:calf-ui:compileTestKotlinIosSimulatorArm64`. It uses the compiler's
public exact source collection and, for native only, its public commonSources.
Gradle9.7.1 CLI filters are inspected separately from configured includePatterns.
Ordinary/full source sets, dependencies, production compilation, public binaries
and all shared CI policies/routing remain unchanged.

Native test compilation contains the four new iOS files plus unchanged
`internal/NativeUiApplicationHost.kt` and `internal/NativeObjectIdentity.kt`.
Its receipt is `build/ci-verification/adaptive-controls-focused-compilation.json`.
A KLIB compiler exit is **zero Apple links or native test executions**.

Run the seven **new lexical/tooling** controls with:

```sh
python3 -m unittest discover -s scripts/ci -p test_adaptive_controls_native_matrix_source.py -v
```

They protect matrix/ownership scope and the byte-identical first-eight accepted
Liquid prefix. They do not prove compilation, interactions, rendering or any
native/platform result. Local logs/XML/maps belong to the lead's additive evidence
packet; fresh native results are still required before #133/#138 closure.

## Acceptance boundaries

- Reuse applicable unchanged accepted bodies without replay; new public branch
  matrices and the changed Cupertino thumb implementation need their own results.
- This branch neither changes GitHub nor dispatches, publishes, releases, deploys,
  rewrites main/history, removes original metadata, changes action policy, nor
  lowers any native, consumer, API/ABI, dependency, legal, security/readiness gate.
- #133 can be considered only after both actual host matrices **and** negative
  cases pass with exact fresh application/XML/custody/cleanup evidence; preserve
  its original numeric-domain dependencies.
- #138 requires both actual customization host rows, the owning common Desktop
  regression and production/test compilation; reuse older relevant unchanged
  accepted tests only with explicit source comparison, never call them fresh.
- #129 remains partial regardless of these two fallback methods.
