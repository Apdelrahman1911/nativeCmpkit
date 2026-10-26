# Contained development checkpoint — 2026-10-25

**Not a release or completion claim.** The owner's repeated **contain** instruction
keeps Actions, packages, releases and Pages off. Work remains on the additive
`development/preview-hardening` branch; `main` retains the issue-sync commit
`94d2492e99d5cbc060409d94d9f88febd06222d5`. No development finding has been closed.
The [readiness ledger](release-readiness.md), not this progress report, controls
the remaining verification gates.

## Preserved migration and issue work

- All 16 open upstream issues in the
  [2026-10-24 reconciliation](upstream-sync-20261024T183300Z/README.md) were already
  mapped; their descriptions, references, labels and relevant history were
  refreshed without duplicate issues. One open pull request was recorded
  separately. This is a dated observation, not continuous upstream monitoring.
- Pages issue #171 was verified and closed after the owner's Unpublish action.
  The [closure receipt](evidence/pages-unpublishing-closure.json) is additive;
  historical deployment and incident evidence have not been erased.
- The [01:07 read-only remote observation](evidence/containment-readback-20261025T010738Z.json)
  confirms disabled Actions, null Pages status, zero GitHub releases, #171 closed
  and unchanged `main`. A later [02:11 readback](evidence/containment-readback-20261025T021153Z.json)
  confirms the same state. Neither enumerates Maven packages or makes a new
  public-site HTTP measurement. No remote mutation was performed.
- Imported Git history, metadata archives, attribution and baseline findings
  remain intact. Existing public packages and `calf-*` project paths are retained
  for compatibility; there is no mass namespace replacement.

## Executed local checks

These are source-bound **dirty-worktree diagnostics at the base commit**, not
immutable release-candidate or hosted-CI results. Repeated cases across runs are
not additional unique tests. Failed and incomplete attempts remain archived.

| Run | Inspected result | Boundary |
|---|---|---|
| [Full JS003](evidence/js-full-003/archive.json) | Exit 0, 70.02 s; **286/286 passed**, all 19 requested modules, 48 fresh XML reports, no skips/errors/missing suites; all 691 helper-selected inputs unchanged | Real Chrome153 browser execution, including common/DOM policies; not physical-camera, native-picker, Apple or production WebView security verification |
| [Cold Wasm tooling001](evidence/wasm-tooling-001/archive.json) | Exit0, 94.94 s; exact root/included-build guard and three root tasks executed; all691 selected inputs and additional tool/script hashes unchanged | **Zero library tests.** Actual Gradle launch log records the expected Node/Yarn executable, fresh task-owned working directory and `--ignore-scripts`, but no frozen-lock flag or script-marker controls |
| [First full Wasm001](evidence/wasm-full-001/archive.json) | **Exit1**, 418.94 s; 211/211 executed cases passed in33 fresh reports, but only14/19 requested modules executed; all691 selected inputs unchanged | IO and WebView production compilation failed. Camera, picker, IO, share and WebView produced **no tests**, not passes or skips. The intended prepared tooling home was not used |
| [Full Wasm002](evidence/wasm-full-002/archive.json) | **Exit1**, 181.03 s; 244/244 executed cases passed in40 fresh reports,16/19 requested modules; all693 selected inputs unchanged | WebView30 (including actual listener detachment) and camera3 ran. Picker/share timer callback compilation failed; IO compiled but its browser bundle could not resolve `skiko.mjs`, so **zero IO testcases** were reported |
| [Full Wasm003](evidence/wasm-full-003/archive.json) | **Exit1**, 65.01 s; 241 executed cases passed in39 fresh XML reports,15/19 requested modules; all693 selected inputs unchanged | IO compilation failed because the enabled Compose compiler could not find Compose runtime on its compile classpath. Camera, IO, picker and share executed **zero cases**. The [diagnostic supplement](evidence/wasm-full-003-io-compiler/failure-review.json) preserves the compiler exception omitted by the general log filter |
| [Full Wasm004](evidence/wasm-full-004/archive.json) and [full JS004](evidence/js-full-004/archive.json) | **290/290 passed per target**, all19 requested modules,48 fresh XML reports per run; exits0,123.02 s /130.03 s respectively;693 unchanged inputs | Actual Chrome browser executions, no skips/errors/missing suites. IO Wasm production compilation was **FROM-CACHE**; linkSync and browser tests ran. Neither a forced-fresh compile claim nor580 distinct test methods |
| [NAV desktop002](evidence/nav-desktop-002/archive.json) | **51/51 passed** | Predates the final two runtime-surrogate **test fixture** edits; not a pass of those later bytes |
| [IO + NAV desktop001](evidence/io-nav-desktop-001/archive.json) | **73/73 passed: IO22 + NAV51**,11 fresh XML; exit0,36.01 s;693 unchanged inputs | Explicit two-module subset under task-owned Xvfb, now including NAV's final runtime-surrogate fixtures. Not the complete desktop library suite |
| [IO Android-host001 preflight](evidence/io-android-host-001-preflight/failure-review.json) | **Exit2**,0.68 s; zero Gradle tasks and zero tests | Runtime capture rejected installed SDK identifier `37.0` before Gradle launch or report quarantine; not the Android-device004 library failure |
| [IO Android-host002](evidence/io-android-host-002/archive.json) | **21/21 passed**,5 fresh XML; exit0,53.01 s;693 unchanged inputs | Explicit IO-only **JVM/Robolectric** subset after the SDK parser correction. No device/emulator or minimum-platform execution |
| [Android device004](evidence/android-device-004/archive.json) | **IO16 passed/1 failed**; picker produced **no XML** before the 840.55 s timeout; bounded command exit143, guard exit1; 691 selected inputs unchanged | API35/x86_64 emulator, software acceleration, SELinux Enforcing. The 25 requested picker cases are neither passed nor counted as skipped |
| [Icon generator repair](evidence/navigation/catalogue-notice-repair/verification.json) | Catalogue9/9; complete development tooling70/70; generator `--check` passed | Python/source-generation checks, **not library runtime tests**; generated Kotlin bytes were not rewritten |
| [Android SDK parser repair](evidence/build/runtime-context-android-api-001/receipt.json) | **19/19 focused offline Python tests passed**, independently repeated | Ten new methods cover valid major/minor identifiers and invalid shapes; the nine existing methods were retained. Not19 Android library tests or38 distinct methods |
| [JVM compatibility diagnostic](evidence/jvm-diagnostic-20261024T224234Z-geo-repair/README.md) | Six reused Java methods/31 assertions passed on the repaired local JARs; original EarthRadius field probe and separate source compile passed | Raw ABI comparator still exits1 with 18 individually reviewed removals; no Maven/KMP/native ABI certification |

