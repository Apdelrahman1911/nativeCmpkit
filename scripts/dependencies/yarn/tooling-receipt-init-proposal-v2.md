# Lead-owned Wasm tooling receipt v2: root-scoped, unexecuted proposal

**Design/snippet only; not an adopted init script.** No Gradle invocation,
Groovy compilation, tool install, parser or live policy was executed/adopted by
this correction. Public API and installed-bytecode inspection are **not**
runtime integration verification. The exact root task remains
`:kotlinWasmToolingSetup`.

The [original v1 proposal][v1] is **blocked for adoption**: its root-only task and
fresh-home gates, exclusive receipt writes and listener registration are placed
unconditionally at init-script evaluation, so they would run in every build if
adopted. The installed Gradle copies init scripts into included
builds while resetting task requests, so the convention build can encounter a
false task-list rejection. Bypassing that single check would still leave duplicate
root receipts and incorrectly scoped graph listeners. Do not patch only the
equality check or permit arbitrary task names globally.

The original proposal/API/documentation receipts remain byte-identical in the
[preservation checkpoint][checkpoint]; its original evidence index is snapshotted
there. This additive proposal uses public `Gradle.beforeSettings(Closure)` to
classify the **actual canonical settings directory** before any root-only work.
See the [scope/API review][scope] and existing [destination review][destination].

[v1]: tooling-receipt-init-proposal.md
[checkpoint]: ../../../docs/development/evidence/build/yarn-fixtures/wasm-tooling-init-scope-checkpoint001.json
[scope]: ../../../docs/development/evidence/build/yarn-fixtures/wasm-tooling-init-scope-review002.md
[destination]: ../../../docs/development/evidence/build/yarn-fixtures/wasm-tooling-destination-source-review.md

## Scope and timing contract

| Actual settings context | Proposed action before any root gates or writes |
|---|---|
| Canonical `/root/projects/nativeCmpKit`, with no parent build | Continue with root-only gates; bind every listener/receipt to this settings object's Gradle instance. |
| Canonical `/root/projects/nativeCmpKit/convention-plugins`, with a parent build | Return from this callback without checking the root request/fresh home, writing a root receipt or attaching any task-graph listener. Convention compilation is not subject to the root task allowlist. |
| Either path with the wrong parent role, or any other settings directory | Fail closed, without root receipts/listeners; stop and review. New `buildSrc`/other included builds require an explicit scoped revision. |

Canonical settings identity is mandatory. The parent check is **additional**, not
a substitute for it. Neither `rootProject.name`, the shell working directory,
`startParameter.currentDir`, nor an unqualified local task path identifies the
intended build. Even a top-level invocation of `convention-plugins` is rejected.

The pinned Gradle implementation calls `beforeSettings` after constructing the
settings object and **before applying that build's settings script**. This avoids
the later `settingsEvaluated` boundary, by which time `pluginManagement.includeBuild`
may already have needed convention compilation. This is source-confirmed call
ordering, not an observed callback trace. Init scripts/other earlier Gradle work
have already happened; this is **not** a fail-before-all-configuration, network,
cache writes or OS-execution boundary. The permitted convention build may compile
and use shared caches; it is deliberately not certified by the root graph gate.

Only imports and the `beforeSettings` callback registration occur outside the
callback. Root freshness checks, task/property checks, receipt creation and graph
listener registration are all **after** exact root-context acceptance. Listeners
use `actualSettings.gradle`, and every observed graph/outcome task must belong to
that same Gradle instance and root directory, not merely share a `:task` name.

## Intended use and non-guarantees

- The lead allocates a **fresh absolute run root**, a `receipts/` child, and an
  absent or empty `kotlin-user-home/` child. Replace the single run-root placeholder
  below, freeze/hash the resulting task-owned script, then pass
  `-Pkotlin.user.home=<run-root>/kotlin-user-home` for this one invocation.
- The checkout paths below are deliberately bound to this reviewed checkout.
  A different checkout or included-build layout requires a reviewed revision,
  not an implicit working-directory fallback or wider path allowlist.
