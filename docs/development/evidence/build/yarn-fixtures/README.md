# Executed RAW-YARN characterization

**Result:** the installed Node **24.16.0** / Yarn Classic **1.22.22** matched all
eight selected fixture predictions on 2026-10-24. **Two are acceptance
counterexamples, not security successes:** frozen Yarn accepted both a missing
lock and a lock missing its transitive leaf. No BUILD-007 closure, Gradle-policy
adoption, package-provenance approval or release-gate pass is implied.

## Actual execution and preserved failures

| Evidence | Actual result |
|---|---|
| [offline001](offline001/receipt.json), [log](offline001/stderr.log) | 67 offline unittest methods attempted; one cleanup error, exit 1. A mocked `os.fstat` escaped its intended scope and confused `tempfile`/`shutil`'s symlink check. **Retained, not overwritten.** |
| [offline002](offline002/receipt.json), [log](offline002/stderr.log) | Same 67 methods, **67/67 passed**, exit 0 after narrowing the mock with `ExitStack`. No actual sockets or child commands in these tests. |
| [raw001 summary](raw001/summary.json) | Harness exit **0**, **4.1502 s**; bootstrap plus eight fixture observations completed. Three intentional Yarn rejections each exited 1. |
| [independent readback](verification001.json), [verifier](verify_raw001.py) | Exit **0**; checked all **137 archived manifest entries** (6 + 6 + 125), original failure, actual logs/argv/errors, source/tool hashes, tarballs, locks and retained task-owned installed files. Its 1,876 data checks are **not** additional executed package/library tests. |

Raw execution was **23:14:12.641256–23:14:16.791370 UTC**. The command actually run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/dependencies/yarn/raw_yarn_fixtures.py \
  --run-id raw001 --total-timeout 300 --per-process-timeout 30 --reserve-mib 8192
```

The unit command, invoked by the bounded offline receipts, was:

```sh
python3 -m unittest discover -s scripts/dependencies/yarn -p 'test_*.py' -v
```

The raw suite used nine separate **install** workspaces plus a fresh shared
version-probe workspace. Node and Yarn version probes are not install cases:
there were **11 directly managed Node processes** (2 probes + 9 installs).
The two harmless lifecycle commands in the positive script control are child
commands within that install, not extra counted fixtures. The registry served
**22 successful GET responses**, totaling **11,533 body bytes**, on the recorded
loopback origin `http://127.0.0.1:40045/registry`.

No timeout/reserve/log-size limit triggered. Each process was recorded as
`completed`, without cleanup escalation; free space at suite end was
**38,875,447,296 bytes**, above the 8 GiB minimum. Harness and pinned tool hashes
were equal before/after execution and checked again during readback.

## Observations

All installs started with task-owned empty HOME/cache/temp/XDG/global/link
directories and no `node_modules`. They used explicit config and constructed
environment allowlists, not inherited auth/proxy/Node hooks. Each case has a
`case-plan.json`, `process.json`, `receipt.json`, input/output files and raw logs.

