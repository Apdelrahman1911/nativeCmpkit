# IO, picker and Coil implementation record

Scope: **IO-001–IO-026**, `calf-io`, `calf-file-picker` (Kotlin and Rust), and
`calf-file-picker-coil`. The [baseline findings](../audit/findings/IO.json) and
[audit report](../audit/io-and-file-picker.md) remain immutable. Current
dispositions, tests and remaining work are in [resolutions/IO.json](resolutions/IO.json).
An `implemented` disposition means a source change, **not** that native behavior,
consumer compatibility or release readiness has been demonstrated.
`partially-verified` names the target/scenario actually exercised while retaining
unexecuted platform, runtime and immutable-revision requirements. No finding in
this area has yet been marked fully `verified`.

## Current native copy and lifecycle verification

The [iOS IO/Coil record](native-io-verification.md) covers the actual owning
Foundation copy helper, Darwin guard-page fixtures, inode/device descriptor
observations and real Coil decoder cancellation/error integration. Final
typechecking passes47 authored methods (IO40/Coil7) at733 held inputs; **zero
Native executions**, not issue closure.11 focused Python methods are within414
full CI methods; first failures are retained. The finite `ios-io` profile requires
all22 exact native cases with no skips/N/A, without replaying unchanged UI or
other hosts. IO-001/#4 stays `partially-verified` until immutable Apple runtime
and all six original requirements are accepted. All other IO/provider/device,
legal/dependency/consumer/API-ABI and release gates remain.

## Provenance and scope of the design changes

After the lead's upstream-reconciliation checkpoint at `243cf1df`, reviewed parts
of Mohamed Rejeb's [Calf PR #551](https://github.com/MohamedRejeb/Calf/pull/551),
tip `66e345a9b291d4d82aa76b1f5f0d05e99b1bb8e1`, were adapted. The
[source provenance](evidence/io/pr551-source-provenance.json) records imported
paths, blob OIDs and original commits/authorship. This was an attributed source
adaptation, not a merge, history rewrite, upstream modification or claim that an
unmerged PR had been accepted upstream.

The adaptation includes metadata/path/bookmark APIs, typed errors, staging and
tests. nativeCmpkit additionally changes session ownership, cancellation, atomic
saving, browser events, streaming Coil integration and native-handle safety.
Shared build/dependency/CI changes are maintained by the build owner, not this
area. Rust crate/JNI names, public packages and Gradle module paths are retained.

### Scoped decision: additive APIs rather than package replacement

- Keep existing `rememberFilePickerLauncher(..., onResult)` and
  `rememberFileSaverLauncher(settings, onResult)` expect declarations **and the
  actual implementations in their original platform files**. Moving these
  bodies to common code would change JVM facade ownership; avoid that incidental
  binary break. An early diagnostic found accidentally duplicated common `actual`
  wrappers; those were removed, retaining the platform facades.
- Add typed `onError: (FilePickerException) -> Unit` overloads. A native cancel is
  an empty selection or `null` save result, not an error. Partial iOS staging
  failure disposes unreturned copies and reports an error instead of silent
  partial success. The legacy overload maps errors to its empty/null result.
- Application callbacks are outside operation/conversion catches. A throwing
  callback must not be reclassified as an operation failure or invoked twice.
- Reject overlapping launches instead of replacing another request's state.
  Configuration is snapshotted at accepted launch; the current callback is used
  when that launch completes. Disposal suppresses late delivery. Cancellation of
  the owning coroutine remains cancellation, not `FilePickerException`.
- This is **not an ABI certification**. The lead's immutable compiled API and
  consumer fixtures must confirm retained descriptors and dependency exposure.

## Changed contracts and migration instructions

### Paths, URI strings and file kind (IO-010/014/019)

`getPath()` now consistently means an optional **filesystem path of the readable
file**, not an arbitrary reference string. This is an intentional observable
change despite retaining its method signature:

| Target | `getPath()` | `toUriString()` |
|---|---|---|
| Android `file:` | Decoded filesystem path | Serialized file URI |
| Android `content:` | `null` | Original provider URI, including tree/grant form |
| iOS `file:` | Readable staged/local file path | Original picked URL string |
| iOS non-file NSURL | `null` | Original URL string, metadata only |
| Desktop | File path | File URI |
| JS / Wasm | `null` | `null` |

Replace URI serialization that previously used `getPath()` with `toUriString()`.
Use `KmpFile.fromUriString(...)` to restore a supported reference; **restoring a
reference does not restore its access grant**. Prefer `source()` for content
rather than reconstructing platform paths. `getName()` uses decoded iOS
`lastPathComponent`, not URL-string splitting. Browser filenames are neither
paths nor unique stable identities.

The iOS public `KmpFile(NSURL)` constructor remains available, but a non-file URL
is **not content access**. `source()` and both reads throw `FileNotFoundException`
before opening a path, scope or Foundation network read; `exists`/`isDirectory`
are false and `getSize`/`getPath` are null. Its original name/URI metadata remains
available. Bookmarks and staging likewise reject non-file URLs. This closes the
source-confirmed mismatch where `https://host/local/path` could expose the local
file's metadata and streaming content via `NSURL.path` even though `getPath`
correctly returned null. Use a networking API for HTTP content; no URL constructor
descriptor was removed. See the [independent iOS review](evidence/review/io-ios-independent.md).

`isFile` means **exists and is not a directory**, not a universal assertion that
the backing object is a POSIX regular file. A browser `File` is never a directory,
even when named `README`, `LICENSE` or `.gitignore`. Android directory existence
uses provider metadata instead of attempting a byte-stream open. Pure tree URIs
are queried as tree roots; `/tree/root/document/child` remains the child, not the
tree root. The original URI remains available for grants and enumeration.

### Reads, memory bounds and stream ownership (IO-001/009/020/021)

- iOS validates the native data length before allocation, returns an empty array
  without `addressOf(0)`, and copies exactly the validated length. Failed NSData
  reads throw instead of masquerading as empty content.
- Android whole-array reads use `InputStream.use`, including read failures.
- `readByteArray(context, maxBytes)` and `readByteArray(maxBytes)` are additive.
  They precheck known size, enforce the limit while consuming at most 64 KiB per
  read, distinguish exactly-at-limit from oversized by one extra byte, reject
  no-progress sources, check cancellation and close the stream on every exit.
  The limit is not permission to allocate `Int.MAX_VALUE` on a small device.
- Existing unbounded reads still allocate the entire content. Their `suspend`
  modifier does **not** move blocking Android/iOS/Desktop work off the caller's
  dispatcher. Use a platform background dispatcher and a realistic application
  limit, or stream. The sample owner has adopted bounded background reads.
- Browser FileReader uses separate load/error/abort handlers registered before
  starting, a cancellable continuation, cancellation-triggered abort and handler
  removal before resumption. A missing result is an error. Browser `source()` is
  still buffered; a synchronous streaming Blob source is not claimed.
- Coil now uses the official `kotlinx-io-okio` bridge. `ImageSource` owns the
  buffered source after a successful fetch; failures/cancellation before that
  transfer close it. Native/JVM data is reported as `DISK`, browser buffering as
  `MEMORY`; source MIME metadata is retained. Real memory profiling and request
  invalidation behavior still need measurement/integration tests.
- Browser Coil fetches reject unknown/negative or over-limit immutable Blob sizes
  before reading. Default limit: **64 MiB**. Configure
  `KmpFileFetcher.Factory(maxInMemoryBytes = ...)` explicitly for another policy;
  the existing no-argument factory and two-argument fetcher constructors remain.
  This cap is source bytes, **not decoded bitmap size**; set an appropriate Coil
  request size too. No peak-memory benchmark is claimed.

