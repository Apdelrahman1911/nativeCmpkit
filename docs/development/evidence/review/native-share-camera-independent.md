# Independent Desktop/Rust share and Android camera review

Reviewed on 2026-10-24 by the navigation/core/icons owner, independently of the
native implementation owner. This is a **read-only implementation and archived
result review**, not a new build, test run, native stress run or release approval.
The reviewer changed no library/test/build source, ran no Gradle/Cargo command,
and made no GitHub changes. Baseline findings and their issue histories remain
unchanged. `R1`–`R3` below are local review references, not new baseline IDs.

## Revision and review boundary

- Original audit baseline: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`.
- Current base: `94d2492e99d5cbc060409d94d9f88febd06222d5`, plus coordinated
  **uncommitted** development. This is not an immutable release candidate.
- Relevant original findings: NATIVE-019–025, 027, 029–034. Android/iOS/Web share,
  iOS camera and WebView were not comprehensively re-reviewed here. Their
  separate native/device/browser acceptance gates are not satisfied by this
  scoped review.
- The first Android source inspected matched
  `../gradle/first-native-and-third-android-host.inputs.json`: SHA256
  `2267c0a6ab8bf6692d37e05f3c9acaa3b386997a7dbc6250bf5f9e99faeb01ba`.
  **R1 and R2 describe that pre-repair source**, not the later replacement.
- During report preparation, the native owner supplied a lifecycle/identity
  repair. Its Android source was read again at **2026-10-24T20:00:13Z**: SHA256
  `9b220f954818780c1c183914c553620d7ae477bc25bce1e0804a36924e88111c`.
  The separately labeled repair check and R3 describe that snapshot. A subsequent
  change requires another review; no old result is silently promoted to it.
- The R3 handoff repair was then read at **2026-10-24T20:13:16Z**: Android
  SHA256 `806793b5c9e9ab5bcb064e257045788c986046907e4123a33310b6c7dc6ff917`.
  Its separate repair check below does not assume the native owner's overall
  edit window was frozen and does not add any executed-test evidence.
- Rust/Desktop share production still matched the receipts listed below at that
  checkpoint. Some Kotlin tests had already changed after failed compilation;
  they are prepared tests, not passing executions.

**Conclusion after the three source snapshots:** the Rust/Desktop replacement removes the
specific baseline raw-owner leak and blocking-new-launch paths in source, but
AppKit runtime ownership/cancellation remains unverified. Android camera had two
concrete review findings, followed by a source repair; a further context-replace
ownership defect was found and then source-repaired. The three exact source
traces are addressed in the latest reviewed camera snapshot, but their new host
regressions have not run and device gates remain. No finding closure is justified
by this review alone.

## R1 — Restorable non-configuration destruction deletes camera output

**Priority:** High. **Status:** confirmed-source policy defect in the pre-repair
snapshot; actual don't-keep-activities/device reproduction not performed.
**Related:** NATIVE-019 and NATIVE-024.

### Exact source and execution

`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt`,
pre-repair SHA256 above:

- Lines 130–132, `DisposableEffect`: calls
  `result.dispose(context.activity()?.isChangingConfigurations == true)`.
- Lines 84–88, `dispose`: every other disposal takes/clears the pending request
  and deletes its owned output.
- Lines 69–81, `handleResult`: missing/empty output is rejected, even if the
  external camera reports success.

Saving the URI/path pair fixes the original lost-field problem at baseline
lines 28, 42–48 and 59–73, but does not make the file survive deletion. A host
Activity can save the request, then be destroyed while the external camera is
foreground without `isChangingConfigurations` being true. Android's
don't-keep-activities scenario is specifically required by NATIVE-019. Treating
every non-configuration disposal as permanent UI abandonment unlinks
`nativecmpkit-camera/capture-*.jpg` even when the saved request will be restored.
If the camera already holds an open file descriptor, it can finish writing an
unlinked inode; a restored path/URI cannot recover that data.

The then-existing `AndroidCameraRequestTest.restoredSuccessUsesSavedUriAndIsDeliveredOnceToNewOwner`
(lines 36–59) manually called `dispose(recreatingActivity = true)` and restored
the saver. It bypassed the actual Activity/Compose disposal classification. It
could pass without covering this defect.

### Required correction and tests

Distinguish restorable host destruction, including non-configuration system
destruction, from explicit navigation removal/finish. Request ownership must
follow Activity/SavedState/ActivityResult lifetime, not only a configuration bit.
Do not unlink an external writer's active output merely because a callback was
unregistered. The corresponding abandoned-cache retention/cleanup policy must
be documented rather than silently claimed as immediate cleanup.

Required cases: actual don't-keep-activities capture/return; configuration
recreation; process recreation with saved state; ordinary navigation removal;
explicit Activity finish; external writer still open; cancellation; exactly one
readable successful result; no old-owner callback or unrelated-file deletion.

### Subsequent source repair check — not executed verification

In SHA256 `9b220f…`, lines 89–98 no longer unlink on disposal. Lines 119–127 use
the host Activity's finishing/configuration/destroyed/lifecycle state, not a
navigation entry's potentially destroyed lifecycle. The lifecycle check also
addresses Compose disposal during `ON_DESTROY` before `Activity.isDestroyed`
becomes visible. Known terminal cancel/launch-failure paths still clean their
owned file; successful outputs stay caller-owned.

`AndroidCameraLifecycleTest.kt` adds four real ComponentActivity/Compose/registry
host scenarios: non-finishing non-configuration destruction/restoration
(91–122), Activity recreation/cancellation (124–140), composition removal
(142–168), and finishing destruction (170–189). It retains an actual host file
writer across destruction, rather than just manually selecting `dispose(true)`.
It supplies bytes/result codes explicitly: **no external camera, process kill,
device developer option, or provider/recipient grant is exercised**. At this
review checkpoint these new tests had not run. They are an appropriate stronger
fixture, not proof R1's full required matrix has passed.

## R2 — Reentrant callback exception clears the next camera request

**Priority:** Medium. **Status:** confirmed-source branch defect in the
pre-repair snapshot under synchronous/custom ActivityResult delivery. Ordinary
Android `TakePicture` delivery is normally asynchronous; there is no claim this
trace was reproduced with a normal device camera. **Related:** callback and
ownership requirements in NATIVE-020/021/023/024 and NATIVE-032's analogous
share callback rule.

### Exact source and trace

Same pre-repair Android file:

- Lines 48–50 install request A and enter `launcher.launch`.
- Lines 71–81 consume A before the application callback.
- Lines 52–57 distinguish callback errors using only
  `if (launchEntered && request.pending == null) throw error`, then take the
  pending slot and delete A's local output.

A synchronous registry callback can finish A, call the application's callback,
and let that callback launch B before throwing. B now occupies `request.pending`,
so A's catch misclassifies the callback exception as A's launch failure. It
clears **B**, deletes **A's successful output**, and invokes an additional Failed
callback for A. B's output is also left untracked. A non-null pending slot is not
evidence that A still owns it.

The earlier `callbackFailureCannotBeRemappedOrDeliveredTwice` test
(`AndroidCameraRequestTest.kt:99–109`) called `handleResult` after `launch`
returned. It did not execute the outer launch catch or a reentrant replacement.

### Required correction and tests

Capture the exact request/token installed by each launch. Clean the pending
slot only while it is still that operation. If a callback already consumed or
replaced the operation, propagate its exception without touching the new request
or delivered output. Regression: a synchronous driver delivers successful A;
A's callback launches B then throws; observe one A result, A's readable output,
B still pending, and no synthetic Failed result. Then complete/cancel B normally.

### Subsequent source repair check — not executed verification

SHA256 `9b220f…`, lines 41–62 stores `launchedRequest` and uses referential
identity (`request.pending !== launchedRequest`) in the catch. This addresses
the exact A-to-B trace without treating structural equality as ownership.
`AndroidCameraRequestTest.kt:111–150` now drives that trace through the real
owner and preserves A's bytes while cancelling B. This new test had not run at
the reviewed checkpoint. Source repair does not establish normal-device timing
or broader ActivityResult compatibility.

## R3 — Context replacement disposes a request now owned by the replacement

**Priority:** Medium. **Status:** confirmed-source conditional execution path;
not an executed reproduction. **Related:** NATIVE-019/020/024. This finding
describes the **post-R1/R2-repair** SHA256 `9b220f…` snapshot.

### Exact source and trace

- Same Android file, line 141: `rememberSaveable` keeps the `CameraRequestState`
  at the existing composition slot.
- Lines 143–145 keep the registry launcher at that slot.
- Lines 146–148: changing `LocalContext` identity recreates the camera owner.
- Lines 149–154: the replacement is installed in `owner.value`; old disposal
  correctly avoids nulling that new owner, but still calls the old owner's
  `dispose(context.retainCameraRequestForActivityRestoration())`.
- Lines 89–92: the old owner's `dispose(false)` clears the **shared** request.

Providing a new `ContextWrapper` of the same live Activity through
`CompositionLocalProvider(LocalContext provides wrapper)` is sufficient to
change the remember key without destroying the Activity or the saveable slot.
Both owners use the same pending state. The old Activity is not finishing,
changing configuration or destroyed, so its disposal clears the request that
the replacement was meant to handle. A later registry result reaches the new
owner, sees no pending request and is dropped. The output survives after R1's
repair, but successful capture delivery is still lost; a new launch can also be
admitted before the old external camera returns.

The `owner.value === result` guard protects only the callback-holder reference,
not the request's ownership. No context-change scenario was present in the
four new lifecycle tests inspected above.

### Required correction and tests

Treat same-slot owner replacement as responsibility transfer when it shares the
same request state. Disposing an old owner must suppress its own callbacks but
must not abandon a replacement's pending request. Keep ordinary composition
removal/finish semantics separate; do not retain every abandoned request merely
to make this scenario pass.

Add a Compose host regression that launches capture, replaces `LocalContext`
with a distinct wrapper of the same live Activity, verifies the launcher owner
changed without a second external launch, rejects overlap as Busy, and delivers
the original result exactly once to the latest callback. Also test context
replacement followed by disposal and callbacks that throw/reenter. Any repair
needs re-review and lead-coordinated execution. Both native owner and lead were
informed before this report was finalized.

### Subsequent source repair check — not executed verification

At 20:13:16Z the native owner's Android SHA256 `806793b5…` adds
`successorOwnsRequest = owner.value != null && owner.value !== result` at lines
152–156. Old disposal now retains the request when the same-slot successor is
already installed, while still marking the old owner disposed. The actual owner
is cleared/abandoned normally when no successor/restoration path exists. This
addresses the specific shared-holder transfer defect without deleting the file
or removing ordinary abandonment.

The updated `AndroidCameraLifecycleTest.kt:38–65,198–215` changes the provider's
context value without changing composition identity, asserts owner replacement,
checks the original request still rejects overlap as Busy, then delivers the
original registry result and reads its exact bytes. Its separate `DisposableEffect(Unit)`
observation confirms this is not being replaced with an Activity-destruction
fixture. The lifecycle file now has **five**, not four, tests; SHA256
`ba2ce7bc94eca8b896f484210d35de4250cb64594f88a712e3b7b1307b349361`.
This is a prepared regression; compilation/execution and additional combined
handoff/disposal/reentrancy scenarios remain unverified.

## Positive source checks: Rust/JNI and AppKit ownership

These checks remove specific baseline defect mechanisms; they are **not a
native memory-safety certification**.

| Boundary | Inspected implementation / finding relation |
|---|---|
| JNI signatures and inputs | `calf-share/native/src/lib.rs:20–104,150–184` keeps old exports and adds ABI1 begin/take/cancel/counts. Input strings are owned Rust data; each array element is validated and its JNI local reference deleted. A bad element aborts the whole conversion rather than being silently omitted. |
| No borrowed window dereference | `lib.rs:187–203` rejects nonzero `parent_window`; focused window/view are acquired on AppKit Main instead. This is a documented compatibility restriction, not support for old arbitrary addresses. |
| Registry identity and bounds | `operation.rs:27–75`, called through the mutex at `lib.rs:12–18`, uses monotonically increasing IDs, one active slot, a maximum of 64 unconsumed results and first-final-result compare/exchange. A late old ID cannot release a newer active slot. Cancellation drops the registry Arc but holds admission until cleanup acknowledges completion. |
| Strong native ownership | `macos.rs:18–32,129–146` owns picker, delegate, selected service, subject, item array, window, view and completion in a Main-thread-local table. The Objective-C ivar contains an integer ID, not an owning raw Arc. There is no baseline `mem::forget(delegate)`/unbalanced `Arc::into_raw` scheme (NATIVE-029). |
| Thread confinement | `macos.rs:58–87,156–160,297–329` checks actual AppKit Main and dispatches only Rust `Send` values. It does not assert unsafe `Send` for retained AppKit objects. No temporary mutex guard crosses a UI wait. |
| Presentation prerequisites | `macos.rs:39–45,58–128` checks class/close-selector availability, cancellation, delegate class/ivar, key window/content view, URL creation and nonempty items before presentation. Native owners are installed before delegate-exposing calls. |
| Cleanup order | `macos.rs:156–178` removes the owned operation, detaches picker/service delegates, closes the picker, drops retained owners and only then publishes the final result/releases admission. Delegate completion schedules a later Main turn rather than releasing its receiver during the callback. |
| Stage-accurate result | `macos.rs:188–259` treats service selection as nonterminal, `didShareItems` as success, `didFailToShareItems` as failure and picker dismissal as dismissal (NATIVE-025). Subject is supplied through `service.setSubject`, not silently discarded (034). |
| Panic/exception boundary | `macos.rs:215–235,311–321` catches Rust panics around the service-delegate body and dispatched action. It **does not catch Objective-C exceptions** or prove every FFI/runtime failure is recoverable. |
| Compatibility adapter | `lib.rs:106–140` retains `showShareSheet`, refuses to block AppKit Main and uses one absolute 300-second deadline. New Kotlin no longer calls it (030). Keeping a descriptor does not certify old binaries' behavioral compatibility; FAILED=3/nonzero-window rejection are additional semantic changes. |

`delegate_for_service` keeps a `RefCell` borrow during its short Rust
retain/replacement operations, then releases it before `setSubject`. No definite
AppKit reentrancy fault was established in this review. Actual callback ordering,
late native callbacks and Objective-C retain/release behavior still need the
runtime matrix; they must not be inferred from a sequential Rust Arc test.

## Positive source checks: Kotlin Desktop sharing and cache

- `ShareLauncher.desktop.kt:17–47`: the scope-owned owner keeps latest callback
  and options, enforces single-flight admission and releases its token in
  `finally` before invoking the application. Cancellation is rethrown; an
  inactive scope suppresses a late result. The callback is outside the platform
  catch, avoiding the original callback-double-report pattern (032).
- Lines 53–55 and `ShareOutcome.kt:49–52` snapshot mutable file lists at the
  public launch boundary. File reference snapshotting does not keep the files
  alive or prevent the caller/OS from changing them.
- `ShareLauncher.desktop.kt:57–72,82–115`: support/load work uses IO, but the
  nonblocking begin call has no suspend handoff that can lose a returned native
  ID to cancellation. Polling uses suspending 25ms delays and a finite configured
  deadline; native cancellation runs in `finally`. There is no new five-minute
  blocking JNI call in the launcher (030).
- Lines 64–79: failed/denied/dismissed native sharing does not automatically copy
  or open content. Only Unavailable can use the allowed text/URL clipboard
  fallback. File payloads are Unavailable; there is no `Desktop.open` or
  `Desktop.browse` fallback (027).
- Lines 85–94 check actual file existence/readability and forward subjects.
  These checks are not a promise of recipient-lifetime readability. Common URL
  validation (`ShareOutcome.kt:54–65`) rejects blank values, not every unsafe or
  malformed scheme. NSURL/custom/file URL and service behavior needs explicit
  tests/policy; this review found no demonstrated exploit from that gap.
- `NativeShareBridge.kt:11–28` checks ABI1 before new async calls; a mismatched
  old library does not silently use assumed symbols. Public `ShareLauncher`
  constructor/launch, legacy factories/packages and original `ShareResult`
  cases remain in source. `ShareOutcome.toLegacyResult` is explicitly lossy;
  legacy Success remains unsuitable for deciding when to delete shared files.
- `NativeLibCache.kt:13–64` uses a full SHA256 content-addressed filename,
  validates exact bytes, rejects symlink components/entries, validates the cache
  directory, applies private POSIX permissions and installs atomically where
  supported. Its unique-file fallback verifies bytes rather than replacing a
  different loaded version. `NativeLibLoader.kt:14–59` closes its resource
  stream and retains trusted packager `System.loadLibrary` precedence (031).
  Hashing bundled bytes is neither a signer check nor protection from a
  same-user process attacker. Windows loaded-DLL, cross-process and permissions
  failure behavior remains unverified by this read-only inspection.

### Timeout and cancellation are deliberately two phases

The Kotlin result/scope can settle after cancellation has been **scheduled** but
before AppKit has run physical cleanup. Rust keeps the native admission slot Busy
until `finish_on_main` acknowledges it. This behavior is explicitly documented
in `NATIVE.md` and the Desktop owner comment; it is not an overlooked claim of
synchronous dismissal. Cancelling the picker cannot retract external effects
already handed to a selected sharing service. Completion/cancellation races,
no-window, window closing, timeout, callback reentrancy and cleanup latency need
an actual AppKit run loop, not just coroutine/registry substitutes.

## Positive Android camera checks outside the review findings

The new result/options factory is additive; the legacy factory remains a
success-only adapter. Main dispatch serializes Android operations. Pending URI
and owned path are stored together **before** external launch. Ordinary result
handling consumes pending state before the callback; Busy leaves it intact.
`rememberUpdatedState` updates callbacks/options without making callback identity
an owner key. File deletion is restricted to a canonical immediate child of the
camera cache directory with the expected `capture-*.jpg` name. A successfully
returned file is not immediately deleted. Provider failures have explicit
Configuration results and a configurable authority; the sample recommends
narrow camera/outgoing directories rather than its old whole-cache exposure.

These checks do not establish real provider grants, supported camera-app
availability, API23 versus API24+ behavior, process restart, hardware capture,
successful file readability through a recipient, or absence of unrelated mobile
native lifetime issues.

## Executed evidence independently inspected

The reviewer inspected actual command logs, exit status, scoped task lines and
camera testcase XML, and independently recomputed the cited log/report hashes.
These are **existing executions**, not new runs by the reviewer.

| Evidence under `docs/development/evidence/` | Actual scoped outcome | Limit |
|---|---|---|
| `native/share-rust-linux-tests.json/.log` | `PATH=/root/.cargo/bin:$PATH CARGO_BUILD_JOBS=2 cargo test --locked --manifest-path calf-share/native/Cargo.toml`: exit0, **6 passed, 0 failed/ignored**. All six recorded input hashes and log hash matched current bytes. | Pure registry tests. Their 10,000-cycle loop checks Rust Arc counts, not AppKit allocations; no cross-thread/JNI/UI stress. |
| `native/share-rust-linux-clippy.json/.log` | `cargo clippy --locked --manifest-path calf-share/native/Cargo.toml --all-targets -- -D warnings` with the recorded PATH/job bound: exit0; hashes matched. | Compiler/lint check, **not tests**. Linux cfg excludes macOS AppKit code. |
| `native/share-rust-apple-cross-check.json/.log` | `cargo check --locked --manifest-path calf-share/native/Cargo.toml --target aarch64-apple-darwin` with the recorded PATH/job bound: exit0; hashes matched. | Real objc2/AppKit target typecheck; cached completion in this recorded repeat after a package-cache lock wait. **Zero Apple links or runtime tests.** |
| `native/camera-share-ios-klib.json` and `gradle/first-ios-klib.*` | Camera/share production and inherited common-test `compile*KotlinIosSimulatorArm64` task lines executed successfully. Log and three linked receipt hashes matched. | Whole batch exit1 in other modules. **Zero native tests**, Apple links, UIKit/device executions or immutable-revision proof. Later common/test edits are not silently certified. |
| `gradle/first-native-and-third-android-host.*` | Whole command exit1. Receipt records 207 held input hashes unchanged at its post-run check. Camera desktop XML: **3 cases, 2 passed/1 failed**, 0 errors/skips. Share desktop and camera/share Android-host tests **did not execute** because test compilation failed. Camera/share desktop and Android production compiled at those held inputs. | Failed camera case was the old empty-saver fixture's force-unwrapped null; later test-harness fixes are not rerun results. Separate WebView cases are not share/camera coverage. The newly repaired camera source/tests were not these inputs. |

The first camera XML has exactly the following testcase outcomes:
`iosQualityBoundsRejectInvalidValues` passed;
`pendingUriAndOutputAreSavedAsOneRequest` passed;
`emptyStateDoesNotInventARestoredCapture` failed.
Its SHA256 is
`89f6591510f44aa64e8e0ab23a03bd48f47686f0bb3c7681e185b74780aa9f0f`.

### Prepared tests are not executed evidence

- `DesktopShareTest.kt`: eight tests use the real admission/callback/fallback
  boundary with an injected operation/clipboard. They do not drive an AppKit
  share service or native timeout cleanup.
- `NativeLibCacheTest.kt`: seven tests perform real filesystem work, including
  same-content concurrent writers and POSIX symlinks/permissions where available.
  They do not load a Windows DLL or simulate separate processes.
- `NativeShareBridgeTest.kt`: four real-JNI tests are prepared. Non-macOS tests
  cover loader/ABI/unavailable/borrowed-pointer behavior. Its opt-in macOS test
  requires a graphical session and performs **three present/cancel cycles**,
  not service success/failure, forced timeout, late callback or sanitizer stress.
  A skipped macOS test is not an AppKit pass.
- `ShareContractsTest.kt`: eight common gate/adapter/validation/snapshot tests.
- Camera common: three tests; Android request owner: six tests after R2's new
  regression; Android Activity lifecycle: four at the R1/R2 snapshot, **five**
  after the separately reviewed R3 repair.
  All new/repaired host tests require a new coordinated run. A host lifecycle
  fixture is stronger than a saver helper but still not OS process death or an
  external camera.

## Required acceptance gates before closure/release

1. Execute the three source repairs' camera host regressions, preserving failed
   diagnostic evidence; re-review any later source changes. Then test real don't-keep-activities/process restoration,
   foreground writer/grants and capture/cancel/error on supported Android levels.
2. Execute real packaged/generated JNI tests on each Desktop host. Match every
   packaged native binary to the tested source/lock/toolchain/ABI; cached local
   extraction tests cannot validate artifact provenance or missing target payloads.
3. On an actual macOS graphical session, exercise service completion/failure,
   selection followed by cancellation, timeout and late callbacks, concurrent
   launch attempts, source-window closure, callback reentrancy and disposal before
   and after Main dispatch. Check exactly-once outcomes and eventual zero owned
   registry/UI objects without assuming cancel retracts external effects.
4. Run thousands of real UI cycles with Instruments/leaks/ASan and Main Thread
   Checker as applicable. The six Rust tests provide no AppKit leak/UAF proof.
   Concurrent JNI begin/take/cancel and external timing stress are still missing.
5. Run independent consumers/compatibility fixtures against an immutable
   revision, including old launcher descriptors/sealed results and deliberate
   JNI behavior changes. Full source retention is not binary certification.
6. Retain the other native owner's iOS/browser/provider/device and release gates.
   Source review and partial cross-compilation do not authorize publication,
   issue closure, or lifting containment.

## Reviewed source identity appendix

SHA256 values below identify the production snapshots used for detailed source
reasoning. They are not a claim that the whole concurrently developed repository
was frozen or that later edits passed these checks.

| File | SHA256 |
|---|---|
| `calf-share/native/src/lib.rs` | `dfcfdc8da55e00339e70a73a57d3a12817f9213066ffe048bc03eb12b24f06b9` |
| `calf-share/native/src/macos.rs` | `fbaf932b1ff809b4bfc3270c0b726ba8f6d6e196a282c1bc77e781b89caa1b0b` |
| `calf-share/native/src/operation.rs` | `926b8c1fd41c2039e6bb8a81e9d05333165ed459aa10b9381ab28d140ed62942` |
| `calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt` | `7917f3fba55b30bed8468470736b7175b6645f503e86bd4ced551d20f1c5adee` |
| `calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeShareBridge.kt` | `6151e6cc7ff16bb68c0eedc13e1b930f081958b4cfe66d8997b9fe78d7a76626` |
| `calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibCache.kt` | `af7281463392c40a567b6d1d7b4dec686a28de0d59126e6a21c65d38e8f19937` |
| `calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibLoader.kt` | `d4c127e26533bd6b0a08d1afe456126e5594241c0cc56c64881232d49f660ae2` |
| `calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareOutcome.kt` | `9c79f573005a38a75709ca6ccca9fc81478c022f56f17abdeb852720c8bbdc27` |
| Android camera before R1/R2 repair | `2267c0a6ab8bf6692d37e05f3c9acaa3b386997a7dbc6250bf5f9e99faeb01ba` |
| Android camera R1/R2 repair; R3 inspected | `9b220f954818780c1c183914c553620d7ae477bc25bce1e0804a36924e88111c` |
| Android camera after R3 source repair | `806793b5c9e9ab5bcb064e257045788c986046907e4123a33310b6c7dc6ff917` |
| `calf-camera-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRequestTest.kt` after R2 regression | `e97bbfe0a5a77e220d8d5160a9f46fe47999280e8a90e63ad7e61efb760365df` |
| `calf-camera-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraLifecycleTest.kt` first four scenarios | `ef70c28b23b351002ac279361643e2c0d599c3220381776aa0977564ef169be8` |
| Same lifecycle file with the fifth context-handoff scenario | `ba2ce7bc94eca8b896f484210d35de4250cb64594f88a712e3b7b1307b349361` |

Rust manifest/lock/toolchain hashes and exact command timestamps remain in the
three independently checked Rust receipts. The original findings cite exact
baseline file/line locations; all later line numbers in this report are tied to
the explicitly named reviewed snapshots, not substituted into baseline history.

## Final scoped refreeze reconciliation — 2026-10-24T20:19:58Z

The native owner announced refreeze at 20:19:05Z and supplied
[`post-review-source-checkpoint.json`](../native/post-review-source-checkpoint.json).
The reviewer independently parsed that receipt (SHA256
`bfda4823676451fe4759a3c4471564d5982b510d9b2084a39818b33fa0dc6904`) and checked
**all 41 camera/share file entries' SHA256 and byte lengths** against the
working tree: **zero mismatches**. This is byte identity, not a new semantic
review of every platform file in that receipt. Its WebView entries are outside
this scoped reconciliation.

The final Android production `806793b5…` and lifecycle test `ba2ce7bc…` are
unchanged from the R3 repair review above. The final request-driver test is
`1ebe15bf3720cd81783c47a6221e19c500e9330b93a82f8b2b51280a79472c2b`;
independent byte comparison confirmed its only change from reviewed `e97bbfe0…`
is the named argument `retainPendingForRestoration` becoming
`retainPendingForSuccessor`. Common/options and Desktop/Rust identities are
recorded in the linked receipt and matched at this check.

An independent lexical recount also matched the receipt's **14 camera and 44
share `@Test` declarations**. This count includes share Android/browser files
outside the deeper implementation review above; it is not 58 test executions,
platform coverage or additional passing evidence. **All newly added/changed
Kotlin regression sources remain uncompiled/unexecuted at this checkpoint.**
The base is still `94d2492e99d5cbc060409d94d9f88febd06222d5` plus uncommitted
changes. The lead schedules compilation/execution; R1/R2/R3's original traces,
native/device/ABI gates and no-closure/no-publication conclusions are unchanged.
