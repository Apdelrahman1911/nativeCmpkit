# BUILD-007 isolated dependency-integrity tooling

This directory is inert: it changes no ordinary Gradle build or CI policy. It is
an implementation checkpoint for the [BUILD-007 plan](../../docs/development/build007-implementation-plan.md),
not closure of the finding, independent trust, or permission to publish. Heavy
commands require a separately scheduled lead-approved slot during containment.

## Evidence boundary

At the **2026-10-24 offline checkpoint**, the Python parser/orchestration tests
passed; the new Gradle init script and real fixtures had **not run**. Read
`checkpoint-offline-001.json` for exact input hashes and test command/result.
Later task-owned `fixture-results.json`/invocation receipts, if present, establish
only the explicitly executed cases; they must not be inferred from this README.

Synthetic receipts, deterministic fixture preparation and mocked runners in
`test_integrity.py` are not actual Gradle enforcement tests. The offline suite
never invokes Gradle or a network service:

```sh
python3 -m unittest discover -s scripts/dependencies -p 'test_*.py' -v
python3 scripts/dependencies/integrity.py --help
```

### First actual smoke and source-only repair

`fixture-smoke-001.json` preserves the first scheduled local-Maven attempt:
Gradle9.7.1/JDK17.0.20 compiled/executed the init script, resolved the project
fixture graph, then **failed** the aggregate because the empty buildscript graph
used an unhandled non-project/non-module root. The process exited1 in8.50s;
the suite stopped after8.55s. **No baseline check, checksum-negative or
locking-negative case ran or passed.** XML was written despite aggregate failure,
and no project lockfile was finalized. Original workspace evidence remains
unchanged; source repair does not retroactively make that run successful.

Read-only public API inspection identified `RootComponentIdentifier`. The repair
models only an identifier of that public type **equal to this configuration's
`ResolutionResult.rootComponent.id`**, and only in the inventoried buildscript
scope. It is labeled `script-root`, never a module or verified artifact. Other
unknown identifiers still fail. The outer validator checks owner, configuration,
root identity/basis and outgoing external edges; it rejects a script root used
as an arbitrary selected dependency or in a project configuration. Completed
owners now also require an explicit `complete=true` and recorded resolution root.
`checkpoint-offline-002.json` records this repair's frozen source hashes and
offline tests; fixture002 then exercised it in successful bootstrap/baseline runs.

### Second smoke and structured classifier repair

The [persistent fixture archive](../../docs/development/evidence/build/dependency-fixtures/README.md)
contains original001/002 invocations, owner/configuration receipts, exact
XML/locks, input/tool bytes and hashes, and sanitized logs. No cache/JAR payloads
or private machine context are archived.

Fixture002 ran all four selected invocations in34.76s on Gradle9.7.1/JDK17.0.20.
Bootstrap and the ordinary baseline passed. Wrong JAR bytes produced the exact
expected/actual SHA256 and `DependencyVerificationException`. Transitive strict
drift failed in Gradle with `ConflictingConstraintsException`, but the original
observer did not recognize `1.0 - from lock file`; **the original suite exited1**.

The narrow repaired observer requires all three unresolved leaf edges (parent
range, locked1.0, strict1.1), their actual typed conflict and explicit lock-origin
message, the exact old lock module set, known JAR/POM bytes/hashes for both leaf
versions, unchanged source/trust/locks, and absence of unrelated failures. An
additive **read-only post-hoc** receipt establishes that exact conflict in retained
002 data without rewriting the original result or running Gradle again. The
repaired observer still awaits a fresh003 bootstrap/baseline/drift sequence.
`checkpoint-offline-003.json` records its offline tests and new frozen hashes.

## Responsibilities and data flow

| File | Responsibility |
| --- | --- |
| `integrity_model.py` | Strict bounded JSON/XML/path/hash/lock parsing; exact artifact conflicts and per-configuration lock checks; completed owner-receipt validation |
| `integrity.py` | Snapshot current source; reserve an external workspace; run bounded acquisition/check; capture finalized trust/locks; aggregate receipts; explicit TOFU review and new-file-only reconciliation |
| `resolve-graphs.init.gradle` | Actual Gradle9.7.1/JDK17 interlocks; per-owner strict project locks; public mutable-dependency guards; configuration/graph/artifact acquisition; no silent failed-configuration allowlist |
| `gradle_fixtures.py` | Deterministic local Maven bytes and deliberately different checksum/lock contexts; fresh isolated cache per invocation; real-error classification |
| `test_integrity.py` | Offline rejection, scope, path, topology, command and resource-budget self-tests |

`snapshot` copies the **current dirty inputs**, not only HEAD. Relevant selected
files and empty `src` directory topology are hashed; this preserves conditional
Android device-test source-set activation. Local properties, credentials/keys,
caches and build outputs are excluded. Computed settings/includes or an unknown
host require an explicit tool update; there is no fallback profile. The marker
is an accidental-misuse interlock, **not a hostile-code sandbox or signature**.

`run` rejects a Git worktree before writing a reservation. It uses a private
HOME/Gradle cache and strips inherited credential/JVM/verification overrides.
Only a task-owned controlled fixture may use the inspected installed Gradle;
real-source candidates use their copied wrapper. Source, XML and owner-local
locks are recorded separately. Fresh run IDs and immutable output paths are
mandatory. A replaced reservation is never silently removed.

