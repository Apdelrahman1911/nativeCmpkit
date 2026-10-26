# BUILD-007: minimum Gradle integrity implementation and verification plan

**Current status (2026-10-25): isolated tooling implemented; BUILD-007 unresolved.**
[`scripts/dependencies/`](../../scripts/dependencies/README.md) now implements
candidate-only acquisition, strict owner/configuration receipts, checksum/lock
reconciliation and bounded controlled fixtures. The latest offline parser suite
has164 tests at core006 (historical005 remains157,004 remains146 and003 remains115).
Actual fixture002 established successful bootstrap/ordinary baseline
and exact wrong-JAR-SHA rejection. Its strict transitive conflict is established
by additive structured analysis, while its original observer/suite exit1 remains
preserved. Fresh003 then passed exactly bootstrap/baseline/transitive rejection,
three invocations in25.722s, not the full suite. Independent review found a
generic-lock false positive in four then-unexecuted cases; a narrow typed/state-bound
repair and offline regressions exist. Actual004 then stopped on its first negative:
missing-host-lock remains **unverified by the original classifier**; the other
three selected negatives never ran. Independently frozen005 adds explicit private JVM/environment paths,
strict Gradle-JVM runtime-observation guards and owned launcher-PID receipts.
Two direct JDK17 probes checked15 selected values each. **Actual004 compiled and
executed the005 init guards in all three invocations**, recording the expected
selected Gradle-JVM/environment paths. External client observations succeeded,
but no external daemon observation/binding or compiler/native cache-use proof
was established. See [persistent fixture evidence](evidence/build/dependency-fixtures/README.md),
the additive [003 archive verification](evidence/build/dependency-fixtures/fixture003/archive-verification.json)
and `scripts/dependencies/checkpoint-offline-{004,005,006}.json`. Their separate
immutable tool archives preserve the classifier/snapshot and runtime-fence scopes.
The additional [passive witness proposal](../../scripts/dependencies/runtime-witness.md)
has108 targeted offline tests at observer003. Its original [witness001 archive](evidence/build/dependency-fixtures/runtime-witness001/archive-manifest.json)
preserves the76-test state that independent review held for a mocked JVM-entrypoint
false positive. The [witness002 correction](evidence/build/dependency-fixtures/runtime-witness002/archive-manifest.json)
parses the complete installed launcher/entrypoint and passed independent offline
review (including14 additional identity scenarios and
11 modeled outer-loop scenarios). Those offline tests launched no Java, `jcmd`
or Gradle; they are separate from the157-test frozen005 core.

The once-authorized paired fixture004/witness002 command subsequently ran:
suite exit1/26.715s and witness exit1/26.756s. Exactly bootstrap, baseline and
missing-host-lock ran (Gradle exits0/0/1), with no timeout, interruption or disk
stop. The witness established all three installed-distribution **clients**, but
attempted no daemon diagnostic. Its discarded candidate-validation errors cannot
be reconstructed from the final generic unavailable-input code. The original
failed classifications and all-false full-coverage flags are preserved in the
[004 archive](evidence/build/dependency-fixtures/fixture004/archive-verification.json):
66 original pairs, six derived records and73 bound files. The exact typed
missing-lock message was rejected because005 omitted the actual
`TypedResolveException` wrapper from its narrow allowlist. The separately authorized
offline corrections are now frozen below; **no additional fixture or source
acquisition is authorized by those repairs**. No unrelated JVM
attachment occurred; all six recorded client/Gradle JVM PIDs were absent at the
recorded completion check, and the Gradle slot was released.

[Core006](evidence/build/dependency-fixtures/checkpoint006/archive-manifest.json)
passed164 offline tests in2.637s and independent source/offline review. Only the
observed `TypedResolveException` plus exact configuration/dependencies message
was added; files/artifacts variants, unrelated causes and arbitrary subclasses
remain rejected. Pure Python inspection of the pinned Gradle classes and a
[read-only replay](evidence/build/dependency-fixtures/fixture004-missing-host-reclassification-006.json)
confirm the retained004 missing-host rejection under the new parser, **not a new
successful fixture or amended original verdict**. The driver/model/init remain
byte-identical to005; its historical receipts are immutable.

[Observer003](evidence/build/dependency-fixtures/runtime-witness003/archive-manifest.json)
passed108 offline checks in0.288s, plus unchanged core006's164 tests in2.807s;
the separate [independent review](evidence/review/dependency-observer003-independent.md)
is GREEN for source/offline only (108 tests in0.273s and17 additional modeled
outer-loop checks), not an actual003 observation. Its six fixed stages/85 reason codes
retain validation counts, each capped at1024, without raw exception/argv/environment
data.26 existing function/class ASTs, including ownership/entrypoint/pidfd/capture
and completion gates, are unchanged. Nine outer-loop tests are **modeled**, not
runtime witnesses. Counters are bounded, unordered and not exhaustive; empty
counters do not establish that no guard failed. Actual004's missing-daemon cause
remains unknown. Fixture005
and root/convention acquisition are still unexecuted/unauthorized.

