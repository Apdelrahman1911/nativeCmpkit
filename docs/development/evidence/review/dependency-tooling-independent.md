# Independent BUILD-007 dependency-tooling review

**Reviewer:** `/root/metadata_archive`, 2026-10-24–25.
**Scope:** the isolated Python/Gradle acquisition, checksum, lock and fixture
tooling; original fixture001/002 evidence; subsequently archived fixture003;
checkpoint004 classifier and checkpoint005 cache-path corrections; separate
passive runtime-witness001/002 helper and proposed paired command; subsequently
actual fixture004 readback, core006 correction, and Wasm tooling init proposals.
This is **not BUILD-007 closure, production dependency verification, independent
artifact trust, security/license clearance, or a release gate**.

The reviewer ran **no Gradle, network, GitHub, publication or status-generation
command** and changed no source, policy or existing archive. Only this report
and its [machine-readable evidence](dependency-tooling-independent.json) are
reviewer-owned deliverables. The build owner owns any coordinated correction.

## Latest follow-up (2026-10-25)

- **Actual004 remains failed/incomplete.** Independent readback matched66
  original/archive pairs,73 archived hash bindings, six derived records and nine
  frozen tool inputs. Bootstrap/baseline graph summaries revalidated; frozen005
  replay retained the original missing-host **unverified** verdict. Three init005
  runtime maps and three external client observations matched; **zero external
  daemon observations** were established. The observer's discarded daemon
  rejection reason cannot be recovered from its generic final reason.
- **Core006 is source/offline-green only:**164 independent Python tests passed
  in2.419s;15 additional exact-wrapper checks passed. The additive parser result
  identifies the retained004 missing-host cause without rewriting its failed
  suite. No new Gradle fixture was executed by this review. Observer003 is not
  certified by these checks.
- **Wasm init proposal v1 has a source-confirmed scope defect, not an observed
  runtime failure.** Separate v2 corrects root/included classification before
  root-only work and is source-only-green for that correction. Neither proposal
  was compiled or run as part of this source review. Its root task allowlist is conservative
  and unexecuted, not a fabricated claim about the actual complete task graph.

The older checkpoint sections below retain their **historical** observations.
In particular, actual004 supersedes the earlier statement that005's Gradle
guards had not compiled/run; it does not establish external daemon identity or
actual compiler/Native/plugin cache consumption. Detailed additive reviews are
at the end of this report and in the JSON companion.

## Historical executive result through observer002

- The five reviewed implementation/test hashes matched checkpoint003; the six
  fixture inputs, including the README, are preserved under fixture003's
  `tool-inputs/`. **115 offline tests passed independently in 0.957s**.
- After the narrow owner correction, **146 tests passed independently in
  2.339s against immutable checkpoint004**. The four original counterexamples
  now reject; an additional28-scenario synthetic matrix also passed. These are
  not actual missing/add/remove Gradle tests.
- Two additional mocked runner checks confirmed that **exit0 plus a captured
  verification XML does not establish a complete graph**. Missing graph receipts
  kept all graph/lock/checksum-success flags false in bootstrap and check modes.
- The reviewer verified **163 bound file hashes, 142 original/archive pairs,
  124 candidate-input file occurrences, 26 deterministic JAR originals, 15
  captured XML/lock pairs, and 16 configuration records** across eight actual
  archived invocations. Four successful bootstrap/baseline graph summaries
  revalidated against the reviewed parser and exact archived locks.
- **A Medium classifier defect was independently reproduced:** the four generic
  lock-negative classifiers can label unrelated I/O failure as expected lock
  rejection merely because its text mentions `lock state`. This does **not**
  invalidate the actually executed001/002/003 cases, which use other branches.
  The owner and lead were notified; the checkpoint004 correction is independently
  source/offline-checked, while its four actual Gradle cases remain unexecuted.
- The owner's separate **JVM-home isolation gap** was independently confirmed:
  private `HOME` does not set JVM `user.home` on the existing JDK17.0.20. No
  shared-cache write was demonstrated. The separate checkpoint005 correction
  passed **157 offline tests in 2.408s** and two bounded direct-JDK probes,
  each with **15/15 selected path/version checks**. Its new Gradle guards have
  not compiled or run; actual client/daemon/cache-use evidence remains pending.
- The separate passive observer's **76 offline tests passed in 0.180s**, but an
  independent six-scenario mocked matrix found an incomplete JVM-entrypoint
  identity gate. Observer001 was held before launch. Its narrow002 correction
  passed **91 tests in 0.210s**, a14-scenario identity matrix and11 modeled
  orchestration cases. **Observer002 is source/offline-green only**; actual
  process behavior remains unverified and launch requires fresh lead scheduling.
  No Gradle/Java/jcmd was run during this observer review.
- Fixture001 remains a failed bootstrap. Fixture002 retains its original failed
  suite and unverified drift verdict, alongside additive exact post-hoc analysis.
  Fixture003 establishes **only** a fresh bootstrap/baseline/transitive-drift
  subset. No batch establishes full fixture or production coverage.

## Frozen inputs and evidence identity

