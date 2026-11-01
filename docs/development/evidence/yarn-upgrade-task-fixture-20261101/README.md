# Yarn actual U4: owning helper-bound recovery — 2026-11-01

Private archival candidate for `docs/development/evidence/yarn-upgrade-task-fixture-20261101/`.
No live integration, issue change or new execution was performed during this readback.

## Exact actual scope

| Existing run | Actual outcome | Scoped observations |
| --- | --- | --- |
| `U4-f46114c63e0fc367` | **FAILED; Gradle 1 / 54.01s** | Two compiler errors at `OrdinaryYarnUpgradeTaskGate.kt:31`: unbounded `T` cannot satisfy Gradle `Action<T : Any>`. Six actionable tasks executed, including the failed helper compile; zero main-root actions/sentinel/graph/result receipts. This is not expected upgrade denial. |
| `U4-1f72e180af608ea3` | **Gradle 0 / 46.01s** | Ten actionable tasks: **five executed, five up-to-date**, not ten fresh executions. Fresh helper compilation reached actual root/child KGP configuration. Main-root graph exactly `:nativeCmpkitActionSentinel`; gate not selected. One fresh sentinel action/RAN/receipt and exact fresh TaskState. |

Recovery registers the actual KGP JS/Wasm upgrade objects at `:kotlinUpgradeYarnLock`
and `:kotlinWasmUpgradeYarnLock`. All twelve recorded typed/provider/dependency
bindings are true. The normal result binds the exact graph hash, reports no build
failure, and records only the sentinel action; its state is executed=true and
failed/skipped/up_to_date/no_source=false. Included-build actions are out of scope.
No U1/U2/U3, Node/Yarn install, test method, original XML or native execution is
accepted here. **#40 stays open.**

## Source cause and independent existing-artifact readback

[Readback](readback001.json) verifies all **52 current source hashes/sizes** and the
exact bounded source inventory/digest. The original 52 inputs reconstruct exactly
from **five saved preimages and 47 unchanged files**. Both original before/after
source-check JSONs, both recovery source-check JSONs and six selected runtime
before/after identities correlate; the six existing named runtime files were
rehash-read, never executed or copied. These are not a full compiler/dependency
closure, supply-chain trust or hostile-writer/atomic acquisition proof.

Only two 62-line helper copies change `<T>` to `<T : Any>` (3272 to 3278 bytes).
Three owning files replace exactly one expected helper digest each; every other
byte is unchanged. Saved before/after images reproduce both patches exactly.
Old helper SHA: `6473a953ad6c95e0eb00f0e79e2275aac0731976db06356b73bcfa6abfac0f14`.
New helper SHA: `5cb4ea67fbf6d8ba22d964ccce03fc5e72bbf78bb16e97b6e254a57a3cd97682`.
The original source-only bound **0/1 → 1/1** and pin **0/3 → 3/3** receipts are
preserved in [repair/](repair/). They are source comparisons, not new type/model/native tests.

Earlier draft **7/18 source passes, 11 failures**, successor **18/18**, and
**19 + five modeled methods** remain [reported historical metadata](reported-history001.json),
not replayed or promoted to fresh corroboration; underlying earlier source-contract
logs were not available in this relocated package.

## Four exact original task receipts

[Task receipts](task-receipts/U4-recovery002/) match both the original actual build
directory and preserved private copies byte-for-byte, with exact inventory, shared
run/source/helper/Gradle9.7.1/Java17/KGP2.4.20 identity, graph/action/state correlation
and actual file mtimes within the recorded request interval. The fixture writes
bounded `CREATE_NEW` receipts after requiring an absent unique run directory.
This readback did not replay their actions or run the strict classifier.

| Receipt | Bytes | SHA-256 |
| --- | ---: | --- |
| `action-0001.json` | 490 | `ad9384f3e8e90e7da7e81efe00f8c437a38430d00c8928c074759347b503ebdb` |
| `graph.json` | 1467 | `b90f7468cb0409bb679ab398944477a452d3ed22a51dd1856288b5114d4e0a2c` |
| `result.json` | 966 | `a1a08e0c174c6d6af002d06063f8cf328657e9f6b308689a9748294a0449e2ca` |
| `sentinel.json` | 403 | `4918492059fe540fbc27209400a7167d4d52d5729f9378f0f3b71e521ab19ac0` |

## Bounds, chronology and public-safe copies

Both existing bounded requests use the unchanged reviewed resource guard,
300-second timeout and **8192 MiB disk reserve**. Resource-result/log-header/embedded
result records correlate and report normal child completion without a timeout/disk
stop reason. Recovery overlay free bytes are 46989619200 → 46964744192.
**Detached/composite descendant cleanup, OS network sandbox, RSS enforcement and
complete bounds remain unknown/null.** Offline/serial flags are not proof of those
properties. No security, production adoption, dependency-policy, Gradle10,
configuration-cache/exclusion/bootstrap, other-host, release or readiness acceptance.

The [request documents](requests/) retain their authored “not-executed/prepared”
status fields: those describe the earlier preparation phase, not the later actual
results. Initial repair metadata similarly retains its then-pending pin update.
Later observations/results are additive, not rewritten historical requests.

Only safe source/hash/task records are copied. [Path symbols](redactions001.json)
replace private roots, runtime locations and environment directories; raw logs,
keys, binaries and machine directories are absent. The four task receipts, freezes,
source-only JSON hash receipts and safe sources retain exact bytes. Internal
invocation/request/observation hashes refer to **original private objects**, not
symbol-redacted copies; [identity correspondence](original-private-identities001.json)
records both hashes/sizes and omitted private originals. This is an evidence subset,
not a complete runnable 52-file snapshot. [SHA256SUMS](SHA256SUMS) covers every
candidate file except itself; final exact-inventory/hash readback and read-only
seal are recorded in [seal001.json](seal001.json).
