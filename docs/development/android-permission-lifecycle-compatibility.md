# Android permission lifecycle and compatibility verification

Status2026-11-04: source integrated and focused controls accepted; **no new device
or compiler acceptance**. #19 and #107 remain open. Evidence and exact commands:
[718–725](evidence/current-platform-recovery-20261101/android-permission-lifecycle718-725/README.md).

## Architecture and execution flow

The API35 tests live in
`calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/`:

- `AndroidPermissionLifecycleDeviceTest.kt`: three finite public/native scenarios.
- `OwnedPermissionLifecycle.kt`: owned Binder connection, signature/UID/PID/nonce/
  generation validation, bounded replies and same-process continuity assertions.
- `PermissionLifecycleSystemUi.kt`: refreshed, uniquely admitted real dialog/
  Settings accessibility queries; no guessed resource or forced input fallback.

`tests/consumer/android-permission-lifecycle/` is a separate debug source fixture,
not an existing sample app and not a packaged-consumer certificate. Its Activity
holds the actual public Compose permission states/batches, records framework
`onRequestPermissionsResult` arrays before forwarding to `super`, and exposes
observations through a signature-protected service. `dispose-content` removes the
actual composition; retained state references allow checking that disposed
observers do not refresh or manufacture callbacks. No synthetic ON_RESUME or
automatic runtime grant is accepted.

Controller `scripts/ci/android_permission_lifecycle.py` derives from the existing
owned-recipient protocol. Preparation validates the source contract, exact API35
SDK inspectors, initial package absence, separate fixture assembly, output metadata,
compiled manifest and actual private debug signing certificate. It then installs
only the owned APK and verifies installed byte identity, including uncertain
installer outcomes. The result is a **preparation receipt**, never test success.
`android_permission_lifecycle_contract.py` supplies bounded manifest/XML, metadata,
request and receipt checks; encoded DTDs and mixed/unknown shapes refuse.

Native tests additionally require the real public states, actual permission-manager
arrays, controlled genuine OS UI and same Activity/service/PID/UID/Binder ownership.
App recreation, a killed process, skipped method, stale XML or successful assembly
alone cannot satisfy a scenario. Cleanup retains primary errors and separately
checks owned app/AVD removal and accessibility restoration.

## Registered API35 routes

| Focus | Exact library method |
| --- | --- |
| `android-permission-location-api35` |`api35ApproximateFineRequestAndForegroundBackgroundBatchUseRealDialogs`|
| `android-permission-lifecycle-grant-api35` |`settingsGrantRepeatedResumeAndDisposedBatchKeepTheSameNativeProcess`|
| `android-permission-lifecycle-revoke-api35` |`notificationSettingsRevocationRefreshesSingleAndBatchWithoutProcessDeath`|

The owning source is
`calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionLifecycleDeviceTest.kt`.
`library_tests.py`, `android_device_tests.py`, `workflow_matrix.py`, storage-probe
admission and `gradle.yml` route only these declared methods. The dated native plan
is archived under `original18/NATIVE-VERIFICATION-PLAN.json`. Its commands are
future execution plans, not completed runs. Dispatch only after current-source/
compiler/runtime/capacity prerequisites and exact immutable selection qualify.

## Compatibility source fixture: broader cases not yet registered

`tests/consumer/android-permission-compatibility/` separates helper and reporter
Gradle projects. Helper manifests define only the selected permission role
(camera, coarse, fine, pair, batch or deliberately omitted); the reporter has six
signature-protected controls and exact helper/system visibility. The native source
has five methods for14 SDK/target profiles. Plan/manifest policy is centralized in
`scripts/ci/android_permission_compatibility_plan.py`; boolean/unknown SDKs,
mismatched actual API/target, extra grants/caps/components and mixed compiled
manifest shapes fail closed.

`test_android_permission_compatibility_source.py` supplies19 focused source controls
including actual Compose disposal during a pending dialog, exact framework arrays,
sender ownership and per-SDK UI/resource admission. The first19 passed once with69
held inputs. These are **not** Android runtime tests. Current standard CLI/controller/
dedicated reporter-APK registration is missing; registration841 is a separate
unqualified successor. API31 CLI support and all14 actual profile results remain
required. Natural one-time expiry is explicitly blocked/unregistered until an
observed real importance/expiry protocol is available; no fake timer, regrant or
restart substitutes for it.

## Maintenance and evidence reuse

Keep legacy public `com.mohamedrejeb.calf` packages and Gradle module paths for
compatibility; use NativeCmpKit for new project identity. Keep original issue
descriptions and native assertions unchanged. Source envelopes current299,
physical union319 and original/static345 are different domains. No global count,
unchecked repin or broad historical-source fallback may replace them.

Reuse accepted original23/XML8/FIRST30/FIRST19 results only on applicable unchanged
bytes. New ingress or controller changes require their important affected controls,
not replay of every accepted population. Full CI producer/native/ordinary package
consumer/API–ABI/dependency/legal/security/release gates remain independent.
