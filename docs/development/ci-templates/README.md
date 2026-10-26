# Verification CI design and execution policy

Files in this directory are **design inputs, not executed workflows**. The
2026-10-26 [owner decision](../containment.md) now authorizes integrating and
automatically executing reviewed verification CI with Actions enabled/all and
no mandatory SHA pinning. No subagents or routine approvals. Only actual
revision-bound run receipts establish hosted results. Do not activate imported
release/deployment workflows; packages, releases and Pages remain gated.

## Activated development workflow (2026-10-26)

The reviewed design is integrated into the existing registered
`.github/workflows/gradle.yml` path, **manual dispatch only** on an immutable
development revision. `scripts/ci/workflow_matrix.py` provides finite profiles:
`core` (Linux desktop + Android host), `browser` (JS + Wasm), `apple` (macOS arm64
desktop + iPhone), `windows`, `extended` (Linux arm64 + macOS x64 + iPad), `all`,
and `tooling` (zero library jobs). The five incremental runtime profiles partition
the ten-slot matrix without duplicates. Each run limits runtime jobs to two at a
time and never cancels a running same-profile job on a source push. Dispatch only
needed profiles; rerun failed jobs on unchanged inputs instead of all successes.

The active workflow runs migration/inventory/index checks and all offline tooling
fixtures before library jobs. It removes sample assembly/distributions as test
substitutes. Fresh-test, native host-N/A and source/SDK receipt rules below are
unchanged. The separate manual Cargo workflow uses `cargo test --locked`; it is
not redundantly dispatched for every JVM test run.

SDK provisioning now uses reviewed `android-actions/setup-android@v3` metadata
and selected source (observed commit `9fc6c4e9069bf8d3d10b2204b1fb8f6ef7065407`),
bootstrapping SDK23 with API37.0 on each actual host. Official SDK23 descriptors
have **distinct** macOS arm64/x64 URLs; constructing a nonexistent generic mac
SDK23 URL is avoided by the SDK manager. This is partial action/dependency review,
not independent bundled-code/download trust. No GitHub credential is supplied to
SDK/Gradle jobs; SDK license text is not dumped. The selected SDK23 tool path and
API37.0 receipt are checked. The original template's bare preinstalled-SDK
assumption is not silently counted as successful provisioning.

**Integration is not execution evidence.** Hosted results will be linked from the
development index with exact revisions/run attempts; until then the runtime slots
remain unverified. Android instrumentation, packaged consumers and the complete
native/legal/dependency matrix remain separate work, not implicitly covered here.

## Proposed library matrix

`library-verification.yml.template` is manual-dispatch-only, uses a read-only
repository token, persists no checkout credentials, has no publishing/Pages/
dependency-submission/build-scan step, and uploads test evidence rather than
packages. No failed or skipped step is hidden by `continue-on-error`.

| Slot | Concrete intended runner | What would execute |
|---|---|---|
| Desktop Linux x64 / arm64 | `ubuntu-24.04` / `ubuntu-24.04-arm` | Actual library desktop tests under Xvfb, including source-declared JavaFX/JNI tests; native host resource task dependencies |
| Desktop macOS x64 / arm64 | `macos-26-intel` / `macos-26` | Actual library desktop tests on each distinct host architecture, with explicit real AppKit GUI-test opt-in required |
| Desktop Windows x64 | `windows-2025` | Actual library desktop tests; no Windows arm64 fallback |
| Android host | `ubuntu-24.04` | Real `testAndroidHostTest` library tasks, including explicitly configured Robolectric tests; **not an emulator or physical device** |
| JS and Wasm | Separate `ubuntu-24.04` jobs | Every library with inherited browser tests; the exact `CHROME_BIN` version is recorded |
| iPhone and iPad | Two `macos-26` arm64 jobs | Actual `iosSimulatorArm64Test` library tasks, including `iosTest` UIKit/Compose fixtures; explicitly selected, booted and recorded simulators |

Runner labels describe requested capacity, not observed identity. The runtime
helper checks actual architecture and JDK17, enforces the checked-in Rust version,
records Xcode version/build and three SDK versions on Apple, and binds the exact
selected simulator UDID, device type, runtime version/build and boot state. It
does not record user-assigned device names, environment values or SDK/cache paths.
The template boots only its selected CI simulator; it neither erases devices nor
operates a personal physical device. Available simulator/runtime selection is
deterministic and recorded, **not a fixed simulator-OS coverage matrix**.

## Fresh execution and coverage rules

`scripts/ci/library_tests.py plan --suite <desktop|android-host|js|wasm|ios>` reads
the repository's explicit settings includes/renames and known hierarchy. Changed
settings syntax or unknown test source groups require review instead of guessing.
It selects **library**, never sample, tasks from inherited test sources and checks
an independently declared minimum set, preventing deletion of the last tests from
silently making a required module disappear. Helpers without actual discovered
tests still fail the nonzero-case gate. Modules without relevant sources are
listed as uncovered, not counted as passing. New test-bearing modules are added
automatically; update the minimum deliberately when their coverage is accepted.

