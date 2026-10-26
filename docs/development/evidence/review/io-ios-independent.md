# Independent review: iOS IO, picker/saver and Coil

Reviewed **2026-10-24**, on `development/preview-hardening`, with base commit
`94d2492e99d5cbc060409d94d9f88febd06222d5` and the held, **uncommitted** development
sources. Reviewer: the history/architecture and earlier native-UI reviewer, not
the IO implementation owner. This is a source/evidence cross-review, **not a new
build, native test run, release receipt, or closure of the original audit**.

**Snapshot navigation:** The initial review and R1–R3 below preserve the sources
inspected at 20:09 UTC. The IO owner subsequently made narrowly authorized
corrections. See **Follow-up cross-review, 20:21 UTC** at the end for their
source-addressed disposition; do not apply the earlier KLIB success or earlier
line numbers to those changed files.

The lead assigned IO-001…005, iOS security-scope ownership, staging/source
preservation, native terminal/cancellation behavior, threading, and the authored
iOS regressions. No production source, test, build, GitHub, or workflow changes
were made by this review. No Gradle, Kotlin compiler, simulator or device command
was run. Baseline findings remain in `docs/audit/findings/IO.json`.

## Summary

- **IO-001's unsafe allocation/copy arithmetic is repaired in source.** The
  allocation and `memcpy` use one checked length; empty data returns before
  `addressOf(0)`; a failed Foundation read throws. Native Coil no longer reaches
  that read-all implementation.
- **IO-005's original-source move and UUID-prefixed filename are repaired in
  source.** All four saver input forms converge on a named, library-owned copy;
  export explicitly uses `asCopy = true`. This does not verify a real provider
  export or the cancellation lifetime of its staging file.
- Security-scoped streams, per-presentation delegate identity, duplicate-result
  rejection, limit-before-copy, and abandoned-photo-copy cleanup have meaningful
  ownership improvements. This review did **not** find a demonstrated leak in
  the `NSItemProvider` continuation handoff.
- **Three follow-ups remain:** a source-confirmed non-file-URL/local-path
  identity inconsistency, a saver presentation race across background staging,
  and native-dismissal/staging lifetime risks on disposal. The last two are
  source-supported **risks**, not reproduced Apple failures. See R1–R3.
- There are **51 authored iOS test functions** in the reviewed IO/picker test
  classes. They were compiled into test KLIBs in the inspected receipt, **not
  executed**. Desktop helper/bridge successes cannot certify Apple permissions,
  gestures, presentation, provider copying, or decoder cancellation.

## Evidence and revision boundaries

### Inspected existing commands/results

1. `docs/development/evidence/gradle/first-ios-klib.log.result.json` records the
   exact lead-run command. Its relevant targets were
   `:calf-io:compileTestKotlinIosSimulatorArm64`,
   `:calf-file-picker:compileTestKotlinIosSimulatorArm64`, and
   `:calf-file-picker-coil:compileKotlinIosSimulatorArm64`, with
   `--continue --max-workers=1 --no-configuration-cache` and the recorded
   compiler/JVM memory settings. This was a wider batch, not an independently
   successful three-target invocation.
   - `first-ios-klib.log:89,99,136,176,180` records execution of IO production/test,
     picker production/test, and Coil production KLIB compilation, respectively.
   - The **whole command exited 1**, with unrelated navigation `isArrayOf` and
     Bluetooth/WiFi mixed Kotlin/Objective-C inheritance compiler errors.
   - `first-ios-klib.verification.json` reports 222 selected inputs unchanged
     during that run and **zero executed tests**. No Apple link, test executable,
     simulator, device, or native UI was run.
   - The log's SHA-256 was independently recomputed and matches the verification
     record: `44d7316cfb49960551f93c1658d6b2d9d6a1e0bea114e49c6a5c3210e0c878c7`.
2. `second-library-desktop.summary.json` and its archived
   `TEST-com.mohamedrejeb.calf.io.BoundedReadTest.xml`: **5 tests, 0 failures,
   errors, or skips**. The XML hash was recomputed and matches the receipt.
   These exercise the actual common checked-length/bounded-reader code with
   `Buffer` and a test `RawSource`, not Foundation or UIKit.
3. `second-io-perm-and-fourth-ui.summary.json`, its command/result JSON, and its
   archived `TEST-com.mohamedrejeb.calf.picker.coil.KmpFileFetcherTest.xml`:
   **3 desktop tests, 0 failures, errors, or skips**. The XML hash matches the
   receipt. A real JVM file is fetched and consumed through the official bridge;
   a test `RawSource` proves explicit `ImageSource.close()` reaches the underlying
   `close`. The whole diagnostic batch exited 1 elsewhere. This is **not** a
   real Coil decode/failure/cancellation integration test on iOS.

### Current-source comparison, 20:09 UTC

A read-only Python SHA-256 comparison against `first-ios-klib.inputs.json`
covered all current Kotlin files under `commonMain`, `nonAndroidMain`, `iosMain`,
`commonTest`, and `iosTest` in the relevant modules:

