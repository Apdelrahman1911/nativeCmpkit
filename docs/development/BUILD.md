# Build, native artifacts and verification work

This is an **in-progress development record**, not release certification. The
baseline [BUILD findings](../audit/findings/BUILD.json) and audit receipts remain
unchanged. Current owner containment means **no publication, Pages activation or
publishing-workflow activation**. Only the lead manages repository controls.

## Shared build ownership and verification

- Kotlin 2.4.20, Compose 1.12.0, AGP 9.4.0, JDK 17 and compileSdk 37 are retained.
  Android's official SDK package is `platforms;android-37.0`.
- `LibraryTests.kt` explicitly supplies `kotlin-test` to every common test source
  set. Coroutine, Robolectric and Compose test dependencies are test-scoped except
  for explicitly used production coroutine/streaming adapters.
- AGP's `androidHostTest` sources run through `testAndroidHostTest`. Resource
  processing is enabled for real Android host-test source directories. Optional
  `androidDeviceTest` sources enable an actual instrumentation compilation, not
  an assertion that any emulator/device test executed.
- Compose browser executable bundling is enabled for modules with browser-inherited
  test sources. Browser behavior must be tested in the browser, not counted from
  desktop execution of the same common functions. Bundling is an upstream Compose
  requirement; root `assemble` can consequently include additional browser outputs.
- UI iOS test sources use the real Compose test dependency. Compilation and a
  real simulator runner must establish support; dependency declaration is not proof.
- Default Gradle heap is 2 GiB, Kotlin daemon 1.5 GiB and workers two. CI should use
  in-process Kotlin within the bounded heap. Wasm production optimization requires
  a separate 4 GiB/one-worker phase based on the audited failure, not an unbounded
  global heap increase.

### Checked commands so far

| Evidence | Actual scope |
|---|---|
| `evidence/build/initial-configuration.log` and `.result.json` | First dependency/convention batch: `./gradlew help`, exit 0, 80.02 s, seven executed tasks and three up-to-date. No library tests. |
| `evidence/build/native-artifact-self-tests.log` | 24 offline Python integrity tests with synthetic binary headers. No Cargo, native loading or device/runtime evidence. |
| `evidence/build/native-staging-abi-configuration.log` | First new-DSL configuration attempt failed: KGP 2.4 removed `abiValidation.enabled` at Kotlin source level despite retaining its bytecode accessor. |
| `evidence/build/native-staging-abi-configuration-retry.log` and `.result.json` | After using the current enabling DSL, `help` passed: exit 0, 25.01 s, three executed/seven up-to-date tasks. Native/staging/notices/ABI conventions compiled; no native/source test task was executed. |
| `evidence/build/resource-identical-origin-retry.log` | The resource-repair convention compiled, but this invocation failed before native compilation because the tool shell did not expose `rustup` on PATH. Retained rather than relabeled as a passing run. |
| `evidence/build/resource-copy-verification.json` and its three command receipts | With the existing Rust PATH restored, actual Linux-x64 picker release/strict resource preparation passed in 7 s. Equal bytes from a different originating path deliberately failed in 10.04 s; a normal rerun passed in 7 s with all 13 tasks up-to-date. Actual processed MIME/native bytes were compared. No JNI/load or cross-host proof. |
| `evidence/build/ci-helper-self-tests.log` | 39 offline Python fixtures passed for runtime identity, source-set plans, strict actual-case XML accounting and simulated execution fences. This historical self-test invocation used synthetic/mock inputs; subsequent actual local helper runs are recorded below. |
| `evidence/build/javafx-registry-observation.json` | 30 public classifier artifacts returned HTTP200; ten sampled classfiles across five classifiers use major61; six exact direct-coordinate OSV queries returned no matches. Not a resolved-graph or embedded-engine security clearance. |
| `evidence/gradle/first-library-desktop.log` | Lead's first dirty-worktree library investigation failed in UI/NAV test compilation. Any independently executed suites require their own XML receipt. Do not call the whole command passing. |
| [`evidence/ci-helper-smoke-001/receipt.json`](evidence/ci-helper-smoke-001/receipt.json) | Actual fresh-test init/helper IO desktop subset: exit 0, 71.02 s, 22 passed cases in 5 XML reports; 688 captured inputs unchanged. Not the complete desktop suite. |
| [`evidence/js-full-001/receipt.json`](evidence/js-full-001/receipt.json) | Actual full-requested JS helper run: exit 1, 580.12 s; 267 cases / 265 passed / 2 failed in 46 XML reports; 18 of 19 requested modules executed. Share test compilation failed, so its missing marker/zero cases are not a pass. |
| [`evidence/js-focused-002/receipt.json`](evidence/js-focused-002/receipt.json) | Actual NAV/share/WebView JS subset: exit 1, 80.01 s; 83 cases / 82 passed / 1 NAV failure in 12 XML reports. Share 17 and WebView 29 passed; whole invocation remains failed. |
| [`evidence/nav-desktop-002/receipt.json`](evidence/nav-desktop-002/receipt.json) | Actual NAV desktop subset: exit 0, 38.01 s; 51 passed cases in 6 XML reports, not a browser fix or full-library pass. The three later helper runs each captured 691 unchanged inputs; source hashes differ between the full and focused JS runs. |