**Original plan distinction:** this document began as a prospective docs-only
design contract; the remaining sections retain that contract, not a claim all
surfaces/gates exist. No real root/composite or standalone-convention acquisition,
ordinary live locking/verification policy, independent trust, full negative suite
or cross-host gate is established. Baseline findings remain unchanged. The lead
still schedules every Gradle window; containment means no publishing,
deployment, Actions enablement or GitHub mutation.

The first deliverable is **Linux-x64-scoped enforcement with truthful missing-host
gates**, not a claim of complete cross-platform dependency reproducibility. It
must acquire the real root/composite and standalone convention graphs and prove
actual checksum and transitive-lock rejection. Adding an XML file alone is not
an acceptable deliverable.

## 1. Evidence behind the design

- Version-specific Gradle9.7.1 locking/verification documentation and observed
  excerpts are recorded in
  `evidence/build/gradle-integrity-documentation-observation.json`.
- Installed Gradle bytecode was inspected read-only and reproduced, with JAR,
  classfile and disassembly hashes in
  `evidence/build/gradle-verification-writer-inspection.json` and selected methods
  in `gradle-verification-writer-bytecode.txt` in that directory. The verification
  writer uses internal `canSafelyBeResolved()`, a module-component artifact view
  with `setLenient(true)`, and catches configuration-resolution exceptions at
  DEBUG before continuing. **Successful bootstrap and emitted XML do not prove
  complete acquisition.** This observation did not execute Gradle.
- The main build's verification XML applies to the root, subprojects, settings
  and project plugins, `buildSrc` if added, and included builds. An included
  build's own XML is ignored in favor of the main build's policy. Independently
  running `./gradlew -p convention-plugins ...` therefore needs a second XML.
- `lockAllConfigurations()` applies to project configurations, **not** buildscript
  classpath configurations. `dependencies --write-locks` on the root is not a
  whole-build acquisition command. Verification `--dry-run` misses resolution
  performed during task execution.
- `compose.desktop.currentOs` occurs in desktop library tests and both desktop
  sample layers. Hosts can select different **component names**, not just
  classifiers. `DesktopJavaFx.kt` also selects the actual host's classifiers.
  One merged lock state for all hosts can be contradictory.
- Gradle9 disallows resolving another project's configuration from a root task.
  The existing `scripts/audit/export_desktop_runtime_graph.init.gradle` uses
  owner-project part tasks and JSON aggregation. It is a useful ownership
  pattern, **not** a complete graph/artifact acquisition implementation.

## 2. Smallest implementation surface

The table retains the original design contract. Isolated helper commands now
exist, but ordinary root/convention policy and real acquired trust/locks remain
unimplemented. Keep dependency-integrity work separate from library behavior or publishing.

| Surface | Minimum responsibility |
|---|---|
| Root and standalone convention build configuration | Apply ordinary project locking, actual-host selection and strict mode before project configurations resolve; do not rely on an optional init script for normal enforcement |
| `gradle/verification-metadata.xml` | Reviewed checksum allowlist for the entire root composite, including convention/plugin dependencies |
| `convention-plugins/gradle/verification-metadata.xml` | Reviewed standalone-convention trust, reconciled with root without conflicting checksum alternatives |
| Per-project `gradle/dependency-locks/<host>.lockfile` | Actual selected external module versions and explicit empty-configuration state for that project/host |
| `scripts/dependencies/resolve-graphs.init.gradle` | Inventory; owner-project resolution/artifact acquisition; fail-closed root/composite receipt aggregation; no library/sample/native build task dependencies |
| `scripts/dependencies/integrity.py` and offline tests | Bounded/strict receipt and XML validation, conflict-rejecting trust reconciliation, reviewed-manifest checks and isolated negative-fixture orchestration |
| Development evidence | Inputs, real invocations, configuration-level results, candidate hashes/review and each negative test's precise rejection |

Use public Gradle APIs; do not import `canSafelyBeResolved()` or other internal
classes just to reproduce the writer's omissions. Configuration-cache
incompatibility must be declared by the acquisition tasks. They produce a fresh
observation on every invocation, not `UP-TO-DATE` or remote-build-cache evidence.

### Ordinary project locking

Use the inspected public API in root and convention build policy:

```kotlin
dependencyLocking {
    lockAllConfigurations()
    lockMode.set(LockMode.STRICT)
    lockFile.set(layout.projectDirectory.file("gradle/dependency-locks/$host.lockfile"))
}
```