The initial reviewed checkpoint is
[`checkpoint-offline-003.json`](../../../../scripts/dependencies/checkpoint-offline-003.json),
SHA256 `10c59162a338fcfd149dec649a105a1f4b04ee6c3001f48dacf8570f4e40ea6e`.
The immutable copies are in
[`fixture003/tool-inputs/`](../build/dependency-fixtures/fixture003/tool-inputs/).
These source locations are **new tooling**, not files from upstream baseline
`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; citations below refer to the recorded
checkpoint unless a later correction is explicitly identified.

| Input | Initial reviewed SHA256 |
| --- | --- |
| `integrity.py` | `2243be3490ce2b46c7c9200562a7c3e8d177544fff913f5535a8e7239fe31d75` |
| `integrity_model.py` | `ac96ed1946ee275094606242dfdeb0b12f0e13193b086711c808e031e57c973b` |
| `gradle_fixtures.py` | `b6322cebf4ccf50dc94fd7678328de0d16a1f1bbb573665a191efa58034963ed` |
| `resolve-graphs.init.gradle` | `cda4bb194b556ed77587498f1637e859394ed69d85f635105ae2a2ccaccfcb5c` |
| `test_integrity.py` | `8ca7c57a8ab624d9ef425785d646af80c77b660ac8d873b89c616b4fcbd3209f` |
| `README.md` | `3778e9fa6fa988d718f2e3f219af2d7e62292b429c17a82eab18b68e5c66cf04` |

The JSON companion records exact executable review commands, their inspected
results, archive manifest hashes, initial test names, the counterexample, and
scope exclusions. Archived historical helper copies are evidence, not current
instructions or policy to execute automatically.

## Implementation-level coverage

### Snapshot, command, orchestration and candidate review

Reviewed [`integrity.py`](../../../../scripts/dependencies/integrity.py),
including every principal execution path:

| Symbols / lines | Review result |
| --- | --- |
| `is_integrity_path`, `_selection_roots`, `selected_inputs`, `source_digest`,50–104 | Source, mutable XML/locks and empty source-directory topology are separate. Selected symlinks fail; named private inputs, caches and build outputs are excluded. Current dirty bytes, not just HEAD, are hashed. |
| `expected_source_projects`,107–135 | Independent expected owners/builds are derived from this repository's literal include/rename idiom. Computed or unfamiliar topology fails rather than being silently guessed. This is intentionally not a general Gradle parser. |
| `_new_workspace_path`, `snapshot`, `load_workspace`, `check_source`,138–204 | New external directory, no Git-worktree reuse, exact post-copy/source hash and topology comparison, host/source/build identity, no independent-trust assertion. |
| `validate_scheduled_tasks`,211–231 | Required acquisition owner/aggregate tasks must be present. Library/sample compilation is not an acquisition task. Convention-plugin build prerequisites are allowed only in the explicit source scope; publish/release/deploy task names are rejected. |
| `validate_graph_tree`,234–291 | Fresh run/mode/host/runtime/digest, exact owner project directories and included-build accounting, owner validation, finalized lock equality and external trust-entry presence. Unsupported whole-build policy/trust/settings/detached flags must remain false. |
| `build_command`,294–317 | Fixed strict-verification acquisition task, one worker, no configuration cache. Bootstrap alone receives both writers; check has neither. Installed Gradle override is fixture-only; real-source candidates use the copied wrapper. |
| `_environment`,320–337 | Private HOME and Gradle cache; inherited credential/Gradle/JVM override variables omitted. Explicit existing SDK paths are retained, not dumped. |
| `_bounded`,340–384 | POSIX process group; common monotonic deadline; at least8GiB reserve; no launch after deadline/low disk; TERM then KILL cleanup. Stop reasons are retained and cannot certify a negative case. |
| `check_review`, `exclusive_workspace`, `run`, `_run_locked`,391–473 | Matching explicit review for check, exclusive reservation, immutable run ID. Source and finalized XML/locks are captured after process exit. Nonzero/stop reason, changed check integrity, or incomplete graph prevents success. A replaced reservation is not silently deleted. |
| `merge_files`, `review`,476–549 | New-file-only deterministic reconciliation, conflicting SHA rejection, unchanged inputs, complete actual acquisitions before explicit registry-TOFU acceptance. Root review requires separate root/composite and standalone acquisitions, not assumed trust inheritance. |
| `main` / signal handling,552–612 | Explicit subcommands and acquisition limits; exit status follows actual completeness/selected-case outcome, not XML existence. No publishing command is provided. |

The marker is an accidental-misuse interlock, not an authenticated manifest or
hostile-code sandbox. Topology restrictions intentionally require maintenance
when settings or target layout changes.

### Exact lock/checksum and graph model

Reviewed [`integrity_model.py`](../../../../scripts/dependencies/integrity_model.py),
including path/read/write/hash helpers, host routing, lock parsing/equality,
verification XML parsing/merging/serialization, artifact validation and complete
owner receipt validation.

- **Lines60–145:** reject relative-path escapes, drives/URLs, controls and
  symlink components through `confined`; bounded regular reads check
  inode/size/mtime before and after; new writes use same-directory temporary
  data, fsync and a non-overwriting hardlink. Leaf-file helpers alone are not a
  race-resistant descriptor-relative filesystem sandbox.
- **Lines148–241:** no unknown-host fallback; owner-local host lock path;
  per-configuration exact module/version sets; duplicate/conflicting and
  empty-versus-populated state rejected. Added/removed/transitive modules are
  not silently accepted; external SNAPSHOT coordinates fail.
- **Lines247–328:** exact verification namespace/structure,
  `verify-metadata=true`, `verify-signatures=false`; one lowercase SHA256 per
  artifact; no alternatives, `also-trust`, wildcard/broad exemptions,
  ignored exceptions, DTD/entities or fabricated signature trust. Conflicting
  candidate digests never become a set of acceptable alternatives.
- **Lines332–356:** artifact outputs must belong to selected external modules;
  hashes/sizes/variants and directory manifests are checked. Provenance is
  explicitly `artifact-view-output-unclassified`, not registry-original bytes.
- **Lines359–469:** complete owner, runtime, source identity and strict policy;
  every inventoried configuration accounted for exactly once; unresolved
  edges/failures/drift fatal; exact project locks; explicitly **unlocked**
  buildscript scope. Public synthetic script roots are accepted only for the
  exact owner/configuration/root basis and cannot become arbitrary dependency
  targets or substitute for unknown external components.

Selected component/edge endpoint consistency is checked, but the receipt is not
an independently authenticated proof of all graph edges or root reachability.
The producer's actual `allComponents`/`allDependencies` traversal was separately
reviewed and the fixture edges inspected. No current producer omission was
demonstrated; stronger receipt reachability checks remain a possible follow-up,
not a claimed Gradle-enforcement vulnerability.

### Gradle producer

Reviewed [`resolve-graphs.init.gradle`](../../../../scripts/dependencies/resolve-graphs.init.gradle)
in full, including:

- Actual Gradle9.7.1/JDK17/host gates and explicit workspace/run/mode/digest
  identity; strict verification and exact bootstrap/check writer interlocks
  (44–107).
- Safe labels and scoped paths; bounded/sanitized **fixture-only** exception
  messages; real-source exception receipts carry cause types rather than raw
  private messages (29–42,63–80,131–150).
- Regular and directory artifact hashing, symlink/special-file rejection,
  before/after identity checks, entry limits and create-new receipts (152–204).
- Public changing-metadata/declaration/SNAPSHOT guards and owner-local
  `LockMode.STRICT`/`lockAllConfigurations`; not the incompatible combination
  with `failOnChangingVersions` (213–303).
- Named project/buildscript inventory; exact public script-root identity;
  components, selected and unresolved edges, external-only lenient artifact
  views. **Leniency collects failures; it does not make them successful**
  (304–375).
- Final inventory drift/owner completeness, explicit included-build dependencies
  and aggregate failure on incomplete receipts. Settings inventory remains
  diagnostic; unsupported coverage flags stay false (382–451).

Changing-version receipts describe observations through installed public guards,
not an attestation of an internal final Gradle flag or protection against a
hostile later build rule. Real mutable-metadata/declaration fixtures are still
needed.

### Fixture generation and observation

Reviewed [`gradle_fixtures.py`](../../../../scripts/dependencies/gradle_fixtures.py),
including deterministic ZIP/POM/Maven metadata generation; exact trust
construction; case mutations; workspace marker/review; failure collection;
classification; subset scheduling; and stop/finalization paths.

- JARs contain only deterministic harmless `fixture.txt`; no compiled code.
  Wrong-hash cases alter fixture bytes, not the accepted digest.
- Parent1.0 requests leaf`[1.0,2.0)`. Strict drift changes the root constraint to
  leaf1.1 while preserving leaf1.0's lock. **Both versions' JAR/POM hashes are
  already known**, separating a lock conflict from missing checksum trust.
- A selected negative always includes known-good bootstrap and baseline.
  Every case uses a new task workspace/cache; one deadline spans the sequence.
  Unexpected outcomes stop the subset; they are not retried or renamed a pass.
- The transitive observer (241–299) requires the exact three parent/locked/root
  unresolved edges, exact typed conflict and explicit lock-origin message,
  exact old configuration lock, known leaf1.0/1.1 bytes and XML hashes, and no
  unrelated configuration/artifact failure. Archived002 and fresh003 match.
- The other generic lock branch lacked those causal checks; see the finding
  below. Existing checksum classifiers were checked against actual002's
  typed target failure and exact report values, not just its nonzero exit.

## BUILD007-REVIEW-001 — unrelated failures accepted by generic lock cases

**Priority:** Medium. **Evidence status:** confirmed-test, offline synthetic
counterexample. **Affected checkpoint:**003. **Location:**
`gradle_fixtures.py:203–238,302–315,344–348`.

**Root cause.** `failure_evidence` combines exception types and text across
configurations/logs. The generic branch accepts either an exception-name suffix
or any occurrence of `dependency lock|locked to version|lock state`. It does not
require the expected owning configuration or missing/added/removed module
discrepancy, and it does not exclude unrelated failure.

**Executed reproduction.** The reviewer called the actual fixture creator,
failure collector and classifier on temporary synthetic owner/invocation
receipts with exact source/host identity and unchanged XML/lock state. The only
failure was:

```text
type: java.io.IOException
message: Could not read lock state diagnostic: unrelated I/O failure
synthetic process exit: 1
```

All four cases returned `actual_expected_result_observed=true` and
`result_kind=lock-rejection`:

1. `missing-host-lock`
2. `missing-configuration-lock`
3. `added-dependency`
4. `removed-dependency`

The exact command and output are retained in the companion JSON. No Gradle was
started and no real failure was fabricated into an archived result. This proves
a **classifier logic defect**, not a production dependency-verification bypass.
The original115 tests passed because they did not cover this counterexample.

**Impact.** A future negative-fixture run can be reported as proving the intended
lock behavior when an unrelated I/O/configuration failure explains the exit.
These four cases were not executed in001/002/003, so no reviewed actual pass
needs retraction.

**Recommendation.** Require exact Gradle9.7.1 cause type and exact owner/config
plus the case-specific lock discrepancy and unchanged known fixture state.
Reject additional unrelated failures. Unknown runtime shapes remain unverified;
do not infer a correct matcher from internal-class names alone.

**Required tests / risk.** All four phrase-only counterexamples must reject;
wrong owner/config/module and extra network/checksum/artifact failures must
reject. Then schedule real bootstrap/baseline and each negative with fresh
cache, unchanged integrity and no stop reason. Synthetic parser tests are not
those actual Gradle runs. Do not rewrite historical receipts or close BUILD-007.

**Coordination.** The reviewer reported the finding to the owner and lead. The
lead authorized a narrow owner repair after immutable003 archival. The initial
counterexample and reviewed hashes remain preserved here; post-repair
verification is recorded separately, not retroactively applied to003.

### Coordinated checkpoint004 correction and independent recheck

[`checkpoint004/archive-manifest.json`](../build/dependency-fixtures/checkpoint004/archive-manifest.json)
binds eight immutable files, including the exact six helper inputs, owner test
log and checkpoint. All eight hashes and six preserved historical receipt
hashes were independently checked. The checkpoint SHA256 is
`33e2e107e98dd84fcc71e9a9719818b0ff38440a006e799824da061e030338f0`.

The corrected `gradle_fixtures.py` SHA256 is
`ea7854ce2372796960c287b22c86853d4a2b60c4ff18ae6cfbaf2d4aa61df50f`.
The reviewer examined the full003→004 delta, especially `_exact_lock_error`,
`_fixture_selected_modules`, `exact_lock_case_evidence` and `classify`
(004lines310–517):

- Removes the generic text and exception-suffix fallbacks entirely; unknown
  cases remain unverified.
- Pairs exact exception types with exact messages for the intended owner and
  configuration. Unknown wrappers, extra causes and unrelated failures reject.
- Checks one expected owner and exact configuration inventory; strict owner
  policy; case-specific absent lock/configuration or added/removed module set;
  unchanged exact build/settings/repository bytes and known verification XML.
- Requires the relevant selected modules and direct/constraint edge set for
  stale-lock cases. The old text alone cannot supply missing state evidence.

Independent validation used the **frozen004 copy**, not the concurrently edited
future005 source:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s docs/development/evidence/build/dependency-fixtures/checkpoint004/frozen-inputs/scripts/dependencies \
  -p 'test_*.py' -v
```