| Module | Current Kotlin files | Match recorded input hashes |
|---|---:|---:|
| `calf-io` | 17 | 17 |
| `calf-file-picker` | 25 | 25 |
| `calf-file-picker-coil` | 3 | 3 |
| `calf-core` | 6 | 6 |

These **51 source files** and the **51 iOS test functions** are different counts
that happen to be equal; neither number is a runtime execution count.

Of 76 selected source/build/config files considered, five build/config hashes
now differ: root `build.gradle.kts`, `calf-io/build.gradle.kts`,
`calf-file-picker/build.gradle.kts`,
`convention-plugins/src/main/kotlin/Android.kt`, and
`gradle/libs.versions.toml`. Therefore the prior KLIB receipt establishes a
historical compile of the same reviewed source, **not a fresh verification of
the entire current dependency/build graph**. Later owner changes must be
compared again; this report must not be treated as a perpetual source freeze.

## Baseline-to-current assessment

Baseline references below are to
`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`, not current line numbers. The original
IO-001 and IO-005 files were also inspected with `git show`, independently of
their finding text.

| Finding | Independent assessment and limit |
|---|---|
| **IO-001** | Baseline iOS `KmpFile.ios.kt:35–41` clamps allocation but copies `data.length`, addresses element zero for empty data, and returns empty for failed reads. Current `:72–81` repairs all three branches. Common `BoundedRead.kt:12–18` checks the limit without a huge allocation. Desktop helper tests passed; the native memcpy/empty tests only compiled in the inspected receipt. No ASan/guarded-memory or iOS execution. |
| **IO-002** | Android pending-save/recomposition finding. Not independently reviewed by this iOS pass; refer to `io-android-independent.md`. Do not infer its repair from iOS results. |
| **IO-003** | Desktop/JNI creation/disposal/configuration lifetime. Outside this iOS pass; a Kotlin iOS KLIB or the atomic iOS session guard says nothing about Rust/JNI pointer safety. |
| **IO-004** | Desktop self-copy/deletion/truncation. Outside this iOS pass; source-preserving iOS staging does not establish desktop semantics. |
| **IO-005** | Baseline saver `:94–113,119–123,137–150` uses the original URL for file export, prefixes a UUID to data names, and omits explicit copy semantics. Current saver `:54–105,110–124` and `Staging.kt:21–32,84–108` use exact named staging for every input plus explicit `asCopy = true`. Source-addressed; actual export, destination reopening, disk-full and animation/disposal behavior remain unverified, including R2/R3. |
| **IO-006, iOS portion** | Staging write/copy booleans are checked; missing staging becomes `FilePickerException`; new overload separates `onError` from cancellation. Operation catches exclude ordinary asynchronous result callbacks. Failure details from `NSItemProvider` are still reduced to a generic failed-copy error rather than preserving `NSError` diagnostics. No disk-full/provider-failure integration run. |
| **IO-007** | A fresh document delegate and session terminal guard cover pick, cancel, duplicate and adaptive-dismiss branches. Photo checks the shared guard before either empty/nonempty processing. Controller identity prevents a late old callback becoming a new session. The baseline duplicate-result branch is source-addressed; actual interactive dismissal and disposal during native presentation are not proved, and R2/R3 remain. |
| **IO-008, iOS portion** | A successful scope start is closed once; synchronous operations and opened streams use appropriate distinct lifetimes. Bookmarks are additive, with explicit release. Local sandbox bookmark tests do not establish grants after a restart, stale resolution, folder descendants, revoked access, or third-party providers. This remains partial evidence, not a blanket persisted-access guarantee. |
| **IO-013** | Limits precede staging; cancellation/failure drops unreturned copies; returned copies carry explicit cleanup ownership. Photo provider copies happen before native callback return and unconsumed resumed values are cleaned. No live provider callback/cancellation test, OS-purge test, or permanent-storage guarantee. |
| **IO-014, iOS portion** | Names use decoded `lastPathComponent`; paths refer to readable copies and URI strings refer to originals. `fromUriString` rejects non-file schemes. The related direct-wrapper inconsistency in R1 remains. |
| **IO-017/018, iOS portions** | Current settings/type/mode are read at launch, not captured once, and in-flight work uses that snapshot; current result/error callbacks are read at delivery. `Multiple` validates positive-or-null limits. Native configuration helper tests cover two limits/representation modes and null-unlimited; no actual recomposition/presentation test executes this facade on iOS. |
| **IO-021** | Native Coil fetcher opens a stream instead of materializing encoded bytes. Read-all APIs document blocking/whole-content allocation, and an additive bounded overload exists. Actual peak-memory, decode-error/cancellation cleanup, and request-key/invalidation behavior remain unmeasured. |

## Implementation-level review

Paths in this section and R1–R3 are **current reviewed source**. For brevity:

- **IOi** = `calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/`
- **IOc** = `calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/`
- **Pi** = `calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/`
- **Pc** = `calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/`
- **Cc** = `calf-file-picker-coil/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/coil/`

### File content and ownership

