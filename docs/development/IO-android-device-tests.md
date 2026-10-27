# Android IO and saver device-test workstream

## Current state

Additive [minimum-platform policy review](checkpoint-gc-diagnostics-navgeo-20261027.md#android-minimum-policy-and-release-gates)
binds Android23-era `android-6.0.1_r81` to an immutable commit/tree/four Git blobs:
`untrusted_app.te:154–160` has `neverallow untrusted_app file_type:file link;`, and
`global_macros:28` omits `link` from create-file permissions. A minimum API23
emulator is **not evidenced as a workaround** for app-created genuine hardlinks.
This is source policy, zero API23 device tests. Original wrong-path404s and correct
retrievals/bindings remain. Provision a genuine permitted fixture or document the
unavailable scenario; never root/change SELinux/skip/replace hardlinks with aliases
to label it passed. The failed native fixture gate remains open.

The lead assigned this bounded workstream after the UI control fixes were held
for diagnostics. The initial work added **29 test functions in 12 new test-only
files**. Two later native-probe controls and two parser controls bring the
current total to **33**:

- `calf-io/src/androidDeviceTest`: **10** IO tests, **1** probe control and
  **1** parser control.
- `calf-file-picker/src/androidDeviceTest`: **11** direct saver/identity tests,
  **1** probe control, **1** parser control and
  **8** public launcher/ActivityResult tests.

Latest completed collection: the **fourth diagnostic** below has **17 IO cases,
16 passed and one failed**; picker emitted no final XML before the bound expired.
The full 42-case request is **incomplete and failed**, not a whole-suite pass.

The initial [authorship inventory](evidence/io/android-device-test-authorship.json)
records exact file hashes and function names. At that checkpoint, XML parsing,
source inventory and whitespace checks passed. **No Kotlin/device-test APK
compilation or device execution had been performed.** This is an authorship
receipt, not passing-test evidence, a finding closure or release authorization.
Production sources, existing Android host tests and baseline audit evidence were
not modified by this test author. The build owner separately wired dependencies
and device-resource processing under the lead's authorization.

The [first actual device diagnostic](evidence/gradle/first-android-device.summary.json)
exited **1** at device-test Kotlin compilation: **zero device tests executed**.
The log confirms missing AndroidX test dependencies in all three selected modules
and two mixed cursor-row array inference errors in the picker fixture. Its 96
primary and 19 prior-bound supplemental input hashes remained unchanged. No APK
or instrumentation pass is claimed. The lead separately discovered actual
`connectedAndroidDeviceTest`, `assembleAndroidDeviceTest` and
`compileAndroidDeviceTest` task names in the configured AGP target.

The [authorized fixture-only corrections](evidence/io/android-device-first-test-repairs.json)
make the two cursor array element types explicit as `Any?` and retain the
ActivityMonitor across cancellation and the next launch. Android's
`Instrumentation.waitForMonitorWithTimeout` unregisters the monitor; the direct
monitor method does not ([implementation inspection](evidence/io/android-device-monitor-inspection.json)).
All cursor values, assertions and 29 test functions are unchanged. The inverse
patch reproduces both the failed input hashes and the preserved initial authorship
snapshot; the other ten authored files are unchanged. These static checks are
not recompilation or runtime verification. Sources are held for lead-scheduled
diagnostics, with dependency wiring owned separately by the build
reviewer.

### Second diagnostic: actual device execution, with failures retained

The [second diagnostic](evidence/gradle/second-android-device.summary.json) exited
**1** after 727.14 seconds on the task-owned Android 15/API 35 software emulator;
all **687** selected input hashes remained unchanged. The
[independent owned-scope XML review](evidence/io/android-device-second-results.json)
records:

| Scope | Executed | Passed | Failed |
|---|---:|---:|---:|
| IO device tests | 0 | 0 | 0 — device Kotlin compilation failed |
| Authored public saver Activity tests | 8 | 2 | 6 |
| Authored direct saver/identity tests | 11 | 0 | 11 |
| Inherited picker common tests | 4 | 4 | 0 |

The two authored passes are the real overlapping-launch result/write/close case
and lost-byte-payload Activity recreation with real error/cleanup. The **17**
authored failures remain failures: fourteen `/proc/self/fd` path-stat `EACCES`
errors, the invented `CATEGORY_OPENABLE` expectation, the stale observation
monitor's second-launch assertion, and a separate native `Os.link` `EACCES`.
Reaching earlier assertions before a probe failure is **not** a passing case.
The combined command also ran WebView tests; their separate outcome does not
change these IO/picker counts.

After the final receipt, the lead authorized [narrow test-only repairs and two
positive controls](evidence/io/android-device-second-test-repairs.json):

- Match pinned FileProvider nullability: fail on an unexpected null descriptor,
  and keep its cursor override nonnullable without altering metadata cells.
- Duplicate each enumerated native descriptor with `ParcelFileDescriptor.fromFd`,
  inspect `Os.fstat`, and close every probe-owned duplicate. Only a wrapped
  `EBADF` from duplication of a concurrently closed original may be ignored;
  enumeration, `fstat`, close and other errors still fail. This is not broad
  `EACCES` suppression ([API inspection and test plan](evidence/io/android-device-fd-probe-plan.json)).
- Give each launch its own observation monitor, while retaining the separate
  real-Activity routing monitor and every result/data/close assertion.
- Compare categories with the real pinned AndroidX `CreateDocument` contract,
  which does **not** add `CATEGORY_OPENABLE`; retain independent action, title
  and MIME assertions ([contract inspection](evidence/io/android-create-document-category-inspection.json)).
- Positively test both descriptor probes against an actually open file, its
  unchanged file offset and post-close zero count; additionally test real pipe
  endpoints with counts **2 → 1 → 0** and repeated scans for leaked duplicates.

These repairs and two new tests were **not** part of the second diagnostic.
Their static checks are not runtime passes. The native hardlink case is unchanged:
no skip, fabricated inode or SELinux policy change disguises the denied operation.
Its fixture-acquisition/device-policy limitation remains a required check.

### Third diagnostic: native probe failure reproduced, not hidden

The [third diagnostic](evidence/gradle/third-android-device.summary.json) exited
**1** after **821.17 seconds**; all **688** captured input hashes remained
unchanged. Both IO and picker compiled and executed on the same task-owned
Android 15/API 35 emulator. The [independent fixture-author XML
review](evidence/io/android-device-third-results.json) preserves each case:

| Scope | Executed | Passed | Failed |
|---|---:|---:|---:|
| Authored IO methods, including the first native control | 11 | 1 | 10 |
| Inherited IO common methods | 5 | 5 | 0 |
| Authored public saver Activity methods | 8 | 3 | 5 |
| Authored direct saver/identity methods, including the first native control | 12 | 0 | 12 |
| Inherited picker common methods | 4 | 4 | 0 |

The one authored IO pass is metadata/URI preservation. The three Activity passes
are overlap rejection with the accepted real result, lost-byte-payload recreation
with error/cleanup, and cancellation followed by another actual launch. The last
case now exercises the repaired per-launch observation monitor and actual pinned
AndroidX category contract. **All 27 other authored methods failed**: ten IO and
sixteen picker cases at real `fstat EACCES`, plus the unchanged native `Os.link
EACCES` setup failure. Earlier byte assertions do not establish resource cleanup.
The two subsequent parser methods were **not** present in this run.

A [minimal native denial receipt](evidence/io/android-device-pmsg-category.json)
identifies a denied `getattr` on `/dev/pmsg0`, a `pmsg_device` **character device**,
while the native probe was running. It explains at least one non-target denial,
not all inaccessible descriptors. Duplication alone had not made `fstat` legal.
No device path exclusion, swallowed `EACCES`, fake stat value or SELinux change
was applied to hide that failure.

### Calibrated fdinfo prefilter: test-only follow-up

After the third receipt, the lead authorized [six bounded test-only
changes](evidence/io/android-device-third-probe-repairs.json). Production,
build files, Activity cases and the hardlink case were unchanged and all owned
sources were refrozen. The [exact running-kernel source
review](evidence/io/android-fdinfo-kernel-review.json) and [independent six-file
review](evidence/io/android-device-fdinfo-source-review.json) record the rationale
and limits:

1. Admit only actual regular-file/FIFO reference descriptors whose nonzero
   `fstat.st_ino` equals their own parsed `fdinfo` `ino`. A caller file reference
   also compares its path stat to the real opened descriptor. This calibration
   is necessary because arbitrary filesystem `getattr` implementations need not
   report the kernel's internal inode unchanged.
2. Snapshot only this test process's numeric FD names. Acquire each owned native
   duplicate using `ParcelFileDescriptor.fromFd`, then read its stable
   `/proc/self/fdinfo/<duplicate>` metadata without reading or seeking its data.
3. Exclude only a **different inode** before `fstat`. Same-inode candidates still
   require actual native device/inode comparison; their native errors fail.
   Do not filter by raw mount IDs: provider namespaces/bind aliases can differ.
4. Require exactly one unsigned-decimal `ino` header, allowing all 64 bits.
   A zero unrelated inode is valid metadata, not an admitted reference. Missing,
   duplicate, empty, signed, nondecimal, internally spaced and overflowing values
   fail rather than yielding a false zero count. Both modules now have explicit
   parser controls.
5. Close every duplicate and metadata reader. Only a duplication `IOException`
   wrapping `ErrnoException(EBADF)` for an already-closed original is ignored;
   metadata access/parse, other native errors and close failures propagate.

IO calibrates actual FileProvider regular descriptors and the actual reliable
pipe before transfer; provider pipe metadata reports that calibration. Picker's
DocumentsProvider calibrates the real descriptors before transfer, and the base
FileProvider path is additionally calibrated through a real received read-only
descriptor closed before the library operation. The latter is extra test setup,
not a production read. A direct received-descriptor versus caller-path identity
assertion is still useful; the retained-source integration must demonstrate a
nonzero matching count instead of assuming cross-process identity.

Both native controls now hold two distinct real files at actual offsets 2 and 1,
unlink the second while it remains open, demand repeated exact detection without
changing offsets, then demand zero after close. The IO control also retains real
pipe counts **2 → 1 → 0**. Two simultaneous descriptors for the *same regular
file* are not yet a dedicated control. The parser streams all fdinfo lines; it
does not log them, but no general hostile/overlong-input bound or actual
inaccessible-header/same-inode protected-collision test has been established.

These static repairs alone prove neither permission nor a working lifetime
measurement. A focused native/control diagnostic must precede any whole-suite
rerun; it cannot substitute for actual provider IPC, pipe error, public saver or
hardlink cases. New results are additive; earlier failures remain preserved.

### Focused diagnostic: one native control actually executed

The [first focused command](evidence/gradle/first-android-descriptor-controls.summary.json)
exited **0** after **96.02 seconds**, with all **688** captured inputs unchanged.
The [independent XML/input/APK review](evidence/io/android-device-first-probe-control-results.json)
confirms **one executed test, one pass**:
`nativeDescriptorProbeCountsFilesAndPipeEndsWithoutLeaksOrOffsetChanges`.
This demonstrates calibrated local-file/deleted-open-file detection, unchanged
offsets, real pipe counts **2 → 1 → 0**, and no retained probe duplicates on this
software Android 15/API 35 device.

The command requested **two** methods through a comma-separated class/method
filter, but `fdInfoParserAcceptsUnsignedInodesAndRejectsInvalidRecords` is absent
from the fresh XML. It remains **unexecuted**, not silently counted as passed;
the selection discrepancy needs investigation. Successful use of the parser by
the native control is not execution of its malformed-input boundary test.
No production IO read/provider IPC/error/cancellation, picker control/provider/
Activity, or WebView case was selected. A whole-suite or immutable-candidate
pass is not established. The test-only private data-class constructor also
emitted a generated `copy()` visibility warning (future Kotlin 2.5 error), not
a compilation failure; it remains a source follow-up under the freeze policy.

The [IO development record](IO.md), [baseline findings](../audit/findings/IO.json)
and [current IO resolutions](resolutions/IO.json) retain their own disposition
and evidence. These tests do not silently change any finding to `verified`.

### Hardlink acquisition: confirmed app-domain policy denial

The [additive policy review](evidence/io/android-device-hardlink-policy-review.json)
checks the **preserved third-run** per-test log, not an in-flight rerun. Its
selected native audit event denies **`link`** from `untrusted_app` to the
fixture's `app_data_file`, with matching application categories and
`permissive=0`. The fixture already lives under the test application's private
`Context.cacheDir`. `actualHardLinkIsNotTruncatedOrDeleted` fails at `Os.link`
(historical line 69, current line 90), **before either library identity or writer
call**. This is an observed fixture-acquisition limitation, not evidence that the
library truncated the original.

Android 15 AOSP `private/app_neverallows.te:105–111` explicitly forbids untrusted
apps from hard-linking `file_type:file`; ordinary `create_file_perms` also omits
`link`. The cited public tag is source context, not an extraction of this image's
exact compiled policy. Changing the ordinary app path to `filesDir`/`codeCacheDir`
or swapping Java/native link wrappers is not a justified repair. No SELinux
override, label/permission change, privileged provisioning, fake identity,
assumption-based skip or expected-denial-as-hardlink-success was introduced.
The original test method and failed evidence remain intact.

The separate [run-as source review](evidence/io/android-hardlink-runas-source-review.json)
finds no ordinary `run-as` provisioning escape: `runas_app.te:4` invokes
`untrusted_app_domain(runas_app)`, whose macro assigns `untrusted_app_all`, included
in the same hardlink `neverallow`. `seapp_contexts:225–226` selects that app
domain for `fromRunAs`; debuggable status and matching UID do not remove the rule.
This is public AOSP source evidence, not a `run-as` execution or an exact image
policy extraction. Externally pre-existing hardlinks remain a possible defensive
input; trusted external provisioning would require a separate, authorized and
provenance-controlled harness, not a waived gate or an ordinary `run-as` retry.

Existing real symlink/`./` aliases and tree/single-document URI aliases already
have separate cases. They normally use earlier canonical-path/document-ID
shortcuts; **content URIs have no production descriptor-identity branch**.
Repeating them cannot certify the file branch's final device/inode comparison
or genuine hardlink behavior. A future, separate OS bind-alias fixture may use
the platform's documented `/data/data` → `/data/user/0` relationship **only for
this application's own file**, with actual readable regular-file, unequal
canonical-path and identical nonzero native device/inode preconditions before
the library call. It remains an unimplemented, unexecuted proposal, not hardlink
equivalence or a reason to remove the hardlink gate.

At this review checkpoint, all **12 device-source hashes** are held. A new full
run is expected to execute **17 IO + 25 picker = 42 cases**: 33 authored methods
plus nine inherited common methods. The lead runs it without selection filters
or skips; no result is claimed here. Parser selection, picker probe/provider
calibration and complete production methods still need their own fresh results.
The old emulator plan and terminated supervisor handoff were inspected only as
historical data; no old PID or lifecycle script was executed by this reviewer.

### Fourth diagnostic: scoped IO results, failed metadata precondition, timeout

The immutable [device004 archive](evidence/android-device-004/archive.json) and
[independent IO review](evidence/io/android-device-fourth-io-review.json) bind
**691 equal before/after input hashes**, 21 archive-manifest entries, seven
raw/archive metadata pairs, 35 quarantined historical files and all 17 final
raw/sanitized testcase identities. All **165 current owned inputs**, including
the **12 device-source files**, still match. No filters or skips were introduced.

| Scope | XML-confirmed cases | Passed | Failed | Unverified requested cases |
|---|---:|---:|---:|---:|
| IO authored device methods | 12 | 11 | 1 | 0 |
| IO inherited common methods | 5 | 5 | 0 | 0 |
| Picker, including four common methods | 0 | 0 | 0 | 25 |

The bounded Gradle command exited **143 after 840.55 seconds** for its time limit;
the guard wrapper returned **1**. IO's final XML was emitted within that command
interval. The picker task started, but no final picker XML exists: unreported
execution is unknown, **not 25 skips or passing cases**. The original hardlink
failure remains preserved; device004 supplies no new hardlink, picker parser,
picker probe, saver-provider or public Activity result.

IO's **native descriptor control and strict parser control both passed**. The
complete production cases now verify whole-read closure across a real provider
process; a nonzero retained-source descriptor before and after EOF, followed by
zero after explicit close; unknown-size overrun and empty/exact-boundary reads;
both actual reliable-pipe error paths; already-cancelled no-open behavior; and
16 success/consuming-failure pairs without accumulating source descriptors.
The real provider calibrates regular-file and FIFO `fdinfo`/`stat` identities.
These are complete passing methods, unlike earlier partially reached assertions.
Same-regular-file duplicate **2 → 1 → 0**, inaccessible-header and same-inode
protected-collision controls remain separate gaps.

`knownOversizeIsRejectedBeforeAnyNativeStreamIsOpened` failed at
`KmpFileDeviceTest.kt:163`: expected metadata **64**, observed **null**. Its bounded
read, zero-open and zero-descriptor assertions at lines 165–168 were **not
reached**. The private per-case log records a `DocumentFile` null-cursor warning
and provider process startup, signal-9 exit and restart in the same case window.
It does not establish who killed the provider or why the size query returned
null. Do not label this a proven library truncation, an emulator-only defect or
a successful known-size precheck.

The [static dependency review](evidence/io/android-device004-metadata-static-review.json)
confirms that `DocumentFile.isDirectory` queries `mime_type`, while the cached
FileProvider supports only display-name/size columns. Its zero-column warnings
also occur in **two passing cases**, including the Unicode metadata case that
returns the correct three-byte size. This mismatch is not sufficient evidence
for the provider death or the failed size assertion. No source patch, retry or
weakened assertion has been applied on that inference.

The [local artifact supplement](evidence/io/android-device004-local-artifact-review.json)
checks two APKs, four merged/packaged manifests and embedded manifest identities.
Both APK modification times fall within the run, but post-run local hashes are
**not installed-byte attestation**. No extra tests follow from APK assembly.
The archived lifecycle receipts report Enforcing API 35/x86_64 and completed
task-owned cleanup. The original paused watchdog's `booted=false` does not
contradict its successor's observed boot. Emulator exit **-11 during requested
teardown** remains a separate runtime failure, not a library result or a clean
engine-shutdown claim. This reviewer executed no lifecycle script or Android
command. All earlier failed evidence and native/immutable-release gates remain.

## What is actually native, and what is a fixture?

| Boundary | Test implementation | Important limit |
|---|---|---|
| File URIs and identity | Actual Android `ContentResolver`, `Os.stat`, `Os.link`, `Os.symlink` and application-cache filesystem | No Robolectric stat shadow, fabricated device/inode values or host filesystem substitution |
| FileProvider reads | Manifest-registered AndroidX `FileProvider`, private and in a separate process of the test application's UID | Synthetic cache files only; not a cloud provider, cross-UID grant or real user-selected document |
| Unknown size | FileProvider subclass delegates real opens, calibrates the returned native regular-file descriptor and returns null size metadata | Deliberately controlled provider metadata, to force the production consuming-bound path; calibration is test setup |
| Failing read | A real `ParcelFileDescriptor.createReliablePipe()` receives an actual source prefix and `closeWithError()` from the provider process | Intentional native provider error, not a faulty network or storage device |
| Saver documents | Manifest-registered `DocumentsProvider` protected by `MANAGE_DOCUMENTS`; native descriptors, real `DocumentsContract.createDocument`/deletion and native close listeners | Deterministic provider fixture; it does not establish behavior of DocumentsUI or other providers |
| Alias read denial | Test provider rejects the read of its designated synthetic document | Injected access revocation; assertions check no output open or delete follows |
| Public saver | Directly mounted public `rememberFileSaverLauncher`, actual `ComponentActivity` registry, actual child Activity and framework result | A non-blocking instrumentation monitor changes only the selected destination Activity component; no system save-sheet interaction |
| Restoration | Real host `Activity.recreate()` while the child Activity is open, then a real result | Activity saved-state reconstruction, **not OS process death** or persistence of cross-UID URI permission |

The Activity routing hook always returns `null`; it never supplies a synthetic
`Instrumentation.ActivityResult`, replaces `ActivityResultRegistry`, or calls
`dispatchResult`. The fixture Activity calls normal `setResult` and `finish`.
The test preserves the outbound action/name/MIME/category for assertions before
choosing the explicit test Activity. This is a library integration test host,
not one of the sample applications.

The [inspected AGP 9.4.0 bytecode](evidence/io/agp-device-identity-inspection.json)
for `KmpAndroidTestImpl.getTestedApplicationId` delegates to `getApplicationId`,
indicating a self-instrumenting library test APK.
Tests additionally assert the actual test/target package identity, component UID,
private FileProvider settings and a different provider PID. Source inspection is
not substituted for those runtime assertions.

## Coverage inventory

### IO: `KmpFileDeviceTest`

1. Whole-array read across a real provider process returns all 131,079 bytes and
   leaves no descriptor for that source in the test process.
2. Returned `RawSource` retains a native descriptor until its caller closes it,
   including after EOF; explicit close removes that descriptor.
3. Unknown-size oversized content throws instead of returning a truncated array;
   the opened descriptor closes and source content remains unchanged.
4. Known oversized metadata rejects before the provider opens any stream.
5. Zero-length and exact-limit unknown-size files return the complete contents
   and close their streams.
6. Unbounded read propagates a genuine reliable-pipe read error and closes the
   transferred pipe descriptor.
7. Bounded read also propagates that actual read error and closes the pipe.
8. An already-cancelled coroutine never opens a provider stream.
9. Sixteen success/consuming-failure cycles do not accumulate source descriptors.
10. A Unicode content reference keeps its URI/name/type/size, does not invent a
    filesystem path, and cannot delete caller-owned content as a temporary copy.
11. The native-probe control detects two distinct open files, including one
    unlinked while open, without moving their actual offsets; probe duplicates
    close, and real pipe endpoints are observed as 2/1/0.
12. The parser control accepts zero/maximum unsigned-64 inode headers and rejects
    missing, duplicate and malformed records rather than implying no descriptor.

`DeviceDescriptorProbe` enumerates **only the test process's** `/proc/self/fd`
numbers, then uses calibrated fdinfo inode filtering and actual device/inode
matching on owned native duplicate handles, as detailed above. It does not log
an FD dump or inspect other applications. An
inaccessible descriptor table, unavailable identity or unexpected native error
fails verification instead of being treated as an empty-success result.
This measures the referenced descriptor lifetime, not heap, bitmap or whole-app
memory performance. The real provider-error producer also reports completion and
its own success independently of the expected consumer error.

### Direct saver: `SaveDestinationDeviceTest`

- Distinct real files have nonzero/different native identities, copy every byte
  and close input/output descriptors.
- A real hard link, real symbolic link and canonical path alias preserve both
  source content and names without truncation or deletion.
- Zero-length content is separate from unavailable identity: two real empty files
  remain distinct, and copying an empty source intentionally truncates a distinct
  nonempty destination.
- A missing source cannot authorize overwrite/cleanup of an existing destination;
  an absent destination can be created only after establishing source identity.
- A real `ENOTDIR` result is not treated as destination `ENOENT`.
- Real tree/single document aliases only open for read and receive no write/delete.
- Read denial on an identified alias produces failure without touching it.
- A real FileProvider-to-DocumentsProvider copy closes both owned resources.
- A failed distinct source deletes only the destination created through the
  fixture's actual `DocumentsContract` API, without opening it for write.
- The positive probe control requires the leak assertion to reject two distinct
  known-open files with the expected diagnostic, including an unlinked open file,
  preserves their actual offsets, and requires zero after their handles close.
- The parser control rejects missing/duplicate/malformed kernel inode headers and
  retains the full unsigned-64 range, without turning parse failure into success.

An inode of zero generally cannot be requested from the real application
filesystem. **No native inode-zero scenario is claimed.** The explicit
`InconclusiveSaveIdentityTest` host fixture remains separate policy evidence, not
device evidence. The new native zero-content case must not be mislabeled as an
inode-zero test.

### Public saver: `FileSaverActivityDeviceTest`

- Byte save after a true Activity round trip, with outbound contract fields
  inspected and real destination write/close.
- Public file overload streams from FileProvider without moving the original.
- Null byte payload intentionally creates a real empty document.
- Framework cancellation delivers one null result and releases the next launch.
- A second launch while the real child Activity is foreground reports one error
  without replacing or launching over the accepted request.
- A returned alias of the original is not opened for write or deleted.
- URI payload survives real host Activity saved-state recreation before result.
- Byte payload lost by that reconstruction reports an error, not successful
  empty output; only the newly created document is cleaned up.

The public Activity suite requires **API 26+** for the instrumentation routing
hook. That test-only requirement does not raise the library's minimum SDK.
The direct IO/identity tests use APIs available within the library's Android
minimum. Common tests inherited by a device task are additional task executions,
not extra newly authored functions.

## Execution and evidence requirements

Only the lead schedules Gradle/emulator work. Discover the actual device compile
and connected-test task names from the configured AGP target; do not infer a pass
from directory presence, resource processing, manifest generation, a successful
host task or zero tests. APK compilation and installation alone are not test runs.

For the eventual diagnostic, retain the exact command, source revision/input
hashes, exit status, fresh test reports, actual APK manifest identity and hashes,
and actual device API/ABI. Report filtered, skipped, timed-out and failed cases
separately. Inspect the merged manifests to ensure fixture providers, activities
and cache paths are present only in the test APK, never distributed in the
library artifact. File cleanup only touches each test's randomly named subtree.

### Observation-monitor diagnostic and repair

An additive [read-only framework inspection](evidence/io/android-device-monitor-reuse-risk.json)
records the framework behavior underlying a fixture race, not a library defect.
Android 15 calls the observation monitor after both Activity creation and resume.
If the first wait consumes the creation match before resume records the same
Activity again, a later launch could receive that leftover first Activity from
the reused monitor. The existing `isFinishing` assertion would reject a stale
finished Activity. The second device diagnostic failed that exact assertion on
the second launch; the source repair retains it.

The authorized bounded follow-up is **one new class-specific observation monitor
per `launchAndAwait` call**, registered before the public launch and removed in
`finally` after waiting/asserting. Keep teardown removal as fallback. The separate
non-blocking **routing** monitor remains installed for the whole test, still
returns `null`, and still leaves launch/result delivery to the real framework.
Do not change test bodies, actual child completion, lifecycle reconstruction or
provider operations. This repair was authored only after the second diagnostic's
input/hash receipt was finalized. In the third diagnostic the complete
cancellation/second-launch case passed; the other five Activity cases that failed
in their descriptor probe still remain failures. Source holds remain in force
outside the lead's scoped correction windows.

Remaining checks include genuine system picker interaction, cross-UID grants and
persistable permission restoration, cloud/provider cancellation, OS process death
during a write, cancellation during a blocked native read, older API public
ActivityResult behavior, physical-device filesystems and immutable-candidate
reruns. The actual software emulator is not a substitute for all of those checks.
Verification Actions are authorized by the 2026-10-26 owner decision; work
without subagents. Publication/deployments remain gated under
[containment](containment.md), and actual device gaps are not waived.
