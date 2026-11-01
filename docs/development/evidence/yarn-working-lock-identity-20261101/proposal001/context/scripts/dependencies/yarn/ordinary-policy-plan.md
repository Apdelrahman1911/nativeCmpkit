# Ordinary Yarn builds: bounded preflight/frozen design proposal

**Status: design only; not implemented, applied, or executed.** This is the
lead-requested next step after the [raw fixtures][raw]. It does not change the
live Gradle build, bootstrap mode, lockfiles, source modules, CI, or publishing.
BUILD-007 remains open. The smallest useful next increment is an offline
selector-closure checker plus an **isolated** KGP integration prototype, not a
package-manager replacement or a general npm resolver.

[raw]: ../../../docs/development/evidence/build/yarn-fixtures/README.md
[review]: ../../../docs/development/evidence/build/yarn-frozen-policy-review.md
[observation]: ../../../docs/development/evidence/build/yarn-fixtures/ordinary-policy-graph-observation001.json
[wasm]: ../../../docs/development/evidence/build/yarn-fixtures/wasm-tooling-ignore-scripts-source-review.md

## 1. Problem and deliberately limited assurance

Raw Node 24.16.0 / Yarn 1.22.22 actually accepted both of these with
`--frozen-lockfile`:

1. No `yarn.lock`: it installed the authored parent and leaf without creating a
   lock (YF002).
2. Parent stanza present, leaf stanza removed, parent's leaf dependency still
   present: it installed both packages without repairing the incomplete lock
   (YF006).

The [installed KGP review][review] separately shows that the current
`yarnLockMismatchReport=FAIL`, `yarnLockAutoReplace=false`, `reportNewYarnLock=true`
are **post-install store policy**, not a pre-install/frozen guarantee. Restore
can skip a missing store; store can create a previously missing store and then
fail. Upgrade tasks force their shared install dependency. An upgrade task's
own `doFirst` is consequently too late to prevent that install.

Proposed assurance is only:

> For a supported primary graph in ordinary mode, require an existing stored
> lock and verify that every external selector reachable from the generated
> root and all its declared workspace manifests has a lock stanza, including
> dependency and optional-dependency edges declared in those stanzas. Then use
> the ordinary frozen/script-suppressed Yarn path without updating the store.

This checks **declared selector closure**, not the truth of dependency metadata,
semver solution correctness, installed `node_modules`, independent provenance,
malicious package behavior, or a release gate. Removing both a parent's declared
edge and its child's stanza can defeat a lock-only metadata check. A valid SRI
can come from an untrusted source. The valid-but-wrong SRI in YF004 is expected
to pass a syntax check and fail only when Yarn checks actual fetched bytes.

The Gradle build and adapter are assumed not to be maliciously rewritten. This
is not an OS/egress sandbox or enforcement against arbitrary direct Yarn calls.
No stronger security claim should be attached to a successful preflight.

## 2. Read-only current-input observations

The [structured observation][observation] records whole-file hashes of the two
stored locks, generated roots, **every declared workspace manifest**, and the
installed KGP artifact/classes used below. These are working-tree observations,
not an immutable revision's build or a parser validation result. No generated
root or workspace was regenerated for this review.

| Primary scope | Stored lock | Bytes / lexical stanzas | Generated root / declared workspaces |
|---|---|---:|---|
| JS | `kotlin-js-store/yarn.lock` | 144,040 / 439 | `build/js/package.json` / 62 |
| Wasm | `kotlin-js-store/wasm/yarn.lock` | 590 / 2 | `build/wasm/package.json` / 60 |

Both roots have **no external dependencies of their own**. Checking only the
root manifest would miss the real dependency seeds. All listed workspace
manifests were present with unique workspace names and literal relative paths
under `packages/` or `packages_imported/`. Across these roots/workspaces,
`resolutions`, `peerDependencies`, and `optionalDependencies` were absent/empty.
That is an observation, not permission to ignore them in future inputs.

Wasm primary directly requests `@js-joda/core@3.2.0` and `ws@8.20.1`. JS also
requests the Karma/Mocha/Webpack toolchain. The JS lock has four stanzas with
optional dependencies, three npm alias selectors, and a **GitHub resolver with
no SRI**:

| Current JS location | Resolver detail the checker must not guess about |
|---|---|
| `kotlin-js-store/yarn.lock:1864–1892` | `karma@github:Kotlin/karma#6.4.5`; package version `6.4.4`; codeload commit `239a8fc984584f0d96b1dd750e7a5e2c79da93a6`; 24 dependency edges; no `integrity` field |
| `kotlin-js-store/yarn.lock:2726` | `string-width-cjs@npm:string-width@^4.2.0` |
| `kotlin-js-store/yarn.lock:2753` | `strip-ansi-cjs@npm:strip-ansi@^6.0.1` |
| `kotlin-js-store/yarn.lock:3067` | `wrap-ansi-cjs@npm:wrap-ansi@^7.0.0` |

Therefore an initial registry-only implementation must **reject the current JS
graph**, not report both graphs verified. Even Wasm primary is only a candidate
for that profile until the checker is implemented/tested. Its two stanzas do
not include Wasm's separate browser tooling graph.

## 3. Smallest candidate task integration

These names are observed in the retained actual task-discovery log, not guessed:

| Scope | Root manifest | Primary install | Restore / store / explicit upgrade |
|---|---|---|---|
| JS | `:rootPackageJson` | `:kotlinNpmInstall` | `:kotlinRestoreYarnLock` / `:kotlinStoreYarnLock` / `:kotlinUpgradeYarnLock` |
| Wasm | `:wasmRootPackageJson` | `:kotlinWasmNpmInstall` | `:kotlinWasmRestoreYarnLock` / `:kotlinWasmStoreYarnLock` / `:kotlinWasmUpgradeYarnLock` |

Manifest umbrellas are `:kotlinPackageJsonUmbrella` and
`:kotlinWasmPackageJsonUmbrella`. Separate Wasm browser tooling is exactly
**`:kotlinWasmToolingSetup`**, not `:kotlinWasmKotlinToolingSetup`.

In KGP 2.4.20, `NodeJsRootPluginApplier$apply$rootPackageJson$1.execute` depends
on its manifest umbrella at bytecode **95–112**. Its primary-install callback
`NodeJsRootPluginApplier$apply$npmInstall$1.invoke` depends on the root manifest
at **243–260** and preinstall tasks at **284–315**. Root generation calls the
resolution manager's preparation method, not the install task action
(`RootPackageJsonTask.resolve`, **0–61**). These observations suggest this
candidate ordering; they are **not** a cycle-free runtime integration test:

```text
graph-mode gate: before any task actions; reject forbidden upgrade/mixed modes
    |
stored-lock guard: always run; require regular existing lock; parse structure
    |
real manifest umbrella -> real root manifest generation
    |
closure guard: always run; read root + all declared workspaces + stored lock
    |
restore -> invocation-boundary check -> ordinary frozen primary install
    |
store-boundary check -> existing mismatch-enforcing store
```

Required integration properties:

1. **Separate always-run guards, not just install `doFirst`.** Missing stored
   lock and basic syntax must fail before restore/install/store mutations.
   Root-generation prerequisites must not allow a sibling restore to run first.
   The closure guard depends on actual root generation; restore and install
   depend on the closure guard. Verify the real graph does not introduce a
   cycle through an umbrella or another plugin.
2. Guards remain mandatory for direct restore/store requests and npm-requiring
   consumers, even when installation is skipped, up-to-date, or restored from a
   cache. A standalone store request must not recreate a missing store. A
   previous success file is not a preflight. Do not cache the guard action or
   give it an `onlyIf` that skips the policy when a lock is missing.
3. Retain the checked lock and manifest-set hashes. Recheck at the invocation
   and store boundaries; after restore, require the generated working lock to
   match the checked stored bytes. Require stored bytes unchanged after the
   ordinary path. This is intentionally stricter than KGP's line-ending-equal
   comparison, and does **not** promise atomicity against concurrent writers.
4. Record guard/task outcomes and actual invocation separately. A missing
   mandatory Gradle `@InputFile` validation error or unrelated plugin/network
   error is not evidence that the intended guard action executed. Design the
   guard's inputs so its absent-lock diagnostic is observable and test it.
