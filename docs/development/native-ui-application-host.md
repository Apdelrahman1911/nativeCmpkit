# Genuine UIKit application-host investigation

Latest additive state: [40480810709's actual Alert delegate crash](checkpoint-consumer-metadata-alert-20261027.md#actual-uikit-delegate-crash)
replaces the earlier running observation. Real Worker activation and plist hash/
Boolean repair succeed;82 executions retain81pass/1fail,15 XML, zero skips.
Production modifies UIKit's Alert delegate and crashes; ten of11 required
methods remain absent. The supported popover-only repair requires12 methods
and has a fresh KLIB/model compile, **not native runtime verification**. All
earlier failures below remain; no issue/native/consumer/release gate is closed.

**Current state (2026-10-27): run40468870504 atb5a4508a genuinely activates main
Worker1/owned Worker2 and executes82 (81pass/1fail),15 XML, zero skips. The first
mandatory native alert aborts at Compose's strict plist check; ten of11 mandatory
application methods are absent. Link/sign/install/owned cleanup pass, but
transport and suite fail. The generated manifest now serializes the real required
Boolean;32 Python guards pass, zero Apple executions verify that correction.
A new immutable `ios-ui` run is required. The earlier startup/identity failures
below remain historical evidence, not claims that no Apple methods ever ran.**
This is contained single-agent verification work. Nothing here certifies native
UI behavior, closes a finding or permits publication. Earlier investigation
sections retain the state of their particular diagnostics, not today's integration.
Preserve the prior failing iPhone run and existing native assertions.

## Actual Worker execution, strict plist failure and owning manifest repair

[Run40468870504](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40468870504)
at immutable `b5a4508a8d28f9937c456db2895b4ae09c4a9343` passes tooling, then
fails Gradle1/1755.81s on macOS26/Arm64/iOS26.5 simulator. [Independent review](evidence/github-actions/40468870504/lead-independent-review.json)
reconstructs all712 inputs from Git, verifies the94111-byte artifact digest,
recounts82 actual outcomes (81pass/1fail/0skip) in15 reports, and inspects real
activation/transport/cleanup. The81 passes are not81 new application scenarios.

`presentedAlertUsesLatestActionAndTextFieldCallbacks` is the only observed one
of11 mandatory application methods, and fails. Compose asynchronously aborts at
`PlistSanityCheck` because the generated `Info.plist` omits Boolean
`CADisableMinimumFrameDurationOnPhone=true`. Genuine Worker activation no longer
fails startup ownership, but incomplete transport cannot certify the host or
presenters. Signing/install/installed bytes and exact owned stop/uninstall/
absence/local-bundle cleanup pass separately. Original missing/failed XML and
two reviewer-precondition errors are preserved; class-name prefixes and absent
startup observations are interpreted against exact KGP/source contracts.

The minimal repair belongs in `scripts/ci/ios_ui_application.py`: write a real
plist Boolean, not a string or a sanity-check-disable option. [32-method red and
32/32 green](evidence/uikit-plist-20261027/green.json) include serialized
type/value and genuine-host no-disable guards. These are Python tooling only,
**zero Apple executions for the repair**. Eleven native methods, strict ownership,
fresh XML/protocol agreement, bounds and cleanup remain mandatory. See [the
contained checkpoint](checkpoint-consumer-uikit-20261027.md); do not close native
issues or recount existing passes as new repaired application acceptance.

## Exact native object identity after the persistent startup timeout

The [first attempt](evidence/github-actions/40460102044/attempt-1/lead-independent-review.json)
at immutable `cebdc8f206a5e34b39e1cb8053b380ba509707c2` fails before Gradle/tests:
the hosted simulator reports **Data Migration Failed**, followed by a60s
`simctl list devices --json` timeout. Zero testcase/XML or app execution.
The failed job alone is rerun at the same SHA; successful tooling retains its
original timestamps and is reused, not freshly recounted.

[Attempt2](evidence/github-actions/40460102044/attempt-2/lead-independent-review.json)
verifies the74,788-byte artifact,711 immutable selected inputs, native link/sign/
install and exact owned cleanup. The737.94s Gradle execution exits1. Startup
records `active=true`, `key=true`, `hidden=false`, `root_attached=false`,
`root_native_equal=true`, `worker_started=false`; there are **zero activation,
testcase or XML results**. At this SHA `root_attached` means Kotlin wrapper
`===`, not pointer equality. Preserve that interpretation in old receipts.
Value equality is not an ownership proof and is not silently accepted.

### Owning test-host repair and adversarial requirements

- New internal `NativeObjectIdentity.kt` uses the configured public
  `kotlinx.cinterop.Any?.objcPtr(): NativePtr`. Both retained
  `platform.darwin.NSObject` references must be nonnull and their pointers equal.
  No stored/exported addresses, native value-equality fallback or production API
  change. Every attachment/root/idle/foreign-root-cleanup check uses it.
- Active/key/visible requirements, main-thread affinity,10s startup deadline,
  exactly-once worker admission, native assertion/transport agreement and exact
  owned cleanup remain. `rootNativeEqual` is diagnostic only. New receipts must
  be interpreted against their source SHA; old wrapper predicates stay historical.
- The new required `nativeObjectIdentityRejectsNullAndEqualButDistinctObjects`
  method creates two actual NSMutableData allocations with equal native data,
  requires native content equality, rejects distinct pointers and every null
  ownership case, then checks the real UIWindow root getter. It is not a mock.
  It has **not executed on Apple yet**. Seven presenter plus four host methods
  and all three host/helper files are mandatory; missing identity tests fail
  receipt/XML validation even when other protocol fields agree.

### Executed red/green evidence and limits

[Independent source/ZIP/compile review](evidence/uikit-native-object-identity-20261027/lead-independent-review.json)
preserves the9-method source-guard red (4failures/1error), first225-method full
CI run (3failures/4errors from outdated synthetic inventories), subsequent226
passes, and the first actual KLIB compile failure. That Gradle compile exits1/
39.68s with712 held/copied inputs: unavailable `Foundation.NSObject` and
`NSMutableString` imports. Its old driver exits0 despite recording Gradle1;
the driver's exit is **not success evidence**.

Configured platform metadata supports `darwin.NSObject`, NSMutableData and its
`dataWithLength`/`isEqualToData` APIs. Corrected imports retain the adversarial
test. A new source-held compile exits0/37.01s; full
`:calf-ui:compileTestKotlinIosSimulatorArm64` executes freshly, while unchanged
production compilation caches are reused. Its actual root KGP application model
also passes. All712 selected inputs and copied inputs match before/after;
produced KLIB component hashes are rechecked in owned tmpfs, not distributed.
The corrected full Python CI suite separately passes226/226 at the same selected
input digest. Earlier226 passes overlap, not additional unique methods.

The66-member lossless archive keeps failed source reconstructed against its
exact precompile hashes, original logs/maps, corrected source and driver, API
observations and the fresh results. These are **zero Apple/native/library/device/
packaged-consumer testcase executions**. New immutable `ios-ui` execution must
prove real pointer/ownership/presenter behavior. Device/iPad/minimum-platform,
VoiceOver, ABI, dependency/legal/consumer and release gates remain open.

## Actual activation attachment failure and bounded startup repair

[Run40453956549 attempt1](evidence/github-actions/40453956549/lead-independent-review.json)
fails at pinned Rust installation because hosted-runner DNS cannot resolve the
registry. Zero library/artifact/native results are produced. Only its failed job
is rerun; tooling is reused at the same immutablebe32a7d6 revision.

[Attempt2 independent Git/ZIP/runtime review](evidence/github-actions/40453956549/attempt-2/lead-independent-review.json)
verifies the74,632-byte artifact and710 selected immutable inputs. Real Mach-O
link/sign/install/byte-readback and exact owned app stop/uninstall/absence/local
cleanup succeed. The actual job now reaches the exported Objective-C delegate's
`applicationDidBecomeActive`, where synchronous `requireOwnedApplicationWindow`
throws `The root must be attached to the owned UIWindow`. There are **zero
activation/TeamCity frames, testcases or XML**. This is not an initializer rerun
failure or a demonstrated production presenter bug; both earlier failures remain.

The test host incorrectly assumed that active means immediately attached. Exact
attachment timing versus Objective-C wrapper identity is not yet distinguished.
The owning repair schedules one main-loop timer and waits for actual active/key/
visible/root referential-identity predicates before starting one owned Worker.
Repeated activation does not restart admission or extend the10s startup deadline.
It does not sleep to infer readiness, attach a foreign root, change `===` to `==`
for acceptance, relax assertions or synthesize XML. Timeout emits only bounded
actual predicate booleans (including both identity comparisons), releases main
leases and fails. Normal completion still settles Worker termination first.

[Source-held regression/compile review](evidence/uikit-startup-readiness-20261027/lead-review.json)
preserves five Python source-guard failures and five passes after the repair.
Full-test KLIB lowering and real root KGP model pass0/46.53s with711 selected
inputs held and copied bytes equal. Unchanged production compilation is reused;
178 KLIB component hashes/5,207,543bytes are checked in owned tmpfs, not distributed.
These are **zero Apple/native/library/consumer executions**. All seven presenter
and three genuine-host methods remain unchanged/mandatory. Run new immutable
`ios-ui`; inspect its actual native failures before any further repair or closure.

The [additive timeout-observation pair](evidence/uikit-startup-observation-20261027/lead-review.json)
repairs a separate transport-evidence loss: an unknown lifecycle marker was
rejected before forwarding, discarding its useful predicate observations. Only
the exact pre-worker startup-timeout grammar now retains six structured booleans;
malformed/extra/late fields are never archived. Retaining it permanently fails
transport, runs owned cleanup and rejects any parent receipt claiming success
with that field. It is not a success frame or replacement XML. Red64 methods
has three failing methods/five failure events; green64/64, including the same
five source guards. Four Python inputs changed after the KLIB run; its Kotlin/
build inputs remain byte-identical and are reused only for compilation scope.
No actual native timeout booleans or Apple execution are claimed yet.

## Actual delegate initialization failure and owning repair

[Immutable run40449374922](evidence/github-actions/40449374922/lead-independent-review.json)
at `9f05d162eb784b28e441498d81b35955ea65e8e4` failed after the real
`applicationDebugTest` executable linked. The Arm64 Mach-O identifies simulator
platform7/minimum15.0.0; local ad-hoc signing, absent-app preflight, installed
binary/plist readback and exact owned stop/uninstall/absence/local cleanup pass.
Those are setup/ownership observations, **zero library/native testcase passes**.

The real job console reports:
`init is not implemented in NativecmpkitUIKitLibraryTestDelegate`.
`UIApplicationMain` allocates/initializes the named exported class through
Objective-C. An ordinary Kotlin primary constructor does not override/export
the inherited Objective-C `init`. No active-application/Worker/TeamCity frames or
KGP XML were observed. The nested original transport receipt and final failed
parent gate remain preserved; two identical crash diagnostics do not establish
a wrapper retry or a production-library defect.

The [source-held full-test compilation](evidence/uikit-objc-initializer-compile-20261027/lead-review.json)
uses the actual `ObjCObjectBase.OverrideInit` secondary constructor. The generated
body fixture additionally asserts that `UIApplication.sharedApplication.delegate`
is the exported Kotlin delegate, rather than bypassing native construction with
a programmatically supplied delegate. Root KGP model and complete
`:calf-ui:compileTestKotlinIosSimulatorArm64` pass0/37.01s with710 inputs held and
rechecked. **Zero Apple/runtime methods execute in this Linux KLIB compile.**

The bounded diagnostic collector now retains only explicit Objective-C exception
headers; it still excludes adjacent app output/stack/transcripts and applies the
same credential and byte limits. Python regressions preserve17/2fail red and
17/17 green (15 methods overlap earlier tooling). No assertion was weakened,
test skipped, XML fabricated or native success inferred. Both failed affected
profiles need a new immutable run; physical-device/presentation/legal/dependency/
ABI/consumer and release gates remain open.

## Why a main-thread Skiko scene is not sufficient

The exact Compose1.12.0 v2 `runComposeUiTest` implementation uses Skiko
`CanvasLayersComposeScene`. It does not create a `UIApplication`, key
`UIWindow` or `ComposeUIViewController` hierarchy. UIKit objects and a successful
`NSThread.isMainThread` assertion alone do not establish an attached native
presenter. The comment in `calf-ui/.../internal/NativeUiTest.kt` now states this
boundary instead of incorrectly claiming a UI-test application.

Actual KGP2.4.20 bytecode inspection shows `KotlinNativeSimulatorTest` launches
`/usr/bin/xcrun simctl spawn`. Its `standalone` toggle adds `--standalone`, not an
application bundle or app-launch lifecycle. The exposed `TestExecutable` and
`AbstractExecutable` model has no `entryPoint` accessor. A host must deliberately
configure a custom compiler entry and launch a real simulator application while
retaining the generated Kotlin test registry and trustworthy results.

Seven presentation fixtures currently require that real hierarchy: three alert,
one dropdown, one time-picker and two sheet tests. Do not skip them or replace
native assertions with a Skiko-only success to make CI green. Other fixtures may
still have independent production/fixture defects; a hosting repair does not
automatically resolve the prior16 failures.

## Actual custom-entry diagnostic and exact limitations

The [preserved probe and independent review](evidence/native-entry-contract-20261027/lead-independent-review.json)
actually compile/run Linux Kotlin/Native2.4.20, not mocks or an Apple linker:

- Explicit `-entry nativecmpkit.probe.customMain` works with `-tr`, `-trn` and
  `-trw`. All three produce the same1,902,800-byte executable with SHA256
  `23dd42c2f565a5a29e5d004e7004db21bb7689a6d08a9b34bdff834901911662`.
- The actual generated suite registers on main and an owned Worker. Each mode
  runs the same two generated methods through `testLauncherEntryPoint`, exit0:
  **six repeated fixture executions / two methods / zero library or iOS tests**.
- All bodies ran on mainWorker1. Worker **registration**, not execution or
  failure propagation, is observed. `-nomain` interactions remain unverified.
- JDK17 was explicitly selected in the child environment, but the attached
  compiler JVM identity was not independently observed. Tool/dependency hashes
  are provenance observations, not independently certified trust.
- Probe001 failed its disk reserve while acquiring absent LLVM21 and then hit
  a secondary missing-log driver error; no methods ran. Preserve that failure.
  Probe002 isolated its native dependency store, outputs and linker temporaries
  in owned tmpfs and cleaned those owned files; no preexisting caches were deleted.

The [owned partial-download isolation](evidence/owned-probe-download-isolation-20261027-001.json)
retains the hash-verified newly created partial separately to protect the8GiB
disk reserve. It is not a completed download, dependency approval or native test.

## Required host contract before claiming success

1. Compile a real UIKit application executable with the generated suites and an
   explicit tested entry. Use a test-only delegate; retain current public APIs,
   native/framework names, copyright and compiler/plugin versions.
2. Run `UIApplicationMain` on the process main thread; create and retain a real
   key window/root `ComposeUIViewController` attached to that application's
   hierarchy. Assert application state, main-thread ownership and native-parent
   attachment before testing presentation, not just object construction.
3. Keep the UIKit event loop live while generated tests run on an owned Worker.
   Prove actual worker method execution, exactly-once completion, failure and
   timeout propagation, and teardown. Native operations remain main-thread-bound.
   A worker registry listing is not evidence that bodies ran there.
4. Build/install/launch only the owned application on the exact selected booted
   Arm64 simulator. Observe its process/result state, not only `simctl launch`
   acceptance. Do not use a sample app, guess another device or fabricate XML.
5. Preserve actual TeamCity/JUnit testcase outcomes through KGP's real parser or
   an equivalently verified integration. Assert unique fresh nonzero methods,
   failed task/JUnit propagation, complete intended discovery and no unexpected skips.
   App crashes/timeout/zero reports must fail the job, not become successful tests.
6. Clean up only the owned application/process/window/Worker and observer leases;
   collect bounded failure evidence. Execute fixture red/green plus the unchanged
   native assertions. Record immutable source/SDK/runtime and output hashes.

KGP's `KotlinNativeHostTest` with an owned app-launch wrapper may allow reuse of
its actual TeamCity/JUnit parser; it remains a candidate integration, **not an
implemented or tested solution**. Genuine simulator/physical-device,
VoiceOver/minimum-iOS, native-parent lifecycle and full-suite gates remain open.

## Subsequent owned-worker and UIKit binding diagnostics

The [worker probe003 review](evidence/native-worker-entry-contract-20261027-003/lead-independent-review.json)
now proves bodies, not just registration, run on owned Worker2 while main is
Worker1 using the actual Linux Kotlin/Native2.4.20 compiler and explicitly
verified JDK17 executable. The positive run passes2 methods, exit0; the negative
control passes1 and deliberately fails1, exit1. Worker termination completes
**before both process exits**. This is four repeated fixture executions/two
methods, **zero library/iOS executions**; native TeamCity frames were inspected,
not yet passed through KGP's actual JUnit parser. Calling `exitProcess` inside a
`try` does not unwind `finally`; an application host must settle teardown first.

The [UIKit binding pair](evidence/uikit-application-bindings-20261027/lead-independent-review.json)
preserves a failed actual iOS-simulator KLIB lowering on Linux: internal
`getObjCClass` access, the enum import and an invalid override of the final
delegate `window` property. The corrected diagnostic uses an explicit
`@ExportObjCClass` runtime name, public `NSClassFromString`/`NSStringFromClass`,
the actual enum import and an owned private window. KLIB lowering passes,
exit0/6s/17,889 recorded output bytes. The owned output was cleaned after hashing;
its digest is an execution observation, not retained independently checked bytes.

**No Apple linking, application install/launch, UIKit lifecycle, KGP parser or
library-native test passed in these diagnostics.** The host is still unintegrated.
Do not replace the seven presenter assertions with a lower-level compile/Skiko
pass, nor infer that the other prior failures have been fixed.

See [UIKit implementation record](UI-native.md),
[immutable CI failures](checkpoint-ci-20261026.md) and
[release gates](release-readiness.md).

## Subsequent actual KGP/JUnit Linux proof

The [actual parser diagnostic](evidence/kgp-native-worker-parser-20261027/lead-independent-review.json)
now feeds the generated owned-worker suite through KGP2.4.20's real
`KotlinNativeHostTest`: positive2pass/Gradle exit0 and intentional-negative
1pass/1fail/Gradle exit1, two fresh XML reports. Worker2 bodies/termination are
observed before both process exits. Four repeated diagnostic executions/two
methods are **zero library/iOS tests**. Failed setup001/002 and the first failed
review are retained; the successful same-source binary from002 was reused, no
cached XML.

Actual KGP bytecode and runtime output show `--ktest_no_exit_code` is intentional:
native result0 in both runs does not suppress the failed testcase or failed Gradle
task. A future app wrapper must propagate crashes/timeouts/transport errors while
preserving that protocol; do not infer success from its completion marker or
incorrectly require native result1 under KGP. This settles only the Linux parser/
worker contract. **Genuine UIKit host is still unimplemented/unverified.**

## Unintegrated application model and byte-identical helper

The [actual KGP model](evidence/native-application-kgp-model-20261027-001/lead-review.json)
accepts a separate `applicationDebugTest` sharing the existing test compilation,
with explicit `-entry`, a `KotlinNativeHostTest` wrapper and distinct report
directories; default `debugTest` arguments remain unchanged. Model configuration
is not final compiler/linker verification, bundling or native execution.

The test-only `NativeUiApplicationHost.kt` candidate now implements an explicit
delegate/`UIApplicationMain`, owned key window, live main event loop, generated
test Worker, staged composition/presenter cleanup and termination-before-exit
markers. Its [byte-identical isolated helper diagnostic](evidence/native-application-helper-klib-20261027-001/lead-independent-review.json)
typechecks with actual Kotlin2.4.20/Compose1.12.0 UI/runtime and compiler plugin:
Linux iOS-simulator KLIB compile exits0/38.01s,705 selected inputs held unchanged.
Nineteen output component hashes were observed, but those owned output bytes were
discarded after hashing and cannot be independently rehashed. Probe/source/log
bytes are retained. **Zero library/native/iOS methods execute.**

It remains **unintegrated and unverified**: no Apple link, `.app` install/launch,
conversion of the seven presenter fixtures, application-backed task/report wiring
or genuine lifecycle success is implied. Polling sleep is backoff, not idle proof;
the helper requires actual attached root, committed SideEffect generation and
no pending Recomposer work. Worker/parser and UI ownership contracts still need
immutable simulator execution; do not relax native assertions to manufacture it.

## Integrated application task and evidence agreement — 2026-10-27

The current implementation follows [ADR 0006](../decisions/0006-owned-uikit-test-application.md):

- `calf-ui/build.gradle.kts` adds **only** `applicationDebugTest` and
  `iosSimulatorArm64ApplicationTest`, sharing the existing generated test
  compilation. Default/public binaries and entry arguments remain unchanged.
  The seven presenter methods now use `runApplicationUiTest`; their native
  assertions are retained. Three additive `NativeUiApplicationHostTest` methods
  require actual active UIApplication/Worker/window/composition ownership,
  repeated recomposition/disposal and primary-failure/presenter cleanup.
- `scripts/ci/ios_ui_application.py` requires actual Darwin/Arm64, the explicitly
  selected booted UDID, the distinct linked `.kexe` and an Arm64 simulator
  Mach-O `LC_BUILD_VERSION`. It creates a fresh source/session-bound disposable
  `.app`, signs it ad hoc, verifies absence before install and installed binary/
  plist hashes, forwards actual console TeamCity frames **verbatim** to KGP,
  checks unique main/owned Worker activation and termination-before-exit, and
  revalidates the owned installation before stop/uninstall/absence/local cleanup.
  No sample, fabricated XML, arbitrary test filters or distributable upload.
- `library_tests.py` passes the receipt root only to the child under that fresh
  suite output. Conflicting inherited selectors fail before quarantine/execution.
  It requires exactly one fresh bounded non-linked receipt; source/SDK/runtime,
  binary/header, bundle/session, install/cleanup and complete testcase identities/
  outcomes must agree with **actual KGP XML**. Only the observed exact
  `iosSimulatorArm64ApplicationTest.` prefix and `[iosSimulatorArm64]` suffix
  are normalized. All seven presenter and three host methods are mandatory once.
  Matching failed cases still fail the parent JUnit gate under runner-exit-zero;
  receipt cases are never added to counts or used as substitute XML.
- The existing read-only workflow uploads only the nested JSON receipt and selected
  XML, never `.app`, `.kexe`, packages or complete console output. Control diagnostics
  retain bounded structured domain/code identities, not transcripts. Missing-app
  (`NSPOSIX`2) and already-stopped (`NSPOSIX`3) assumptions fail closed if the
  real selected simulator exposes another result; inspect evidence before repair.

### Executed evidence, not native success

The [initial tooling archive](evidence/ios-application-initial-tooling-20261027/lead-independent-review.json)
preserves the five-method planner red (2pass/3failed methods, four subtest failures),
initial23-method Python fixture failure (3failure/10error events), and corrected
24/24 transport tooling. These were archived only after later Kotlin/planner
edits: each old input is reconstructed/hash-checked using immutable Git and retained
added source bytes, **not** claimed unchanged in the current checkout across that
older execution and archive.

The [receipt red/green](evidence/ios-application-receipt-contract-20261027/lead-independent-review.json)
preserves21 methods: red has44 error/subtest events from absent agreement/environment
wiring; green21/21. The [control/shape pair](evidence/ios-application-control-contract-20261027/lead-independent-review.json)
preserves unknown-terminate silent success and malformed/schema/boolean receipt
acceptance before their owning repair. Final transport27/27, receipts23/23,
plan5/5 and workflow8/8 pass. These63 methods overlap earlier runs; two pipe
methods launch actual Python children with **simulated** native frames. All are
**zero Apple/library/device/packaged-consumer executions**.

The [actual root compile](evidence/uikit-application-root-compile-20261027/lead-independent-review.json)
preserves failed001 (probe init accidentally queried the included convention build,
exit1/13.01s, no UI compile). Guarded002 actually inspects KGP and compiles full
UI production/test iOS-simulator KLIBs, exit0/67.51s. All710 selected source/build
inputs are held and rechecked before archive. The178 output-component hashes
(5,203,601bytes) were independently rechecked in owned tmpfs; output bytes are not
distributed or retained in documentation. The same source freeze separately
compiles the Android fixture, exit0/30.01s. Neither command executes library tests.

**Still required:** actual Apple linker/`-nomain` behavior, real Mach-O app,
install/launch/console transport, UIKit and remaining Skiko fixture interaction,
native success/failure/lifecycle outcomes, full iPhone/iPad/minimum-platform and
physical-device/VoiceOver verification. A new immutable `ios-ui` run is required.
The integration and Python/compile passes clear no issue or release/security gate.

[Source-held preflight008](evidence/ci-preflight-20261027-008/lead-review.json)
passes21 bounded commands/890 Python tooling methods, including the same210 CI
methods, strict MkDocs and actionlint. Five actual generated HTML/anchor targets
are independently inspected. All14,516 captured inputs are held and rechecked
before archive. This evidence/link follows that freeze; it is not circular
certification of a later commit. **Zero library/native/device/consumer methods**
execute; immutable Android/application CI still needs its own reviewed outcomes.