The new DSL has its own successful configuration receipt and a 48-file hash
checkpoint in `evidence/build/shared-build-checkpoint.json`; subsequent real
native/staging/test tasks remain required. Files can change while agents work,
so every later claim must bind exact inputs/revision.

The later authorized core/share module-only Android-host dependency changes and
the resource-origin repair have their current hashes in the resource-copy receipt;
the earlier 48-file checkpoint remains historical rather than being overwritten.

### Browser004 recovery: actual tests, not dependency-policy clearance

The later browser sequence is additive; none of its failures is relabeled as a
success. Counts below are actual non-skipped cases, not compiled source files.

| Run | Observed outcome |
|---|---|
| [JS003](evidence/js-full-003/archive.json) | Exit 0, 70.02 s; 286/286 cases, 19/19 requested test-bearing modules, 48 reports; 691 selected inputs unchanged. |
| [Wasm001](evidence/wasm-full-001/archive.json) | Exit 1, 418.94 s; 211 passing cases in 14/19 modules, 33 reports. Its 14 fresh configs selected the default tooling home rather than the requested prepared home. Missing modules remain unverified; the original environment/property mismatch's unique cause is not established. |
| [Wasm002](evidence/wasm-full-002/archive.json) | Exit 1, 181.03 s; 244 passing cases in 16/19 modules, 40 reports. The explicit prepared home was selected, but IO produced no XML: its executable could not resolve `./skiko.mjs`. The whole invocation remains failed. |
| [Wasm003](evidence/wasm-full-003/archive.json) | Exit 1, 65.01 s; 241 passing cases in 15/19 modules, 39 reports. IO's first plugin-only repair ran Skiko unpack/process tasks but introduced an unnecessary Compose compiler requirement; IO compilation failed because its compile classpath has no Compose Runtime. IO/camera/picker/share executed zero cases. |
| [Wasm004](evidence/wasm-full-004/archive.json) | Exit 0, 123.02 s; **290/290** cases in 19/19 test-bearing modules, 48 reports. All 19 fresh configs name the explicitly prepared Kotlin tooling home. |
| [JS004](evidence/js-full-004/archive.json) | Exit 0, 130.03 s; **290/290** cases in 19/19 test-bearing modules, 48 reports. Uses the normal `build/js` tooling context; no optional Kotlin home was requested. |

The [BUILD readback](evidence/build/browser004-runtime-readback.json) independently
rechecked all 164 browser004 archive/context file bindings, both raw and archived
copies of 96 reports, actual runtime task markers and all 38 fresh selected Karma
configs. Both runs used the same 693 selected source/build/helper inputs, unchanged
through their runs and this readback. The explicit launcher extras also matched
(12 for Wasm, 7 for JS). These are held **dirty-tree** receipts at base commit
`94d2492e99d5cbc060409d94d9f88febd06222d5`, not an immutable candidate. Five included
projects have no inherited browser tests and are not counted as passes. The two
targets reuse test functions; 580 executions do not mean 580 distinct tests.
Chrome 153 used the explicit root-container `--no-sandbox`/dev-shm wrapper, not a
new production policy or security certification.

The [optional-home helper correction](evidence/build/ci-kotlin-user-home-001/checkpoint.json)
adds a run-only JS/Wasm `--kotlin-user-home` argument, validates a nonsymlink
descendant of the repository's `build/` directory and emits the exact
`-Pkotlin.user.home=...` argument. Its 62 offline tests and
[independent repeat](evidence/review/ci-kotlin-user-home-001-lead.json) are separate
from the original 51-test receipt. The
[shell transport control](evidence/review/kotlin-user-home-property-transport-001.json)
showed that this host's `/bin/sh` discarded a synthetic dotted environment key,
while pinned Gradle/KGP bytecode accepts the exact project property. It did not
capture the original failed Gradle JVM environment or uniquely prove Wasm001's
cause. Effective use is established separately by the later fresh configs, not
merely by passing an argument.

