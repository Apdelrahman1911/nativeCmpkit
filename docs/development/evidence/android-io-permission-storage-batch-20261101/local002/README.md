# Android IO / permission / storage — compiler recovery and finite CI batching

**ZERO new native executions.** This receipt archives existing compiler and
source-only results; preparing it ran no builds, SDK/device commands, accepted
test replays or Git/GitHub operations. APK identity/manifest inspection is owned
by a separate receipt; no APK, key, signing material or raw build log is copied.

## Actual owning compiler recovery

The five-Kotlin-file repair preserves all original native methods and refusal/
cleanup assertions. It uses nullable public `permissionToOp` with null refusal,
throwing `Os.remove` with the original descriptor/lstat/ENOENT checks, the existing
permissions opt-in, equivalent forbidden-membership assertions and explicit
`Any?` cursor-array types. No runtime AppOps mapping is inferred.

| Existing serial recovery command group | Exit | Seconds | Scope |
| --- | ---: | ---: | --- |
| Six storage flavors | 0 | 67.02 | All six assembly tasks, no installation/tests |
| Permission library reporter once | 0 | 35.01 | Reporter assembly, no native execution |

Both commands held the same **1064 library / 1141 combined** identities before
and after, with reserve 8192 MiB, no parallel Gradle work and at most two workers.
Warnings remain observations, not native failure or clearance. Commands, source
pre/post hashes, raw-log hashes and held input witnesses are recorded in
`compiler-recovery.json` and `input-witnesses.json`.

The earlier storage command **exit1/73.02s** and aggregate reporter command
**exit1/103.02s** remain failed. `retained-compiler-failures.json` preserves all
**eight exact diagnostic messages, repository paths and line/column coordinates**.
The IO reporter completed inside the failed aggregate command; it was not
replayed. The earlier IO/permission helpers and debug/release sample merged
manifests are reused from [local001](../local001/README.md), not freshly rebuilt.
Their packaging review is not Call/picker/denial/media/storage native acceptance.

## Two exact serial hosted batches

| Fixed profile | Original routes | Target executions | Distinct original methods |
| --- | ---: | ---: | ---: |
| `android-io-permission-storage-api35` | 4 | 8 | 8 |
| `android-permission-storage-compatibility` | 8 | 8 | 7 |
| Union | **12** | **16** | **13** |

The union is three IO executions plus thirteen permission/storage executions.
The complete original profile/API/module/focus/task/method mapping is in
`ci-batches-source-plan.json`. The first batch uses API35; compatibility uses
API28/29/30/33/34. No original method is broadened or removed. All original
individual profiles and all 11 complete matrix slots remain available. The
separate Android WebView request-state profile is not selected.

The lead applied 13 uniquely anchored Android fragments and three new scripts,
preserving outside shared-file bytes. Each route still invokes the original
owned-device controller with a fresh output, AVD, private signer and connected
task. Same-checkout Gradle compilation may naturally reuse unchanged outputs;
**no measured speedup or 90-minute hosted runtime fit is claimed**.

A failed route stays red. Later independent routes require certified prior
source identity, graceful owned-emulator exit0/transport removal and matching
helper cleanup. Original bounded XML is archived before another route can
quarantine shared reports. Unknown cleanup, stopped controllers, changed inputs/
workflow, invalid archival or local reclamation failure refuse remaining routes.
Only certified completed `avd`/`android-user` state is reclaimed after archival;
receipts/XML, compilation/dependency caches and foreign paths are not selected.
Missing XML evidence never establishes zero native activity.

Read-only token permissions, existing cache fences, serial local heavy builds,
8 GiB reserve, at most two combined heavy hosted requests and the original
90-minute hosted bound remain. Uploads add bounded JSON/XML only. No publishing,
Pages, main/history, security, consumer, ABI or release-readiness gate is relaxed.

## Source evidence and final input inventory

The original held private CI fixture passed **129/129** source/model methods,
no skips, unittest 13.626s: 13 new models plus 116 existing controls. This is not a
fresh 129-method merged-checkout run. The lead's two affected merged source
methods pass 2/2/0.992s; overlap is not additive coverage. All twelve recorded
real read-only controller-plan commands exit0 and match the exact fixed route
suites/output hashes. Actionlint exits0 with shellcheck/pyflakes disabled;
reader/model/ambiguous-anchor refusals remain recorded in `integration-review.json`.
No result was replayed to prepare this documentation.

The recorded integration snapshot held **1068 library / 1145 combined** inputs.
The final root inventory, based on `19a474cd`, keeps those counts and changes
only two unrelated reviewed Apple source hashes; all owning Android plans and
source projections are unchanged. `library-inputs.json`, `combined-inputs.json`
and `final-freeze.json` bind that final source inventory, not the earlier compiler
snapshot. Digests: library `4b47d416…`, combined `937ef59b…`. Hosted evidence must
still bind its actual immutable commit and original fresh XML.

All literal original criteria remain [unchanged](../local001/original-criteria.json).
No issue closes or native/device/physical/vendor/minimum-platform acceptance
follows from these compiler, model, plan or inventory observations.
