# Build, dependency, CI, security and verification audit

## Scope and evidence boundary

Reviewed baseline: **`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`**, 2026-10-24.
Finding locations below and in [`findings/BUILD.json`](findings/BUILD.json) refer to that
immutable commit, not line numbers after identity changes. The review covers **67
build/tooling files**, including every Gradle build/settings/convention file, catalog,
wrapper, Rust manifest/build script, workflow, cleanup script, Renovate config,
MkDocs config and the Xcode build configuration. The complete reviewed-file list,
line counts and SHA-256 values are in
[`baseline-build-source-inventory.json`](../testing/evidence/baseline-build-source-inventory.json).
Runtime/native implementation defects are owned by the corresponding module reports;
this report does not duplicate their lifecycle, filesystem or cookie findings.

**A successful configuration/POM task is not a successful library build.** The Linux
host configured the baseline after a documented JDK-criteria workaround, compiled
the convention plugins and generated metadata successfully. Full Gradle library
tests were initially blocked by the vendor-specific daemon requirement, then cache
misses and a shared-disk safety limit. The available execution evidence and any
later direct-source test results are indexed in [testing](../testing/README.md).
Nothing was published to Maven Central, another package registry, a website or a
GitHub release by these checks. Public artifact metadata was queried over HTTPS.

## Executive assessment

- The apparently new toolchain versions are **real and accessible**. Official
  repositories returned Kotlin 2.4.20, AGP 9.4.0 and Compose Multiplatform 1.12.0 POMs.
  Both the committed Gradle wrapper JAR and the configured distribution digest match
  Gradle's official 9.7.1 digests. Do not misdiagnose them as nonexistent versions.
- The build is not just a collection of independent pure Kotlin libraries. Even
  `calf-io` exports `calf-core`, which uses Compose Foundation; convention plugins
  configure all shared targets, and desktop picker/share resources invoke Cargo.
- **Confirmed packaging defect:** a generated desktop WebView POM contains six
  Linux-specific JavaFX classifiers, because the publication captures the producer
  OS. The artifact coordinates themselves are not OS-specific (BUILD-001).
- Native artifact presence is tested using an arbitrary nonempty directory, not an
  ABI/source/target manifest. The native release matrix is incomplete for ARM
  desktop paths described by the loaders (BUILD-003/004).
- The reviewed security results are deliberately narrow: one **low-severity**
  JavaFX-media advisory match and three **informational unmaintained-crate** RustSec
  notices. No exploit against the library was established. Absence of other direct
  matches is not a clean bill of health for unresolved JVM/npm transitives.
- Tests are concentrated in four modules. There are **86 Kotlin test functions**:
  UI 69, picker 9, IO 6, navigation 2. There are no native Rust unit tests and no
  Android-device or iOS-specific test files in the baseline.
- A cache-only direct Kotlin2.4.20/JUnit run **passed15 original IO/picker tests**
  using unchanged baseline sources, real context expect/actuals and no stubs, with
  exact IO0.9.1/coroutines1.11.0 dependencies. It is genuine JVM test evidence,
  separate from the blocked full Gradle pipeline and supplemental defect probes.
- A separate Kotlin2.4.20 run passed **32 original UI common assertion bodies**
  after removing test registration, with explicit Compose/Material type stubs;
  three additional exact-body checks reproduced known UI defects. Permissions/geo
  probes passed16 deterministic controls/defect characterizations with platform
  adapters. These are source-isolated results, not framework or device tests;
  the central testing ledger preserves the exact transformations and limitations.
- Reviewed remote **Rust compilation passed on Linux, macOS26 and Windows** for
  both crates. All six `cargo test` invocations explicitly ran **zero tests**;
  this does not establish JNI load, dialog or lifecycle correctness.
- Migration verification successfully generated and parsed **42 POMs** (21 modules,
  root KMP plus desktop) with the new group/artifact/version mapping and retained
  the exact generated Cupertino resource package. This proves those identity edits
  configure and generate metadata, not that every platform is release-ready.

## 1. Settings and build graph

`settings.gradle.kts:28-60` includes **29 projects besides the root**: 24 library/
experimental projects and five sample projects. Twenty-one projects apply
`module.publication`; `calf-geo`, `calf-navigation` and `calf-maps` do not. The
`calf-media` and `calf-notifications` directories are **excluded**, not failing parts
of the active graph. They retain obsolete Android plugin aliases, `androidTarget`,
JVM 11 and `iosX64` configuration; simply adding them to `include()` is not supported.
Their scaffold state is documented in the native-feature report, not a second
duplicate build issue.