Result: **146 tests,0 failures/errors,2.339s,exit0**. Replaying the original four
counterexamples returned `unverified` in every case. A separate independent
matrix used fuller synthetic owner/configuration receipts: four synthetic
positive controls and24 rejected perturbations spanning all four cases and all
three old phrases, wrong exception package, additional I/O failure and timeout.

These positive shapes are **synthetic inputs derived from inspected class
templates**, not observed Gradle producer behavior. No missing-host/config,
added or removed actual fixture ran. The finding's demonstrated false-positive
logic is corrected and offline-rechecked; its runtime coverage is still pending.

The lead separately authorized the one-line `integrity.py:50–59` addition of
`kotlin-js-store` to selected snapshot roots. Driver SHA256 is
`e36f7a9994de7cc48f0c253082eb01022b59cd8d32df2f28f69f7c443c25bff6`.
Four added tests verify JS/Wasm lock copying as **immutable source**, detection
of added/changed locks, and continued exclusion of private files/node_modules.
This source-selection repair does not certify Yarn/npm artifact provenance or
install npm/Gradle verification policy.

## BUILD007-REVIEW-002 — HOME is not JVM cache-home isolation

**Priority:** Medium. **Evidence status:** confirmed-test for the effective JVM
property; cache-write impact remains a risk. **Affected checkpoint:**004 and
earlier. **Location:** `integrity.py:320–337`, `_environment`.

