# Share630 — one missing-only AppKit batch and timeout JNI method

This is a source-qualified **recovery/diagnostic route**, not a native pass,
production deadline fix or release gate. Issues **#84, #85 and #150 remain open**.
The lead owns shared workflow integration, immutable dispatch, original review
and any evidence-based closure; this patch changes no workflow or production code.

## Original result; reuse, do not replay

Run [41774113636](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41774113636),
attempt 1, actually used `6fb368eb77a0863cd3d725f75e85d59b41caee71` and failed:

- AppKit: three reached XML cases, two passed (`cancel_before_dispatch`,
  `no_key_window`), `missing_content_view` failed, five cases unexecuted.
  The generic failure XML does not identify the failed phase/assertion. The
  owning private stderr body is unavailable; its size/checksum cannot establish
  window activation, nil-view behavior, a result enum or the native cause.
- JNI: two methods passed (independent-owner overlap rejection and retained-request
  cancellation/same-worker heartbeat). The timeout method failed at its **first
  retention wait**, before deadline-result assertions or the replacement launch.
  The exact original assertion was `Actual AppKit operation was not retained`.
  Individual active/live counts and emitted outcome were not recorded. This is
  **not a confirmed production deadline defect**.
- Source-bound final live/registry/cleanup assertions are not separate exported
  raw readings. Sanitized console markers are receipt derivatives, not an
  independently exported private stdout stream. Neither native/library step nor
  the whole failed run is reclassified as green.

The once-acquired original review remains sealed in the local original cache:
`REVIEW-original630.json`, SHA-256
`d27931e577a5e830733d2180c87eb248552dff28e34dafd76651c39bedc8e756`.
Its 132 passive custody checks, four actual 1,373-input maps and 56 archive-member
hash checks are reused, not repeated downloads, extractions or native executions.

## Exact next population

The owning AppKit route compiles **one** fresh, admitted executable, then runs
these exact six missing cases serially in fresh owned processes:

1. `missing_content_view`
2. `real_picker_cancel`
3. `controlled_picker_dismissal`
4. `controlled_success_duplicate_late`
5. `controlled_service_failure`
6. `bounded_concurrent_requests`

```sh
python3 scripts/ci/macos_share_appkit_lifecycle.py --plan --missing-only-share630
# Only after lead integration, immutable source freeze and available capacity:
python3 scripts/ci/macos_share_appkit_lifecycle.py --missing-only-share630 \
  --output build/ci-verification/share630-missing-appkit
```

The plan is side-effect-free. The executor refuses non-macOS/ARM64 hosts, absent
exact GUI opt-in, existing output, source/runtime/artifact drift or insufficient
8-GiB reserve. Original Rust toolchain 1.98.0, 1,200-second compilation envelope,
240-second per-child envelope and native ten-second waits remain unchanged.
Every child retains full source/native/Git/runtime/executable/report custody,
exact one-case XML/console agreement, independent owned cleanup and transitive
preservation of preexisting reports. **Stop on the first refusal/failure**; no
later child runs against a failed/unknown population. Reached red XML stays red.
Unreported cases are not accepted passes. Review per-child execution state and
XML together; absence of a qualifying XML is not proof that no native action ran.

Legacy default-eight behavior remains available for its original callers, but
must not be selected to repeat the two accepted original cases. A single exact
`--case=<one of these six>` is supported for a later owning failure-only recovery;
accepted cases, stress, arbitrary skip lists and unknown selectors are refused.
After accepting any new subset, never repeat it via an unchanged six-case request.

The shared JNI route is prepared but **not registered by this scoped patch**:

- profile: `macos-share-missing-lifecycle`
- focus: `macos-share-timeout-retention-recovery`
- task: `:calf-share:desktopTest`
- filter: `com.mohamedrejeb.calf.share.MacOsShareCoroutineLifecycleTest.realNativeTimeoutReportsOnceWithoutFallbackAndAllowsFreshRequestAfterMainCleanup`
- required population: exactly this one genuinely passed method, fresh XML and
  one actual task execution on opted-in macOS ARM64; no skip/N/A substitute.

The lead must register the finite source/identity/host/outcome helpers in the
shared matrix/library plan/receipt paths and keep the JNI step independent of an
AppKit failure while retaining the overall failed-job result. No accepted JNI
method, old bridge method, broad library suite or sample execution is requested.

## Failure-only evidence, not a workaround

The missing-view reader runs only for this execution's reached failed case. It
reads at most 4,096 bytes from the owning sealed ordinary stderr file, with
checksum, size, descriptor/path identity and link-count custody. One exact panic
source/frame plus a fixed unchanged assertion can identify an assertion phase;
unknown, ambiguous, overflowing, absent or source-drifted observations remain
**unavailable**. A printed numeric thread token is not exported/interpreted as a
PID. A fixed terminal-result enum additionally requires the unchanged operation
source and exact original `left: 2`/known `right` pair. No panic/error/private-path
body, raw control/weak-owner readings or exact native cause is exported. Synthetic
reader fixtures must never be matched to the unavailable original stderr to guess
its contents.

The timeout helper preserves the original **2,000-ms operation deadline**, both
retention assertions, cancellation and owned cleanup. It captures active/live
values from the **same original predicate evaluation**: active is queried first,
live only when active is one. The failure handler performs **zero new native
queries**, emits only fixed phase/count/outcome enums from bounded immutable
already-emitted callback snapshots, then rethrows the **same** assertion. Unqueried
live stays `unavailable`, not zero; absent outcome stays `not-emitted`. Multiple or
overflowing callbacks remain explicit. No callback/error message body is printed.

## Qualified locally; missing externally

At the owning e593d556 branch base, NEW18 Python source/mock/file controls passed
once (0.137 s); affected12 default-runner/report/declaration controls passed once
(0.113 s). Both held the same 1,387 actual source inputs. A sparse-source freeze
refusal occurred before any test; exact tracked secure-alert provenance/build/JS
lock inputs were materialized without changing guards. This is **zero** Kotlin
compilation, AppKit/JNI/SDK execution or library-method verification.

Next: lead union Kotlin compiler qualification, shared source/matrix/workflow
qualification, immutable dispatch and independent original-native acceptance.
Workflow artifact allowlists must include per-child `cases/*/*.json` and
`cases/*/fresh-reports/*.xml`, **never private logs or executable/package output**.
Visible presentation, service/recipient delivery, stress/ASan/Instruments/leaks,
other platforms, packaged consumer, API/ABI, dependency/legal/security and all
release-readiness criteria remain separate unverified requirements. No issue
closure, artifact publishing, release, deployment or Pages action is authorized
by this source-only result.
