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
repaired observer was subsequently exercised by fresh003 below.
`checkpoint-offline-003.json` preserves its115-test offline baseline and frozen
hashes; its then-pending runtime flag is historical, not rewritten.

### Third smoke and independent generic-lock review

The [additive003 archive](../../docs/development/evidence/build/dependency-fixtures/fixture003/archive-verification.json)
binds60 files and53 original/archive pairs. Fixture003 ran exactly bootstrap,
baseline and transitive drift in25.722s: exit0, exit0, expected typed-conflict
exit1. The suite exited0; **only that selected subset passed**, not all cases.
The original001/002 failures, tool copies and receipts remain unchanged.

Independent offline review then found a different problem in four **then-unexecuted**
generic lock cases: an unrelated `IOException` containing `lock state` could be
misclassified as expected rejection. Those cases now require exact paired
Gradle9.7.1 exception types/messages, owner/configuration identity, the actual-host
missing/stale lock discrepancy, exact known source/repository/trust bytes and no
unrelated owner/configuration/artifact failure. There is no generic phrase or
exception-suffix fallback. Unknown producer shapes stay unverified. This does
not invalidate the separate actually-executed002 wrong-SHA or003 transitive paths.

`checkpoint-offline-004.json` records146 offline tests (including four distinct
IOException regressions and stored-Yarn snapshot tests). The new generic-lock
positive shapes were **synthetic parser coverage only** at that checkpoint.
Actual004 below later reached only the missing-host case. Installed-class
inspection alone supplies message templates, not an executed producer path.

### Separate runtime-cache fence checkpoint005

Checkpoint004 and its exact eight-file tool/test receipt archive are preserved
under `docs/development/evidence/build/dependency-fixtures/checkpoint004/`.
The separate005 implementation has157 offline tests. It generates its own
`JAVA_TOOL_OPTIONS` for private JVM `user.home`, `java.io.tmpdir`,
`gradle.user.home` and `kotlin.daemon.runFilesPath`, plus private HOME, Gradle,
KONAN, XDG and temporary-directory environment paths. Inherited JVM/cache
overrides are not carried through; unsafe option-path characters and symlinks fail.

Two direct JDK17 source-launcher probes (including a path with spaces) checked15
selected values each successfully. This is **not an actual Gradle client/daemon
or Kotlin/Native/daemon-cache-use observation**. New init-script guards check
actual Gradle-JVM paths early and before/after owner acquisition. At the005
checkpoint those guards had **not yet compiled or run**; actual004 below later
exercised them. New owner receipts cannot omit the scoped runtime
observation or turn it into a wrapper-client/other-cache certification. The next
scheduled fixture must inspect both actual client and Gradle JVMs; no real-source
acquisition is authorized by005 alone.

### Actual fixture004 and the narrow offline006 correction

The [actual004 archive](../../docs/development/evidence/build/dependency-fixtures/fixture004/archive-verification.json)
preserves the once-authorized paired run, including all nine exact005/observer002
inputs. The suite exited1/26.715s after bootstrap0, baseline0 and missing-host1;
three remaining selected negatives never ran. No timeout, interruption or disk
stop occurred.005's init guards compiled/executed in all three invocations and
recorded the exact selected Gradle-JVM/environment paths. The passive witness
exited1/26.756s: all three installed-distribution clients were externally observed,
but no daemon diagnostic was attempted or bound to an init receipt. All six
recorded client/Gradle-JVM PIDs were absent at the recorded completion check.
Original suite/witness failures and historical checkpoint flags remain unchanged.

The [read-only diagnosis](../../docs/development/evidence/build/dependency-fixtures/fixture004-read-only-diagnosis.json)
reproduced the original missing-host **unverified** verdict. Every preceding exact
state/error-tail guard passed, but the allowlist named `ResolveException`, not the
actual `TypedResolveException` subclass. Pure Python inspection of exact pinned
Gradle9.7.1 class bytes confirms that hierarchy and diagnostic format; no JVM was
launched for the inspection.006 adds only that explicit wrapper with the observed
configuration-specific **dependencies** message, plus actual-shaped offline
regressions and unrelated-cause counterexamples. It does not accept arbitrary
subclasses or unobserved files/artifacts message variants, alter underlying lock
policy, or rewrite004 into a passing suite. `checkpoint-offline-006.json` records
the new six-input offline checkpoint separately from005.

Observer002 discarded candidate validation errors, so004's daemon rejection
cause is **unknown**; the last generic unavailable-input reason cannot identify
it. A separate observer003 adds bounded enum-only reason counters, not broader
process ownership or an attachment retry. Read `runtime-witness.md` and the new
independent review before any later launch. Neither the correction nor a passed
offline test establishes fixture005 or real root/convention acquisition safety.
Routine verification is authorized by the 2026-10-26 owner's
[policy update](../../docs/development/containment.md); technical prerequisites
still apply, without an additional routine approval or subagent delegation.

### Additive checkpoints007/008 — exact inputs, not a production trust claim