The build owner identified that setting `HOME` and `GRADLE_USER_HOME` does not
necessarily set JVM `user.home`. The reviewer independently reproduced this
with the existing **JDK17.0.20**, frozen004 environment generator, a temporary
candidate, and a15-second-bounded direct
`java -XshowSettings:properties -version` probe:

| Check | Observed |
| --- | --- |
| Environment HOME is candidate-private | true |
| JVM user.home is candidate-private | false |
| JVM user.home matches existing account home | true |
| Probe exit |0 |
| Gradle/plugin/Native invocations |0 |
| Actual shared-cache writes proven |false |

Only selected booleans and Java version were exported, not raw machine
properties. An initial unpinned reviewer probe did not satisfy the required
JDK17/property assertion; explicitly selecting the already inspected JDK17
produced the result above. No source/archive change made that probe pass.

**Root cause / impact.** The environment generator lacks JVM-home fencing and
effective-runtime verification. Plugins or Kotlin/Native/daemon components
deriving cache locations from `user.home` may use account-shared paths despite
private environment HOME. This is a preflight isolation gap, not evidence that
the plugin-free001/002/003 fixtures wrote to shared native/plugin caches.

**Recommendation / required tests.** Fence task-owned JVM/native/compiler cache
paths, strip inherited overrides, verify effective runtime values before source
resolution, and test symlinks/quoting/reuse/override cases. A direct-JDK fix must
then be checked in a separately scheduled actual Gradle invocation; real
Kotlin/Native/plugin cache behavior and other hosts remain separate gates. This
is not a claim of sandboxing hostile build scripts or arbitrary descendants.

**Coordination:** the lead required a separate cache005 checkpoint after
immutable004. Its source/offline/direct-JDK recheck is complete below. The separate
passive runtime observer was subsequently reviewed; its001 identity-gate defect
and independently rechecked observer-only002 repair are recorded below. Only the lead can
authorize an actual launch after independent recheck.

### Coordinated checkpoint005 correction and independent recheck

The immutable
[`checkpoint005/archive-manifest.json`](../build/dependency-fixtures/checkpoint005/archive-manifest.json)
binds eight files, including the six helper inputs, owner test log and checkpoint.
The reviewer verified all eight hashes, live/frozen input equality, and the
separately bound owner direct-JDK receipt and probe source. Checkpoint SHA256 is
`880026493b933ed9d1e665520fdc576fc056337d152ecefce03020518dcc1bf0`;
archive-manifest SHA256 is
`fd8c916a98692dd67dfe732a9ada03bc7bb208f201719616801c28a848ec5667`.
The exact six input hashes and full probe commands/results are in the JSON
companion. The004 classifier is unchanged.

Reviewed changes in the frozen005 copies:

| File / lines | Source-confirmed change and boundary |
| --- | --- |
| `integrity.py:320–348`, `_environment` | Generates exact `JAVA_TOOL_OPTIONS` internally; does not inherit them. Sets four private JVM properties and ten private environment paths. Quotes space-containing paths; rejects quotes, backslashes and controls before directory creation. Inherited JVM/Gradle overrides and credentials are omitted. |
| `integrity.py:351–401`, `_bounded` | Adds a create-new launcher-PID context receipt, explicitly **not** Java identity evidence. Receipt-write errors remain inside process cleanup. The mocked write-failure/cleanup regression passed; no actual Gradle cleanup was exercised by this reviewer. |
| `integrity_model.py:21–38,378–388` | Complete owner receipts now require exact `runtime_isolation` properties/environment. Wrapper-client observation and actual non-Gradle cache-use flags must remain false. |
| `resolve-graphs.init.gradle:81–107,256–265,328,421` | Checks actual Gradle JVM/environment paths before setup and at owner boundaries; writes a separate PID/runtime observation. These new Groovy/Gradle guards are **source-reviewed, not compiled or executed**. |

The four JVM properties are `user.home`, `java.io.tmpdir`, `gradle.user.home`
and `kotlin.daemon.runFilesPath`. Environment paths are `HOME`,
`GRADLE_USER_HOME`, `KONAN_DATA_DIR`, `TMPDIR`, `TMP`, `TEMP`, and the four
`XDG_CACHE_HOME`/`XDG_CONFIG_HOME`/`XDG_DATA_HOME`/`XDG_STATE_HOME` values.
Each maps to an exact candidate-private location; merely setting a variable is
not proof that every plugin or subprocess uses it.

Independent offline command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s docs/development/evidence/build/dependency-fixtures/checkpoint005/frozen-inputs/scripts/dependencies \
  -p 'test_*.py' -v
