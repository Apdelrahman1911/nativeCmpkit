# Independent IO / Android saver safety cross-review

Reviewed on 2026-10-24 by the geo/metadata owner, independently of the IO
implementation owner. This is a **read-only source/dependency-bytecode and
archived-result review**. The reviewer did not run Gradle, modify IO/picker/build
sources, or mutate GitHub. Baseline findings remain unchanged.

## Revision and evidence boundary

- Original finding/source baseline:
  `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`.
- Current source base: `94d2492e99d5cbc060409d94d9f88febd06222d5`, plus
  **uncommitted** implementation/test changes, not an immutable release revision.
- Primary Android source snapshot:
  `docs/development/evidence/gradle/first-native-and-third-android-host.inputs.json`.
  The failed command's receipt records all 207 selected inputs unchanged during
  the run. Source line references below describe that held input, before the IO
  owner's subsequently authorized diagnostic edits.
- Reviewed baseline records: IO-001 through IO-006, IO-008, IO-010, IO-014,
  IO-018, IO-019 and IO-020. Deepest review: Android pending-save state,
  pre-truncate identity, stream/cleanup ownership and restoration. iOS/Desktop
  high-priority fixes were cross-checked at their allocation/lease/staging/
  replacement boundaries; this is not a second complete native UI audit.

### Results independently inspected

The reviewer parsed actual testcase nodes and independently checked report SHA256
values against the lead's summaries; these are not new test executions.

| Receipt | Inspected scoped outcome | What it does not prove |
|---|---|---|
| `second-io-perm-and-fourth-ui.summary.json` | IO Android host: **21 cases / 5 XML**, zero failures/errors/skips; picker desktop: **43 / 10**; Coil desktop: **3 / 1**, also zero failures/errors/skips | Combined command failed elsewhere. No physical provider, Apple UI, Android process restart or immutable revision evidence. |
| `first-native-and-third-android-host.summary.json` | Picker Android host: **30 cases / 7 XML; 28 passed, 2 failed**, zero errors/skips | **Not a passing picker suite.** Both file-copy/restoration failures need a new run after diagnosis. |
| `first-ios-klib.verification.json` and matching log hash | IO/picker production and test iOS Simulator Arm64 KLIB tasks executed successfully; Coil production KLIB compiled | **Zero native test executions.** No native linking, simulator/device behavior, scope enforcement, or ASan proof. The combined command exited 1 in other modules. |

All receipt names above are under `docs/development/evidence/gradle/`. An
assertion/helper/provider fixture is not a real SAF provider or kernel test.

## 1. Confirmed host failure: placeholder inode identity produces a false self-copy

**Classification:** confirmed host/test-harness interaction, verification blocker;
not a demonstrated Android device data-loss defect. **Priority:** High for keeping
the release gate closed; the production/device severity of unsupported identity
metadata is not established by Robolectric.

### Observed failure and exact path

Two fresh XML cases failed with expected `[9, 8, 7]`, actual `[]`:

- `FileSaverLauncherTest.aFileIsCopiedWhenTheResultArrivesInALaterComposition`,
  `calf-file-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncherTest.kt:57–69`.
- `SaverRestorationTest.rememberedUriRequestSurvivesSavedStateRestore`,
  `calf-file-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/picker/SaverRestorationTest.kt:31–41`.

The result callback has completed before either content assertion. This is not
evidence that the tests merely forgot to wait for the copy coroutine. Both use
distinct existing `file:` source/destination files.

The reviewed `SaveDestinationIdentity.kt:16–24` compares canonical paths, then
accepts equality of `Os.stat`'s `st_dev` and `st_ino` without validating that the
identity is meaningful. The pinned Robolectric dependency supplies a placeholder
identity for every file:

- Coordinate: `org.robolectric:shadows-framework:4.16.1`.
- JAR SHA256:
  `a59802cffec783aa0e7df1489b0c2ce1126ef7cdedb940ffc378eb61e86958c8`.
- Read-only command: `javap -p -c -classpath <shadows-framework.jar>
  org.robolectric.shadows.ShadowLinux`.
