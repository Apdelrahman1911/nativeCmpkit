# Damped drag / interactive shader lifecycle — six new library scenarios

This related #142/UI-042 and #162/UI-041 patch preserves the original eight
`DragAnimationAndHighlightTest` methods. Their historical actual UIKit evidence
is run `40522929974`, attempt 2, source
`202059090bbbf896d07d38a3441cf21c8888c63b`: the owning subset passed 8/8 within
the full 121/121 execution. Reuse unchanged accepted observations; do not rerun
those eight as if they were new evidence.
Their byte-identical bodies and supporting historical observations do not turn
into passes against changed production boundaries: the six new affected
scenarios still require actual execution at this patch's frozen source.

## New scenarios and source ownership

All sources below are library `calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/`
inputs. No sample application, replacement shader, stubbed animation or ignored
test supplies these results.

| Class | Exact method | Important boundary |
| --- | --- | --- |
| `utils.DampedDragLifecycleRegressionTest` | `cancellationFromActualStartAndStopCallbacksCannotRecreateFeedbackAndNextGestureRecovers` | Owner cancels inside real start/stop callbacks; no later feedback jobs/business completion; next complete gesture recovers. |
| Same | `removingAnActiveActualModifierLeavesNoReleaseWorkInTheCallerScopeAndRangeReplacementRecovers` | Real attached modifier removal, injector reset plus actual scene cancellation, external caller scope/sibling preservation, replacement range -2..2. |
| Same | `thousandSustainedUpdatesTraceActualJobTreesAcrossFramesAndRepressWithoutCancellingSiblingWork` | 1,000 distinct updates over 50 controlled frames, release/repress, actual child Job identities/counts and finite value/velocity. |
| `utils.InteractiveHighlightResourceLifecycleTest` | `disposingAPressedRetainedModifierClosesItsRealBuilderStopsPixelsAndNeverRestartsItsJobs` | Two independent real Skia builders, native closed state, actual captured pixels, disposal while pressed and re-input through retained nodes. |
| Same | `removingAnActualPressedHighlightClosesItsBuilderAndNewCompositionUsesANewOwnedResource` | Actual pressed-node removal, native builder closure, same surviving caller/sibling, fresh real builder identity after recreation. |
| `button.LiquidButtonConstructionTraceTest` | `hundredActualPublicButtonsKeepOptionalShaderConstructionAtZeroThroughInputDisableAndRecreation` | Eager composition of 100 **public** `LiquidGlassButton` instances, actual first/last-button scrolling/input, held-button disable, zero optional highlight shaders, two generations/200 terminal disposals. |

The fully qualified class prefix is `com.mohamedrejeb.calf.ui.`. The original
application, Worker, runtime/source receipts, exact selected XML, failure
propagation and independent owned cleanup remain required for native execution.
`requireUiDragShaderApplication()` requires the original active, visible owned
`UIApplication` window before each scenario. Compose scene injection is actual
library input but is **not** a claim of physical UIKit input delivery.

`UiDragShaderTestHost.kt` provides the original application guard, a real
composition dispatcher/frame clock with an independently caller-owned Job,
actual child-job enumeration, test-owned screenshot closure and cleanup which
retains both primary and close/cancel failures. Tests cancel their own independent
scopes, never claim node removal automatically owns the caller's scope.

## Focused compiler command

The lead grants the serial local heavy slot before execution. Require at least
8 GiB free, offline cached dependencies, no other local heavy build, and this
exact compile-only request:

```sh
./gradlew --offline --no-daemon --console=plain \
  --no-configuration-cache --max-workers=1 \
  '-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8' \
  -Pkotlin.compiler.execution.strategy=in-process \
  -Pkotlin.native.jvmArgs=-Xmx2048m \
  --init-script scripts/ci/ui_drag_shader_compile.init.gradle.kts \
  :calf-ui:compileTestKotlinIosSimulatorArm64
```

The isolated init admits exactly seven ordinary repository test files: the three
classes, `UiDragShaderTestHost.kt`, and unchanged `PointerCancellation.kt`,
`NativeUiApplicationHost.kt`, `NativeObjectIdentity.kt`. Its public KGP source
collection is checked before compilation with common sources empty. Normal
production compilation and dependencies remain; no production filtering or
default source-set modification. The precompiler JSON is source admission only,
not a successful compiler receipt or native execution.

Native selection/registration is **pending lead integration**. Do not invent a
workflow focus or bypass the original transport. Only the six new methods above
should execute after the lead freezes/registers that finite selection. Never use
the compile-only init for native linking, a full suite or publishing.

## Evidence limits / remaining original acceptance

- Compilation is not runtime, shader capability, memory/leak, graphics or API/ABI
  acceptance. Unsupported real shader construction is a failing resource test,
  not a fallback-only success.
- Actual child-job traces use a controlled Compose frame clock. Monotonic elapsed
  nanoseconds and observed native helper identities are reported without invented
  allocation/frame budgets. They are not Instruments or hardware profiling.
- The public-button trace observes the real optional `InteractiveHighlight`
  construction/resource path, not all Backdrop blur/lens effects or GPU overdraw.
- #142 still needs hardware frame-time/allocation tracing and relevant native
  clock/cancellation checks. The older monotonic implementation is unchanged;
  these scenarios do not simulate changing the OS wall clock.
- #162 still needs supported older/current Apple hardware GPU/frame/overdraw,
  Instruments allocation tracing, reduced motion/transparency and the existing
  dark/scrolling/fallback-effect criteria. No new unrelated closure gate is added.
- Retain dependency, consumer, public API/ABI, legal, security and release gates.
  Neither issue is closed by the six new sources or a KLIB-only success.

The focused production/test KLIB compiler now passes; native execution remains
pending. See the [source/actual-result packet](../development/ui-drag-shader-20261104/README.md)
for exactly what was executed and which original controls were reused.
