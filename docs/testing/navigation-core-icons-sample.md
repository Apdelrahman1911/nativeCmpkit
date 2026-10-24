# Testing: navigation, core, icons and sample applications

Baseline **`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`**, reviewed2026-10-24.
Read the [central execution ledger](README.md) for full build/remote CI outcomes.
This area distinguishes four different claims: source inspection, executable
isolated baseline probes, full project tests, and device/integration behavior.
Only the first two were completed locally for navigation/icons by this reviewer.

## Executed checks

### 1. Pure Kotlin JVM baseline probes — exit0, ten assertions

Run from the repository root:

```sh
python3 docs/testing/evidence/navigation-core-icons/run_jvm_repros.py
```

The runner obtains four **unchanged baseline** files with `git show`:

- `calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt`
- `calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBundle.kt`
- `calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt`
- `calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt`

It uses the already-cached Kotlin2.4.20 compiler/stdlib through
`org.jetbrains.kotlin.cli.jvm.K2JVMCompiler`, a512MiB compiler heap, and Java to run
`ReproKt`. No Gradle build, network download, repository source edit, Compose stub
or fake bundle implementation is used. Temporary source/JAR files are removed by
the runner. It fails clearly if a required compiler dependency is not cached;
`--cache PATH` can select a different Gradle `modules-2/files-2.1` cache. The script
contains exact bootstrap coordinates (including compiler-support jars) rather
than silently substituting the project's runtime dependency versions.

| Assertion | Observed baseline result | Meaning |
|---|---|---|
| Typed Int argument, no default | IllegalArgumentException | Reproduces NAV-003 |
| Nullable String argument, explicit null default | IllegalArgumentException | Reproduces NAV-003 |
| Int type with String default | Construction succeeds; putDefaultValue throws ClassCastException | Reproduces NAV-003 |
| StringArray inference with explicit-array control | Inference throws; explicit put/get returns expected array | Reproduces NAV-005 without assuming arrays are wholly unimplemented |
| Generic String lookup of stored Int | JVM ClassCastException despite safe-cast-looking implementation | Reproduces NAV-004; exact JS/Native behavior still needs tests |
| getString(Int42), with/without fallback | `"42"` in both cases | Reproduces NAV-004 contract violation |
| Generic Float insert with direct-setter control | putObject rejects; putFloat/getFloat succeeds | Reproduces NAV-004 |
| URI-delimiter String serialize | Unescaped input returned | Reproduces NAV-005 contract mismatch, not a live route-injection exploit |
| Int/Long/Boolean/array parse controls | Hex Int, uppercase Long L suffix, strict bool rejection and append order correct | Positive controls |
| NavArgument.verify controls | Rejects wrong type/explicit null; accepts correct Int | Positive controls, not proof of missing-required validation |

Inspected output is archived in
[`evidence/navigation-core-icons/jvm-repro-result.txt`](evidence/navigation-core-icons/jvm-repro-result.txt).
The compiler's only observed warning was the unnecessary safe call on nonnull
`defaultValue` at baseline NavArgument66. **A PASS here means the expected baseline
behavior, including defects, was reproduced. It is not ten passing production
correctness tests.** To write regressions for a fix, invert the defect expectations
against the changed implementation while retaining separate baseline evidence.
The final local rerun used OpenJDK21.0.12 and again exited0; targeted tool versions,
60 baseline finding locations (one binary verified by hash), schema/report-link
checks and zero validation errors are recorded in
[`review-validation.json`](evidence/navigation-core-icons/review-validation.json).

Source/harness:
[`Repro.kt`](evidence/navigation-core-icons/Repro.kt),
[`run_jvm_repros.py`](evidence/navigation-core-icons/run_jvm_repros.py).

### 2. Complete generated catalogue and font structure check — exit0

```sh
python3 docs/testing/evidence/navigation-core-icons/check_catalogues.py
```

Uses only Python standard library and `git show` from the baseline; no font SDK,
network or Gradle/resource compilation required. The checker:

1. Reads the TTF directory and Unicode cmap tables (implemented formats4,6,12;
   fails instead of silently skipping an unsupported format).
2. Parses every Cupertino and SF `const val`, including Kotlin backtick identifiers.
   Checks parsed counts against literal declaration count so escaped names are
   not accidentally omitted.
3. Verifies unique identifiers and unique SF values, nonzero font mappings for
   every Cupertino constant, and that all bundled constants are BMP-compatible.
4. Parses every sample IconEntry, checks unique display names, exact coverage of
   exposed constants, valid references and category counts.