1. `IOi/KmpFile.ios.kt:33–61` distinguishes a readable URL, original metadata URL,
   optional bookmark lease, and optional library-copy release closure. Only the
   attached closure can be invoked by `releaseTemporaryCopy`; it is atomically
   consumed once. Arbitrary original handles do not acquire deletion authority.
   Cleanup failure consumes the attempt too; `docs/development/IO.md` explicitly
   documents that this is not a retryable-delete API.
2. `IOi/KmpFile.ios.kt:72–81` reads `NSData` under a synchronous scope and then
   copies exactly `checkedByteArraySize(data.length)`. Foundation has already
   loaded the encoded content before the length check, and the Kotlin allocation
   adds another copy. This is **not** an OOM prevention guarantee for the legacy
   unbounded API. Zero returns before pin/address/memcpy. Native read failure is
   distinct from a legitimate empty file.
3. `IOc/BoundedRead.kt:26–52` prechecks known size, then owns the source through
   `use`. Its 64-KiB chunks and one extra byte distinguish at-limit EOF from
   truncation; `Long` arithmetic avoids `Int.MAX_VALUE + 1` overflow. It checks
   cancellation between reads, yields, rejects a no-progress zero-byte read,
   and closes on all exits. A blocking single read may still finish before
   cancellation is observed. The bounded helper does not reinterpret “suspend”
   as an IO dispatcher or promise decoded-image bounds.
4. `IOi/SecurityScopedAccess.kt:9–23` closes only its own successful start via a
   compare-and-set, so nested per-operation scopes do not deliberately stop a
   separately retained bookmark/stream lease. False from Apple's start call is
   allowed for app-local files; subsequent IO determines whether access works.
   `IOi/KmpFile.ios.kt:142–149` uses `try/finally` for synchronous blocks only.
5. `IOi/KmpFileSource.ios.kt:13–31` acquires before open, closes on open failure,
   and returns a `RawSource` retaining the lease until underlying close completes
   or throws. This corrects the “scope ends just after open” hazard. The caller
   must actually close the returned stream; source code does not automatically
   close it when some unrelated coroutine is cancelled. The standard documented
   `use` contract is not itself a proven leak. Non-file URL handling needs R1.
6. `IOi/KmpFileBookmark.ios.kt:18–56` creates the original location's bookmark
   under a synchronous scope, resolves it, retains a lease, and releases on a
   false existence check. It uses options `0u` rather than unavailable macOS-only
   flags. It discards the stale/error out parameters. Renewal is documented, but
   tests do not prove restart/cloud/stale/denied behavior or exact OS scope counts.
7. `IOi/KmpFile.ios.kt:84–134` correctly distinguishes original name/URI from
   readable file path/content metadata. A URI string does not persist authority;
   `IOc/KmpFile.kt:72–85` explicitly says so. Original URLs from photo-provider
   temporaries can expire even while the returned library copy remains readable.
   No test should conflate URI serialization with a durable copy or grant.

### Picker, saver and provider flows

1. `Pi/FilePickerLauncher.ios.kt:69–91` owns sessions per remembered presenter,
   reads current callbacks/settings, enforces a main-thread launch and rejects
   an already-presented controller/overlap. Disposing the owner suppresses late
   callback delivery. Owner state is not globally shared across other launcher
   instances or unrelated UI.
2. `Pi/IosDialogSession.kt:18–30,48–60` invalidates terminal and stored cleanup
   references before invoking cleanup. `owner.end(old)` cannot clear a newer
   session. This is a genuine improvement for reentrancy/cleanup exceptions.
   The mutable owner/controller fields assume UI-thread confinement; the atomic
   terminal field alone would not make the entire owner thread-safe. Production
   launch/UI delegates and Compose delivery use the UI path, while worker code
   manipulates only the owned result list. No off-main native invocation was
   demonstrated by this review.
3. `Pi/DocumentPickerDelegate.kt:24–64` can attach once, is strongly retained by
   the session's detach closure, and gates both pick signatures, cancel and
   adaptive dismiss. `close` invalidates before detaching. The photo delegate
   (`Pi/PhotoPickerDelegate.kt:16–23`) checks controller identity and the shared
   terminal claim before filtering/processing results, regardless of list size.
   It is explicitly retained by `session.retainedDelegate`.
4. `Pi/FilePickerLauncher.ios.kt:93–118` keeps the mutable list outside a
   cancellable `withContext` result handoff. A successful staged allocation is
   reachable for cleanup even if returning from IO is cancelled. Cancellation
   is rethrown; ordinary processing failure reports typed error; success marks
   ownership transferred **before** application code. User callback exceptions
   neither fabricate a second cancellation nor delete already-returned copies.
5. `Pi/Staging.kt:50–68` applies `limitedTo` before copy, checks cancellation
   between copies and before returning, and releases all unreturned allocations
   on an exception. A partial helper result carries files and a failure; the
   actual document facade (`Pi/FilePickerLauncher.ios.kt:163–165`) adds those
   files to its cleanup list, throws the failure, and returns **no partial list**
   to the user. `StagePickedUrlsTest` is a helper test, not proof of a different
   facade partial-success contract.
