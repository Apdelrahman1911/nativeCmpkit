# IO / picker / Coil verification and test plan

Baseline under review: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`.
See [module internals](../modules/io-and-file-picker.md) and
[audit findings](../audit/findings/IO.json) for exact code locations and required
tests. A command appearing below is not a claim it ran: the result column and
saved evidence define the actual verification.

## 1. Executed original tests — 15 passed

```bash
python3 scripts/audit/io_original_tests.py
```

Inspected result on 2026-10-24: **`OK (15 tests)`**, compiler/run exit code 0.
Evidence: [io-original-desktop-tests.log](evidence/io-original-desktop-tests.log).

The harness:

* Extracts unchanged source files from the fixed Git baseline into an owned
  TemporaryDirectory and deletes it after execution.
* Compiles the actual core PlatformContext common/nonAndroid declarations, IO
  common/desktop declarations, NativeLibCache, the three Jodd utilities and all
  three original test files. **No stubs or source rewriting** are used.
* Uses cached Kotlin compiler/test/stdlib **2.4.20**, kotlinx-io/core+bytestring
  **0.9.1**, coroutines **1.11.0**, JUnit **4.13.2**, Hamcrest **1.3** and Java 21.
  Kotlin's common-source/expect-actual compiler flags retain the real declarations.
  Supporting compiler jars come from the installed Gradle distribution; target
  library/test jars are selected explicitly by exact version.
* Downloads nothing, writes no shared caches, loads no native library and does
  not launch Gradle, a Compose window, browser, Activity or simulator.

| Original class | Cases actually run | What they establish |
|---|---:|---|
| `KmpFileSourceTest` | 6 | 100,003-byte content equality; reads bounded by 4,096-byte chunks; context-free desktop source; missing-file error; empty-file EOF; `use` closes stream. |
| `NativeLibCacheTest` | 6 | Hash filename placement; deterministic 16-hex hash; exact new bytes; identical file untouched; different-byte replacement; unique-temp fallback for blocked target. |
| `MimeTypesTest` | 3 | Known/fallback MIME lookups; exact/multi-MIME extension sets; simple wildcard image matching. |

These are genuine executions of the original JVM tests. They **do not** verify
Gradle resource wiring/publication, the full core module, native/JNI dialogs,
Compose lifecycle, file-picker UI, Android/iOS/browser targets, or Coil decoding.
There are no original tests for those behaviors in these three baseline modules.

Reproduce on another machine by pointing `--cache` and `--compiler-support-lib`
at already installed equivalents. The script fails clearly if a required cached
jar is missing rather than downloading dependencies unexpectedly.

## 2. Additional probes — 10 passed, including confirmed defects

```bash
python3 scripts/audit/io_jvm_probes.py
# Optional older installed compiler comparison, also executed during this review:
python3 scripts/audit/io_jvm_probes.py --gradle-lib /opt/gradle/gradle-8.14.5/lib
```

Saved current-distribution result:
[io-jvm-probes.log](evidence/io-jvm-probes.log), **10/10 probes**, exit code 0.
The default run uses installed Kotlin **2.4.0** / coroutines **1.10.2**. An earlier
comparison used Kotlin **2.0.21** / coroutines **1.6.4** with the same outcomes.
These installed-runtime comparisons are not substituted for the exact-version
original test run above.

The probe compiles unchanged baseline NativeLibCache, PlatformFilePicker,
IOUtil, MimeTypes, Wildcard and the actual MIME resource. It supplies a **fake JNI
bridge, type declarations and ComposeWindow**. The fake dialog returns a selected
temporary path; file writes and filter resolution execute real source functions.
Each potentially destructive reproduction is restricted to the script's owned
TemporaryDirectory. Do not reproduce self-copy against a valuable file.

| Probe | Observed result / limitation |
|---|---|
| Cache hash/name | Known SHA prefix and extension/no-extension insertion match. |
| Cache new/reuse/replace/fallback | Exact bytes retained; old timestamp unchanged on reuse; blocked directory produces unique-temp fallback. Does not test a Windows loaded DLL. |
| MIME positive table | Whole resource initialized: 763 records, 981 unique extensions; JPEG and image wildcard cases succeed. |
| **IO-015 modern/unknown formats** | AVIF/HEIC/HEIF absent; actual Custom(image/avif) filter resolution sends null extensions (unrestricted) to fake native dialog. |
| **IO-016 comma normalization** | `image/jpeg,image/png` produces empty list; comma-space variant produces four extensions. |
| **IO-016 locale** | Uppercase TIFF lookup fails under tr-TR; lowercase tiff succeeds; locale restored afterwards. |
| Wildcard positives | Empty star, question, double star, escaped literal and mismatch behave as expected. This is not a complexity benchmark. |
| Save/copy/cancel positives | Normal streamed copy preserves content, cancellation returns null, new null-content destination is empty. |
| **IO-004 self-copy** | Actual showSaveDialogWithFile throws FileNotFoundException and source no longer exists after selecting the same source path. |
| **IO-004 null overwrite** | Existing 13-byte destination remains nonempty although null-content save returns a File. |

A probe passing an assertion about a bug means the **bug was reproduced**, not
that the product is correct. There are ten unique probe scenarios, not twenty
new tests merely because two runtime versions were exercised.

## 3. Build and native checks, kept separate

| Verification | Actual scope/result |
|---|---|
| Local full/focused Gradle desktop tests | Attempted by build reviewer. `baseline-desktop-online.log` was stopped at disk safety threshold before tests; `baseline-io-desktop-offline-focused.log` failed on missing offline artifacts. Neither is a failed unit-test assertion or an all-tests pass. |
| Native GitHub Actions run `40106895492` | Archived run conclusion success at head `cf6547931d8e339d673e7605ff5fd141a5e42091`; jobs `windows-latest`, `macos-26`, `ubuntu-latest` completed. File-picker native check/test steps compile, but each reports **running 0 tests**. No file picker was interacted with. |
| Native evidence inspected | `evidence/github-actions/native-run-40106895492.json`, `native-jobs-40106895492.json`, `native-log-40106895492.txt`. Lead owns workflow management; these are read-only validation, not release authorization. |
| Dependency resolution/advisory checks | Build reviewer owns `calf-file-picker-cargo-dependencies-online.json`, resolved Rust/Maven advisory data and conclusions in [build-security](../audit/build-security.md). Successful resolution is not vulnerability absence. |

The central [testing README](README.md) is the source of truth for any later
whole-project CI results. Do not keep this scoped report's limitations by silently
overwriting original failed-attempt logs; preserve each attempt and its context.

## 4. Missing tests and prioritized matrix

Each JSON finding carries specific tests. The following matrix groups fixtures
and harness work to avoid creating isolated one-off tests for every issue.

### P0 — data loss and unsafe memory

1. **iOS bytes (IO-001):** native unit tests for empty/one/binary files; checked-size
   helper tests at Int.MAX_VALUE and above without multi-gigabyte allocation;
   controlled sanitizer/guard-page test where supported. Missing/unreadable data
   must not masquerade as a valid empty file.
2. **Android save (IO-002/006):** Robolectric Compose ActivityResult registry that
   records the launch, recomposes/recreates the host, then delivers URI/null.
   Exercise both bytes and KmpFile plus deliberate null content, lost pending
   state, null/throwing resolver streams, cancellation and process death.
3. **Desktop handles (IO-003):** injectable native bridge or handle-registry tests
   with barriers before allocation delivery/JNI show. Dispose/change settings at
   each barrier; count creates/destroys and assert no show-after-free or leaked
   allocation. Add real JNI ASan/Valgrind stress tests on supported native hosts.
4. **Desktop overwrites (IO-004):** real filesystem tests for same path, aliases,
   hard/symbolic links, existing/absent null destinations, source read failure,
   disk full and cancellation. Preserve old destination on failed replacement.
5. **iOS exports (IO-005):** real save sheet confirms Copy/Save, not Move; exact
   requested names for all overloads; source preserved on success/cancel; staging
   failure, filename components and owned-file cleanup.

### P1 — lifecycle and portable semantics

| Fixture | Scenarios / findings |
|---|---|
| iOS delegate fakes plus simulator | Repeated nonempty PHPicker completion; empty→nonempty order; interactive photo/document/save dismissals; per-launch token; cancellation while provider work completes; no duplicate copies/callbacks (IO-007/013). |
| Real providers and grants | Android local/cloud SAF trees/documents, revoked/persisted grants; iOS iCloud/third-party folder security scope, sandbox copies and bookmarks; scope lifetime extends through stream close (IO-008/019). |
| Web JS **and** Wasm browser tests | FileReader read/error/abort; dispose during read; single resume; input node/listener cleanup; callback throws; cancel throws; same-file reselect; repeated launch (IO-009/026). |
| Browser downloads | Safari/WebKit iOS/macOS delayed object URL consumption; Chromium/Firefox positives; large/repeated downloads and failure cleanup. Real-save versus download-only callback contract (IO-011/012). |
| Metadata common/platform tests | README/dotfiles, absent paths, directories/symlinks; URI vs filesystem path; percent/space/Unicode names; original URL expiry and readable copy identity (IO-010/014/019/024). |
| Compose state tests | Recompose limits null→N and N→M; Compatible↔Current; replace parent window; callback update while dialog is open (IO-017). |
| Picker contract matrix | Multiple null/-1/0/1/2/native-cap+1; Android built-in fallback versus explicit fallback; apply limit before document staging; iOS Document/Custom UTTypes; unknown/modern MIME types (IO-015/018/025). |

### P2 — performance, packaging and hardening

* Measure Coil peak heap/read latency and cancellation with requested image sizes,
  EXIF, malformed input and large encoded data; verify decoder source closure,
  cache-key invalidation and DataSource semantics (IO-021). Include app background
  and provider removal. Do not benchmark only in-memory byte arrays.
* Test NativeLibLoader actual classpath and system-library paths, correct/missing
  native resources, duplicate classloaders, ABI mismatch, noexec/read-only home,
  absent user.home, foreign/symlinked cache directory, concurrent processes and
  Windows already-loaded DLLs (IO-022 plus build findings).
* Test parent-modal/focus behavior on Windows, macOS main-thread checking and
  closed/replaced NSWindow content views, Linux X11/Wayland portal availability
  and parent handles. Do not infer GTK behavior from a source comment: resolved
  rfd defaults here are xdg-portal (IO-023).
* Add table provenance/update tests for MIME entries, locale-independent
  normalization, unknown filters and bounded wildcard work (IO-015/016).
* Verify Android read failure closes its stream exactly once and preserves
  primary/suppressed exceptions (IO-020).

## 5. Test evidence discipline

Record command, baseline/migration commit, tool/dependency versions, host/target,
exit status, whether a real provider/native UI was used, and the assertions
actually checked. Never label zero-case `cargo test` output a native behavioral
pass, mocks a real OS picker, a compilation check a lifecycle test, or an
upstream PR author's statement a local verified result.

Resource limits: coordinate full Gradle/Cargo jobs with the lead. The shared
environment had low disk headroom; the two included scripts are intentionally
download-free and delete only their own temp artifacts. They do not require,
modify or publish to the original repository.