```

Inspected result: **157 tests,0 failures/errors,2.408s,exit0**. Added checks cover
private paths, inherited override removal, safe quoting, unsafe-path/symlink
rejection, launcher-receipt failure cleanup, and rejection of missing/foreign
runtime observations or overbroad cache-use claims. These are Python, mocked
process and source-assertion tests, not executed Gradle guards.

The reviewer additionally inspected and ran the bounded
[`RuntimePathProbe.java`](../build/dependency-fixtures/checkpoint005/RuntimePathProbe.java)
source launcher with the existing `/usr/lib/jvm/java-17-openjdk-amd64/bin/java`,
`-Xmx64m`, a15-second timeout per probe, and the frozen005 environment generator.

| Temporary candidate | Selected property/environment/JDK checks | Exit / elapsed |
| --- | --- | --- |
| `plain-candidate` |15/15 true |0 /0.795s |
| `candidate with spaces` |15/15 true |0 /0.706s |

Only the selected booleans were exported; raw stderr, environment and machine
properties were not archived. Java executable and probe-source hashes were
checked before/after. These are **actual direct-JDK observations**, not Gradle,
wrapper-client, daemon, compiler, Kotlin/Native or plugin-cache observations.
No `jcmd` attachment or actual shared-cache write was performed/proven.

Historical001/002/003 receipts remain unchanged and were revalidated with their
earlier frozen parser, not retrofitted to satisfy005's new runtime requirement.
The fix addresses the observed selected-path gap; it is not an OS sandbox,
production dependency verification or evidence that unexecuted tools consume
only those caches.

## Separate passive runtime-witness001 review

This is a new helper, not a change to the frozen six005 inputs. Its
[`archive-manifest.json`](../build/dependency-fixtures/runtime-witness001/archive-manifest.json)
SHA256 is `5025c8ace0bbbdd5a2300df2164ed97b06a3236a8ea4b8ab4a4ad93d21724f59`;
checkpoint SHA256 is
`ef15795f5fcf61c3f395c650099dc709ccba24658dbb7ba8f7ab19edb9c4fac2`.
All six archive entries were independently hash-checked.

| Frozen observer input | SHA256 |
| --- | --- |
| `runtime_witness.py` | `ad9cac992f60c66cdf2a2cee8158080d6542996993f1b0659992fbff38af286d` |
| `test_runtime_witness.py` | `33fe3028a8c11cefe8361fa96e8240b3e34d9c6581cabf2be0a00269bcf7407c` |
| `runtime-witness.md` | `dcfc268c168ad2b74fd91b19d7ba8a367f308db487efb12019a091b9d25503e8` |

The reviewer read the entire550-line helper,500-line test file and130-line
proposal before running the offline suite. Important execution boundaries:

| Observer001 symbols / lines | Review |
| --- | --- |
| `fixed_arguments`, path/JSON/frozen-input helpers,54–94 | Exact six-case sequence, new external output, bounded regular receipts; frozen005 and observer hashes checked before/after the observation. |
| `ProcessIdentity`, `/proc` parsers, `owned_children`,97–168 | UID/live start identity, bounded reads, all bounded client threads' children rather than a global JVM scan. No claim that PID identity alone proves Java. |
| `private_values`, `check_environment`, `check_suite`,171–199 | Exact private selected environment and generated JVM options; suite must be the same-shell sibling with selected Python/JDK, checkout, full fixture CLI and unchanged start identity. |
| `check_java`,202–232 | Candidate cwd, Java executable and suite/client/daemon ancestry checks. **Incomplete actual launcher-target parsing is a defect; see below.** |
| Property parsing and bounded diagnostic,235–326 | Four selected private properties plus validated public Java version; duplicates, missing keys, unsupported continuations/escapes reject. Bounded pipe capture; only the newly created diagnostic child is killed/reaped. |
| `observe_java`,329–352 | Retains a pidfd and rechecks identities/environment before/after one diagnostic. No role retry; failed/exited identities do not become observed. |
| Runtime/subset binding and `witness`,355–526 | Six known cases, separate client/daemon/init receipt, exact expected exits and selected result kinds; missing roles or runtime mismatch prevent complete subset. Full orchestration was source-reviewed, not actually run against Gradle. |
| `main`,529–550 | Fixed public error codes rather than raw exception bodies; incomplete witness returns nonzero. |

The proposal uses `$!` from the exact background suite in the same shell, not a
guessed PID, no-clobber outputs, `set +e` and a final `wait` for the original
bounded driver even if observation fails. Its **`bash -n` syntax check exited0**;
the paired command was not executed. The proposed driver remains at most six
invocations/300 seconds total/90 seconds each/one worker/8GiB reserve. The
observer proposes at most12 diagnostic attempts, each at most5 seconds with a
64MiB Java heap and128KiB accepted diagnostic output. These are not OS sandbox
or RSS limits, and output-limit rejection may retain one read chunk beyond the
acceptance cap before discarding it.

Independent command, using immutable observer and core imports:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=docs/development/evidence/build/dependency-fixtures/checkpoint005/frozen-inputs/scripts/dependencies \
python3 -m unittest discover \
  -s docs/development/evidence/build/dependency-fixtures/runtime-witness001/frozen-inputs/scripts/dependencies \
  -p 'test_runtime_witness.py' -v
```

Inspected result: **76 tests,0 failures/errors,0.180s,exit0**. Four tests launch
tiny task-owned Python children to check capture/timeout/output-limit/nonzero
cleanup; other process and diagnostic records are synthetic/mocked. This is
**not** actual Java, jcmd, Gradle, pidfd/ancestry runtime validation, or private
compiler/native cache consumption.

An additional independent **11-scenario modeled orchestration check** exercised
the real outer `witness` loop, runtime/subset binding and create-new/readback
reporting with process/checkpoint/observation boundaries mocked. One synthetic
complete control was accepted. Missing client, missing daemon, diagnostic
failure, wrong runtime PID, missing runtime receipt, failed fixture subset,
changed core inputs, changed observer inputs, expired window and interruption
all remained incomplete. All11 report readbacks matched. These positive/negative
modeled results are not actual Gradle or operating-system observations.

### BUILD007-REVIEW-003 — argv markers are not the actual JVM entrypoint

**Priority:** Medium. **Evidence status:** confirmed-test, mocked process
records. **Affected checkpoint:** runtime-witness001, not frozen core005 or the
upstream baseline. **Location:** `runtime_witness.py:202–232`, especially217–227.

**Root cause.** Client checking searches `-jar` and compares its suffix. Daemon
checking searches the first `-cp` and compares its value plus the final
`GradleDaemon`/version strings. Neither consumes the Java launcher grammar to
establish that these are the actual target/classpath rather than application
arguments or an overridden earlier option.

The reviewer independently called the real `check_java` with mocked `/proc`
records using the owner's test harness. All six malformed command shapes were
accepted despite otherwise exact synthetic identity/cwd/private environment:

| Role | Accepted counterexample |
| --- | --- |
| Client | A foreign class/main before the expected `-jar` marker; Java would pass that marker and following text to the foreign main. |
| Client | Earlier `--module` main before the expected `-jar` marker. |
| Client | Earlier `--source 17` source launcher before the expected `-jar` marker. |
| Daemon | A foreign class/main before the final expected daemon-main/version strings. |
| Daemon | Earlier `--module` main before the expected classpath/main strings. |
| Daemon | A second, foreign `-cp` after the expected first classpath; the later classpath overrides it. |

The exact commands and outputs are in the JSON companion. No Java/jcmd/Gradle
process or real unrelated attachment was created. The demonstrated defect is
**overacceptance by the identity gate**, not an observed cross-task attachment,
compromised distribution or dependency-verification bypass. Same-shell suite and
candidate ancestry restrictions still apply.

**Recommendation / required tests.** Consume the entire command under a strict
installed-client prefix and bounded daemon JVM-option grammar; require exactly
one actual known entrypoint/classpath. Reject earlier class/module/source/jar
launchers, duplicate/overriding classpaths and unknown options. Preserve supported
synthetic positives and reject all six counterexamples before any diagnostic.
Recheck an immutable observer-only002 checkpoint; do not alter six005 or loosen
checks just to fit a future runtime.

**Initial coordination / status.** The owner and lead were notified before
launch; the owner accepted **HOLD** and prepared an additive observer-only
repair. Witness001 remains immutable. The subsequent002 review below lifts the
source/offline objection only; it is not an actual runtime or release pass.

### Observer002 correction and independent recheck

The reviewer examined the complete001→002 helper/test/document diff. The
[`observer002 archive`](../build/dependency-fixtures/runtime-witness002/archive-manifest.json)
SHA256 is `fa37a76f5e49b68813756e23165ef7f7179a0203100efbe5e42b87737d5d85f8`;
checkpoint SHA256 is
`2726f5f43ed20a6179ed99227f7c33fe02adb049bb92899365bf3f8efb041dbd`.

