# Verification and testing knowledge base

## Read this before interpreting results

Baseline: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6` (upstream main at migration).
Audit source probes, repository checks, metadata generation, compilation, unit
tests, platform integration and publication are **different evidence levels**.
Never add their counts together as a single number of passing library tests.

- A defect-confirmation assertion marked `PASS` means the reported defective
  behavior was reproduced, not that the library is correct.
- `NO-SOURCE` and `SKIPPED` are not executed tests.
- A `cargo test` run with `running 0 tests` proves compilation/test-harness startup,
  not native dialog, JNI, ownership or lifecycle correctness.
- A generated POM proves configuration and metadata, not a published or working
  binary.
- Logs belong to the exact revision/worktree named in them. Migration changed
  identity/build safety, not the implementation defects under audit.

The build investigation is in [build-security.md](../audit/build-security.md).
Each finding's `required_tests` field is the regression-test specification.

Current development evidence is additive: see the
[2026-10-26 immutable hosted run ledger](../development/evidence/github-actions/README.md)
and [contained follow-up](../development/checkpoint-ci-20261026.md). Core and macOS
passes do not erase the failed iPhone/Windows jobs, missing WebView execution,
Android-device gaps, or unexecuted artifact consumers. The original baseline
inventory/ledger below deliberately retains its historical scope.

## 1. Existing baseline test inventory

The executable-source inventory is generated in
[`evidence/baseline-test-inventory.json`](evidence/baseline-test-inventory.json).
Counts below are `@Test` functions, not parameterized cases, coverage percentages
or a claim that Gradle executed them in this environment.

| Module / source set | Test class | Tests | Scope |
|---|---|---:|---|
| IO desktop | `KmpFileSourceTest` | 6 | Full/chunked/context-free file source, missing/empty file, close behavior. |
| Picker desktop | `NativeLibCacheTest` | 6 | Cache hash/name, exact writes, reuse, replacement and fallback. No JNI load/dialog. |
| Picker desktop | `MimeTypesTest` | 3 | MIME mappings/parser behavior. |
| Navigation desktop | `AdaptiveNavHostStateTest` | 2 | Saveable state after navigating away/back and after popping. |
| UI common | `DateBoundsSelectableDatesTest` | 6 | Selectable date bounds adapter. |
| UI common | `DateBoundsTest` | 16 | Date bounds normalization/query behavior. |
| UI common | `DateRangeSelectionTest` | 6 | Range selection rules. |
| UI common | `AdaptiveAlertDialogActionsTest` | 4 | Dialog action policy. |
| UI desktop | `AdaptiveCompactDatePickerMaterialTest` | 7 | Compact Material picker state/UI. |
| UI desktop | `AdaptiveDatePickerStateMaterialTest` | 11 | Material date picker state/UI. |
| UI desktop | `AdaptiveDateRangePickerStateTest` | 9 | Material date range state/UI. |
| UI desktop | `AdaptiveAlertDialogMaterialTest` | 4 | Material alert dialog UI. |
| UI desktop | `AdaptiveClickableMaterialTest` | 6 | Material click/long-click behavior. |
| **Total** | 13 test classes + 2 helper files | **86** | **32 common + 54 desktop-only functions.** |

The remaining active modules, samples, excluded scaffolds and Rust crates have no
test-function coverage in the baseline. There are no Android instrumentation,
iOS-specific, JNI integration, native UI, WebView engine, permission-device,
performance benchmark or binary-compatibility test suites. Common tests may run on
several targets but do not thereby exercise every native actual's behavior.

## 2. Execution ledger (local unless labeled remote)

The audit used a detached baseline worktree outside the migration worktree. Its
only tracked-file deviation was temporarily renaming the generated daemon JVM
criteria file, **after recording the unmodified failure**. The installed Gradle
distribution was the exact declared9.7.1; using `/opt` avoided another distribution
download. No dependency versions were downgraded to make the Gradle build pass.

| Check | Actual outcome | Evidence |
|---|---|---|
| Original baseline focused desktop suite, offline, provisioning disabled | **Failed before configuration**: requires JetBrains JDK17, while installed JDK17/21 were Ubuntu OpenJDK. | [`baseline-desktop-offline.log`](evidence/baseline-desktop-offline.log) |
| Same tasks, only daemon criteria disabled in detached worktree, offline | **Failed before project compilation**: kotlin-dsl6.7.3 plugin not cached. Artifact was subsequently verified to exist online. | [`baseline-desktop-daemon-override.log`](evidence/baseline-desktop-daemon-override.log) |
| Online `:calf-io:desktopTest :calf-file-picker:desktopTest :calf-ui:desktopTest :calf-navigation:desktopTest`, capped heap/workers, Xvfb | Convention plugins compiled and projects configured. **Terminated at disk reserve**, exit143, before any library tests; no test XML files generated. | [`baseline-desktop-online.log`](evidence/baseline-desktop-online.log), [`disk-safety-stop.json`](evidence/disk-safety-stop.json) |
| Focused IO desktop test, offline after configuration caches existed | Reached `:calf-core:compileKotlinDesktop`; **failed on17 uncached Compose/Skiko JARs**, not a source diagnostic. | [`baseline-io-desktop-offline-focused.log`](evidence/baseline-io-desktop-offline-focused.log) |
| Retry focused IO online | **Not started**: free disk below1GiB reserve (guard exit75). | [`baseline-io-desktop-online-focused.log.result.json`](evidence/baseline-io-desktop-online-focused.log.result.json) |
| Migrated four-module desktop suite after disk recovered, first attempt | Wrapper9.7.1 downloaded and Gradle progressed into real compilation; **failed starting Cargo**, which was installed but absent from PATH. No desktop test task executed in this attempt. | [`migrated-desktop-cargo-path-failure.log`](evidence/migrated-desktop-cargo-path-failure.log), adjacent result JSON |
| Migrated suite with explicit Cargo PATH and `--continue` | **77 real Gradle tests passed**: IO6, UI69, navigation2;11 XML reports, no failed/skipped cases. Whole command still **failed** at picker native compilation because `wayland-client.pc` was absent. No dependency replacements or framework stubs. | [`migrated-desktop-wayland-failure.log`](evidence/migrated-desktop-wayland-failure.log), [`77-case summary`](evidence/migrated-desktop-before-wayland-summary.json), [`preserved XML manifest`](evidence/local-gradle/attempt2-wayland-missing/manifest.json) |
| Migrated suite after Wayland install, `--rerun-tasks` | **Failed on HTTPS/TLS metadata fetches**, not Kotlin source diagnostics: lifecycle2.9.4 and Material3alpha03 POM retrieval terminated during the handshake. Picker Cargo build completed after its retries; no desktop test task ran. Earlier77-case XML is not evidence of fresh execution here. | [`migrated-desktop-tls-failure.log`](evidence/migrated-desktop-tls-failure.log), adjacent result JSON |
| Migrated four-module desktop suite, fourth attempt, `--rerun-tasks` | **Passed86 original tests**: IO6, picker9, UI69, navigation2;13 XML reports,0 failures/errors/skips. All four `desktopTest` tasks executed,55/55 actionable tasks executed, command exit0 in311.07s. Real Gradle9.7.1/project dependencies, no framework stubs or version downgrades. | [`migrated-real-desktop-tests.log`](evidence/migrated-real-desktop-tests.log), [`86-case summary`](evidence/migrated-real-desktop-summary.json), [`verified XML/hash manifest`](evidence/local-gradle/attempt4-complete-desktop/manifest.json) |
| Original IO/picker JUnit tests through direct cached compiler | **Passed15 original tests** (IO6, cache6, MIME3), unchanged baseline source, real context expect/actual and **no stubs**, Kotlin2.4.20/IO0.9.1/coroutines1.11.0/JUnit4.13.2. Does not test Gradle/Compose/native UI. | [`io-original-desktop-tests.log`](evidence/io-original-desktop-tests.log), [`io_original_tests.py`](../../scripts/audit/io_original_tests.py) |
| Original UI common assertion bodies through direct cached compiler | **Passed32 existing assertion bodies**, plus3 expected-defect characterizations, under Kotlin2.4.20. Exact common algorithm/model source and unchanged assertions; `@Test` registration removed, Compose/Material/platform types explicitly stubbed. Not a real framework or native UI test run. | [`ui-source-probes.txt`](evidence/ui-source-probes.txt), [`ui-source-probes.py`](ui-source-probes.py) |
| Permissions/geo source-isolated probes | **Passed16 deterministic checks** (11 permission/helper,5 coordinate controls), with explicit Android/CoreLocation/Compose adapters. A separate5,000,000-trial seeded antipodal search found no NaN witness; trials are not test-case counts or numerical proof. | [`permissions-geo-baseline.txt`](evidence/permissions-geo-baseline.txt), [`permissions_geo.py`](reproductions/permissions_geo.py) |
| Baseline `:calf-ui:tasks --all` and WebView desktop POM generation | **Passed**,42s; confirmed exact test/compile task names and host-specific JavaFX POM classifier defect. No publication. | [`baseline-task-inventory-and-webview-pom.log`](evidence/baseline-task-inventory-and-webview-pom.log), [`baseline-webview-desktop-linux.pom`](evidence/baseline-webview-desktop-linux.pom) |
| Migrated root/desktop POM generation plus icons resource generation | **Passed**,87s;42 POMs validated and exact resource package retained. Initial publication guard/convention scripts compiled. Later guard extensions need the final revision's configuration/CI evidence, not this earlier log. | [`migrated-poms-and-resource-package.log`](evidence/migrated-poms-and-resource-package.log), [`migrated-coordinate-and-res-checks.json`](evidence/migrated-coordinate-and-res-checks.json) |
| Cargo offline metadata, picker/share | Cache-miss failures; not Rust compiler failures. | `evidence/calf-*-cargo-dependencies.json` |
| Cargo online metadata, picker/share | **Passed resolution**:197/48 packages including roots,202 distinct non-root name/version pairs combined. No native compilation or tests implied. | `evidence/calf-*-cargo-dependencies-online.json` |
| Remote native matrix, both crates on Linux/macOS26/Windows | **Passed all three jobs / six `cargo test` invocations; each explicitly ran0tests.** Confirms host Rust compilation/test-harness startup, not native GUI/JNI behavior. Commit `cf6547931d8e339d673e7605ff5fd141a5e42091`. | [Run40106895492](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40106895492), `evidence/github-actions/native-{run,jobs,log}-40106895492.*` |
| First remote Gradle matrix, commit `3d2b772b27bed3da0f34677225b843d29f1c3ba6` | **Overall failed**: both hosts used an invalid SDK package identifier; desktop/Android/Apple steps skipped. Linux's independent browser step **passed32 JS +32 Wasm common tests**, then JS sample distribution completed with warnings; Wasm production compilation exhausted its2GiB heap. macOS ran0 tests. Archive/audit validation job passed. | [Run40110188721](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40110188721), [inspected results below](#inspected-remote-results) |
| Corrected remote Linux job, commit `1160893ca17404891b312990bc829535cddb75a2` | **Succeeded**:182 fresh test executions across25 XML reports (86 desktop,32 Android host,32 JS,32 Wasm), no failures/errors/skips. Android sample debug assembly and both browser distribution tasks succeeded; JS production compile/webpack came from cache, while Wasm production compilation/optimization/webpack executed freshly at4GiB. macOS is a separate job. | [Run40114966617](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40114966617), [`Linux terminal log`](evidence/github-actions/gradle-linux-log-40114966617.txt), [`independent XML summary`](evidence/github-actions/gradle-junit-linux-40114966617.json) |
| Corrected remote macOS job, same commit/run | **Succeeded**:118 fresh executions across17 XML reports (86 desktop,32 common iOS-simulator tests), no failures/errors/skips;713/713 actionable tasks executed. WebView Objective-C cinterop and the static sample simulator framework link succeeded. Overall corrected run's three jobs succeeded:42 XML reports/300 target executions of86 original functions, not300 distinct tests. | [`macOS terminal log`](evidence/github-actions/gradle-macos-log-40114966617.txt), [`independent XML summary`](evidence/github-actions/gradle-junit-macos-40114966617.json), [`complete run summary`](evidence/github-actions/gradle-verification-summary-40114966617.json) |
| Official wrapper/declared toolchain checks | **Passed** wrapper JAR/distribution digests; Kotlin2.4.20/AGP9.4.0/CMP1.12.0/kotlin-dsl6.7.3 artifacts accessible. | [`registry-version-checks.json`](evidence/registry-version-checks.json) |
| Exact direct Maven advisory scan |45 queries, one low-severity JavaFX media advisory match; exploitability unverified. | [`osv-direct-maven-query.json`](evidence/osv-direct-maven-query.json) |
| Selected-host desktop runtime dependency graph and advisory scan | **25 `desktopRuntimeClasspath` graphs resolved**,193 unique Maven coordinates,8,613 edges,0 unresolved nodes. All193 OSV queries completed; only the same low-severity JavaFX media advisory matched. The separately named `sample:desktop:jvmRuntimeClasspath` was not selected. This is metadata/advisory evidence, not a binary/SBOM or runtime test. | [`desktop-runtime-graph.log`](evidence/desktop-runtime-graph.log), [`graph`](evidence/desktop-runtime-graph.json), [`OSV query/results`](evidence/desktop-runtime-security/osv-desktop-runtime-query.json) |
| Exact Rust resolved graph advisory scan |202 queries, three informational unmaintained warnings; no confirmed exploit. | [`osv-resolved-rust-query.json`](evidence/osv-resolved-rust-query.json) |
| Narrow baseline secret-marker scan |548 text-like files, no matches. Not an entropy/full-history audit. | [`baseline-secret-marker-scan.json`](evidence/baseline-secret-marker-scan.json) |
| Lead's advertised-history secret-marker scan |2,638 unique text blobs, no marker matches;63 binary blobs skipped. Preserved refs only, not inaccessible/server-deleted history. | [`advertised-history-secret-marker-scan.json`](evidence/advertised-history-secret-marker-scan.json) |
| Expanded advertised + recovered-history marker scan |3,532 text blobs,0 marker matches;166 binary blobs skipped. Includes supplemental recovered commit refs; still not entropy/binary/attachment analysis or inaccessible-history coverage. | [`complete-recovered-history-secret-marker-scan.json`](evidence/complete-recovered-history-secret-marker-scan.json) |
| Audit resource guard and static syntax controls | Passed success/timeout/disk-preflight/publication-command rejection controls; baseline shell syntax, three TOML manifests and audit Python AST checks. Not library tests. | [`build-tooling-self-checks.json`](evidence/build-tooling-self-checks.json) |
| CI JUnit summarizer fixtures | Passed8 tooling tests: counts, aggregate exclusion, empty/malformed input, redacted output, deterministic ordering, UTF8/UTF16 DTD rejection, archived/cache report isolation and explicit artifact-root inspection. Not library tests. | [`junit-summarizer-self-tests.log`](evidence/junit-summarizer-self-tests.log), [`test_summarize_junit.py`](../../scripts/audit/test_summarize_junit.py) |
| Runtime OSV helper fixtures | Passed7 offline tooling fixtures for exact coordinate extraction/deduplication, invalid or empty inputs, batch alignment, malformed responses and rejecting unresolved pagination. No network/Gradle calls in fixtures. | [`runtime-osv-helper-tests.log`](evidence/runtime-osv-helper-tests.log), [`test_scan_runtime_osv.py`](../../scripts/audit/test_scan_runtime_osv.py) |
| Final complete audit/migration tooling suites | **Passed35 audit and55 migration fixtures**, no skips, both command exits0. Includes overlapping individually listed helper fixtures; not Kotlin library tests. | [`final-audit-tooling-tests.log`](evidence/final-audit-tooling-tests.log), [`final-migration-tooling-tests-v3.log`](evidence/final-migration-tooling-tests-v3.log), adjacent result JSON |

**The initial baseline Gradle attempts executed zero tests; the fourth migrated
desktop attempt passed all86 existing test functions through real Gradle.** Earlier
77-case and direct-compiler results overlap that inventory, as do the32 common
tests later executed on each of JS and Wasm in remote CI. Do not sum these as
distinct original test functions. The browser executions add real target coverage,
not new test logic. Direct-source defect probes below remain separate.
The first remote matrix failed on SDK setup and Wasm production heap limits.
The corrected Linux job then passed182 executions across desktop, Android host,
JS and Wasm, built the Android debug sample and completed both browser distributions.
The corrected macOS job additionally passed86 desktop and32 common simulator
executions and linked the static sample framework. Across both hosts, **300 target
executions cover86 distinct original functions**, with no failures/errors/skips.
Their sums with earlier runs are not additional unique tests. Physical-device,
native UI/JNI integration and full Windows JVM verification remain absent;
Android host tests/debug packaging and simulator common tests/framework linking
must not be promoted into those unperformed checks.

## 3. Source-isolated and browser evidence

These small probes were used to confirm concrete behavior without replacing the
project dependency graph or pretending to run native platforms.

| Area | Reproduction/evidence | Interpretation |
|---|---|---|
| Original IO/picker test suite | [`scripts/audit/io_original_tests.py`](../../scripts/audit/io_original_tests.py), [`io-original-desktop-tests.log`](evidence/io-original-desktop-tests.log) |15 unmodified original tests with real baseline common/JVM sources and resources, no doubles; exact pinned Kotlin/IO/coroutine versions. Selected JVM sources only, not complete module/Compose/native integration. |
| IO/picker | [`scripts/audit/io_jvm_probes.py`](../../scripts/audit/io_jvm_probes.py), area test report | Exact dependency-light production bodies with dialog/platform doubles;10 checks include cache controls and confirmed self-save/overwrite/MIME defects. See script/report for its actual compiler/coroutine version, not assumed project versions. |
| Navigation/core/icons | [`navigation-core-icons/run_jvm_repros.py`](evidence/navigation-core-icons/run_jvm_repros.py), [`jvm-repro-result.txt`](evidence/navigation-core-icons/jvm-repro-result.txt), [`catalogue-result.json`](evidence/navigation-core-icons/catalogue-result.json) | Exact bundle/argument/type source under cached Kotlin2.4.20,10 defect/control assertions; font glyph and symbol-catalog checks are static asset validations. Not the two Compose UI navigation tests. |
| Native features/WebView/share | [`native-features-probes/run.py`](native-features-probes/run.py), [`results-baseline.json`](native-features-probes/results-baseline.json) | Five exact-body Kotlin probes with FX/Compose doubles; mocked Node clipboard promise behavior; six real Chrome DOM/cookie semantic observations. No Kotlin/Compose web bundle or native dialog was launched. |
| Permissions/geo | [`permissions_geo.py`](reproductions/permissions_geo.py), [`permissions-geo-baseline.txt`](evidence/permissions-geo-baseline.txt), [area report](permissions-and-geo.md) |16 deterministic checks with exact baseline classes/helpers, Kotlin2.4.20 and explicit Build/CoreLocation/Stable adapters. Confirms registry alias selection and permission request/delegate branches;5 coordinate controls passed. The5,000,000 seeded antipodal trials found no NaN witness. No native callback ordering or device API execution is proved. |
| UI | [`ui-source-probes.py`](ui-source-probes.py), [`ui-source-probes.txt`](evidence/ui-source-probes.txt) |32 original common assertion bodies passed with only test registration removed and documented framework type stubs. Three exact-body expected-defect probes reproduced invalid-minute acceptance (UI-009), the iOS-version comparator (UI-024) and negative slider semantic snapping (UI-033). No Compose runtime, Material implementation, UIKit, graphics or pointer interaction was loaded. |

The individual scripts record compiler/runtime choices and limits. Standalone
probes that use older cached Kotlin/coroutine versions must say so. They may confirm
language-level logic without establishing compatibility of the pinned full build.

## 4. Reproducible local setup

Use the migrated checkout for normal work; the detached baseline is audit-local,
not required to maintain the repository.

1. Install **JDK17** and use the committed Gradle9.7.1 wrapper. The migration removes
   the unnecessary JetBrains-only daemon restriction.
2. Install Android SDK platform37 using its official package identifier
   **`platforms;android-37.0`**, plus the build tools required by AGP9.4.0. The
   literal `platforms;android-37` is not advertised in the inspected repository;
   AGP's SDK32.4.0 target normalization maps `android-37` to canonical37.0 without
   changing `compileSdk=37`. See the [registry check](evidence/github-actions/android-sdk-registry-check-40110188721.json)
   and [identifier probe](evidence/github-actions/sdk-identifier-probe-40110188721.json).
   Set SDK discovery through documented SDK environment/local.properties; never
   commit `local.properties` or licenses/credentials from the machine.
3. Install Rust and ensure `cargo`/`rustc` are on PATH. Future release workflows must
   use a pinned toolchain and committed locks; the baseline manifests are not locked.
4. Linux browser/desktop tests need Chrome and may need Xvfb/system UI libraries.
   Picker compilation requires `wayland-client.pc` (provided by `libwayland-dev`);
   the CI `libgtk-3-dev` installation brings it transitively on the reviewed Ubuntu
   runner. A working Cargo PATH is also required by Gradle's native resource tasks.
   rfd's default Linux backend is XDG portal; actual dialog tests require an
   appropriate desktop/session bus, not merely a successful compiler invocation.
5. Apple work needs a supported macOS/Xcode/SDK/simulator combination. Windows JNI
   builds need the MSVC toolchain. A Linux cross-target declaration is insufficient.
6. Provision ample free storage. This host started with only~2.7GiB free, already had
   large unrelated dependency caches, and was shared with other builds. Fresh full
   KMP/native/browser environments require substantially more. Preserve at least
   the owner-coordinated reserve, do not delete other projects or shared caches.

Safe bounded runner (does not delete anything, refuses obvious publish/scan tasks):

```sh
python3 scripts/audit/run_bounded_build.py \
  --cwd . --log /tmp/nativecmpkit-desktop-check.log \
  --timeout 900 --reserve-mib 1024 -- \
  ./gradlew --no-daemon --max-workers=2 \
  '-Dorg.gradle.jvmargs=-Xmx1536m -Dfile.encoding=UTF-8' \
  -Pkotlin.compiler.execution.strategy=in-process \
  :calf-io:desktopTest
