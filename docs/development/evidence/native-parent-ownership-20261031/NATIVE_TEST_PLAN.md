# Finite actual IO-023 / #58 acceptance plan — not implemented or dispatched

**Zero native-parent methods have executed.** These names describe new bounded
fixtures required after a source-reviewed peer acquisition bridge exists.
No raw stale-pointer experiment against the current implementation is proposed.

The original issue requires macOS main-thread checking, parent close/recreate,
Windows owned-dialog focus and destruction, Linux X11 and Wayland portal
parenting, and supported no-parent fallback. Safe model checks, compilation,
parent-0 config tests, and the current accepted Compose/config/cancellation suites
cannot replace those criteria. Existing accepted results are reused only after
an exact owning-source applicability review; they are not replayed here.

## Required before the first native request

- Freeze the implemented bridge, generation/disposal hook, native-dialog adapter,
  actual test fixture, complete relevant project input manifest, and payload
  hashes at an immutable SHA. Read back all new and retained JNI descriptors,
  additive capability behavior and old-payload rejection. This private source
  review is not that payload verification.
- Pin and record the actual per-target JDK/Skiko/rfd runtime and native build
  inputs. Match acquisition and destruction contracts to that runtime's peer
  implementation; a JDK major selection is insufficient implementation proof.
- Add bounded test-only instrumentation to the real acquisition/owner and dialog
  operations: actual native thread ID, peer identity/generation, guarded borrow
  entry/exit, owner acquire/release, panel/dialog identity, in-flight leases and
  final release/drain. Never log a raw pointer as if that proves ownership.
- The guard may remain held only through identity check and native owner capture
  on the actual native owner thread. Assert no AWT or registry lock is held at
  native-main/rfd dispatch, modal show, JNI result conversion or release wait.
- Deterministic barriers use owned live resources and normal dispose/detach APIs.
  Never feed random/stale pointers into baseline native code or force allocator
  reuse. The repaired candidate must reject before borrowing an invalid source.
- The lead owns dispatch/integration. Keep local heavy builds serial, at least
  8 GiB reserve, and at most two combined heavy verification requests. Capture
  fresh XML, exact selectors/markers, actual runtime results and owned cleanup;
  a compilation/synthetic failure does not count as a native execution.

## macOS arm64 and x64: five methods on each actual target

1. `genuineParentsTransferOwnersWithinPeerBorrowOnNativeMain`
   Use visible real ComposeWindow parents and the public file, folder and save
   facade paths, including the current coroutine IO callers. Confirm the real
   peer borrow spans both NSWindow and NSView ownership acquisition, all AppKit
   operations run on actual native main, and modal parenting/focus are correct.
   Include one genuinely absent-parent positive control. Run Main Thread Checker;
   record any checker finding as failure, not an off-main rejection pass.
2. `directDisposeAtTransferAndShowBarriersRejectsOldGeneration`
   Directly call `ComposeWindow.dispose()` before acquisition, during guarded
   acquisition, after ownership/before show, and while the panel is visible.
   Use bounded barriers that release the event loop. Before-show cases must
   reject the old logical generation; visible cases must follow the defined
   close/finish policy and refuse result delivery. Confirm session owners remain
   valid until final use even if the peer drops its own references.
3. `contentViewDetachReplacementAndPeerRecreationRejectOldBinding`
   After real owned acquisition, detach/replace the owned NSView on native main,
   and dispose/recreate a Java peer normally. Confirm the old binding cannot
   attach to the replacement view/window, including when native numbers happen
   to match. Assert actual logical peer identity and generation; never accept a
   matching number as identity or force address reuse. Check main-thread release
   of old retained objects after the final lease.
4. `ownedDialogCancelAbortAndParentCloseHaveDistinctOutcomes`
   Cancel a real owned panel, invoke a documented abort/failure operation on that
   same panel, and close the real parent during a visible modal. Verify typed
   cancellation, failure and invalidated delivery, then a successful new launch.
   If a failure is injected at an adapter boundary, label that observation as
   injected and retain a separate actual native failure requirement. Do not
   claim coroutine cancellation dismissed a native panel.