5. Reject unsupported package managers, relevant policy-task exclusions,
   bypass args/config, and unknown integration states rather than silently
   falling back. Prototype tests must include `-x` exclusions; if a dependable
   consumer/guard boundary cannot be identified, keep adoption blocked.

The early guard does not promise zero Gradle configuration/cache/Maven activity.
Even successful manifest generation can perform dependency-resolution work.
The no-Node/no-registry-request assertion belongs to the controlled raw
preflight fixtures, not an uninstrumented ordinary Gradle build.

### Ordinary versus explicit bootstrap/update

- Default is ordinary. A proposed strict property such as
  `nativecmpkit.yarnMode=ordinary|bootstrap` is a **design name only**, not a
  supported current CLI. Reject unknown values.
- Reject any real graph containing a Yarn upgrade task in ordinary mode **before
  task execution**. Do not use only `startParameter.taskNames`: abbreviations
  and indirect upgrade dependencies exist. Reject mixed build/test/consumer
  plus upgrade graphs, rather than letting the upgrade force their shared
  install. A bootstrap graph must be limited to explicit upgrade tasks and
  reviewed prerequisites; a property by itself is not an ordinary-build bypass.
- A first isolated prototype may use `taskGraph.whenReady` **only with an
  explicit configuration-cache rejection**. Do not claim configuration-cache
  compatibility. Either produce and test a cache-compatible production design
  later, or explicitly adopt the restriction with the build owner's agreement.
- For ordinary primary tasks, the inspected public API is
  `KotlinNpmInstallTask.args`, a mutable `List<String>`; it is not a
  `ListProperty`. Add `--frozen-lockfile` only in ordinary mode. Retain
  `ignoreScripts=true`; reject force/checksum-update/no-lock/other bypass modes
  and unsupported relevant Yarn rc/resolution settings. Capture actual argv in
  tests: this API inspection is not proof of effective options.
- Bootstrap intentionally permits lock generation/update without the frozen
  flag, still suppresses lifecycle scripts, records diffs and input hashes, and
  requires a subsequent ordinary verification. No automatic retry in bootstrap,
  checksum repair, fallback resolver, or silent change to an existing lock.
- An absent lock is **never** inferred to mean an empty graph. Initially reject
  absence even for empty manifests. Existing header-only locks can be supported
  only after proving all manifests have no external seeds. KGP's native upgrade
  can delete an empty stored lock; define and test an explicit empty-lock
  bootstrap convention before claiming empty-graph support.

The selected tools and relevant config must be inspectable without logging
credentials or environment dumps. For the prototype, use fixture-owned config,
HOME/cache/temp and a pinned tool wrapper/receipt. Do not silently impose that
fixture environment on every developer build or claim host-environment safety.

## 4. Narrow offline checker contract

This section specifies future behavior. The raw harness's small `lock_blocks`
helper is fixture-specific and **must not become the production parser**.

### Inputs and fail-closed syntax

- Read only the configured stored lock, actual generated root manifest, and the
  exact workspace manifests it declares. No package download, Yarn/Node call,
  installed-module scan, modification, glob expansion, or script execution.
- Reject missing/non-regular/symlinked inputs and path traversal. Support only
  literal root-relative workspace arrays initially; reject absolute paths,
  globs, object-form workspaces, nested workspaces, duplicate paths/names and
  escapes through ancestor symlinks. Check every declared manifest, not only
  the subset containing obvious dependencies.
- Bound reads and graph work before allocation/traversal. Initial proposed caps:
  2 MiB lock, 64 KiB line, 10,000 stanzas, 100,000 edges, 256 workspaces, 1 MiB
  per manifest / 8 MiB aggregate. These are draft limits to fixture-test and
  document, not proven existing resource guarantees.
- Parse JSON with duplicate-key/type checks. Dependency-bearing maps must map
  names to strings; do not coerce null/numbers/arrays. Treat inert package
  metadata as data, not instructions. Nonempty unsupported resolution, peer,
  bundling, workspace or install-semantic fields fail explicitly. Empty fields
  are accepted only in their documented types.