The browser launcher explicitly uses `--no-sandbox --disable-dev-shm-usage` for
this root/container test host. Its bytes and context are archived. This is not a
production security-policy change or a claim that the host is sandboxed.

Wasm004, JS004 and IO/NAV desktop001 have the **same693-input snapshot**. Only
`scripts/ci/runtime_context.py` and its test file changed before Android-host002;
its library source bytes still match those browser/desktop runs. Each receipt
records its own before/after maps rather than upgrading earlier evidence to a
later tooling snapshot. Browser004 [Wasm](evidence/wasm-full-004-context/context-review.json)
and [JS](evidence/js-full-004-context/context-review.json) context checks bind all19
fresh generated configs to their selected prepared tooling homes. This is not
whole-dependency-tree or running-process-byte attestation.

Per browser target, the290 cases comprise IO12, picker17, camera3, share17,
WebView30, navigation37, geo38, permissions72 and UI64. UI's native-area49 cases
are common policies, not UIKit execution; stub-target camera/permission checks
are not physical-device functionality. These totals do not establish that every
one of the24 included library projects has an executed runtime suite.

### Defects and fixture problems distinguished

- Navigation's real Float negative-zero serialization defect was repaired.
  JS003 passes the original array case and both new signed-zero regressions.
- Two malformed-UTF16 fixtures now construct code unit55296 at runtime and
  assert length/code before testing rejection. The prior generated fixture
  contained ASCII `?`; the exact compiler/cache stage that changed it is still
  unknown. No production parser validation was weakened. The
  [independent JS003 review](evidence/navigation/full-js-003-verification.json)
  checks both emitted module and Karma bundle as well as the 37 NAV cases.
- The generator omitted modification notices already present in all three
  generated files. A generator/test-only correction preserves the exact notice
  prefix and checks placement/nonduplication. The original failed69-test tooling
  sweep remains historical evidence; the repaired sweep passes70.
- Wasm001 exposed a real shared-web compilation defect: the pinned Wasm DOM
  binding declares `FileReader.error` as `JsAny?`, so its direct Kotlin `.name`
  access cannot compile. The [six-file IO repair](evidence/io/wasm-filereader-error-bridge-review.json)
  adds an internal name-only bridge without changing public APIs, native message
  disclosure or cancellation/cleanup behavior. Its strengthened error regression
  requires the exact error and detached handlers **before** a late abort; the old
  test could have passed through the abort path instead. Two new instance-local
  fixtures cover a native `DOMException` and non-string name. These source-review
  records are not themselves execution evidence. The later paired browser004
  runs now pass all12 IO cases per target, including the strengthened regressions.