The included `convention-plugins` build shares `gradle/libs.versions.toml`, resolves
AGP, KGP, Compose and publishing plugins, and compiles JVM-17 convention code. Root
repositories are Google Maven, Maven Central and the Gradle Plugin Portal; ordinary
library dependencies use Google Maven and Maven Central. No runtime library module
requires a Git checkout or Maven repository hosted by the original Calf project.
The baseline catalog's four upstream Calf coordinates are aliases; the samples use
local project dependencies, not those published aliases.

The permissions settings rename each nested project so its *published* artifact
keeps `calf-permissions-*`. Consequently the Gradle task path is, for example,
`:calf-permissions:calf-permissions-camera`, **not**
`:calf-permissions:camera` after settings evaluation. Generated project accessors
likewise use `projects.calfPermissions.calfPermissionsCamera`.

### Every module build and its dependency intent

`C` means the Compose convention, `K` the plain KMP convention and `P` the
publication convention. Both C and K declare all shared platforms; C additionally
applies the Compose/compiler plugins and browser-test-check helper.

| Project | Plugins | Dependencies and important build behavior |
|---|---|---|
| `calf-core` | C/P | Implementation Compose Foundation; small context/dispatcher module still introduces a Compose graph. |
| `calf-ui` | C/P | Core, Foundation, Material3 alpha, coroutines; Android Activity/Android dispatcher; desktop Swing dispatcher; iOS Kyant backdrop/shapes. Only module enabling main executable bundling for browser tests. Kotlin common tests and Compose desktop tests. |
| `calf-webview` | C/P | Foundation, Material3, coroutines; Activity/Android dispatcher; six JavaFX 19 desktop modules and Swing dispatcher; browser bindings; iOS Objective-C `nskeyvalueobserving` cinterop. |
| `calf-cupertino-icons` | C/P | Foundation, Material3, Compose resources. Generated resource package depends on identity unless explicitly pinned; migration pins it and verifies generated `Res.kt`. |
| `calf-io` | K/P | API exports core and kotlinx-io; Android DocumentFile; web browser bindings; Kotlin-test and desktop coroutine test support. |
| `calf-file-picker` | C/P | API exports IO; Foundation; Activity Compose; browser bindings; Kotlin tests; Rust release build feeding desktop resources. |
| `calf-file-picker-coil` | K/P | API exports core and IO; implementation Coil 3. Its public Coil adapter API needs consumer fixtures, not just internal compilation. |
| `calf-camera-picker` | C/P | API exports IO; Foundation; Android Activity Compose; declares Kotlin test dependency but has no tests. |
| `calf-share` | C/P | API exports IO; Foundation; Activity Compose; browser bindings; own Rust release build/resource staging; no tests. |
| `calf-permissions` | C/P | API exports every permission leaf and core; umbrella itself adds no implementation or tests. |
| `calf-permissions:calf-permissions-core` | C/P | API exports Compose Foundation; Activity Compose on Android. |
| All ten permission leaves: camera, gallery, location, background-location, bluetooth, contacts, calendar, notifications, wifi, microphone | C/P | Each API exports permission core. Every leaf build script was read; no leaf declares tests. Platform permission manifests and API behavior are in the permissions review. |
| `calf-geo` | C | Foundation; Android AppCompat, lifecycle-extensions 2.2.0 and Play Services Location. Not published by current conventions. |
| `calf-navigation` | C | Foundation/Material3; Android Navigation 2.9.7; Kotlin and Compose desktop tests. Not published. |
| `calf-maps` | C | Foundation/UI; test dependency but no implementation/test sources. Not published. |
| `sample:common` | C | Local UI, picker, Coil adapter, permissions, WebView, navigation, camera, share and icons; datetime; JetBrains Navigation; Coil/Coil-Ktor and platform Ktor engines. UI exported from static `Common` Apple framework. |
| `sample:android` | Android app/Compose | Common sample, Activity, tooling and AppCompat. AGP built-in Kotlin; compile/target SDK 37, **minSdk 24**, Java/Kotlin target 17. |
| `sample:desktop` | KMP/Compose | JVM app plus common sample, picker/share, platform Compose desktop runtime; DMG/MSI/DEB packaging is host-dependent. |
| `sample:web-js` | KMP/Compose | JS browser executable, output `web.js`, common sample and Foundation/UI. Tracked webpack `fs.js` fragment is empty. |
| `sample:web-wasm` | KMP/Compose | Wasm browser executable, output `web.js`, common sample and Foundation/UI. |
| Excluded `calf-media`, `calf-notifications` | Obsolete direct plugin setup | Not configured, compiled or published. Stale build scripts must not be mistaken for supported targets. |