- `ShadowLinux.stat(String)` constructs `StructStat` with **zero device and zero
  inode** (`lconst_0` at bytecode offsets 47 and 48). It derives length/mode/mtime
  from the host file but does not derive identity. The class annotation applies
  to `libcore.io.Linux`, `minSdk=26`; the picker test configuration uses SDK35.

Consequently two distinct test files are classified as the same file. In
`FileSaverLauncher.android.kt:115–131`, `sameSource=true` opens the source only
for readability and deliberately skips opening/writing the destination; lines
134–136 then mark completion. The observed empty destination is therefore
consistent with the identity branch, **not a recurrence of the baseline local
`remember { null }` capture defect**. The byte-array export bypasses this identity
branch and its recomposition test passes.

### Required correction / verification

The IO owner was informed of this dependency-bytecode evidence before editing.
The agreed direction is:

1. Supply an explicitly disclosed host filesystem-backed stat shadow for the
   affected tests (real `unix:dev,ino`), rather than substituting the save method,
   weakening byte assertions, or disabling self-copy protection.
2. Include distinct files as a negative identity test and real hard links as a
   positive identity test. A fixture that only proves aliases compare equal
   cannot detect an implementation that labels **everything** an alias.
3. If production treats an unavailable/zero inode or failed stat as inconclusive,
   **refuse** destructive work rather than interpreting it as either equal
   (false successful no-op) or different (possible truncation). Preserve the
   existing `identityChecked=false` cleanup guard when identity evaluation fails.
   Only a genuinely absent destination can take a creation path; source absence
   or failed source identity must not authorize output/deletion.
4. Rerun the actual Compose and restoration tests, identity positive/negative
   cases and cancellation/error ownership cases. The planned correction is not
   a passing result, an Android kernel test, or a new universal identity proof.

## 2. Positive source checks: Android saver ownership and destructive ordering

The original baseline `FileSaverLauncher.android.kt:31–32,42,65–73` was inspected
with `git show`: it remembered null rather than a shared mutable holder and
unconditionally emitted success after nullable stream branches. The replacement
addresses those specific source defects:

- `PendingSaveSource.kt:14–34`: one holder distinguishes waiting/busy. `consume`
  clears the payload and ignores duplicate results; overlap remains rejected
  while writing. `finish` makes the holder reusable. `FileSaverLauncher.android.kt:61`
  remembers this holder, and lines 55–57 keep current callbacks/settings.
- `PendingSaveSource.kt:36–53`: URI references are saved as strings; byte content
  becomes an explicit `bytes-lost` marker rather than a large Bundle payload.
  A missing required source reaches a typed error at saver line 114. Intentional
  `bytes=null` becomes a deliberately empty byte source at line 100.
- Saver lines 69–75 enter `finally` undispatched, finish ownership before calling
  application code, and do not catch application callbacks as operation errors.
  Launch failure only clears a request this attempt actually accepted (79–96),
  so rejecting an overlapping attempt does not discard the first request.
- Saver lines 115–129 evaluate known file identity **before** `wt` output access.
  Identified self-copy still opens the input for readability and never opens the
  output. Source failure cannot be converted into a successful empty write.
- Both input/output streams have `use` ownership. Completion is set only after
  write, close, and an activity check (120–136). `copySaveContent:154–162` uses
  bounded 64 KiB chunks and checks coroutine cancellation between blocking reads.
- Cancellation is rethrown (138–139); cleanup runs non-cancellably only when
  identity was checked and the target is not the identified source (142–150).
  Provider deletion failure is best-effort, not reported as successful cleanup.

These are source checks, **not proof** of every required provider failure or
disposal interleaving. In particular, a blocking resolver call need not respond
promptly to coroutine cancellation, and provider deletion can hang or fail.

## 3. Alias identity is conditional, not a transaction or an arbitrary-provider proof

**Classification:** risk / explicitly bounded contract, not a newly reproduced
provider exploit. **Priority:** High verification requirement for destructive IO.

The reviewed identity helper handles URI equality, canonical file paths,
filesystem device/inode pairs, same-authority document IDs across tree/single
forms, and provider canonicalization hints (`SaveDestinationIdentity.kt:14–41`).
The original three identity tests (`SaveDestinationIdentityTest.kt:34–69`) cover
tree-document vs single-document, unreadable alias preservation, and file
symlink/canonical-path aliases using actual resolver streams and owned host files.

