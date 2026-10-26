# Installed KGP/Yarn frozen-install policy review

**Scope:** additive BUILD-007 evidence, 2026-10-24; read-only inspection of the
installed Kotlin Gradle plugin (KGP) **2.4.20**, Yarn Classic **1.22.22**, and the
configured Node **24.16.0**. This is **source/bytecode evidence, not an install,
negative-test, browser-test, or supply-chain-trust pass**. No finding is closed.
Only this report and its [structured companion](yarn-frozen-policy-review.json)
were written by this review. No Gradle execution, npm/Yarn execution, network
request, source/build/convention/CI/lock edit, or GitHub mutation was performed.

## Conclusions for the build owner

1. The root build configures KGP's **post-install lock-store drift policy**. It
   does **not** presently pass Yarn `--frozen-lockfile`. The actual primary-task
   API is `KotlinNpmInstallTask.args`, a mutable `List<String>`.
2. **A frozen flag alone is not a missing-lock guard in this installed Yarn.**
   Its frozen-mismatch check returns early when the loaded lock cache is absent.
   Ordinary builds need an explicit stored-lock preflight before restore/install/
   store, including when the install task would otherwise be up-to-date.
3. `yarnLockAutoReplace=false` protects an **existing** stored lock from
   replacement by the store action. When that lock is absent, the store action
   can **create it and then throw FAIL**. This is not fail-before-install and is
   not rollback/no-mutation-on-failure.
4. Bootstrap/update must remain a separate, explicit mode. The upgrade tasks
   depend on the same primary install tasks and set their internal `withForce`,
   which becomes Yarn `--force`. Blindly adding frozen to every invocation both
   suppresses lock writing and encounters Yarn's force-path check bypass.
5. Wasm has a **separate `KotlinToolingSetupTask` installation** using an embedded
   KGP tooling lock. Two project locks and `withType<KotlinNpmInstallTask>` do not
   establish enforcement for that third scope.

These are bounded implementation observations, not claims that the current
library dependency graph is malicious, vulnerable, or successfully installed.

## Evidence binding and performed checks

The root file reviewed is `build.gradle.kts`, SHA256
`bcaccb919d2aec3dc5eec04c2c4039696b3fc96decbb72756f0ee2365013fccc`.
Its relevant lines are **5–14 and 27–48**. HEAD was observed as
`94d2492e99d5cbc060409d94d9f88febd06222d5` at 22:39:36 UTC; these observations
bind inspected working-tree bytes, **not all files at that commit or the
consumer reviewer's separate frozen input set**.

| Installed input | SHA256 |
|---|---|
| `org.jetbrains.kotlin:kotlin-gradle-plugin:2.4.20`, `kotlin-gradle-plugin-2.4.20-gradle96.jar` | `6f49688f2c6715d60f5dc52d4c1ada992ce4bed6053d1bd6e579c9392d7ba0ed` |
| `yarn-v1.22.22/package.json` | `9533b84eaaeea708ab99bcf92772bc81c7389f90a04f8b0188c163f9b3b621c3` |
| `yarn-v1.22.22/lib/cli.js` | `443ed69e76443b89afddccfc9faec1ff16eb5e500979cc079c696dec4c3d94ee` |
| `yarn-v1.22.22/bin/yarn.js` | `148e19db309ec9eaf7720b28df811337906eea8a1758deaa54afee60a6305e04` |
| `node-v24.16.0-linux-x64/bin/node` | `b2959781cc5a74c357ffa02367efa8a0330cbb1c9cb347732fdfaaaca381cbcd` |
| KGP JAR entry `org/jetbrains/kotlin/gradle/targets/js/yarn/yarn.lock` (160,311 bytes) | `52abe46477f1343005d5059baa218042f7555e03060f2a7f0f39645dfb996dcb` |