- Wasm001 separately rejected anonymous Kotlin implementations of the external
  `EventListener` interface in `WebView.web.kt`. The pinned
  [binding review](evidence/native/wasm-event-listener-bindings.json) also identifies
  the same latent test-side pattern. Listener registration/removal must retain
  **one native callback object**; independent lambda conversions at add/remove
  are not evidence of correct identity or detachment.
- The [seven-file listener repair](evidence/native/first-wasm-listener-repair.json)
  passed all30 WebView Wasm002 cases. The new synchronous real-DOM test observes
  native delivery **before** disposed guards, checks identical callback objects
  on both removals, and has a wrong-object-removal negative control. Normal and
  throwing disposal both run. This proves the tested detach path, not garbage
  collection or native/desktop WebView cleanup.
- Wasm002 then exposed two timer callback type mismatches, plus the same latent
  pattern behind the picker compilation failure. Pinned Wasm browser timers
  require `() -> JsAny?`, while those lambdas returned `Unit`. A final `null`
  preserves side effects, exception propagation and the original delays; the
  [share fixture correction](evidence/native/first-wasm-share-timer-correction.json)
  changes only that discarded callback return. Paired browser004 now passes all17
  share and17 picker cases per target. The new
  [default picker scheduler regression](evidence/io/wasm-default-timeout-adapter-review.json)
  registers64 real timers in two32/33-capacity rounds and manually invokes their
  retained callbacks, with cleanup. It does **not** wait40 seconds or demonstrate
  completion of an actual browser download.
- IO's [preserved Wasm002 bundle failure](evidence/wasm-full-002-io-failure/failure-review.json)
  occurs before any XML-confirmed IO cases: generated code imports missing
  `./skiko.mjs`, then Karma disconnects after30 seconds. The Gradle HTML's one
  skipped aggregate placeholder and “100% successful” display are **not library
  test results**. This is separate from the FileReader bridge and must not be
  hidden by extending timeouts or treating compilation as an IO pass.
- The [IO build correction](evidence/build/io-wasm-skiko-002.json) uses the existing
  official Compose convention to carry required transitive browser resources.
  Wasm003 then failed when Compose compiler transformations were enabled for this
  non-Compose-declaring module. The pinned compiler's public
  `targetKotlinPlatforms.set(emptySet())` DSL scopes those transformations out of
  IO while retaining the plugin and normal resource/check wiring. No dependency
  padding, SDK downgrade, classpath stripping or task/check suppression was used.
  Browser004 verifies actual IO execution after this repair. Resource-publication
  variants are a real build change, not assumed metadata/ABI-neutral.
- Android-host001 exposed a **tooling preflight bug**, separate from library
  behavior: `.isdigit()` rejected the installed SDK's documented major/minor
  `AndroidVersion.ApiLevel=37.0` and accepted some non-ASCII digit forms. The
  [narrow parser repair](evidence/build/runtime-context-android-api-001/receipt.json)
  accepts ASCII integer or single-dot decimal identifiers and retains the exact
  normalized string in runtime receipts/fingerprints. Existing whitespace
  stripping is unchanged; there is no lossy numeric conversion. Pinned SDK/AGP
  readers corroborate the format, and installed SDK files were not edited.
  Android-host002 then passes21 IO JVM/Robolectric cases; it does **not** fix or
  replace Android-device004's failing metadata scenario.
- Android004 fails at `KmpFileDeviceTest.kt:163`: metadata expected size64,
  actual `null`. This is **before** the bounded-read/open-count assertions.
  Provider restarts/null-cursor warnings are observations, not an established
  root cause. Similar projection warnings also occur in passing tests. No source
  or test was weakened in response to this failure.
- The actual Android descriptor positive control and parser control pass, as do
  the recorded real-provider success/error/REG+FIFO cleanup and repeated-operation
  cases. Those passes do not complete the failing metadata scenario or absent
  picker suite. Read the
  [IO review](evidence/io/android-device-fourth-io-review.json).
- Android15 untrusted-app hardlink restrictions also apply to `run-as`; neither
  disabling SELinux nor replacing the hardlink case with a weaker test is an
  accepted verification shortcut. See [device testing](IO-android-device-tests.md).

