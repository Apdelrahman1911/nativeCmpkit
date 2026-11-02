# Share test-KLIB compile207 — verified narrow acceptance

**PASS:** one fresh `:calf-share:compileTestKotlinIosSimulatorArm64` invocation, bounded compiler exit0 / **32.01s**;
wrapper exit0 / **32.057135869s**. The saved log says `BUILD SUCCESSFUL in 31s`.
The selected task is executed, not `UP-TO-DATE`; 36 actionable tasks comprise eight executed and 28 up-to-date.
Core, IO and Share main compilers remain **UP-TO-DATE**, not new production compiler outcomes.
The offline serial command retained its 8GiB reserve; recorded daemon identity is JDK17.0.20 / Gradle9.7.1.

Both exact **1190 library / 1268 combined** saved input maps hold before/after. Two integrated Kotlin files bind to
qualified private002 postimages, corroborated by a two-leaf readback:

- `NativeShareApplicationHost.kt`: `d3dc78ba45e1047eb7d6a85005dc3a08443ded38432c78d28d5c65e1c85d3a17`
- `ShareTerminalInputObservation.kt`: `39efcc0000efc75448d346a564e3fc80cc681c100763ddfc4fca2e78a173c690`

The other seven proposal paths remain preimages/absent in the saved map; their later integration is separate.
Earlier source339 and accepted NEW8 actual206 are reused, never replayed.

## Retained warnings and limits

- Camera `iosSimulatorArm64Test` is disabled on Linux-x86_64: simulator execution requires macOS.
- WebView `iosArm64` **and** `iosSimulatorArm64` cross-compilation is disabled because `nskeyvalueobserving`
  cinterop cannot be processed on `linux_x64`; required platform-native toolchains are unavailable.
  The separate **Disabled Kotlin/Native Targets** warning lists both targets. None is waived by this Share pass.
- `calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosShareRequestTest.kt:97:65`: **Expression is unused.**
- Type-safe project accessors and the generated Problems report carry incubating notices; that report was not separately reviewed.
- `--no-daemon` still produced a logged single-use Gradle daemon; no daemon-absence claim.

**Zero Apple links/native tests and zero reviewer compiler/test replay.** This is source test-KLIB compiler acceptance only,
not KLIB artifact custody, genuine UIKit callbacks, original Share188 cause resolution, closure or readiness/security/release proof.
All existing gates remain unchanged. The reviewer made no live edits, Git/network calls or original reacquisition.