| Case / receipt | Yarn exit | Verified observation |
|---|---:|---|
| [bootstrap](raw001/cases/bootstrap/receipt.json) | 0 | Unfrozen install wrote the 765-byte seed lock; scripts did not run. |
| [YF001-positive](raw001/cases/YF001-positive/receipt.json) | 0 | Fresh frozen install fetched both authored tarballs, installed exact parent/leaf 1.0.0 files and preserved the complete lock. |
| [YF002-missing-lock](raw001/cases/YF002-missing-lock/receipt.json) | 0 | **Counterexample:** root and leaf installed; the lock was absent both before and afterward, despite `--frozen-lockfile`. |
| [YF003-direct-drift](raw001/cases/YF003-direct-drift/receipt.json) | 1 | Root manifest requested available parent 2.0.0 while the seed contained 1.0.0. Exact frozen-lock diagnostic; lock and input bytes unchanged. Registry metadata resolution succeeded first. |
| [YF004-wrong-sri](raw001/cases/YF004-wrong-sri/receipt.json) | 1 | Only the leaf lock SRI changed to a valid SHA-512 token encoding 64 zero bytes. Original valid leaf archive was served completely; exact integrity diagnostic contained its independently verified computed digest. |
| [YF005-changed-tarball](raw001/cases/YF005-changed-tarball/receipt.json) | 1 | Original valid lock; served a valid repacked leaf archive changing only `payload.txt`. Exact integrity rejection, not an HTTP/gzip/extraction failure. |
| [YF006-incomplete-transitive](raw001/cases/YF006-incomplete-transitive/receipt.json) | 0 | **Counterexample:** removed only the leaf lock stanza, retaining parent's dependency on leaf 1.0.0. Both packages installed; incomplete 455-byte lock stayed unchanged. |
| [YF008-script-control](raw001/cases/YF008-script-control/receipt.json) | 0 | With scripts enabled, both authored root/dependency marker writers ran. Each produced the expected 38-byte local file. Complete lock unchanged. |
| [YF008-scripts-suppressed](raw001/cases/YF008-scripts-suppressed/receipt.json) | 0 | Fresh equivalent frozen install with `--ignore-scripts` produced neither marker; package files and lock matched the control inputs. |

The exact frozen rejection was:

```text
Your lockfile needs to be updated, but yarn was run with `--frozen-lockfile`.
```

The integrity receipts retain Yarn's exact URL-prefixed error, computed SHA-512
and SHA-1 tokens, and the separate expected lock SRI. Arbitrary nonzero outcomes
were not used as substitutes. All nine `security_enforcement_pass` fields and the
suite's `security_enforcement_complete` remain **false**.

## Bound inputs

The [seed lock](raw001/seed/yarn.lock) has SHA256
`e49d61844aee19660f40a4e37c646a6fa96af0d6342e13121dcceb95f1a3e666`.
The port is ephemeral; actual manifests/rc/locks are retained, not claimed to be
byte-identical across runs on different ports. Synthetic package archives are
deterministic valid USTAR/gzip, not downloaded third-party dependencies.

| Archived tarball | Bytes | SHA256 |
|---|---:|---|
| [parent 1.0.0](raw001/registry/nativecmpkit-fixture-parent-1.0.0.tgz) | 316 | `092de7d723c91bb6db4f17764340a5aba00b7160a79cfdc54ddcc1751bd53197` |
| [parent 2.0.0](raw001/registry/nativecmpkit-fixture-parent-2.0.0.tgz) | 318 | `e355f958e41969ff2f0786e8ca3ed7ae9b31b901d82464366861301f72b9029f` |
| [leaf original](raw001/registry/nativecmpkit-fixture-leaf-1.0.0.tgz) | 427 | `00150018d21d20fe8936ae0536b0a2b9e3f78ad5e793b84e7e1e74d3d9408b7a` |
| [leaf changed](raw001/registry/nativecmpkit-fixture-leaf-1.0.0-changed.tgz) | 427 | `d11559474d3c361e377f69b9fdee9428b32e28712497acb73e365ed3c54068c2` |

Full source/tool hashes, including the pinned Node binary and Yarn entrypoint,
bundle, compile-cache helper and manifest, are in the raw summary. Readback
compared installed package files with the independently opened authored tarball
members rather than merely trusting a “success” line. Original harness/test/docs
inputs are copied into each run. Task-owned raw HOME/cache/work directories stay
local and gitignored; no installed tools, shared-cache contents, credentials or
environment dumps are archived.

## Explicit limits and remaining gates

- **No kernel or egress sandbox was available.** The server listened only on
  IPv4 loopback and had no forwarding/file-serving route; all recorded requests
  matched authored responses. That server log does not prove no external network
  request occurred. Yarn's informational documentation URL was printed, not
  evidence that the URL was fetched.
- Hash pins identify observed bytes, **not independent provenance or trust**.
  SRI rejection here does not prove that real dependency graphs, tool archives,
  all resolver forms or lifecycle scripts are safe.