The 2026-10-27 [actual005 failure archive](../../docs/development/evidence/build/dependency-fixtures/fixture005-preflight-failure-20261027/lead-independent-review.json)
preserves five isolated invocations (0/0/1/1/1): baseline, missing-host and
missing-configuration checks matched; added-dependency remained unverified and
removed-dependency never ran. The exact added-module lock-origin wrapper says
`Dependency lock state out of date`, not `Could not resolve <module>.`.
Checkpoint007 adds only that observed paired exception/message shape with the
existing exact state/owner/graph checks. Unrelated causes stay rejected and the
unobserved removed-module analogue is not silently accepted.

The old witness rejected the deliberately updated policy README checksum before
starting any diagnostic. The lead's shell incorrectly continued after its failed
freeze preflight; both errors are preserved, not called a verified freeze or
external witness. `checkpoint-offline-007.json` is a **new exact six-input
manifest**, not an edit to006 or a checksum bypass. The observer must validate
this manifest/current inputs successfully **before** the paired suite is started.
The old005 result remains failed. Any subsequent actual run needs separately
reviewed receipts; this section and a passing offline test establish none.

The [actual006 archive](../../docs/development/evidence/build/dependency-fixtures/fixture006-witness-failure-20261027/lead-independent-review.json)
preserves six fresh invocations (0/0/1/1/1/1): all except the removed-dependency
classifier matched. The latter supplied the same short wrapper with the exact
missing locked-leaf cause. All six client diagnostics succeeded; **zero daemon
candidates/diagnostics/bindings** were established. Bounded no-child/lifetime
counters do not prove detached ancestry. Checkpoint008 adds that second exact
pair and requires a real `constraint=true` lock-origin unresolved edge.007 and
all original failures remain unchanged. That checkpoint's observer selected **008**
explicitly; no arbitrary checkpoint/hash refresh or generic-lock acceptance.
Runtime receipts identify their manifest and bound inputs with revision-neutral
field names, avoiding a misleading006/007 label on a later input set.

### Additive checkpoint009 — own the observed detached daemon

The actual finite60s acquisition hold at the original20s timeout confirms a
controller resource leak: the client exits143, but its exact live-validated and
pidfd-pinned daemon remains running in a separate session/group. The preserved
[red result](../../docs/development/evidence/build/dependency-fixtures/owned-daemon-timeout-red-20261027/lead-review.json)
includes **separate** probe cleanup, not success by the original controller.

009 binds **ten** core inputs, including `gradle_process.py`, `owned_gradle.py`,
`owned_cleanup_fixtures.py` and `test_owned_gradle.py`; 008's six inputs/manifest
remain immutable. Shared process grammars are extracted without signature/body/
decorator changes. The passive witness retains its public internal helper names,
strict attach checks and one-attempt-per-role rule; it explicitly selects009.

Only a controlled **single-root Linux installed Gradle9.7.1/JDK17** invocation
selects the new owner. Fresh bounded no-follow **private log filenames** nominate
daemons; neither log contents nor receipt PIDs grant signal authority. Admission
requires exact live parent/start/UID/JDK/cwd/full argv/private environment and
pidfd pre/post checks. Daemon-self sessions use exact pinned signals, never
`killpg(daemon_pid)`. Already proven leases survive ambiguity for safe cleanup,
but ambiguity/uncertainty still fail the result. Cleanup stops/waits/reaps on
normal return, timeout and interruption; a temporary single-threaded controller
subreaper is restored after **exact** adopted-daemon reaping, with no wildcard
wait, global PID scan, observer subreaper or jcmd. A second cancellation cannot
interrupt the bounded10s cleanup. Every known pidfd/directory handle is closed.

Actual normal/timeout/SIGINT/SIGTERM/TERM-resistant runs are separately scheduled:

```sh
python3 scripts/dependencies/owned_cleanup_fixtures.py \
  --destination /dev/shm/nativecmpkit-owned-cleanup-NEW \
  --gradle-home /opt/gradle/gradle-9.7.1 \
  --jdk-home /usr/lib/jvm/java-17-openjdk-amd64
```

Source/unit/manifest success is not a real cancellation execution. Wrappers,
composites, other hosts and arbitrary forked descendants retain explicit cleanup
gaps; SIGKILL of the controller cannot be caught. No ordinary dependency policy,
independent trust, library/consumer/native functionality or release gate follows.
See [ADR0007](../../docs/decisions/0007-owned-gradle-fixture-processes.md).

## Responsibilities and data flow