6. Photo results are limited first and copied serially. The
   `NSItemProvider` adapter (`Pi/FilePickerLauncher.ios.kt:190–214`) copies the
   provider's temporary URL **inside** its callback; deferring that copy until
   after callback return would be wrong. An atomic terminal flag rejects repeat
   callbacks and cancellation-before-copy. If cancellation wins while a copy is
   running, `continuation.resume(file, onCancellation)` releases the unconsumed
   value. Resume is outside the staging catch, so a resume failure is not caught
   and retried as a second resume. `progress.cancel()` requests cancellation; it
   does not prove that blocking native file copy stops immediately.
7. `Pi/Staging.kt:21–32,84–119` puts uniqueness in the directory, not the basename.
   `Pc/FileName.kt:4–9` rejects blank/dot/path/control components while preserving
   Unicode and an empty extension. File staging uses `copyItemAtURL` under scope,
   not move/delete-original. Write/copy false returns trigger owned-directory
   cleanup. Cleanup checks the parent against the two library staging roots;
   it does not search or delete arbitrary picked originals.
8. `Pi/FileSaverLauncher.ios.kt:54–105,110–124` funnels bytes, `NSData`, `KmpFile`
   and `NSURL` through staging. `NSData` construction and copy/write run on IO;
   assignment to the outer `staged` variable is intentional cancellation-safe
   retention. The native document picker receives only that copy and
   `asCopy = true`. A staging failure occurs before presentation; success/cancel
   delegates finish ownership before user callbacks. Presentation refusal and
   early disposal are the remaining gaps in R2/R3.
9. `Pi/FileSaverEvent.ios.kt:6–17` maps typed saver error to `Failed`, non-null
   destination to `Saved`, and null to `Cancelled`. It adds no extra native
   lifecycle observation. The legacy overload intentionally maps an error to a
   null result; this is documented compatibility, not proof that errors vanish
   in the new overload.

### Coil handoff and threading

`Cc/KmpFileFetcher.kt:36–56` checks active context, opens the platform stream,
adapts with `kotlinx-io-okio`, and wraps in `ImageSource`. The catch after source
creation closes on pre-transfer failure and preserves a cleanup exception as
suppressed. MIME lookup failure therefore closes the stream too. Native sources
are classified `DISK`; the browser-only cap/classification is not exercised by
this iOS pass. Non-Android context conversion returns `PlatformContext.INSTANCE`.

The fetched `ImageSource` owns the stream after success. The inspected desktop
test proves that **explicit close** traverses the bridge; it does not prove
every real Coil engine decoder/cancellation path invokes it. The fetcher does
not switch dispatchers internally. The caller/Coil execution context owns that
choice, as documented for `source` and `readByteArray`. Required remaining checks
include real native decoder failure/cancel, large-source peak memory, decoded
size constraints, EXIF/format parity and stable request invalidation policy.

## Remaining review findings

These are local cross-review identifiers, **not silently inserted replacements
for the stable baseline IO findings**. The lead/IO owner must integrate accepted
follow-ups and any subsequent fixes separately. No failure below was executed
on an Apple runtime during this review.

### R1 — Non-file NSURLs can be reinterpreted as unrelated local files

- **Priority/status:** Medium / **confirmed-source** identity inconsistency.
  Related to IO-014; the `source` behavior already exists in the baseline, so it
  is not falsely described as a newly introduced regression or demonstrated
  security exploit.
- **Locations:** `IOi/KmpFileSource.ios.kt:13–17` (`source`);
  `IOi/KmpFile.ios.kt:33–38,67–79,92–104,109–115` (public constructor, `exists`,
  read-all, `getPath`, `fromUriString`, `getSize`). Baseline streaming location:
  `KmpFileSource.ios.kt:9–11` at `af388bd…`.
- **Root cause:** The public `KmpFile(NSURL)` constructor accepts a non-file URL.
  `getPath` and `fromUriString` explicitly reject that scheme, but streaming,
  existence and size use `url.path` without checking `isFileURL`. A URL's path
  component is not proof of a local filesystem reference. The read-all variant
  instead passes the full URL to `NSData`, so the two read APIs can name
  different resources.
- **Source-level scenario:** Create an app-local fixture at an absolute path;
  wrap `NSURL(string = "https://example.invalid" + fixturePath)`. `getPath()`
  is null, but `source()` passes `fixturePath` to `SystemFileSystem.source`.
  No connection to the host is necessary for that streaming path. This sequence
  is derived from the concrete calls, not claimed as an executed iOS test.
- **Impact:** Manually wrapped unsupported URLs can select local bytes or local
  metadata unrelated to the caller's resource identity. Whether this is
  attacker-reachable depends on an application's input/trust boundary; no such
  boundary or exfiltration was demonstrated here.
- **Recommendation:** Validate a local-file URL before local-path operations.
  Choose and document one policy for direct non-file wrappers across both read
  APIs; generally reject unsupported schemes rather than silently stripping the
  scheme/authority. Preserve supported sandbox and security-scoped file URLs.
- **Compatibility/risk:** An application relying on undocumented `NSData` remote
  loading could observe a behavior change. Document that separately rather than
  interpreting a remote URL as local or inventing new network-fetch semantics.
