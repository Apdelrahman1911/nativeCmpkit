# Independent passive observer003 review

**Reviewer:** `/root/metadata_archive`, 2026-10-25.
**Result:** **GREEN, source/offline only**, for the exact frozen003 diagnostic
correction. This is not an actual003 runtime observation, a fixture005 launch
authorization, production dependency trust, BUILD-007 closure or a release gate.

This is a separate additive record. The [earlier reviewer report](dependency-tooling-independent.md)
and [JSON](dependency-tooling-independent.json) remain sealed at SHA256
`48efb14422b5659a861170bd2ce7f6612954f88e961f69b0d1bd335571874260`
and `c8edade1ce1c9f7a41542aace597909afdfede8ef022368bfc1a7105f7419199`,
respectively. Their historical statement that003 had not yet been reviewed
remains correct for that checkpoint; it is not retroactively edited. The lead's
separate Wasm tooling runtime is outside this review.

Exact commands, outputs, AST bindings, modeled results and validation diagnostics
are in the [machine-readable companion](dependency-observer003-independent.json).

## Inputs and preservation

[Observer003 checkpoint](../build/dependency-fixtures/runtime-witness003/checkpoint.json)
SHA256: `94b5ed8a9aab74a9fa0801e498a75376f915558e58d09c420895094602de2959`.
[Archive manifest](../build/dependency-fixtures/runtime-witness003/archive-manifest.json)
SHA256: `66bc8c3ab665592f3159a4e50dd016cac270fcf81c0deae7ef1f98a4f8caecd0`.
The helper now pins independently reviewed core006 checkpoint
`42df397c9ddc0a7c6419cb1d109a680e2204dba54e78250b3a4e6b8f49fd6f46`.

| Frozen observer input | SHA256 |
| --- | --- |
| `runtime_witness.py` | `66ae5fe309c1d6550c2c4765f2693f0c6b171ce02712d9622b2eff482a288134` |
| `test_runtime_witness.py` | `fe2228aa8b610d49247263810116a53920f90aff8a094fad824bc8afa15f25b8` |
| `runtime-witness.md` | `fd693730b4b09b0b91aa6aefb676337f3ee898ca92d63cc1cc8b560c717dd501` |

All eight003 archive entries, the three live/frozen observer copies and six
live/frozen006 inputs matched. Prior001/002 archives and all73 actual004 archive
bindings were checked. **117 distinct bound paths were unchanged** during the
read-only source/archive check, including the sealed prior review and the
author's completed tooling-scope receipt that binds it. Those are data checks,
not fresh Gradle/JVM executions.

The [original004 evidence](../build/dependency-fixtures/fixture004/archive-verification.json)
still reports suite/witness failure or incompleteness: three installed-distribution
clients observed, **zero external daemon observations**, original missing-host
classifier `unverified`. The old missing-daemon cause remains **unknown**, not
reconstructed from new counters or synthetic examples. Core006's additive
post-hoc classifier interpretation does not rewrite that original outcome.

## Implementation-level changes

Line numbers below refer to the exact003 `scripts/dependencies/runtime_witness.py`
bytes above, also available in the [frozen source](../build/dependency-fixtures/runtime-witness003/frozen-inputs/scripts/dependencies/runtime_witness.py).

| Lines / symbols | Independently inspected behavior |
| --- | --- |
| 43–76: enum constants | Six fixed stages,85 explicit reason strings, cap1024. All73 literal `require`/`WitnessError` codes belong to the enum. Counts are poll events, not unique PIDs or attach attempts. |
| 88–101: `failure_reason` | Only exact `WitnessError` with one exact string enum argument retains that code. Unknown bodies, subclasses and other exception types map to fixed categories without formatting raw data. |
| 104–113: `record_validation_reason` | Validate stage before mutation; collapse unknown code keys; increment a bounded integer and set a saturation flag on overflow. No acceptance or observation flag is changed. |
| 32,144–151,537–557,642–645 | Pin exact core006 instead of005, update corresponding report names and add per-case diagnostics. The preflight and final six-file checks remain required. |
| 565–620: case loop | Preserve context, client, child-enumeration, candidate, daemon and binding error categories. Rejected candidates still `continue` before attachment. Empty child lists and no eligible candidates are separately counted. |
| 647–660,679–680 | Preserve completion gates; emit fixed failure categories in finalization/CLI catches. Successful cases discard only the transient last-reason field, not prior counters. |

The independently compared **26 old002 function/class ASTs are unchanged**,
including suite/process ownership, complete argv parsing, environment/property
checks, pidfd before/after checks, bounded diagnostic subprocess handling,
runtime binding and fixture-result matching. Only `checkpoint_files`, `witness`
and `main` changed; only the two diagnostic helpers were added. All five final
completion/attempt-count assignment ASTs are identical to002.

### Execution flow and retained safety gates

1. **521–557:** validate bounded host/time/paths, destination outside Git,
   exact006/observer input hashes and the owned sibling suite before observations.
2. **561–590:** for each fixed case, wait for its launch receipt, validate marker
   and client identity, then make at most one client diagnostic attempt.