| Frozen observer002 input | SHA256 |
| --- | --- |
| `runtime_witness.py` | `8cd06b303fb0e602596938cdb8cf4b7a19d37318f4728d1c09b2a252e8ff9085` |
| `test_runtime_witness.py` | `f966a0f58c5cf06a938a55a39b045ea1e582f28ac820508822f834078748fc46` |
| `runtime-witness.md` | `3a045b10ceb275ec6fcd51f0d6777ef3793a2ab882b737cb633c8c5ae97f8c13` |

- **002lines202–207,281–286:** the entire client argument vector must match the
  inspected installed launcher: selected Java, heap flags, exact instrumentation
  agent, appname, actual `-jar` target and exact frozen-driver arguments. A later
  matching suffix is insufficient.
- **002lines210–268,287–291:** `daemon_entrypoint` consumes every argument before
  one actual daemon main/version. It requires one exact classpath and agent,
  bounded allowed JVM options/properties, and rejects duplicates, earlier
  entrypoints, alternate launch modes, argfiles, unknown options and overriding
  classpaths. Unknown real producer shapes must remain unverified.
- The observer's process ancestry, pidfd checks, selected-property filtering,
  one-attempt rule, outer binding/reporting and scoped cleanup are unchanged.
  No core005 or existing evidence bytes were changed.

Independent immutable command:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=docs/development/evidence/build/dependency-fixtures/checkpoint005/frozen-inputs/scripts/dependencies \
python3 -m unittest discover \
  -s docs/development/evidence/build/dependency-fixtures/runtime-witness002/frozen-inputs/scripts/dependencies \
  -p 'test_runtime_witness.py' -v
```

Inspected result: **91 tests,0 failures/errors,0.210s,exit0**. The15 added tests
cover the reported entrypoint/classpath defects, additional launch modes,
unknown/duplicate options, foreign agents and a supported **synthetic** daemon
option control. Four tiny Python children run; no Java/jcmd/Gradle or network.

Two additional independent checks passed against frozen002:

1. **14 identity scenarios:** two supported synthetic client/daemon controls
   accepted; all six exact original counterexample shapes rejected; the same
   six preemptions/overrides applied to the newly valid002 bases also rejected.
   Thus rejection is not explained only by changing the positive test prefix.
2. **11 modeled outer-loop scenarios:** the original modeled control and ten
   missing/failure/mismatch/drift/timeout/interruption checks were rerun; only
   the synthetic complete control was complete, and all report readbacks matched.
   Process/checkpoint/observation boundaries remain mocked.

All **seven002 archive entries**, three live/frozen observer files, six005 inputs
and the complete001 archive were hash-checked. The reviewer read the owner's
[`launcher inspection`](../build/dependency-fixtures/runtime-witness002/launcher-identity-inspection.json)
and independently matched the installed launcher script, client-services JAR
and enclosed `DefaultDaemonStarter.class` hashes. The launcher script itself was
read; the reviewer did **not** rerun `javap`, Java or a Gradle process. The owner's
bytecode inspection is supporting source evidence, not executed producer-shape
or cache-use proof.

The paired shell proposal is byte-identical to001 and independently passed
`bash -n` again; script SHA256 is
`ce0899e4576db9c0944a46b76afc6853815edee7d24dc73fc91b36586c214de6`.
It remains unexecuted by this reviewer.

**Conclusion:** the demonstrated argv defect is source-corrected and
offline-rechecked. **GREEN is limited to these exact observer002 inputs and
source/offline checks.** This was sent to the build owner and lead. At handoff,
the lead's separate device-run hold required a fresh explicit GO for the single
paired fixture004 batch. No review statement lifts scheduling/publishing
containment or certifies actual client/daemon observations.

**Residual limits even after a parser repair.** `jcmd` addresses a numeric PID,
not the retained pidfd. Pre/post identity checks reject observed exit/reuse but
do not make attachment an atomic kernel transaction. The diagnostic may start
HotSpot's attach listener/create a socket; it is not a zero-side-effect read.
Actual process shapes may fail the deliberately strict guards and must then
remain unverified. The installed-distribution fixture never runs the wrapper;
wrapper, compiler/native/plugin cache use, real dependency acquisition and
release gates remain outside this witness.

## Actual archived evidence versus offline checks

| Batch | Actual invocations / elapsed | Independently inspected conclusion |
| --- | --- | --- |
|001 | Bootstrap only;8.547s suite | Gradle ran and wrote XML, but the unmodeled buildscript root failed the owner/aggregate. Project graph resolved; no finalized project lock. Graph/lock/checksum flagsfalse, no baseline or negative case. |
|002 | Bootstrap0, baseline0, wrong-JAR1, drift1;34.756s | Bootstrap/baseline graph and exact locks validate. Wrong-JAR failure has the actual verification exception and exact expected/actual SHA. Original drift observer did not match lock-origin wording; original subsetfalse and driftunverified remain unchanged. |
|003 | Bootstrap0, baseline0, drift1;25.722s | New exact drift observer ran on fresh inputs and observed the expected typed3-edge conflict with known hashes and old lock. Selected subsettrue; full suitefalse. Wrong JAR was not rerun. |

All inspected owner receipts record **Gradle9.7.1/JDK17.0.20/linux-x64**. The
commands use strict verification, no configuration cache and one worker.
Bootstrap has both writer flags and never claims checksum enforcement. Ordinary
baseline has no writers and exact unchanged XML/lock hashes. Failed invocations
retain false completeness flags.

Specific independent checks:

1. Original/archived entries match exact SHA256; only the declared task-path
   replacements differ in nine log/HTML pairs. Sanitized text was recomputed
   from retained originals, not accepted on assertion alone. HTML is inert text.
2. Candidate digests recompute from source hash maps/topology; copied tool/source
   bytes and deterministic binary originals match. No cache or JAR payload was
   added to the archive by this review.
3. Reconstituted initial XML matches the original pre-run receipt hash. Final
   and captured XML/locks match their invocation hashes. All eight XML trust
   entries match the controlled generator; no broad or alternative trust.
4. Four complete archived graphs were reparsed with exact inventory and locks,
   and their full normalized summaries/hash maps match saved summaries.
5. Actual002 wrong-JAR evidence names `leaf-1.0.jar`, expected SHA256
   `0dccd3ab1acf0ca5a80d0a6fdd567912f9f573deba48936c6f0c04bc73d2ed89`,
   actual SHA256
   `28361d21ed6ec9abb39422c8778bf4b67c1762073209ab9c904cade8ae23a0b1`,
   and `DependencyVerificationException` in the target configuration.
6. The exact002 post-hoc and003 classifier results were recomputed read-only
   using frozen003 helpers and original retained fixture workspaces. They match
   saved observations. Original suite hashes remained unchanged. This is
   re-analysis of actual evidence, not new Gradle execution.
7. Drift receipts contain unresolved constraints even though an artifact view
   observed leaf1.1. The failed graph is **not** promoted to completeness based
   on artifacts, XML, or the presence of a correctly hashed later version.

The first reviewer archive-check script stopped on Python tuples versus
JSON-decoded lists when comparing equal graph summaries. Normalizing through
JSON fixed that reviewer-only comparison; the next check passed. No archive,
source or producer receipt changed to make the check pass.

## Offline validation performed

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s scripts/dependencies -p 'test_*.py' -v
```