`host` must be derived from the actual JVM OS/architecture, normalized to exactly
`linux-x64`, `linux-arm64`, `macos-x64`, `macos-arm64` or `windows-x64`. Unsupported
hosts fail. An optional expected-host assertion may reject a mismatch, but must
not override the actual host or emulate another host's graph. There is **no
Linux/default fallback** for a missing host lock. Empty required configurations
also need recorded lock state; a zero-dependency project is not simply omitted.

Keep each project's locking provider local: root `allprojects` does not include
the convention composite automatically, and its policy must also work when
the convention build is invoked independently. Any graph-changing target/mode
settings must be represented in the receipt and either proven graph-invariant
or assigned a separate deliberate lock profile. Never silently overwrite one
profile with another. This includes new conditional device-test source sets,
browser test-source topology, KGP/Compose feature flags and future target changes.

### Buildscript, settings plugins and detached configurations

This boundary must be visible rather than hidden under “all configurations”:

1. Explicitly inventory each project's `buildscript.configurations` and the
   actual plugin/settings requests, in both invocation modes. Root and standalone
   script classpaths can resolve before ordinary project policy is applied.
2. The documented buildscript activation is stage-one configuration, for example:

   ```kotlin
   buildscript {
       configurations.classpath {
           resolutionStrategy.activateDependencyLocking()
       }
   }
   ```

   Gradle normally writes `buildscript-gradle.lockfile`. Do not claim that the
   project `LockMode.STRICT` or project custom lockfile automatically configures
   this separate script provider. The inspected public `ScriptHandler` does not
   supply a demonstrated strict-lock/custom-file DSL in this work.
3. Before declaring script version locking complete, prove the actual stage-one
   behavior in a tiny fixture: existing-state drift **and missing state** must
   fail before plugins run. If a public strict script API is unavailable, a
   separately tested early missing-state/configuration preflight plus activated
   existing-state locking is required. A late root-task check is insufficient.
   Host-invariant script lockfiles need explicit cross-host comparison; a
   host-dependent script graph needs a supported host-keyed design, not copied
   Linux state or an undocumented internal API.
4. Record detached/plugin-internal/tool-download graphs separately. Project
   locking does not establish their coverage. Gradle verification covers artifacts
   resolved through its dependency engine, including settings/project plugins;
   it is not a general checksum mechanism for SDK managers, browser downloads,
   Cargo, npm or arbitrary HTTP clients.
5. The Linux minimum may be reported as **project locking + Gradle-engine
   checksum enforcement** while any unproven script/detached version-lock gate
   remains open. It must not close BUILD-007 or be labeled whole-build locking.

Reject external changing/SNAPSHOT modules where the selected graph requires
verification: Gradle does not verify changing dependencies. The implemented
candidate uses public metadata/declaration guards; installed Gradle9.7.1 forbids
combining dependency locking with `failOnChangingVersions()`. Do not reintroduce
that incompatible combination. Guard installation is not proof that changing
module/declaration negative fixtures have run.
Do not reject internal project identity `0.1.0-SNAPSHOT` as though it were an
external downloaded artifact. Dynamic transitive selectors can be pinned by
locks; do not blindly prohibit all ranges and break otherwise lockable graphs.

## 3. Required acquisition scope

Inventory **all** projects in actual Gradle settings, including root, implicit
aggregators, all24 included library projects, all five sample projects and the
included convention build. Match actual permission project paths after settings
renaming; filesystem directory names are not their Gradle paths. Excluded
experimental modules remain explicitly outside the configured build.

For every owner project, inventory every named configuration with its role and
attributes. Classify each resolvable configuration, including late-created ones,
instead of guessing a fixed list from task-name prefixes. At minimum cover:

| Graph family | Required contents / boundary |
|---|---|
| Convention build | Compiler/plugin implementation, compile/runtime/test classpaths and code-generation/tool dependencies; acquire independently and in root composite use |
| Root/plugins | Applied and `apply(false)` project plugin graphs, settings plugin graph, buildscript classpaths and plugin marker/implementation metadata actually resolved |
| Desktop | Main/test compile/runtime, Compose/Skiko, JavaFX actual-host variants, and all sample desktop graphs |
| Android | Main/host-test compile/runtime, AGP/tool/transform inputs and sample Android variants; actual device-test compile/runtime/runner/resource graphs in IO, picker and WebView |
| Common/metadata | Common/shared-source-set metadata, dependency constraints/BOMs, KMP metadata variants and metadata transformation inputs |
| JS and Wasm | Main/test KLIB and Gradle tool/distribution configurations; distinguish these from npm package resolution and stored Yarn locks |
| Apple | Device/simulator dependency configurations that can actually resolve here; preserve disabled cinterop/SDK/link/runtime gates instead of marking them passed |
| Other generated configurations | Compiler plugins, annotation processing/lint/ABI/publication-metadata tools if created; unknown/new configuration requires classification, never automatic exclusion |

