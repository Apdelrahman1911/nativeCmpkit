# UI-018 same-operation cancellation gap — batch447, 2026-11-03

## Original criterion and implementation

Issue **#31/UI-018 C2** requires cancelling a show/hide waiter, completing its
native animation, then **repeating the same operation** with correct await timing.
The previously accepted cancelled-show→hide and cancelled-hide→show tests cover
opposite transitions; they are not substituted for this missing same-operation
case. The earlier criteria mapping is historical and is corrected here.

The new library-level `NativeSheetCancellationRepeatTest` has exactly two cases:

1. Cancel native **show**, observe its own completion, verify visible show is an
   immediate no-op, hide fully, then require a second real show to remain pending
   while UIKit is presenting and complete only in the matching visible state.
2. Cancel native **hide**, observe its own completion, verify hidden hide is an
   immediate no-op, show fully, then require a second real hide to remain pending
   while UIKit is dismissing and complete only after the presenter is detached.

Both retain exact native controller identity, independent cancelled/repeated
jobs, current/target values, no user-dismiss callback and owning state/manager/
scope cleanup. Native completion predicates—not sleeps or elapsed thresholds—
qualify await ordering. They use the genuine library application/Main bridge and
public state operations; no sample, native callback injection or fake animation.
No production, public API, dependency or original native test bytes changed.

`ios-sheet-cancellation-repeat` reserves one Arm64 `macos-26` iPhone and exactly
two authored selectors. Its three-source init script compiles only the new class,
unchanged application host and native identity helper. All original runtime,
Worker, fresh nonzero XML, source/dependency and owned cleanup gates remain.

## Important local results

- First **NEW4 + affected1**: 4 pass/1 fail, zero errors; unittest0.097s,
  wrapper0.427446s. The failure was the control's missing public KGP
  `iosSimulatorArm64ApplicationTest.` classname decoration, before later checks.
- Only that failed control then passes **1/1**; unittest0.156s,
  wrapper0.448783s. **Five unique controls/six invocations**; accepted four are
  not replayed. The exact two-method selection, wrong-host/module/disabled-source
  refusals and complete three-path/seven-fragment history are qualified.
- Narrow actual test compiler **exit0/39.01s**, **1,262 inputs held**, production
  UP-TO-DATE, actual exact three-source receipt. Four cross-compilation/disabled
  ordinary-target configuration warnings remain. **ZERO Apple link/native tests**.
- Eleven precompiler and eleven results/source passive checks hold. Original
  six23 Worker inverse/pins remain immutable; the additive exact inverse cannot
  admit historical or mutated bytes as current native source.
- Actionlint exit0; the output/source hash was recorded after the observed tool
  command, not claimed as a pre-execution freeze. An earlier local PATH lookup
  missed this already-qualified binary; its explicit path was used.
- First binding-population nonunique Desktop anchor was refused before manifest
  writing/imports/tests/compiler. It remains recorded; recovery uses the exact
  unique two-line site and does not normalize or relax admission.

Reproduction (compiler, not tests):

```sh
./gradlew :calf-ui:compileTestKotlinIosSimulatorArm64 \
  --init-script scripts/ci/ios_sheet_repeat_compile.init.gradle.kts \
  --offline --no-daemon --no-configuration-cache --max-workers=2 --no-parallel \
  --console=plain '-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8' \
  -Pkotlin.compiler.execution.strategy=in-process -Pkotlin.native.jvmArgs=-Xmx2048m
```

## Current scope

**#31 remains open.** These two native methods are still unexecuted; the current
memory3 request41574895107 remains at its own **5e0dc713/1,256** frozen inputs,
and startup41575956373 at **edc8c44d/1,257**. Neither uses this later local1,262
population. Do not replay accepted modal/Worker/lifecycle selections, substitute
current maps for actual originals, or dispatch beyond two hosted reservations
including queued. Genuine startup acceptance precedes the independent interaction
batch. No new issue comment/closure or release/package/deployment publication.
Physical/minimum-platform/heap profiling/consumer/API–ABI/security/legal/release
requirements remain separate and unverified. Work is solo on development only.