- **Required tests:** A real existing local fixture plus `https:`/custom-scheme
  wrappers with the same path; no local bytes returned; false/null metadata or
  the documented typed error; ordinary file URL, spaces/Unicode, missing file,
  folder, and scoped-provider file regressions. Existing
  `KmpFilePathTest.getPathOfANonFileUrlIsNull` does not call `source` or metadata.
- **Effort/dependencies:** S; coordinate IO-014/IO-021 because Coil now uses
  `source` and inherits its reference semantics.

### R2 — Saver's presenter check expires while staging runs

- **Priority/status:** Medium / **risk**. The missing post-staging check and
  absent presentation-success state are source-confirmed; the rejected native
  presentation sequence has not been reproduced on iOS here.
- **Locations:** `Pi/FileSaverLauncher.ios.kt:54–75,88–105` (`launchStaged`);
  `Pi/IosDialogSession.kt:43–60` (per-instance owner). Related picker checks:
  `Pi/FilePickerLauncher.ios.kt:80–85,148–149,176–178`.
- **Root cause:** The saver checks `presentedViewController == null` before
  `withContext(Dispatchers.IO)` staging. On return it does not revalidate that
  presenter or its window attachment. Another saver owner, picker or unrelated
  modal can present during the suspension. `presentViewController(..., null)`
  has no observed success/failure completion here; `presented = true` is assigned
  just because the call returned. A native refusal that logs rather than throws
  bypasses the Kotlin exception cleanup path.
- **Impact:** The session can remain occupied and its copy retained until
  composition disposal, while no user-visible saver/result/error occurs.
  Same-launcher overlap rejection does not serialize different owners sharing
  one `UIViewController`. An unattached presenter is a related untested case.
- **Recommendation:** Recheck usability/current presentation on the UI thread
  immediately before requesting native presentation. Track accepted/presenting/
  terminal ownership rather than equating call return with presentation success.
  Handle busy/detached/rejected presentation with a typed error and owned-copy
  cleanup. Coordinate any shared-presenter policy narrowly; a global modal
  architectural rewrite is not necessary for this review finding.
- **Compatibility/risk:** Do not “fix” the race by dismissing someone else's
  modal or walking to an arbitrary topmost presenter without an explicit policy.
  UIKit transition callbacks and synchronous refusal paths need separate tests.
- **Required tests:** Gate staging to suspend, present a competing controller,
  then release the gate; repeat with two distinct saver owners. Also detach the
  presenter during staging. Assert no silent session/copy leak, exactly one
  error for a rejected request, source preserved, and a subsequent valid launch
  works. Use a hosted UIKit test; current session/helper tests never request a
  real presentation.
- **Effort/dependencies:** M; relates to IO-005/006/007 and the lifecycle in R3.

### R3 — Disposal releases saver staging before native dismissal is terminal

- **Priority/status:** Medium / **risk**, not confirmed destination corruption
  or a reproduced orphaned controller. The cleanup/dismiss order is directly
  visible in source.
- **Locations:** `Pi/IosDialogSession.kt:20–39` (`finish`/`cancel`);
  `Pi/FileSaverLauncher.ios.kt:75,88–93` (copy consumer and cleanup attachment);
  picker dismissal/processing handoff at
  `Pi/FilePickerLauncher.ios.kt:123–149`.
- **Root cause:** `cancel()` sets cancellation, cancels the coroutine, and invokes
  `finish()` before it requests native dismissal. For a saver, `finish()` removes
  the file exported by the controller. The controller/delegate/cleanup references
  are dropped, and dismissal is only attempted if `presentingViewController` is
  non-null, with no completion or presenting/dismissing phase tracking. Cancelling
  the Kotlin job does not establish that an already-presented document export
  has stopped consuming its staging URL.
- **Impact:** Disposal during an animated presentation or in-flight export may
  remove input before the native consumer finishes, or leave a presentation
  without retained lifecycle observation. Exact UIKit/provider ordering is
  platform-dependent and must not be reported as an observed failure. The
  original user file is still protected by copy staging; this risk concerns
  native input lifetime and completion, not reintroduction of move semantics.
- **Recommendation:** Suppress user results immediately on disposal, but retain
  the controller and native-consumed staging until dismissal/export is terminal
  or cancellation-before-presentation is proven. Model presentation-in-flight
  separately from result-processing completion and make cleanup exactly once at
  that safe ownership boundary. Do not immediately release a resource merely
  because the owning composable has disappeared.
- **Compatibility/risk:** Over-retaining until a callback that never comes also
  leaks; handle refused/unstarted presentation and teardown explicitly. Existing
  duplicate-result protection must not be weakened or reset for a new generation.
- **Required tests:** Dispose before presenting, immediately after requesting an
  animated presentation, while stably presented, during interactive dismissal,
  and during provider/export work; assert native consumer input remains available
  until terminal, no stale callbacks, one cleanup, no orphaned modal, and no
  interference with another controller. These require hosted UIKit/provider
  observations; a synthetic `Job.cancel()`/cleanup-count test is insufficient.