The task-owned emulator and both supervisors were cleaned up and absence checked.
The emulator returned **-11 after requested SIGTERM teardown**. This abnormal
exit remains in the archived receipt; it is not a passing emulator-shutdown test
or evidence of a library-caused crash. Do not reuse its old PIDs.

### Dependency-verification tooling is not dependency verification

The [fourth isolated Gradle fixture attempt](evidence/build/dependency-fixtures/fixture004/archive-manifest.json)
completed three invocations in26.715s: bootstrap and baseline passed, then the
missing-host-lock case failed its classifier as **unverified**. The remaining
three requested negative cases did not run. The paired witness confirmed three
actual Gradle clients and **zero daemon observations**; its retained data cannot
establish why daemon candidates were rejected. This was not a successful fixture
suite or production dependency acquisition.

The exact observed exception wrapper was `TypedResolveException`, which the
old classifier did not accept. The narrow
[core006 correction](../../scripts/dependencies/checkpoint-offline-006.json)
adds the source-verified, configuration-specific wrapper shape and passes164
offline Python tests. Reclassifying retained004 data with the new parser is
explicitly additive; it does **not** rewrite the original failed result or
substitute for another actual Gradle fixture. Observer diagnostics and ordinary
Yarn lock-closure enforcement remain separately scoped work. The additive
[observer003 review](evidence/review/dependency-observer003-independent.json)
checks108 offline tests plus17 independently modeled scenarios; no observer003
runtime or fixture005 has executed. Neither an offline fixture pass nor the
browser suite establishes independent dependency trust.

The separate cold Wasm-tooling diagnostic now establishes one actual install:
the root-scoped init snippet worked with the convention included build, emitted
three exclusive root receipts and launched Yarn in the expected fresh Kotlin
home. Its output lock is byte-identical to the pinned KGP embedded resource:
489 lexical resolutions,488 integrity lines, with the same no-SRI Karma Git
resolution. This graph is **not** the two-resolution primary Wasm project lock.
The actual argv includes `--ignore-scripts` and omits `--frozen-lockfile`.
No ordinary/warm enforcement, completeness, tamper rejection or independent
provenance is established. The earlier source-only proposal records remain
unchanged; the executed evidence is [additive](evidence/wasm-tooling-001/archive.json).

The subsequent Wasm001 launcher attempted reuse through
`ORG_GRADLE_PROJECT_kotlin.user.home`, but **all14 fresh generated Karma configs**
named the default `/root/.kotlin` tooling tree instead. The
[context supplement](evidence/wasm-full-001-context/context-review.json) preserves
the discrepancy and first collector failure. Five selected manifest/lock/runner/
context files matched the prepared tree; that does not prove the entire installed
graph or running-process bytes. The cause of the mismatch is not established by
those observations. The narrow [CI helper change](evidence/build/ci-kotlin-user-home-001/checkpoint.json)
adds a browser-run-only `--kotlin-user-home` with a single canonical explicit
`-P` argument, strict build-directory confinement and no reset or gate relaxation.
Its62 offline tests passed on [independent repeat](evidence/review/ci-kotlin-user-home-001-lead.json).
Actual use still needs fresh generated-config evidence; argv alone is not proof.

Wasm002 now supplies that [scoped generated-config evidence](evidence/wasm-full-002-context/context-review.json):
all16 reporting modules name the prepared home, and five selected prepared
tooling files are unchanged before/after. The separate IO-failure supplement
also records its fresh prepared-home config, despite no IO testcases. These
observations are not whole-tree or process-byte attestation. A
[current-host controlled transport reproduction](evidence/review/kotlin-user-home-property-transport-001.json)
shows that the dotted environment key survives direct process launch but is
dropped by `/bin/sh` (`dash`), which the hash-identical Gradle wrapper uses.
Pinned Gradle/KGP code accepts the key if it reaches them. The original JVM
environment was not captured, so this explains a reproducible mechanism without
retrospectively claiming a uniquely proven historical cause.

### IO publication metadata: runtime passes do not clear packaging

The IO Compose-resource repair changes plugin wiring and must not be declared
metadata-neutral from browser tests. A bounded offline
[ten-task observation001](evidence/io-metadata-observation-001/archive.json)
first requested POM and Gradle metadata for the root, desktop, Android, JS and
WasmJS publications. The272-entry dry-run passed in42.01s and was reviewed before
execution; no publishing, signing, staging, installation or deployment task was
selected. The actual command **failed in26.01s** at core's
`transformCommonMainDependenciesMetadata`, with45 distinct uncached common
metadata artifacts. Only IO's root POM was freshly generated; the existing
desktop POM was stale, and all five `.module` outputs were absent. A generated
POM's standard “published-with-gradle-metadata” comment is not evidence of either
publication or available Gradle metadata.

