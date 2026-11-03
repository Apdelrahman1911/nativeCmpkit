# Grouped modal CI455 and owning fixture recovery456 — 2026-11-03

## Actual original, not a native failure

[Run41581612628](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41581612628)
at `bf5b30b090635309c5401c9ee67a6eb4d242b96c` is **FAILED**. Tooling reports
2,542 methods: 2,541 passes and one error in
`SheetCancellationRepeatControls.test_seven_exact_additive_fragments_preserve_every_old_worker_pin_and_refuse_mutation`.
It stops at `test_ios_sheet_cancellation_repeat.py:107` before platform selection.
**ZERO library Gradle, Apple, Swift, native executions, XML or artifacts.**
All seven downstream jobs were skipped. The eight original log members were
acquired/reviewed once; all1,266 own-Git frozen inputs were checked. This is not
actual platform custody. Its hosted reservation is freed, not still pending.
See [original review](original-tooling-review.json).

## Root cause and minimal repair

The older SheetRepeat reader received the newer WorkerCompletion postimage.
It correctly refused those bytes. The fixture now first admits and inverts the
exact current WorkerCompletion stage, then passes that exact historical stage to
the existing SheetRepeat reader. Its forward round-trip compares against that
stage, not the newer current source. Negative mutations remain separately required
at **both** admission layers. Neither a generic hash refresh nor a looser reader
is used.

Only the failed test method/import and a NEW three-method source-control file
change. All live helpers, native bodies, workflows, dependencies, APIs, old source
pins and manifests remain unchanged. Every other original test method AST is held.

## Important tests and source/results review

Only **failed1+NEW3** execute: **4/4 pass**, unittest0.106s,
wrapper0.247427374s. The NEW controls check exact stage composition at all three
bindings, refusal **before** historical reader invocation, and the real fixture's
inverse/forward/negative-control wiring. An `AssertionError` barrier and zero reader
calls prevent historical failure from impersonating current admission failure.

Fifteen passive source/results checks accept1,267 held current inputs: precisely
one old input changes and one control file is added. The earlier43.01s five-source
KLIB is reused only on unchanged compiled Kotlin/dependency/compiler bytes.
**ZERO compiler/native invocations**, accepted-control replays or original
redownloads. See [controls](controls.json), [actual log](failed1-NEW3.log) and
[source/results review](source-results-review.json).

## Next and issue/release scope

Commit/push this owning CI-only repair on development, freeze its exact revision,
and request the same **five missing native cases once** after fresh capacity.
Do not redispatch the old failed revision or replay accepted native selections.
The earlier three-green-XML memory run still lacks mandatory Worker completion;
its native lifecycle/root cause remains unverified. Real interactive iPhone7/iPad7
remain required after applicable shared transport qualification.

#28/#30/#31/#125/#126 remain open; no issue status promotion, comment or closure.
SOLO; serial local heavy/8GiB reserve; maximum two combined hosted-heavy
reservations **including queued**; read-only Actions/all/no mandatory SHA pinning.
All publishing/Pages/main/history/legal/security/consumer/API–ABI/readiness gates
remain. No releases, packages or deployments.
