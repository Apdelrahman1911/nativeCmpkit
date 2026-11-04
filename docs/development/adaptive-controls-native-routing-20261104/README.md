# Adaptive related native batch: finite routing proposal

Base implementation/test commit: `b542da6509a15a1583fcc24fb460797383e5a55f`.
Date: 2026-11-04. Issues: **#133 / #138 / partial #129**.

This follow-up adds only three uniquely owned tooling files and this evidence
packet. It does not edit production, Kotlin tests, the earlier compiler-only
init, shared runner, native transport, matrix, workflow, policy or old evidence.

## Important verification actually executed

```sh
python3 -m unittest discover -s scripts/ci \
  -p test_ios_adaptive_controls_native_focus.py -v
```

**Seven NEW Python methods pass once**, 0.020 s unittest / 0.110361348 s wrapper,
exit 0. Fifteen owning, shared and native inputs match before/after hashes.
`new-routing-controls.log`, `control-run.json` and `inputs.json` are originals.

The controls cover exact disjoint four-method selections; missing/duplicate/
mixed/foreign/full/compiler/publish requests; both enabled branch declarations
and all six source inputs; symlink refusal; malformed/unavailable/wrong iOS
runtime; exact application-task/target XML identities; failed/skipped/N/A/
malformed outcomes; actual Apple host requirements; and the native init's exact
selectors/source collection and zero-execution receipt scope.

These are **synthetic selection/outcome and lexical controls**, not KGP report
production, Gradle configuration, compiler, Apple linking, UIKit rendering or
native execution. ZERO new Gradle/compiler/link/native tests were run. The
native-only init has not yet been loaded by Gradle; its ordinary source API is
the same inspected API used by the separate successful compiler-only packet.

The original Desktop RED2/GREEN2 and successful focused iOS KLIB compiler are
preserved in `../adaptive-controls-20261104/`; their unchanged sources/results
are reused, not replayed or called fresh here.

## Lead integration contract

`scripts/ci/ios_adaptive_controls_native_focus.py` exports:

- `FOCUSES`: `ui-native-adaptive-pre26`, `ui-native-adaptive-ios26plus`.
- `focus_spec(focus)`: fresh ordinary registry spec with three groups and **four
  selected methods**. Both branches' complete declarations remain in every group.
- `selectors`, `test_filter`, `native_request`, `identities`: exact Gradle/KGP
  selectors and existing `iosSimulatorArm64ApplicationTest` XML identities.
- `validate_sources(root, test_sources=None)`: all six ordinary authored Kotlin
  inputs, actual branch wrappers and positive public-control call admission.
- `validate_runtime(simulator, focus)`: actual recorded Booted UDID/iOS runtime
  and `<26` or `>=26` matching. Native methods independently read UIDevice on
  owned application Main; runtime absence or mismatch is failure, never N/A.
- `outcomes(cases, system, focus)`: four exact passed native identities on Apple,
  no skipped/duplicate/foreign-target/other-branch substitution. This consumes
  parsed cases; the original runner still owns report freshness/task markers,
  protocol agreement and complete application runtime/custody/cleanup acceptance.

The lead must register the two finite specs in the existing shared runner,
select only `calf-ui` / iOS / the genuine application task, add the distinct
native init and explicit `-PnativecmpkitAdaptiveControlsFocus=<focus>`, and wire
source/runtime/outcome checks into the existing pipeline. Qualify those **new**
integration controls before hosted work. Do not patch globals, bypass the
original transport, fabricate XML, or use direct/simctl-spawn/sample test hosts.

The existing transport currently refuses these unregistered selections. This
standalone helper does not authorize or execute native tests by itself.

## Distinct native-only init and safe unchanged prerequisite reuse

`scripts/ci/ios_adaptive_controls_native.init.gradle.kts` accepts only the exact
four application method selectors for its explicit focus, on real Darwin Arm64
with an explicit UDID. No implicit/full task, compiler-only invocation, ordinary
native task, second branch, sample or publish task is permitted.

Its six selected compiler inputs are exactly the already compiled adaptive
sources and original owned host/identity helpers. Both branches use the same
KLIB source collection: the focus property is deliberately **not** a compiler
input that would force an unnecessary rebuild. Ordinary source sets, production,
dependencies, test binary/entry, original test task and transport remain intact.

Before the owning native task it records a fresh source/selection admission at:

```text
build/ci-verification/adaptive-controls-native-source-admission.json
```

This receipt explicitly attests **0 compiler executions, 0 Apple links, 0 native
tests**. It may coexist with genuinely UP-TO-DATE compiler/link prerequisites;
it is not a compiler/link or result receipt. Original fresh native XML and
runtime/protocol/source/cleanup agreement, plus applicable compiler evidence,
are still required. The earlier `adaptive_controls_compile.init.gradle.kts`
stays byte-identical and does not admit an iOS application/native task.

## Remaining issue and operational boundaries

- #133: both real OS matrices and both negative-step methods still need fresh
  native execution; original numeric-domain dependencies remain unchanged.
- #138: both real native customization matrices still need execution. The
  Desktop thumb-color fix is proven independently, not an iOS substitute.
- #129: Material fallback is only a subset. Populated native26+ toolbar,
  genuine safe-area/keyboard/orientation and native bottom-bar integration remain.
- No GitHub mutation, dispatch, issue closure, publishing, release/deployment,
  main/history rewrite or new delegation occurred. Lead alone integrates and
  dispatches; fresh capacity/max-two-hosted-heavy and serial-local/8 GiB remain.
- All consumer/API-ABI/dependency/legal/security/readiness and publication gates
  stay in force. No release readiness or verified-platform coverage is claimed.