A separate explicit [four-target observation002](evidence/io-metadata-observation-002/archive.json)
retained the failed root gate and requested only desktop/Android/JS/WasmJS outputs.
Its189-entry dry-run passed in21.0s, but execution **failed in24.01s** at Android
annotation extraction: `androidLintTool` could not resolve uncached
`com.android.tools.lint:lint-gradle:32.4.0` offline. Desktop's POM and `.module`,
plus Android's POM, were fresh; Android metadata and both browser publications
were not generated in that run. These are missing offline prerequisites, not
demonstrated library implementation defects or successful full-KMP graph checks.

Both runs preserved693 selected input hashes, their complete reviewed dry-run
graphs, exact failure diagnostics and per-output freshness. There was no online
retry, dependency/task exclusion, disabled check or registry operation. No
pre-switch `.module` baseline exists, so these observations cannot establish
unchanged dependency exposure, ABI, payload notices or legal completeness.

The final separate [JS/Wasm-only observation003](evidence/io-metadata-observation-003/archive.json)
**passed in27.01s**, generating all four requested POM/metadata files after a
112-entry,23.0s dry-run. All693 inputs remained unchanged. Each browser metadata
file has API, runtime, sources and resource variants; each resource variant
references a380-byte ZIP. Desktop's metadata has API/runtime/sources variants.
The source-bound coordinates use `io.github.apdelrahman1911.nativecmpkit` and
`0.1.0-SNAPSHOT`; Maven artifact URLs use `nativecmpkit-*`, while local build-file
names retain `calf-*`. None of these generation tasks publishes those coordinates.
Root and Android `.module` files remain unavailable, Apple publication metadata
was not requested, and no strict packaged consumer was executed. The metadata
phase is therefore **partial**, not a complete package graph or release gate.

The additive [bounded payload readback](evidence/build/io-metadata-payload-001/receipt.json)
matches eight local archives to eleven metadata variant references, including
all declared sizes and hashes. The two380-byte resource ZIPs contain only empty
directories, **not Skiko**. Skiko resources occur in the JS KLIB, not the inspected
Wasm KLIB; the successful producer browser-link path cannot substitute for an
external packaged-consumer test. Embedded project notices were compared, but
the separate accompanying notices ZIP was not generated by these task graphs.
This inspection neither clears transitive licensing nor proves a complete
published dependency/resource graph. See the detailed [BUILD record](BUILD.md).

## Outstanding acceptance work

The area ledgers currently contain **89 implemented, 67 partially verified,
8 unresolved, 0 verified** dispositions. “Implemented” does not mean all required
tests passed. All original 530 acceptance requirements remain in the
[status index](status.md); none is waived by a successful unrelated suite.

Prioritize the following before contemplating a preview:

1. **Data and resource safety:** establish the remaining Android metadata failure
   cause; execute the full picker/activity-result/alias matrix without weakening
   real-provider, recreation or hardlink assertions. Verify native parent-window
   acquisition, lifetime and UI-thread guarantees; configuration-handle cleanup
   alone does not resolve [IO-023](IO-parent-windows.md).
2. **Native interoperability:** real Apple/Windows/minimum-platform runs, iOS
   security-scope/provider lifetimes, native permissions/presenters, accessibility
   and popup-dependent WebView flows. An iOS KLIB compile executes zero tests.
3. **Dependency trust:** root/convention Gradle locks and verification, real
   rejection fixtures, ordinary JS/Wasm lock-closure enforcement and separate
   Wasm browser-tooling scope. Raw Yarn accepted missing/incomplete frozen locks;
   successful browser tests are not a dependency-integrity gate.
4. **Distribution and compatibility:** resolve the15 objc2-family license-material
   gaps and separate Apple-SDK ambiguity; assemble all native slots; inspect
   actual Maven payloads/notices and compiler ABI; run independent packaged
   consumers. **Zero of17 strict Maven Kotlin consumer methods have executed.**
5. **CI and publication:** validate immutable candidate bytes across hosts with
   efficient reuse only after the control-policy update permits remote work.
   Current prospective workflows are inert. No preview tag, release or package
   has been published by this phase.

The scoped development documents and evidence are the persistent handoff. Do not
close issues from this report, relabel older failures, infer hosted-CI success,
or enable publication merely because one platform's suite is green.