- **Effort/dependencies:** M; IO-005/007/013 and R2.

## Authored-test coverage, not runtime certification

The test source reviewed below matches the first iOS KLIB input hashes. All are
under the respective module's
`src/iosTest/kotlin/com/mohamedrejeb/calf/{io,picker}/`. Count is by `@Test` methods,
not by setup/cleanup functions or native execution.

| Class | Functions | What it actually exercises when run | Important missing proof |
|---|---:|---|---|
| IO `NativeReadSafetyTest` | 4 | Real temporary `NSData` empty/binary reads; stream parity; missing-file exception; attached-copy release vs original | No ASan/huge native buffer, denied provider, non-file streaming, or measured scope balance |
| IO `KmpFileBookmarkTest` | 4 | Local temp bookmark round-trip, double release, missing/invalid bookmark | No security-scoped external folder, process/device restart, stale bookmark, revocation, grant count |
| IO `KmpFileMetadataTest` | 6 | URI/path round-trip and rejection, local size, missing/directory size, no-extension MIME | No provider metadata or real Uniform Type database coverage |
| IO `KmpFilePathTest` | 7 | Decoded path/name, copy-vs-original semantics, non-file `getPath`, encoded URI | Does not read a non-file URL, renew a grant, or preserve expired originals |
| Picker `DocumentPickerDelegateTest` | 5 | Direct delegate calls for swipe/cancel/pick ordering, new delegate, duplicate nonempty pick | Synthetic presentation controller, not real native event delivery/gesture/animation |
| Picker `IosDialogSessionTest` | 4 | Terminal claim, overlap/generation isolation, synthetic job cancellation/cleanup, throwing cleanup | No UIViewController presentation, dismiss completion, export reader, or worker handoff |
| Picker `IosPickerContractTest` | 5 | Real UTType/configuration object construction; limit/representation values; direct empty-photo and disposed callbacks | No actual photo selection/provider or nonempty PHPicker result/cancellation adapter run; no Compose recomposition |
| Picker `FileSaverStagingTest` | 5 | Exact names, distinct directories, exists/removal, copy source remains, missing source | No export UI, byte-for-byte saved destination, denied/disk-full provider, or native `asCopy` behavior |
| Picker `PickedCopyOwnershipTest` | 3 | 100 inputs with limit one; injected cancellation between copies; Unicode/release idempotence | Cancellation hook is synchronous, not a live NSItemProvider mid-copy callback race |
| Picker `PickedFileStagingTest` | 3 | Name/source preservation, uniqueness, missing file | No security-scoped external location, content comparison or native picker session |
| Picker `StagePickedUrlsTest` | 2 | Readable staged list and helper partial-failure count | Not facade delivery; facade intentionally discards all results on a partial failure |
| Picker `InitialDirectoryTest` | 3 | Folder URL serialization, plain path, empty setting | No guarantee native picker honors a directory, has a persisted grant, or opens a provider |
| **iOS total** | **51** | **Compiled test source only in the inspected receipt** | **Zero executed Apple tests in that receipt** |

Additional existing execution evidence: five common `BoundedReadTest` functions
on desktop and three `KmpFileFetcherTest` desktop functions, as described above.
There is no authored iOS Coil test class in this reviewed source set. The common
bounded tests do not yet cover a zero-progress source, a close-that-throws case,
or cancellation before a platform source is opened. This review did not add
tests or substitute mocks for missing native evidence.

## Recommended integration disposition

1. Keep IO-001 **partially verified** and IO-005/007/013 **implemented**, rather
   than closed, until Apple runtime gates actually execute. Do not downgrade
   earlier evidence or relabel KLIB compilation as tests passed.
2. Integrate R1 as a narrow unsupported-scheme contract fix with a real regression
   test, and R2/R3 as explicit native-lifecycle follow-ups pending owner triage
   and hosted reproduction. Preserve source/evidence snapshots when fixing them.
3. Run the 51 authored iOS methods on a correctly hosted Apple runner and then
   add the provider/presentation/scope cases they cannot presently cover. Do not
   combine helper assertions with device coverage in one undifferentiated count.
4. Verify real Coil success/failure/cancellation cleanup on native targets, and
   keep the documented background-dispatcher and permanent-storage guidance.

The review supports the narrow source repairs described above. It does **not**
establish general iOS correctness, Apple release readiness, or verification of
Android/JNI/Desktop issues outside its assigned scope.

## Follow-up cross-review, 20:21 UTC

After the lead released only the IO/picker iOS freeze for focused corrections,
the IO owner revised the implementation and added tests. I independently read
the changes and the new test bodies, without editing source or running a build.
The owner then reported those sources refrozen for lead-scheduled compilation.
The following is **source review only**; at this cutoff there was **no inspected
compile or runtime result for the new revisions**. The original first-iOS-KLIB
receipt cannot be carried forward over them.

### Disposition of R1–R3 after the focused correction