It does **not** establish identity for mixed `file:`/`content:` references
(line 26 returns false), noncanonical opaque provider aliases, or mutable provider
mappings between the check and the later open. Canonicalization failure/null is
not evidence of different physical storage. Pure document-ID parsing also assumes
the authority/path actually obeys a DocumentsProvider identity namespace, rather
than any arbitrary provider that happens to use a `/document/` path.

The current saver relies on `ACTION_CREATE_DOCUMENT` returning a **new**
destination. That documented assumption bounds the risk: no compliant-provider
self-alias failure was demonstrated here. It must not be upgraded to a promise
that existing source data survives an arbitrary/nonconforming provider that
aliases its destination to that source. Once such an unknown alias is opened
`wt`, an already-open input descriptor does not prevent truncation, and the
failure cleanup could delete the underlying aliased document.

Required follow-up tests: canonicalization success/null/error; distinct IDs and
different authorities; mixed scheme aliases under a controlled real provider;
hard links; identity query revocation; source/destination replacement between
check/open; and cancellation immediately before/after the identity boundary.
Document exactly which cases are rejected versus supported. Do not add blanket
deletion to compensate for an ambiguous alias or cleanup failure.

## 4. Important remaining Android execution gaps

**Classification:** unverified required contracts, not confirmed runtime defects.

1. **Resolver/close failures and cancellation.** Current saver tests exercise
   normal resolver file streams and readability rejection, but not null output,
   a stream failing after partial bytes, disk-full/failing close, cancellation
   before first IO dispatch, during copy or immediately after output close, or
   provider deletion refusal. Add controlled resolver/descriptor transports to
   assert exact open/close/delete counts and no successful result on failure.
   Do not use tests of an independent copy helper as the whole integration proof.
2. **Real read path.** Android `KmpFile.android.kt:37–45` correctly delegates to
   `InputStream.use`. `ReadOwnershipTest.kt:11–31` verifies a throwing read plus
   suppressed close failure and a successful empty read. It does not invoke the
   actual `ContentResolver.openInputStream` failure/null/revocation path or the
   Coil failed-fetch pipeline. IO-020 should not be closed on these two helper
   tests alone without dispositioning its remaining required tests.
3. **Restoration vs process death.** `SaverRestorationTest` uses real Compose
   `StateRestorationTester` but retains its in-memory
   `RecordingActivityResultRegistry` (lines 24–26,54–60). It does not recreate the
   Android process, registry transport, or URI grants. URI string restoration is
   not a persisted permission. Android `KmpFileBookmark.android.kt:10–45` exposes
   persistence explicitly; the grant-store tests are Robolectric-shadowed.
4. **Whole-launcher disposal / retention.** The saver has no disposal hook that
   clears a still-waiting holder before any result/write coroutine starts.
   A consumer retaining the retired launcher also retains its captured
   `launchSave`/holder and byte source (saver 79–103; pending 15–24). This is a
   source-visible retention risk **conditional on the caller retaining that
   object**, not a measured leak in normally collected compositions. Consider
   clearing only that disposed holder; verify restoration ordering and do not
   deliver callbacks to disposed UI. Forced-GC assertions are not required proof.
5. **Launch snapshot / callback policy.** Picker registrations use one saved
   pending limit and consume before delivering (`FilePickerLauncher.android.kt:47–62,103–115`).
   Add actual single/multiple/photo-fallback limit changes, overlapping launch,
   callback reentry/throw, duplicate/late result and cancellation-after-recreation
   integration cases. Basic document success/missing-app tests do not cover them.

## 5. Metadata and streaming checks (IO-008/010/014/019/020)

- Android file metadata uses file paths; content metadata preserves tree grants
  and distinguishes a tree child from the root (`KmpFile.android.kt:104–124`).
  `DocumentTreeMetadataTest.kt:24–45` passes real DocumentFile/ContentResolver
  queries against an in-process provider for root, child and missing ID. It does
  not test ExternalStorageProvider/Downloads/cloud providers or restarted grants.
- `getPath` now returns a path only for `file:` and `toUriString` retains the URI
  (`KmpFile.android.kt:52–61`). This is a documented observable correction, not
  an ABI certification or a reason to guess a path from a content URI.