IO now applies the established `compose.multiplatform` convention for its
transitive browser runtime resources and selects
`composeCompiler.targetKotlinPlatforms.set(emptySet())` locally: IO has no direct
Compose declarations. The pinned Kotlin 2.4.20 applicability API excludes this
module's compiler plugin without removing the required Gradle plugin or bypassing
Compose's guard. No production dependency was added solely to appease that
unneeded compiler check. The original
[plugin-only repair](evidence/build/io-wasm-skiko-001.json),
[failed compiler attempt](evidence/wasm-full-003-io-compiler/failure-review.json)
and [corrected source receipt](evidence/build/io-wasm-skiko-002.json) retain their
historical pending/failure observations; browser004 supplies later evidence.

IO ran 12 cases per browser target (5 bounded-read, 7 browser-file-read).
Wasm004's IO main compilation was **FROM-CACHE**, its test/executable compilation
and Skiko preparation **UP-TO-DATE**, and its link-sync/browser execution ran.
JS004's corresponding compilations, resource processing, link-sync and tests ran.
The readback found byte-identical `skiko.mjs`, `skiko.wasm` and `skikod8.mjs` in both
packaged IO test executables and IO's processed/unpacked module outputs. Official
Wasm wiring supplies link-sync inputs; JS uses resource processing. These logs,
bytecode and file comparisons are **not** captures of runtime Gradle task-input
properties or every process-loaded byte.

Applying Compose also retains non-browser compatibility/resource/publication
hooks. The JS IO resource-publication ZIP task ran; its Wasm equivalent was
up-to-date. Unchanged dependency declarations therefore do not prove neutral
publication variants or ABI. Non-web tests and a lead-scheduled IO-only POM/module
metadata graph review remain separate; no root assemble, staging, signing or
publishing is authorized by the browser result. Ordinary frozen/integrity
enforcement, VCS-byte trust, native/device/consumer checks and release gates remain
open.

### Android SDK identity preflight and bounded parser correction

[IO Android-host001](evidence/io-android-host-001-preflight/failure-review.json)
stopped **before Gradle or report quarantine**, exit 2 in 0.68 s, with zero library
tests. `runtime_context.android_platform` required `.isdigit()`, while the
installed official-shaped `platforms;android-37.0` metadata records
`AndroidVersion.ApiLevel=37.0` and XML `api-level=37.0`. The previous synthetic
fixture covered only integer `37`; the SDK files were not edited.

The [bounded correction](evidence/build/runtime-context-android-api-001/receipt.json)
changes only that predicate to strict ASCII major-or-major.minor full matching.
The **exact normalized identifier** remains in the existing cache fingerprint;
existing property whitespace stripping is unchanged, and no raw-RHS preservation,
float conversion or `37.0`→`37` collapse is claimed. Cached AGP 9.4.0 and Android
tools 32.4.0 bytecode/schema evidence supports the major/minor form; the older
legacy properties helper's integer-only behavior is recorded separately, not
generalized to all SDK parsing.

The same 19 focused offline Python tests first reproduced the old behavior
(exit 1, three Unicode-acceptance failures and nine valid-shape errors, including
subtests), then passed after the correction (exit 0, 0.012 s). All original nine
methods remain unchanged. Added checks cover real-shape/legacy/minor identifiers,
malformed and non-ASCII values, privacy, missing/leaf-symlink guards, exact-version
cache separation and `capture` with **mocked** tool commands and SDK roots. This is
not an actual Android host/device pass. Only the two authorized runtime-context
source/test files changed after browser004; the other 691 selected inputs and
both installed SDK metadata hashes were rechecked unchanged. The preflight failure
and browser004 source maps remain immutable; a fresh lead-owned host invocation
needs its own result.

### BUILD-007 isolated dependency tooling

The [dependency-integrity implementation](dependency-integrity.md) now has164 core006
offline parser/orchestration tests and an actual local-Maven fixture archive under
[`evidence/build/dependency-fixtures/`](evidence/build/dependency-fixtures/README.md).
Fixture001 failed closed; fixture002 established bootstrap/ordinary baseline and
exact wrong-JAR-SHA rejection. Its actual transitive lock conflict was diagnosed
from retained typed/structured evidence; the original classifier/suite exit1 is
unchanged. Fresh003 passed exactly bootstrap/baseline/transitive rejection in
25.722s (selected subset only), with an additive60-file archive verification.
Independent review found a generic lock-text false positive in four then-unexecuted
cases; the exact typed/state-bound correction has offline regressions, not a
complete four-case actual Gradle verification. Historical115-test003 and146-test004 input hashes
are preserved in independently scoped archives. The snapshot now includes stored
`kotlin-js-store` inputs. Separate005 generates private JVM/environment cache paths
and requires scoped Gradle-JVM observations; two direct JDK17 probes checked15
selected values each. **Actual004 then compiled/executed those guards in all three
invocations and recorded matching selected Gradle-JVM/environment paths.** Three
external client observations succeeded; external daemon binding and actual
Kotlin/Native/compiler cache use remain unverified. Complete
client/execution-JVM witnesses in a separately scheduled fixture are a prerequisite
to real-source acquisition. These path fences are not an OS sandbox. This does not
install any ordinary root/convention policy or verify production dependency graphs,
all hosts, library runtimes or releases. Every further Gradle run needs a scheduled
slot; containment is unchanged.