For a small helper smoke test, `--module calf-io` selects an explicitly labeled
diagnostic subset. Its receipt has `complete_suite_requested=false` and lists the
other test-bearing modules not requested. The CI template does not use this
option. Even a subset captures all known library/shared source inputs, so schedule
a short source-stable window; unrelated concurrent source repairs invalidate the
consistency receipt rather than being silently ignored.

Example, only after reserving the build slot and arranging the actual runtime:

```sh
export PATH="$JAVA_HOME/bin:$HOME/.cargo/bin:$PATH" # JAVA_HOME must identify JDK17
xvfb-run -a python3 scripts/ci/library_tests.py run --suite desktop \
  --output build/ci-verification/desktop-investigation-001
```

Each invocation:

1. Uses a new output directory and an exclusive helper lock; never overwrites an
   old receipt or kills another build. Coordinate other Gradle commands separately.
2. Hashes known source/assets, native inputs, shared/module/sample build settings,
   wrapper/locks and the test/native helpers. Hashes are consistency evidence,
   not a hermetic environment or signed attestation. Out-of-tree compiler/build
   inputs require an explicit inventory extension.
3. Quarantines **only selected generated task-report directories** under the new
   output. It does not clear project sources, unrelated tests or dependency caches.
4. Passes `fresh-tests.init.gradle.kts`: tests cannot use cached/up-to-date outputs,
   failures are not ignored, JVM forks are bounded and use `-Xcheck:jni`. Compiler
   caches can still be reused. Each expected task must emit its execution marker.
5. Counts actual `<testcase>` elements per expected module, validates declared
   counts, rejects duplicate identities, DTD/entities (including UTF-16), stale/
   future reports, unsafe paths and oversized input. Zero reports, zero non-skipped
   cases, any failure/error/unexpected skip, or a missing/duplicate runtime marker
   fail. The exact native host-N/A policy below does not count skips as passes.
6. Preserves Gradle exit failure even if other modules passed. Source/revision
   changes during execution invalidate the run. JVM/common execution is not
   relabeled as native/device coverage; repeated targets are executions, not new
   unique source test functions.

The runner keeps a local Gradle log. Uploaded receipts exclude failure/output
bodies, but the proposed workflow also retains original XML from its public
library fixtures for independent inspection. Do not upload private local
application data, environment dumps or arbitrary machine files. A missing XML/
receipt is never repaired by copying reports from an older run.

### Exact native sharing scenario eligibility

`scripts/ci/native_test_policy.py` binds the four scenarios in
`calf-share/src/desktopTest/kotlin/com/mohamedrejeb/calf/share/platform/NativeShareBridgeTest.kt`.
All four case identities must appear exactly once (KGP's `[desktop]` suffix is
recognized); deleting the native test source or a case cannot silently reduce
coverage. No arbitrary skip flag or substring/class-name exception exists.

| Scenario | Linux / Windows | macOS |
|---|---|---|
| `nativeAbiAndDiagnosticsLoadOnTheActualHost` | Required actual JNI pass | Required actual JNI pass |
| `borrowedNativeWindowPointersAreRejectedWithoutDereference` | Required actual JNI pass | Required actual JNI pass |
| `unsupportedHostRequestsAndCancellationNeverRetainNativeOwners` | Required actual JNI pass | Exact host-N/A skip, not a pass |
| `macOsPickerCancellationReleasesRealMainThreadOwners` | Exact host-N/A skip, not a pass | Required real AppKit GUI pass |

Both designated macOS desktop jobs set `NATIVECMPKIT_NATIVE_UI_TESTS=true`.
Missing opt-in, a headless session, unavailable AppKit cancellation support, or
an assumption skip on these jobs remains a failure. The helper requires the
explicit environment opt-in; an incidental external JVM property alone does not
satisfy its recorded contract. Raw XML skips remain visible; receipts separately
count `not_applicable`, `unexpected_skipped`, `passed` and `executed`. One host
passing its applicable scenarios never establishes the other hosts or the full
native matrix. All unrelated skips still fail.

## Caching and action review

The template uses exact cache keys partitioned by source commit, suite/slot,
actual host, JDK, Rust and relevant SDK/browser/simulator runtime. There are no
prefix restore keys, cross-OS archives, project outputs, native target directories,
Gradle build-cache entries, configuration caches or test XML in cached paths.
Only selected registry/distribution dependency material is cached; native
compilation remains host-local. Cache reuse is not integrity/provenance proof.
BUILD-007's independently reviewed checksums, complete locks and tamper tests
remain necessary.

The initial source-commit/slot cache partition is intentionally conservative and
inefficient: unchanged dependency graphs in another commit or suite cannot reuse
it. Once complete checked-in verification metadata/locks exist and their trust is
reviewed, partition **downloaded dependency** caches by a digest of those manifests,
verification policy, toolchains and relevant host/runtime instead. Share those
immutable downloads across suites where valid; keep any future compiled-output
cache separately keyed by source/compiler/target and keep test outputs uncached.
Do not replace this with broad prefix restores or omit a graph before it is locked.