Inspected result:
[`catalogue-result.json`](evidence/navigation-core-icons/catalogue-result.json).

| Metric | Result |
|---|---:|
| Font bytes |257,628 |
| Font SHA256 |`67c44fe9183b002e79dde7f6977e2988661c9a3e4a3c5fce968787efdbed823c` |
| Unicode cmap nonzero mappings |1,274 |
| Cupertino declarations / distinct identifiers |1,322 /1,322 |
| Distinct exposed codepoints |1,234 (aliases permitted) |
| Missing glyph mappings / out-of-BMP constants |0 /0 |
| Sample entries / distinct display names |1,322 /1,322 |
| Unresolved references / unrepresented constants |0 /0 |
| SF declarations / distinct identifiers / distinct values |6,984 /6,984 /6,984 |
| Unparsed Cupertino / SF declarations |0 /0 |

This is **not** a glyph screenshot, name-to-shape meaning check, accessibility
test, GPU/font-load performance test or Apple symbol availability test. A font
mapping can exist while the rendered meaning/size/semantics are wrong. It also
does not prove Compose resource inclusion in every produced package.

### 3. Font/source notice provenance — checked separately from rendering

Read-only retrieval compared the complete local baseline font byte-for-byte with
Flutter/packages at the pinned commit in
[`licenses/cupertino-icons-provenance.json`](../../licenses/cupertino-icons-provenance.json).
The MIT text was downloaded verbatim, SHA256 verified, and stored locally with
copyright attribution. Jodd's five pre-existing headers were normalized only for
comment prefixes and compared as identical; they were **not missing at baseline**.
Compose Cupertino/Kyant/AOSP reference notices and hashes are preserved under
`licenses/`; observation pins are not original-copy-version claims.

These operations establish the identified source/notice evidence. They are not a
full dependency-license certification, signed SBOM, native runtime test or package
publication. Inspect built distribution contents before claiming notice packaging.

## Original project tests: inspected, not locally completed

The only navigation tests are in
`calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/AdaptiveNavHostStateTest.kt`:

| Lines | Test | Actual coverage |
|---|---|---|
|23-46 | `saveable state of a destination survives navigating away and back` | Increment Home counter, navigate Detail, pop, observe Home1 |
|49-71 | `saveable state of a popped destination is dropped` | Navigate Detail, increment, pop/idle, revisit, observe Detail0 |
|74-80 | Counter helper | Uses rememberSaveable inside a Button; not a plain-remember lifecycle test |

They do not exercise duplicate routes, payload arguments, controller replacement,
graph mutation, invalid/removed routes, deep links, process restore, predictive
back, UIKit gestures, browser history or coroutine/resource cancellation.
Core, Cupertino icons and sample roots contain no baseline test suite.

The build reviewer coordinated a full baseline run including
`:calf-navigation:desktopTest`. Logs were inspected for commands/results:

| Attempt | Outcome and evidence |
|---|---|
| Unmodified baseline, offline, provisioning disabled | Exit1 before configuration: installed OpenJDK does not meet forced JetBrains JDK17 criteria. [`baseline-desktop-offline.log`](evidence/baseline-desktop-offline.log) |
| Baseline detached worktree with daemon criteria disabled, offline | Exit1: kotlin-dsl6.7.3 plugin not cached; not a navigation compiler diagnostic. [`baseline-desktop-daemon-override.log`](evidence/baseline-desktop-daemon-override.log) |
| Online, criteria override, Xvfb, capped heap/workers | Convention plugins/configuration ran; exit143 after controlled disk-reserve stop, before library tests. [`baseline-desktop-online.log`](evidence/baseline-desktop-online.log), [`disk-safety-stop.json`](evidence/disk-safety-stop.json) |

The online run's commands selected IO/picker/UI/navigation together, but selecting
a task does not mean it executed. No navigation test XML/pass count was produced.
Later central CI results must identify their own revision/run/artifacts; do not
substitute historical upstream PR claims or zero-test Rust jobs for these tests.

## Regression plan by finding and layer

### Common/JVM model tests (no native UI required)

- `NAV-001/002`: immutable entry IDs, payload default merge/type validation,
  independent repeated-route entries, pop identity and saver round-trips.
- `NAV-003/004/005`: absent versus null defaults, invalid types at construction,
  checked getters/fallbacks, all generic setter cases, array null/empty/mixed
  values, Unicode/URI/null-string round-trip, unsupported class diagnostics.
