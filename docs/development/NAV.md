# Navigation, core, icons and sample development (NAV-001–018)

This is additive development evidence after the immutable audit, not a rewrite of
`docs/audit/findings/NAV.json`. The lead's synchronization gate opened at
2026-10-24 18:43:24 UTC, after current Calf issues were reconciled at source baseline
`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. Development began on
`243cf1df4bff7a6d54b204f64c320124ef9e698c`, with other owners' disjoint changes in the
shared working tree. No GitHub mutation, commit, publish or independent Gradle run
was performed by this area owner.

**Live per-finding status:** [`resolutions/NAV.json`](resolutions/NAV.json).
Implemented source/new tests are not equivalent to verified runtime fixes.

Current [NAV-006 empty/nonempty policy follow-up](checkpoint-windows-consumer-nav-20261027.md#nav-006-emptynonempty-start-policy-regression):
one actual old-effect control fails, original host complete12/12 passes under real
Compose/Xvfb with726 held/copied inputs. New same-attached-controller empty-stack
method still needs immutable navigation-desktop CI; #94 stays open/partial.
No production navigation edit or whole-runtime/consumer/API-ABI acceptance.

Earlier [immutable NAV-005 original acceptance](checkpoint-navigation-verified-20261027.md):
54/54 actual desktop methods/seven fresh XML/726 exact Git inputs at70114ff3,
including both finite work/allocation methods and all52 previous identities.
Unchanged codecs/inference/type errors have four-runtime immutable evidence;
all four original NAV-005 requirements now pass. #93 closure follows pushed
evidence/exact readback; NAV-004 remains independently open. No external-input
limit, portable latency/Native-performance, consumer/ABI or release pass.

Latest [bounded navigation work/allocation checkpoint](checkpoint-navigation-work-20261027.md):
two actual JDK17 methods pass with726 held source/copy inputs, one fresh XML and12
finite thread-allocation observations after two preserved fixture compiler failures.
Five array parsers read each tested input once; no timing threshold or external-input
bound is introduced. Unchanged common codecs have four-runtime immutable evidence;
new JVM probes await `navigation-desktop` immutable CI and original acceptance.
NAV-005 remains open/partially verified; NAV-004 legacy erased reads stay independent.

## Navigation contract and execution flow

[ADR 0004](../decisions/0004-adaptive-navigation-entries.md) was written before
entry ownership changed, following the lead's compatibility review.

1. `rememberAdaptiveNavController` explicitly creates the independent Compose
   controller; old `rememberNavController` forwards to it. The separate legacy
   platform `NavHostController` is AndroidX on Android and adaptive elsewhere.
   Neither factory now claims UIKit/browser native navigation integration.
2. Controlled navigation snapshots portable values into a fresh `NavBackStackEntry`.
   Stable IDs consist of a persisted controller namespace and nonreused sequence.
   A duplicate route is a new visit. `navigate(route, Map<String, NavArgument>)`
   converts explicit defaults into values; `navigateWithValues` is the additive,
   unambiguous value API. Missing defaults resolve against the current graph;
   supplied values are immutable snapshots and remain visit-specific.
3. Graph registration rejects blank/duplicate routes. Before mutation, attached
   controllers validate route existence and required/nullability/type constraints.
   A controller populated before attachment is validated by the host. Unsupported
   arbitrary payload objects are rejected; no reflection/deep-link parser is added.
4. The host refreshes graph closures on recomposition, binds one owner per controller,
   and initializes an empty replacement controller. Changing `startDestination`
   does not reset a nonempty stack. Removing an in-use route or making its schema
   incompatible fails explicitly instead of rendering a blank screen.
5. Both composition keys and `SaveableStateProvider` keys use entry IDs. Retained
   ID sets are themselves saved, and popped IDs are removed from the holder. This
   covers duplicate routes, consecutive visits, same-frame pop/revisit and restored
   duplicate stacks without sharing state or using controller object identity.
6. The versioned saver persists namespace/sequence, IDs, routes and typed encoded
   payloads. Old route-array saves restore route order as fresh entries; ambiguous
   old route-keyed UI state cannot be recovered. Corrupt/unknown formats reject
   instead of partially restoring. Saved payloads are **not a secret store**.

### Compatibility intentionally retained, and its limits

- The exact public `backStack: SnapshotStateList<String>` getter remains. It is a
  deprecated mirror; controlled methods are canonical. An observed legacy list
  change keeps only its common prefix and recreates the suffix with fresh IDs/no
  inherited payloads. **Net-equal raw remove/reinsert changes before observation
  cannot be distinguished** and are unsupported for new visit identity. They
  are not counted as fixed by the controlled-operation regressions.
- The erased generic `AdaptiveBaseBundle.get<T>` descriptor remains callable by
  existing binaries, but its impossible runtime-type-safety promise is explicitly
  deprecated. Use new `getOrNull<T>` or existing/new typed getters. Reified checks
  cannot validate erased Array/List/Map type parameters; supported collection
  accessors inspect elements. Direct `mMap` writes and bundle value aliasing remain
  intentional. Object-array checks first scan an `Array<*>` before a reified
  whole-array safe cast. This retains JVM component checks without the JVM-only
  `isArrayOf` API, while Native/browser erasure requires element-based validation.
  On an erased target an empty `Array<Any>` is indistinguishable from an empty
  String array. Use explicitly typed String arrays for portable source behavior.
- `NavArgument.defaultValue` is now nullable with presence separate from null.
  Its JVM Object getter descriptor remains, but callers assigning it to non-null
  `Any` must handle null when recompiling. Bad defaults fail at construction;
  all built-in array snapshots/equality/hash code are content-aware.
- Raw `parseValue` retains its historical behavior. Decode the new UTF-8
  percent-encoded strings and length-framed arrays with `parseSerializedValue`.
  Null, literal `"null"`, empty arrays/elements, Unicode and URI delimiters are
  distinct. Unsupported Parcelable/XML/reflection promises were removed.
  Bulk `parseValues` avoids repeated immutable-array appends; old incremental
  append calls still copy and must not be used as a large-input linear-time parser.
- No whole-library ABI certification, native back stack/history, per-entry ViewModel
  owner, deep-link matcher or new publication of navigation is implied.

## Icons, catalogues and source attribution

- `CupertinoIcon` clears descendant text semantics in both decorative and labeled
  cases. Only a non-null description contributes an Image role/label; private-use
  text must not become an announcement. New desktop tests cover decorative glyphs,
  labeled glyphs, and a parent button retaining its own description/click action.
  TalkBack/VoiceOver and real-device rendering are separate checks, not inferred.
- `tools/icon-catalogues/` contains hashed, lossless source snapshots and explicit
  provenance. `scripts/development/generate_icon_catalogues.py` deterministically
  regenerates all three catalogue files, checks the actual font cmap and refuses
  invalid identifiers/assignments/guessed OS versions. No network is required.
  All 1,322 Cupertino constants, 1,234 glyph codepoints, sample assignments and
  6,984 SF names are preserved. **All 6,984 minimum iOS versions remain unknown**;
  system names are not runtime availability promises. This does not recover Calf's
  unidentified original generator or establish an authoritative Apple database.
- Font KDoc now correctly identifies the MIT Flutter CupertinoIcons font, not an
  Apple SF Symbols font. The existing pinned font provenance/notice is preserved.
  The build owner is responsible for distributing notices with each actual font/
  resource artifact; source-only notices or POM generation are not enough.
- Four navigation-derived helper files now contain AOSP copyright/Apache headers
  matching the verified reference snapshots in `licenses/navigation-aosp-provenance.json`
  and modification notices. Exact originally copied revisions remain unknown.
  UI-derived headers are owned/coordinated separately; no invented attribution.
- A later notice-preservation correction makes all three catalogue renders retain
  the exact existing nativeCmpkit modification header once, before `@file:`. The
  fixed historical date is not replaced on regeneration. Generator/test code was
  corrected; no generated source, pinned input or manifest was changed. This is
  source-notice preservation, not a distribution-license or OS-availability gate.

## Sample safety and correctness

- The secure/name dialog callbacks do not log or retain personal input. The secure
  field remains a secure input demonstration. Source-policy tests are not an iOS
  captured-log/device test.
- File saver reads at most 8 MiB via the IO library's new bounded API, checks decoder
  header dimensions before pixel allocation (at most 8 million pixels/4096 per side),
  produces a PNG at most 512×512, and then supplies only that bounded PNG to preview
  and saving. It does not let the original file bypass limits through an eager Coil
  preview. Selection work is canceled/rebound by `LaunchedEffect` with a generation
  guard; busy/error state prevents duplicate export preparation/presentation.
- Decode/crop/encode runs on `Dispatchers.Default`, with cancellation checks around
  the non-suspending bounded codec call. **Browser Default is still the event loop**;
  no worker-based, interruption-during-decode or measured-latency claim is made.
  Encoded/pixel limits are not an exact peak-memory proof or an OOM guarantee.
  This is a deliberately limited sample, not an unrestricted image editor.
- Privately owned software bitmaps are released after processing. Android PNG
  compression checks its Boolean result; Skia Image/Data wrappers close in finally
  blocks and reject absent output rather than force-unwrapping it. Borrowed
  caller-owned bitmaps are not closed by `toByteArray`.
- ImagePickerScreen uses lazy, 240dp-bounded previews instead of an eager scrolling
  Column. FilePickerScreen's source consumer checks cancellation/yields every64 KiB,
  detects no progress/overflow and always closes on EOF/failure/cancel. A browser
  source may still buffer at open time; the sample no longer claims universally
  constant-memory streaming.
- The undeclared Call row and unrelated SMS/all-files Android permissions were
  removed. Legacy storage declarations are capped at API32/28. Current calendar and
  local-network iOS demo keys were added in coordination with the permission owner.
  This is source configuration, not proof an OS prompt or entitlement works.
- The unused JetBrains navigation dependency was removed by the build owner.
  Showcase now truthfully says its share action is only a preview; no clipboard or
  native sharing side effect is invented.

## Verification ledger (living; see resolution records for latest state)

### Completed source/offline checks

- `python3 scripts/development/generate_icon_catalogues.py --check`: exit0,
  three generated outputs equal; all mapped glyphs present. Receipt:
  [`evidence/navigation/catalogue-check.json`](evidence/navigation/catalogue-check.json).
- `python3 -m unittest discover -s scripts/development -p 'test_icon_catalogues.py' -v`:
  **8 tests passed** on current generator/data/output and preservation against baseline.
  [`catalogue-unittests.log`](evidence/navigation/catalogue-unittests.log).
- `python3 -m unittest discover -s scripts/development -p 'test_nav_sample_contracts.py' -v`:
  **6 source/configuration checks passed**, not UI/native runtime tests.
  [`sample-source-checks.log`](evidence/navigation/sample-source-checks.log).
- Scoped `git diff --check`: no whitespace errors at the check time. Historical
  `run_jvm_repros.py`/`check_catalogues.py` still target the immutable defective
  baseline and are **not** used as fixed-code regression evidence.

### Catalogue modification-notice tooling correction

The lead's later `python3 -m unittest discover -s scripts/development -p 'test_*.py'`
check failed: **69 tests, one failure** in
`test_generated_current_sources_match_reviewed_inputs`. The original failed log
is preserved in
[`catalogue-notice-repair/development-tooling.original-failed.log`](evidence/navigation/catalogue-notice-repair/development-tooling.original-failed.log).
An independent read-only comparison found all three generated outputs differed
from the renderer only by their required leading nativeCmpkit modification notice;
the failed unit method stopped at the first mismatch.

The authorized correction changed only the generator and its Python test file.
A fixed notice prefix preserves the existing exact bytes, and one new regression
independently checks the header, its placement and nonduplication for all three
outputs. Actual subsequent commands inspected:

- Generator `--check`: **exit0, no mismatched outputs**; `--write` was not run.
- Focused `test_icon_catalogues.py`: **9/9 passed**.
- Full `scripts/development/test_*.py`: **70/70 passed**; the nine are a subset,
  not nine additional independent cases.

The [verification receipt](evidence/navigation/catalogue-notice-repair/verification.json)
preserves command/log hashes and exact before/after proofs: all691 inputs held by
the concurrent device run, all three generated Kotlin files (including the sample
catalogue), and pinned manifest/data remain byte-identical. Reversing only the
authorized generator addition and one added test reproduces both original script
hashes. No Gradle, library/source regeneration or device verification was performed
for this repair. Unknown SF availability and artifact notice gates remain open.

### Root-scheduled JVM diagnostic run, first attempt

`xvfb-run -a ./gradlew :calf-io:desktopTest :calf-ui:desktopTest
:calf-navigation:desktopTest :calf-permissions:calf-permissions-core:desktopTest
--continue --max-workers=2 --no-configuration-cache
-Dorg.gradle.jvmargs="-Xmx2048m -Dfile.encoding=UTF-8"
-Pkotlin.compiler.execution.strategy=in-process` (2026-10-24 18:52 UTC):
**exit1**. NAV production sources compiled; NAV test compilation failed on two
heterogeneous array inferences and two invariant-type `assertSame` calls. Those
fixtures were corrected with explicit types. **Zero NAV tests executed in this
attempt**. Other areas' passing tests are not substituted for NAV results.
Receipt: [`first-library-desktop.log.result.json`](evidence/gradle/first-library-desktop.log.result.json)
and matching log. This was a changing-worktree diagnostic, not immutable CI evidence.

### Root-scheduled JVM diagnostic run, second attempt

The exact command, timing and exit status are preserved in
[`second-library-desktop.log.result.json`](evidence/gradle/second-library-desktop.log.result.json);
the lead reran the selected desktop tasks, including navigation and icons, with
per-task `--rerun` under Xvfb at 2026-10-24 19:13:34 UTC. The overall command
**exited 1**. This was an uncommitted diagnostic based on
`94d2492e99d5cbc060409d94d9f88febd06222d5`; 274 selected input hashes were unchanged
during execution. It is not immutable CI or release/consumer evidence.

Inspected XML reports and the compiler log establish:

| Scope | Executed | Passed | Failed | Meaning |
|---|---:|---:|---:|---|
| Navigation common tests on desktop | 30 | 30 | 0 | Actual controller, argument/bundle and codec code |
| Navigation desktop host tests | 11 | 10 | 1 | The restoration helper failed in Compose's Skiko TODO |
| Navigation JVM descriptor/array fixtures | 2 | 2 | 0 | Narrow compatibility checks, not whole-library ABI certification |
| Cupertino icons | 0 | 0 | 0 | Test compilation failed on invalid top-level `onAllNodes` import |

Navigation totals: **43 executed, 42 passed, 1 failed, zero skipped/errors**.
The failed `save restore preserves duplicate entry state identity and payloads`
test reached `StateRestorationTester.platformEncodeDecode`, which throws
`NotImplementedError` at `StateRestorationTester.skiko.kt:21` in Compose 1.12.
It therefore did **not** verify navigation restoration and is not evidence of a
navigation implementation defect. Full failed receipts remain unchanged.
See [`second-library-desktop.summary.json`](evidence/gradle/second-library-desktop.summary.json)
and [area extraction](evidence/navigation/second-desktop-diagnostic.json).

After that run, only the two affected test files changed:

- The restoration test now supplies a real `SaveableStateRegistry` through
  `LocalSaveableStateRegistry`, calls `performSave`, and Java-serializes the complete
  produced map through an in-memory byte stream. It hides the host, waits for
  disposal and zero live effects/providers, then constructs a distinct registry
  and controller at the same composition slot. Duplicate entry IDs, route order,
  supplied payloads (including Unicode/null), both per-entry counters and the
  pop-to-original result remain asserted. A post-snapshot live counter mutation
  must not leak into the restored value. No saved controller/holder map is replaced
  with a mock or custom copy. Since desktop `MutableState` itself is not Java
  Serializable, this fixture's counter uses a normal Compose scalar `Saver`;
  the ten other host fixtures retain their original state implementation. The
  deserializer only accepts bytes just produced by this same test, never external
  files or streams. This is a desktop registry fixture, not Android Bundle or real
  process-death coverage.
- The icons test no longer imports scope member `onAllNodes` as a top-level
  extension; the unrelated unused `Box` import was also removed. Assertions remain.

At the second-run checkpoint, both repairs were **pending the next scheduled
compile/run**. Neither was called passing from source inspection or from the
earlier 42 passing tests. Their executed result follows.

### Root-scheduled JVM diagnostic run, third attempt

`xvfb-run -a ./gradlew :calf-ui:desktopTest --rerun
:calf-navigation:desktopTest --rerun :calf-geo:desktopTest --rerun
:calf-cupertino-icons:desktopTest --rerun --continue --max-workers=2
--no-configuration-cache -Dorg.gradle.jvmargs="-Xmx2048m -Dfile.encoding=UTF-8"
-Pkotlin.compiler.execution.strategy=in-process` (2026-10-24 19:22:55 UTC):
**overall exit1**, from a separate UI test failure. Actual NAV/icons results:

- **Navigation 43/43 passed**: controller13, host11, codec8, argument/bundle9,
  JVM compatibility2. The repaired real-registry byte-roundtrip restoration
  fixture executed and passed; this includes disposal, new controller/registry,
  duplicate entry IDs/payloads, independent counters and pop-to-original assertions.
- **Cupertino icons 3/3 passed**: decorative glyph silence, exactly one labeled
  Image node without text semantics, and containing button label/click retention.
- **Six XML reports, zero failures/errors/skips** for these two modules. The exact
  command/result and reports are in
  [`third-desktop-ui-nav-geo-icons.summary.json`](evidence/gradle/third-desktop-ui-nav-geo-icons.summary.json)
  and [area extraction](evidence/navigation/third-desktop-diagnostic.json).

All183 selected source hashes were unchanged during this run; base commit remains
`94d2492e99d5cbc060409d94d9f88febd06222d5`. This is scoped **desktop diagnostic
verification**, not an immutable revision, whole-command pass or completion of
the required platform matrix. Android Bundle/process death, browser/Apple common
tests, native accessibility, artifact consumers/notices and ABI checks remain
separate gates. No issue is closed from this result. Sample10 tests were not
selected and remain pending.

### Root-scheduled Linux iOS KLIB diagnostic, first attempt

The first iOS simulator Arm64 production/test **KLIB compilation** ran on Linux
at 2026-10-24 19:40:54 UTC. Exact selected tasks and options are in
[`first-ios-klib.log.result.json`](evidence/gradle/first-ios-klib.log.result.json);
[`first-ios-klib.verification.json`](evidence/gradle/first-ios-klib.verification.json)
records 222 unchanged selected input hashes. **Overall exit1; zero native tests
executed.** Navigation production failed at five JVM-only `isArrayOf` callsites:
`AdaptiveBaseBundle.kt:128/156/162`, `AdaptiveNavType.kt:250` and `NavValues.kt:64`.
Navigation test KLIB compilation consequently did not run. Icons production KLIB
compiled, which is not native rendering/accessibility or artifact verification.

The subsequent minimal common-source repair replaces those five calls and two
unchecked array casts with `CheckedNavArrays.kt`: scan star-projected elements
before a reified whole-array safe cast. It uses no JVM-only extension, reflection
or platform adapter. Exact JVM component-type rejection remains asserted, including
empty `Array<Any>`. Native's erased-array behavior is explicit rather than falsely
claiming it can recover a component type. Mixed/null String values reject before
typed access. Borrowed bundle references and copied NavArgument/entry ownership
remain unchanged; no public method descriptor changed.

Added regressions (not executed at this checkpoint): five common cases for typed/
empty/mixed/nullable arrays, caller mutation and default/entry/saver copies; one
additional JVM component-type case; two iOS cases distinguishing erased-array
element validation/borrowed aliases from owned navigation snapshots. Current
source counts are common35, desktop14 and iOS2; a desktop run selects49 and a
native run would select37, **not** the43 previously verified desktop cases.
The prior third-run PASS does not certify these subsequent edits. Sources were
refrozen for the lead's combined retry; see
[area failure/repair receipt](evidence/navigation/first-ios-klib-diagnostic.json).

KLIB typechecking is not Apple linking, a simulator executable, an XCTest/device
run, or proof of native behavior. Failed diagnostics remain intact, and no issue
status is closed from compilation or unexecuted test source.

### Root-scheduled Linux iOS KLIB diagnostic, second attempt

At 2026-10-24 **19:50:08 UTC**, the lead's combined retry successfully executed
`:calf-navigation:compileKotlinIosSimulatorArm64` and
`:calf-navigation:compileTestKotlinIosSimulatorArm64`. The common-array repair and
common/iOS regression sources therefore **compiled as KLIBs**. The whole command
still **exited1**, from a separate UI initializer diagnostic; it is not a NAV
compile failure or a passing whole batch.

The reviewer inspected the exact task lines, command/exit receipt and log hash,
then matched all22 NAV input hashes to current source. The lead's post-run receipt
records all263 selected hashes unchanged during the run. Evidence:
[`second-ios-klib.verification.json`](evidence/gradle/second-ios-klib.verification.json),
its command/log/input receipts and
[scoped independent extraction](evidence/navigation/second-ios-klib-diagnostic.json).

**Zero native tests executed and zero Apple links occurred.** The35 common and
two iOS test methods are compiled source inventory, not37 passing tests. The
Native-only erased-array/borrowed-alias behavior still needs actual execution.
This is a held-input modified-working-tree Linux diagnostic, not immutable CI,
device or release/consumer verification. The first failed KLIB receipt remains
historical evidence and was not overwritten.

### Root-scheduled JVM diagnostic run, fourth attempt

At 2026-10-24 **20:11:43 UTC**, the lead ran the exact Xvfb/Gradle command in
[`fourth-ui-ios-and-android-nav.log.result.json`](evidence/gradle/fourth-ui-ios-and-android-nav.log.result.json).
It selects `:calf-navigation:desktopTest --rerun` alongside UI iOS KLIB and
picker/geo Android-host tasks. The overall command **exited1**, from a separate
picker host fixture failure. NAV production/test compilation and `desktopTest`
executed successfully; the test task was not cached, skipped or `NO-SOURCE`.

Independent parsing of the **six fresh NAV XML reports** and verification of
every report/log hash found:

| Suite | Executed | Passed | Failed/errors/skipped |
|---|---:|---:|---:|
| `AdaptiveNavControllerTest` | 13 | 13 | 0 |
| `AdaptiveNavHostStateTest` | 11 | 11 | 0 |
| `AdaptiveNavTypeCodecTest` | 8 | 8 | 0 |
| `CheckedNavArraysTest` | 5 | 5 | 0 |
| `NavArgumentAndBundleTest` | 9 | 9 | 0 |
| `NavJvmCompatibilityTest` | 3 | 3 | 0 |
| **Total** | **49** | **49** | **0** |

This is35 common methods executed on Desktop plus14 Desktop-only methods.
It includes the five new checked-array regressions and the extra JVM component
metadata regression added after the earlier43-case pass. The actual
SaveableStateRegistry/full-map Java byte-roundtrip/dispose-recreate host
restoration test passed again. These49 executions overlap the prior43: they are
not92 distinct tests. Narrow legacy getter descriptors/runtime-array fixtures
are not whole-library ABI certification.

The lead's post-run summary records **366 selected input hashes unchanged** and
unchanged conditional target presence. At this documentation review, all25 NAV
entries in that input receipt still matched current bytes; this is not a claim
that every other module remained unchanged after its later authorized edits.
Evidence: [lead summary](evidence/gradle/fourth-ui-ios-and-android-nav.summary.json)
and [scoped independent extraction](evidence/navigation/fourth-desktop-diagnostic.json),
which preserves all49 testcase names, per-report hashes, exact command and NAV
source hashes.

The base remains `94d2492e99d5cbc060409d94d9f88febd06222d5` plus uncommitted
changes. No NAV Android/device/browser/native runtime test was selected here;
the iOS tasks in this fourth batch belong to **UI**, not NAV. Icons and sample
tests were not selected, so this result neither reruns icons nor certifies the
sample. Immutable revision, platform matrix, Android Bundle/process recreation,
native accessibility, artifact notices/consumers and full compatibility gates
remain. Findings retain their existing statuses; no issue was closed, and no
publication decision follows from these scoped results. NAV code stayed frozen;
the area owner only read evidence and updated assigned documents.

### First full-JS run: signed-zero codec defect, not an invalid oracle

The lead's full browser-JS command started at **2026-10-24 23:00:48 UTC**.
NAV's four fresh XML reports completed at 23:04 UTC: **35 executed, 34 passed,
one failed, zero errors/skips**. Controller13, checked-array5 and argument/bundle9
passed; codec7 of8 passed. The failed method is
`AdaptiveNavTypeCodecTest.primitiveArraysRoundTripNullEmptyAndValues`.

Initial diagnosis was read-only while the whole command was still running; no
source/test edits or separate Node/browser reproductions were run. The terminal
receipt arrived during documentation: the full command **exited1 at23:10:28 UTC**,
and all691 selected before/after input hashes were identical. This reviewer
independently recounted NAV's XML only and matched all32 NAV input hashes to
current bytes; other modules' terminal totals remain the lead's responsibility.

The failure is a **confirmed JS serialization defect**, not NaN inequality or a
reason to remove negative zero from the test. The actual stack's generated
`commons.js:161607` maps to source line51's
`floatArrayOf(-0f, 1.5f, Float.NaN, Float.POSITIVE_INFINITY)`. `FloatArrayType`
delegates element serialization to `FloatType`, which currently inherits generic
`value.toString()`. The generated stdlib wrapper ultimately calls JavaScript
number `toString()`, which renders `-0` as `"0"`; parsing that string returns
positive zero. Generated array equality correctly distinguishes zero signs by
reciprocals and treats NaN pairs as equal. The scalar codec shares this defect;
saved FloatArray navigation payloads use the same codec. No separate whole-saver
negative-zero reproduction was run.

The proposed narrow repair is a common `FloatType.serializeAsValue` override
that emits `"-0.0"` for an actual negative-zero bit pattern, preserving all other
formatting, parsing and framing. Both scalar and array bit-sensitive +/-0 cases
must be added without weakening the original test or dropping NaN/infinity.
There is no separate Float-list codec to patch. **At this diagnostic checkpoint
the repair is not applied or verified**, and the source freeze remains in force
until the lead releases it. Historical desktop49/49 results are preserved; they
do not certify this JS edge case or a future patch.

Evidence: [read-only diagnostic, exact source/generated-bundle excerpts,
terminal receipt hashes and raw NAV XML copies](evidence/navigation/first-js-float-codec/diagnostic.json).
This is a held-input dirty-worktree diagnostic, not immutable release/consumer
evidence; NAV-005 remains open for correction and verification.

### Authorized signed-zero correction, awaiting execution

After the lead captured the terminal [full-JS archive](evidence/js-full-001/archive.json)
and released its source freeze, the authorized patch changed only
`AdaptiveNavType.kt` and `AdaptiveNavTypeCodecTest.kt`. `FloatType` now emits
`"-0.0"` when `value == 0f && value.toBits() == Int.MIN_VALUE`, otherwise retaining
`value.toString()`. The zero guard avoids treating a tiny nonzero JS number as
negative zero merely because conversion to Float bits rounds it to zero.
`FloatArrayType` already delegates to this scalar serializer; neither the array
format nor raw parsing was changed.

Two common methods explicitly check scalar and FloatArray round trips for both
zero signs, +/-1.5, smallest-positive and largest-finite Float values with both
signs, NaN and both infinities. They assert the zero input bits, distinct scalar
zero encodings and returned `toBits()` values. NaN bits are canonicalized by
`toBits()`; arbitrary NaN-payload preservation is not promised. The original
failing method and its equality oracle are unchanged.

The [source checkpoint](evidence/navigation/signed-zero-source-checkpoint.json)
records exact before/after hashes. Removing only the authorized additions
reproduces the two failed-run hashes, independently confirming patch scope.
The two files are refrozen for lead-scheduled desktop/JS and subsequent Wasm
verification. **No post-patch compilation or test has run at this checkpoint**;
the planned unfiltered NAV selections are desktop51, JS37 and iOS39, not passes.
The first failing XML and generated-bundle evidence remain intact.

### Focused verification: Float repair passed; a generated Unicode fixture changed

The lead's focused JS run at **2026-10-24 23:17:59 UTC** executed all37 NAV common
methods: **36 passed, one failed, zero errors/skips**; the command exited1. Its
subsequent Xvfb desktop NAV run at **23:19:20 UTC** exited0 with **51/51 passed**.
Both had691 identical before/after input hashes; this reviewer independently
verified all32 NAV input hashes and recounted the four JS/six desktop XML reports.
The original FloatArray regression **and both new signed-zero methods passed on
both runtimes**. The desktop host restoration/identity fixtures passed again.
See the [independent focused result extraction](evidence/navigation/signed-zero-focused-verification.json).
These are overlapping methods on two runtimes, not88 distinct tests.

JS's new failure is a separate **emitted-fixture discrepancy**, not a reason to
undo the Float repair or relax navigation validation. The second assertion in
`unsupportedPayloadsAndSchemaOnlyNavigationArgumentsFailBeforeMutation` expected
rejection of `"\uD800"`, but the generated pre-webpack module already passed ASCII
`'?'` instead. The first run's generated method passed `'\uD800'`; the entire
method diff changes only that literal, despite unchanged controller-test source.
The regenerated codec test still contained `'\uD800'` and rejected it correctly.
The emitted production `newEntry` and `encodeNavString` bodies were identical.
The failing method owns a fresh local controller and each generated test wrapper
creates a fresh test instance; the observed input discrepancy explains this
failure without a shared-state/order hypothesis. The preceding unsupported-Any
assertion passed; later route/schema assertions within that failed JS method did
not execute, although their desktop method passed.

The [transport diagnostic](evidence/navigation/js-surrogate-transport-diagnostic.json)
preserves both bundle hashes, exact method diff, pre-webpack hash/lines and source
excerpts. Loss is established **before webpack**, but the precise compiler/cache
stage is not isolated; no independent cold/warm compiler reproduction was run.

After both runs were archived, the lead authorized a **test-only** correction:
the two existing malformed-string cases now construct U+D800 with
`charArrayOf(0xD800.toChar()).concatToString()`. Explicit length1 and code-unit
`0xD800` assertions precede the unchanged rejection assertions, so a future input
substitution cannot silently turn the test into a valid-string probe. All30
other NAV inputs, including production and the Float repair, are unchanged.
The [fixture source checkpoint](evidence/navigation/surrogate-fixture-source-checkpoint.json)
verifies that reverting only these constructions/preconditions reproduces both
focused-run test hashes. These later fixture edits were **not yet compiled or
executed at that checkpoint**. Sources were refrozen, and JS remained a failed
gate until the subsequent full-JS execution below. No issue was closed.

### Full JS003: numeric Unicode fixtures and Float regressions executed successfully

The lead's complete JS command ran at **2026-10-24 23:56:31–23:57:41 UTC** and
**exited0 after70.02 seconds**. Its archive reports286/286 across19 test-bearing
modules; this reviewer independently recounted **NAV's37/37**, not every module:

| NAV suite | Executed | Passed | Failed/errors/skipped |
|---|---:|---:|---:|
| `AdaptiveNavControllerTest` | 13 | 13 | 0 |
| `AdaptiveNavTypeCodecTest` | 10 | 10 | 0 |
| `CheckedNavArraysTest` | 5 | 5 | 0 |
| `NavArgumentAndBundleTest` | 9 | 9 | 0 |
| **Total** | **37** | **37** | **0** |

Both malformed-string methods passed their **runtime length1/code-unit0xD800
preconditions and retained rejection assertions**. The inspected pre-webpack
module and the matching fresh Karma bundle construct the input from numeric55296
Char arrays; neither substitutes `'?'` for that value. The original primitive
FloatArray test and both explicit signed-zero methods also passed again.

The [independent source/XML/emitted-fixture receipt](evidence/navigation/full-js-003-verification.json)
records the exact command, source and artifact hashes, relevant generated-code
excerpts, all37 testcase names, and timestamps/mtimes inside the run interval.
All691 before/after input entries were identical, and all32 NAV inputs still
matched their held hashes and the test-only fixture checkpoint at review.
Exactly one fresh NAV test-runtime marker was present. Production
`compileKotlinJs` was **UP-TO-DATE**; test compilation, executable linking and
browser tests executed. No production recompilation is invented.

This is a successful current **JS runtime** check, not an immutable release
candidate or a reason to close findings. The earlier desktop51/51 predates the
two runtime-surrogate fixture edits; this run does not rerun desktop host tests,
Android/Apple devices, Wasm, ABI or artifact consumers. The initial Float failure,
later emitted-fixture failure and their diagnostic/source checkpoints remain
unchanged. The precise compiler/cache stage of the earlier surrogate loss is
still unisolated; a passing runtime-input correction does not resolve that
toolchain investigation or other required platform/distribution gates.

### Contained Wasm004/JS004 and current-fixture desktop001 verification

The next held-source checks on **2026-10-25** all completed successfully. This
area independently recounted NAV's fresh raw/archived XML, rather than treating
the other modules' aggregate totals as NAV coverage:

| Lead invocation | UTC interval | NAV passed/executed | NAV scope |
|---|---|---:|---|
| [Full Wasm004](evidence/wasm-full-004/archive.json) | 01:25:19–01:27:22 | **37/37** | All common NAV methods on browser WasmJS |
| [Full JS004](evidence/js-full-004/archive.json) | 01:28:05–01:30:15 | **37/37** | The same common methods on browser JS |
| [Scoped IO+NAV desktop001](evidence/io-nav-desktop-001/archive.json) | 01:33:37–01:34:13 | **51/51** | Common37 plus host11 and JVMcompat3 |

Each command exited0; there were **zero NAV failures/errors/skips** in four,
four and six XML reports respectively. The two complete browser commands each
report290/290 across19 modules, while the scoped desktop command reports73/73
acrossIO+NAV. Those broader counts are attributed to the lead, not independently
recounted here. NAV's **125 target executions reuse51 distinct source methods**:
37 common methods on three targets plus14 desktop-only methods. Prior JS003 or
desktop passes are not additional unique tests.

Both runtime-constructed U+D800 fixtures passed their actual length1/code-unit
preconditions and retained rejection assertions **on all three targets**. The
original FloatArray regression and both explicit signed-zero methods also passed
on all three. Desktop now executed the **current** two fixture implementations,
removing the earlier pending-desktop-fixture gap. Its11 real Compose host tests
passed again, including registry/full-save-map Java-byte/dispose/recreate
restoration; its three JVM checks remain narrow compatibility fixtures, not an
ABI certification.

The [combined independent receipt](evidence/navigation/browser004-desktop001-verification.json)
preserves commands, source/report/context hashes, all testcase names, selected
fixture source and emitted-entry evidence. All693 before/after input entries
were identical for each run; the same32 NAV hashes matched current bytes and the
original runtime-surrogate refreeze throughout all three readbacks. Fresh NAV
runtime markers and XML/config timestamps were inspected. **Browser production,
test compilation and executable linking were UP-TO-DATE**; the test tasks really
executed. Desktop production was UP-TO-DATE and its test compilation executed.

Fresh generated [Wasm](evidence/wasm-full-004-context/context-review.json) and
[JS](evidence/js-full-004-context/context-review.json) configurations matched their
archived hashes/selected fields. Wasm's config selected the prepared tooling home
and `load.mjs → test.mjs → .wasm/startUnitTests` path; loader text and binary
magic/version/hash were inspected, **not Wasm instruction disassembly**. JS's
generated module retained both numeric55296 constructions/preconditions. The
[desktop context](evidence/io-nav-desktop-001-context/context-review.json) bound
the fixed IO+NAV subset to Xvfb with matching selected executable/driver hashes.
These checks bind selected observed paths; they do not attest every process byte,
transitive dependency or later executable configuration branch.

All previous failures and diagnostic/source checkpoints remain unchanged, and
**all finding statuses are retained**. Android Bundle/process death, Apple/native
runtime and minimum-platform checks, immutable-candidate/consumer/ABI gates,
exact originally copied source revisions, artifact notices and legal/distribution
review are not promoted by these results. The two iOS-only methods remain
unexecuted. No source/script edits, new builds, GitHub operations, commits or
publishing were performed by this readback owner.

### Added runtime test inventory and remaining verification

- Navigation: 37 common tests, 14 desktop tests and two iOS tests (51 selected on
  desktop, 39 on iOS). Actual library classes; no copied controllers or stubs. Covers
  typed/default/null arguments, safe getters/collection checks, value snapshots,
  codecs, schema/route ownership, old/new saver and corrupt formats, source/JVM
  compatibility fixtures, host duplicate/same-frame/closure/controller replacement,
  state cleanup, and the real Compose registry/byte-roundtrip save/restore fixture
  above. **The earlier49 passed in the fourth desktop diagnostic**, including the
  common-array repairs/regressions; the second iOS KLIB diagnostic compiled
  production and common/iOS test sources but executed **zero** native tests.
  The first JS run then executed the earlier35 common methods with34 passes and
  one real signed-zero codec failure. The focused reruns verified that repair:
  NAV desktop51/51, JS36/37, including all three original/new Float regressions
  on both. JS failed instead on the generated malformed-string input discrepancy.
  Full JS003 then passed **37/37**. Current Wasm004 and JS004 subsequently passed
  **37/37 each**, and desktop001 passed **51/51**, including both latest runtime-
  surrogate preconditions/rejections and all three Float regressions on all three
  targets. These125 executions cover51 distinct methods. Immutable-revision,
  Android, Apple/native-runtime and distribution/consumer gates remain separate;
  no iOS-only execution is inferred.
- Cupertino icons: three actual desktop semantics tests passed in the third
  desktop diagnostic after the second run's compilation failure.
- Sample: six common cancellation/bounds tests and four actual desktop Skia codec/
  output/header-limit tests, **not yet compiled/executed in this development
  phase**. The sample tests do not substitute for library IO, picker, permission
  or native UI integration tests owned by other areas.

Scheduled JVM/Android/JS/Wasm/Native results, packaged notices and consumer tests
must be added after command/report inspection. No device/platform result is assumed.
The remaining gaps in `resolutions/NAV.json` are release/closure review inputs,
not a blanket declaration that the whole library is ready to publish.