- Common `isFile` now requires existence (`KmpFile.kt:121,207`), repairing the
  missing-path false positive. Its contract remains **existing non-directory**,
  not a proven regular-file type test. Device nodes/FIFOs/sockets and unavailable
  MIME metadata must not be described as regular-file certification.
- Android `source` transfers stream closure to the caller
  (`KmpFileSource.android.kt:8–10`). Common bounded reads hold `use` across
  cancellation/yield (`BoundedRead.kt:26–49`). Caller code must keep open/use/close
  in one owned background operation; merely moving an acquired resource through
  a cancellable dispatcher handoff can lose ownership outside this API.
- iOS `SecurityScopedAccess.kt:9–14` atomically releases only its own successful
  start. `KmpFileSource.ios.kt:13–31` closes the lease on open failure and after
  stream close, including failing close. Local sandbox access need not require a
  successful security-scope start. No real scoped-provider test ran on Linux.

## 6. High-priority baseline disposition cross-check

| Finding | Current implementation boundary independently checked | Still required / not established here |
|---|---|---|
| **IO-001** | iOS `KmpFile.ios.kt:72–80` uses one checked length for allocation/copy and returns before `addressOf(0)` for zero bytes. `BoundedRead.kt:13–17` rejects over-Int lengths; common tests cover limits without huge allocation. | Actual NSData round trips, missing/unreadable native input and guarded-buffer/ASan/Coil integration. KLIB compilation is not native execution. |
| **IO-002** | Shared remembered pending holder, explicit lost-byte restoration, busy/consume/finish and current callbacks replace the baseline local reference cell. Byte recomposition test passed; two URI-copy cases currently fail for the host identity interaction above. | Corrected URI cases must execute successfully; true Activity/process/registry restoration, overlap/disposal and error/cancellation cases remain separate requirements. |
| **IO-003** | Desktop `PlatformFilePicker.kt:16–45` creates/uses/destroys handles inside one IO operation. Rust `registry.rs:24–56` leases Arc values with monotonic IDs; `lib.rs:266–293` no longer manufactures static references from raw Box addresses. | Real native show/config-build/disposal timing, ASan/Valgrind, native parent-window close/recreate. **IO-023 remains a distinct unresolved parent-window lifetime/thread-affinity blocker.** |
| **IO-004** | Desktop `AtomicSave.kt:24–50,65–81` checks same-file identity, stages into a sibling file, closes before atomic replacement, checks cancellation and refuses non-atomic fallback. Relevant desktop suite passed; no new desktop failure found in this boundary review. | Crash durability/fsync and real native dialog paths are not established; preserve read/write/close-failure, symlink/hard-link and cancellation evidence without equating helper success to GUI verification. |
| **IO-005** | iOS saver uses named private staging for bytes/NSData/file, explicit `asCopy=true` (`FileSaverLauncher.ios.kt:66–125`), checked native writes/copies and owned cleanup (`Staging.kt:84–119`). | Actual export/source survival, interactive dismissal/disposal, disk-full staging, exact returned names and external destination access. No Apple runtime test was executed. |

## 7. Conclusion and handoff

The source repairs are materially stronger at the reviewed ownership boundaries.
The independent review found an actionable **real failing-host evidence problem**
caused by stat placeholder identity, not grounds to weaken destructive-IO
protection or claim the original pending-source bug remains unchanged. The IO
owner is handling source/test corrections; this reviewer made none.

Keep original findings open/partially verified until required tests and immutable
revision evidence are reviewed. No universal provider-alias safety, native
resource-leak absence, process restoration, physical UI behavior, or release
readiness is established by this report.

### Selected held Android input hashes (before the diagnostic correction)

Full repository-relative paths and all selected hashes are in the input receipt.

