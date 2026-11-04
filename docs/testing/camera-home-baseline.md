# Camera HOME-baseline regression and native acceptance

The [556–559 evidence](../development/evidence/current-platform-recovery-20261101/camera-home-baseline556-559/README.md)
qualifies a test-only preserved FallbackHome baseline. It is not a public camera
API change, owned task, installed-image attestation or Android native pass.

## Source and execution flow

1. The controller owns one fresh API35/x86_64 AVD/transport and observes the actual
   shell UID/boot/master/native/scalar/Settings-activity absence.
2. `android_camera_home_baseline.py` admits complete empty framing or exactly one
   fully parsed thirteen-row nonowned HOME record. Completed command exit,
   stderr and byte bounds are checked before parsing.
3. Two complete equal snapshots capture the original HOME baseline along with
   original master/scalar/native/epoch. Rank and elapsed inactivity may progress;
   object/leaf/root identity, original activity clock and all other bytes cannot.
4. Read-only precompile capture and postcompile revalidation preserve that same
   original. Every later allowed mutating IPC rechecks HOME and brackets its
   query with the expected kernel identity; there is no action-boundary shortcut.
5. `OwnedDeveloperSettingsUi` independently proves the installed platform
   Settings/FallbackHome components, captures only a prelaunch nonowned baseline,
   and creates its own shell-caller/nonce/component-bound **standard** Settings
   task. It revalidates the HOME baseline before preference actions and removal.
   Both owned IDs must exclude both preserved IDs; baseline records are never
   handed to the removal path. The live-task reader remains strict.
6. Only the existing latched normal-reboot cleanup can accept a new epoch with
   two equal complete snapshots. It stores the new epoch and HOME baseline
   together, restores only the original master presence/value, and requires
   exact native/scalar restoration. No other epoch substitution is permitted.

## Important library-level tests

| Test population | Scope |
|---|---|
| `SettingsHomeTaskBaselineTest`8 | Genuine Kotlin common library JVM regressions; exact fields/ordering/overflow/clock/policy/immutability and redacted formatting |
| `CompleteHomeParserTests`9 | Actual Python parser, no Android IO; malformed/live/foreign/unknown/unsafe and complete envelope checks |
| `PreservedHomeControllerTests`6 | Real controller snapshot methods on explicit inert device fixtures; same-epoch stability/drift/refusal and native-source wiring |
| `HomeEpochAndActionBoundaryTests`7 | Actual controller cleanup/new-epoch and action-guard methods on inert models; two-snapshot drift, every existing mutation, query failure and kernel bracketing |
| `HomeBaselineHistoryTests`8 | Exact before/after/round-trip/current-vs-ancestor fixture histories, retained old pins and source actions; **not new native behavior** |

Models never create an emulator, access Android UI, grant URIs, capture camera
data or replace native JUnit results. Existing sample applications are not used.

For a **changed relevant input** needing verification, the common regression is:

```sh
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew \
  :calf-camera-picker:desktopTest \
  --tests com.mohamedrejeb.calf.camerapicker.SettingsHomeTaskBaselineTest \
  --offline --max-workers=2 --no-configuration-cache \
  -Pkotlin.compiler.execution.strategy=in-process
```

Select only new/affected Python methods with `PYTHONPATH=scripts/ci python3 -B -m
unittest <module.Class.method> ...`. Do not blindly run every accepted class.
Source/model receipts must record exact selections, input hashes, failure/error
records **and distinct failed methods**, duration and zero native executions.
Subtest failure records are not additional executed methods. Preserve red
results and rerun only failed/meaningfully affected selections.

A changed Android caller needs one serial bounded
`:calf-camera-picker:assembleAndroidDeviceTest`, retaining8 GiB free disk. Require
the actual task/compiler exit, exact held sources and fresh APK identity. APK
compilation/signing is not a device test or distributable publication. Reuse
accepted common/XML/compiler results only on unchanged applicable inputs; never
restore old XML as fresh execution.

## Missing native gate

Use only the reviewed `android-camera-real-restoration-dont-keep` API35 focus
after an immutable development freeze and fresh max2 combined hosted-capacity
readback. It must actually run
`AndroidCameraRestorationTest.nativeDontKeepActivitiesRestoresOneReadableCapturedFile`,
with the real public launcher/ActivityResultRegistry, OS destruction/rebuilt
owner, exactly one readable result, grants/descriptors, sibling preservation,
native/scalar/master restoration and owned app/emulator/AVD/transport disposal.
Do not replay accepted camera009 rotation/process-death/cancellation cases.

If a new HOME shape/state/ownership/refusal is observed, retain it and qualify
the complete actual grammar/identity before changing admission. No purging,
unknown-row ignoring, force-stop, guessed namespace/root IDs, fake registry
result, manual URI grant, timeout waiver or unchanged retry is permitted.
Installed-image provenance, actual native memory/resource behavior, physical
camera/vendor/API compatibility, consumer/API–ABI and release/security checks
remain independent. #13 closes only after all original criteria pass and their
actual source/results/cleanup are reviewed.
