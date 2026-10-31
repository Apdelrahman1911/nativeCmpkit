# Android I/O provider lifecycle — integrated and compiled, native pending

The reviewed 25-file test/controller patch is SHA256
`11552d98ceae0b9f3cc9c67fcce91f895ad26652c7e8c39e37204d324f62623a`.
All preimages/postimages were checked and independently reconstructed. The
19-file initial proposal and1009-input author snapshot are historical only:
the integrated reporter has **1010 library/1087 combined held inputs**.
No production APIs, dependency versions or accepted oversize method changed.

- One separate-UID Java helper assembles **exit0/26.01s**; reporter APK assembles
  **exit0/104.03s** on those exact inputs. **ZERO new native tests executed.**
- The SDK36.0.0 default/minSdk-range APK verifier exits0 but reports the actual
  unsigned `META-INF/.../app-metadata.properties` warning. The strict parser
  correctly refuses it. Preserve that failure; do not suppress warnings or infer
  min23/security/release clearance.
- On the **same unreconstructed APK**, exact minSDK=maxSDK35 verification passes
  unchanged strict warning/v2-or-v3 rules and actual private-key certificate
  equality. The two-file owning adapter recovery records/requires integer35/35
  scope. Native minimum compatibility is not inferred.
-42 author-owned modeled methods and19 overlapping affected controls are read
  back, not repeated. Eight new signer-scope models have four baseline reds and
  eight candidate passes; exact integrated bytes reuse those results. Four
  owning existing preparation/controller tests are rechecked after the recovery.
  Source/helper/native/catalog inputs and warning/manifest parsers are unchanged;
  only two adapter/test files differ from the held compile. No accepted native,
  host or original browser method is replayed.

The finite `android-io-provider-lifecycle` request requires five actual API35
methods, fresh exact XML/filter/task marker, Enforcing owned emulator, inspected
and installed helper APK-byte identity/signature/native UIDs, actual Activity
result grants, client/provider Binder death, revocation, public reads and Coil
close/cancel assertions. Helper preparation precedes reporter/native cost;
partial receipts and owned helper/emulator/ADB cleanup must remain failure-safe.
All11 full slots/eight Android modules and the browser content profile remain.

#45/#55/#57 stay open. Fixed synthetic tree documents are not real system/cloud/
single-document/iCloud/bookmark reboot/unknown-size binary sources. Injected Coil
decoders are not default bitmap/EXIF/seek/peak-memory/cache-key behavior. These
new native methods must be reviewed against original criteria individually;
no automatic closure, packaged consumer/ABI/security/legal/readiness, publishing,
Pages/main/history change. Raw console/APKs/signing inputs remain private;
data receipts preserve failures, command/timing/input identities and archive hashes.

See [the implementation/test guide](../../android-io-provider-lifecycle.md).