Do not execute `assemble`, library Kotlin compilation, Cargo, linking, browser
installation, publication or tests in a dependency-only slot. An external-only
artifact view must filter project components, while preserving project graph
edges in the receipt. Platform/BOM components can legitimately have metadata and
no binary artifact; record that fact rather than counting missing files as success.

Applying/building the local convention plugin may itself require convention
compilation, plugin code execution, downloads or external artifact transforms.
Thus “source-free” means **no library/sample compilation**, not “no code executed”
or a security sandbox. Assert and record the scheduled task graph so an accidental
project artifact dependency cannot silently turn acquisition into a native build.

### Owner-task execution and missing gates

- Proposed `nativeCmpkitDependencyInventory` writes the complete inventory
  without intentionally resolving library artifacts. Initialization/plugin
  resolution can still occur. An inventory-only exit0 is not graph completeness.
- Proposed `nativeCmpkitDependencyGraphPart` executes in each owner project,
  accesses only that project's configurations, collects result components/edges
  and external artifacts, and writes a receipt even for resolution failures.
- Proposed `nativeCmpkitDependencyGraph` aggregates only current-run part files.
  For the root composite it explicitly depends on/collects convention build
  parts. Prove init-script task registration and included-build invocation;
  standalone evidence alone is not proof the composite used the same graph.
- A diagnostic lenient **artifact view** may collect all artifact failures, but
  every failure makes its configuration incomplete and causes aggregate failure.
  This is not permission to use `--dependency-verification lenient` or `off`.
- Snapshot configurations after setup and check for additions during resolution.
  Newly generated configurations must be included/classified before success; a
  bounded fixed-point pass may be used. Unexpected inventory drift fails closed.
- Empty, failed, unsupported and excluded are different states. A disabled Apple
  configuration gets an explicit capability gate with the responsible source
  location/host requirement. A broken required Linux graph fails the run; it must
  not be reclassified as “other host” just to obtain a green aggregate.
- Report both `selected_host_scope_complete` and `all_required_hosts_complete`.
  Only the former may become true after actual Linux acquisition. Never silently
  remove an unacquired host from the project's required matrix.

## 4. Receipt contract: one record per configuration

The helper must preserve enough information to identify the **exact** missing
graph instead of reporting only one total dependency count:

| Field group | Required data |
|---|---|
| Identity | Schema, unique invocation ID, UTC start/end, root/composite/standalone identity, owner project path, configuration name, declared roles, inherited configurations |
| Inputs | Source revision **and truthful dirty state**, source/configuration manifest hash, helper/policy/catalog/wrapper/XML/lock hashes, test-directory/source topology, graph-affecting properties |
| Runtime | Actual Gradle/JVM versions and host; relevant Android SDK or Apple SDK availability/version; allowlisted identities only, no environment dump |
| Selection | Configuration and selected-variant attributes, external component GAVs, project component IDs, constraints, requested-to-selected edges and selection reasons |
| Artifacts | Owning external component, artifact identity/name, selected variant, size and SHA256 of each actually read file; explicitly mark artifact-view outputs as original/transformed/unknown provenance |
| Metadata trust | Active verification policy hash, candidate/strict mode, associated original artifact/POM/module verification entries and their hashes; no invented association when public APIs cannot expose it |
| Locks | Active host/profile and project-relative lock path/hash, locking activation/mode, this configuration's locked entries or explicit empty-state record |
| Failures/gates | Unresolved selectors, safe exception types, missing hashes/files, inventory drift, disabled/unavailable capability reasons; no raw exception bodies or private cache URLs/paths |
| Result | Resolved/empty-resolved/failed/capability-gate status; separate acquisition, lock-enforcement, checksum-enforcement and runtime-test claims |

Artifact views may return transformed AAR contents or KMP metadata outputs.
Hashing such a file must **not** mislabel it as the registry's original artifact.
Gradle's verification writer records original artifacts/metadata separately.
Every selected external component, including metadata-only platforms, must be
reconciled against lock coverage; every trust addition needs acquired evidence.
Same-registry checksum observations establish consistency, not independent trust
or proof of actual origin for a previously cached artifact.

The aggregate rejects missing/duplicate part files, wrong invocation/input/host
identity, stale reports, invalid or escaping paths, omitted required configurations,
unexpected unclassified configurations, unresolved nodes, artifact failures,
changed inputs, incompatible lock states or unexplained trust entries. Use bounded
JSON/XML parsing; reject DTD/entities, symlinks and unsafe output paths. Persist a
failure receipt before the final nonzero result where execution reaches the helper.
An initialization/plugin failure before registration still needs the outer command
receipt and **no completeness claim**.

## 5. Bootstrap candidates without installing unreviewed trust

Metadata generation writes the active default XML path and is incremental. It is
not a harmless report command and is **not a strict verification test**, even if
`--dependency-verification strict` also appears on the command line.

