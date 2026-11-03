# Camera shared CI source-fixture recovery —491–494

## Original run stays failed

[41700490263](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41700490263)
ran at **d63e57f1d3ac7b0a297a1d39f2641292fea71bd3**. Tooling executes2,596
source methods/119.139s, with **two failures**; the other seven jobs are skipped.
Eight original log members were acquired once and reviewed; **zero artifacts,
Gradle/APK/native executions or XML**. All1,281 frozen inputs match their own Git
blobs, not nonexistent platform before/after maps. New recents19 all pass in
that hosted tooling execution; no local replay or native acceptance is inferred.

Root causes and exact owning locations:

1. `test_android_camera_boot_handoff.py::test_new_stage_exact_inverse_preserves_old_pins_sources_and_roundtrip`
   reconstructs the older boot-stage bytes, then compares them against a later
   recents-observation controller postimage. It must first admit current bytes,
   compare against the exact boot postimage, and keep the older forward round-trip.
2. `test_android_external337_fixture_recovery.py::test_source_digest_admits_exact_current_identity_but_not_old_or_changed_images`
   correctly refuses historical/drifting source at the newest boundary, but its
   exact expected message still names boot rather than recents admission.

Both are **confirmed tooling fixture defects**, not camera-native root causes.
#13's missing Dont-keep C1 remains required. Prior camera failures stay failed.

## One related repair batch

Four existing tooling paths/eight exact reversible fragments plus three new
source files repair those contracts. An independent newest leaf preserves all
three previous manifest hashes and historical source pins; only one exact older
External337 pre-handoff digest is admitted for history, never current admission.
The previous handoff fixture separates actual-current custody from its own older
stage; every original assertion/refusal remains, without generic repinning.
Controller, observer, boot waiter, parser/helper, original324/1375 callsites,
Kotlin/native APIs, dependencies, workflow and permissions are **unchanged**.

492 executes failed2/affected2/NEW4: **seven pass/one source-admission error**,
8methods/0.132s/wrapper0.574354195s. The error exposes one remaining older-stage
argument supplied to a strict current-source reader; original result/source are
preserved. Only that failed method, new eight-fragment geometry, and two affected
owning controls run at493: **4/4 pass**,0.038s/wrapper0.448775298s. No unchanged
accepted population is replayed. Across snapshots:9 distinct method names and
12 invocations; **all eight final live important obligations qualify**. The
renamed seven→eight geometry guard is not two final obligations.

494 accepts38 passive source/results checks: all1,284 current inputs held,1,277
other preexisting inputs unchanged, own-Git preimages, original manifest/pin
custody, three older endpoint stages plus16 External/three ARM endpoints. ZERO
local compiler, SDK, native, or new original-download operation.

## Next and limits

Freeze/push development only, then request **only the missing C1** at changed
immutable bytes within max2 combined hosted-heavy reservations INCLUDINGqueued.
Reuse applicable camera009 C2/C3; never replay accepted native populations or
redownload original491. Apple480 keeps its separately frozen SDK-only reservation;
its source SHA/input count is not replaced by this documentation revision.

**No issue closed here:103closed/69open/172;22implemented/36partial/101verified/
five unresolved.** Native absence/capture/developer-state restoration and owning
cleanup must actually pass before #13 closure. No package/release/deployment,
Pages/main integration, consumer/API–ABI/legal/security/readiness inference.