The complete catalog alias → exact Maven coordinate/version → referencing build
files inventory is in
[`baseline-declared-dependencies.json`](../testing/evidence/baseline-declared-dependencies.json).
This records unused aliases as well as active ones; unused catalog entries are not
automatically runtime dependencies.

## 2. Convention implementation walkthrough

| File / symbol | Actual execution and review observations |
|---|---|
| `kotlin.multiplatform.gradle.kts:1-12` | Applies KGP and `com.android.kotlin.multiplatform.library`; installs hierarchy and non-Android targets; configures Android and JVM compiler targets. No old `com.android.library`/KMP combination remains in active libraries. |
| `Android.kt:23-39`, `androidLibrarySetup` | Computes namespace from group plus normalized project path, gets AGP's target extension named `android`, sets SDK 37/min23/JVM17, enables host tests. Changing Maven group also changes these generated Android namespaces; public Kotlin/JNI packages remain independently retained. |
| `Hirearchy.kt:10-32`, `applyHierarchyTemplate` | Extends the default hierarchy with overlapping `material` (Android/JVM/JS/Wasm), `nonAndroid` (JVM/iOS/JS/Wasm), and `web` (JS/Wasm) groups. This deliberately shares Material actuals while iOS uses UIKit actuals. |
| `Hirearchy.kt:43-45`, `withAndroidLibraryTarget` | Matches `KotlinMultiplatformAndroidLibraryTarget` through `withCompilations`, rather than KGP's old Android target class. This prevents silently losing Material actual implementations after AGP9 migration. Convention compilation succeeded. |
| `Hirearchy.kt:48-58`, source-set helpers | Helpers for desktop/material/nonAndroid and legacy `jsWasmMain`; the latter is not the current `webMain` group and is unused. Do not copy it into new module code without fixing the name. |
| `Targets.kt:11-23`, `applyTargets` | JVM target called `desktop`, browser JS/Wasm, iOS arm64 and simulator arm64. No native macOS, Linux, Windows, watchOS/tvOS or Intel iOS target is declared; desktop OS support comes through JVM plus platform-native dependencies. |
| `Targets.kt:33-38`, `withBrowserTestBundling` | Adds executable binaries for JS/Wasm so Skiko-backed browser test validation can succeed. It also adds browser distributions to library assemble; use deliberately rather than enabling everywhere. |
| `ComposeWebTests.kt:20-35` | Configures Compose validation tasks by target name. It resolves the test compilation's inherited source-set directories, walks for any file and captures that boolean in `onlyIf`. Current hand-written source layout is covered; generated tests created later could be missed. Configuration-time directory walks and non-Kotlin files are maintenance/performance considerations, not reproduced failures here. |
| `Java.kt:9-14`, `setJvmTarget` | Sets all Kotlin JVM compile task targets from catalog Java17. This is bytecode level, not the selected runtime JDK vendor. |
| `compose.multiplatform.gradle.kts:1-7` | KMP convention plus Compose/compiler; installs the browser-check helper for all Compose modules. |
| `module.publication.gradle.kts:5-37` | Enables Central publishing/signing, derives coordinates and license/developer/SCM POM fields. Signing is configured but no key availability or signature was exercised. Baseline points to Calf; migration rewrites identity while retaining author attribution. |
| `GradleSetupPlugin.kt` | Empty `apply()` implementation, unused by active convention setup. No functionality should be inferred from its class name. |
| `convention-plugins/build.gradle.kts:29-30` | The generated version-catalog class is exposed through a `compileOnly(files(...protectionDomain...))` workaround for Gradle issue 15383. It worked in the tested configuration, but is a specific upgrade coupling to preserve/test, not a stable public plugin API. |

## 3. Toolchain compatibility and verified host constraints