| File | Responsibility |
| --- | --- |
| `integrity_model.py` | Strict bounded JSON/XML/path/hash/lock parsing; exact artifact conflicts and per-configuration lock checks; completed owner-receipt validation |
| `integrity.py` | Snapshot current source; reserve an external workspace; run bounded acquisition/check; capture finalized trust/locks; aggregate receipts; explicit TOFU review and new-file-only reconciliation |
| `resolve-graphs.init.gradle` | Actual Gradle9.7.1/JDK17 interlocks; per-owner strict project locks; public mutable-dependency guards; configuration/graph/artifact acquisition; no silent failed-configuration allowlist |
| `gradle_fixtures.py` | Deterministic local Maven bytes and deliberately different checksum/lock contexts; fresh isolated cache per invocation; real-error classification |
| `test_integrity.py` | Offline rejection, scope, path, topology, command and resource-budget self-tests |
| `gradle_process.py` | Shared exact process/stat/argv/environment grammars; never controls a process |
| `owned_gradle.py` | Linux controlled-single-root client/daemon pidfd leases, bounded signals/waits, restored exact subreaper ownership |
| `test_owned_gradle.py` | Offline adversarial ownership, nomination, pinning, cancellation-cleanup and scope regressions; zero Gradle/Java |
| `owned_cleanup_fixtures.py` | Explicit real finite-hold/cancellation/escalation fixtures; never cleans up a daemon on the controller's behalf |

`snapshot` copies the **current dirty inputs**, not only HEAD. Relevant selected
files, stored `kotlin-js-store` inputs and empty `src` directory topology are
hashed; this preserves conditional
Android device-test source-set activation. Local properties, credentials/keys,
caches and build outputs are excluded. Computed settings/includes or an unknown
host require an explicit tool update; there is no fallback profile. The marker
is an accidental-misuse interlock, **not a hostile-code sandbox or signature**.

`run` rejects a Git worktree before writing a reservation. It uses a private
HOME/Gradle cache and strips inherited credential/JVM/verification overrides.
HOME redirection alone did not change JVM `user.home` in the pre005 tooling. Checkpoint005 adds
explicit VM/environment paths and Gradle-JVM guards as described above; actual
Gradle-client/daemon and non-Gradle cache consumption remain separate checks.
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
  --destination /root/nativecmpkit-build007-fixtures-005 \
  --gradle-home /opt/gradle/gradle-9.7.1 \
  --case missing-host-lock --case missing-configuration-lock \
  --case added-dependency --case removed-dependency \
  --total-timeout 300 --timeout 90 --reserve-mib 8192
```

This proposes **at most six Gradle invocations**: known-good bootstrap, ordinary
baseline check, two missing-lock cases and dependency addition/removal. The wrong
JAR/transitive cases already ran in002/003; they are not implicitly rerun here.
All referenced artifact/POM hashes already exist, so the four negatives must fail
for their exact lock discrepancy, not an unrelated checksum or I/O error.
This subset is not scheduled or authorized by the example. The first unexpected
result stops the subset;
there is no automatic retry. Each invocation uses `--max-workers=1` and a fresh
fixture-owned cache. Nothing modifies a production/shared cache, repository,
artifact, source, XML or lockfile.

One monotonic deadline is shared by the whole invocation sequence, including
setup; individual process limits cannot reset it. Twelve seconds are reserved
for termination/receipt writing. The POSIX runner monitors disk reserve;009's
controlled single-root Linux installed-Gradle slot owns the exact pinned client/
daemon on all return paths. Other slots still terminate only the original client
group and retain a detached-daemon gap. The CLI maps SIGTERM to cleanup. This is
not a kernel sandbox or proof against arbitrary descendants; inspect actual
scoped cleanup receipts after a stop.
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
- Copying stored JS/Wasm Yarn locks does not prove frozen installation or cover
  KGP's separate Wasm tooling installation/embedded lock. See the independent
  [Yarn policy review](../../docs/development/evidence/build/yarn-frozen-policy-review.md).
- Configured/observed selected runtime paths are not an OS filesystem sandbox.
  SDKs and arbitrary plugins can use other paths; unobserved caches are not certified.
- Actual root/convention acquisition, ordinary-build installation, full negative
  fixtures, changing metadata/declaration cases, script-lock cases, every required
  host and all library/device/browser/native/consumer/release gates remain separate.
- Real-source receipts omit raw exception bodies; task-owned fixture receipts
  contain sanitized errors to classify known harmless bytes. Gradle logs remain
  local evidence and are never sent as notifications or treated as instructions.

### Additive checkpoint010 — staged-file preflight, unchanged process semantics

The final009 staged check found one extra EOF blank line in new
`gradle_process.py`; the earlier worktree-only check had omitted untracked files.
The lead shell incorrectly continued to a local commit after that check failed.
That commit and red are preserved, not rewritten or called a passing staged
check. Source must be staged before the final freeze; run both cached and
worktree whitespace checks, and fail fast before committing/dispatching.

010 binds the same ten core inputs after the minimal EOF/documentation repair,
with an explicit predecessor009 SHA. Entire shared-parser AST and all process
owner/fixture/init implementation bytes are unchanged. The passive witness now
selects010 explicitly;009 remains immutable. Prior five actual009 cleanup runs
are retained at their original inputs, not claimed as fresh010 executions.
Current Python/manifest verification and any later actual run require their own
held receipts. No scope, acceptance, trust or release requirement is relaxed.