- Implement a strict Yarn-v1 tokenizer with complete input consumption, correct
  quoted-string escapes, quote-aware multi-selector headers, and explicit
  zero/two/four-space nesting. Do not split headers blindly on commas, use
  indentation regexes as a general parser, or invoke a general YAML loader.
  Reject duplicate selectors/fields/dependency keys, unknown sections/scalars,
  invalid indentation/encoding, trailing junk and unsupported versions. Accept
  tested LF/CRLF input without rewriting its bytes.
- Initially allow only the reviewed `version`, `resolved`, `integrity`,
  `dependencies`, and `optionalDependencies` stanza fields. Validate supported
  resolver/SRI syntax without treating syntax or a URL as proof of origin.
  Registry SHA-512 tokens must decode canonically to 64 bytes. Do not synthesize
  integrity from a URL fragment, accept a malformed token, or fetch missing data.

### Selector closure, without a new semver solver

1. Index **each exact selector** in every grouped header to its stanza. Preserve
   full range text, scoped package names and quoting meaning. Do not collapse
   `foo@^1`, `foo@~1`, and `foo@1` to a name-only or resolved-version match.
2. Seed dependencies, devDependencies and optionalDependencies of the root
   **and every declared workspace**, independent of build production mode.
   If optional and ordinary dependency entries conflict, reject until their
   precedence is deliberately implemented/tested; do not guess.
3. Resolve an external seed by exact selector membership and then traverse
   every declared dependency and optional-dependency edge to exact selectors.
   Require optional closure conservatively across platforms; never discard an
   edge because it is not installed on this host. Use an iterative visited set
   so legitimate cycles terminate and bounds remain enforceable.
4. A missing selector is a deterministic failure with a bounded path such as
   `workspace test -> parent@1.0.0 -> leaf@1.0.0`, including source manifest or
   lock line. Empty root dependencies do not short-circuit workspace traversal.
   Unreachable old stanzas may be reported, but never satisfy another selector.
5. Local workspace links need a separate exact-name/version rule, not an absent
   lock exemption by name alone. Initially support only unambiguous exact
   local-version matches; reject local ranges/protocols until tested. Current
   observed seed edges do not target workspace names. Do not apply public npm
   publishing-name rules blindly to KGP's mixed-case private workspace names.
6. Recognize only explicitly supported registry-range/tag grammar; preserve it
   exactly. This is not a second semver solver: a stanza's mere presence does
   not prove its version satisfies that range. Unknown resolver syntax fails,
   rather than being reclassified as a plain registry version.

### Resolver profiles and the current JS adoption blocker

Keep resolver acceptance explicit and separate from closure traversal:

- **First profile:** reviewed registry selectors, scoped packages, supported
  ranges/tags, HTTPS registry origins and canonical SHA-512 syntax. Parse URLs
  structurally; reject credentials, unexpected hosts/schemes/query forms and
  ambiguous package paths. The controlled fixture profile may allow its exact
  loopback origin only; it must not become a production network fallback.
- **Small additive next profile:** npm aliases, with dedicated fixtures. Index
  `alias@npm:real-name@range` by the requested alias selector while validating
  the **real target** in the resolution. Do not compare an alias name directly
  to its tarball's real package path or erase the alias prefix.
- **Git/GitHub/file/link/patch/exotic forms:** reject unless separately modeled
  and reviewed. In particular, do not call Karma's Git tag `6.4.5` versus package
  version `6.4.4` a semver drift, and do not treat the commit URL as SHA-512
  byte-integrity evidence. No dependency substitution or Git exception is
  authorized by this proposal.
- If the build owner later chooses a narrow Karma exception, it needs its own
  decision and tests binding the exact selector, pinned commit URL and declared
  stanza/metadata bytes. The exception must still disclose missing independent
  byte integrity/provenance. It must not turn every no-SRI Git lock into a pass.

## 5. Bounded implementation and actual-test gates

Do **not** run these merely because they appear here. Obtain the lead's next
execution slot and preserve fresh run IDs, frozen inputs and exact receipts.
Each actual batch remains at most 300 seconds with at least 8 GiB disk reserve;
split the matrix into small scheduled batches rather than one unbounded build.
No arbitrary downloads, external fixture packages, shared-cache cleanup or
publishing is part of the plan.