- Recheck the separately pinned hashes of the exact Node/Yarn executable paths
  below before scheduling. Those pins identify bytes, not independent provenance.
  Unexpected paths or nonempty args/resolutions are rejected without dumping them.
- Request exactly `:kotlinWasmToolingSetup`, with canonical
  `--rerun-tasks --no-configuration-cache`, the lead's separately approved bounded
  runner, resource reserve, `--info` and non-task flags. No task abbreviations,
  exclusions, dry-run or `wasmNpmTooling.installationDir` override.
- The root graph allowlist remains small and **unexecuted**: the target plus
  `:kotlinWasmNodeJsSetup` and `:kotlinWasmYarnSetup`. Unexpected root prerequisites
  fail for review. This is not a build-wide allowlist of included-build compilation
  tasks and not a defense against malicious build code.
- This snippet reads task/environment properties. It does not configure task
  destination, args, Node/Yarn, script policy, dependency versions or ordering.
  Reads can realize providers; this diagnostic has not been proven harmless by
  runtime execution. Its only intended filesystem writes are exclusive JSON
  receipt creation in the lead-allocated directory.
- `CREATE_NEW` on `requested-task.json` happens **before** listener registration.
  A duplicate root callback/script or reused receipt directory therefore fails
  rather than registering a second set of listeners or overwriting evidence.
  Every later receipt is also exclusive-create; never change these to overwrites.
- A fresh `kotlin.user.home` isolates the source-derived default tooling
  destination, **not** HOME, Yarn's package cache, all Gradle/Kotlin caches,
  network access or the OS. Separate runner/config/environment policy is required;
  do not fill this gap by dumping whole environments or project properties.
- Capture pre-action properties with `whenReady`, including when the task will
  be skipped. Require absent `node_modules`: even `--rerun-tasks` does not defeat
  KGP's action-level existing-modules early return. An explicit installation
  directory instead means preinstalled tooling and skips the install.
- KGP classes are not imported. Public getters operate on actual task objects
  with runtime class/hierarchy checks. `KotlinToolingSetupTask.args` is a
  `ListProperty<String>`. `YarnResolution` has `path`, `includedVersions`,
  `excludedVersions`, **not** `version`; this diagnostic accepts only an empty
  resolutions list and never serializes arbitrary resolution objects.

## Proposed Groovy init script — uncompiled and unexecuted