| File | SHA256 |
|---|---|
| Android `FileSaverLauncher.android.kt` | `3dde1e48d2d44f7abcfcef4897bf49094b8acafce99e4b987a5a772aa470e5a8` |
| `PendingSaveSource.kt` | `55ff5487f342b60915e41bb6acf9536e87dd9eca1a1798b6a795ff7622cd25a1` |
| `SaveDestinationIdentity.kt` | `1015c47707ca25e03a76b1923cc119e86f9b779c93f5b5740a48243f050a1316` |
| `FileSaverLauncherTest.kt` | `b5699782b3d4ccc31bbd2749853158723ab5bbb1ebbf813a570bca9bdfa54e2b` |
| `SaverRestorationTest.kt` | `52fb6975c3fae36b652959c52c88f0c1f1206c62b858c58ac3ced639190ca551` |
| `SaveDestinationIdentityTest.kt` | `15aad3b8ff592125d53c1eeb359dc0a3b9ebd3cf428d9d50668cd02dd5b4bb20` |

## 8. Read-only correction review — 2026-10-24 19:59 UTC

The IO owner has refrozen a scoped correction for the lead's next run. This
addendum inspects that correction; it **does not replace the failed evidence
above or claim the retry passed**. No IO/build file was edited by this reviewer.

- `SaveDestinationIdentity.kt:28–38` now requires nonzero source and destination
  inodes. Source-stat errors propagate. Only destination `ENOENT`, after a valid
  source identity, means a new file can be created; other destination errors and
  an unavailable inode refuse the operation. The unchanged saver sets
  `identityChecked=true` only after this helper returns (`FileSaverLauncher.android.kt:115–117`),
  so an identity error cannot authorize output or cleanup. Equal URI/canonical
  path shortcuts remain safe no-write paths with subsequent source-read checks.
- `HostFileStatShadow.kt:14–37` obtains **real host** `unix:dev,ino` attributes,
  maps missing/denied paths to the corresponding errno and delegates other stat
  metadata to Robolectric. The null-path inherited `fstat` fallback is explicitly
  delegated, not assigned invented identity. The fixture is disclosed as Unix
  host-only and its annotation applies from API26; the current suites use API35.
  This does not test Android's kernel/filesystem stat behavior.
- The three saver/identity suites use this host adapter. The original failed
  copy assertions still require `[9, 8, 7]` after their result waits
  (`FileSaverLauncherTest.kt:59–71`, `SaverRestorationTest.kt:33–42`).
- Four added identity cases (`SaveDestinationIdentityTest.kt:76–132`) cover real
  distinct-file identities and full copy, a real hard link, missing source with
  existing destination preservation, and absent destination creation. These
  positive **and negative** cases avoid an all-alias implementation passing the
  identity oracle.
- `InconclusiveSaveIdentityTest.kt:23–37` uses an explicit zero-identity shadow
  and requires an error plus unchanged source/destination bytes. It exercises
  the **source-zero** refusal; destination-zero after a valid source, denied
  stat, and non-ENOENT destination-stat errors remain separate unexecuted cases.
  Preserved file-URI bytes do not by themselves count attempted
  `DocumentsContract.deleteDocument` calls; cleanup suppression is a source
  check here, not an instrumented provider-delete assertion.

The revised file-path logic follows the agreed fail-closed direction. Section 3's
bounded provider-identity contract and section 4's cancellation, resolver failure,
disposal and true restoration gaps are unchanged. Await actual retry XML and
input receipts before claiming these new tests or corrected copies succeeded.

### Correction inputs independently hashed for this addendum

Production helper path is under `calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/`;
the tests/fixtures are under the corresponding `src/androidHostTest/kotlin/` path.
The saver itself retains its preceding SHA256.

| File | SHA256 |
|---|---|
| `SaveDestinationIdentity.kt` | `1e8398f9720676082bbb2ca1508d0685d07267318352ec93ccea3c848247b370` |
| `HostFileStatShadow.kt` | `72037a8ea4b1f09577ea6d4e53d49f765c8ef2a02928a508c678631962809a5b` |
| `InconclusiveSaveIdentityTest.kt` | `f826f933b68578e81e3706350846fdd4bf95b21aa7609e029e93a98502dd669d` |
| `SaveDestinationIdentityTest.kt` | `dd1831fc9cfead33c41ea086bdde88944da9407d6592d649aebfa0e6e48ae775` |
| `FileSaverLauncherTest.kt` | `1968904a21110a67989a81682614dee6a857e8a40278d4351487d9a6605d83a1` |
| `SaverRestorationTest.kt` | `a0fcc323ce00316c52ce323dddffee3a8a421173cd9d376206a226e231202ff1` |