### Access grants and temporary-copy ownership (IO-008/013)

`createBookmark`, `KmpFile.fromBookmark` and `releaseBookmark` are opt-in:

- Android attempts a persistable read/write grant, then read-only; providers
  without a persistable grant return `null`. Explicit release relinquishes the
  app's persisted grant. Multiple application components must coordinate grant
  use: this is not a globally reference-counted permission manager. Grant
  existence is not proof the provider still has the file or can currently read it.
- iOS bookmark resolution keeps a security-scope lease until explicit release.
  Re-create/store bookmarks when reopening because stale external references
  can change. Device restart, stale bookmarks and third-party providers still
  need device integration tests. No macOS-only bookmark flag is used on iOS.
- Every iOS `source()` owns its own successful security-scope start through stream
  close, including failing close. The internal `acquireSecurityScopedAccess()`
  lease is atomically closed once. A sandbox-local URL may legitimately return
  false from Apple's start call; the actual read reports access errors.
- `withSecurityScopedAccess` is only for synchronous work inside its block. Do
  not return a stream or asynchronous native operation from it; keep a lease for
  the entire native operation instead. The share owner uses the lease API.
- Nonfolder iOS picker results are app-owned **temporary** copies, preserving the
  real basename under a unique directory. The OS can purge them. Copy to durable
  app storage when permanence is required; a path/bookmark string alone does not
  make temporary content permanent.
- Call `file.releaseTemporaryCopy()` only after the final stream/decoder/share
  consumer has finished. It removes only attached library-owned staging, once;
  caller-owned originals and all other targets return `false`. A failed cleanup
  also returns `false`; the current API does not promise retryable deletion.

iOS limits are applied **before copying**. Document staging checks cancellation
between files and removes all unreturned copies on exceptional exits. Photo
provider work is serialized, not unbounded `async` fan-out. The temporary
NSItemProvider URL is copied **inside its callback before that callback returns**;
an unconsumed resume result is released on cancellation. These changes do not
establish cloud-provider performance or photos-library behavior without Apple
runtime checks.

### Saving without destroying the source (IO-002/004/005/006)

**Android:** one `rememberSaveable` holder owns the pending request across
recomposition. A URI can be restored; a byte payload is recorded as `bytes-lost`,
never put wholesale in an Activity Bundle. Lost required content reports an error
instead of a successful empty file. Passing `bytes = null` deliberately requests
an empty file. The holder remains busy through the write, consumes the result once
and is reset after success/failure/cancel. Coroutine ownership begins
undispatched so disposal before the first IO dispatch cannot skip its `finally`.

The writer checks nullable streams, truncates intentionally with `wt`, copies in
bounded chunks and checks cancellation. Best-effort deletion applies only to the
new CreateDocument destination; provider deletion refusal can leave a partial
document. URI equality, same-authority document IDs across tree/single forms,
provider canonicalization hints, canonical file paths and device/inode identity
recognize known aliases. An identified original is checked for readability but is
never opened for write/deleted. If cancellation prevents identity evaluation,
cleanup conservatively leaves the destination alone.

For two different `file:` paths, an unavailable/zero inode or unexpected stat
failure now refuses the save **before** any destination stream is opened. It is
neither proof of equality (a false successful no-op) nor proof of difference
(potential original truncation). Only destination `ENOENT`, after a valid source
identity, authorizes creating a missing destination. Real provider aliases across
`content:` references still have the separate limit below.

**Limit:** `ACTION_CREATE_DOCUMENT` promises a new document. Opaque identifiers
from unrelated/nonconforming providers cannot prove distinct physical storage.
Alias detection is not a transactional guarantee for a provider violating that
contract. Process death during writing can also leave incomplete provider output;
Robolectric saved-state restoration is not an OS process-kill test.

**Desktop:** compare file identity before writing (including normalized paths,
symlinks and hard links). Same-file copy is a non-destructive no-op. Otherwise copy
or write into a sibling staging file, close it, check cancellation and atomically
replace the destination. `null` content writes a deliberate zero-length file.
**Atomic replacement fails closed when unsupported**; it does not silently
delete/replace an existing destination through a non-atomic fallback. Surface the
typed error and choose a supported location. Stage/commit failures preserve the
old destination; cleanup failures are suppressed onto the primary exception.
No fsync/crash-durability guarantee or transactional network filesystem guarantee
is made.

**iOS:** bytes, NSData, KmpFile and NSURL all stage to an owned directory with the
exact requested filename; the original is never moved. Export uses the explicit
`asCopy = true` initializer. The preparing coroutine owns the copy until a
main-thread handoff to the session; after that, only session teardown may remove
it. An unpresented failure can clean immediately, but success/cancel/disposal
wait for completed native dismissal, not just a callback or dismissal request.
`NSData.writeToURL`/file-copy failures are checked. Returned export destinations
are external URLs: reopen via supported scope/bookmark APIs rather than assuming
permanent unscoped path access.

`IosDialogPresentation` rechecks the **attached, visible, active-scene, idle
presenter and its ancestors after suspendable staging**, immediately before the
native call on Main. An earlier idle check is not a reservation against another
launcher. Rejected/unstarted presentations clean their own staging; they never
dismiss a competing owner's controller. This source fix still needs actual
hosted UIKit acceptance/rejection and two-owner staging-gate tests.

Basenames/extensions are single filename components. Reject blank/dot/path/control
names instead of silently interpreting paths. Unicode is retained. An empty
extension produces `name`, not `name.`.

### Exactly-once native and browser sessions (IO-003/007/017/018/026)

- `Multiple(maxItems)` accepts `null` or positive integers only. Android limit one
  uses the single contract; native maxima are adapted, and every result/fallback
  path is post-limited using the launch snapshot. Limit changes must not rewrite
  a request already in flight.
- iOS uses a fresh retained session/delegate per presentation. Photo and document
  callbacks, including swipe dismissal, share a terminal guard. An old delegate
  cannot be reattached and replayed as a new generation. `Prepared`, `Presenting`,
  `Presented`, `Dismissing`, `Dismissed` and `Finished` are explicit phases.
  Cancellation stops the owned job and suppresses outcomes immediately; native
  controller/delegate/staging ownership persists through presentation/dismissal
  completion. Adaptive `didDismiss` updates native lifetime even after the result
  guard was consumed. An interactive rollback is not dismissal completion.
  Provider processing and native completion must both finish before teardown;
  the owner remains busy and callbacks await teardown. Cleanup references are
  invalidated before invocation so reentry/throws cannot run them twice.
- For an already dismissing iOS controller, use the native transition completion;
  a cancelled interactive transition queues an owned dismissal after rollback.
  Without a usable coordinator, request dismissal of that controller and wait for
  completion/adaptive `didDismiss`. There is **no timer-based early deletion**.
  If UIKit supplies neither lifetime signal, resources can remain retained rather
  than being deleted under a native consumer. This and the immediate
  post-presentation rejection check remain hosted-native verification gates,
  not guarantees proved by synthetic phase tests.
- Desktop creates, uses and closes the native configuration **inside one IO-worker
  ownership scope**, not through a cancellable handoff to composition state.
  A `finally` closes it before callback delivery. Settings/callback changes no
  longer mutate a handle while it is being shown. Native dialogs are blocking:
  disposing composition does not prove the OS sheet immediately closes, but the
  configuration remains owned until the blocking call returns.