- These are **raw Yarn fixtures**, not KGP execution, a root preflight, a stored
  lock policy or project/browser tests. Frozen Yarn alone demonstrably does not
  enforce missing-lock or full transitive-closure policy on this graph.
- Failed installs may write task-owned caches/extraction intermediates. Only
  the checked manifests/locks/markers are asserted unchanged; this is not a
  transaction or a fail-before-all-filesystem-writes guarantee.
- The suite did not run KGP store/restore/upgrade behavior, warm/up-to-date or
  mixed-task guards, or separate Wasm tooling fixtures (the earlier proposed
  YF-007/YF-009/YF-010). Those remain adoption gates.
- Node emitted Yarn's `url.parse()` deprecation warning. It was retained and not
  counted as a vulnerability, integrity rejection or test failure.
- No shared root/source/build policy was edited, no Gradle was run by this task,
  and no publishing/CI/GitHub state changed. BUILD-007 remains open.

See the earlier [installed KGP/Yarn policy review](../yarn-frozen-policy-review.md)
for source/bytecode context. The later lead-requested
[Wasm script-propagation review](wasm-tooling-ignore-scripts-source-review.md)
and [JSON](wasm-tooling-ignore-scripts-source-review.json) confirm the configured
`ignoreScripts` **source path only**, not an actual tooling invocation or frozen
guarantee. That follow-up is distinct from the raw fixtures above.

## Next step: design only

The lead-requested [ordinary-build policy proposal](../../../../../scripts/dependencies/yarn/ordinary-policy-plan.md)
specifies explicit missing-lock and declared-selector-closure guards, ordinary
versus bootstrap separation, and mandatory real KGP warm/direct-store/mixed-task
tests before adoption. **No proposed checker or Gradle integration was run.**
Its [read-only graph observation](ordinary-policy-graph-observation001.json)
binds 132 input files, including all 124 generated root/workspace manifests.
The current JS graph includes npm aliases and a GitHub Karma resolver without
SRI; a registry-only first profile must reject it, not report all graphs verified.

That observation also binds the exact Wasm tooling task-name derivation and
historical task-discovery evidence: **`:kotlinWasmToolingSetup`**. This is an
additive source/readback result, not a new Gradle/tooling execution.

The later [destination/environment review](wasm-tooling-destination-source-review.md)
and [JSON](wasm-tooling-destination-source-review.json) document the default
user-Kotlin-home tooling cache, explicit-directory skip trap and pre-Yarn lock
write. The [original v1 receipt snippet](../../../../../scripts/dependencies/yarn/tooling-receipt-init-proposal.md)
and [installed API binding](wasm-tooling-init-api-review.json) are **unexecuted**
historical records. **V1 is blocked for adoption:** included builds inherit init
scripts, but its unconditional root task/home gates, receipt writes and listeners
do not distinguish the convention build. A successful earlier hash/API readback
did not establish that design's correctness.

The additive [v2 proposal](../../../../../scripts/dependencies/yarn/tooling-receipt-init-proposal-v2.md)
uses `beforeSettings` with exact canonical root/convention identity and parent-role
checks, deferring every root-only effect until root acceptance. Known convention
compilation returns without root gates, receipts or graph listeners. See its
[scope/API review](wasm-tooling-init-scope-review002.md),
[JSON binding](wasm-tooling-init-scope-review002.json), and
[preservation checkpoint](wasm-tooling-init-scope-checkpoint001.json), including
the byte-identical [pre-correction index](wasm-tooling-init-v1-evidence-index.md).
V2 received independent **source-only** scope review; it is still uncompiled,
unexecuted and unadopted. Public method existence is not Groovy integration or a
real tooling result. The additive
[readback](tooling-scope-verification002.json) checks documentation/evidence only,
not callbacks, install behavior, test execution or BUILD-007 closure.

[Documentation verification](verify_documentation.py) rechecks archived hashes,
source/class/resource bindings, local links and task-owned ignore rules without
running the harness or any proposed policy. Its data-check count is not another
fixture/library-test count. It requires the recorded local generated manifests
and installed JARs; later input changes should fail that historical binding.