```groovy
import groovy.json.JsonOutput
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.StandardOpenOption

gradle.beforeSettings { actualSettings ->
    def expectedRoot = new File('/root/projects/nativeCmpKit').canonicalFile
    def expectedConvention =
        new File('/root/projects/nativeCmpKit/convention-plugins').canonicalFile
    def actualSettingsDir = actualSettings.settingsDir.canonicalFile
    def contextGradle = actualSettings.gradle

    // Identity-only classification comes before EVERY root-specific operation.
    if (expectedRoot == expectedConvention) {
        throw new GradleException('Root and convention settings identities overlap')
    }
    if (actualSettingsDir == expectedConvention) {
        if (contextGradle.parent == null) {
            throw new GradleException('Convention context must be an included build')
        }
        return // No root gates, root receipts, or task-graph listeners here.
    }
    if (actualSettingsDir != expectedRoot || contextGradle.parent != null) {
        throw new GradleException('Unexpected settings context; stop for scoped review')
    }

    def wanted = ':kotlinWasmToolingSetup'
    def runRoot = new File('/REPLACE_WITH_LEAD_ALLOCATED_ABSOLUTE_RUN_ROOT')
    def expectedNode = '/root/.gradle/nodejs/node-v24.16.0-linux-x64/bin/node'
    def expectedYarn = '/root/.gradle/yarn/yarn-v1.22.22/bin/yarn.js'
    def requireValue = { boolean ok, String message ->
        if (!ok) throw new GradleException(message)
    }
    requireValue(runRoot.isAbsolute() && runRoot.isDirectory(), 'Allocate run root first')
    requireValue(runRoot.toPath().normalize() == runRoot.canonicalFile.toPath(),
                 'Run root must be canonical, without symlink aliases')
    def receipts = new File(runRoot, 'receipts')
    def home = new File(runRoot, 'kotlin-user-home')
    requireValue(receipts.isDirectory() &&
                 receipts.toPath() == receipts.canonicalFile.toPath(),
                 'Allocate canonical receipt directory first')
    requireValue(home.toPath() == home.canonicalFile.toPath(), 'Kotlin home alias rejected')
    requireValue(!home.exists() || (home.isDirectory() &&
                 home.list() != null && home.list().length == 0), 'Kotlin home is not fresh')

    def sp = contextGradle.startParameter
    requireValue(sp.taskNames == [wanted], 'Only the exact root tooling task may be requested')
    requireValue(sp.excludedTaskNames.isEmpty(), 'Task exclusions are not allowed')
    requireValue(!sp.isDryRun(), 'Dry run is not a tooling execution')
    requireValue(!sp.isConfigurationCacheRequested(), 'Use --no-configuration-cache')
    requireValue(sp.isRerunTasks(), 'Use canonical --rerun-tasks for this diagnostic')
    def selectedHome = sp.projectProperties.get('kotlin.user.home')
    requireValue(selectedHome != null && new File(selectedHome).isAbsolute() &&
                 new File(selectedHome).canonicalFile == home.canonicalFile,
                 'Pass the exact fresh task-owned kotlin.user.home project property')

    def buildIdentity = [settingsDir: actualSettingsDir.path,
                         buildPath: contextGradle.buildPath, topLevelBuild: true]
    def writeNew = { String name, Map value ->
        requireValue(name in ['requested-task.json', 'tooling-pre-action.json',
                              'tooling-task-outcome.json'], 'Unexpected receipt name')
        def payload = value + [schemaVersion: 2,
            observedUtc: java.time.Instant.now().toString(), buildIdentity: buildIdentity,
            scopeHook: 'Gradle.beforeSettings']
        def json = JsonOutput.prettyPrint(JsonOutput.toJson(payload)) + '\n'
        Files.writeString(new File(receipts, name).toPath(), json,
            StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
    }
    // Exclusive creation precedes both listeners; duplicate registration fails closed.
    writeNew('requested-task.json', [taskNames: sp.taskNames,
        excludedTaskNames: [], configurationCacheRequested: false, dryRun: false,
        rerunTasks: true, kotlinUserHome: home.absolutePath,
        actualProcessObserved: false, libraryTestsExecuted: 0])

    def allowedGraph = [wanted, ':kotlinWasmNodeJsSetup', ':kotlinWasmYarnSetup'] as Set
    def belongsToRoot = { task ->
        task.project.gradle.is(contextGradle) &&
            task.project.rootDir.canonicalFile == actualSettingsDir
    }
    contextGradle.taskGraph.whenReady { graph ->
        def tasks = graph.allTasks
        requireValue(tasks.every { belongsToRoot(it) && (it.path in allowedGraph) },
                     'Unexpected task/build in root graph; stop for review')
        def task = tasks.find { it.path == wanted }
        requireValue(task != null, 'Tooling task absent from actual root graph')
        def hierarchy = []
        for (Class type = task.getClass(); type != null; type = type.superclass) {
            hierarchy.add(type.name)
        }
        requireValue(hierarchy.contains(
            'org.jetbrains.kotlin.gradle.targets.js.npm.tasks.KotlinToolingSetupTask'),
            'Unexpected tooling task implementation')
        def node = task.nodeJsEnvironment.get()
        def yarn = task.packageManagerEnv.get()
        requireValue(yarn.getClass().name ==
            'org.jetbrains.kotlin.gradle.targets.js.yarn.YarnEnvironment',
            'Selected package manager is not the reviewed Yarn environment')
        def args = task.args.get()
        requireValue(args.isEmpty(), 'Nonempty task args need review; not dumped')
        requireValue(yarn.yarnResolutions.isEmpty(),
                     'Nonempty Yarn resolutions need review; not dumped')
        requireValue(!yarn.standalone && yarn.ignoreScripts,
                     'Require reviewed Node+Yarn-script mode and script suppression')
        requireValue(node.nodeExecutable == expectedNode && yarn.executable == expectedYarn,
                     'Unexpected selected executable path; value not dumped')
        def destination = task.destination.get().asFile.canonicalFile
        def modules = task.nodeModules.get().asFile.canonicalFile
        def expectedBase = new File(home, 'kotlin-npm-tooling/yarn').canonicalFile
        requireValue(destination.parentFile == expectedBase &&
                     (destination.name ==~ /[0-9a-fA-F]{32}/),
                     'Destination is not the expected fresh default hash directory')
        requireValue(modules == new File(destination, 'node_modules') && !modules.exists(),
                     'Selected node_modules must be absent for this cold diagnostic')
        // Executable hashes are frozen/rechecked separately, not certified by these paths.
        writeNew('tooling-pre-action.json', [taskPath: task.path,
            graphTaskPaths: tasks.collect { it.path }, destination: destination.path,
            nodeModules: modules.path, nodeModulesExisted: false, args: args,
            nodeExecutable: node.nodeExecutable, yarnExecutable: yarn.executable,
            yarnStandalone: yarn.standalone, ignoreScripts: yarn.ignoreScripts,
            yarnResolutions: [], actualProcessObserved: false,
            frozenOrClosurePolicyVerified: false, provenanceVerified: false])
    }
    contextGradle.taskGraph.afterTask { task, state ->
        requireValue(belongsToRoot(task) && (task.path in allowedGraph),
                     'Unexpected task/build outcome in root listener; stop for review')
        if (task.path == wanted) {
            writeNew('tooling-task-outcome.json', [taskPath: task.path,
                executed: state.executed, didWork: state.didWork, skipped: state.skipped,
                upToDate: state.upToDate, noSource: state.noSource,
                failureType: state.failure == null ? null : state.failure.getClass().name,
                actualProcessObservedByThisListener: false, libraryTestsExecuted: 0])
        }
    }
}
```