| Layer | Baseline declaration | Audit observation |
|---|---|---|
| Gradle | 9.7.1 | Installed under `/opt`; same version used to avoid downloading a duplicate distribution. Wrapper JAR/distribution digests verified against official HTTPS checksum endpoints. Wrapper download/extraction itself was not needed. |
| Daemon | JetBrains JDK17 | Baseline with auto-download disabled failed before configuration despite Ubuntu OpenJDK17/21 being installed. Only this criteria file was renamed in the detached baseline worktree. Migration accepts any JDK17 and configured successfully. |
| Kotlin/compiler | 2.4.20 | Artifact available and several compiler/plugin artifacts pre-cached. Convention build uses Gradle's kotlin-dsl plugin 6.7.3 (its own compiler integration), so convention success alone is not application compilation. |
| AGP / Android | 9.4.0 / compile37 | Official AGP POM accessible; SDK platforms34–37 and build-tools34–36 installed. No emulator/device attached. Installing another full SDK was avoided. |
| Compose | 1.12.0 | Official plugin accessible, but many desktop runtime JARs were not cached; an offline library compile failed on these cache misses, not on unresolved source symbols. |
| Material3 | 1.12.0-alpha03 | Explicit alpha input, not a stable API promise. Align tests/ABI fixtures with this exact version. |
| Android minimums | Library23; sample24 | AndroidX navigation2.9.7 in library vs JetBrains navigation2.10.0-alpha02 in sample intentionally differ. Do not lower sample minSDK or update library navigation without checking Android manifest metadata and consumer minSDK23 builds. |
| Rust | Floating `stable`, edition2021 | Cached Rust1.98.0 works via `~/.cargo/bin`; not initially on PATH. Metadata resolution succeeded. GTK3 development package absent, but rfd0.15.4 defaults to XDG portal + async-std, so absence of GTK3 alone is **not** a proven blocker. |
| Web | KGP-managed Node/Yarn/Karma/webpack | Host Node24.20.0, Chrome and Xvfb available. Managed npm dependencies/browser test bundles were not installed or validated as a complete suite under disk limits. |
| Apple | arm64 targets; Objective-C cinterop | Linux disables simulator execution and WebView Apple cinterop cross-compilation explicitly. It cannot validate Xcode/SDK availability, linking, code signing, device behavior or Swift export. |

The Xcode sample invokes `:sample:common:embedAndSignAppleFrameworkForXcode` from a
shell build phase unless IDE integration sets its documented skip variable. Its
framework search path names `Common`, matching the static framework base name. The
project-level deployment target26.0 is overridden at the app-target level by18.5;
do not report26.0 as the effective sample minimum without respecting Xcode setting
precedence. The sample originally embeds an upstream signing team and bundle ID;
these are migration configuration, not usable credentials. Permission usage strings
and supported deployment API behavior are analyzed in the platform reports.

## 4. Native compilation and artifact delivery

For picker and share, desktop resource processing reaches a `Copy` task, which
depends on `Exec(cargo build --release --target <host>)`; the output is staged below
`build/native-libs/native/<os>-<arch>/`. Target/library names are duplicated across
two Gradle scripts, the file-picker shell script, CI and runtime loaders. Changes
must update every layer, including case/architecture aliases and JNI names.

If *any* prebuilt directory contains a file, those build/copy tasks are not even
registered. This is why adding a stale binary folder to make tests pass would be
misleading; no such fake native artifact was created in this audit. Pure Kotlin
tests may be isolated without invoking native UI, but their evidence must say so.

Release profiles use size optimization, LTO, stripped symbols and one codegen unit.
Those are reasonable size defaults, but remove debugging information and increase
clean release-link work. No size, throughput or native-latency benchmark was run.
Production symbols/provenance should be retained separately where redistribution
policy permits. Native builds do not automatically imply JNI load/dialog tests.

Cargo metadata resolution is substantive dependency evidence, not a compilation:

- Picker: **197 packages including the root**, resolving `jni0.21.1`, `rfd0.15.4`,
  raw-window-handle0.6.2 plus target-specific dependencies.
- Share: **48 packages including the root**. macOS Objective-C/block dependencies
  appear in the all-target graph even though Linux compilation would not exercise
  the macOS share implementation.
- Combined scan: **202 unique non-root name/version pairs**. Audit-generated
  Cargo.lock files were confined to the detached worktree and are not described as
  historical release locks.
- Cargo registry metadata records package licenses/repositories. These are declared
  metadata, not a complete binary attribution compliance assessment. Candidate JARs
  and native binaries still need bundled-license/notice checks against their exact
  resolved graphs.