```

The runner is a resource guard, not a security sandbox. Never put secrets in its
command arguments. It creates a dedicated process group and terminates only that
group if its timeout/disk reserve is reached. It writes command/result metadata next
to the log, including whether the process was started at all.

## 5. Test and compile commands by platform

These are procedures, **not additional executed results**. Publication tasks are
intentionally absent. Current exact task names were verified from Gradle's model.

### Desktop / Android host

```sh
# Desktop targets, real project dependency versions; Linux may need xvfb-run -a.
./gradlew desktopTest --no-configuration-cache

# AGP9 KMP host unit tests (not Android device tests).
./gradlew testAndroidHostTest --no-configuration-cache

# Focused existing test-bearing modules.
./gradlew :calf-io:desktopTest :calf-file-picker:desktopTest \
  :calf-ui:desktopTest :calf-navigation:desktopTest

# Android library compilation and sample application packaging.
./gradlew compileAndroidMain :sample:android:assembleDebug
```

Host tests do not verify Android runtime permissions, ContentResolver lifetimes,
activity recreation, camera intents, real WebView, API-level behavior or application
manifest merging on devices. Add device fixtures rather than reclassifying host
tests as instrumentation. Library minSdk23 and sample minSdk24 need separate
consumer fixtures, especially for navigation and transitively raised API floors.

### JS / Wasm

```sh
./gradlew compileKotlinJs compileKotlinWasmJs
./gradlew :calf-ui:jsBrowserTest :calf-ui:wasmJsBrowserTest
./gradlew :sample:web-js:jsBrowserDistribution \
  :sample:web-wasm:wasmJsBrowserDistribution
