# Minimum camera AVD device contract — owning repair

Actual [41076903983](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41076903983)
at `62b632c7` FAILED before any emulator/native method: reporter APK assembly
exit0/281.08s, owned AVD creation exit1/2.0s. The actual command used `Nexus5`;
the SDK returned `Error: No device found matching --device Nexus5.` This is the
owning cause of **this** setup failure, not proof of the earlier serial refusals.

Official installed SDK23 `avdmanager list device` independently reports
`id: 19 or "Nexus 5"`, name `Nexus 5`, OEM Google, with no `Nexus5` identifier.
Two new focused synthetic regressions fail before the repair. The repair selects
the exact official ID and, only for the finite camera contract, creates the owned
private AVD before costly APK compilation. Invalid AVD setup cannot start compile,
receiver installation, emulator or native suite. Other profiles keep their setup
order. **54/54 focused controller/camera methods pass**, including both repaired
reds; actual SDK discovery is not an AVD/native execution.

Only controller/two new tooling tests change. Camera production, native fixture,
APK/compiler/dependency bytes remain unchanged; accepted API35 four-method,
host22 and actual APK compile results are reused, not repeated. API23 still needs
four actual methods on a fresh enforcing owned AVD. #78 remains open; no packages,
release, Pages/main/history or independent readiness/security gate changes.
