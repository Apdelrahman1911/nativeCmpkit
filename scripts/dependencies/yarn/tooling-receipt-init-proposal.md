# Lead-owned Wasm tooling receipt: unexecuted init-script proposal

**Design/snippet only.** No init script, Gradle invocation, tool install, parser
or live policy was executed/adopted by this review. Public API signatures were
checked in the installed Gradle 9.7.1/KGP 2.4.20 JARs; **Groovy compilation and
runtime integration remain unverified**. The lead may copy/review a task-owned
script only in the separately scheduled invocation.

See [destination/environment source evidence][destination] and the
[API/hash binding][api]. The exact task is `:kotlinWasmToolingSetup`.

[destination]: ../../../docs/development/evidence/build/yarn-fixtures/wasm-tooling-destination-source-review.md
[api]: ../../../docs/development/evidence/build/yarn-fixtures/wasm-tooling-init-api-review.json

## Intended use and non-guarantees

- Allocate a **fresh absolute run root**, a `receipts/` child, and an absent or
  empty `kotlin-user-home/` child. Replace the single literal below with that
  lead-owned run root, freeze/hash the resulting init script, then use
  `-Pkotlin.user.home=<run-root>/kotlin-user-home` for this invocation.
- The two executable-path literals match this host's previously pinned raw
  fixture tools. Recheck their frozen hashes separately before scheduling;
  unexpected selected paths are rejected without printing their values. These
  local paths and hashes identify bytes, not independent provenance.
- Request exactly `:kotlinWasmToolingSetup`, with canonical
  `--rerun-tasks --no-configuration-cache`, the lead's approved bounded runner,
  reserve, `--info` and other non-task flags. Do not substitute arbitrary task
  abbreviations, `-x`, a dry run, or a `wasmNpmTooling.installationDir` override.
- This snippet **reads** task/environment properties; it does not configure
  destination, args, Node/Yarn, scripts, dependency versions, or task ordering.
  Its only intentional writes are exclusive-create JSON receipts in the
  allocated directory. It does not enable configuration-cache support.
- A fresh `kotlin.user.home` isolates the source-derived default **tooling
  destination**, not HOME, the Yarn package cache, all Gradle/Kotlin caches,
  network access, or the OS. The parent runner's separate environment/config
  policy still matters. Do not dump environment variables or whole environment
  objects to fill that gap.
- The requested-task equality check occurs when the init script is evaluated.
  A second graph allowlist permits only the target and the two known root
  setup prerequisites. **That small graph allowlist is unexecuted**; if a real
  additional prerequisite appears, fail and review it rather than automatically
  retrying or permitting every task. It prevents silent install/upgrade/consumer
  mixing within this proposed diagnostic entry point, not malicious build code.
- This narrowly expected environment has empty task args and empty Yarn
  resolutions. Reject nonempty values **without dumping them**. In particular,
  `YarnResolution` exposes `path`, `includedVersions`, `excludedVersions`, not an
  imagined singular `version` member. Do not call its `toString()` as a receipt.
- Capture before task actions with `whenReady`, not just `doFirst`, so a skipped
  task cannot omit the pre-action observation. Even `--rerun-tasks` cannot
  bypass the action's existing-`node_modules` early return. Require the selected
  destination's modules to be absent in this cold diagnostic.

## Proposed Groovy init script

KGP classes are intentionally **not imported** into the init-script classloader.
The snippet uses public getters on the actual task objects and checks runtime
type names; it does not introduce a second KGP dependency/classloader.

```groovy
import groovy.json.JsonOutput
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.StandardOpenOption

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

def sp = gradle.startParameter
requireValue(sp.taskNames == [wanted], 'Only the exact tooling task may be requested')
requireValue(sp.excludedTaskNames.isEmpty(), 'Task exclusions are not allowed')
requireValue(!sp.isDryRun(), 'Dry run is not a tooling execution')
requireValue(!sp.isConfigurationCacheRequested(), 'Use --no-configuration-cache')
requireValue(sp.isRerunTasks(), 'Use canonical --rerun-tasks for this diagnostic')
def selectedHome = sp.projectProperties.get('kotlin.user.home')
requireValue(selectedHome != null && new File(selectedHome).isAbsolute() &&
             new File(selectedHome).canonicalFile == home.canonicalFile,
             'Pass the exact fresh task-owned kotlin.user.home project property')

def writeNew = { String name, Map value ->
    requireValue(name in ['requested-task.json', 'tooling-pre-action.json',
                          'tooling-task-outcome.json'], 'Unexpected receipt name')
    def payload = value + [schemaVersion: 1, observedUtc: java.time.Instant.now().toString()]
    def json = JsonOutput.prettyPrint(JsonOutput.toJson(payload)) + '\n'
    Files.writeString(new File(receipts, name).toPath(), json,
        StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
}
writeNew('requested-task.json', [taskNames: sp.taskNames,
    excludedTaskNames: [], configurationCacheRequested: false, dryRun: false,
    rerunTasks: true, kotlinUserHome: home.absolutePath,
    actualProcessObserved: false, libraryTestsExecuted: 0])

def allowedGraph = [wanted, ':kotlinWasmNodeJsSetup', ':kotlinWasmYarnSetup'] as Set
gradle.taskGraph.whenReady { graph ->
    def tasks = graph.allTasks
    requireValue(tasks.every { it.path in allowedGraph },
                 'Unexpected prerequisite/task; stop and review actual graph')
    def task = tasks.find { it.path == wanted }
    requireValue(task != null, 'Tooling task absent from actual graph')
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
    // The lead must review/freeze expected executable paths and hashes separately.
    // These are paths from public fields, not whole environment object dumps.
    writeNew('tooling-pre-action.json', [taskPath: task.path,
        graphTaskPaths: tasks.collect { it.path }, destination: destination.path,
        nodeModules: modules.path, nodeModulesExisted: false, args: args,
        nodeExecutable: node.nodeExecutable, yarnExecutable: yarn.executable,
        yarnStandalone: yarn.standalone, ignoreScripts: yarn.ignoreScripts,
        yarnResolutions: [], actualProcessObserved: false,
        frozenOrClosurePolicyVerified: false, provenanceVerified: false])
}
gradle.taskGraph.afterTask { task, state ->
    if (task.path == wanted) {
        writeNew('tooling-task-outcome.json', [taskPath: task.path,
            executed: state.executed, didWork: state.didWork, skipped: state.skipped,
            upToDate: state.upToDate, noSource: state.noSource,
            failureType: state.failure == null ? null : state.failure.getClass().name,
            actualProcessObservedByThisListener: false, libraryTestsExecuted: 0])
    }
}
```

## Required interpretation of the later command

The above receipts are **configuration/task-state observations**, not direct
process instrumentation. The bounded runner must separately retain the command,
exit/timeout reason, actual `--info` process argv/cwd (reviewed for sensitive
values), selected tool hashes, output/input hashes, and resource bounds. A
task's `executed`, `didWork`, or overall Gradle success does not prove Yarn ran,
that scripts were suppressed in real packages, or that a lock was enforced.

If configuration, a prerequisite, a graph guard, script compilation, or the
runner fails, a later receipt may be absent. Preserve that failure and never
interpret absence as a successful check. No listener can promise a terminal
receipt after an external kill; that is the runner's responsibility.

Passing the same `kotlin.user.home` to later ordinary Wasm tests is a separate
lead-owned invocation and environment receipt. This proposal does not claim
that such reuse, either graph's dependency policy, script behavior, tooling
installation, or any Wasm library test has already been observed.
