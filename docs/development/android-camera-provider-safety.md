# Android camera provider / output safety — 2026-10-30

Related original findings: [#78/NATIVE-022](https://github.com/Apdelrahman1911/nativeCmpkit/issues/78),
[#13/NATIVE-019](https://github.com/Apdelrahman1911/nativeCmpkit/issues/13) and
NATIVE-024. **No closure or native pass is inferred from this preparation.**

## Actual request and owning recovery

[41073167954](evidence/android-camera-provider-20261030/native-ci002/README.md)
at `a2ecd026` verifies **all4 actual API35 methods**, Gradle0/54.02s,984/1061
immutable inputs, native grants/writes/descriptors, zero implicit handlers and
exact system-camera state restoration, fresh XML and owned app/emulator/transport
cleanup. The overall workflow remains failed: API23 again refuses before its first
output/any native execution; the exact early cause is unknown. Minimum-only
recovery requests only the still-unverified API23 four-method contract, reusing
accepted API35 rather than repeating it. #78 stays open until original criteria
are met; no compile-only/native-UI/photo/process/release inference.

[41069819642](evidence/android-camera-provider-20261030/native-ci001/README.md)
at `d95a0502` **failed**: API35 3 fresh native methods/2pass/1failed, Gradle1/40.02s;
API23 preflightValueError/zero executions/cause unknown. Actual AVD report names
were also rejected by the new archiver. Original failed XML and owned cleanup
are preserved; these failures are not silently superseded.

[Recovery](evidence/android-camera-provider-20261030/recovery001/README.md)
separates legacy/wrong-root provider components, inspects the receiver write error
before capture assertions, repairs the data-only report-name guard, records
camera-only preflight stages and observes already-owned transport disappearance.
A fourth case exercises the actual implicit intent with zero available handlers
and exact restoration of fixed system-camera enabled states. No uninstallation
or physical/vendor-camera claim. The updated APK compiles0/36.01s/984+1061 held
inputs, **zero native executions**;209 distinct important synthetic methods and
Actionlint pass. Final changed manifests/prerequisites require both APIs freshly;
the old two native passes cannot certify these changed inputs. #78 stays open.

## Owning repair and actual regressions

`CameraPickerLauncher.android.kt` created its output in private
`cacheDir/nativecmpkit-camera/` but bypassed FileProvider on API23. Another UID
cannot read/write that filesystem path; a provider option was silently ignored
and missing/wrong setup was allowed to launch without a configuration result.
Three new real-source/Robolectric API23 regressions failed before the fix:
configured output was `file://`, and missing/wrong-root setup emitted no required
failure. [Evidence](evidence/android-camera-provider-20261030/implementation001/README.md)
retains the failures and the separate test-fixture compiler error.

The minimal repair uses existing AndroidX FileProvider on **all supported Android
versions (API23+)**, retaining custom authority selection/default
`${applicationId}.provider`, public signatures, packages and attribution. Existing
exception classification clears only the owning pending request/file. Provider
setup errors report `Configuration`; platform no-handler errors report `Launch`.
Successful files remain caller-owned cache outputs; cancellation deletes only its
owned output. No disposal unlink, new cleanup sweep or native-owner rewrite.

Eight new provider regressions and all existing camera host scenarios pass:
**22/22 executions/four fresh XML, zero failures/errors/skips, Gradle exit0/19.01s**.
Correct/missing/wrong-root providers are exercised at SDK23/34; sibling cache
files are outside the recommended root. Real XML/FileProvider/ContentResolver
bytes replace the fixtures' former filesystem interpretation of URI paths.
Existing five Activity/Compose lifecycle and reentrant/exactly-once assertions
remain intact. External camera/result boundaries are still controlled on the
host: these outcomes do not establish actual grants, process death or hardware.

## Native fixture and efficient verification

The minimal `CameraProviderVerificationActivity` consumes the **public** Compose
launcher. A native ActivityResultRegistry bridge only selects a finite installed
external camera receiver (or an actually absent component); Android itself
starts that different UID, migrates EXTRA_OUTPUT grants and returns the Activity
result. No manual URI grant, fabricated descriptor read or mocked platform launch.
The receiver writes explicitly **synthetic bytes**, not a claimed camera photo.

The independent receiver APK has a fixed package and signature-protected
Activity/service. Both endpoints check caller identity; replies are UID/nonce
bound. No arbitrary URI/file/grant RPC. Native cases inspect read/write grants,
ClipData, balanced real descriptor close outcomes, delayed caller reads, custom
and default authorities, missing/wrong-root setup, a real Android absent-component
launch error, narrow-path exclusion and cancellation ownership. This is a source
consumer/library test, **not** a sample or packaged Maven/API-ABI consumer.

The finite `android-camera-provider` profile requests API35 followed by API23
**serially on one host**, with distinct fresh owned AVDs, report receipts and
cleanup. API23 is accepted only for this exact module/focus; all eleven complete
slots and all seven prior Android modules remain, with camera added as the eighth.
Only dependencies/unchanged compiler work can be reused, never old XML. Each
first XML is preserved before the second API replaces Gradle's report directory;
failed outcomes stay failed. APKs/keystores/environment/raw logs are not uploaded.

Local reporter and receiver APK assembly pass exit0/41.01s and0/11.0s with all
983 library/1060 combined selected inputs held. **Zero native methods ran locally**:
this host has no KVM. Important synthetic plan/lease/archive/workflow guards pass
179 distinct methods plus Actionlint; they are not Android outcomes. An immutable
CI execution and independent receipt/original-criteria review are still required.

## Compatibility / remaining acceptance

API23 hosts must now configure the same narrow FileProvider required on API24+.
This intentional URI/configuration behavior change replaces broken private-path
delivery; it does not rename public APIs. Follow [provider setup](NATIVE.md#android-provider-setup-for-camera-and-local-file-sharing).
Do not broaden paths to hide configuration errors. Existing `KmpFile.uri` remains
an opaque Android URI, not a filesystem path. No API/ABI certification is claimed.

#78 requires actual correct/missing/wrong provider checks on API23/24+, own
authority/no-handler and narrow grantability. Native execution is still pending;
the absent **selected** component does not certify removal of all system/vendor
camera handlers. #13 additionally requires actual don't-keep-activities, rotation
and OS process death while an external camera is foreground; host restoration or
this synthetic-output recipient cannot close it. NATIVE-024's real 12/48MP memory,
latency, disk-full and cache-lifetime/device measurements remain separate gates.
Physical device, native photo/UX, complete consumers/API-ABI, dependency/provenance,
legal/security and release gates remain. **Nothing published or deployed.**