Use a lead-created, task-owned **candidate snapshot of current dirty inputs**, not
`git archive HEAD` or a HEAD-only worktree that silently omits the current repairs.
The snapshot must include build-relevant tracked/untracked source, Gradle/config/
helper/native-resource inputs and conditional test directories, while excluding
private properties, credentials, `.git`, caches and outputs. Check its input
manifest against the frozen original before/after acquisition. Its supplied
revision label is an observation of origin, not a claim that the dirty snapshot
is a commit. Keep it outside the source checkout's Git-parent discovery, or prove
the acquisition never consults an unrelated parent repository.

Use a task-owned Gradle user home and existing explicitly selected SDKs; do not
copy user Gradle init scripts, credentials or `local.properties`. Account for the
fresh wrapper/plugin cache cost before starting. No shared-cache deletion, global
cache corruption or unbounded downloads. The bounded wrapper is a resource guard,
not a command/network sandbox. Raw local logs require review/redaction before
promotion to public evidence.

If the snapshot cannot accurately preserve the evaluated build, stop and record
that limitation. An alternative requires an **exclusive lead-controlled** live
acquisition window: generated trust/locks must remain identified as candidates
and must not silently become normal-build policy before review. Do not switch
the shared worktree while another verification command is using it.

### Original design-only Linux command sketches — do not execute

These retained sketches specify the original future helper contract, not the
current CLI. They use old proposed properties/modes and an audit wrapper not
included by the implemented snapshot. **Do not execute them.** The scoped,
implemented-CLI proposal immediately afterward supersedes these invocation
sketches without claiming the whole design contract is complete.
`CANDIDATE` is the frozen task-owned input copy; `RUN` is a fresh task-owned output
directory. Set the already selected JDK17/SDK context without exporting secrets.
Commands must run sequentially with8GiB reserve, bounded time and two workers.

```sh
# Inventory first; inspect both modes and define required configurations/gates.
python3 "$CANDIDATE/scripts/audit/run_bounded_build.py" \
  --cwd "$CANDIDATE" --log "$RUN/convention-inventory.log" \
  --timeout 600 --reserve-mib 8192 -- \
  ./gradlew -p convention-plugins nativeCmpkitDependencyInventory \
  --init-script "$CANDIDATE/scripts/dependencies/resolve-graphs.init.gradle" \
  -PnativecmpkitDependencyRun=linux001-convention-inventory \
  --no-daemon --no-configuration-cache --max-workers=2 --console=plain

python3 "$CANDIDATE/scripts/audit/run_bounded_build.py" \
  --cwd "$CANDIDATE" --log "$RUN/root-inventory.log" \
  --timeout 600 --reserve-mib 8192 -- \
  ./gradlew nativeCmpkitDependencyInventory \
  --init-script "$CANDIDATE/scripts/dependencies/resolve-graphs.init.gradle" \
  -PnativecmpkitDependencyRun=linux001-root-inventory \
  --no-daemon --no-configuration-cache --max-workers=2 --console=plain

# Explicitly mutating acquisition, only in the candidate snapshot.
python3 "$CANDIDATE/scripts/audit/run_bounded_build.py" \
  --cwd "$CANDIDATE" --log "$RUN/convention-acquire.log" \
  --timeout 900 --reserve-mib 8192 -- \
  ./gradlew -p convention-plugins nativeCmpkitDependencyGraph \
  --init-script "$CANDIDATE/scripts/dependencies/resolve-graphs.init.gradle" \
  -PnativecmpkitDependencyRun=linux001-convention-acquire \
  -PnativecmpkitDependencyMode=bootstrap \
  --write-locks --write-verification-metadata sha256 \
  --no-daemon --no-configuration-cache --max-workers=2 --console=plain

python3 "$CANDIDATE/scripts/audit/run_bounded_build.py" \
  --cwd "$CANDIDATE" --log "$RUN/root-acquire.log" \
  --timeout 900 --reserve-mib 8192 -- \
  ./gradlew nativeCmpkitDependencyGraph \
  --init-script "$CANDIDATE/scripts/dependencies/resolve-graphs.init.gradle" \
  -PnativecmpkitDependencyRun=linux001-root-acquire \
  -PnativecmpkitDependencyMode=bootstrap \
  --write-locks --write-verification-metadata sha256 \
  --no-daemon --no-configuration-cache --max-workers=2 --console=plain
```

Initial inventory can fail when strict policy has no state or a previously
installed XML lacks plugin entries. Capture that failure; use a specifically
identified candidate bootstrap inventory/acquisition pass if necessary, **not**
verification-off/lenient mode in the real checkout. Actual results may require
splitting graph acquisition by explicit project/configuration allowlists to fit
the resource bound. Each split retains the full expected inventory and explicit
pending configurations; the final aggregate must reject any missing part. No
receipt can claim an unexecuted900s command succeeded.

