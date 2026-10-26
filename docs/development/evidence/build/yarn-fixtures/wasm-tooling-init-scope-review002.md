# Wasm tooling receipt proposal: additive scope correction 002

**Source/API review only. No Gradle, Groovy compilation, Node/Yarn installation,
network request, policy adoption or library test was performed by this correction.**
The [v2 proposal][v2] corrects a confirmed control-flow defect in the **unexecuted**
[v1 proposal][v1]; it does not establish an actual tooling install or close BUILD-007.
The [machine-readable binding][json] records inspected files, class hashes and
read-only `javap` results. The [independent review][review] owns its separate
installed-bytecode/control-flow evidence.

[v1]: ../../../../../scripts/dependencies/yarn/tooling-receipt-init-proposal.md
[v2]: ../../../../../scripts/dependencies/yarn/tooling-receipt-init-proposal-v2.md
[json]: wasm-tooling-init-scope-review002.json
[review]: ../../review/dependency-tooling-independent.md
[checkpoint]: wasm-tooling-init-scope-checkpoint001.json
[index-snapshot]: wasm-tooling-init-v1-evidence-index.md
[original-api]: wasm-tooling-init-api-review.json
[original-verification]: documentation-verification001.json

## Preserved failure history

The [checkpoint][checkpoint] verifies the following original bytes without editing
them. The [original evidence index][index-snapshot] is also preserved byte-for-byte
before updating the live index to warn against v1 adoption.

| Original record | SHA256 |
|---|---|
| v1 proposal | `7febc84a82896342a38e42bcd328eb9a77e91e4127577a1b3720c643e9727af1` |
| [v1 installed API review][original-api] | `6354cf0d56f11e116c3c4df218edba1debffb01b701e9cb95eca8b03ed68522e` |
| [original documentation readback][original-verification] | `f05ddb3fe38ce51e8c59e010655d7eeb6396169df1a850e60481b4686b18d092` |

That earlier successful readback established historical hash/link/API consistency,
**not** semantic correctness, a compiled script or included-build behavior. It is
not rewritten to imply that it found the later scope defect. The newly found
problem is a proposal defect, not an observed failed Gradle invocation.

## Root cause and consequence

Current `settings.gradle.kts:4–5` includes `convention-plugins` in
`pluginManagement`; `convention-plugins/settings.gradle.kts:1–24` is a distinct
settings context. V1 proposal lines **72–93** perform root run-directory,
fresh-home, requested-task and project-property checks during init evaluation.
Lines **95–106** define/write the exclusive requested receipt, and **108–161**
attach unqualified graph/outcome listeners. None first identifies the actual
settings directory/build that received the init script.

The independent reviewer inspected the **installed Gradle 9.7.1 class bytes**:

| Implementation | Source-confirmed implication, not an executed trace |
|---|---|
| `BuildDefinition.startParameterForIncludedBuildFrom` and `StartParameter.newBuild` | Included-build start parameters copy init scripts but reset task requests; root requested-task equality is not an included-build invariant. |
| `DefaultSettingsPreparer.loadBuild` | Init scripts are processed before finding/loading settings in each prepared build. |
| `ScriptEvaluatingSettingsProcessor.process` | Settings construction precedes `beforeSettings`, which precedes settings-script application. |
| `DefaultIncludedBuildRegistry`, `DefaultIncludedBuildFactory`, `AbstractBuildState`, `DefaultGradle.getParent` | Registered included builds are given a non-null parent, exposed through the public Gradle model. Parent role can supplement, but cannot replace, directory identity. |

Thus v1 has a concrete source-level path to falsely rejecting the included
convention build's empty/reset task list. Removing only that equality would leave
root freshness checks, duplicate exclusive writes, and child compilation subject
to a root-only task allowlist. **No v1 init script was run to reproduce this.**

## V2 control-flow correction

The corrected v2 proposal has SHA256
`e1697dc6345bc9e5fb4f2b78a2f3ea86f796929184e272fdfc634afbc32d338d`.
Its line numbers are bound to that exact document, not the imported source baseline.

| V2 lines | Reviewed responsibility |
|---|---|
| 103–108 | Imports plus a public `gradle.beforeSettings` registration; no root-only gates, writes or task listeners at global init evaluation. |
| 109–127 | Read `actualSettings.settingsDir.canonicalFile` and `actualSettings.gradle`; exact known convention + non-null parent returns immediately, exact root + null parent continues, wrong role/unknown/overlapping identity rejects. |
| 129–157 | All root-only fresh-directory, task-list/flag and `kotlin.user.home` gates run only after root-context acceptance. |
| 159–175 | Every receipt carries canonical settings/build identity. Exclusive requested-receipt creation precedes both listener registrations, preventing silent duplicate registration/overwrite. |
| 177–185, 225–228 | Attach to the accepted settings object's Gradle instance only. Each graph/outcome task must have that same Gradle identity and canonical root directory, as well as an allowed local task path. |
| 186–223, 229–233 | Preserve the original KGP type/environment/fresh-destination observations and task-state-only outcome semantics. No process-execution or policy success assertion. |

Public signatures were independently rechecked with read-only `javap` in the
pinned core-API JAR: `Settings.getSettingsDir/getGradle`,
`Gradle.beforeSettings(Closure)/getParent/getBuildPath/getStartParameter/getTaskGraph`,
`Task.getProject/getPath`, and `Project.getGradle/getRootDir`. The unchanged KGP,
task-graph, task-state and JSON getter evidence remains in the preserved v1 API
record. The independent reviewer additionally checked `DefaultGradle.getBuildPath`
does not require root-project realization.

This chooses `beforeSettings`, not `settingsEvaluated`: convention plugin builds
may be needed while root settings are being evaluated. It still runs **after init
scripts and earlier Gradle work**, and is neither a network/OS sandbox nor proof
of no previous cache/configuration side effects. Permitted convention compilation
is intentionally **outside** the root graph allowlist, not approved by that gate.

## Review result and remaining gates

The independent metadata reviewer reported **source-only GREEN** for the v2 hash
above: directory/parent-role classification, root-effect ordering, exclusive
receipt ordering and graph/task ownership. See its separate review record for
persisted evidence and scope. The final additive readback checks bytes/API/link
consistency; its checks are **data checks, not additional executed tests**.

Still unverified: Groovy compilation and closure dispatch/return semantics in a
real invocation; actual settings callback multiplicity/order; per-build graph
behavior and the conservative root prerequisite allowlist; task property
realization; duplicate/wrong-context/mixed-task negative cases; actual Yarn
argv/cwd, scripts and installation; later same-home Wasm test reuse. An external
bounded runner must preserve failures, partial/absent receipts and terminal
status. API existence and static review do not authorize launching a diagnostic,
adopting policy, package provenance, finding closure or publication.