```

Browser tests use Karma and webpack; they need the managed JS dependency install
and a usable headless browser. Kotlin's generated lock storage should be tracked
and frozen before these become reproducible release gates. Test trusted-gesture
file/clipboard/share APIs, cancellation, unsupported APIs and iframe origin policy
separately from plain arithmetic/common tests.

The first remote run executed32 common tests on each browser target, but the
sample's Wasm **production** compiler ran out of heap with in-process Kotlin and
`-Xmx2048m`. A passing development/test bundle does not prove production optimization
fits the same budget. Run production distributions separately with a measured heap
budget and bounded workers. The JS sample distribution completed in that run,
with missing Node `os`/`path` module and bundle-size warnings; no sample
browser interaction or startup/performance timing was measured.
The corrected Linux run succeeded with4GiB and one worker: Wasm production
compilation, Binaryen optimization and webpack all executed. JS production compile
and webpack were restored from the earlier successful cache; its distribution
task completed. This resolves the observed verification heap failure without
claiming an optimized runtime or changing library dependencies.

### Apple

```sh
# Run on a compatible macOS host, not Linux.
./gradlew :calf-ui:iosSimulatorArm64Test
./gradlew :sample:common:linkDebugFrameworkIosSimulatorArm64
./gradlew allTests --no-configuration-cache
```

The framework-link command compiles the sample dependency surface including the
WebView Objective-C cinterop; a common test run alone can miss it. Device UI tests
must cover delegates, cancellation/disposal, presentation/dismissal, retained
closures/objects, observer removal, keyboard/safe areas and permissions on the
oldest supported and current iOS versions. The sample target's18.5 minimum does not
prove the library's older API paths are safe. Intel simulator support is not declared.

### Rust / JNI

```sh
(cd calf-file-picker/native && cargo test)
(cd calf-share/native && cargo test)
```

Run on Linux, macOS and Windows. Add `--locked` only after reviewed lockfiles are
committed; otherwise failure is expected. `cargo check`/`cargo test` on Linux does
not compile macOS-only `cfg` blocks. Create separate JNI load, filter/selection,
owner-window, concurrent request, cancellation, malformed-string and repeated
load/unload smoke tests. Preserve ABI/symbol/resource manifests for all supported
OS/architecture combinations, including any intended Linux/Windows ARM support.

### Metadata and distribution checks without publication

```sh
./gradlew generatePomFileForKotlinMultiplatformPublication \
  generatePomFileForDesktopPublication \
  :calf-cupertino-icons:generateComposeResClass