- Rust uses monotonic opaque IDs, not raw `Box` addresses. The registry holds
  `Arc<DialogConfig>`; a show leases its Arc before close can remove the entry.
  Double close is safe, stale IDs fail, IDs are not recycled, and destructors run
  outside the registry mutex. This solves configuration lifetime, **not native
  parent-window lifetime**.
- Browser sessions own the input/listeners, clean before callbacks, reject overlap
  and detach on disposal. Conversion catches exclude application callbacks.
  Cancellation callback failure therefore cannot strand a DOM node or deliver a
  second result. The real DOM tests call the session/event path, not the OS picker.

### Browser save capability and download events (IO-011/012)

Prefer `rememberFileSaverEventLauncher` and handle all `FileSaverEvent` variants:

| Event | Meaning |
|---|---|
| `Saved(file)` | Selected destination was written and closed by the save API |
| `Cancelled` | Native save picker reports cancellation |
| `DownloadStarted(fileName)` | Download was requested; eventual completion is unobservable |
| `Failed(error)` | Preparation, permission, launch or write failed |

`fileSaverCapability()` reports `SaveDestination` only when a secure browser
exposes `showSaveFilePicker`, otherwise `DownloadOnly`. Capability is not a grant;
launch must occur synchronously in the user-activation stack. A rejected save
picker/write does **not** silently fall back to a download that would misrepresent
the failure. Disposing a save cancels delivery and aborts a writable when acquired;
late native promises do not deliver another outcome. Synchronous
`createWritable()` failures also take the write-error path.

The legacy `onResult(KmpFile?)` cannot truthfully represent an unobserved download
completion. For the download-only fallback it intentionally remains silent,
matching the historical behavior. **Migrate web callers waiting on that callback
to the event API**, rather than treating `null` as fake completion.

Download anchors are removed in `finally`. Blob URLs are retained for **40 seconds**
and then revoked independently of composition disposal. At most **32** downloads
may await cleanup; additional requests fail rather than revoking an in-flight
URL early. Click/scheduling failure revokes immediately. This is a bounded
heuristic, **not evidence that Safari/iOS consumed a large Blob within 40 seconds**.
It bounds URL count, not total payload bytes; callers must still bound input size.

### Filters, encoding and desktop loading (IO-015/016/022/024/025)

- Add the IANA HEIC/HEIF/AVIF and sequence MIME names to the retained MIME table.
  Unknown or mixed known/unknown custom desktop MIME filters throw; use explicit
  `FilePickerFileType.Extension` when the table lacks a type. Filters are UI hints,
  **not a content/security boundary**.
- MIME comparison uses `Locale.ROOT`, comma splitting with trim, a reverse MIME
  index and synchronized retained registration. Remove unused per-entry work and
  spread-array copies. The wildcard matcher is iterative, preserves escapes and
  avoids recursive exponential backtracking; no measured CPU speedup is claimed.
- iOS `Document` maps to **UTTypeData**, not the application-bundle UTI. This is
  deliberately broader than Android/Desktop `application/*`; explicit Pdf/Word/
  Spreadsheet modes retain specific mappings. Empty/invalid filters reject
  rather than silently disabling filtering. Apple can synthesize dynamic UTTypes
  for otherwise unknown extensions/MIME names; visibility still depends on the
  provider and the platform's registered types.
- Native Unix paths that cannot be represented as Java Unicode strings now throw
  `IOException` instead of aliasing a replacement-character filename. Unicode
  accents/CJK/emoji remain supported by normal JNI encoding. Supporting arbitrary
  Unix path bytes would require a different public path representation.
- Bundled native payloads are preferred. To intentionally trust system library
  lookup, packagers must set
  `-Dnativecmpkit.picker.trustSystemLibrary=true`; never include untrusted writable
  directories in that search path. After loading, JNI requires `abiVersion() == 1`.
  Old/mismatched payloads fail instead of being presumed compatible. This is an
  observable packaging change; keep native code and Kotlin code together.
- Cache extraction checks directory ownership, symlinks and POSIX group/other
  write access, and reuses only byte-identical cached content. Missing/unusable
  home falls back to a randomized private directory, not shared `tmp/.cache`.
  The created temporary path is resolved to account for macOS's system `/var`
  alias. Full Windows ACL/noexec/foreign-user race checks remain unverified.
  A content hash is cache naming/integrity checking, not artifact signing or trust
  in arbitrary externally supplied binaries.
- Rust pins jni 0.21.1, rfd 0.17.2 and raw-window-handle 0.6.2 with a lockfile.
  The old ashpd/zbus dependency chain is removed. Its matched advisories were
  **unmaintained informational advisories**, not demonstrated exploits. The build
  owner's dependency/provenance verification still governs release readiness.

## Explicit open blocker: IO-023

**Native parent-window thread affinity and lifetime are not fixed.** The registry
protects `DialogConfig`, not the NSWindow/NSView/HWND/X11 resources behind its raw
handles. AppKit acquisition/retention/release needs a genuine main-thread-bound
native lease, close/recreate tests and main-thread checker coverage. The Linux
handle/backend assumption and Windows parent-destruction behavior likewise need
runtime verification. Do not misread existing Rust safety comments as proof.
The [source-backed parent-window design/test plan](IO-parent-windows.md) identifies
the precise `rfd`/borrow/thread boundary and a possible platform binding; it is
not an implemented repair or native runtime verification.

Silently dropping every parent would alter focus/modality and is **not** accepted
as a fix. No-parent non-GUI JNI tests establish only payload loading/handle
registration, not modal parenting. IO-023 remains `unresolved` and belongs in the
preview gate rather than being closed because a config registry exists.

## Verification ledger (diagnostic working tree, not a release receipt)

The full command and source-hash scope are in the linked lead evidence. Repeated
runs reuse test functions; never sum repetitions as new independent coverage.