| Review item | Revised implementation | Independent disposition |
|---|---|---|
| **R1: non-file URL identity** | `IOi/KmpFile.ios.kt:73–105,121–146` uses the file-only `getPath` authority check for existence/size/directory and shared `requireFilePath` for content. `IOi/KmpFileSource.ios.kt:12–18` validates before acquiring scope/opening; read-all validates before Foundation can download a non-file URL. Bookmark creation/resolution and picker/export staging/cleanup now reject non-file URLs too. Original name/URI metadata and public constructor signatures remain available, with the content policy documented. | **Source-addressed**, pending the new real-Foundation regression execution. The previous source identity mismatch is no longer present in the inspected revision. No exploit was claimed before, and none is claimed now. |
| **R2: post-staging presentation race** | Saver `Pi/FileSaverLauncher.ios.kt:82–104` returns to `Dispatchers.Main.immediate` and calls the shared `presentIosDialog` after staging. `Pi/IosDialogPresentation.kt:15–41` requires a loaded view attached to a visible window, an active scene when one exists, and idle presenter/ancestors immediately before the native call. Admission has no intervening suspension. It detects an unattached, nontransitioning controller after a returned native call instead of unconditionally declaring presentation success. | **Source-addressed race precondition/cleanup logic**, with native acceptance/refusal still **unverified**. No new concrete source blocker found in the correction. Hosted tests must establish that a normal accepted native presentation is not falsely rejected by the immediate post-call observation and that competing presentation really takes the typed-error cleanup path. |
| **R3: premature native-resource cleanup** | `Pi/IosDialogSession.kt:12–117` separates Prepared/Presenting/Presented/Dismissing/Dismissed/Finished, terminal result claim, finish request and dismissal request. It suppresses/cancels immediately but retains controller/delegate/cleanup during presentation/dismissal. Release occurs only without a started presentation or after native dismissal, and the owner remains occupied until release. The saver transfers its copy to session cleanup before presentation and never directly deletes that transferred file from its coroutine `finally`. | **Source-addressed lifetime order**, not certified UIKit/export cancellation. Seven new session tests plus one Foundation-file lifetime test exercise explicit phase ordering, not the real transition adapter. No concrete new source blocker was found; the hosted native gates remain. |

The primary phase/ownership details were checked, not merely the added enum:

- `finish` while Presenting waits for presentation completion; it no longer
  clears the controller and guesses that an absent parent means terminal.
- The Presenting→Presented completion advances a pending dismissal; the
  Dismissing phase is set **before** invoking native code, so synchronous
  completions do not start a second dismissal. `dismissalCompleted` advances
  cleanup independently of whether a user result was already claimed.
- `releaseResources` invalidates stored callbacks/resources, runs cleanup, clears
  the matching owner's current session, and completes `awaitFinished` once.
  Repeated old completion cannot terminate a new session.
- `Pi/DocumentPickerDelegate.kt:54–70` has a separate one-shot native-dismiss
  notification, so a prior pick/cancel does not filter out the lifetime event.
  `Pi/PhotoPickerDelegate.kt:21–25` also informs session lifetime separately from
  deciding whether to deliver cancellation. Disposed sessions still suppress
  user results through the session guard.
- Picker processing still owns its result list across IO/cancellable handoff.
  Photo dismissal can complete while provider copying continues; native terminal
  alone does not finish normal processing. Final delivery waits asynchronously
  for session teardown; this is a suspending wait, not a UI-thread blocking wait.
- Saver `ownedBySession` distinguishes local staging cleanup before handoff from
  native-consumed copy cleanup afterward. Cancellation after the Main-context
  handoff calls session cancellation instead of deleting the export input in the
  outer coroutine. Normal success/error delivery waits for safe session finish.
- `dismissOwnedIosDialog` observes an already-dismissing controller through its
  transition coordinator when possible. Cancelled interactive dismissal is a
  rollback, so the adapter dispatches a subsequent owned-controller dismissal
  rather than releasing the input. No timer-based “probably finished” deletion
  was introduced, and unrelated presented controllers are not dismissed.

### Added tests and remaining native gaps

The count is now **63 authored iOS functions**, preserving the earlier 51 and
adding exactly these 12:

| File | New method(s) | Actual scope, if executed |
|---|---|---|
| IO `NativeReadSafetyTest.kt` | `aNonFileUrlWithTheSamePathCannotReadOrDescribeALocalFile`; `aNonFileUrlCannotDescribeALocalDirectoryOrDeleteAnOriginal` | Real Foundation URLs/files, with identical local and non-file URL path components. Assert file-only metadata/read policy and original preservation. Loopback URL avoids an external test endpoint if the read-all guard regresses. Not yet executed at this cutoff. |
| Picker `DocumentPickerDelegateTest.kt` | `nativeDismissalIsReportedAfterAnAlreadyDeliveredResult` | Direct native-delegate method calls prove distinct result/lifetime notifications and one dismissal. No real gesture or OS callback delivery. |
| Picker `FileSaverStagingTest.kt` | `aNonFileUrlCannotStageOrRemoveTheLocalFileWithItsPath`; `exportCopyRemainsUntilDismissalCompletionButNeverDeletesTheOriginal` | Actual Foundation staging files and rejection, but dismissal completions are **synthetically supplied** to the session. Not actual export-reader or animation proof. |
| Picker `IosDialogSessionTest.kt` | `disposalDuringPresentationKeepsNativeResourcesUntilDismissalCompletes`; `finishingAPresentedDialogDoesNotAdmitAnotherUntilNativeDismissal`; `dismissedSheetKeepsProviderOwnershipUntilProcessingFinishes`; `aRejectedNativeCallCleansEvenWhenDisposalArrivedWhilePresenting`; `disposalDuringDismissalNeitherCleansEarlyNorRequestsItTwice`; `anAdaptiveDismissalDuringPresentationIsAlsoANativeCompletion`; `awaitingFinishDoesNotReturnBeforeNativeCleanup` | Production session state machine, injected completion callbacks, synthetic job/delegate ownership and a coroutine waiter. These are **policy/ownership tests**, not UIKit presentation/transition execution. |