### Current-source acquisition proposal — not scheduled or executed

**Prerequisites:** actual004 established the005 init guards and three external
client observations, but not daemon identity/property bindings or the selected
negative suite. A reviewed subsequent fixture must close those missing gates; the original004 failure is not a pass. The passive
fixture witness is specific to the installed Gradle distribution and does not
observe a wrapper. A separate reviewed source-run wrapper/client witness and
explicit SDK-write boundary are still required before this proposal can run.
Neither a direct JDK probe nor offline parser success lifts these prerequisites.
The lead must release/schedule the Gradle slot and freeze source inputs; there is
no blind retry or fallback to a live-checkout acquisition. The owner's 2026-10-26
[CI decision](containment.md) authorizes routine verification/dependency work
without further approval; this does not waive these technical prerequisites.

Proposed fresh candidate: `/root/nativecmpkit-build007-source-001`, outside every
Git worktree. No snapshot has been created by this proposal. Use the **current
dirty source**, not `git archive HEAD`; the observed origin revision/dirty flag
is not a claim that the resulting source snapshot is a commit.

The implemented copy selection is explicit:

- Root settings/build files (Kotlin or Groovy), `gradle.properties`, both wrapper
  launchers, `rust-toolchain.toml`, `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`
  and `.gitattributes`, when present.
- Every `calf-*` tree plus `convention-plugins`, `sample`, `gradle`,
  **`kotlin-js-store`**, `licenses`, `.cargo`, `scripts/native` and
  `scripts/dependencies` (including the separate Yarn tooling).
- Source hashes, existing integrity-file hashes and empty `src` directory
  topology are compared against both the original and the copied tree. The
  literal settings parser includes renamed permission projects and implicit
  aggregators. Excluded experimental source may be copied but is not thereby
  promoted into the configured project inventory.
- `.git`, `.gradle`, `.kotlin`, `build`, `target`, `node_modules`, `__pycache__`,
  private candidate caches and known private property/key/credential filenames
  are excluded. Symlinked selected inputs fail. This is not a repository-wide
  secret detector; review selected public inputs before promotion. The original
  repository's files, policy and Git history are never changed by acquisition.

```sh
# Stage 0: copy only, after the lead grants the short source-freeze window.
python3 scripts/dependencies/integrity.py snapshot \
  --source /root/projects/nativeCmpKit \
  --destination /root/nativecmpkit-build007-source-001

# Stage 1: one separately scheduled standalone-convention acquisition.
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
ANDROID_HOME=/opt/android-sdk ANDROID_SDK_ROOT=/opt/android-sdk \
python3 /root/nativecmpkit-build007-source-001/scripts/dependencies/integrity.py run \
  --workspace /root/nativecmpkit-build007-source-001 \
  --build convention-plugins --mode bootstrap \
  --run-id convention-bootstrap-001 --timeout 900 --reserve-mib 8192

# Stage 2: a different, explicitly scheduled root/composite acquisition window.
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
ANDROID_HOME=/opt/android-sdk ANDROID_SDK_ROOT=/opt/android-sdk \
python3 /root/nativecmpkit-build007-source-001/scripts/dependencies/integrity.py run \
  --workspace /root/nativecmpkit-build007-source-001 \
  --build . --mode bootstrap \
  --run-id root-bootstrap-001 --timeout 900 --reserve-mib 8192
```

The source runs deliberately use the **copied wrapper**, not an installed
distribution override. Each helper invocation forces `--max-workers=1`,
`--no-daemon`, no configuration cache and strict Gradle-engine verification;
bootstrap explicitly writes candidate locks/SHA256 metadata. The root/composite
and standalone-convention policy paths are different and must be reconciled
later; neither is installed into ordinary live builds by these commands.

Runtime/resource limits and remaining hazards:

- Actual observed host is Linux x64. At proposal preparation the source filesystem
  had38,637,305,856 free bytes (about36GiB); **recheck before each slot**. Each
  scheduled run is bounded900s with8GiB reserve; a stopped/failed run preserves its
  evidence and does not start the other mode automatically. Snapshot copying
  itself is not yet wrapped by this runner: preflight selected-byte size/current
  reserve and use a separate bounded copy window rather than claim a nonexistent
  copy-time/RSS quota.
- The first candidate run starts with a fresh private Gradle/JVM-home cache; the
  second may reuse **only that candidate cache**, so it is not a fresh-cache
  execution. No shared Gradle cache/init scripts/credentials are copied, deleted
  or corrupted. Generated JVM/environment paths are not a filesystem sandbox.
- Current root properties specify a2GiB Gradle heap,1.5GiB Kotlin daemon heap and
  `parallel=true`; workers are forced to one by the helper. There is no
  `convention-plugins/gradle.properties`, so do not assume those root heap values
  apply to the standalone JVM: observe its actual options separately. No hard
  RSS limit exists. Account for compiler/daemon processes and the lead's other
  bounded workloads before granting a slot.