| Evidence | Actual inspected outcome | Boundary |
|---|---|---|
| [Rust first run](evidence/io/cargo-test-first.log.result.json), [log](evidence/io/cargo-test-first.log) | `cargo test --jobs 1`: exit 0, **5 tests**, zero failures/ignored | Registry lease/close races and path conversion; no GUI/JNI UI interaction |
| [Second desktop batch](evidence/gradle/second-library-desktop.summary.json) | IO: **22 tests / 5 reports**, zero failures/errors/skips; batch exit 1 elsewhere | Real IO sources/common bounds/JVM metadata, not Apple/Android/browser |
| [First Android host batch](evidence/gradle/first-android-host.summary.json) | IO/picker test execution **did not occur**: compilation errors | Accidental common wrappers and a mixed-type test row were repaired; rerun was required at that checkpoint, with later executions recorded below |
| [First picker/Coil desktop batch](evidence/gradle/first-picker-coil-desktop.log.result.json), [log](evidence/gradle/first-picker-coil-desktop.log) | Coil: **3 tests / 1 report**, zero failures/errors/skips. Picker production/Rust release compilation passed; picker tests blocked by duplicate resource-copy task failure; batch exit 1 | Real bridge binary content and ImageSource close; no memory profile or Coil device pipeline |
| [Second IO/picker combined batch](evidence/gradle/second-io-perm-and-fourth-ui.summary.json), [command/result](evidence/gradle/second-io-perm-and-fourth-ui.log.result.json) | Picker desktop: **43 tests / 10 reports**; Coil desktop: **3 / 1**; IO Android host: **21 / 5**; zero failures/errors/skips in these suites. Whole batch exit 1 from picker Android **test compilation**, so no picker Android tests ran | 283 selected inputs unchanged during this held diagnostic. Archived XML hashes inspected. Real Linux filesystem, non-GUI JNI, Robolectric/provider/helper scope only |
| [Locked Rust verification](evidence/io/rust-locked-verification.json) | `cargo test --locked --jobs 1`: **5 passed**; `cargo clippy --locked --all-targets --jobs 1 -- -D warnings`: exit 0; `cargo fmt -- --check`: exit 0 | rustc/cargo 1.98.0; six Rust input hashes unchanged. `--all-targets` means this host's crate targets, not macOS/Windows compilation |
| [First iOS KLIB typecheck](evidence/gradle/first-ios-klib.verification.json), [command/result](evidence/gradle/first-ios-klib.log.result.json) | IO and picker production plus common/iOS test KLIB compilation executed successfully; Coil production KLIB compiled. **Zero runtime tests**. Batch exit 1 in unrelated navigation/Bluetooth/WiFi compilation | Pre-cross-review Linux typecheck only: no Apple link, executable, simulator or device. All 222 selected inputs unchanged; runtime dispositions unchanged. Current IO/picker typecheck appears below |
| [First picker Android execution](evidence/gradle/first-native-and-third-android-host.summary.json), [command/result](evidence/gradle/first-native-and-third-android-host.log.result.json) | Picker Android host: **30 cases / 7 reports, 28 passed, 2 failed**. File-source copy after recomposition and URI restoration returned empty destinations instead of `[9,8,7]` | All 207 selected inputs unchanged during the run. Root cause: real Robolectric stat shadow returns placeholder dev/inode 0; the original identity comparison invented a same-file no-op. This is not a passing suite |
| [Second picker Android execution](evidence/gradle/fourth-ui-ios-and-android-nav.summary.json), [command/result](evidence/gradle/fourth-ui-ios-and-android-nav.log.result.json) | Picker Android host: **35 cases / 8 reports, 34 passed, 1 failed**. Original copy/recomposition/restoration and four real-host identity regressions passed. The zero-ID case failed at its initial `Os.stat` with `HostFileStatShadow` → `InconclusiveFileStatShadow` `ClassCastException`, before refusal assertions | All 366 selected inputs unchanged. Eight picker XML hashes and log independently checked. A two-file, single-shadow-class fixture repair was refrozen; full success was pending **at this checkpoint**. Later success does not erase this failed run or establish Android kernel/device behavior |
| [First Android device attempt](evidence/gradle/first-android-device.summary.json), [command/result](evidence/gradle/first-android-device.log.result.json) | Device-test APK compilation failed for IO/picker (and selected WebView); **zero device tests executed**. Missing AndroidX test dependencies and two mixed cursor-array inference errors blocked compilation | 96 primary + 19 supplemental inputs unchanged. Build owner repairs dependencies; device-test author applied only two explicit `Any?` array types and a monitor-reuse correction. No APK/instrumentation success is claimed |
| [Second Android device attempt](evidence/gradle/second-android-device.summary.json), [command/result](evidence/gradle/second-android-device.log.result.json) | Picker: **23 executed, 6 passed, 17 failed**. Two complete public Activity cases passed (overlap preserves first request; lost bytes after actual Activity recreation report error/clean new document), plus four common contract cases. IO device compilation still failed on FileProvider nullness overrides, **zero IO device cases** | 687 inputs held. Actual software AOSP Android 15/API 35, not physical devices. Fourteen failures hit a `/proc/self/fd` pathname-stat `EACCES` probe; one category assertion, one stale monitor observation, one real hard-link `EACCES`. Failed cases remain failed; fixture errors are not assumed library defects |
| [Third Android device attempt](evidence/gradle/third-android-device.summary.json), [command/result](evidence/gradle/third-android-device.log.result.json), [independent IO review](evidence/io/android-device-third-io-review.json) | IO: **16 executed, 6 passed, 10 failed**; picker: **24 executed, 7 passed, 17 failed**; no errors/skips. IO's URI/metadata case and three public saver cases passed completely, plus nine inherited common cases. Both descriptor positive controls failed | Batch exit 1 after 821.17 seconds; 688 inputs held. Two report, two local test-APK and four manifest hashes inspected. Twenty-six cases hit `fstat EACCES` even with owned duplicates; real hardlink setup separately failed. No successful resource-lifetime suite or physical-device verification |
| [Focused descriptor control](evidence/gradle/first-android-descriptor-controls.summary.json), [command/result](evidence/gradle/first-android-descriptor-controls.log.result.json), [independent check](evidence/io/android-descriptor-first-control-io-review.json) | **One native IO probe method passed**; zero failures/errors/skips. The requested parser method is **absent**, so the intended two-method selection is incomplete despite command exit 0 | 96.02 seconds, 688 inputs held; log, XML, local test-APK and source hashes inspected. Real caller-file/deleted-open/offset and FIFO 2→1→0 control only. No production read/provider/Activity/picker or Coil operation executed |
| [Local CI-helper IO subset](evidence/ci-helper-smoke-001/receipt.json), [archive](evidence/ci-helper-smoke-001/archive.json), [independent check](evidence/io/io-desktop-ci-helper-verification.json) | IO desktop: **22 cases / 5 fresh reports, all passed**, zero failures/errors/skips; exit 0 after 71.02 seconds | Explicit `calf-io` subset, **not GitHub Actions or a full-library run**. Prior reports quarantined and test execution forced fresh. 688 before/after input maps equal; 165 current owned input hashes checked. Repeated existing methods, not 22 new cases |
| [Third picker Android host execution](evidence/gradle/second-native-and-fifth-ios.summary.json), [command/result](evidence/gradle/second-native-and-fifth-ios.log.result.json), [independent check](evidence/io/io-host35-ios63-verification.json) | **35 cases / 8 reports, all passed**, zero failures/errors/skips. The single-shadow source-zero refusal/no-write/no-delete case now passes along with original copy/restoration and host identity regressions | Whole batch exit 1 after 91.02 seconds from unrelated JavaFX/camera-host failures. 688 inputs held, 165 current owned hashes checked; all eight raw/archived report pairs inspected. Host Unix identities are not Android kernel proof; destination-zero, device and immutable-revision gates remain |
| [Post-cross-review iOS KLIB typecheck](evidence/io/io-host35-ios63-verification.json), [command/result](evidence/gradle/second-native-and-fifth-ios.log.result.json) | IO/picker production plus common/iOS test KLIBs compiled; **63 authored iOS-specific methods compiled, zero runtime tests**. Four owned compile task markers and 115 KLIB component hashes checked | Same failed aggregate command as preceding row, not a separate successful batch. 24/28 cross-review files unchanged; four differ only by verified attribution-comment insertions. No Apple link, executable or UIKit/provider execution. **Coil was not freshly compiled** |
| [First full-requested JS diagnostic](evidence/js-full-001/receipt.json), [archive](evidence/js-full-001/archive.json), [independent IO review](evidence/io/io-js-full-001-verification.json) | **IO 10/10 in two reports; picker 16/16 in four reports**, zero failures/errors/skips. Actual Chrome 153 browser execution | Whole run exit 1 after 580.12 seconds: navigation/WebView each failed a case; share failed test compilation and did not execute. 691 helper inputs held, 165 current owned hashes and all six raw/archived report pairs checked. Local root-container `--no-sandbox` wrapper disclosed; not hosted CI, Wasm, native picker UI or Coil execution |
| [Fourth Android device attempt](evidence/android-device-004/archive.json), [command/result](evidence/android-device-004/gradle.log.result.json), [independent IO review](evidence/io/android-device-fourth-io-review.json) | **IO 17 cases: 16 passed, one failed**, no errors/skips. Native descriptor and parser controls both passed. **Picker: zero XML-confirmed cases of 25 requested**, not 25 skips | Full 42-case request incomplete: bounded command exit 143 after 840.55 seconds; guard wrapper exit 1. Known-size metadata expected 64 but returned null before bound/open-count assertions. 691 inputs held, 165 current owned hashes and 21 archive items checked. Picker task began but emitted no final XML; no fresh hardlink/provider/Activity outcomes |