The separate reviewed GitHub
[native verification run40106895492](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40106895492)
on `cf6547931d8e339d673e7605ff5fd141a5e42091` **did** compile both crates with
`cargo test` on Ubuntu, macOS26 and Windows. All three jobs succeeded; each of the
six commands logged `running 0 tests`. The job JSON and full sanitized text log in
`docs/testing/evidence/github-actions/native-*-40106895492.*` were inspected.
This narrows the limitation to absent behavioral/JNI/GUI coverage and untested
release/cross-architecture binaries, rather than incorrectly saying Rust could
not be compiled anywhere. The controlled workflow performed no package publishing.

## 5. Original CI and publishing execution flows

The workflows in imported history are preserved. **Do not re-enable them unchanged**
on the independent repository. The lead disabled repository Actions before history
push and replaces automatic publication/deployment with non-publishing verification;
see the migration report for exact applied changes.

| Baseline workflow | Trigger and execution | Review conclusion |
|---|---|---|
| `gradle.yml` | main push/PR or reusable call → macOS26 JDK17/Rust → `allTests`; main push also builds native artifacts, downloads both modules' binaries and publishes snapshots. | Test and publication concerns coupled; tests only on one desktop OS; no device consumer gate; read-only contents permission is a positive default. Snapshot credentials/automatic publication must not migrate as an enabled policy. |
| `build-native-libs.yml` | Manual/reusable → macOS14 arm64+x64, Windows x64, Linux x64 → release Cargo builds → combined artifacts. | No baseline Rust test commands; compiler/action tags float; lockfiles ignored; optional version input is direct shell interpolation; target matrix/combined staging defects recorded. |
| `deploy.yml` | Manual version → reusable tests + native build → macOS26 signs/publishes/releases Central → version-stamping branch/PR. | Broad contents/PR write permission, job-level publication secrets, unsafe input interpolation and mixed artifact-action versions. `ls -lhR` is existence logging, not binary/ABI/provenance verification. Version updates occur after external publication, so a successful release can still leave source/catalog drift if the update job fails. No release was invoked. |
| `deploy-web.yml` | GitHub release or manual → Wasm sample distribution → production Netlify deploy. | External side effect with deployment secrets. It is not a routine test and was not executed. Requires independent identity/site/secret/owner authorization before any future use. |
| `mkdocs.yml` | main push → unconstrained Python dependencies → `mkdocs gh-deploy --force`. | Floating build inputs and history-writing deployment. Neither preservation of original pages nor migration verification authorizes rerunning it. Python/docs toolchain should be locked and site builds separated from deployment. |

Baseline signing uses Vanniktech's in-memory signing properties sourced from GitHub
secrets; none were read or printed. An explicit future release must verify namespace
ownership, complete targets, license payloads, package metadata, ABI, key handling,
and actual signatures. A POM `<license>` URL is metadata, not proof the entire binary
distribution fulfills third-party notice obligations.

The migration's local publication interlock is an extra guard, **not owner
authorization**. A guard on `PublishToMavenRepository` alone does not cover all
Vanniktech standalone Central lifecycle tasks; the lead extends it to Central-named
tasks. No publishing task was executed to test the guard because that would violate
the task's safety boundary. Compilation/configuration checks are distinct from
proving every remote task's safety behavior.

## 6. Security methodology and results

### Artifact authenticity / secret hygiene

The wrapper's configured distribution SHA-256 is
`acd53f1edaf02f1a8ff99879f8a34b302661a057d9b063ae9e35b552f804d20a`;
the wrapper JAR SHA-256 is
`7a9ce74cff467ca1bf60a4fcd9f05185acceda4d0f382434d393e17864262c5d`.
Both match the official9.7.1 endpoints captured in
[`registry-version-checks.json`](../testing/evidence/registry-version-checks.json).
The shell/batch wrappers use the standard launcher pattern, validate JAVA_HOME and
pass arguments through their generated quoting logic. Shell syntax checks do not
prove every Windows path/quoting scenario.

A deliberately narrow marker scan inspected **548 tracked text-like files <=10MB**
for private-key headers, GitHub tokens, AWS access identifiers and OpenAI-key
patterns. It found no matches and emitted no secret values. This is **not** an
all-history, entropy-based or authenticated secret scan. Historical Git objects and
every archived attachment need a separate disclosure-safe process if a full secret
audit is required. The lead also ran a narrow marker scan across the preserved
advertised-ref history:2,638 text blobs,63 binary blobs skipped, zero marker matches
(`advertised-history-secret-marker-scan.json`). That expands Git coverage but is
still not an entropy-based or attachment/binary secret audit. Public metadata
content is untrusted data, not agent instructions.

### Advisory queries