The structured report gives exact installed paths. No KGP sources JAR was found
in the installed 2.4.20 artifact tree; none was downloaded. KGP references below
are therefore **fully identified class/method bytecode offsets**, not invented
source line numbers. Yarn references are actual line numbers in the installed
bundle above. Hashes identify acquired bytes; they do not independently trust
their provenance.

Performed read-only command groups:

- Read root configuration and
  [dependency-integrity.md](../../dependency-integrity.md), plus existing
  `yarn-task-discovery.log` and materialization evidence.
- `javap -p`, `javap -c -p`, and selected `javap -v -p` against that exact JAR;
  inspected APIs, implementation branches, task registration and input annotations.
  `javap -version` returned **21.0.12**, exit 0.
- `rg` and line-numbered source windows in the installed Yarn distribution;
  Python `zipfile`/`hashlib` read JAR entries and computed artifact hashes without
  extraction. Only compact derived evidence is retained, not raw cache dumps.
- The exact Node binary above with `--version` returned **v24.16.0**, exit 0.
  Yarn's `package.json` reports 1.22.22. **Yarn itself was not executed** by this
  reviewer, and neither version observation proves an install used that runtime.
- At **22:35:15.658710 UTC**, the four paths below were absent (also not symlinks);
  `git ls-files -- kotlin-js-store` returned no tracked paths. This is an explicit
  **pre-bootstrap snapshot**, not a claim about subsequent lead-owned runs.

| Scope | Stored lock | Generated working lock |
|---|---|---|
| JS primary graph | `kotlin-js-store/yarn.lock` | `build/js/yarn.lock` |
| Wasm primary graph | `kotlin-js-store/wasm/yarn.lock` | `build/wasm/yarn.lock` |

Existing execution evidence was read, not rerun:

- Task discovery succeeded; actual names include `kotlinNpmInstall` (log 3038),
  `kotlinWasmNpmInstall` (3066), `kotlinWasmToolingSetup` (3067), and the
  restore/store/upgrade names (10770–10782).
- The first materialization failed Maven TLS resolution; the next
  [fresh-JVM receipt](yarn-materialization-fresh-jvm-verification.json) records
  `kotlinUpgradeYarnLock kotlinWasmUpgradeYarnLock --no-daemon`, entering actual
  `kotlinNpmInstall` before a 300-second bound terminated the owned process group
  (exit 143, 300.42 seconds). Its lock list is empty. Neither failure proves a
  frozen-lock rejection, and this review does not diagnose that timeout.
- Later transport or materialization receipts belong to their own commands and
  timestamps. A registry HTTP 200 alone is not an install/enforcement/trust pass.

## Primary installation: actual API and argument flow

For the class names in this section, the prefix is
`org.jetbrains.kotlin.gradle.targets.`.

`js.npm.tasks.KotlinNpmInstallTask` exposes:

```java
public final java.util.List<java.lang.String> getArgs();
public final void resolve();
```

The constructor creates an `ArrayList` at offsets **40–51**. The private field
has Gradle `@Input`; it is not a `ListProperty`. In `resolve()`:

| Offsets | Operation |
|---|---|
| 0–22 | Copy configured `args` into the outgoing argument list |
| 23–38 | Append `--offline` when Gradle was invoked offline |
| 39–71 | Append `--force` when internal `withForce` is true |
| 78–137 | Pass the list to `KotlinNpmResolutionManager.installIfNeeded…` |

`js.npm.KotlinNpmResolutionManager.installIfNeeded…`, offsets **75–85**, forwards
the list unchanged to `NpmApiExecution.resolveRootProject`; its already-installed
state returns early at **35–55**. `js.yarn.YarnWorkspaces.resolveRootProject`,
offsets **25–65**, forwards it to `packageManagerExec` in the root package directory.

`js.yarn.YarnBasics$packageManagerExec$1.invoke(ExecSpec)` assembles the process:

- **6–32:** supplied arguments plus optional debug `--verbose`;
- **35–55:** `--ignore-scripts` when the environment requests it;
- **61–93:** `--network-concurrency 1 --mutex network`;
- **99–201:** remove empty optional strings;
- **202–337:** use the configured executable, or configured Node plus Yarn's
  script when Yarn is non-standalone;
- **338–351:** set the root package working directory.

There is **no automatically added frozen flag** in this path. With no command
token, Yarn defaults to `install` (`cli.js` **88815–88818**). The fixed network
mutex/concurrency options are not evidence of the earlier timeout's cause.

`web.yarn.BaseYarnRootEnvSpec` exposes ignore-scripts, mismatch-report,
report-new-lock, auto-replace and resolutions properties, but **no install-args
or frozen-lock property**. `js.yarn.YarnEnvironment` contains executable,
standalone, ignore-scripts and resolutions; it does not carry the store policy
into the process as a frozen argument.

The root currently pins both typed environments and sets:

```text
version=1.22.22; ignoreScripts=true;
yarnLockMismatchReport=FAIL; yarnLockAutoReplace=false; reportNewYarnLock=true
```

An API-supported **candidate**, not compiled/applied here and **not a complete
policy on its own**, is:

```kotlin
import org.jetbrains.kotlin.gradle.targets.js.npm.tasks.KotlinNpmInstallTask

// Only inside a separately validated ordinary-install policy, not bootstrap.
tasks.withType<KotlinNpmInstallTask>().configureEach {
    args.add("--frozen-lockfile")
}
```

JS `NodeJsRootPlugin.apply` and `wasm.nodejs.WasmNodeJsRootPlugin.apply` both use
`web.nodejs.NodeJsRootPluginApplier`. Its `apply` registers platform-disambiguated
`npmInstall` tasks with this **same task class** at **646–710**. Do not substitute
an imagined `WasmKotlinNpmInstallTask` or pass the Yarn option as an unsupported
Gradle CLI option. Effective process arguments still need an actual-run receipt.

## Restore/store/upgrade are different guarantees

`js.yarn.YarnPluginApplier.apply`, offsets **594–641**, records restore as a
pre-install task and store as a post-install task. Its `$apply$4.execute`,
**0–17**, makes store depend on primary installation; **18–189** wires the
generated/stored files and mismatch flags. `$apply$5.execute`, **0–96**, wires
restore in the other direction and installs an `onlyIf` existence check.

`web.nodejs.NodeJsRootPluginApplier$apply$npmInstall$1.invoke`, **284–312**, makes
primary installation depend on the pre-install tasks. The browser-test wiring
`js.ir.KotlinBrowserJsIr.configureTestDependencies`, **47–99**, depends on both
primary installation and post-install tasks. **Directly requesting only the
install task is not itself proof that the store task ran.** Record selected tasks
and actual outcomes, or request store explicitly for store-policy verification.

The default store directory lambdas are `js.yarn.YarnPlugin$apply$4.invoke`
(**6–12**, `kotlin-js-store`) and `wasm.yarn.WasmYarnPlugin$apply$4.invoke`
(**6–21**, `kotlin-js-store/<platform>`). `WasmPlatformDisambiguator` returns
`wasm`. `BaseYarnRootExtension` constructor **526–559** defaults the filename to
`yarn.lock`; root does not override these locations.

### Store behavior, with the current FAIL/false/true settings

`js.npm.LockStoreTask.copy()` performs these operations **in this order**:

1. **0–105:** resolve stored output and generated input provider.
2. **107–170:** determine mismatch: missing output uses `reportNewLockFile`;
   existing output uses `contentEqualsIgnoringLineEndings` when reporting enabled.
3. **172–192:** delete `additionalInputFiles` (not an unconditional stored-lock
   deletion). The base initializes an empty collection and the inspected Yarn
   registration does not add any extras.
4. **193–225:** invoke `LockCopyTask.copy()` **if output does not exist OR
   auto-replace is true**.
