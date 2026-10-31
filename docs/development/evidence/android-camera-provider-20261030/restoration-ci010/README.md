# Camera restoration CI010 — original failure preserved

Run [41246939704](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41246939704), attempt 1, at `6eaac5e01e5631d567e571c32d6523d663a8a184` completed **FAILED**.

- **1 actual API35 method executed / 0 passed / 1 failed**, no errors or skips. Gradle **exit 1 / 49.02 s**. The two XMLs are original and additive archival copies of this **one** execution, not two runs.
- `nativeDontKeepActivitiesRestoresOneReadableCapturedFile` refused at ordinary declared-field lookup of `TRANSACTION_setAlwaysFinish`: `NoSuchFieldException`, `OwnedAlwaysFinish.kt:94` (constructor line 38; fixture line 108).
- This occurs **before native setting mutation/readback, client launch, capture, destruction or result work**. Physical field absence versus hidden-API-policy cause is **unknown**; no bypass or guessed transaction is justified. Native helper restoration was not needed and is **not claimed executed**.
- The existing independent review passes **41 integrity checks**, not native acceptance: exact **1012 library / 1089 combined** immutable Git inputs, four actual library input maps, fresh task/filter/XML correspondence, installed receiver-byte identity, receiver component lease and owned receiver/emulator/ADB cleanup. Receiver/reporter compilation succeeds **0 / 79.03 s** and **0 / 293.09 s**; compilation is not a native pass.
- The receiver APK has **890471 bytes**, source/installed SHA-256 `84d470f0cd69f32cb6fa5b936025aab65df1e8103181a4046844d706ad09c77f`. Its identity, stop/uninstall and later absence were reviewed. The owned Enforcing API35 / Android15 / x86_64 emulator exits gracefully with code 0, no forced group; its ADB transport is removed. Unreached native grants/signatures/capture assertions are **not** setup passes.

## Original criteria and reuse

[#13](https://github.com/Apdelrahman1911/nativeCmpkit/issues/13) **remains open**: cumulative restoration executions **25**, accepted **3**. Reuse the three applicable camera009 passes without replay; all earlier failures stay failed.

[Original criteria/source checklist](original-criteria-source-checklist.json) and [independent actual review](independent-actual-review.json) remain authoritative. Dont-keep capture is not verified. Rotation and kernel death occur while the recipient is foreground, but new Activity/orientation is checked only after recipient completion: **foreground recreation itself remains unverified**. Foreground destruction must not silently substitute for that criterion. The native009 cancellation/owned-file criterion remains verified; it does not close the issue.

[Source correspondence](accepted-source-correspondence.json), [frozen source identities](frozen-source-identities.json), [independent source preflight](source-preflight-independent.json), and [frozen request](request-frozen/) retain the reviewed immutable scope. No current-tree or later Settings UI recovery was reviewed for this archive. The [initial reviewer digest refusal](initial-reviewer-digest-refusal.json) is retained: raw JSON SHA `c7086b89d5bd5b2d9552d9f6bdf1179813485cf2eef4b6adb3c2c86699b222a1` is not the source-defined input digest `c742c84939852e9bf6a1ea3ef629c3c0d45ecec90dcc84886218d2ae9560adc0`; the completed reviewer corrected that distinction on unchanged bytes, not with a rerun or source change.

## Public archive and privacy

[Reports](reports/) mirror **20 of 24** original artifact objects. Both failure XMLs remain **byte-exact**, including their original failure text; the fixed framework.jar location is a public Android OS path. Other copied FAILED receipts are not rewritten into success.

[Archive manifest](archive.json) and [original artifact manifest](artifact-manifest.json) retain the artifact ID **13060545411**, original ZIP **217026 bytes**, SHA-256 `4aff93e54988ee152bd4b9c01ac6dca080bf1a8b46121d84fe31294772cad524`, and original/archived file hashes. The ZIP itself is not published.

[Withheld values](withheld-values.json) documents **four** private absolute command-prefix substitutions across **two** JSON files, with original scalar UTF-8 sizes/hashes and whole-file hashes. Only those files are reserialized. Commands are **display-only provenance**, not executable verification/dispatch requests. The entire `failure-diagnostics.json` is hash-only because it contains raw log excerpts and private runner paths (**28031 bytes**, SHA-256 `79d4712f5fbec9f8964b81b21615fbd6ac60165943015b89767e2af8f87e5315`). Two cache-action receipts and the dependency recipe are also hash-only for camera-only compactness, not cache/dependency clearance. No raw logs, APKs, keys, native binaries, source bodies or private machine paths are included.

[Terminal run](run-final.json), [jobs](jobs-final.json) and [artifacts](artifacts-final.json) are the final existing snapshots: tooling success, sole native job failure, three unrelated jobs skipped. [Provenance](archive-provenance.json), [archive-only checklist](archive-checklist.json) and [preservation readback](archive-readback.json) describe packaging verification, **not new tests or a new native verdict**. `SHA256SUMS` covers all public files except itself:

```sh
sha256sum --strict --quiet --check SHA256SUMS
```

No downloads, tests, builds, accepted-suite replays, dispatches, Git/GitHub mutations, issue closure, publishing/Pages/main/history, minimum/hardware/vendor/consumer/ABI/legal/security/dependency/profile/readiness or capacity-policy clearance occurs here.
