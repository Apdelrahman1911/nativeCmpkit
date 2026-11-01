# Camera012 actual recovery remains failed — no native execution

[Run 41263840100](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41263840100),
attempt 1, immutable `375123435c892bd7a93e6d5d18e336f434ca8a21`, is **FAILED** at step 17.
The request retained only API35 / `calf-camera-picker` / existing profile
`android-camera-restoration-dont-keep` / `nativeDontKeepActivitiesRestoresOneReadableCapturedFile`.
The three accepted camera009 methods were not requested or replayed.

## Observed boundary, not a guessed cause

Owned AVD creation succeeded exit 0/2.0 s and reporter APK assembly succeeded
exit 0/284.09 s. The controller then records **ValueError**, safe source origin
[`android_camera_developer_prerequisite.py:47`, `require`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/375123435c892bd7a93e6d5d18e336f434ca8a21/scripts/ci/android_camera_developer_prerequisite.py#L45-L47).
The actual journal has `launch_attempted=false`, no completed AVD-definition/config
identity publication and no Popen-session establishment. Original owned diagnostic
inventories contain only the assembly/create logs; no emulator log was opened.
Together with [immutable controller ordering](https://github.com/Apdelrahman1911/nativeCmpkit/blob/375123435c892bd7a93e6d5d18e336f434ca8a21/scripts/ci/android_device_tests.py#L307-L329),
this localizes the refusal to **pre-launch owned guest capture/admission**.

The innermost generic `require` frame does not retain its calling guard or actual
generated INI/config input. The particular guard, value, row, schema/path condition
and underlying cause remain **unknown**. This is not a proven config/path/schema,
KVM, boot, SELinux or master-setting failure. No guessed repair is justified.

## Native/runtime nonacceptance

**Zero actual native methods, zero connected-task execution markers, zero original
native XML and no library execution receipt.** Both official camera result
directories are absent in the complete original diagnostics (all 18 inspected result
directories are absent). The reporter assembly is compilation, not a test pass;
the controller step's exit 1 is not a failed native testcase/Gradle execution.

Guest launch/boot/Enforcing readback, installed reporter/receiver identities and
signatures, original master/native/scalar snapshot, master initialization, unchanged
Settings UI/accessibility/task leases, camera capture/return, pre-barrier restoration,
normal reboot, changed-kernel barrier and exact original-row restoration were all
unreached. Actual012's original master was not read. Actual011 remains its separate
failed native execution with unknown returned master value/cause; neither 0 nor
absence/null is inferred from this attempt.

## Exact cleanup scope

The exact original guest receipt and controller agree: both exclusive 0700 `avd` and
`android-user` roots were FD-confined removed, `roots_absent=true`,
`identity_confined_disposal=true`, `disposal_status=passed`, `errors=[]`.
But **`clean_shutdown=false` remains false**. `engine_known_exited=true` and
`owned_transport_absent=true` are expressly the [source no-launch branch](https://github.com/Apdelrahman1911/nativeCmpkit/blob/375123435c892bd7a93e6d5d18e336f434ca8a21/scripts/ci/android_camera_developer_prerequisite.py#L520-L551),
not an observed emulator graceful exit or post-exit ADB removal. No engine was
launched; no guest restoration/cleanup acceptance is substituted. Successful owned
root disposal never waives the primary failure or missing runtime evidence.

## Integrity/source evidence only

The original 114702-byte artifact ZIP (SHA256
`310540496ebe7e3c028b50985d4136214d690cdd0b918cef993cf1f795d68586`), all 14 members, original current-job/tooling logs
and receipts are retained privately. This candidate exports reviewed exact safe JSON
and derived bounded facts, **not the ZIP, terminal logs, private paths, generated
config/userdata, signing material or secrets**. No XML is fabricated.

Both actual input maps are the exact **1070-library** frozen map; there is **no actual
combined map**. The 1147 combined frozen hashes and identical library subset independently
match immutable 375 Git blobs. Controller before/after source is clean/unchanged.
All 31 selected camera/receiver native source paths still equal actual011, including
the original Dont-keep method and native/Settings UI lease bytes. The three Python
postimages exactly match the sealed prerequisite delivery. These are source/static
observations, not runtime certification. Tooling succeeded separately, including
its 1581-method CI guard gate; overlapping tooling counts are not summed as coverage.

37 integrity/source/results/absence checks pass. One initial reviewer regex
incorrectly required the tooling `OK` line immediately after its count; the actual
blank separator is retained and the owning reviewer parser is corrected. This was
not a CI/native failure and changed no actual artifact/source. No local build/model/
native execution, live edit, dispatch or Git/GitHub mutation was performed for this
review.

## Original requirement and disposition

Original criterion 1 (Dont-keep enabled, real launch/capture/return, exactly one readable
KmpFile with exact ownership/restoration cleanup) remains **unaccepted**. Original
criteria 2/3 retain the three accepted camera009 methods, without adding an immediate
second client-onCreate while the external recipient stays top. #13 **remains open**;
zero new native acceptances, no automatic repair/replay/dispatch, and no publishing,
release/security/readiness or capacity-policy clearance follows this attempt.