5. **228–430:** report the earlier mismatch; FAIL throws `GradleException`.

| State when store action executes | Source-confirmed consequence |
|---|---|
| Existing stored lock; generated lock differs beyond line endings | Compare fails; existing stored file is not replaced; FAIL is thrown **after installation** |
| Existing stored lock; only line endings differ | Store comparison treats them as equal; this is not a byte-for-byte comparison |
| Stored lock absent; valid nonempty generated lock | Copy may create stored lock, then `reportNew=true` causes FAIL |
| Stored lock absent; existing generated lock is blank/comment-only | Yarn subclass can skip copy/report as an empty-dependency case |

`js.yarn.YarnLockStoreTask.copy`, **72–126**, implements the last exception and
logs “No NPM dependencies detected, and stored lockfile does not exist - skipping
copy”. `js.yarn.LockCopyTaskKt.isEmptyYarnLock` also treats null/missing files as
empty, otherwise checks only blank lines or lines starting with `#`. This is not
semantic dependency-graph validation. **Method-level missing-input branches do
not prove a real Gradle task with a configured nonexistent `@InputFile` reaches
its action**: `LockCopyTask.getInputFile` is `@Optional @InputFile`, and no such
Gradle validation fixture was executed. The existing empty-file case does not
need that assumption.

Restore's `$apply$5$1.isSatisfiedBy`, **0–42**, returns false when its stored file
does not exist. Thus restore has a skip, not an explicit missing-lock rejection;
stale generated files are not cleaned by that skipped restore.

### Upgrade must not be silently substituted for enforcement

`YarnPluginApplier$apply$upgradeYarnLock$1.execute`, **0–83**, depends on primary
installation and copies generated `yarn.lock` to the configured store. It is a
`YarnLockUpgradeTask`, not the mismatch-enforcing store task.

`YarnPluginApplier$apply$2.execute`, **41–82**, sets the primary task's internal
`withForce` from `$apply$2$1.call`: `taskGraph.hasTask(":" + upgradeTaskName)` at
**0–41**. This affects the shared installation whenever that upgrade task is in
the graph. `YarnLockUpgradeTask.copy`, **0–161**, copies nonempty input; for an
empty lock it can delete an existing stored lock. As above, reaching an action
with a nonexistent configured input is a separate Gradle validation question.

Therefore ordinary/upgrade task mixing must be rejected by policy, not inferred
safe because the environment's mismatch report still says FAIL.

## What Yarn 1.22.22 actually freezes

All references here are to the installed `lib/cli.js` hash above.

### Missing lock and drift checks

- **3057–3088:** `Lockfile.fromDirectory` reads/parses an existing lock. When
  absent, it logs “No lockfile found.” and returns a lock object whose `cache`
  and parse result are undefined; it does not throw for missingness.
- **7311–7321:** installation resolves packages **before** calling `bailout`.
  Missing-pattern fixtures must make resolution possible; an unrelated network
  failure before the check is not frozen-enforcement evidence.
- **7097–7117:** `Install.bailout` returns early for audit, Plug'n'Play,
  skip-integrity-check or force, and then for **absent `lockfile.cache`**. Only
  afterward does frozen mode reject a non-successful parse result or missing
  patterns with the exact message:

  > Your lockfile needs to be updated, but yarn was run with `--frozen-lockfile`.

- **47494–47506:** missing patterns are the supplied patterns without lock
  entries, excluding workspace manifests. The caller supplies **top-level
  patterns**, not an independently traversed complete transitive lock closure.
- **65163–65204**, **36766–36844:** a missing dependency entry is considered
  fresh and version lookup can still occur; `frozen` selects exact-version reuse
  rather than being an unconditional “no missing entry may resolve” guard.

Consequences established by source: a missing file is not universally rejected
by the flag; the named frozen error is conditional; `--force` is not an innocent
way to force a cold negative test. The check does **not establish universal
manifest/transitive-graph equivalence**. Missing transitive entries, removed
dependencies, resolutions and workspace changes need their own negative cases
before a whole-graph guarantee. No executable counterexample is claimed here.