| Input | Result | Correct interpretation |
|---|---|---|
| 45 unique exact direct Maven dependencies/versions (39 catalog external aliases + six JavaFX modules) | One match: `javafx-media:19`, GHSA-47g3-mf24-6559 / CVE-2024-20925. | Confirmed declared dependency match; LOW CVSS3.1. Exploit preconditions are narrower than ordinary WebView use; exploitability unverified. |
| 202 exact resolved Rust dependency name/version pairs across both all-target graphs | RUSTSEC-2026-0370, -0371, -0372. | **Informational unmaintained** crates, not discovered memory-safety exploits or CVEs. |
| JVM transitives, managed npm graph, Python docs graph, native system libraries | No complete resolved-graph scan. | Not assessed fully; do not infer safe from the direct queries. |

Full public advisory responses, exact query inputs and result timestamps are in
`docs/testing/evidence/osv-*.json` and `advisory-*.json`. Registry availability
checks validate public artifact existence, not compatibility of every transitive
version or the authenticity of the entire dependency supply chain.

Runtime concerns such as WebView URL/cookie policies, native cache replacement,
filesystem overwrite, JNI panics, Objective-C object ownership and UI thread
dispatch require the module findings; they cannot be replaced with a dependency
scanner. See the native-features, IO/picker, UI and permissions reports.

## 7. Performance and maintenance considerations

The reproducible BUILD findings take priority over generic cleanup:

1. Fix producer-host metadata and prebuilt manifests before optimizing packaging.
2. Fix native task inputs/outputs and pin toolchains/locks together; a fast stale
   native binary is worse than a redundant Cargo invocation.
3. Cold convention/plugin instrumentation is substantial: the first Gradle9.7.1
   configuration created roughly1GiB of new version-specific cache data on this
   shared host. This measurement includes Gradle instrumentation/generated API
   caches, **not** the library's runtime memory footprint. Do not translate it into
   an application performance finding.
4. Configuration touches all included projects, even a focused IO test. Catalog
   aliases, overlapping source-set hierarchies and JS executables should be kept
   explicit; casually adding targets or bundling every library multiplies work.
5. Build scripts use internal/generated Gradle APIs (`OperatingSystem`,
   `LibrariesForLibs` workaround). Preserve regression checks when upgrading Gradle.
6. Many modules use `implementation` for Compose/Coil types visible in public APIs.
   Consumer compile-classpath fixtures are needed before changing all dependencies
   blindly to `api`; module reports identify concrete affected signatures.
7. `cleanup.sh` is working-directory-relative and deletes IDE/build/old `iosApp`
   outputs. It was **not run**. Do not use it to reclaim unrelated project caches or
   as a generic migration cleanup command.

## 8. Findings, migration disposition and next gates

| ID | Priority | Evidence/status | Action |
|---|---|---|---|
| BUILD-001 | High | Confirmed generated POM | Correct OS-aware JavaFX publication; cross-host consumer fixtures. |
| BUILD-002 | Low | Exact advisory match; exploitability unverified | Maintained JavaFX line and complete graph re-scan. |
| BUILD-003 | High | Confirmed source predicate | Native module/target/revision/ABI manifests. |
| BUILD-004 | Medium | Confirmed matrix mismatch | Add or explicitly limit ARM desktop support. |
| BUILD-005 | Medium | Reproducibility risk | Commit Rust locks, pin toolchain, locked builds. |
| BUILD-006 | High | Improvement; measured test gap | Layered platform and consumer/API compatibility gates. |
| BUILD-007 | Medium | Supply-chain risk | Verified/locked dependencies and immutable workflow inputs. |
| BUILD-008 | Medium | Trusted-input boundary risk | Unsafe original release paths removed/disabled; validate replacements before enablement. |
| BUILD-009 | Medium | Confirmed baseline bootstrap failure | Vendor restriction removed during migration; migrated configuration passed. |
| BUILD-010 | Low | Confirmed task declaration | Correct native incremental inputs/outputs. |
| BUILD-011 | Low | Confirmed staging duplication | Separate/validate per-module native artifacts in future pipeline. |
| BUILD-012 | Low | Informational maintenance risk | Track compatible rfd/portal stack modernization. |

Before a first authorized release: acquire sufficient build storage, rerun the
entire pinned target/test matrix, validate minimum SDK/runtime consumers, fix native
artifact provenance/coverage and host-captured JavaFX metadata, inspect API/ABI
compatibility and license payloads, then perform a separately authorized signing and
publication dry-run against a non-production fixture. No audit finding or green
configuration log substitutes for these gates.