| Phase | Small increment | Required observations before moving on |
|---|---|---|
| P1 | Offline parser + closure library/CLI under this directory, no live Gradle wiring | Full grammar consumption; malformed/duplicate/oversized inputs; grouped/scoped selectors; missing root/workspace/stanza; empty-root/nonempty-workspaces; optional edges; cycles; path escapes; unsupported resolutions; alias/Git rejection; no real child process/socket |
| P2 | Controlled preflight wrapper around the existing authored raw graph | Missing lock and removed transitive leaf rejected **before Node invocation or registry requests**; complete graph reaches Yarn; wrong valid SRI and changed valid tarball still get Yarn's exact integrity rejection; original raw counterexamples remain immutable |
| P3 | Small disposable KGP 2.4.20 project + prototype init adapter | Actual root/workspace generation, effective argv/scripts and task order; ordinary/explicit bootstrap split; both primary scopes; warm and direct-store negatives below; no policy action skipped/cached |
| P4 | Read-only check of actual generated project graphs, then separately authorized root adoption | Real JS alias/Git disposition, tooling scope, portable runtime/config-cache decision, all required KGP fixture results reviewed; no unreviewed registry/provenance claim |

The real KGP matrix must include, separately for JS/Wasm where applicable:

1. Cold complete-lock ordinary install and a warm repeated install; record which
   actual actions ran. A warm success must not rely on reinstalling to enforce
   the guards.
2. Stored lock removed with no working lock; removed with stale generated lock
   and existing `node_modules`; lock replaced by malformed/symlinked input.
   Expected: the guard rejects without recreating/modifying the store.
3. Transitive stanza removed with its parent edge retained, both cold and warm;
   workspace-only seed missing; root workspace list changed; declared manifest
   removed; generated manifest changes while root dependencies remain empty.
4. Direct install, restore, store and browser consumer entry points, including
   up-to-date/skip behavior. Capture exact restore/root/guard/install/store
   ordering. Exercise relevant `-x` exclusions and confirm they cannot silently
   bypass the advertised guarded entry points.
5. Direct and indirectly selected upgrade; abbreviated task selection; ordinary
   plus upgrade in one graph; combined JS/Wasm upgrade; bootstrap property mixed
   with a normal consumer. Expected forbidden graphs reject before forced
   installation, not from an upgrade action after installation.
6. Explicit bootstrap creates/updates only the intended task-owned lock, keeps
   scripts suppressed, preserves receipts/diffs, then a distinct ordinary
   invocation succeeds unchanged. Include empty-graph convention and cache-mode
   rejection tests; do not count an unrelated failure as the policy outcome.
7. Relevant conflicting rc/args and valid script positive/suppression controls;
   actual selected tool/argv/config, not only task configuration output.
8. Separate Wasm `:kotlinWasmToolingSetup` fixtures. Its embedded lock and skip
   when `node_modules` exists are not covered by primary-graph guards. The
   [source-only ignoreScripts propagation proof][wasm] is not a tooling install,
   frozen/closure or warm enforcement test.

For every batch retain expected versus observed outcome, command/exit/reason,
task outcomes, actual controlled requests/served bytes, pre/post locks/manifests,
tool/adapter hashes, marker results, resource bounds and original failures.
Stop on unexpected outcomes; do not automatically retry or loosen policy.
No kernel/egress sandbox is established by these controls.

## 6. Adoption boundaries

An isolated prototype can use Python because the existing offline fixture
tooling does. That does **not** establish Python as an ordinary-build dependency
on Android/iOS/Desktop developer hosts. Choose one maintained parser/runtime and
an explicit portable adapter with the build owner before live integration; do
not silently maintain divergent Kotlin/Python parsers or vendor all of Yarn.

The first increment can reject the two actual counterexamples without claiming
that the current JS graph, Wasm tooling, provenance, all warm paths or release
readiness has been verified. Leave those gates visible. No live policy should
be adopted from this design without inspected **real KGP** results.
