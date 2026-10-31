# Android I/O provider lifecycle verification

## Actual result — 2026-10-31

[Native41245152018](evidence/android-io-provider-lifecycle-20261031/native-ci001/README.md)
now passes all five API35 methods/one exact original XML/Gradle0/45.02s;
real framework grants, own secondary-client restart, revocation, unstable Binder
death/recovery and injected-Coil error/cancellation/descriptor closure execute.
Only the [mapped original-criterion subsets](evidence/android-io-provider-lifecycle-20261031/native-ci001/criterion-subset-review.json)
are accepted. #45/#55/#57 remain open; earlier preparation observations below
retain their historical scope. No accepted lifecycle replay is required.

## Scope and execution flow

`calf-io/src/androidDeviceTest/.../AndroidIoProviderLifecycleTest.kt` exercises
public KmpFile/bookmark/child metadata APIs and the real Coil KmpFileFetcher
pipeline. `tests/consumer/android-io-documents/` is an independent Java fixture,
not a sample application or published consumer. It uses a separate Android UID;
its DocumentsProvider requires MANAGE_DOCUMENTS, which the reporter must lack.
Signature-only bounded control endpoints cannot grant broad content access.
A native Activity result creates read/persistable/prefix grants for one fixed
synthetic tree; no manual URI grants, mocked resolver or fabricated result.

1. Owned API35 AVD lease/Enforcing boot and fixed official SDK inspector recipe.
2. Helper source/manifest compilation, one strict modern APK signer, exact actual
   private-key DER equality, installed-byte/source identity and scoped35/35 receipt.
3. Only then assemble reporter with the same private signing home; expose the
   owned-helper bit only after prepared-receipt validation.
4. Run exactly five unique library-level methods and one fresh XML/task marker.
5. Restore/release actual grants, close Binder/descriptor owners, uninstall only
   reverified owned helper bytes, gracefully stop owned emulator/ADB transport.
   Any uncertain preparation/cleanup prevents green status; preserve primary error.

## Methods and limits

| Method | Actual required behavior |
| --- | --- |
| persistedTreeBookmarkSurvivesOwnedClientRestartAndExplicitRelease | Real persisted grant + SharedPreferences, acknowledged owned client self-kill/Binder death, new PID/generation, public bookmark restore and release denial |
| ownerRevocationDeniesTreeAndChildMetadataAndActualContentRead | Real metadata/bytes before source-owner framework revocation, tree/child/bookmark/read denial afterward |
| ownedProviderDeathProducesRealBinderFailureAndTreeMetadataRecovers | Unstable client, closed cursor/PFD before provider self-kill, real DeadObjectException, new PID/generation and public metadata/read recovery |
| nativeCoilDecoderFailureClosesCrossUidSourceAfterExactBinaryRead | Actual ImageLoader/Okio/native REG descriptor; injected decoder consumes exact binary bytes, retains EOF FD, fails, observes close1/FD0 |
| nativeCoilCancellationClosesTransferredSourceWithoutLateSuccess | Same real transfer; paused injected decoder, actual coroutine cancellation, close1/FD0, no late success |

Do not retain a stable client/PFD/cursor across provider kill: Android15 may kill
stable dependents. This intentional unstable-client event does not diagnose the
historical signal9/null-size failure. Directory null metadata is not unknown-size
binary coverage. Default bitmap/EXIF/seek, memory/key benchmarks, physical/min23/
vendor/cloud/system-provider/single-document and Apple bookmark scopes remain open.

## Verification commands

Read-only plans, before any cost/mutation:

```sh
python3 scripts/ci/workflow_matrix.py android-io-provider-lifecycle
python3 scripts/ci/android_device_tests.py plan --output build/ci-verification/io-provider-plan --api-level 35 --module calf-io --focus android-io-provider-lifecycle
```

Use the exact immutable GitHub `gradle.yml` profile through the lead's one-shot
request protocol. Do not manually set the owned-helper bit or bypass controller
receipts. Do not replay accepted oversize/host methods to replace missing tests.

[Prepared evidence](evidence/android-io-provider-lifecycle-20261031/README.md)
contains held inputs, actual helper/reporter compiler receipts, original default
signer warning refusal, unchanged-APK strict API35 readback and modeled guards.
It records ZERO new native executions and no issue/release/security clearance.
#45/#55/#57 require independent original-criteria review after actual results.
