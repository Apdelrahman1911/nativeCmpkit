# macOS Share native ownership and coroutine verification

Related findings: [#84/NATIVE-029](https://github.com/Apdelrahman1911/nativeCmpkit/issues/84),
[#85/NATIVE-030](https://github.com/Apdelrahman1911/nativeCmpkit/issues/85), and the macOS
subject-property subset of [#150/NATIVE-034](https://github.com/Apdelrahman1911/nativeCmpkit/issues/150).
The [original requirements](../audit/findings/NATIVE.json) remain authoritative.
See [batch604 evidence](../development/evidence/current-platform-recovery-20261101/macos-share-lifecycle604/README.md).

## Boundary: what is actually exercised

The ordinary public Kotlin/JNI signatures and default shipped native implementation
are unchanged. The opt-in Cargo integration executable includes the actual
`native/src/lib.rs`, registry and AppKit dispatch implementation. Its helper is
under `native/tests/appkit_lifecycle/cases.rs`, not a root auto-discovered Cargo
integration target. The six-line inclusion in `macos.rs` requires both `cfg(test)`
and `appkit-lifecycle-tests`; neither the harness nor controlled callback inputs
are included in a normal cdylib/release build.

Native objects are created, observed and destroyed on **actual process Main**.
Only numeric IDs, owned Rust content and atomic counters cross thread boundaries.
The harness retains actual NSWindow, picker, delegate and optional native service
objects, observing delegate deallocation using Objective-C zeroing weak references
and Rust completion deallocation using `Weak<Completion>`. The late-callback test
intentionally retains its old receiver until the controlled messages are finished;
this is not a dangling-pointer callback experiment.

A retained operation count is **not proof that the picker is visibly open**.
Controlled Objective-C `didShareItems`, failure and nil-service messages exercise
real native callback/cleanup interoperability, **not actual recipient delivery**.
Reading `NSSharingService.subject` does not prove Mail uses/delivers the subject.
The original visible-picker, memory instrumentation and service integration gates
are not replaced by these tests or by a compiler/source-control pass.

## Finite native batch (eight new cases)

| Exact case | Actual operation/assertions | Remaining distinction |
|---|---|---|
| `cancel_before_dispatch` | Actual ID is cancelled before Main service; registry reference disappears while new admission stays Busy until queued Main acknowledgement. | Does not present a picker. |
| `no_key_window` | A real NSApplication without a key window returns Unavailable and retains no owner. | Required precondition must really hold. |
| `missing_content_view` | Real key NSWindow is temporarily given a nil content view; Unavailable and cleanup are asserted before restoring it. | The OS may refuse that precondition; refusal is failure, not a skip. |
| `real_picker_cancel` | Four actual retained picker creations/cancellations, native single-flight rejection, duplicate cancellation and weak release. | Retention alone is not visible-presentation evidence. |
| `controlled_picker_dismissal` | Real delegate receives controlled nil-selection message; exactly one Dismissed and balanced owners. | Not user dismissal. |
| `controlled_success_duplicate_late` | Real delegate receives controlled success followed by failure; first result wins; safely retained old callback receiver cannot remove/reopen a newer owner. | Not real service completion. |
| `controlled_service_failure` | Real Mail-service object receives delegate/subject assignment; controlled failure is terminal; service delegate clears and weak owners die. | Never opens/performs Mail; installed service absence remains red. |
| `bounded_concurrent_requests` | Eight real Rust request contenders yield exactly one positive ID and seven Busy; real Main picker cleanup releases that owner. | Bounded trial, not prolonged sanitizer/pool stress. |

Every native case also independently checks queued cleanup, zero live picker
owners, zero retained registry entries and dead weak lifetime witnesses. Native
assertions dispatched through production's panic-catching dispatcher set a separate
failure witness: a caught assertion cannot accidentally become a green terminal
result. Only reached cases produce XML. The first failed/unknown ownership state
stops the remaining cases instead of replaying them against contaminated state.

### macOS prerequisites and first execution

Use an immutable reviewed development checkout, an actual graphical macOS session,
a supported AppKit picker with `close`, explicit opt-in, a held Rust/Cargo toolchain,
JDK17 for Kotlin, and original before/after source/artifact/environment custody.
Reserve one hosted-heavy slot initially; native GUI processes in the batch run
serially. Do not run on Linux and relabel that outcome as AppKit evidence.

```sh
NATIVECMPKIT_NATIVE_UI_TESTS=true CARGO_BUILD_JOBS=2 \
  cargo test --locked --features appkit-lifecycle-tests \
  --test appkit_lifecycle --manifest-path calf-share/native/Cargo.toml
```

Wrap the actual process with the lead's bounded process controller/outer timeout.
Internal run-loop waits are cooperative: nested native menu handling, stalled Main
or a stuck native call still requires the outer deadline. Do not waive a timeout,
opt-out, missing graphical session, unsupported service or failed cleanup.

For recovery, select **only** the exact failed/unreached case after reviewing the
original failure and changing/qualifying its cause:

```sh
NATIVECMPKIT_NATIVE_UI_TESTS=true CARGO_BUILD_JOBS=2 \
  cargo test --locked --features appkit-lifecycle-tests \
  --test appkit_lifecycle --manifest-path calf-share/native/Cargo.toml \
  -- --case=controlled_picker_dismissal
```

Fresh reports are written to
`build/ci-verification/share-appkit-native/process-<pid>/TEST-<case>.xml`.
The per-process directory must be exclusively created; existing output is refused.
Archive raw process exit/log and XML ONCE, hash actual executable/source inputs,
and require exactly the requested class
`com.mohamedrejeb.calf.share.native.AppKitLifecycle` / case identities and actual
cleanup witnesses. XML is not a substitute for executable/runtime custody. Report
absence on an earlier preflight failure is missing evidence, not successful tests.

## Actual default Kotlin owner / JNI / AppKit batch (three new methods)

Class: `com.mohamedrejeb.calf.share.MacOsShareCoroutineLifecycleTest`.
No native-operation stub, virtual scheduler, sample application, clipboard write
or external recipient is used. Each fixture owns an actual JFrame, single-thread
coroutine executor, scope and default `DesktopShareOwner` operation.

1. `cancellingRetainedAppKitRequestFreesOwnersAndDoesNotOccupySingleCoroutineWorker`:
   actual native retention, same-worker heartbeat, prompt scope cancellation/join,
   Main cleanup, zero late outcomes and fresh native admission.
2. `realNativeTimeoutReportsOnceWithoutFallbackAndAllowsFreshRequestAfterMainCleanup`:
   actual two-second native polling deadline yields one distinct TimedOut result,
   no fallback, balanced Main owners, fresh retained request and no cancellation
   callback from the replacement.
3. `independentRealNativeOwnersRejectOverlapWithoutReplacingTheRetainedRequest`:
   two independent owners produce one Busy without completing/cancelling the
   original; only the admitted owner releases the actual native ID/picker.

```sh
NATIVECMPKIT_NATIVE_UI_TESTS=true ./gradlew --no-daemon --max-workers=2 \
  --no-parallel --no-configuration-cache \
  --init-script scripts/ci/daemon-jvm.init.gradle.kts \
  :calf-share:desktopTest \
  --tests 'com.mohamedrejeb.calf.share.MacOsShareCoroutineLifecycleTest.*'
```

This **runtime** command must use the real generated/bundled JNI native library;
never carry the local compile-only `buildNativeLib`/`prepareNativeResources`
exclusions into runtime verification. Use fresh Gradle XML, no restored task
outputs/reports and the lead-owned finite receipt/selector. The shared selector
and workflow are deliberately not edited by resource-lifecycle604.

For finite selection, call
`native_test_policy.macos_lifecycle_cases(cases, host, native_ui_opt_in)` directly.
Require exactly all three XML method identities once; missing/duplicate/unknown
names, macOS headless/opt-out and failed cases remain red. Only those exact
macOS-only methods skipped on an opposite host may receive N/A; they never count
as native passes. Full-suite `apply` classifies the new class when present while
leaving the original four-method focused registry unchanged. This avoids turning
an absent new finite population into success through an unrelated old registry.

## Stress, memory instrumentation and unchanged issue closure gates

The separate `--case=stress_2048` selector runs 2,048 real retained picker cancellation
cycles and drops test-owned weak-witness/ID bookkeeping after each cycle. It is
not included in the finite batch and is **not yet executed** at source preparation.
It requires an outer deadline chosen from actual reviewed host observations.

For Instruments/leaks/sanitizer verification, first list/record available Xcode
instrument templates/tool versions, build and hash the actual feature-gated test
executable without executing old suites, then instrument that exact executable
and exact selected workloads. Preserve baseline/terminal allocations and original
trace/leaks output; report any framework allocation exclusions explicitly instead
of silently filtering them. Use a held sanitizer-capable Rust toolchain/build;
a cross-check without a sanitizer is not ASan evidence. Never publish those
private instrumentation builds as library packages.

| Finding | Original criterion still required for closure |
|---|---|
| #84 | Thousands of actual share/cancel cycles with stable allocations under Instruments/leaks; all success/cancel/timeout/no-window/duplicate/late paths release owners exactly once; actual ASan/native concurrent stress shows no UAF/double-free. |
| #85 | Actual cancellation while **visibly open**, prompt Main cleanup and bounded-worker responsiveness; repeated/unavailable-view/deadline/late paths; bounded native pool stress and exactly-once terminal/lifetime checks. |
| #150 | Actual iOS Mail subject integrations and documented web/macOS native/fallback behavior; controlled native subject property alone is insufficient. |

The current ID/deadline implementation removed the original Condvar wait, so
spurious-Condvar-wake tests do not validate the current architecture. Retain that
historical criterion and document the owning absolute-deadline/late-callback
replacement evidence; do not claim a spurious wake was reproduced on current code.
No issue is closed by preparing this batch. The lead reviews originals, integrates,
dispatches and closes only the fully verified original subset; no publication,
release/deployment/Pages or independent legal/security/consumer/API–ABI gate is waived.