- `/opt/android-sdk` and its `platforms/android-37.0/android.jar` are present.
  Read-only package identity shows platform revision2/API37.0; build-tools34,
  35 and36 are installed, not37. An existing SDK is not proof all AGP tool
  requirements are present or that the SDK will remain unwritten. Preflight the
  actual required packages, then explicitly protect/isolate the selected SDK or
  document an approved writable boundary. No SDK copy/permission change or
  package-manager invocation is authorized by this proposal.
- Applying the local convention plugin may compile **convention** code and run
  artifact transforms. The task guard forbids library/sample/native/publication
  build tasks; it does not mean arbitrary plugin code cannot execute. Native
  provenance's lazy Git providers are attached to native tasks; if configuration
  unexpectedly evaluates them outside Git, preserve the failure rather than
  fabricate a Git identity or run native work to bypass the boundary.
- Every resolvable owner configuration is required. Unknown/unsupported producer
  shapes, artifact failures, late inventory drift and unresolved Linux graphs
  fail closed. Do not add convenience exclusions to get a green aggregate.
  Acquisition and actual script/settings/detached **version locking**, separate
  Kotlin/Native/compiler cache use, other hosts, independent provenance/advisories
  and every runtime/release gate remain distinct.

After each run, bind exact command/exit status, source topology and before/after
hashes, actual wrapper/client/daemon identity, scheduled tasks, every owner
receipt, finalized locks/XML, resource-stop reason and retained sanitized logs.
No900s command, snapshot or real dependency graph in this proposal has run.

## 6. Review and reconcile trust, then test strict operation

The minimum XML policy requires `<verify-metadata>true</verify-metadata>`, SHA256
for original artifact/metadata entries and no broad `<trusted-artifacts>` bypass.
Do not invent trusted signing keys or equate downloaded signatures with vetted
signatories. Reject changing external modules, missing metadata, unexpected
repositories, unexplained extra components and unsupported generated constructs.

The reconciliation tool must canonicalize each `(group, module, version,
artifact-name)` key across root/composite, standalone convention and later host
candidates. Identical SHA256 observations may be deduplicated. **Any distinct
SHA256 for the same key is a hard conflict** requiring investigation; do not
append `<also-trust>`, select the newest observation or overwrite the first hash.
Conflict failure must leave every input and installed XML unchanged. Reject
malformed XML, unexpected trust exceptions, conflicting duplicates and non-SHA256
fallbacks. A complete standalone-convention subset must exist in the reviewed
root trust; the standalone copy may be an exact reviewed subset, not a stale
omission of convention-only dependencies. Lockfiles are compared per host/project,
not union-merged across incompatible hosts.

Store candidate digests, graph/metadata counts, missing capabilities, per-entry
acquisition references and reviewer decisions in an explicit review manifest.
The truthful initial value is `independent_trust_reviewed=false`. Registry-provided
checksums, HTTPS access and repeated downloads alone must not flip that flag.
Review the sources of plugin/tool execution too. Existing approved trust remains
immutable until an intentional, evidence-backed update is accepted by the lead.

Only after review, install the candidate policy/locks **inside the isolated
candidate first**, remove bootstrap flags and execute both acquisition modes
again with normal locking and explicit strict verification:

```sh
# Same bounded wrapper/SDK/JDK context as above, unique new log and invocation ID.
./gradlew -p convention-plugins nativeCmpkitDependencyGraph \
  --init-script "$CANDIDATE/scripts/dependencies/resolve-graphs.init.gradle" \
  -PnativecmpkitDependencyMode=verify \
  -PnativecmpkitDependencyRun=linux001-convention-strict \
  --dependency-verification strict --offline \
  --no-daemon --no-configuration-cache --max-workers=2 --console=plain

./gradlew nativeCmpkitDependencyGraph \
  --init-script "$CANDIDATE/scripts/dependencies/resolve-graphs.init.gradle" \
  -PnativecmpkitDependencyMode=verify \
  -PnativecmpkitDependencyRun=linux001-root-strict \
  --dependency-verification strict --offline \
  --no-daemon --no-configuration-cache --max-workers=2 --console=plain
```

Offline success can prove the acquired scoped artifacts are sufficient without
another download; offline missing-artifact failure is not a checksum rejection.
Require identical source inputs and unchanged lock/XML bytes before/after both
strict runs. Ordinary verification must reject writer/update flags and attempts
to relax verification; no upgrade/bootstrap tasks in test/consumer CI. Finally,
after coordinated integration, run a real selected library/build consumer command
without the acquisition init script to establish that **ordinary** builds apply
the policy. This remains separate from full platform/runtime/release testing.

