# Correct third-party recipient selection; genuine OS restoration retained

The [actual third request](../restoration-ci003/README.md) failed four methods at
an invalid global implicit camera-selection prerequisite, before client launch.
[Reviewed Android15 public source](public-camera-selection-source.json) restricts
unqualified camera intents to system apps unless DPC preference applies; package
or component selection is explicit. No exact running framework binary or actual
timed-out caller-handler list was extracted. Earlier failures remain distinct.

The **test-only** consumer validates the real unqualified TakePicture action,
owned fresh content EXTRA_OUTPUT, fixed foreign UID/signature/permission/component
and actual enabled override, copies the intent and calls the genuine
`super.startActivityForResult` with **unchanged request code/options**. It does not
replace/inject the ComponentActivity registry, saved state or result, grant URIs,
mutate ClipData, configure DPC/root/system apps or change production policy.
Android still owns grant migration, presentation, destruction/process restoration
and result delivery. Recipient selection and output bytes remain synthetic.

Reporter preflight now uses actual package-scoped native resolution with exact
component/recipient UID. Unnecessary system-camera disabling/restoration is removed.
Disabled manifest, receiver-owned lease/DONT_KILL_APP/exact restore-before-close,
all native grant/descriptor/PID/task/settings/rotation/file/cleanup assertions remain.
Persisted real-boundary launch count1/native recipient UID/unchanged registry code
are additionally checked before and after recreation.

Five new source guards first execute with **four failures**; all **49 important
camera-tooling methods** pass after repair. These are synthetic, not device proof.
An owning private pre-Gradle input-set guard omitted the changed source-test input;
that refusal is preserved, then corrected to require all three exact changes.
Serial reporter APK compilation passes exit0/35.01s, **987/1064 held inputs**.
The unchanged receiver's reviewed exit0/14.0s compile is reused, **not a fresh run**.
No native execution or issue closure is inferred. Request the four still-unverified
API35 restoration methods on immutable Git; provider/API23/host/unrelated results
are not replayed. #13 and physical/minimum/consumer/API-ABI/heap/dependency/legal/
security/release, publishing/Pages/main/history/solo/capacity gates remain.
