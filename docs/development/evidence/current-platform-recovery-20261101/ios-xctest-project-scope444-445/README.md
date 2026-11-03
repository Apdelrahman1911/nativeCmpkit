# Shared XCTest project-scope recovery — 2026-11-03

## Confirmed new tooling defect, not the earlier native startup cause

The runner extraction in `2ef28eaa` moved `_start_runner` away from
`_prepare_project`, but its compiler command still referenced `project_root`,
which existed only as the latter method's local variable. The extracted runner
therefore refused **before Swift/Popen**, after preparing its loopback server.
This is not evidence of the cause of the earlier native runner-readiness failure
at `510f2531`; that revision had successfully compiled Swift.

The first private regression incorrectly mocked `_serve` without providing its
required server, and refused at `AttributeError` before the suspected load. That
run is unqualified and preserved. The corrected fresh control uses genuine owned
loopback tooling and a simulated compiler boundary. **One method/two route
subtests** reports the exact `NameError` for both ordinary library-input and
standalone startup, with unchanged1,256 inputs and zero compiler/native calls.

## One shared owning fix

`scripts/ci/native_ui_input.py::_start_runner` now derives the same exclusive
`self.scratch / "project"` path in its own frame. **Exactly one driver line**
changes; credential, compiler, input, library-app, native and cleanup predicates
remain intact. `ios_modal_worker_source_projection.py::XCTEST_PROJECT_SCOPE`
adds one complete-source/fragment binding with unique inverse/forward checks.
The six23-fragment Worker manifest, fixture-reader and AWT manifests/old pins
remain unchanged. Inverse preimage idempotence does not weaken current admission.
The initial binding-population script had a pre-execution `SyntaxError`; its
refusal remains separate from the actual regression and corrected source review.

Only the **failed1 +new1** controls execute: **2/2 once**, wrapper1.353258s,
1,257 held inputs, zero Swift/UIKit/XCTest/compiler/native executions. The
qualified red method body is byte-identical in the green recovery; only its
repository-root declaration is made portable. The27 passive source/results
checks preserve all four Kotlin compiler sources, Swift, production/public APIs,
live selectors/workflow and prior accepted native populations. No compiler or
accepted test is replayed.

## Preserve the cancelled request and keep memory running

[41574865107](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41574865107)
at `5e0dc71311035d074725fdd1e67f0ea1756de12b` is **CANCELLED**, not failed or
passed native verification. After the fresh source reproduction, only this
knowingly doomed queued startup request was cancelled. Originals prove:

- Source tooling **2,525 methods /124.961s**, all reported tooling groups green.
- Startup job **runner_id0 /zero steps**, cancelled before Apple allocation.
- **Zero Swift/Gradle/native methods/XML/artifacts** for that startup request.
- All1,256 predispatch frozen inputs match their own complete Git blobs.
  They are neither actual platform inputs nor the later local1,257 population.
- Originals acquired/member-verified/reviewed once; raw logs stay private.

[41574895107](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41574895107)
memory3 remains **untouched at5e0dc713**. Its exact four Kotlin/production inputs
are unchanged by this separate input-driver correction. Its own original
runtime/input/XML evidence must be reviewed at its actual Git revision; never
substitute later local hashes or claim a native result before terminal review.

`local/inputs.json` is one copy of the identical before/after maps, whose separate
original captures remain private. `ARCHIVE.json` binds the public evidence, not
the later storage commit.

## Next and restrictions

Freeze/push development only and request **only corrected startup-only** after
fresh capacity reconciliation. Real iPhone7 input requires accepted actual
startup; iPad7 follows later. No replay of accepted modal9, repeated-disposal or
state-replacement/native subsets. Original modal issue criteria remain open.

No issue comment/closure: last verified98closed/74open/172;22implemented/
41partial/96verified/five unresolved. SOLO, serial local/8GiB reserve/max2
combined hosted reservations **including queued**. Actions all/no mandatory SHA
pinning/read-only verification. Every publishing/Pages/main/history/legal/
security/consumer/API–ABI/release-readiness gate remains; no publication.