The separately frozen [passive witness proposal](../../scripts/dependencies/runtime-witness.md)
has108 targeted observer003 offline checks, distinct from actual Gradle/jcmd observations. The earlier
76-test001 archive preserves the independently reproduced mocked entrypoint/
classpath false positive;002 corrects that parser and passed independent offline
re-review. Its exact paired command subsequently ran once: **fixture004
exit1/26.715s, witness exit1/26.756s**, only three Gradle invocations0/0/1.
Bootstrap and baseline passed; missing-host-lock reached the exact typed Gradle
rejection but remained unverified because the narrow classifier did not recognize
the actual `TypedResolveException` wrapper. The other three selected negatives
never ran. All three clients were externally observed; no daemon diagnostic was
attempted. The candidate-rejection cause is unknown because002 discarded those
errors. The [004 archive](evidence/build/dependency-fixtures/fixture004/archive-verification.json)
preserves every outcome and73 bound files. No timeout/disk stop or unrelated JVM
attachment was observed; recorded fixture processes exited and the slot was
released. [Core006](evidence/build/dependency-fixtures/checkpoint006/archive-manifest.json)
then passed164 offline tests in2.637s and independent source/offline review. The
explicit observed wrapper/message is now recognized by a read-only parser replay
against retained004, not by a new successful fixture. Original results stay
unchanged. [Observer003](evidence/build/dependency-fixtures/runtime-witness003/archive-manifest.json)
passed108 offline tests in0.288s and164 unchanged core regressions in2.807s;
the separate [independent source/offline review](evidence/review/dependency-observer003-independent.md)
is GREEN (108 tests in0.273s and17 additional modeled outer-loop checks), not
an actual runtime witness. Its six-stage/85-code counters cap at1024
without raw exception/argv/environment export, ownership relaxation or retries.
26 prior function/class ASTs are unchanged. The counters are not exhaustive:
missing files or false runtime equality may produce no event; empty counters do
not prove no guard failed. Actual004's missing-daemon cause is
still unknown. Routine fixture/source acquisition is now authorized by the
2026-10-26 owner decision; technical gates and source/SDK boundaries remain,
not a requirement for another routine approval.
The [current-source acquisition proposal](build007-implementation-plan.md#current-source-acquisition-proposal-not-scheduled-or-executed)
remains unscheduled: complete actual runtime bindings, source-run wrapper
observation and an explicit SDK-write boundary still precede acquisition.

The separate [Yarn003 bootstrap receipt](evidence/build/yarn-materialization-003.summary.json)
records both project locks generated/stored, exit0/122.03s,135 bound evidence files
and **zero tests**. JS has438 registry SRI entries plus one exact-commit Kotlin/karma
codeload resolution without an integrity entry; Wasm has2/2 project-lock SRI
entries, not coverage of its separate tooling install. This is not ordinary
frozen installation, complete VCS byte integrity or release trust. Separately,
[actual JS003](evidence/js-full-003/archive.json) passed286/286 browser cases in19
modules/48 XML reports, exit0/70.02s, with691 selected inputs unchanged. This
library-runtime result does not establish frozen graph/VCS-SRI/tooling trust.
The later Wasm004/JS004 successes above extend executed browser coverage, not
BUILD-007's enforcement or independent-trust disposition.

The subsequent [cold Wasm-tooling001 diagnostic](evidence/wasm-tooling-001/archive.json)
passed one `:kotlinWasmToolingSetup` installation: exit0/94.94s,691 unchanged
selected inputs,13 archive hash bindings and **zero tests**. The Gradle launch log
records tooling cwd and actual Node/Yarn argv with `--ignore-scripts`, no frozen
flag; no external OS attachment or script-marker control is implied. Its separate
tooling lock matches KGP2.4.20's embedded bytes and has489 lexical resolvers/488
integrity entries, not two project-lock entries or a validated closure. Karma's
exact-commit VCS entry has no SRI. A fresh task-owned Kotlin home does not isolate
shared Gradle/Yarn/OS state or establish ordinary enforcement, runtime success or
independent trust.

## JavaFX: explicit application runtime, not publisher-host metadata

`calf-webview` compiles against six aligned JavaFX **21.0.13** modules using
`compileOnly`. Its published metadata must not select the producer's OS. Desktop
applications explicitly supply `base`, `graphics`, `controls`, `media`, `web` and
`swing` for **their** host. Source samples use `desktop.javafx` and WebView tests
declare their runtime explicitly. There is no silent unsupported-host fallback.

| Supported candidate host | JavaFX classifier | Native resource slot | Rust target |
|---|---|---|---|
| Linux x64 | `linux` | `linux-x64` | `x86_64-unknown-linux-gnu` |
| Linux arm64 | `linux-aarch64` | `linux-arm64` | `aarch64-unknown-linux-gnu` |
| macOS x64 | `mac` | `macos-x64` | `x86_64-apple-darwin` |
| macOS arm64 | `mac-aarch64` | `macos-arm64` | `aarch64-apple-darwin` |
| Windows x64 | `win` | `windows-x64` | `x86_64-pc-windows-msvc` |

These are the **required verification slots**, not a claim they have all passed.
Windows arm64 has no verified builder/JNI candidate and is explicitly unsupported.
Public package/class signatures are retained; removal of accidental transitive
JavaFX runtime selection is an intentional dependency migration documented for
consumers. Both POM-only and Gradle-metadata consumers must be checked.

Read-only Maven queries found all 30 classifier artifacts, and sampled JavaFX
base/module-info classfiles use Java 17 bytecode (major 61). Exact-version OSV
queries for the six JavaFX coordinates returned no matches at observation. This
is neither a full runtime-graph scan nor a statement that WebKit is vulnerability
free. Real JavaFX engine and consumer tests remain required.

## Native resource contract

`NativeLibraries.kt` replaces the two duplicated build blocks. Importable,
stdlib-only `scripts/native/artifacts.py` is the manifest/completeness oracle used
by both Gradle and the isolated consumer inspector.

- `buildNativeLib` builds **only the actual host**, using `rustup run 1.98.0 cargo
  build --locked --release --target <host>`. No release version is stamped into
  Cargo files. Native crate names/JNI symbols and `publish = false` remain.
- Both lockfiles are maintained by their source owners. The root Rust toolchain
  is exact, not a moving `stable` channel.
- Declared Gradle inputs include native source/assets/tests/config, lockfile,
  desktop JNI Kotlin source, module/shared build implementation, Git revision,
  dirty-state boolean and version. Outputs are module-local generated resources.
  Unchanged tasks can be up-to-date; a second-run proof is still required. Remote
  Gradle caching of native binaries is deliberately disabled because the system
  linker/SDK is not a fully hermetic input.
- `prepareNativeResources` validates then replaces only its generated directory;
  legacy `copyNativeLib` is an alias. Nonempty legacy source-resource payloads fail
  rather than suppress builds. Full matrix staging is explicitly different from
  a host developer build.
- `desktopProcessResources` deduplicates repeated traversal of the identical
  normalized source path at the identical destination, needed by the overlapping
  KGP/Compose hierarchy. **Different** origins at one destination still fail even
  when their contents are equal; the real negative fixture verified this distinction.
- Default `nativecmpkitNativeMode=host` builds the host. An explicit
  `nativecmpkitNativePrebuiltDir` selects `<root>/<module>` and requires that exact
  host payload. `nativecmpkitNativeMode=release` requires all five slots from the
  explicit root and clean, matching source provenance. Partial input is an error,
  never a fallback to whatever happens to be present.
- Runtime support and ABI are established separately through actual JNI tests.
  Header/machine checks verify ELF/Mach-O/PE architecture, **not JNI correctness**.

Each module's resources contain only:

```text
native/<platform>/<retained-library-filename>
META-INF/nativecmpkit/native/<module>/<platform>.json
```

Manifest schema 1 contains `module`, `platform`, `rustTarget`, `filename`, `size`,
`sha256`, additive `abiVersion=1`, `crateVersion`, `libraryVersion`, exact
`rustToolchain`, actual `rustcVersion`/`cargoVersion`, release profile, empty
declared Rust flags, `sourceRevision`, truthful `sourceTreeDirty`, `sourceFiles`
and `sourceSha256`. Source paths/hashes are recalculated from the checkout, not
trusted merely because the manifest listed them. The aggregate is SHA256 of
sorted UTF-8 lines `<sha256>  <repo-relative-path>\n`.

Native compiler inputs must remain below the module's `native/` tree. Adding
external Rust includes/build inputs requires extending the explicit inventory.
Custom compiler/profile/flags overrides fail closed instead of silently reusing
up-to-date results. No environment values or machine/cache paths are exported.

The manifest is an **integrity/consistency record, not signed builder attestation**.
A forged manifest cannot be distinguished from trusted provenance by hashes
alone. Release review must bind artifacts to the trusted producing run/revision,
and run the actual binaries on each intended host.

## Isolated candidate publications and attribution

Local staging is an explicit, non-remote operation:

```sh
./gradlew stageVerificationPublications \
  -PnativecmpkitVerification=true \
  -PnativecmpkitVerificationTargets=desktop
# A capable Apple host can select `all` after native/SDK/notice prerequisites.
```

The only unsigned allowlisted repository is named `NativecmpkitVerification` and
has the exact normalized file destination `build/verification-repo`. Desktop mode
stages root and desktop metadata/artifacts for all publishing modules; it does not
claim other target publications exist. `all` selects root, Android, desktop, JS,
Wasm, iOS device and arm64 simulator publications. Verification mode forbids every
remote/arbitrary-repository/Central task, even with an allow-publishing flag.
Maven-local is not used; the consumer fixture has no project/composite/source or
Maven-local fallback. Remote signing/authorization is never disabled by local mode.

Every Maven publication receives a same-coordinate `-notices.zip` containing
`META-INF/nativecmpkit/{LICENSE,NOTICE,THIRD_PARTY_NOTICES.md,licenses/**}`. JVM JAR
and Android AAR embedded paths are module-scoped
`META-INF/nativecmpkit/<retained-project-name>/...` to avoid duplicate paths when
multiple libraries are packaged together. KLIBs are not edited behind compiler
outputs; their accompanying ZIP is required and inspected, including icon/font
resource variants and preserved MIT text.

Rust static dependency code also needs accompanying notices. The metadata command
exports an unfiltered locked package union with crate checksums, SPDX expressions,
and manifest/lock hashes, without local cache paths. The consumer license tool
reads only explicitly selected public `.crate` caches, validates archive bytes
against Cargo.lock, and copies bounded recognized license text without extraction.
Generated `build/native-notices/<module>` is merged into that module's ZIP/JAR/AAR.
Native publication tasks reject absent, stale or incomplete collection reports.
Complete text collection is **not legal clearance**; exact obligations and actual
distributed archives still require review.

The consumer owner's first locked all-target metadata/collection attempt is in
`evidence/native-license-material-20261024T193225Z/`. Missing crate license material
remains an explicit publication blocker; staged incomplete collection reports must
not be promoted to passing live inputs or replaced with generic SPDX/template text.

## API and unresolved reproducibility gates

KGP 2.4.20's compiler-backed ABI tasks are enabled for library modules:
`checkKotlinAbi` and `updateKotlinAbi`, with reference dumps under each `api/`.
Main-compilation inputs avoid KGP's unsupported Android Maven-publication analysis.
JVM/KLIB ABI is not Swift/JNI ABI, and freshly generating the candidate's baseline
is not backward-compatibility proof. Compare retained baseline inputs, document
intentional changes and compile isolated consumers before accepting new dumps.

Gradle verification/locking, frozen npm/Yarn state and
the expanded read-only CI are **not complete yet**. Hash-locked local docs
installation, exact graph checks, actual pip tamper rejection and strict local
MkDocs build are now verified for Linux x64 CPython3.12; this remains a registry
**TOFU** bootstrap, not independent provenance review. Actual JS/Wasm lock
acquisition failed first on TLS, then hit its300s bound after progress; the
[third explicit bootstrap](evidence/build/yarn-materialization-003.summary.json)
succeeded (exit 0, 122.03 s), retaining 701 existing inputs and adding two stored
project locks (703 total). It executed zero tests. JS has 438 registry resolutions
with SHA512 integrity plus one exact Kotlin/karma commit without lock SRI; the
Wasm project lock has 2 registry resolutions with integrity. This bootstrap did
not initialize the separate Wasm browser-tooling lock or prove ordinary frozen
installation. Actual full-requested JS003 subsequently passed286/286 browser cases
(19 modules/48 reports); earlier full/focused failures remain unchanged. These
Chrome JS executions are distinct test evidence, not
retroactive bootstrap trust or a complete Wasm/browser/platform pass.
The separate later cold tooling001 installation described above is additive
installation evidence, not a replacement for browser or policy verification.
Subsequent Wasm004/JS004 each passed 290 fresh browser cases as recorded above;
neither makes the historical bootstrap trusted or establishes every platform.
Ordinary frozen installation and the exact-commit VCS entry's byte-integrity gate
remain unverified. See [dependency integrity](dependency-integrity.md).
An inactive manual-only design
and strict fresh-test helpers are documented in [ci-templates](ci-templates/README.md);
the original 51 offline fixture/syntax checks remain tooling evidence. The later
62-test optional-home checkpoint and 19-test focused Android-parser correction
are separately scoped, not retroactive changes to that original count. Separate
actual local helper runs are recorded above; none proves hosted template success,
a complete passing library matrix, or release verification. The exact native
host-N/A matrix does not count skips as passes and
requires real AppKit GUI execution/opt-in on designated macOS jobs.
Initial checksum acquisition
must be identified honestly as bootstrap rather than independent trust. Required
tamper/frozen-install tests, cross-host native/engine/UI tests, complete consumer
artifacts, library-level device tests and exact SDK/runtime receipts remain gates.
Do not reuse the audit's successful run for changed source.

## Later IO host and metadata checkpoint — 2026-10-25

This additive checkpoint supplies the later results for the earlier pending IO
host/metadata statements. Earlier text, failures and sealed receipts remain a
chronological record; they are not silently rewritten into passing results.
Finding statuses and production dependency/release gates are unchanged.

### Separate actual Android-host002 result

[IO host002](evidence/io-android-host-002/archive.json), not the 19 offline parser
fixtures, ran **21/21 JVM/Robolectric cases in five XML reports**, exit 0 in
53.01 s. The [BUILD context readback](evidence/build/io-android-host002-runtime-context-readback.json)
verified 18 archive/context bindings, both report copies, the fresh runtime task
marker and 693 unchanged post-parser inputs. IO Android main and host-test
compilation executed. The exact normalized SDK identifier `37.0` appears in its
runtime receipt and independently recomputed cache fingerprint; SDK provenance is
not established by those consistency checks.

This satisfies only the earlier requirement for a new **IO-only host** invocation
after the parser correction. Host001's exit-2 preflight failure remains intact.
No emulator/device ran; the separate Android-device004 metadata failure, picker
missing XML and broader Android/native/consumer gates remain open.

### Offline metadata generation: two failures and one narrower success

Each run below has its own prior dry-run review, explicit task subset and
individually forced POM/module generation tasks (`--rerun`, not global
`--rerun-tasks`). Ordinary dependencies/checks were not excluded or disabled.
All three used `--offline`, two workers, no parallel execution and the same 693
post-parser inputs, unchanged through independent readback. No dependency
acquisition, staging, signing, publishing or library/consumer tests occurred.

| Observation | Dry-run evidence | Actual result and fresh outputs |
|---|---|---|
| [001: root + four targets](evidence/io-metadata-observation-001/archive.json) | Exit 0 / 42.01 s; 272 graph entries, 10 requested tasks. | **Exit 1 / 26.01 s** at `:calf-core:transformCommonMainDependenciesMetadata`: 45 distinct uncached common metadata artifacts. Only root POM fresh; all five `.module` outputs absent. Existing desktop POM stale. |
| [002: desktop/Android/JS/Wasm](evidence/io-metadata-observation-002/archive.json) | Exit 0 / 21.0 s; 189 graph entries, eight requested tasks. | **Exit 1 / 24.01 s** at `:calf-io:extractAndroidMainAnnotations`: `androidLintTool` cannot resolve uncached `com.android.tools.lint:lint-gradle:32.4.0`. Desktop POM/module and Android POM fresh; Android module and JS/Wasm generation not reached. |
| [003: JS/Wasm only](evidence/io-metadata-observation-003/archive.json) | Exit 0 / 23.0 s; 112 graph entries, four requested tasks. | **Exit 0 / 27.01 s**, all four JS/Wasm POM/module files fresh. Root and Android modules remain unavailable; their failures are not rerun or cleared. |

Independent BUILD readbacks for [001](evidence/build/io-metadata001-readback.json),
[002](evidence/build/io-metadata002-readback.json) and
[003](evidence/build/io-metadata003-readback.json) checked 18/20/24 manifest-bound
files respectively, archived sanitized task/error records, parsed metadata and
original output timestamps. No mutable raw log or publication output was used to
retroactively revise those archives. The original pre-generation POMs are **not a
source-bound pre-switch baseline**. A prelaunch 003 review guard falsely matched
eight shared `NonAndroidMain` resource task names as Android-target tasks; its
correction and original observation are preserved in the lead graph review, not
counted as a library-build failure or permission to bypass checks.

003's IO JS/Wasm compilation, Skiko preparation, resource processing and resource
ZIP dependencies were **UP-TO-DATE**; archive/source-JAR tasks executed. Desktop
compilation/JAR in 002 were also up-to-date. Fresh metadata does not mean freshly
compiled libraries, a full passing KMP graph or a runtime test.

### Observed dependency variants and local payloads

All observed publications use group `io.github.apdelrahman1911.nativecmpkit` and
version `0.1.0-SNAPSHOT`. Target POM artifact IDs/file URLs use `nativecmpkit-*`;
local archive names retain `calf-*`. All three target `.module` component links
point back to `nativecmpkit-io`'s **unavailable root `.module`**. Class/linkdata and
source paths retain `com.mohamedrejeb.calf` compatibility packages. These are
metadata/name observations, not successful isolated consumer resolution.

In the following table, the shared API set is root-coordinate nativeCmpkit core
`0.1.0-SNAPSHOT`, kotlinx-io-core `0.9.1` and Kotlin stdlib `2.4.20`.

| Target module | API variant | Runtime additions | Other variants |
|---|---|---|---|
| Desktop | Shared API set | Coroutines `1.11.0` | Sources with no dependencies; no resource variant. |
| JS | Shared API set + DOM API compatibility `2.4.20` | Browser `0.5.0`, coroutines `1.11.0` | Sources with no dependencies; resource dependencies equal runtime. |
| Wasm/JS | Shared API set | Browser `0.5.0`, coroutines `1.11.0` | Sources with no dependencies; resource dependencies equal runtime. |

Both browser resource variants declare usage and library-elements
`kotlin-multiplatformresourcesjs`. Browser POMs have `klib` packaging and all
target-specific dependencies in `compile` scope, unlike their more precise
module API/runtime separation. Desktop POM has three compile dependencies and
runtime coroutines; Android POM additionally has runtime DocumentFile `1.1.0`.
The fresh root POM from 001 records core, kotlinx-io, stdlib and coroutines as
runtime dependencies. None of these lists is a full resolved dependency closure.

The separately authorized [bounded payload inspection](evidence/build/io-metadata-payload-001/receipt.json)
matched **eight local archives / eleven variant references**, including every
declared size and SHA-512/SHA-256/SHA-1/MD5 before and after readback. Its
[entry inventory](evidence/build/io-metadata-payload-001/entries.json) covers 226
entries, 3,633,714 archive bytes and 10,102,378 declared uncompressed bytes. Path,
type, count, size and expansion bounds passed; selected bytes were read in memory
without extraction/execution. Unselected bytecode/IR was not decoded. MD5/SHA-1
were checked as metadata fields, not treated as independent security evidence.

- Each **380-byte resource ZIP contains only two empty directory entries**:
  `composeResources/` and the IO generated namespace directory. They have equal
  hashes, distinct target URLs and **no Skiko payload**.
- The **3,511,274-byte JS KLIB** includes `js-reexport-symbols.mjs`, `skiko.mjs`,
  `skiko.wasm` and `skikod8.mjs`. Bounded reads of the three Skiko entries match
  the size/SHA-256 recorded for browser004's unpacked/processed/test-packaged
  copies. This comparison is not another browser execution.
- The **45,677-byte Wasm KLIB** has no Skiko filenames. The separately established
  Wasm browser link-sync path must not be confused with the directory-only
  publication resource ZIP or inferred to work for every external consumer.
- Desktop JAR and both browser KLIB publication archives each contain 11
  module-scoped notice/license/provenance files, byte-equal to current repository
  files. Source JARs and resource ZIPs lack that embedded subtree. Across three
  source JARs, 37 source entries match 19 distinct frozen source files.
- `PublicationNotices.kt:23-62,95-97` configures the supplementary
  `publicationNoticesZip` artifact and embedded notice hooks. The earlier
  “every publication receives a notices ZIP” statement describes that **source
  contract**, not verified ZIP production/distribution: none of these graphs
  executed that ZIP or publication task. Embedded project notices do not prove
  complete transitive/Skiko licensing material or legal clearance.

The source/metadata/payload checks are held dirty-tree consistency evidence at
base `94d2492e99d5cbc060409d94d9f88febd06222d5`, not an immutable candidate.
No Android AAR was inspected or certified. Full root/Android metadata,
pre-switch comparison, ABI compatibility, ordinary frozen/integrity enforcement,
independent provenance, complete accompanying notices, native/device and isolated
consumer checks remain required. The lead stopped that metadata checkpoint after
003. The later 2026-10-26 owner decision authorizes routine Gradle/acquisition/CI
verification; it does not retroactively complete any of these missing checks.