python3 scripts/migration/verify_migration.py
python3 scripts/audit/validate_audit.py
```

Inspect group/artifact/version/internal dependency mappings, POM licenses/SCM,
target variants and explicit JavaFX classifiers. Preserve old public Kotlin/JNI
names and generated resource names as declared by migration decisions. Candidate
JAR/AAR/KLIB contents, signatures and license payloads require separate checks.
Neither these commands nor a local publication interlock authorize a release.

## 6. Coverage expansion order

1. Turn **confirmed High** data-loss, lifecycle, loop, permission and cross-platform
   metadata defects into focused failing regressions before fixing them.
2. Native artifact manifest and JNI load tests must precede a release-candidate
   distribution; CI must reject incomplete/wrong-module resources.
3. Add public consumer compile/ABI fixtures for every shipped module and supported
   Kotlin/Compose/SDK combination, including independently resolved coordinates.
4. Add cross-host desktop plus real JS/Wasm/browser checks, then Android/iOS device
   lifecycle/permission tests with deterministic doubles where possible.
5. Add adversarial path/URI/Unicode/locale/date/DST/large-input cases and stress tests
   for cancellation/reentrancy/threading. Tests must exercise the actual platform
   implementation, not only a shared interface.
6. Benchmark cold/warm initialization, native resource extraction, file streaming,
   allocations and high-frequency UI changes. Record hardware/versions and compare
   baselines; source speculation is not a measured performance regression.

No global line/branch coverage percentage is available. Do not invent one from
source inventory or test counts.

## 7. Remote verification handoff

The lead may run the **reviewed, read-only** GitHub workflows on the independent
public repository to overcome local platform/storage limitations. This is not
permission to run archived upstream publication/deployment workflows. The
2026-10-26 [owner policy](../development/containment.md) permits Actions enabled
with all actions/reusable workflows allowed and no mandatory SHA pinning. No
routine verification approval or subagents; minimum permissions and all release
gates remain. Historical disabled-Action observations below remain dated facts.
Record:

| Required field | Reason |
|---|---|
| Workflow run URL, run/attempt ID, exact commit SHA | Associates evidence with the actual reviewed source and workflow. |
| Runner OS/architecture, JDK/Rust/Xcode/SDK versions | Prevents treating one host as all target coverage. |
| Job and individual task/test outcomes | A failed earlier setup step is not a compiler failure; skipped steps prove nothing. |
| Parsed JUnit/native test counts or explicit zero-tests output | Distinguishes compilation from behavioral verification. |
| Sanitized logs/artifacts and restrictions | Never archive secrets; a GitHub green badge alone is insufficient. |

`python3 scripts/audit/summarize_junit.py --root . --output build/audit-junit-summary.json`
provides a log-only, stdlib XML summary for an `always()` CI step. It excludes
`allTests` aggregate directories, top-level `docs`/`site` archives and any
`.git`/`.gradle`/`node_modules` components relative to the supplied root. For
intentional historical inspection, set `--root` to the downloaded artifact tree
itself. This prevents committed historical XML from inflating a fresh CI count.
The helper does not copy failure/stdout contents, rejects DTD/entity declarations
and reports missing/malformed reports explicitly. A test
report restored from Gradle's cache is still not proof of uncached execution;
retain the task log alongside the summary. Uploading selected test XML/POM metadata
for audit evidence is not publication of library packages.

### Inspected remote results

[Native run40106895492, attempt1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40106895492)
completed successfully on commit
`cf6547931d8e339d673e7605ff5fd141a5e42091`. The archived jobs and text log were
inspected: Windows, macOS26 and Ubuntu jobs all succeeded, both crates' `cargo test`
commands ran on each host, and **all six reported `running 0 tests`**. Rust1.98.0
was selected by the reviewed workflow. This is real cross-host Rust compilation
evidence, not a native integration suite or a new package release.

Archived evidence: [`native-run-40106895492.json`](evidence/github-actions/native-run-40106895492.json),
[`native-jobs-40106895492.json`](evidence/github-actions/native-jobs-40106895492.json),
[`native-log-40106895492.txt`](evidence/github-actions/native-log-40106895492.txt).
The lead disabled Actions again after that controlled run. Full remote Gradle,
Android and Apple results must be interpreted separately from native compilation.

[Gradle run40110188721, attempt1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40110188721)
completed **failure** on commit `3d2b772b27bed3da0f34677225b843d29f1c3ba6`,
2026-10-24 16:08:43–16:47:04 UTC. Job metadata, all three sanitized job logs and both
downloaded report artifacts were inspected, not merely the run badge.

| Job / task | Verified outcome |
|---|---|
| Archive/documentation job | Passed migration verification and audit structural validation (164 findings,424 locations,607 inventory files). No library tests in this job. |
| SDK setup on Ubuntu24.04.5 x64 and macOS26.6.2 arm64 | Failed `sdkmanager 'platforms;android-37'`: package not found. Official package is37.0; API37 itself and the project's `compileSdk=37` are valid. Both hosts skipped desktop/Android/Apple steps requiring successful setup. |
| Linux `:calf-ui:jsBrowserTest` | Executed32 tests,4 XML reports,0 failures/errors/skips, ChromeHeadless155.0.0.0. |
| Linux `:calf-ui:wasmJsBrowserTest` | Executed the same32 common tests on Wasm,4 XML reports,0 failures/errors/skips, ChromeHeadless155.0.0.0. Neither test task was cached or `UP-TO-DATE`. |
| Linux `:sample:web-js:jsBrowserDistribution` | Completed. Webpack5.108.1 reported4 warnings, including unresolved Node `os`/`path` modules and large emitted assets (8.09MiB JS,8.24MiB Skiko Wasm). This is bundling evidence, not deployed/runtime sample validation or measured user performance. |
| Linux `:sample:web-wasm:compileProductionExecutableKotlinWasmJs` | Failed with `OutOfMemoryError: Java heap space`; configured in-process heap2GiB. Whole browser/distribution Gradle command exit1 after37m16s,527 actionable tasks executed. This does not invalidate the earlier64 passing browser test executions or establish a library source defect. |
| macOS test artifact | Contains only the explicit0-file/0-test summary; no Apple test, framework link or Android build ran. |

Linux used Temurin17.0.20+1, Gradle9.7.1 and Rust1.98.0. These32 common tests cover
date bounds/range rules and dialog action policy, not DOM adapters, native file
pickers, permissions, canvas interaction or iframe behavior. The revised CI separates
browser tests from production bundling and corrects SDK setup; its independently
inspected outcome is recorded below, not inferred from this first run.

Evidence: [`run`](evidence/github-actions/gradle-run-40110188721.json),
[`terminal inspection summary`](evidence/github-actions/gradle-verification-summary-40110188721.json),
[`jobs`](evidence/github-actions/gradle-jobs-40110188721.json),
[`artifact metadata`](evidence/github-actions/gradle-artifacts-40110188721.json),
[`Linux log`](evidence/github-actions/gradle-linux-log-40110188721.txt),
[`macOS log`](evidence/github-actions/gradle-macos-log-40110188721.txt),
[`archive job log`](evidence/github-actions/gradle-archive-log-40110188721.txt),
[`independent Linux XML counts`](evidence/github-actions/gradle-junit-linux-40110188721.json),
[`independent macOS counts`](evidence/github-actions/gradle-junit-macos-40110188721.json).
Raw XML and uploaded summaries are preserved under
[`gradle-40110188721/`](evidence/github-actions/gradle-40110188721/);
its [`manifest`](evidence/github-actions/gradle-40110188721/manifest.json) records
verified GitHub artifact ZIP digests and per-file hashes.
[`log-redactions.json`](evidence/github-actions/log-redactions.json) records omitted
environment blocks and raw/sanitized log hashes. The reviewed test workflows do
not publish packages. Repository-wide Pages/deployment state is a separate migration
control and is documented in [migration](../migration/README.md), not established
by a read-only test job.

### Corrected Gradle run: successful, with explicit coverage limits

[Run40114966617, attempt1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40114966617)
on `1160893ca17404891b312990bc829535cddb75a2` completed **success** on all three jobs,
2026-10-24 17:11:10–17:34:44 UTC. All terminal logs and both artifact archives were
downloaded and inspected; each ZIP digest matched GitHub's advertised SHA-256,
and every extracted file matched the preserved bytes. No historical `docs`/`site`
reports were included in the new artifacts.

| Executed check | Verified result |
|---|---|
| Archive/documentation |536 migration checks passed; audit validation passed164 findings,424 locations and607 inventory files with no errors/warnings. Tooling integrity, not library behavior. |
| Linux desktop |86 tests across IO/picker/UI/navigation;13 XML reports. All four populated `desktopTest` tasks freshly executed. |
| Linux Android host |32 common UI tests;4 XML reports; `:calf-ui:testAndroidHostTest` freshly executed. Other host-test tasks had no sources. No emulator/device instrumentation. |
| Linux JS and Wasm browser |32 common tests each;8 XML reports; both browser-test tasks freshly executed under ChromeHeadless155.0.0.0. |
| Linux Android sample |`:sample:android:assembleDebug` completed after actual Android compilation. APK not installed, distributed or retained as a release artifact. |
| Linux browser production |Both distribution tasks succeeded. JS compiler and webpack were `FROM-CACHE`; Wasm compiler, Binaryen optimizer and webpack freshly executed with4GiB/one worker. Wasm webpack reported4 warnings, including a dynamic dependency expression and asset/entry-size warnings (534KiB JS,5.71MiB application Wasm,8.24MiB Skiko Wasm). No sample startup or user-perceived performance measured. |
| macOS desktop |86 tests,13 XML reports, all four populated desktop test tasks freshly executed. This is an additional host execution of the same functions. |
| macOS iOS simulator |32 common tests,4 XML reports; `:calf-ui:iosSimulatorArm64Test` freshly executed. The four classes are date bounds, selectable bounds, range selection and dialog action policy—not UIKit/delegate/permission/device tests. |
| macOS framework/cinterop |`:calf-webview:cinteropNskeyvalueobservingIosSimulatorArm64` and `:sample:common:linkDebugFrameworkIosSimulatorArm64` freshly executed successfully. This is a static simulator framework build, not a signed Xcode app or physical-device artifact. |

Totals: **Linux25 reports/182 executions, macOS17 reports/118 executions; zero
failures/errors/skips.** The32 common functions run on desktop twice and Android
host/JS/Wasm/iOS simulator once each;54 desktop-only functions run on both desktop
hosts. Thus300 executions represent **86 original test functions**, not300 unique
tests or any global line/branch coverage measurement.

The three Linux Gradle phases succeeded in5m,1m13s and3m11s respectively, with
compile/dependency cache use explicitly recorded in the
[machine-readable summary](evidence/github-actions/gradle-verification-summary-40114966617.json).
All seven populated Linux test-task invocations were fresh. The macOS command
succeeded in22m24s,713 actionable tasks/713 executed, including all five populated
test-task invocations. Its compiler warned that the framework bundle ID fell back
to `Common` and that four native compiler threads exceeded three processors;
these warnings did not fail compilation and merit explicit configuration review.

Linux runner: Ubuntu24.04.5 x64, image20261012.334.1, Temurin17.0.20+1.
macOS runner:26.6.2 arm64, image20261013.0424.1, Temurin17.0.20+101.
Both used Gradle9.7.1, Rust1.98.0 and canonical Android SDK package37.0; Kotlin/Native
2.4.20 was observed on macOS. Effective Xcode, Apple SDK and simulator runtime
versions were not separately printed; do not infer an exact selection or minimum
OS compatibility from the runner image alone. Some API step snapshots lagged the
completed job status; execution claims above are based on complete task logs/XML.

Evidence: [`run`](evidence/github-actions/gradle-run-40114966617.json),
[`jobs`](evidence/github-actions/gradle-jobs-40114966617.json),
[`summary`](evidence/github-actions/gradle-verification-summary-40114966617.json),
[`Linux log`](evidence/github-actions/gradle-linux-log-40114966617.txt),
[`macOS log`](evidence/github-actions/gradle-macos-log-40114966617.txt),
[`archive log`](evidence/github-actions/gradle-archive-log-40114966617.txt),
[`artifact metadata`](evidence/github-actions/gradle-artifacts-40114966617.json),
[`Linux integrity receipt`](evidence/github-actions/gradle-linux-artifact-integrity-40114966617.json),
[`macOS integrity receipt`](evidence/github-actions/gradle-macos-artifact-integrity-40114966617.json).
Raw XML/uploaded summaries are under
[`gradle-40114966617/`](evidence/github-actions/gradle-40114966617/).
No finding is automatically resolved merely because existing tests pass; its
specified regression/device/consumer checks still govern release readiness.