## 7. Actual negative fixtures required before an enforcement claim

Use a tiny plugin-free Groovy Gradle fixture with project-owned local Maven
artifacts/POMs and deterministic harmless JAR contents. No Kotlin compiler or
remote plugin is necessary. Invoke the inspected installed Gradle9.7.1 distribution
read-only with a **fresh fixture-owned Gradle user home per case**. Never corrupt
the shared cache or the production locks. First prove that the fixture artifacts
and metadata genuinely pass through Gradle verification; an exempt local-file
dependency would not exercise the required behavior.

| Case | Required observed result |
|---|---|
| Known-good baseline | Exact graph and artifact/POM checksums accepted; lock/XML bytes unchanged on ordinary run |
| Wrong JAR SHA256 | Modified fixture artifact rejected with that artifact's expected/actual checksum evidence, not an unrelated download/initialization error |
| Modified POM metadata | Same artifact bytes but altered POM rejected with metadata verification enabled |
| Missing expected hash | Remove only the required artifact/hash entry; precise missing-verification-metadata rejection |
| Missing host/project state | Delete selected host lock without supplying fallback; strict/preflight lock rejection |
| Missing configuration state | Add a required resolvable configuration or remove its explicit empty-state entry; reject missing lock coverage |
| Forced transitive drift | Both old/new leaf versions already checksum-allowed; a changed strict constraint on the transitive leaf conflicts with its locked version. Failure must be locking-related, not missing hashes |
| New compatible transitive version | Keep a parent's transitive dynamic range unchanged, add a newer compatible leaf, allow both checksums; ordinary resolution must still select the old locked version |
| Dependency addition/removal | With fixture checksums already available, newly introduced or removed locked external components are rejected without `--write-locks` |
| Script classpath missing/drift | Actual stage-one plugin/buildscript fixture establishes the separate script-lock behavior before claiming it covered |
| Included versus standalone trust | Root policy governs included build even when its local XML disagrees; standalone uses its own XML. Test both positive and missing-hash rejection |
| Trust importer conflict | Same coordinate/artifact, distinct hashes across candidate inputs fails; no `<also-trust>` escape and no input/output mutation |
| Receipt integrity | Missing/duplicate/stale/foreign-host parts, omitted config, unresolved edge, symlink/path escape, transformed-as-original mislabel and changed inputs fail the aggregate |
| Policy bypass attempt | Verification lenient/off and write/update flags rejected by normal verification entry points; no successful enforcement label |

Record exact command, Gradle identity, exit code, input/fixture hashes and the
specific inspected reason for each case. A nonzero command alone is **not** a
security-test pass. Reusing cached untampered bytes would invalidate a tamper
test; isolated homes and controlled repository bytes are essential. Do not count
these fixtures as library, Android device, Apple, browser or JNI tests.

## 8. Completion boundaries and remaining owners

Accept the first Linux implementation only when all of these are demonstrated:

1. Complete actual project/configuration inventories for root/composite and
   standalone convention; no silent omissions or acquisition failures in the
   selected Linux scope; explicit missing-capability list for everything else.
2. Acquired original artifact/metadata trust with reviewed, conflict-free root/
   convention reconciliation and actual-host version lock state; TOFU disclosed.
3. Two ordinary strict runs with unchanged trust/locks/inputs, and actual negative
   SHA/POM/missing-hash/transitive-drift tests whose causes were inspected.
4. Ordinary non-init-script project enforcement demonstrated; script/settings/
   detached version-lock limits stated precisely rather than inherited by claim.
5. All remaining required host profiles kept as missing gates until actual
   capable-host acquisition/review/strict runs. Linux cannot impersonate Apple or
   Windows, even if it downloads some of their Maven/KLIB artifacts.

Both JS/Wasm project locks were acquired by the separate
[bootstrap003](evidence/build/yarn-materialization-003.summary.json), with zero
tests; [JS003](evidence/js-full-003/archive.json) separately passed286/286 browser
cases across19 modules. The later [cold Wasm-tooling001 diagnostic](evidence/wasm-tooling-001/archive.json)
passed installation only (exit0/94.94s, zero tests), recording `--ignore-scripts`
without a frozen-lock flag and a separate embedded tooling lock with489 lexical
resolvers/488 integrity entries. The exact-commit Karma resolver still lacks SRI;
lexical counts and registry-acquired bytes are not graph closure or trusted
provenance. None of these results adopts ordinary frozen-install policy.
BUILD-007 retains that enforcement work, graph-aware advisory review and
independent trust limitations documented in
[dependency integrity](dependency-integrity.md). Docs locks already have their
own Linux/CPython proof. Cargo/native notices remain with the native/consumer
owners; incomplete legal material is a publication blocker, not fixed by Gradle
checksums. None of these steps authorizes a release or unfreezes shared build
files while another scheduled verification is in progress.