The init script inventories every named project and project-buildscript
configuration and its roles/attributes. It acquires every resolvable entry,
selected components, dependency edges and external-only artifact-view outputs.
Lenient artifact views collect diagnostics; **any unresolved graph/artifact
failure remains fatal**. Root aggregation explicitly includes the convention
build. Independent expected project and task inventories detect omissions.

Project locks use `<owner>/gradle/dependency-locks/<actual-host>.lockfile` and
`LockMode.STRICT`. Gradle9.7.1's resolver explicitly prohibits combining locking
with `failOnChangingVersions()` (read-only installed-JAR inspection). Instead,
public `ComponentMetadataDetails.isChanging`/external SNAPSHOT checks and
`ExternalModuleDependency.isChanging` checks before resolution reject observed
mutable dependencies. Guards are installed before project evaluation and appended
after evaluation. The receipt labels this **public-guard inference**, not a read
of Gradle's internal final changing flag. A hostile later build rule is not an
attested scope; real changing-module fixtures remain a separate required check.

After Gradle **exits**, the outer runner captures finalized XML/locks. Bootstrap
requires both `--write-locks` and `--write-verification-metadata sha256`. Exit0 or
an XML file alone is insufficient: owner/configuration receipts and finalized
lock equality must validate. Bootstrap is **not** checksum enforcement.

An ordinary `check` forbids writer flags, requires an explicit matching candidate
review, and refuses changed source/trust/locks. `review` accepts only explicit
registry-TOFU acknowledgement after actual complete acquisitions. Root review
requires separate root/composite and standalone-convention acquisitions. `merge`
can create only a **new** output, never replace an input or install live trust.
Conflicting SHA256 values for the same coordinate/artifact fail; alternative
trust, broad exemptions, disabled metadata verification and fabricated signature
trust are rejected.

## Scheduled tiny fixture command

Use a new directory **outside every Git checkout**, on a filesystem with at least
8GiB free reserve (avoid RAM-backed `/tmp` on a memory-constrained host). This
example is not permission to run it:

```sh
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
python3 scripts/dependencies/integrity.py fixtures \
  --destination /root/nativecmpkit-build007-fixtures-003 \
  --gradle-home /opt/gradle/gradle-9.7.1 \
  --case transitive-strict-drift \
  --total-timeout 300 --timeout 90 --reserve-mib 8192
```

This requests **at most three Gradle invocations**: known-good bootstrap, ordinary
baseline check, and strict transitive-version drift. The wrong-JAR case already
ran in002; it is not implicitly rerun here. Both leaf
versions' known hashes exist before drift, so that case must fail for locking,
not an unrelated missing checksum. The first unexpected result stops the subset;
there is no automatic retry. Each invocation uses `--max-workers=1` and a fresh
fixture-owned cache. Nothing modifies a production/shared cache, repository,
artifact, source, XML or lockfile.

One monotonic deadline is shared by the whole invocation sequence, including
setup; individual process limits cannot reset it. Twelve seconds are reserved
for termination/receipt writing. The POSIX runner monitors disk reserve and
terminates its child process group on time/disk/interruption. The CLI maps
SIGTERM to this cleanup path. This is not a kernel resource sandbox or proof
against arbitrary detached descendants; inspect process cleanup after a stop.
Windows process execution has not been implemented/tested.

Available case names (`--case` is repeatable; baseline is always included):

- `baseline-check`: ordinary strict positive check.
- `wrong-jar-sha`, `wrong-pom-sha`: expected/actual known checksum rejection.
- `missing-hash`: required artifact hash absence.
- `missing-host-lock`, `missing-configuration-lock`: strict missing state.
- `transitive-strict-drift`: conflicting strict transitive version with known hashes.
- `dynamic-transitive-frozen`: new repository version must not change the lock.
- `added-dependency`, `removed-dependency`: exact locked module-set drift.
- `included-root-check`, `standalone-wrong-hash`: included-root trust versus
  standalone trust ownership (requires another known-good bootstrap).

Omitting `--case` requests the complete authored suite, not just the tiny subset,
and still obeys the total deadline. A larger slot must be explicitly scheduled.
Partial success is exported as `selected_cases_observed_as_expected`; it never
sets `all_cases_observed_as_expected`. Missing/time-limited/unexecuted cases stay
visible. A nonzero exit without the expected real Gradle error is not a negative
test pass; timeouts are never counted as checksum/lock rejection.

## Explicit remaining gates

- No ordinary project/build/CI policy is installed by this directory alone.
- Project locking does **not** lock buildscript provider versions. Settings
  script/plugin and detached configurations lack a complete version-lock
  inventory. Settings inventory is diagnostic, not complete acquired graphs.
- Artifact-view results can be transformed outputs/directories, not registry
  originals. Their hashes are always `artifact-view-output-unclassified`.
  Verification XML supplies original external dependency trust observations,
  still TOFU. No independent provenance/advisory clearance is claimed.
- Source/local-project/file artifacts and non-Gradle downloads are not covered.
- Actual root/convention acquisition, ordinary-build installation, full negative
  fixtures, changing metadata/declaration cases, script-lock cases, every required
  host and all library/device/browser/native/consumer/release gates remain separate.
- Real-source receipts omit raw exception bodies; task-owned fixture receipts
  contain sanitized errors to classify known harmless bytes. Gradle logs remain
  local evidence and are never sent as notifications or treated as instructions.