### Persistence, checksums and lifecycle scripts

- **7734–7764:** `saveLockfileAndIntegrity` writes installation integrity metadata
  and may prune an offline mirror **before** returning for frozen/no-lock/pure
  modes. Frozen prevents saving `yarn.lock`, not all package/cache/filesystem
  writes. With no original lock, this path does not bootstrap one in frozen mode.
- **7120–7139:** existing lock plus matching installation-integrity state can
  yield “up to date”; missing integrity/state changes can require further work.
  A warm install is not evidence that tarball bytes were revalidated.
- **47941–47969:** the cache-hit path compares cached metadata's integrity/hash
  with the requested remote values; this excerpt does not freshly hash every
  installed `node_modules` byte. Do not corrupt the shared cache to test this.
- **63476–63535**, **63682–63729:** tarball streams validate supplied hash/SRI;
  mismatches reject with `SecurityError` unless checksum updating is requested.
  The message at **94471** is `Integrity check failed for ... (computed integrity
  doesn't match our records, got ...)`. It prints the computed integrity; retain
  the expected digest separately in fixture evidence rather than requiring Yarn
  to print both. A syntax error, gzip failure or network error is not that result.
- **50015–50069:** a `file:` **directory** uses a `copy` (or link) resolver and a
  synthetic hash. It is not a substitute for exercising registry tarball SRI.
- **7393–7401** and **41257–41267:** `ignoreScripts` skips dependency build scripts
  and configured root lifecycle execution. This is useful source confirmation,
  not a sandbox, malicious-package clearance, or proof that browser tooling
  needing install scripts works. `--update-checksums`, force, audit/PnP and other
  policy-bypassing modes must not creep into an ordinary enforcement fixture.

## Separate Wasm tooling scope

`wasm.nodejs.WasmNodeJsRootPlugin.kotlinToolingSetup` registers
`js.npm.tasks.KotlinToolingSetupTask`, not `KotlinNpmInstallTask` (registration
**203–262**). `js.ir.KotlinBrowserJsIr.configureTestDependencies`, **100–139**,
adds that task for Wasm browser tests, so it is not merely an unrelated class.
It exposes **`getArgs(): ListProperty<String>`**, a different API.

`KotlinToolingSetupTask.install`, **348–484**, writes a tooling manifest, invokes
`prepareTooling(destination)`, then calls the package manager with **its own
`args.get()`**. `YarnBasics.prepareTooling`, **6–62**, opens destination
`yarn.lock` and copies the embedded JAR resource; that resource is fingerprinted
above. The root has no tooling-task-argument policy. A primary-task `withType`
does not cover this class, and the tooling lock is not one of the two root-store
files. Embedded bytes bound to KGP are not independently reviewed provenance.

Before claiming all npm inputs frozen, capture the actual tooling task path,
destination, manifest, embedded/generated lock, effective Node/Yarn versions and
arguments, and its cache/skip behavior. Review an explicit tooling policy or
retain this gap. Do not modify the shared tooling cache for a negative test.

## Proposed ordinary/bootstrap contract — not implemented here

The build owner should implement and execute-test the smallest explicit policy:

1. **Ordinary is the default.** No upgrade task may execute in this mode; reject
   mixed ordinary/upgrade graphs before mutable lock actions. Validate any mode
   property against an exact enum/boolean contract. Do not infer permission from
   a task-name substring or silently switch because a lock is missing.
2. **Preflight both required scopes.** Require regular, non-symlink, reviewed
   stored locks at the configured JS/Wasm locations, with usable contents and
   required graph coverage. An empty/no-dependency target needs an explicit
   policy, not a skip interpreted as success. Wire validation before restore,
   install and store and ensure it still executes with warm/up-to-date tasks.
   A `doFirst` only on an install task that may be skipped is insufficient.
