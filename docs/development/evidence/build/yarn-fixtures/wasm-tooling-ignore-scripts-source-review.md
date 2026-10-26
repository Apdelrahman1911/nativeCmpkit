# Wasm tooling: script-suppression propagation (source/bytecode only)

Additive lead-requested follow-up, **2026-10-24**. This is separate from the raw
fixture execution: no Gradle invocation, tooling install, configuration change or
shared-cache write was performed. The [structured record](wasm-tooling-ignore-scripts-source-review.json)
binds the inspected root file, installed KGP JAR and each referenced class.

**Answer:** in the inspected KGP **2.4.20** Yarn path, the configured
`WasmYarnRootEnvSpec.ignoreScripts=true` does propagate to
`KotlinToolingSetupTask`'s Yarn invocation. The task's separate `args` property
does **not** remove the independently supplied package-manager environment or its
`--ignore-scripts` argument.

Artifact: `kotlin-gradle-plugin-2.4.20-gradle96.jar`, SHA256
`6f49688f2c6715d60f5dc52d4c1ada992ce4bed6053d1bd6e579c9392d7ba0ed`.
These are **bytecode offsets**, not Kotlin source line numbers. Class names below
share the prefix `org.jetbrains.kotlin.gradle.targets.`.

| Class/method | Offsets | Inspected data flow |
|---|---|---|
| `wasm.yarn.WasmYarnPlugin.apply` | 16–35 | Selects `WasmYarnRootExtension` and `WasmYarnRootEnvSpec` for the shared applier. |
| `js.yarn.YarnPluginApplier.apply` | 105–198, 237–243 | Creates that spec/root pair; sets the Wasm Node root's `packageManagerExtension` to the Yarn root. |
| `wasm.yarn.WasmYarnRootExtension.<init>` | 39–55 | Passes its Wasm Yarn spec to `BaseYarnRootExtension`. |
| `wasm.nodejs.WasmNodeJsRootPlugin$kotlinToolingSetup$1.invoke` | 134–152 | Configures the tooling task with the **Wasm** Node root and Node spec through `configureNodeJsEnvironmentTasks`. |
| `web.nodejs.NodeJsRootPluginApplierKt.configureNodeJsEnvironmentTasks` | 78–104 | Binds `task.packageManagerEnv` to the selected root package-manager extension's environment and disallows task-property changes. |
| `web.nodejs.NodeJsRootPluginApplierKt$configureNodeJsEnvironmentTasks$2.transform` | 0–6 | The mapping calls `NpmApiExtension.getEnvironment()`. |
| `web.yarn.BaseYarnRootEnvSpec$produceEnv$1.transform` | 198–219, 312 | Reads the spec's `ignoreScripts` boolean and passes it to the `YarnEnv` constructor. |
| `web.yarn.BaseYarnRootExtension.finalizeConfiguration` | 0–22 | Returns the configured spec's environment. |
| `web.yarn.BaseYarnRootExtension$environment$2.invoke` | 0–13 | Obtains the configured `YarnEnv` and converts it to `YarnEnvironment`. |
| `js.yarn.YarnEnvironmentKt.getAsYarnEnvironment` | 18–26 | Copies `YarnEnv.ignoreScripts` into `YarnEnvironment`. |
| `js.npm.tasks.KotlinToolingSetupTask.install` | 419–434, 465–484 | Passes this `packageManagerEnv` **alongside** the task's own `args.get()` into `packageManagerExec`. |
| `js.yarn.YarnBasics.packageManagerExec` | 56–73 | Supplies the environment and args to the real execution lambda. The generic bridge casts to `YarnEnvironment` at 4 and forwards at 13. |
| `js.yarn.YarnBasics$packageManagerExec$1.invoke` | 38–55 | Reads `YarnEnvironment.ignoreScripts`; appends `--ignore-scripts` when true. |

The inspected root `build.gradle.kts` has `ignoreScripts.set(true)` at line **32**;
lines **46–47** apply its helper to `WasmYarnRootEnvSpec`. The structured companion
records its whole-file SHA256 and exact line excerpts, rather than attributing a
concurrently edited checkout to HEAD.

## Boundaries

- This confirms the configured source path **if that selected environment remains
  unchanged and is realized after configuration**. It does not observe effective
  argv, inherited config, the selected tool binary or script execution in a real
  Gradle command. Capture those in the lead-owned bounded invocation.
- Tooling can be skipped: `KotlinToolingSetupTask.install` checks whether its
  `nodeModules` directory exists at **98–111**, returning by **145**. A task's
  presence or successful build is not proof Yarn actually ran.
- Tooling still has its **own args and embedded lock**, separate from the two
  primary graphs. `ignoreScripts` is not a frozen-lock, lock-completeness,
  reproducibility, origin/provenance or package-trust assertion.
- Script suppression is not an OS/network sandbox and does not itself establish
  that installing/parsing untrusted packages is safe. No egress proof or release
  gate is claimed. Existing containment is unchanged.