The 43 picker cases include nine atomic-save cases, three worker-handle ownership
cases, ten cache/isolation cases, nine MIME cases, two actual packaged-JNI smoke
cases and ten common settings/limit/error cases. JNI smoke uses **parent 0**,
creates and closes each configuration kind, and rejects invalid/stale handles
before GUI entry. It does not open a dialog or return a selected native path.
The five Rust tests are three registry/Arc lifetime/race cases and two strict
Unicode path conversions. The invalid-byte test constructs `PathBuf`/`OsString`
values, **not actual invalid-byte filesystem entries**.

IO Android host's 21 cases include five common bounds cases, eight path/size/MIME
cases, five bookmark cases, two actual InputStream ownership cases and one real
DocumentFile/ContentResolver tree-root/child metadata case against an in-process
provider. The bookmark grant store is Robolectric-shadowed; it cannot establish
real SAF persistable-grant enforcement or process/device restart behavior.
The picker Android test import was corrected to the JUnit4
`StateRestorationTester`, allowing the later 30 cases to execute. The two
subsequent failures were **not** fixed by relaxing byte-preservation assertions
or adding sleeps. Inspection of Robolectric 4.16.1's `ShadowLinux.stat` bytecode
confirmed constant-zero device/inode values; the production alias check then
skipped writing distinct files as if they were the original. The
[independent review](evidence/review/io-android-independent.md) records the
pre-correction evidence.

The focused correction refuses inconclusive identities and uses a disclosed
`HostFileStatShadow` for the host saver/alias suites: actual Unix host
`Files.readAttributes("unix:dev,ino")`, **not invented per-path identities**.
Other stat fields retain the existing shadow's semantics. Five added regressions
cover distinct files, real hard links, missing source preservation, missing
destination creation and explicit zero-ID refusal without data loss. The two
original copy/restoration assertions remain intact and passed in the second
execution. That 35-case run still failed: changing the shadow class for the
explicit zero-ID test met a Linux singleton with the preceding shadow type.
The narrowly scoped harness correction now uses **one** shadow class everywhere;
zero identity is injected only for exact fixture paths in a `try/finally` scope,
with a resetter and post-scope real-ID assertions. Zero-ID/data-preservation
assertions are unchanged, not disabled. **34/35 is not a green suite**; retry is
recorded separately: the third execution now passes **35/35 complete cases** in
eight reports, including source-zero refusal without write/deletion. Its
[independent receipt](evidence/io/io-host35-ios63-verification.json) checks every
case, raw/archived report hashes, both corrected harness files and the held
inputs. The failed 34/35 run remains historical evidence. Source-zero does not
exercise the separate destination-zero branch after a valid source, nor every
non-ENOENT stat failure. Real Android kernel/provider instrumentation, its
unresolved hard-link setup denial and immutable-revision reruns remain separate.

The [Android device-test workstream](IO-android-device-tests.md) initially added 29 methods:
10 IO, 11 direct saver/identity and eight public launcher/ActivityResult cases.
They use real framework IPC, descriptors and Activity recreation with disclosed
test providers/destination routing. The first device attempt above reached only
compilation failure; fixture/static fixes are
[separately recorded](evidence/io/android-device-first-test-repairs.json).
Neither source review nor an available emulator establishes a runtime pass.
Same-UID test providers, controlled read denial and Activity recreation must not
be represented as cloud-provider behavior, persisted cross-UID grants or process
death. Zero-length content is not the host's explicit zero-inode fixture. The
second attempt executed the 19 picker-device methods and four inherited common
cases. Only the six full successes listed above are passes; reaching earlier
byte/close assertions before a failing probe does **not** turn a failed case green.
The real hard-link setup denial remains unresolved, not waived or worked around
by weakening SELinux. Archived device/main manifests were hash-checked: fixture
providers/instrumentation belong to the test APK, not the library manifest.
The [third-run input correction](evidence/io/android-device-second-test-repairs.json)
uses owned descriptor duplication plus `fstat`, per-launch observation monitors
and the pinned CreateDocument contract's actual categories. Two positive probe
controls brought that input's authored device total to **31**; its 12 source hashes
and method count were independently checked. The third attempt executed all 31,
but only **four authored methods** passed: IO URI/metadata, saver overlap,
framework cancellation followed by a real next launch, and lost bytes after
Activity recreation. Nine common cases also passed. All 27 failed methods remain
failed, including both probe controls and the unchanged native hard-link setup.
The byte-save method no longer fails at its category assertion, but its later
probe failure means it is **not** a complete pass.

A later [read-only hardlink review](evidence/io/android-device-hardlink-policy-review.json)
identifies the exact preserved native `link` denial: `untrusted_app` to its own
`app_data_file`, matching application categories, Enforcing. The fixture already
uses private `cacheDir`; `Os.link` fails before either library call. Public AOSP
Android 15 policy explicitly forbids that app-domain operation. Ordinary app-path
or wrapper changes cannot be presumed to fix it. The original failed test and
native hardlink gate remain intact; existing symlink/document aliases and a
possible future OS bind-alias test are **not hardlink equivalence**. No policy
change or skip is used to make the full rerun green.

An additive [run-as policy review](evidence/io/android-hardlink-runas-source-review.json)
also finds `runas_app` covered by the same public AOSP hardlink `neverallow` via
`untrusted_app_domain`/`untrusted_app_all`. No `run-as` command was executed and
no ordinary app-domain provisioning workaround is established. Pre-existing
external hardlinks remain a possible input, not a waived native acceptance gate.

A [matched-kernel review](evidence/io/android-fdinfo-kernel-review.json) binds the
positive control's concrete `pmsg_device` character-device `getattr` denial to the
kernel revision reported by this emulator. Duplicating an inherited descriptor
does not grant permission to inspect every underlying object. The lead authorized
a test-only `fdinfo` inode-prefilter/calibration correction, now
[independently source-reviewed](evidence/io/android-device-fdinfo-source-review.json)
for a focused IO probe diagnostic. Two parser controls bring that new checkpoint
to **33 authored methods**, not 33 passing tests. The focused command above later
executed only the native IO control successfully; its requested parser case is
absent from the report, not a pass. Full production/provider and picker scenarios
still require a new run.
Unknown/malformed header data and same-inode `fstat`
errors must still fail. Provider and caller REG/FIFO descriptors must first prove
the assumed native `st_ino`/kernel-header agreement; raw mount-ID equality is not
a valid negative filter across provider mount namespaces. The review explicitly
retains full-provider, same-regular-file duplicate and reader-error control gaps;
the parser streams rather than bounds the complete `fdinfo` text. No device policy
or hard-link expectation is relaxed, and no finding status is promoted.

The [fourth device review](evidence/io/android-device-fourth-io-review.json) now
provides complete passing IO methods for actual provider read/close, retained
source ownership through EOF, unknown-size bounds, both native reliable-pipe
errors, already-cancelled no-open behavior and 16 success/failure pairs without
descriptor accumulation. Both the IO native probe and its previously absent
strict parser control execute successfully. Eleven authored IO methods and five
inherited common methods pass; the **IO suite still fails** its twelfth authored
method, and the full request times out before any picker result is verified.
The current picker probe/parser, saver provider and all Activity scenarios still
need fresh complete results. No genuine hardlink pass is established.

