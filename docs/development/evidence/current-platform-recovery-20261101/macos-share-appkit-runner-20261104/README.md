# macOS share AppKit runner — source-only qualification, 2026-11-04

Parent source: `090870fbee2c0988e3a979f2a1e3f222973de576` (resource lifecycle604).
Isolated branch: `development/batch-share-appkit-runner-20261104`.
Only a new native controller, its new controls and scoped documentation/evidence
are added. No existing production/harness/Kotlin/native/Gradle/shared-selector/
workflow/policy/API/dependency files were edited. The lead's separate workflow
and selector integration is **not** this branch's source custody.

## Actual local executions and retained failure

| Execution | Exact outcome | Complete source custody |
|---|---|---|
| NEW32 source/mock controls, once | 27 pass / five fail; unittest0.122s; wrapper0.6355627779848874s / exit1 | 1,342 before/after; zero changed inputs |
| Only FAILED5 + owning changed-freshness3, once | 8/8 pass; unittest0.073s; wrapper0.6443595390301198s / exit0 | 1,342 before/after; zero changed inputs |
| Fixed read-only CLI `--plan`, once | exit0 / empty stderr / 0.4953798248898238s | Same final 1,342 inputs, unchanged |

All **32 unique new methods** are qualified across **40 method invocations**.
The other 24 accepted methods were not replayed; no existing accepted suites or
native bodies were executed. The complete first red result and original stderr
are retained privately and hash-indexed here; they are not rewritten as green.

The first five failures came from strict nanosecond mtime/start admission in the
**new** artifact/report controls. A new clock-only filesystem diagnostic observed
a freshly written ordinary file's mtime **595,676ns before** the surrounding
`time.time_ns` start reading. The changed controller now uses the owning library
runner's existing two-second filesystem/wall-clock envelope **only alongside**
exclusive target/actual-PID absence, ordinary-file/checksum/source/toolchain and
before/after custody. Changed negative controls explicitly predate that envelope;
the failed five plus affected positive/negative owners recover without waiving a
stale target, reused PID, cached XML or failed native process.

Final held input aggregate:
`fcf9d72c0317a36c49029d494d8211f6c7782d8c25864b0d19dfbcedd2174959`.
First red aggregate remains in its original result/maps, not relabelled current.
Original private logs are indexed by `original-file-index.json`; uploaded source
maps/results contain only repository-relative source hashes and fixed context.

## New controller boundary

- Real macOS arm64 and exact GUI opt-in; immutable clean Git; complete library
  and native maps; pinned Rust/Cargo1.98.0 / actual Apple compiler host; effective
  toolchain executable hashes and before/after macOS/Xcode/SDK context.
- One fixed `--locked --no-run` compile into exclusive target; exact one-artifact
  package/source/feature/profile origin; ordinary arm64 Mach-O **MH_EXECUTE**.
- Execute that exact binary with **zero selector arguments**, default NEW8 only.
  Cooperative native waits are covered by external time/disk/log monitoring,
  owned-group TERM/KILL and bounded reap. Surviving descendants remain red even
  when the leader exits zero; cleanup refusal retains its own evidence.
- Preserve complete old report state; actual-PID collision refuses without
  copying/deleting baseline XML. Fresh exact reached XML is checksum-bound and
  copied to `fresh-reports` even if the native case is red. Unknown/aliased/
  skipped/missing/foreign/duplicate cases and bad cleanup remain red.
- Console + XML + zero-count/native-cleanup agreement is required independently
  of the unchanged **source-bound** failed-control guard. The guard is not a
  separately exported/read raw flag; receipts explicitly say so.
- Public artifact boundary: only sanitized top-level JSON and exact reached
  `fresh-reports/TEST-*.xml`; private Cargo/native logs and executable are hashed,
  not uploaded. No environment/job/path dump, package or publication command.

## Unchanged closure and verification limitations

This assignment ran **zero Cargo compilation/linking, native/AppKit/JNI/Kotlin
tests or GUI observations**, and no stress/visibility/service delivery/
Instruments/leaks/ASan. Prior604 compiler results are historical, not rerun here.
Mock/source controls are never native evidence; code container/header matching is
not ABI/consumer/security certification. The control-gated eight retain actual
native objects but do not establish visible presentation or actual Mail recipient
delivery. #84/#85/#150 therefore remain open, with all original closure gates.

No GitHub mutation, CI dispatch, push, issue closure or release/package/
deployment/Pages publication was performed by this agent. Lead alone integrates,
captures actual owning workflow/source custody, dispatches within fresh capacity,
reviews original results and closes only the fully verified original subset.
See [runner procedure](../../../../testing/macos-share-appkit-runner.md).
