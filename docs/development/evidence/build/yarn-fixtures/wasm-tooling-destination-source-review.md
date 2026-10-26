# Wasm tooling destination and environment: source-only follow-up

**No Gradle, Node/Yarn, tooling install, cache mutation, or policy edit was
performed.** This additive review supports a later lead-scheduled
`:kotlinWasmToolingSetup` invocation. The [structured evidence](wasm-tooling-destination-source-review.json)
binds the installed KGP 2.4.20 artifact, relevant classes/resources and inspected
root build bytes. It does not observe a runtime destination or effective argv.

## Exact default destination rule

When the public `wasmNpmTooling.installationDir` property is **not** set, the
selected Yarn path is:

```text
<KGP kotlin.user.home property, else JVM user.home/.kotlin>
  /kotlin-npm-tooling/yarn/<versionsHash>
```

`nodeModules` is `<destination>/node_modules`; actual Yarn working directory is
the task's **destination**, not `build/wasm` or the Node environment's primary
root package directory. This default cache is not rooted in `GRADLE_USER_HOME`.
No concrete versions hash/current runtime path has been guessed or realized.

The `versionsHash` is the hex representation of an **MD5 cache key**
over each supplied dependency's UTF-8 name, requested version and resolved
version, in list order, with missing values replaced by empty strings and no
separators between those three updates. It is not a cryptographic integrity or
provenance assertion; it does not hash package archives or the embedded lock.

The path prefix `/root/.kotlin/kotlin-npm-tooling/yarn` existed as a directory
and was not itself a symlink at the recorded read-only presence check. No children
were enumerated or changed, and its presence does not identify the next task's selected hash or
prove that the selected `node_modules` exists/is complete.

## Source locations

Artifact SHA256:
`6f49688f2c6715d60f5dc52d4c1ada992ce4bed6053d1bd6e579c9392d7ba0ed`.
Offsets below are **bytecode offsets**, not Kotlin source line numbers. Unless
otherwise shown, names start with `org.jetbrains.kotlin.gradle.targets.`.

| Class / method | Offsets | Rule |
|---|---|---|
| `wasm.nodejs.WasmNodeJsRootPlugin.kotlinToolingSetup` | 94–112; 140–187 | Creates extension `wasmNpmTooling`; binds default installation base to user Kotlin persistent directory, tooling folder, and selected package-manager name. |
| `org.jetbrains.kotlin.gradle.utils.PersistentCachesKt.getUserKotlinPersistentDir` | 6–53 | KGP user-home property overrides the `System.getProperty("user.home")/.kotlin` fallback. |
| `org.jetbrains.kotlin.gradle.plugin.PropertiesProvider.getKotlinUserHomeDir` | 0–10 | Reads its property through KGP's property provider. |
| `org.jetbrains.kotlin.gradle.plugin.PropertiesProvider$PropertyNames.<clinit>` | 491–500 | Exact property key: `kotlin.user.home`. |
| `js.npm.tasks.KotlinToolingSetupTask$Companion$NPM_TOOLING_DIR_NAME$2.invoke` | 0–10 | Reads resource `project.properties`, key `kotlin.web.npm.tooling.dir.name`. |
| `project.properties` in the JAR | line 3 | `kotlin.web.npm.tooling.dir.name=kotlin-npm-tooling`. |
| `wasm.nodejs.WasmNodeJsRootPlugin$kotlinToolingSetup$packageManagerName$1.transform` | 0–6 | Uses selected package-manager extension's `name`. |
| `web.yarn.BaseYarnRootExtension.getName` | 0–2 | Yarn name is exactly `yarn`. |
| `wasm.nodejs.WasmNodeJsRootPlugin$kotlinToolingSetup$npmTooling$1$1.apply` | 0–7 | Adds that manager name as a directory component. |
| `wasm.nodejs.WasmNpmTooling$produceEnv$1.transform` | 0–229; 230–311 | Computes cache hash; chooses explicit directory or default base plus hash; creates `web.nodejs.NpmToolingEnv(version, dir, explicitDir)`. |
| `wasm.nodejs.WasmNpmTooling$produceEnv$1$nodeDir$1.transform` | 0–10 | Adds the versions hash as a child directory. |
| `wasm.nodejs.WasmNodeJsRootPlugin$kotlinToolingSetup$1.invoke` | 76–129 | Binds task destination/nodeModules providers and calls `disallowChanges()` on both. |
| Same callback's `$1$3.transform` / `$1$4.transform` | 0–4 / 0–9 | Map environment to `dir` / `dir.resolve("node_modules")`. |
| `js.npm.tasks.KotlinToolingSetupTask.install` | 437–484 | Passes destination's file provider as actual package-manager working directory, independently of task args and package-manager environment. |