The known-size case fails at `KmpFileDeviceTest.kt:163`, before the read-bound and
zero-open/descriptor assertions. Its log records a null-cursor warning and a
provider process being killed/restarted, but the cause of the null metadata is
unproven. A [cached-AAR inspection](evidence/io/android-device004-metadata-static-review.json)
finds a `DocumentFile` MIME-column query unsupported by FileProvider. The same
zero-column warnings appear in two **passing** cases, so this is not proof that
the mismatch killed the provider or caused the failed size precondition. No
source repair or skip is justified as already verified from that correlation.

The independent review checks all 17 raw/sanitized XML identities, 18 private-log
hashes, seven metadata pairs and 35 preserved earlier report files. The separate
[artifact inspection](evidence/io/android-device004-local-artifact-review.json)
checks two local APK hashes and four manifests, **not installed-byte attestation**.
Archived cleanup receipts report no remaining device/owned watchdog; emulator
exit -11 during requested teardown is retained separately from command exit 143
and the one assertion failure. This is bounded software API 35 evidence, not
physical-device, minimum-API, cloud-provider, Coil or immutable-release clearance.

The first iOS typecheck establishes that the **pre-cross-review** interop and test
source compiled to KLIB; that receipt alone cannot establish later edits. Existing
expect/actual/BetaInterop warnings and an unused export expression were observed;
it was not a warning-free build. The focused iOS review added **12 test methods**
without removing the original 51: IO now has 23 and picker 40 authored iOS methods.
These additions cover non-file URLs, Foundation staging ownership and injected
session-phase completions. None executes `presentIosDialog` with a real window,
provider or native transition; native runtime execution remains **zero**. The
post-review source/test changes have now passed a fresh Linux KLIB check:
**four owned production/test compile tasks**, with all **63 iOS-specific methods**
retained. The [new receipt](evidence/io/io-host35-ios63-verification.json) checks
115 component hashes across IO/picker main/test KLIB outputs and the native
`ios_simulator_arm64` manifests. This is no Apple link or runtime pass. Coil was
not selected in this command; its earlier compile evidence remains separate.
Expect/actual, BetaInterop and host-test deprecation warnings remain. Original
cross-review source hashes are in the
[correction checkpoint](evidence/io/ios-cross-review-correction.json).

Before the latest helper/host/typecheck diagnostics, the lead added 170
[attribution comments](evidence/attribution-notices-20261024T2210.json),
[independently reviewed](evidence/review/attribution-notices-independent-20261024T2210.json).
The IO receipt independently binds all 28 cross-review files: 24 exact unchanged
hashes and four exact reversible comment insertions. This preserves the old
receipts rather than relabeling changed hashes as unchanged. Both diagnostics
held 688 inputs; the area owner additionally checked all 165 current owned inputs.
The [local helper receipt](evidence/io/io-desktop-ci-helper-verification.json)
also verifies all 11 archived items, five fresh report pairs and the distinction
between the canonical sorted file-hash/path input digest and the raw JSON hash.
Its 22 desktop methods repeat five common bounds, three bookmark, six metadata,
two path and six RawSource cases. Other test-bearing modules were explicitly
not requested; neither full CI nor Coil execution is implied.

Unexecuted test source is not execution evidence. The first full-requested JS
diagnostic now executes the authored IO/picker browser tests in Chrome 153:
IO's five common bounds methods and five File/FileReader/metadata methods, plus
picker's four common contract, five DOM session, four download/owner and three
save-bridge methods. Repeated common functions are not new independent coverage.
The [independent receipt](evidence/io/io-js-full-001-verification.json) checks all
26 testcase outcomes, six raw/archived report pairs, nine selected test-source
files, both actual task markers and all 55 archive-manifest hashes. Its helper
snapshot contains 691 inputs, not the broader 703-file bootstrap/notice set.
Overall failure remains recorded; a full requested run is not a full passing run.

The browser save-operation tests use a disclosed OS API fixture with real native
Promise and bridge behavior, **not** actual user grants or destination writes.
Download tests inject scheduling/click hooks while using real anchors/Blob URLs;
they do not observe downloads or prove the 40-second retention policy. FileReader
tests use actual browser File/FileReader, with a synthetic error event for failure
dispatch (not an OS-revoked file grant). Browser execution used a disclosed local
root-container `--no-sandbox --disable-dev-shm-usage` launcher, not a production
WebView change or browser security clearance. Coil had only four up-to-date
package-metadata tasks, no fresh compilation or execution, and is explicitly
uncovered in this JS plan. Wasm and ordinary frozen dependency enforcement remain
separate gates.

Android host tests use real ContentResolver/ParcelFileDescriptor/DocumentFile
against an in-process provider and Compose/Robolectric restoration. The separate
device workstream uses actual framework IPC and Activity recreation; neither is
cloud-provider or killed/restarted-process verification. Apple tests construct actual platform
objects and filesystem data but cannot be run on this Linux host.

Queued coordinated tasks include IO/picker `wasmJsBrowserTest`, immutable JS
reruns and actual browser integration, Coil browser compilation, the complete
Android-device/provider rerun and Apple
linking/simulator tests. The passed desktop and Android-host suites still need
immutable-revision reruns and the missing integration scenarios; current IO/picker
KLIB compilation does not remove any Apple runtime gate. Cargo locked
test/clippy/fmt checks are recorded above; schedule subsequent runs with the lead
and avoid parallel unbounded Rust/Gradle builds.

### First full Wasm diagnostic and FileReader correction (2026-10-25)

The [first full-requested Wasm run](evidence/wasm-full-001/archive.json) failed
with exit 1 after 418.94 seconds. Its 211 passed cases in 14 modules do **not**
include IO or picker: `BrowserFileRead.kt:41:88` could not resolve `name` on
Wasm's nullable `JsAny` error binding. IO's dependent camera/picker/share tests
were absent; WebView had a separate compiler failure. These are missing suites,
not skips or passing IO builds. The
[scoped review](evidence/io/wasm-filereader-error-bridge-review.json) rechecks all
42 archive hashes, seven raw metadata pairs, 33 raw/archived XML pairs, their 211
case identities, and the equal 691-input before/after maps.

After that failed run was archived, the lead authorized exactly six IO web
production/test files. A nullable-string expect/actual bridge now reads
`FileReader.error` and its name once, accepts only string names, and retains the
existing name-only IOException prefix and `unknown error` fallback. No native
message is included. The receipt binds the cached KLIB metadata, each pre/post
source hash and a reversible [scoped patch](evidence/io/wasm-filereader-error-bridge.patch).
The other 159 owned inputs, including all 42 Android inputs, remain unchanged.

The old synthetic-error test could pass via the immediately following abort.
It now checks handler detachment and the exact error **before any abort**. Two
additional tests expose a real `DOMException("ignored native message",
"NotReadableError")` or a non-string name through a disclosed instance-only
getter; neither fixture is actual OS read denial. Each error getter permits one
read, cleanup removes the property, and finally stops the native read. All five
earlier web methods are retained: seven web plus five common methods means
**12 expected IO cases per browser target**, not 12 executed cases at this
checkpoint. Fresh full Wasm and focused JS runs are pending with the lead.
JS003 and the original Wasm failure remain immutable historical evidence;
the IO resolution ledger and all runtime/release gates are unchanged.

### Second full Wasm diagnostic and default timer adapter (2026-10-25)

