# Android device-selection contract: AGP failure and owning CI repair

This is contained verification work, not a library-runtime pass or a release
gate waiver. Public library APIs, platform support, the selected API35/x86_64
image and SELinux Enforcing requirement are unchanged.

## Second hosted failure: report guards pass, zero tests execute

Run [40425272170](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40425272170)
at immutable `9d0d920603d2b56943cdc04aa72faae768ef23d5` compiled the three
library instrumentation APKs, booted its owned emulator and shut it down cleanly
with exit0. All three connected tasks emitted one fresh execution marker and
the repaired, separately checked XML/UTP directory contracts. Nevertheless, AGP
reported `ExecutionException: UnsupportedOperationException` for each task:
**zero tests, zero XML**. The [independent review](evidence/github-actions/40425272170/lead-independent-review.json)
checks exact Git source, ZIP digest, inputs, plan, task markers and controller
teardown. It preserves a failure, not successful native behavior.

That workflow did not request a stack trace. Its precise failure frame therefore
cannot be established from its log. The separate executed reproduction below
establishes an owning defect in the exact selection path we supplied to AGP;
it must not be represented as a recovered hosted stack trace.

## Actual AGP/Gradle reproduction, not a mutable-list guess

The [JDK17 probe and independent review](evidence/android-serial-contract-20261027/lead-review.json)
invoke the actual cached **Gradle9.7.1** and **AGP9.4.0** Java implementations.
Serial-only `IDevice` discovery fixtures feed real `ConnectedDevice` objects;
there is no ADB discovery or instrumentation. Four modeled tooling checks run,
**zero library/device tests**:

1. `DeviceProviderInstrumentTestTask.setSerialOption` adds values to its
   `TestRunnerFactory.getDeviceSerialValues()` `ListProperty`.
2. `getTargetSerials()` returns that property's immutable Guava list unchanged.
3. `getFilteredDevices()` removes a matching serial at
   `DeviceProviderInstrumentTestTask.java:547`, throwing
   `UnsupportedOperationException`. Passing a **mutable** list into the setter
   still produces the same immutable property result and failure.
4. The actual empty-options path preserves the already-selected connected
   provider. The actual mutable direct-method fixture consumes its matching
   serial. Neither check proves real `ANDROID_SERIAL`/ADB selection.

The bytecode also establishes AGP's supported alternative: when target options
are empty, `run()` forwards `ANDROID_SERIAL` to `ConnectedDeviceProvider`, whose
`init()` constructs a private mutable `HashSet` for its filter. This is a separate
implemented selection contract, not a change to the dependency, an arbitrary
device fallback or suppression of the failing task.

Two setup/diagnostic runs remain separate. Probe001 accidentally placed Gradle's
compile-only `lib/api` stubs before executable classes and failed at the property
constructor, executing zero modeled checks. Probe002 corrects that classpath and
executes four checks on the local default JDK21. Probe003 explicitly uses JDK17,
records class origins/dependency hashes and supplies the canonical reproduction.
Do not count these as eight distinct requirements or as dependency authenticity.

## Repair and safeguards

- `scripts/ci/library_tests.py::android_device_environment` validates the exact
  owned emulator serial, creates a child-only environment copy and supplies
  `ANDROID_SERIAL`. A conflicting inherited selector fails **before** report
  quarantine, output creation or process launch. No environment dump is stored.
- `gradle_command` carries the same serial in the internal marker property
  `nativecmpkitAndroidDeviceSerial`, not AGP's serial option. Connected execution
  is sequential and now requests `--stacktrace` for owning failure diagnostics.
- `scripts/ci/fresh-tests.init.gradle.kts` does not call `setSerialOption`.
  Before the task body it checks the environment equals the validated marker,
  both actual AGP target-serial properties are empty, the XML/UTP paths are the
  inspected ones, and ignore-failure/cached-result bypasses remain disabled.
- Receipts record only the validated selection mechanism/serial and re-establish
  actual emulator boot/security identity after execution. The owned controller's
  AVD-name and process-group teardown rules are unchanged.

Five additional Python methods test source guarding, caller-environment isolation,
inherited selector conflicts, pre-quarantine rejection and complete child/receipt
transport. All132 CI tooling methods pass locally. These fixtures model execution
and reports; they do not execute Android or certify native success. The fixed init
script also compiled/configured through actual offline Gradle `help`, exit0,
34.5seconds, zero library tests. That command did not capture prelaunch source
hashes and is not a held-snapshot or release-candidate certification.

The repair still requires a **new immutable hosted Android run** with nonzero
fresh test reports and independently reviewed native failures/teardown. Keep both
zero-test hosted failures, actual model limitations and physical/minimum-platform
gaps. No issue is closed and no package, release or deployment is authorized by
this repair.