3. **Bind the actual working lock.** After restore, check the generated lock
   exists and corresponds to the intended stored one; missing stores must fail
   even when stale generated locks or `node_modules` remain. Keep store FAIL,
   `autoReplace=false`, `reportNew=true` as a second, post-install check, not as
   the preflight. The guard must prevent Yarn invocation and source-controlled
   lock mutation on missing locks; do not promise rollback of all Gradle caches.
4. **Forward the frozen argument only to ordinary primary installs** and inspect
   the real process arguments. Reject incompatible modes such as `--force`,
   `--no-lockfile`, `--pure-lockfile`, `--skip-integrity-check`, checksum updates,
   audit/PnP variants unless separately designed and tested. Use a fresh scoped
   fixture/process for negative tests instead of Yarn force. Account separately
   for Wasm tooling installation and any changed runtime/plugin version.
5. **Bootstrap/update is explicit and bounded.** Invoke the actual upgrade tasks
   only under an intentional mode that does not add the ordinary frozen flag.
   Keep script suppression. Restrict unrelated task mixing, snapshot manifests,
   artifact/lock hashes and graph versions, and require review before adopting
   candidate locks. A successful bootstrap still is not enforcement or trust.
6. **Hash checks are not semantic completeness.** Prove rejection of incomplete
   transitive locks and other supported graph changes, or add a complete-graph
   validation mechanism and keep its gaps explicit. A frozen install can leave
   an incomplete on-disk lock unchanged, so a final no-diff check alone is not
   sufficient. Never use an automatic upgrade as that validation mechanism.

This contract is a recommendation, not authorization for a live root edit or
for lifting containment. It must be coordinated with immutable consumer/build
verification; no current lock is changed by this report.

## Small safe negative-fixture design — all cases unexecuted

Use **two layers**: first characterize raw Yarn, then exercise the real pinned
KGP task APIs/wiring and proposed policy in a small isolated project with JS and
Wasm targets. A raw-Yarn pass cannot certify the Gradle integration. Do not use
the whole live library checkout or another project's/shared cache as a fixture.

### Controlled graph and isolation

- Create a marked disposable fixture root with separate HOME, XDG/cache, Yarn
  cache/global/modules directories and, for integration, dedicated Gradle/tooling
  storage. Keep inputs/logs/receipts; delete only fixture-owned paths afterward.
  Copy/reuse verified tools read-only where possible. Avoid uncontrolled daemon,
  compiler or network-heavy work; schedule it with the lead.
- Serve two tiny self-authored npm packages through a **loopback-only** registry
  and tarball server: `fixture-parent@1.0.0 -> fixture-leaf@1.0.0`, plus a known
  `fixture-parent@2.0.0` for drift. Tarballs contain only fixed package JSON and
  small inert payloads, with deterministic ownership/timestamps and recorded
  SHA256/SHA512. Do not package symlinks or executable third-party code. This
  exercises a registry/tarball path rather than `file:` directory copying.
- Use only synthetic, nonoptional dependencies and allowlisted loopback routes;
  log status/byte count/digest and reject unexpected external origins. Use an
  outbound-denying sandbox when available; a `--registry` flag alone is not one.
  An unavailable sandbox must be disclosed, not mislabeled as zero-network.
  Disable self-update checks and inherited config/proxies/auth/alternate Yarn
  paths; do not copy credentials or print an environment dump. Relevant source
  controls include `--no-default-rc` (88720), `YARN_IGNORE_PATH=1` (89249–89256),
  and `disable-self-update-check` (7899). Isolate/disable the wrapper's V8 compile
  cache (`DISABLE_V8_COMPILE_CACHE=1`, installed `lib/v8-compile-cache.js` 326).
