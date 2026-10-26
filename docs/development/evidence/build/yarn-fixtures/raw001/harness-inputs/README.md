# Bounded RAW-YARN fixtures

This task-specific harness characterizes the **already installed** Node 24.16.0 /
Yarn Classic 1.22.22 bytes pinned in `raw_yarn_fixtures.py`. It does not install or
download tooling, run Gradle, change root build policy, use real dependencies,
modify shared caches, enable CI, publish, or write to GitHub. A hash pin identifies
observed tooling bytes; it is not independent provenance verification.

## Order of execution

First run the independent offline unit suite:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s scripts/dependencies/yarn -p 'test_*.py' -v
```

The tests deny real socket creation and child processes; process-group/budget
tests are **mocked**, not runtime isolation proofs. Temporary unit files stay in
this directory's ignored `.test-work/`. There is deliberately **no `__init__.py`**:
these tests are not part of the sibling dependency tooling's discovery checkpoint.

Only after inspecting a successful offline result, run the explicitly authorized
bounded characterization. Use a **new** run ID; the command below is the first
planned ID, not a statement that it has already run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/dependencies/yarn/raw_yarn_fixtures.py \
  --run-id raw001 --total-timeout 300 --per-process-timeout 30 --reserve-mib 8192
```

The executable entry points and install argv are fixed. The CLI accepts only a
new `rawNNN` ID and tighter runtime/storage limits; arbitrary tools, scripts,
registry endpoints and package names are not CLI inputs. Total budget is at most
300 seconds, individual processes at most 60 seconds (30 in this command), with
12 seconds reserved for cleanup and a minimum 8 GiB available-disk reserve. A
timeout, low disk, oversized log, startup/runner failure, unexpected category or
changed tool/source input stops the suite. Nothing retries or overwrites a run.

## Scope and limits

The registry binds only `127.0.0.1` on an ephemeral port and serves exact,
self-authored metadata/tarballs from memory. It has no proxy/forwarding/file
server. Origin, method, auth-header presence, status, completed writes and response
hashes are checked. **There is no kernel or egress sandbox.** Fresh environment
construction, explicit config and loopback package URLs reduce unintended access;
the registry log does not prove no outside network request occurred.

Each command uses its own task-owned HOME, TMPDIR, XDG directories, Yarn cache,
global/link/node_modules directories, empty npm config and explicit Yarn rc.
Inherited environment/config/auth/proxy/Node hooks are excluded. Default rc
discovery, self-update checks and V8 compile caching are disabled. A file mutex
avoids a second network listener. Pinned Node runs the pinned Yarn entrypoint;
the separate harmless script control uses only two authored local marker writers.

Packages are deterministic valid USTAR/gzip archives, with parent 1.0.0 depending
on leaf 1.0.0. Parent 2.0.0 is available only to model direct manifest drift. A
changed leaf archive differs in one inert payload but remains a valid archive.
The wrong SRI is valid SHA-512 syntax with exactly 64 zero digest bytes. These are
not malformed-string, broken-HTTP or invalid-gzip substitutes for integrity tests.
The port, timestamps and absolute work paths vary per run; those actual inputs
are preserved and hashed. Only package bytes are expected to be reproducible.

| Case | Intended raw observation |
|---|---|
| bootstrap | Unfrozen seed creation, scripts suppressed |
| YF001-positive | Fresh frozen install of complete valid lock |
| YF002-missing-lock | Characterize absent-lock acceptance; **counterexample** |
| YF003-direct-drift | Exact frozen-lock error for root parent 1.0.0→2.0.0 |
| YF004-wrong-sri | Exact integrity error after original valid leaf bytes served |
| YF005-changed-tarball | Exact integrity error after changed valid leaf bytes served |
| YF006-incomplete-transitive | Characterize missing leaf-lock acceptance; **counterexample** |
| YF008-script-control | Frozen install runs both harmless local marker writers |
| YF008-scripts-suppressed | Fresh equivalent install creates neither marker |

Every receipt records expected versus observed categories. Arbitrary nonzero,
network, gzip, I/O or timeout failures are inconclusive, never accepted negative
tests. Accepting a missing/incomplete lock is an observed counterexample, **not a
security pass**. All `security_enforcement_pass` fields remain false: this is not
KGP/root-policy enforcement, a real dependency graph, or a release gate.

## Evidence

Runs are immutable directories under
`docs/development/evidence/build/yarn-fixtures/`. Archives retain controlled
inputs/outputs, tarballs, the actual seed/mutated locks, tool/source hashes,
argv/environment-key policy, process logs/receipts, server body hashes, installed
graph file hashes and script markers. Self-authored harness inputs are copied
into each run. Raw task-owned HOME/cache/work directories stay local and ignored;
installed tools or unrelated machine files are not archived. The summary has a
hash manifest of its other archived files, not a self-referential hash.

Read the executed evidence summary before reporting a result. A matched raw
prediction is not a passing project policy. Missing-lock preflight, transitive
closure/origin validation, KGP store ordering, ordinary versus explicit update
mode, Wasm's separate tooling setup and Gradle integration remain separate gates.