Inspected result: **115 tests,0 failures/errors,0.957s,exit0**. Tests cover exact
metadata, conflicting merges, source/topology/path drift, lock equality,
owner/included/configuration accounting, script roots, writer/review commands,
fresh cache, deadline/reserve rejection, timeout nonacceptance and narrow drift
matching. These are offline Python/synthetic/mocked tests, **not** actual
dependency resolution or process-termination tests.

Two separate reviewer scenarios mocked only the runner's exit as0 while leaving
valid verification XML and no graphs. Both bootstrap and check captured XML but
reported `IntegrityError` for the missing graph receipt; graph/lock/checksum
flags remainedfalse. This directly checks the outer success boundary without
launching Gradle.

## Historical remaining limits before actual004

- **Do not close BUILD-007.** Ordinary root and convention verification XML were
  absent at inspection; these helpers install policy only for explicit
  init-script invocations. No ordinary-build/CI policy is established.
- Real nativeCmpkit root/composite and standalone convention graph acquisition,
  exact trust reconciliation and owner acceptance are separate work. Fixture
  bytes are not those dependencies and confer no provenance/advisory/license
  clearance.
- Strict project locking does not lock buildscript provider versions. Settings
  script/plugin and detached configurations lack complete version-lock coverage.
  Project/file/local outputs and non-Gradle downloads are outside external trust.
- Checkpoint004 does not fence JVM `user.home`. The005 correction is
  source/offline/direct-JDK checked, but its Gradle guards are uncompiled and
  unexecuted. Actual wrapper/client/daemon observations and tool-cache
  consumption remain separate requirements before real-source acquisition.
- No actual cases in001–003 for: wrong POM SHA, missing hash, missing host/config
  lock, dynamic-transitive freeze, added/removed dependency, included-root check,
  or standalone wrong hash. Real changing-metadata/declaration cases are also
  required. Post-repair synthetic tests cannot fill these gaps.
- Windows execution is unimplemented; other host profiles were not run by this
  review. Library/device/browser/native/consumer gates remain separate.
- Path/regular-file checks are not protection against arbitrary hostile build
  code or all symlink races. Process-group/time/disk monitoring is not a kernel
  sandbox or proof against detached descendants; actual stop cleanup was not
  exercised by the reviewer.
- This report does not change the original164 finding records, status ledger,
  publication containment, or frozen library source inputs.

At that pre-actual004 checkpoint, the next step was a **fresh lead-authorized** scheduled run for actual runtime
fencing and missing/added/removed lock fixtures using the frozen **observer002**
correction, not observer001. The observer must never start or stop Gradle and
must not attach to unrelated/unverified process identities. The six005 inputs
remain frozen. Preserve negative evidence and only expand claims to precisely
executed cases; this source/offline green is not launch authorization.

## Actual fixture004: independently preserved failure and partial runtime evidence

The [immutable archive](../build/dependency-fixtures/fixture004/archive-manifest.json)
is SHA256 `a6ed29cc13e2f5a2c73245f714087c3ee22dee7f5f6355425525476fdfad793e`;
its [verification receipt](../build/dependency-fixtures/fixture004/archive-verification.json)
is `bc86dba48aeefbeec040c346aa34d59e4e9b5ff421faa1fb4e892726d3381648`.
The suite ran once for26.715s and exited1; the witness ran26.756s and exited1.
Only bootstrap, baseline and missing-host ran (exit0,0,1); the remaining three
selected lock negatives were not executed. No per-invocation timeout/disk stop
was reported. The original suite and witness were not rewritten.

Read-only Python revalidation independently checked:

1. All66 original/archive pairs, including exactly three declared log path
   substitutions;73 archive file bindings; six derived XML/JAR-hash records;
   nine frozen input copies and171 before/after unchanged paths. Reconstituted
   initial XML is explicitly derived, not presented as a retained original.
2. Original candidate source/topology identity, captured XML/locks, and bootstrap
   and baseline complete graph summaries using **frozen005**, not live006.
3. Exact original classifier replay: baseline remains `strict-acceptance`;
   missing-host remains `unverified`. All earlier state/owner/configuration guards
   passed before `_exact_lock_error:333` returnedfalse and
   `exact_lock_case_evidence:422` returnedNone. Actual cause types include
   `TypedResolveException`, absent from005's explicit wrapper table. This is a
   conservative false negative, not permission to accept generic lock text.
4. All three init receipts contain005's exact four JVM and ten environment-path
   observations. Together with complete owner graphs, these establish actual
   selected Gradle-JVM guard execution, not merely a source/JDK probe.
5. Each of three external **installed-distribution client** observations matches
   its launcher/result/runtime hashes and selected values. Each daemon record is
   only `{observed:false}`; no daemon attachment attempt is recorded and no
   external runtime-receipt match exists. Do not infer an ancestry, argv,
   timing or property mismatch from unavailable reason data.
6. The owner's completion receipt names the same six client/Gradle-JVM PIDs as
   absent at its recorded time. The reviewer **did not reprobe** those PIDs or
   assert present-day/global process absence.

The verification command installed a Python read-only audit hook and launched
no Gradle, Java, jcmd, network or child process. It made no source/archive changes.
The two external client/JVM roles, wrapper use, actual non-Gradle cache consumption,
production trust and BUILD-007 closure remain separate claims.

## Core006: narrow actual-type correction, independently offline-checked

The [checkpoint](../../../../scripts/dependencies/checkpoint-offline-006.json)
is SHA256 `42df397c9ddc0a7c6419cb1d109a680e2204dba54e78250b3a4e6b8f49fd6f46`.
Only fixture classifier, tests and README changed. Driver, integrity model and
init script remain byte-identical to005. **164 tests passed independently
in2.419s** against the frozen006 copies; this number describes Python tests,
not a change to the original164 audit findings.

