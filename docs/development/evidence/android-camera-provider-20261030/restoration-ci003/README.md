# Actual third restoration request: shared selection prerequisite failed

[Run41102937453, attempt1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41102937453)
at `1f5f31bd9ef543bd9681d8e9d24a4337c6a070ce` **FAILED**. Tooling passes;
API35 executes **four methods, four failures, zero accepted**, one fresh XML,
Gradle exit1/174.03s. Reporter APK exit0/332.09s and owned AVD exit0/2.0s;
987 library/1064 combined inputs match immutable Git. Enforcing Android15,
receiver installed-byte identity and owned removal, graceful owned emulator exit
and owned ADB transport removal were reviewed. Original/sanitized XML copies
represent **one report**, not two executions.

All four fail at `AndroidCameraRestorationTest.capture:109`, waiting for the
third-party delayed receiver to be the sole **unqualified implicit** camera
handler, before client launch/capture/restoration. Preceding receiver-UID/nonce
lease, exact component setting and real **package-scoped** native-handler1 checks
passed. The actual caller's timed-out handler set was not logged; do not invent
its contents or a visibility/cache failure. This is not an observed production
restoration defect. Earlier empty CLI reply and tooling failures remain distinct.

[Owning recipient-selection repair](../restoration-recipient001/README.md) cites
Android15 public source: unqualified implicit camera resolution is system-only
unless DPC persistent preference applies; package/component selection is explicit.
That is source context, not extraction of this emulator's exact framework binary.
No production policy bypass, root, DPC configuration or manual URI grant is used.
#13 remains open; provider#78 and unrelated accepted results are not replayed.
All original acceptance and independent security/release gates remain.