None of these new methods calls the new `presentIosDialog` adapter. Required
hosted cases are still: ordinary accepted presentation; idle→busy/detached window
between saver staging and presentation; two distinct owners; animated
presentation-time disposal; native document auto-dismiss; interactive rollback;
and already-dismissing controllers with/without a usable transition coordinator.
The adapter deliberately retains ownership if UIKit supplies no usable terminal
signal rather than deleting native input early; that fallback can still retain
a session/resource indefinitely and requires real-platform investigation, not
a claim that the risk was eliminated.

I checked the new native calls against the **already available** Kotlin 2.4.20
UIKit metadata: presentation/dismissal completion is nullable `() -> Unit`;
`transitionCoordinator` is an imported extension; coordinator completion receives
a nullable context and registration returns `Boolean`; cancellation uses
`context.isCancelled()` (or `cancelled` property); `viewIfLoaded`, `windowScene`,
`activationState`, and `isBeingPresented/isBeingDismissed` exist with the used
shapes. This was a metadata read, **not typechecking or an execution result**.

### Follow-up snapshot fingerprints

SHA-256 values recomputed at `2026-10-24T20:20:58Z`. These are the changed/new
reviewed iOS files relative to the first iOS KLIB receipt; they enable later
evidence comparison without pretending these uncommitted sources are immutable.
Test prefixes: **IOt** =
`calf-io/src/iosTest/kotlin/com/mohamedrejeb/calf/io/`; **Pt** =
`calf-file-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/picker/`.

| File (prefixes above) | SHA-256 |
|---|---|
| `IOi/KmpFile.ios.kt` | `2216a9aee6b0b396a78a990d4ddf69f76f8ccfb4ef72253c41d74400ecebb1c8` |
| `IOi/KmpFileBookmark.ios.kt` | `4330855df5667175f87e68d97bf4270d67d505cc9852807771ab877b67b9587c` |
| `IOi/KmpFileSource.ios.kt` | `13e52e2bfff41151dc8f2a3b4de661a9492b52d9ac5ceb70b4786d5be1a0d77d` |
| `IOt/NativeReadSafetyTest.kt` | `b9519430e5e461bf51383c6818b378955cefd465043f88c0a535af4dd94d2e3d` |
| `Pi/DocumentPickerDelegate.kt` | `863b824857ae97f3d134bad54ad181da17d0f9111a10b3add6b1b513c9464d13` |
| `Pi/FilePickerLauncher.ios.kt` | `b3c4d40da8d8c9fae7b65402bc8ae9249d2d0171e6ae71c52cee8c3e1e364e6c` |
| `Pi/FileSaverLauncher.ios.kt` | `386655e242c5a01883bee9ec9c08947b594dec04ca4146a93070ab3e2310c0e9` |
| `Pi/IosDialogPresentation.kt` | `b263b15c03a717d51f24789312bf47e594349ce6d85495e60cc5c2deea26d1d7` |
| `Pi/IosDialogSession.kt` | `51e76ae1980e090562349c7fea8b5b0c514b3467f3b5f5d7459d0611b10101d7` |
| `Pi/PhotoPickerDelegate.kt` | `d176752ed937751fc696e911446d3b2c2f8f3200790bc4369b5e976f2d1355b0` |
| `Pi/Staging.kt` | `3b2a9b985da5da628fca626518b5df6e32aaa2837abeb2403306e826014388dd` |
| `Pt/DocumentPickerDelegateTest.kt` | `d89013ff8394aa112e12aec355ce2ac4ed422347dad41222c344f877b033c8d8` |
| `Pt/FileSaverStagingTest.kt` | `25255ace23d24babd18787b3c8439430c1700f50b0a834a27a494a9c7bf8874a` |
| `Pt/IosDialogSessionTest.kt` | `72382f4d526f7b0bcddae07566018e5618226b0de69fec3d42ae4bf72c22e4d2` |

**Follow-up conclusion:** the narrow corrective source changes are acceptable
for the lead's next compile/test gate; no new source blocker was found. This is
not a runtime approval. Preserve R1–R3 and their original evidence, attach the
new command/result to the new hashes, and keep native/provider claims open until
their real tests run.