The [second full Wasm run](evidence/wasm-full-002/archive.json) held 693 inputs
but still failed: exit 1 after 181.03 seconds, with 244 passed cases in 16 modules.
IO's production, test and executable compile tasks ran, but its browser bundle
could not resolve `skiko.mjs`, followed by a Karma disconnect. IO has **zero
XML-confirmed cases**, not an asserted FileReader failure or a runtime pass.
Picker compilation separately failed at `FileSaverLauncher.web.kt:127:72`:
Wasm's timer callback requires nullable `JsAny`, not `Unit`. The matching latent
test-helper expression was found at `BrowserSaveOperationTest.kt:64`.

The [scoped source review](evidence/io/wasm-default-timeout-adapter-review.json)
binds all 50 archive hashes, seven raw metadata pairs, 40 XML pairs and 244 case
identities. The authorized [five-file patch](evidence/io/wasm-default-timeout-adapter.patch)
adds only final `null` to both callback bodies and one default-adapter test with
JS/Wasm timer spies. Production delay remains **40,000 ms**, the test helper
remains **0 ms**, and the URL limit remains **32**. Callback and registration
exceptions are not caught or replaced by the production correction.

The new synchronous test omits `schedule`, unlike every prior download test.
Its spy forwards the unchanged receiver and arguments to the saved native timer,
records real handles, and checks exact delay, anchor cleanup, null callback
returns, two full 32/33-capacity rounds and repeated release. Callbacks are
**manually invoked**, not proof of elapsed 40-second dispatch or downloads. The
failure-safe finally restores the descriptor, attempts every timer clear and
every retained release callback, and preserves a primary assertion failure.
All four prior download methods remain byte-identical: **17 expected picker
cases per browser** are authored, not executed, at this checkpoint.

The previous six FileReader source hashes, Android sources, baseline findings,
JS003 and Android004 receipts and resolution statuses remain held. Separately,
the build owner changed IO's Gradle convention under lead authorization to address
Skiko packaging; this area owner neither edited nor certified that build repair.
Fresh coordinated Wasm/JS execution and all original native/release gates remain.

### Remaining release/runtime work

1. Immutable cross-platform CI, native payload manifest/ABI checks and consumer
   fixtures. Diagnose test failures rather than masking/omitting failing targets.
2. IO-023 genuine parent-window ownership/threading, then real native picker/save
   UI tests on supported desktop backends and physical Apple/Android providers.
3. iOS ASan/guarded-buffer checks, security-scope grant/restart/stale-bookmark
   coverage, nonempty photo provider duplicate/cancel races, interactive dismiss,
   disk-full staging and returned export URL access. Include attached-window
   normal/rejected presentation, two owners competing while save staging is held,
   dispose during presenting/dismissing, interactive rollback and no-coordinator
   completion. Policy tests are not native safe-point proofs.
4. Android null/partial-failing resolver stream and close integration (the two
   InputStream helper cases passed), permission revocation,
   process death/restart, native photo picker/fallback limits and provider cleanup.
5. Real Chromium save integration; Safari/Firefox download fallback, large Blob
   retention and native user-activation tests. Fixture tests cannot certify these.
6. Coil real decoder-failure/cancel ownership, modified-file request key policy,
   per-target peak-memory profiling and decoded-image bounds.
7. Windows cache ACL/loaded-DLL behavior, foreign-owned cache/noexec deployment,
   real invalid-byte Unix filename selection and JNI result conversion cleanup.

No package, release, deployment, commit or GitHub issue state was mutated by this
area owner. Findings stay open until the lead reconciles these results with each
original `required_tests` and the owner-authorized preview gate.


### Paired browser004 execution after the scoped repairs (2026-10-25)

The earlier “authored, not executed” and pending-Wasm paragraphs are historical
checkpoints, not current execution claims. Their original outcomes and source
receipts remain intact. The new
[paired independent readback](evidence/io/io-browser004-verification.json)
confirms actual execution of the repaired IO/picker methods:

| Lead-run archive | Actual outcome | IO / picker |
|---|---|---|
| [Wasm003](evidence/wasm-full-003/archive.json) | Exit 1, 65.01 s; 241 passed elsewhere; IO compile rejected missing Compose Runtime | No owned runtime pass |
| [Wasm004](evidence/wasm-full-004/archive.json) | Exit 0, 123.02 s; 290/290, 19 requested test-bearing modules, 48 XML | 12/12 and 17/17 |
| [JS004](evidence/js-full-004/archive.json) | Exit 0, 130.03 s; 290/290, 19 requested test-bearing modules, 48 XML | 12/12 and 17/17 |

The build owner's [second correction](evidence/build/io-wasm-skiko-002.json)
retains official Compose resource wiring while selecting an empty
`composeCompiler.targetKotlinPlatforms` for IO, which has no Compose declarations.
It does **not** add a runtime dependency to hide the missing-runtime diagnostic.
Current IO build-file hash is
`b9bd58c259400dd614aa92f814fc4e74189b6cec0e7ada3485cf27c8576c6b45`.
The third-run [compiler supplement](evidence/wasm-full-003-io-compiler/failure-review.json)
and Wasm001/002 failures remain unchanged. This IO readback binds the build-owner
receipt/current source and the resulting runtime, not every plugin hook or target.

Both browser archives' **58 manifest files**, seven raw metadata pairs and all
48 raw/archived XML pairs were independently checked. Each owned task has one
fresh execution marker and matching runtime marker; raw report times fall inside
the invocation and match their archived timestamps. The nine selected IO/picker
test-source files per target yield exactly the executed method sets. All 693
before/after input hashes agree across JS004, Wasm004 and the desktop subset below;
they and all 165 owned inputs matched current files at **01:43:55 UTC**. This is a
dated dirty-source checkpoint, not a promise that later coordinated edits share
the same inputs. The raw JSON input hash is distinct from the helper's sorted
hash/path digest; both were checked.

IO's 12 cases are five common bounds/allocation methods plus seven browser
read/metadata methods. Six of those seven exercise FileReader; named and malformed
errors use the disclosed instance-only getter and **synthetic error dispatch**,
not OS permission revocation. Exact diagnostics and handler detachment are now
checked before a late abort can mask failure. The seventh method confirms browser
File metadata for extensionless, dot and ordinary names. No Apple memcpy/ASan or
Coil decoder behavior follows from these checks.

Picker's 17 cases are four common contracts, five DOM session/owner cases, five
download/owner cases and three native-Promise save-boundary cases. Selection and
`showSaveFilePicker`/writable boundaries remain disclosed fixtures; there are no
real user grants or destination writes. The new default scheduler method forwards
real native timer registration at unchanged **40,000 ms** and records 64 handles
across two 32/33-capacity rounds. It **manually invokes** captured callbacks twice,
checks actual JavaScript `null`, anchor cleanup and recovered capacity, then
clears/restores the timer fixture. The click hook avoids a real download. Neither
elapsed 40-second delivery nor browser download consumption/completion is proved.
All four older download method bodies remain unchanged. Together the two targets
execute **58 instances of 29 source methods**, not 58 independent tests.

The [Wasm context](evidence/wasm-full-004-context/context-review.json) and
[JS context](evidence/js-full-004-context/context-review.json) each have 24 checked
manifest entries and 19 fresh raw/config-selected pairs. Independent JSON parsing
verified selected fields from the **first literal** `config.set` only, without
executing JavaScript. Wasm references the requested prepared Kotlin tooling home;
JS references repository `build/js`. Twelve Wasm extra inputs (including five
prepared tooling files) and seven JS extra inputs match before/after/current at
readback. These path/hash observations do not attest all installed dependencies,
later executable webpack configuration or running-process bytes.