3. **591–614:** enumerate only the verified client's children. Reject/record
   invalid candidates without attachment. More than one eligible daemon remains
   ambiguous; exactly one may make one diagnostic attempt. Attempt flags still
   precede the diagnostic, so failures are not retried.
4. **615–653:** bind observations to the exact runtime receipt, refresh on final
   fixture output, recheck source hashes and require six client/daemon/binding
   triples plus the exact selected fixture results and no stop reason.
5. **654–665:** retain diagnostics and all cases, record a fixed stop reason on
   failure/interruption and exclusively write the final report.

## Executable offline evidence

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=docs/development/evidence/build/dependency-fixtures/checkpoint006/tool-inputs/scripts/dependencies \
python3 -B -m unittest discover \
  -s docs/development/evidence/build/dependency-fixtures/runtime-witness003/frozen-inputs/scripts/dependencies \
  -p test_runtime_witness.py -v
```

Inspected result: **108 tests,0 failures/errors,0.273s,exit0**. All91 existing
test method ASTs are unchanged. The17 authored additions comprise seven
diagnostic tests, nine modeled outer-loop tests and one CLI test. Four existing
tiny, task-owned **Python** pipe children were actually started/reaped for bounded
capture/timeout/nonzero tests. All `/proc`, JVM identity and attachment boundaries
are synthetic/mocked; no Gradle, Java, jcmd or network ran.

The owner003 logs for108 observer tests and164 unchanged-core regression tests
match their checkpoint hashes/counts. This additive reviewer did not rerun the
core164 suite: its independent pass is already preserved in the sealed report.

### Additional independent checks

- **All85 exact enum errors** retain their code; **16 poison/invalid exception
  cases** map correctly. Poison `__str__`/`__repr__` and command objects raise if
  formatted; none were formatted. Exact-string and exact-exception-type guards
  prevent subclasses from bypassing the enum check.
- **510 stage/reason pairs**, each incremented1026 times, saturate at1024.
  Unknown dynamic keys collapse to one bucket; **eight invalid-stage cases**
  reject without mutation. Client/daemon/runtime flags remain unchanged. Six
  copies of the saturated counter test state serialize to127827 bytes versus
  the1MiB receipt input limit; this is not an arbitrary whole-report size proof.
- **17 independently modeled outer-loop scenarios** passed: the earlier11
  missing/failure/drift/timeout/interruption controls plus context failure,
  ambiguity, poison diagnostic error, reject-then-valid, saturated rejection and
  malformed runtime receipt. Only the complete control and later-valid control
  complete; all15 negatives stay incomplete. Every saved report matches return
  data, every role is attempted at most once and no scenario exceeds12 mocked
  observations.
- The later-valid control retains its earlier rejection counts while requiring
  all12 synthetic observations and matching bindings. A saturated rejection map
  cannot fabricate an absent daemon observation. This directly checks that
  counters are diagnostic history rather than success conditions.

The additional source/diagnostic commands use Python audit hooks rejecting
process/network/proc operations; the outer-loop harness writes only synthetic
temporary files and mocks process boundaries. They launch no child processes.

## Recipe and remaining limits

The [future paired recipe](../../../../scripts/dependencies/runtime-witness.md)
differs from002 only by four destination004-to005 strings. Its exact extracted
SHA256, without an added terminal newline, is
`7a43eab740c3ac0883449ab661dc82e4ddd4063e43e6546847ed281a217edadc`.
The owner recorded `bash -n` exit0. This reviewer compared bytes but did not rerun
that syntax check or execute the recipe. A fresh lead-scheduled GO remains
required; no source/runtime acquisition is authorized here.

- Actual003 client and daemon shapes remain unobserved. Actual004 establishes
  the unchanged client path only; its daemon cause is still unknown.
- Counters are not a complete event log: absent launch/runtime files, false
  runtime equality and final receipt-refresh handling may leave no counter.
  The modeled wrong-PID and missing-runtime cases correctly remain incomplete
  with empty diagnostic maps. Absence of counters is not proof no guard failed.
- Saturation loses exact counts; no ordering or candidate PID is retained.
  This intentional boundedness prevents reconstructing a full causal trace.
- Numeric-PID jcmd attachment is not an atomic pidfd-addressed operation or
  an OS sandbox. The unchanged pre/post checks and scoped cleanup retain their
  existing limitations, including potential attach-listener side effects.
- Wrapper/compiler/Native/plugin cache use, actual production dependency trust,
  ordinary-build policy, security/license review, library/device/browser/native
  tests and all release gates remain separate.

The original164 findings, source/policy, existing archives and sealed reviewer
files were not edited. No new baseline finding or finding closure is claimed.
The JSON retains reviewer-only orchestration/OS-argument-limit errors and an
initial validator code-block-count assumption failure; only corrected executed
checks receive PASS. No source/evidence was changed to make them pass.

Final document/hash consistency passed with eight local links,126 before/after
unchanged paths and all false runtime/trust/release/launch flags preserved. The
same command is retained in JSON and rechecked after saving the final record.
