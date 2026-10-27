# Genuine UIKit application-host investigation

**State: not yet implemented or verified.** This is contained single-agent
verification work. Nothing here certifies native UI behavior, closes a finding
or permits publication. Preserve the prior failing iPhone run and existing tests.

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
   explicit failure exits, complete intended discovery and no unexpected skips.
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