- Acquire a positive fixture lock using the real pinned package manager; do not
  claim an invented lock came from it. Preserve this immutable seed. Each case
  gets fresh lock/manifests and **its own empty package cache/node_modules**, or
  an explicitly documented warm-cache variant. KGP-generated workspaces/tools
  must be enumerated; do not assume the raw two-package graph is its whole graph.

| Case | Controlled change | Required observation / acceptance |
|---|---|---|
| YF-001 positive | None; clean fixture with valid generated lock | Ordinary frozen install succeeds; expected graph and payload bytes match; no lock/manifest changes; real args/versions captured |
| YF-002 missing lock | Remove only fixture's stored lock; test both clean and stale generated-lock/cache states | Raw Yarn behavior is characterized honestly; **policy/KGP layer must reject before Yarn runs or any stored lock is created**, with exact missing-lock diagnostic, not connectivity failure |
| YF-003 direct drift | Change requested parent 1.0.0 to the available 2.0.0 without updating lock | Raw ordinary frozen invocation produces the exact frozen-lock error, nonzero exit; no changed lock; registry resolution must be available, with no force/skip/audit bypass |
| YF-004 wrong lock SRI | Replace one expected SHA512 with a different, syntactically valid 64-byte digest; keep real tarball unchanged | Empty-cache fetch yields the actual tarball-integrity rejection and observed computed digest; independently record original/altered expected digests; no checksum auto-update |
| YF-005 changed tarball | Keep valid lock/expected SRI; serve a **valid repacked tarball** with different inert payload | Integrity-specific nonzero result, not gzip/extraction/404/TLS failure; server proves bytes served; original and changed digests recorded |
| YF-006 incomplete closure | Delete only the transitive leaf's lock stanza; keep direct manifest/parent stanza | Determine whether raw Yarn accepts; **ordinary whole-graph policy must reject** rather than silently resolve leaf while leaving lock unchanged. Preserve any raw acceptance as a counterexample, not a passed negative |
| YF-007 store mismatch | In a separate KGP-action fixture, use two valid nonempty differing generated/stored locks; also test initially absent store | Record actual post-install/store failure and before/after bytes. Existing store must remain unchanged with autoReplace=false; characterize missing-store copy-before-failure. Do not assert pre-install enforcement from this test |
| YF-008 scripts | Add self-authored root and dependency lifecycle scripts that only write named markers **inside their own fixture directories** | A separate bounded control proves those harmless markers can be produced; ordinary `ignoreScripts=true` run produces neither marker. Do not run downloaded scripts or infer suppression solely from absent markers without control |
| YF-009 empty/mixed/warm modes | Empty dependency graph/blank lock; unauthorized upgrade or mixed task graph; second warm ordinary invocation | Defined empty-scope policy, explicit-mode rejection, and missing-lock preflight cannot be bypassed by skip/up-to-date state. Record task outcomes, not just overall exit |
| YF-010 tooling scope | Separate fresh fixture-owned Wasm tooling destination | Observe embedded lock, manifest, actual process args/version/cache handling and ordinary integrity policy; do not count JS/Wasm project-lock checks as this result |

For the KGP store-action characterization, a tiny task harness may use the actual
installed task classes with fixture-owned input/output paths; identify it as a
task-action fixture, **not** evidence that a real library install ran. The second
integration layer must also run real primary install/store wiring for each
platform. Do not “simulate” enforcement by throwing the expected error in a
wrapper; observe the actual Yarn/KGP rejection, with the wrapper responsible only
for its separately named preflight policy.

Each receipt must include command argv, cwd/scope, bounded start/end/exit/reason,
exact tool/input hashes, effective ordinary/bootstrap mode, selected and executed
task outcomes, expected vs observed rejection category, safe server observations,
and **before/after lock and manifest hashes/presence**. A timeout or arbitrary
nonzero exit is a fixture failure/inconclusive result, not security success.
Retain all failed runs and record positive-control results before interpreting
negatives. Broader platform/browser tests and independent artifact provenance
remain additional release gates even after these fixtures pass.
