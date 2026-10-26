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
| `evidence/build/ci-helper-self-tests.log` | 39 offline Python fixtures passed for runtime identity, source-set plans, strict actual-case XML accounting and simulated execution fences. No real CI-helper Gradle/Apple/browser/JNI invocation yet. |
| `evidence/build/javafx-registry-observation.json` | 30 public classifier artifacts returned HTTP200; ten sampled classfiles across five classifiers use major61; six exact direct-coordinate OSV queries returned no matches. Not a resolved-graph or embedded-engine security clearance. |
| `evidence/gradle/first-library-desktop.log` | Lead's first dirty-worktree library investigation failed in UI/NAV test compilation. Any independently executed suites require their own XML receipt. Do not call the whole command passing. |

The new DSL has its own successful configuration receipt and a 48-file hash
checkpoint in `evidence/build/shared-build-checkpoint.json`; subsequent real
native/staging/test tasks remain required. Files can change while agents work,
so every later claim must bind exact inputs/revision.

The later authorized core/share module-only Android-host dependency changes and
the resource-origin repair have their current hashes in the resource-copy receipt;
the earlier 48-file checkpoint remains historical rather than being overwritten.

### BUILD-007 isolated dependency tooling

The [dependency-integrity implementation](dependency-integrity.md) now has157
offline parser/orchestration tests and an actual local-Maven fixture archive under
[`evidence/build/dependency-fixtures/`](evidence/build/dependency-fixtures/README.md).
Fixture001 failed closed; fixture002 established bootstrap/ordinary baseline and
exact wrong-JAR-SHA rejection. Its actual transitive lock conflict was diagnosed
from retained typed/structured evidence; the original classifier/suite exit1 is
unchanged. Fresh003 passed exactly bootstrap/baseline/transitive rejection in
25.722s (selected subset only), with an additive60-file archive verification.
Independent review found a generic lock-text false positive in four unexecuted
cases; the exact typed/state-bound correction has offline regressions, not actual
Gradle coverage of those cases. Historical115-test003 and146-test004 input hashes
are preserved in independently scoped archives. The snapshot now includes stored
`kotlin-js-store` inputs. Separate005 generates private JVM/environment cache paths
and requires scoped Gradle-JVM observations; two direct JDK17 probes checked15
selected values each. **The new guards have not compiled/run in Gradle; actual
client/daemon and Kotlin/Native/compiler cache use remain unverified.** Actual
client/execution-JVM witnesses in the next scheduled fixture are a prerequisite
to real-source acquisition. These path fences are not an OS sandbox. This does not
install any ordinary root/convention policy or verify production dependency graphs,
all hosts, library runtimes or releases. Every further Gradle run needs a scheduled
slot; containment is unchanged.

The separately frozen [passive witness proposal](../../scripts/dependencies/runtime-witness.md)
adds91 targeted offline checks, not actual Gradle/jcmd observations. The earlier
76-test001 archive preserves the independently reproduced mocked entrypoint/
classpath false positive;002 corrects that parser and passed independent offline
re-review. Actual producer/runtime verification remains pending. No
unrelated JVM attachment was observed. Its exact
paired command and the [current-source acquisition proposal](build007-implementation-plan.md#current-source-acquisition-proposal--not-scheduled-or-executed)
remain unscheduled; independent observer review, actual fixture runtime witnesses,
source-run wrapper observation and an explicit SDK-write boundary precede real
acquisition. The six005 files remain unchanged.

The separate [Yarn003 bootstrap receipt](evidence/build/yarn-materialization-003.summary.json)
records both project locks generated/stored, exit0/122.03s,135 bound evidence files
and **zero tests**. JS has438 registry SRI entries plus one exact-commit Kotlin/karma
codeload resolution without an integrity entry; Wasm has2/2 project-lock SRI
entries, not coverage of its separate tooling install. This is not ordinary
frozen installation, complete VCS byte integrity, browser success or release trust.

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
acquisition failed first on TLS, then hit its300s bound after progress; a third
explicit bootstrap succeeded with both stored project locks and zero tests.
Ordinary frozen installation and the exact-commit VCS entry's byte-integrity gate
remain unverified. See [dependency integrity](dependency-integrity.md).
An inactive manual-only design
and strict fresh-test helpers are documented in [ci-templates](ci-templates/README.md);
they have51 distinct offline fixture/syntax checks, not hosted or real helper-test
evidence. The exact native host-N/A matrix does not count skips as passes and
requires real AppKit GUI execution/opt-in on designated macOS jobs.
Initial checksum acquisition
must be identified honestly as bootstrap rather than independent trust. Required
tamper/frozen-install tests, cross-host native/engine/UI tests, complete consumer
artifacts, library-level device tests and exact SDK/runtime receipts remain gates.
Do not reuse the audit's successful run for changed source.