`action-pins.json` records read-only observations of exact action metadata and
entrypoints. This is **not** a full audit of bundled JavaScript/transitive code.
The template reuses previously observed checkout/setup-java/wrapper/upload pins
and adds the observed `actions/cache` v6.1.0 commit. It intentionally avoids the
third-party Rust action's conditional network bootstrap; hosted-runner `rustup`
must already exist, and only pinned compiler components are installed. It also
does not use setup-gradle's default enhanced cache provider, injected scans or
dependency submission. Added actions require source/security review, not another
routine owner approval or a mandatory exact-SHA allowlist. The owner explicitly
accepts all actions/reusable workflows without mandatory SHA pinning; retained
SHA references are optional reproducibility controls. Keep inherited publishing
workflows inert and review the actual executed workflow, not merely this design.

## Verification state and still-missing gates

- 51 distinct offline Python fixtures validate helper logic with synthetic
  reports, runtime responses and mocked execution, including exact host aliases,
  missing/duplicate/renamed native cases, required AppKit skips, false N/A passes
  and per-report/total accounting. They do **not** run Gradle, Chrome, UIKit or JNI.
  Evidence: `../evidence/build/ci-helper-native-policy-self-tests.log`.
- The fresh-test init script and runner **have executed real local Gradle tests**:
  [IO smoke](../evidence/ci-helper-smoke-001/receipt.json) passed 22 cases (exit 0,
  71.02 s), and [NAV desktop](../evidence/nav-desktop-002/receipt.json) passed 51
  (exit 0, 38.01 s). Both are explicit subsets, not the complete desktop suite.
  [Full-requested JS](../evidence/js-full-001/receipt.json) failed (exit 1, 580.12 s):
  267 cases, 265 passed, 2 failed, and share never executed after test compilation
  failed. [Focused JS](../evidence/js-focused-002/receipt.json) also failed
  (exit 1, 80.01 s): 83 cases, 82 passed, 1 NAV failure; share 17 and WebView 29 passed.
  These Linux-x64/JDK17.0.20 runs used dirty, input-stable source at base 94d2492e;
  browser runs used Chrome 153.0.8010.36. Counts and input receipts remain separate:
  neither combining runs nor a later subset pass makes the earlier full run green.
  A separate [full JS run 003](../evidence/js-full-003/archive.json) subsequently
  passed **286/286** cases across all 19 requested modules and 48 fresh XML reports
  (exit 0, 70.02 s, 691 unchanged inputs). It includes the corrected signed-zero
  implementation and explicitly checked runtime-constructed Unicode fixtures.
  Earlier failures remain preserved. This is a local browser execution, not a
  hosted workflow run or proof of native functionality/dependency trust.
- The template has not run on any hosted runner. Its ten slots are requirements,
  not completed host/device verification. Apple/Windows/arm64 SDK/runner capacity,
  provisioning, simulator tests and JavaFX interactions remain unverified here.
  AGP evaluates SDK configuration even in library desktop/Apple jobs; installing
  the official API37 package on all requested runner images is a real, currently
  unverified prerequisite, not a promise that every hosted image provides the SDK.
- IO/picker/WebView device fixtures have separately executed in local diagnostics;
  the template still has **no instrumentation execution slot** and claims no
  hosted-device result. The [fourth IO/picker command](../evidence/android-device-004/archive.json)
  reached its 840-second bound (command exit 143): IO emitted 17 actual cases,
  16 passed and one failed its known-size metadata precondition; picker emitted
  no XML. The earlier three-module failures remain recorded in the
  [device workstream](../IO-android-device-tests.md). Local instrumentation is
  not complete, stable device CI, and the failed commands are not passing gates.
  Before adding an emulator slot, inspect actual AGP task/report contracts, record
  emulator API/ABI and require actual nonzero library instrumented execution.
  Camera hardware, real permission dialogs and process-death behavior still need
  physical-device/manual evidence where emulation is insufficient.
- A common test passing on iOS or Robolectric is not evidence that its native API
  prompt, renderer or file provider works. Required native tests must be reviewed
  by assertion/flow, not just by nonzero counts.
- Cross-browser Safari/Firefox behavior, iOS device/framework consumers, min-SDK
  Android consumers, five-host staged native artifacts, ABI comparisons, license
  obligations, strict dependency verification/locking and their tamper tests are
  separate release gates. The template neither stages nor publishes candidates.
- No old audit CI run or earlier dirty-tree test can certify changed code.

## Resource-copy regression fixture

The explicitly invoked `scripts/ci/resource-collision-probe.init.gradle.kts` is a
negative test, **not** a default CI init script. It supplies a second, distinct
origin at `jodd/net/MimeTypes.properties`. Prepare the fixture by copying the public
source file into `build/resource-copy-probe/MimeTypes.properties`; invoke the
picker's `desktopProcessResources` with this init script and require the exact
duplicate-origin error. Then invoke normally and inspect actual processed bytes.

The Linux dirty-tree runs in `../evidence/build/resource-copy-verification.json`
confirm that repeated traversal of an **identical source path** is accepted, while
equal bytes at a **different origin** remain rejected. Both native resource tasks
were subsequently `UP-TO-DATE`; this is scoped incremental evidence, not clean-cache
reproducibility or a full cross-host resource/JNI certification.