## Two skip traps and pre-invocation writes

1. **Do not use `wasmNpmTooling.installationDir` merely to redirect an install.**
   Its presence sets `NpmToolingEnv.explicitDir=true`
   (`WasmNpmTooling$produceEnv$1.transform`, **230–242**). The registered
   `onlyIf` callback `$kotlinToolingSetup$1$1.isSatisfiedBy`, **0–23**, returns
   `!explicitDir`: an explicit directory means dependencies are expected to be
   preinstalled, so the task skips. Changing task destination/nodeModules after
   their normal configuration is also not a supported redirect: both properties
   have been locked with `disallowChanges()`.
2. `$kotlinToolingSetup$1$6.isSatisfiedBy`, **0–16**, uses `nodeModules.exists()`
   for its up-to-date predicate. Even if the action executes,
   `KotlinToolingSetupTask.install`, **98–145**, returns when that path exists.
   This is not a completeness or integrity check. Forcing task execution alone
   therefore does not prove Yarn ran. Never delete a shared cache just to force
   this observation.
3. The action opens/locks `<destination>/lock` first (**0–86**), before that
   action-level early return. On its real install path it writes
   `<destination>/package.json` (**146–354**), then calls `prepareTooling`
   (**355–371**) before invoking Yarn.
4. `js.yarn.YarnBasics.prepareTooling`, **6–59**, opens a `FileOutputStream` for
   `<destination>/yarn.lock` and copies KGP's embedded
   `org/jetbrains/kotlin/gradle/targets/js/yarn/yarn.lock` into it. This can replace
   a prior destination lock **before** Yarn's invocation. Passing a frozen flag
   to Yarn is not a no-pre-invocation-lock-write guarantee for this task.

The embedded lock is **160,311 bytes**, SHA256
`52abe46477f1343005d5059baa218042f7555e03060f2a7f0f39645dfb996dcb`.
It is separate from the two primary project stores. Its presence/hash neither
trusts its dependency provenance nor proves tooling installs from it unchanged.

## Allowlisted values for the later actual receipt

The inspected public APIs permit recording these specific values. Inspect
argv/URLs before logging and redact credential-bearing values; never print whole
environment objects, credentials, or host environment dumps.

- Task path, task outcome, `destination.get().asFile`, `nodeModules.get().asFile`,
  and `args.get()` (this task uses `ListProperty<String>`).
- `nodeJsEnvironment.get().nodeExecutable` and selected package-manager class.
- After checking that `packageManagerEnv.get()` is a `YarnEnvironment`:
  `executable`, `standalone`, `ignoreScripts`, and reviewed resolution entries
  (redact/reject any credential-bearing value rather than logging it).
- Actual process argv/cwd and file/tool hashes, separately from these configured
  properties. Record whether the action reached Yarn at all.

The existing [script-propagation review](wasm-tooling-ignore-scripts-source-review.md)
proves the conditional source path from configured Wasm Yarn `ignoreScripts`
to `--ignore-scripts`. It does not prove the next command's final environment,
selected tool version, effective inherited config, cache freshness or argv.

A fresh task-owned `kotlin.user.home` is a **source-supported candidate** for
moving the default tooling cache without setting the explicit-directory skip
flag. This review did not execute/validate that CLI configuration, choose an
output directory, or authorize downloads. The lead must still schedule the
bounded invocation, inspect the resolved providers, protect the disk reserve,
and retain original failures. No sandbox, frozen/closure policy, trust or
release gate is established by this source-only review.