`gradle_fixtures.py:310–340` adds exactly the fully qualified
`org.gradle.api.internal.artifacts.ivyservice.TypedResolveException` wrapper and
its configuration-specific **dependencies** message. Unobserved files/artifacts
messages **for that newly added wrapper**, unknown subclasses and extra/unpaired
causes remain rejected; all existing state, ownership, checksum and timeout
guards are retained. Seven new authored tests
cover actual-shaped synthetic receipt acceptance and surrounding negative cases.
An additional independent15-case in-memory matrix passed (one retained actual
pair,14 distinct nonmatches). Three pinned exception class hashes, superclass
links and diagnostic constants matched by Python classfile reading, without JVMs.

All11 checkpoint archive/original pairs and97 before/after paths matched.
The new parser's **read-only post-hoc** interpretation of the retained004
missing-host case exactly matches the owner's additive record. The original
invocation/suite/witness still report their original failure/incomplete state.
This does not establish an executed corrected suite, the other three lock cases,
any external daemon observation, or production/ordinary-build policy.

## Wasm tooling init proposal: root/included lifecycle source review

The [original proposal](../../../../scripts/dependencies/yarn/tooling-receipt-init-proposal.md),
SHA256 `7febc84a82896342a38e42bcd328eb9a77e91e4127577a1b3720c643e9727af1`,
must not be adopted. Its lines72–106 perform root-only home/task checks and a
`CREATE_NEW` receipt before identifying the build; lines108–160 attach listeners
selected only by local task path. The repository explicitly includes
`convention-plugins` in `settings.gradle.kts:5`.

Independent standard-library classfile inspection binds16 installed Gradle
classes/32 methods. Important **bytecode offsets**, not Kotlin/Java source lines:

| Implementation | Inspected consequence |
| --- | --- |
| `BuildDefinition.startParameterForIncludedBuildFrom:1–19` | Creates new included start parameters and copies parent init scripts. |
| `StartParameter` constructor/`prepareNewBuild`; `RunDefaultTasksExecutionRequest.getArgs:0–3` | New task requests are not the root request; the default args are empty. |
| `DefaultSettingsPreparer.loadBuild:33–43` | Executes init scripts for root and included models before finding/loading settings. |
| `ScriptEvaluatingSettingsProcessor.process:35–90` | Constructs actual Settings, invokes `beforeSettings`, then applies its settings script. |
| `DefaultIncludedBuildRegistry.registerBuild:43–60,112–124` | Requires nonnull root build and passes it as the included build's parent. |
| Included-build constructors; `AbstractBuildState.getParent`; `DefaultGradle.getParent:1–34` | Parent survives into the Gradle model; this is source-confirmed, not an observed callback. |

Thus v1 has a concrete included-build rejection path. Duplicate receipt/listener
effects are a conditional secondary risk if its request guard is bypassed;
`CREATE_NEW` would not overwrite a prior receipt. No v1 runtime was attempted.
Ten original API input hashes and ten class/getter bindings also match.

The [separate v2 proposal](../../../../scripts/dependencies/yarn/tooling-receipt-init-proposal-v2.md),
SHA256 `e1697dc6345bc9e5fb4f2b78a2f3ea86f796929184e272fdfc634afbc32d338d`,
is **source-only-green for the scoped correction**:

- Only imports and `beforeSettings` registration are top-level. Exact canonical
  root/no-parent permits root checks; known convention/nonnull-parent returns
  before root gates/writes/listeners; wrong roles and unknown directories reject.
- Root operations follow that classification. Exclusive requested-receipt creation
  precedes listener registration, preventing a second listener set on duplicate
  invocation. Receipts record the bound settings/build identity.
- Both graph and outcome listeners require the identical Gradle instance and
  canonical project root, not merely the same colon-prefixed task path.
- The added `buildPath` getter exists publicly and reads the identity path without
  realizing `rootProject`. KGP properties are checked through reviewed public APIs.
- The root allowlist is still target plus two setup prerequisites; unknown graph
  members fail for review. Convention compilation is outside this root-only
  diagnostic and may execute/use caches; no process-wide allowance is claimed.

The [preservation checkpoint](../build/yarn-fixtures/wasm-tooling-init-scope-checkpoint001.json)
and four original proposal/API/documentation/index bindings independently match.
Original documentation/API success is not retrospectively redefined as scope
or runtime success. JSON key `wasm_tooling_init_scope_review` contains consolidated
class/API evidence, exact inspection commands, static branch review and limits.

No proposal compilation, real root/included callback, task graph, duplicate-write
fixture, Node/Yarn invocation, tooling installation, script suppression, lock
closure, package provenance or library test has been observed by this review.
Fresh `kotlin.user.home` is not all-cache/OS/network isolation. A later bounded
command must retain actual failures and selected process evidence; source-only
green is **not** launch authorization, BUILD-007 closure or a release gate.

### Final companion readback and evidence boundary

The subsequently completed [scope/API companion](../build/yarn-fixtures/wasm-tooling-init-scope-review002.md)
and its [JSON binding](../build/yarn-fixtures/wasm-tooling-init-scope-review002.json)
were independently read back with Python only. Both reported document hashes,
all ten input hashes, four installed class hashes and eleven public abstract
method descriptors match; eight local links resolve. Eleven distinct bound
paths were unchanged before/after that check. The owner's recorded `javap`
success was read, **not rerun** by the reviewer.

This additive readback resolves the earlier timestamped statement that those
companions were still being authored; the original preservation-check result
remains unchanged. The final owner-side tooling/documentation verification
receipt is intentionally separate and may bind these finalized reviewer files
without a circular self-hash. Its future completion is not claimed here.

**Final scoped result:** exact core006 is source/offline GREEN; exact v2 is
source/control-flow/API GREEN. Original004 failure/incomplete evidence remains
intact. Observer003 is **not reviewed or certified** at this handoff. No new
Gradle/JVM/Node/Yarn process, network request, process probe, source/policy edit,
production trust, security/license clearance, BUILD-007 closure, release gate
or diagnostic-launch authorization is supplied by this follow-up.

Final read-only document/hash consistency checks passed: the three original
reviewer findings, all164 original audit IDs, six recorded offline suite counts,
17 historical bindings,29 frozen checkpoint/observer entries,73 actual004
bindings,11 core006 archive/original pairs and21 local Markdown links were
consistent;174 bound paths were unchanged during that check. This is a data
readback, not another164-test execution. The two initial validator attempts
stopped on reviewer-only checkpoint schema/path assumptions (`KeyError`, then
`FileNotFoundError`); both failed outputs are retained separately in JSON. Only
the corrected command passed; no source or evidence was changed to repair it.

This sealed source-review checkpoint does not include the lead's separately
started tooling diagnostic or any later observer003 review. Those require
separate additive records; they must not rewrite this evidence boundary.
