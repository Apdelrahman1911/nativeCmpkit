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
| Original IO/picker JUnit tests through direct cached compiler | **Passed15 original tests** (IO6, cache6, MIME3), unchanged baseline source, real context expect/actual and **no stubs**, Kotlin2.4.20/IO0.9.1/coroutines1.11.0/JUnit4.13.2. Does not test Gradle/Compose/native UI. | [`io-original-desktop-tests.log`](evidence/io-original-desktop-tests.log), [`io_original_tests.py`](../../scripts/audit/io_original_tests.py) |
| Original UI common assertion bodies through direct cached compiler | **Passed32 existing assertion bodies**, plus3 expected-defect characterizations, under Kotlin2.4.20. Exact common algorithm/model source and unchanged assertions; `@Test` registration removed, Compose/Material/platform types explicitly stubbed. Not a real framework or native UI test run. | [`ui-source-probes.txt`](evidence/ui-source-probes.txt), [`ui-source-probes.py`](ui-source-probes.py) |
| Permissions/geo source-isolated probes | **Passed16 deterministic checks** (11 permission/helper,5 coordinate controls), with explicit Android/CoreLocation/Compose adapters. A separate5,000,000-trial seeded antipodal search found no NaN witness; trials are not test-case counts or numerical proof. | [`permissions-geo-baseline.txt`](evidence/permissions-geo-baseline.txt), [`permissions_geo.py`](reproductions/permissions_geo.py) |
| Baseline `:calf-ui:tasks --all` and WebView desktop POM generation | **Passed**,42s; confirmed exact test/compile task names and host-specific JavaFX POM classifier defect. No publication. | [`baseline-task-inventory-and-webview-pom.log`](evidence/baseline-task-inventory-and-webview-pom.log), [`baseline-webview-desktop-linux.pom`](evidence/baseline-webview-desktop-linux.pom) |
| Migrated root/desktop POM generation plus icons resource generation | **Passed**,87s;42 POMs validated and exact resource package retained. Initial publication guard/convention scripts compiled. Later guard extensions need the final revision's configuration/CI evidence, not this earlier log. | [`migrated-poms-and-resource-package.log`](evidence/migrated-poms-and-resource-package.log), [`migrated-coordinate-and-res-checks.json`](evidence/migrated-coordinate-and-res-checks.json) |
| Cargo offline metadata, picker/share | Cache-miss failures; not Rust compiler failures. | `evidence/calf-*-cargo-dependencies.json` |
| Cargo online metadata, picker/share | **Passed resolution**:197/48 packages including roots,202 distinct non-root name/version pairs combined. No native compilation or tests implied. | `evidence/calf-*-cargo-dependencies-online.json` |
| Remote native matrix, both crates on Linux/macOS26/Windows | **Passed all three jobs / six `cargo test` invocations; each explicitly ran0tests.** Confirms host Rust compilation/test-harness startup, not native GUI/JNI behavior. Commit `cf6547931d8e339d673e7605ff5fd141a5e42091`. | [Run40106895492](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40106895492), `evidence/github-actions/native-{run,jobs,log}-40106895492.*` |
| Official wrapper/declared toolchain checks | **Passed** wrapper JAR/distribution digests; Kotlin2.4.20/AGP9.4.0/CMP1.12.0/kotlin-dsl6.7.3 artifacts accessible. | [`registry-version-checks.json`](evidence/registry-version-checks.json) |
| Exact direct Maven advisory scan |45 queries, one low-severity JavaFX media advisory match; exploitability unverified. | [`osv-direct-maven-query.json`](evidence/osv-direct-maven-query.json) |
| Exact Rust resolved graph advisory scan |202 queries, three informational unmaintained warnings; no confirmed exploit. | [`osv-resolved-rust-query.json`](evidence/osv-resolved-rust-query.json) |
| Narrow baseline secret-marker scan |548 text-like files, no matches. Not an entropy/full-history audit. | [`baseline-secret-marker-scan.json`](evidence/baseline-secret-marker-scan.json) |
| Lead's advertised-history secret-marker scan |2,638 unique text blobs, no marker matches;63 binary blobs skipped. Preserved refs only, not inaccessible/server-deleted history. | [`advertised-history-secret-marker-scan.json`](evidence/advertised-history-secret-marker-scan.json) |
| Audit resource guard and static syntax controls | Passed success/timeout/disk-preflight/publication-command rejection controls; baseline shell syntax, three TOML manifests and audit Python AST checks. Not library tests. | [`build-tooling-self-checks.json`](evidence/build-tooling-self-checks.json) |
| CI JUnit summarizer fixtures | Passed6 tooling tests: counts, aggregate exclusion, empty/malformed input, redacted output, deterministic ordering and UTF8/UTF16 DTD rejection. Not library tests. | [`junit-summarizer-self-tests.log`](evidence/junit-summarizer-self-tests.log), [`test_summarize_junit.py`](../../scripts/audit/test_summarize_junit.py) |

**Local full Gradle unit-test total at this ledger: zero executed; direct-compiler
original JUnit tests:15 passed; UI common assertion bodies with type stubs:32
passed.** These are distinct evidence levels, not one interchangeable test total.
The Gradle tasks did not reach test execution. Direct-source defect probes below
are separate. Android/iOS/Windows full builds and managed JS/Wasm tests were not
proven by the Linux checks. The lead is arranging reviewed read-only remote verification;
actual remote results must be appended with run URL, commit, job result and test
counts before claiming those platforms passed.

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
2. Install Android SDK platform37 and the build tools required by AGP9.4.0. Set SDK
   discovery through documented SDK environment/local.properties; never commit
   `local.properties` or licenses/credentials from the machine.
3. Install Rust and ensure `cargo`/`rustc` are on PATH. Future release workflows must
   use a pinned toolchain and committed locks; the baseline manifests are not locked.
4. Linux browser/desktop tests need Chrome and may need Xvfb/system UI libraries.
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
permission to run archived upstream publication/deployment workflows. Record:

| Required field | Reason |
|---|---|
| Workflow run URL, run/attempt ID, exact commit SHA | Associates evidence with the actual reviewed source and workflow. |
| Runner OS/architecture, JDK/Rust/Xcode/SDK versions | Prevents treating one host as all target coverage. |
| Job and individual task/test outcomes | A failed earlier setup step is not a compiler failure; skipped steps prove nothing. |
| Parsed JUnit/native test counts or explicit zero-tests output | Distinguishes compilation from behavioral verification. |
| Sanitized logs/artifacts and restrictions | Never archive secrets; a GitHub green badge alone is insufficient. |

`python3 scripts/audit/summarize_junit.py --root . --output build/audit-junit-summary.json`
provides a log-only, stdlib XML summary for an `always()` CI step. It excludes
`allTests` aggregate directories, does not copy failure/stdout contents, rejects
DTD/entity declarations and reports missing/malformed reports explicitly. A test
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
Android/browser and Apple framework results are still pending; append them only
after inspection and preserve the limited local evidence above.