5. `repeatedModalSessionsReleaseAndDrainOnApplicationMainLoop`
   Run ten bounded owned modal cycles, including reentrant callbacks and
   cancellation. End the owned test application with a queued acquisition and
   final owner release pending. Assert admission closes, work finishes or safely
   refuses, owners release exactly once on the allowed application loop after
   the last show/conversion lease, and the loop drains before shutdown. Verify
   focus restoration and no AWT/registry/native-main wait deadlock. Retain/leak
   counters are ownership evidence, not independent heap/security certification.

## Windows x64: four methods on the actual native target

1. `nativeOwnerThreadOwnsFileFolderSaveAndRestoresFocus`
   Record `GetWindowThreadProcessId` for the genuine parent and the actual
   acquisition/show/destruction thread, plus COM apartment/message-loop state.
   Exercise owned file/folder/save dialogs and a no-parent control through the
   public facade. Establish native owner-thread dispatch by the supported peer
   adapter, not by equating AWT EDT with the HWND thread or spawning another STA.
   Verify owned modality, stacking and focus before/during/after show.
2. `parentDestructionAndRecreateInvalidateNativeOwnerBinding`
   Directly dispose/recreate the real parent before acquisition, before show and
   during visible modal use. Verify the adapter's destruction hook invalidates
   generation before the HWND is destroyed; close/finish the owned dialog safely
   and reject delivery to a replacement peer. IsWindow alone is not admission.
   Test numeric reuse only if it occurs naturally; never dereference a stale
   HWND or force a current baseline failure for coverage.
3. `nativeCancelAndNativeFailureRemainDistinctAndAllowNextLaunch`
   Cancel a real owned dialog and obtain a documented failing native HRESULT
   through the owned dialog adapter. Preserve the code/category and distinguish
   it from ERROR_CANCELLED. Confirm a new launch works after each outcome. rfd's
   current `.ok()` result is insufficient to pass this criterion; injected faults
   remain explicitly injected and do not certify an unrelated native cause.
4. `repeatedOwnedDialogsDrainDuringShutdown`
   Perform ten bounded cycles, including active cancellation/parent closure and
   pending work at owned application shutdown. Assert owner-thread destruction,
   dialog release, outstanding lease drain, rejection of old generations, focus
   restoration and no COM/message-loop/registry-lock deadlock.

## Linux x64: three methods for X11 and separately for XWayland

The controller must establish the actual AWT X11/XWayland backend and owned real
portal/compositor/session. An environment variable or Cargo feature is not that
proof. Record the actual portal parent identifier and modal option with the
owned genuine AWT parent; avoid an injected portal receipt being counted as a
real compositor/portal result.

1. `actualPortalUsesVerifiedXidWithModalParent`
   Launch file/folder/save dialogs from the real parent and verify its exact
   observed XID reaches the portal identifier and produces correct parent/modal
   behavior on the actual compositor. Hold the logical generation through the
   session; release AWT_LOCK before portal dispatch or waiting for a response.
2. `destroyedParentAndNewPeerRejectOldGeneration`
   Dispose/recreate the real parent in acquisition/pre-show/visible gaps and
   reject old-generation show/delivery. Validate the supported native destruction
   coordination. An XID is an external identifier, not a Rust retained pointer;
   do not turn the test into invalid-pointer injection or a number-only query.
3. `strictParentRejectsUnparentedPortalFallbackAndNoParentStillWorks`
   Make the owned test portal unavailable through a bounded controlled session
   configuration, verify the explicit strict requested-parent error policy and
   ensure zenity cannot silently report unparented success. Exercise an actual
   no-parent launch under its documented supported fallback policy. Restore and
   remove owned session resources and launch a fresh real parent afterward.

## Native Wayland: still an unmet original criterion

The selected Skiko/JAWT Long-only source supplies no wl_surface/wl_display/export
lease. XWayland method results do not satisfy native Wayland parenting. Keep the
original Wayland criterion open until a supported surface/display/export lifetime
bridge is reviewed, implemented and exercised on a real Wayland compositor and
portal, with corresponding destruction/reuse and strict fallback methods. The
current unsupported boundary is explicit; no criterion is silently waived.

## Independent final readback

Review each original issue bullet against the immutable selected source, exact
native payloads, actual peer/backend/thread identities, fresh XML results and
owned cleanup. Close only a fully verified subset if original criteria support
one; this review supplies no such subset. Packaging, public/API ABI, heap,
consumer, minimum OS, dependency/legal/security/publishing/readiness gates remain
independent and unchanged. No new native/parent/security test count is claimed.