## Required interpretation and later verification

The receipts are **configuration/task-state observations**, not process
instrumentation. The lead's separately bounded runner must preserve the frozen
script, command, exit/timeout reason, reviewed actual `--info` process argv/cwd,
tool/input/output hashes, resource bounds and any failure. Do not dump sensitive
values. `executed`, `didWork` or overall Gradle success is not proof that Yarn
ran, scripts were suppressed in real packages or a lock/closure was enforced.

No actual root or included `beforeSettings` callback has been observed in this
proposal review. Public API inspection, static control-flow review and data/hash
checks do **not** test Groovy compilation, closure return/ownership integration,
root graph compatibility, duplicate-callback behavior, task execution or an
actual tooling install. Those remain for a separately authorized lead-owned
invocation; do not schedule one merely because this document exists.

During that later invocation confirm one root `requested-task.json`, exactly one
root pre-action/outcome observation if execution reaches them, no corresponding
receipt/listener effect from convention compilation, and the bound settings/build
identity on every emitted receipt. Deliberate wrong-context, reused-directory,
mixed-root-task and extra-prerequisite checks need separately bounded fixtures;
do not silently broaden this proposal when they fail.

If script compilation, identity/configuration, a prerequisite, a guard, task,
receipt write or runner fails, a later receipt may be absent. Absence is not a
successful check. An externally killed process may leave a partial receipt;
neither listener promises a terminal receipt after a kill. Preserve the failure
and let the runner account for it rather than overwriting evidence or retrying
automatically.

Passing this same `kotlin.user.home` to later ordinary Wasm tests is a separate
lead-owned command and environment receipt. No such reuse, ordinary/tooling graph
policy, actual script suppression, package provenance, Wasm library test,
BUILD-007 closure or release-gate success is established here.