Fresh runtime is not forced recompilation: Wasm IO production compilation was
`FROM-CACHE`, and its test/executable/resource tasks included `UP-TO-DATE` outcomes.
JS IO compilation and both browser test tasks did execute. Coil has only four
up-to-date package-metadata tasks per browser, **no fresh Coil compile/test**.
“Full” here means the helper-discovered test-bearing suite, not every library
feature or target. Chrome 153.0.8010.36 on Linux x64/Java 17.0.20 used the disclosed
root-container `--no-sandbox --disable-dev-shm-usage` launcher; this is not
production sandbox or hermetic dependency/release clearance.

### Post-plugin desktop IO regression subset (2026-10-25)

The [desktop001 archive](evidence/io-nav-desktop-001/archive.json) and
[independent IO review](evidence/io/io-desktop-post-plugin-001-verification.json)
confirm **22 IO + 51 navigation = 73 passed**, exit 0 after 36.01 seconds. This is an
explicit two-module subset (`complete_suite_requested=false`), not full-library
CI. Navigation's report totals were corroborated, not its implementation reviewed
again by this area owner. The task-owned Xvfb
[launch context](evidence/io-nav-desktop-001-context/context-review.json) binds five
extra driver/executable hashes; it is not process/dependency provenance.

All 19 archive items, five raw metadata pairs and 11 raw/archived reports checked;
five reports and 22 methods belong to IO. A fresh IO task/runtime marker appears at
sanitized log lines 142/143, with fresh production/test compilation markers and
report times inside the run. The five test-source hashes match the earlier helper
smoke run: five common bounds, three bookmark, six metadata, two path and six
RawSource methods repeat after the build-plugin change. These are **not 22 new
tests**, nor picker/Coil or native-dialog execution.

No new Android-host/device result is supplied by these browser/desktop receipts.
A host preflight stop is not a Gradle/library test result; any later actual host
run needs its own verified handoff. Android-device004 remains 16 passed/one failed
IO case, zero final picker cases, expected-64/actual-null metadata failure and an
unproven provider-death cause. Existing Apple/native, real browser grants/downloads,
Coil, immutable-revision/API/ABI/consumer and dependency gates remain.

The resolution ledger only appends these scoped checks and remaining requirements;
all original tests/requirements remain prefixes. Its statuses stay **16 partially
verified, nine implemented, one unresolved, zero verified**; IO-023 remains
unresolved. No issue closure, new build/device/network execution, source change,
containment change or publication was performed by this reviewer.


### IO-only Android-host002 follow-up (2026-10-25)

The [new host archive](evidence/io-android-host-002/archive.json) and
[independent IO readback](evidence/io/io-android-host-002-verification.json)
now supply a separate post-plugin **JVM Android-host** result: **21/21 passed**,
exit 0 after 53.01 seconds, five fresh XML reports. This supersedes the preceding
“no new Android-host result” statement only at that earlier checkpoint; it does
not rewrite an old attempt or establish Android-device behavior. Only calf-io
was requested (complete_suite_requested=false), with no picker or Coil task.

| Existing suite | Passed methods | Actual boundary |
|---|---:|---|
| BoundedReadTest | 5 | Common bounds/allocation/closure policies on JVM |
| DocumentTreeMetadataTest | 1 | AndroidX DocumentFile/ContentResolver under Robolectric with in-process MatrixCursor provider |
| KmpFileAndroidTest | 8 | Robolectric URI/path transforms and host temporary-file size/MIME metadata |
| KmpFileBookmarkTest | 5 | Shadow-managed permission bookkeeping and host file bookmark policy |
| ReadOwnershipTest | 2 | Injected JVM InputStream read/close failure and empty-success handling |

All 13 archive files, five raw metadata pairs and five raw/archived XML pairs were
checked. Exact testcase identities/statuses match the five selected test-source
files and report timestamps lie inside the invocation. Fresh IO task/runtime
markers are at sanitized log lines 100/101; compileAndroidMain and
compileAndroidHostTest also have fresh markers. Other outputs can be reused by
Gradle; this is not a forced clean build or artifact/ABI consumer test. The
[host launch context](evidence/io-android-host-002-context/context-review.json)
has five checked manifest entries and two unchanged executable/driver hashes,
not whole-process/dependency provenance.

Fourteen methods use RobolectricTestRunner; seven common/helper methods are
plain JVM. The selected robolectric.properties requests **sdk=35**. Runtime
identity separately records the installed compile platform **37.0**, revision 2,
extension 22. Neither number is evidence of an Android device/minimum runtime.
The folder fixture supplies a synthetic child size **42**, while the local-file
fixture uses **1234** bytes; neither is the device004 known-size **64** scenario.
Bookmark permissions are managed by Robolectric shadows, not acquired through a
real user grant or tested after process death. The two read/close tests inject an
InputStream; they do not open a real ContentResolver/ParcelFileDescriptor or Coil
pipeline. These are 21 existing methods executed again, not 21 new authored tests.

The [host001 preflight failure](evidence/io-android-host-001-preflight/failure-review.json)
is preserved: exit 2 after 0.68 seconds, zero Gradle/library tests, and no runtime,
Gradle log or helper receipt. Its raw directory contains only the original input
snapshot and plan. The old numeric predicate rejected the installed SDK property
AndroidVersion.ApiLevel=37.0. The separately archived
[two-file helper repair](evidence/build/runtime-context-android-api-001/receipt.json)
accepts the recorded major.minor identity without truncating it or modifying SDK
metadata; this IO reviewer did not rerun its offline tests or edit either script.

Host002 holds 693 identical before/after/current input hashes at the independent
readback (**01:58:34 UTC**). Its input set differs from earlier browser004 and
desktop001 snapshots only in scripts/ci/runtime_context.py and
test_runtime_context.py; the other 691 and all 165 owned inputs are unchanged.
Old snapshots, the first preflight failure, browser/desktop receipts and their
outcome histories remain intact, rather than being relabeled with new hashes.

**Android-device004 remains unresolved:** 16 passed/one failed IO case, zero final
picker XML of 25 requested, and expected-64/actual-null metadata before the
bounded-read/open-count assertions. Provider death/restart is observed, its cause
unproven. No device/emulator operation or native provider/grant/process-death,
hardlink, saver, Apple/ASan or Coil gate is satisfied by the host result. Likewise,
no publishing metadata/immutable revision/consumer/API/ABI or release gate changes.

Seven bounded host entries and seven remaining notes were appended to the ledger;
all prior tests/requirements, fixed fields and statuses are preserved by the
[prefix readback](evidence/io/io-android-host-002-ledger-prefix-verification.json).
Counts remain 16 partially verified, nine implemented, one unresolved and zero
verified; IO-023 remains wholly unchanged and unresolved. Only IO documentation
and additive JSON evidence changed in this follow-up.


## Immutable Android follow-up — 2026-10-27

The [reviewed67-case run](checkpoint-android-runtime-20261027.md) atab213b40
passes all17 IO methods and24/25 picker methods on the owned Enforcing API35
emulator. All8 real FileSaverActivityDeviceTest ActivityResult/recreation cases
pass; IO-002 gains only that scoped additive evidence. Its prior tests/fields and
all other IO ledger records are unchanged, checked by the
[prefix review](evidence/io/io-android-hosted-40436756084-ledger-prefix-verification.json).
No OS process-death, physical/minimum-API, complete native-parent, consumer/ABI
or release claim follows. The hard-link case fails at Os.link EACCES before save
assertions; its real-inode/bytes/cleanup requirements remain unmodified and open.
Reference AOSP rules do not prove the installed policy or establish run-as as a
safe successful fixture provisioner. No root or SELinux bypass was used.