- Model/property tests for large stacks, repeated pop at root, externally mutated
  stack policy, unknown restored routes, duplicate graph definitions, and bounded
  repeated-array accumulation. Do not store secret payloads in reproduction data.
- Port erased-generic assertions to JS/Wasm/Native to record actual language-
  backend differences; Kotlin common compilation alone is insufficient.

### Compose host and semantics tests

Extend the real `runComposeUiTest` tests with:

1. A -> B -> A, consecutive A -> A, and independent restoration after popping
   duplicate entries; verify fresh plain and saveable state under intended policy.
2. Pop/re-push the same route without an idle frame; state must not resurrect a
   completed entry accidentally.
3. Controller replacement, captured callback update, and startDestination changes
   at the same composition site; no stale controller/empty-screen surprise.
4. Invalid route and duplicate definition diagnostics; upgrade/removed-route saver
   migration behavior.
5. CupertinoIcon null-description produces no readable glyph-text node; a labeled
   icon has exactly one meaningful image label. Test merged/unmerged semantics
   inside clickable components, RTL, high font scale and custom modifier labels.
6. Sample tab retention, back buttons, route registration coverage, search/filter
   count and lazy catalogue item identity.

Example **future** focused command after toolchain/disk prerequisites are met:

```sh
xvfb-run -a ./gradlew :calf-navigation:desktopTest \
  --no-daemon --max-workers=2 --no-configuration-cache
```

Coordinate all heavyweight runs with the lead and use the central resource guard.
Do not clear unrelated caches or change project dependency versions merely to
obtain a green result.

### Sample failure/cancellation tests

- Synthetic secure text must not occur in captured logs; never use an actual
  password to demonstrate `NAV-012`.
- Fake slow RawSource counts and records close; cancel between chunks, reselect
  and leave composition; assert bounded further reads and no stale UI updates.
- Export empty/corrupt/revoked/huge-dimension images; limit read bytes and decoded
  dimensions; simulate encoder null/false/error; verify busy state, cancellation
  and user-facing recovery. Measure peak memory and frame responsiveness instead
  of guessing an OOM threshold.
- Many-image selection should instantiate only visible/lazy items within a
  documented bound. JS/Wasm tests must measure whole-Blob buffering separately.
- Clipboard demonstration must either perform and verify one user-requested copy
  or display truthful illustrative text. Do not claim the distinct ShareScreen
  was tested just because a dialog appeared.

### Platform integration matrix (not executed locally here)

| Platform | Required evidence |
|---|---|
| Android23 library consumer / sample24+ | Compile consumer and sample; inspect merged manifest; root/system/predictive back, rotation/process recreation, fresh-install Call/media/notification cases, TalkBack, picker/camera/export denial and revoked URI, file-provider URI scope |
| iOS oldest/current supported target | Xcode framework/app build with owner signing, native back buttons/modal/tab transitions, VoiceOver, real symbol availability fallback, font rendering, camera/photo/export privacy scopes, modal nesting, repeated enter/leave memory graph. Baseline app target overrides to18.5; iOS26 compile SDK and glass branches are separate |
| Desktop JVM Linux/macOS/Windows | Real Window/filepicker owner behavior, file/export cancellation, font rendering/accessibility, OS back/key handling under declared contract; desktop JVM is not a Kotlin/Native support claim |
| Browser JS/Wasm | Both sample bundles load, resource font fetched, search/grid behavior, unsupported-Wasm warning, browser navigation contract (currently no history bridge), large Blob memory/cancellation, accessibility and no-op feature messaging |

### Asset/license/generation gates

- Inspect actual AAR/JAR/KLIB/framework/JS/Wasm/application distributions and
  accompanying legal materials for complete known MIT/BSD/Apache notices.
- Preserve verified font bytes/provenance; ensure public resource package remains
  compatible after migration. A generated resource accessor alone is not a
  packaged-font runtime test.
- Add deterministic generators and source-version manifests for both catalogues;
  rerun complete declaration checks on every update.
- Check newest SF names on older iOS releases and define deliberate fallback;
  do not download/repackage Apple font artwork under the library's Apache license.

## Results reporting rules for future maintainers

Record exact commit, command, exit status, real test count and limitations. Keep
source-probe success separate from JUnit/Compose/device results. `NO-SOURCE`,
`SKIPPED`, toolchain configuration, successful POM generation and historical green
badges are not executed tests. When a baseline reproduction intentionally proves
a bug, retain that evidence and add a new regression expectation for the fixed
revision rather than editing history to suggest the bug never existed.
