# iOS Camera ownership: unwired controlled-native acceptance batch

**Source-only additions. No Camera Apple compiler, link or native execution is claimed.**
The lead must review/enroll the genuine application host and acquire a compiler/native slot.
The proposed focus is `ios-camera-ownership-memory-callback`, only `calf-camera-picker`,
with proposed task `:calf-camera-picker:iosSimulatorArm64ApplicationTest`. It is not yet wired.

## Finite application scope

The five new methods are in `IosCameraOwnershipAcceptanceTest`. They use a new
Camera-owned UIApplication/Compose host, not a Skiko-only scene or a file-picker dependency:
public remembered-owner recomposition/actual Kotlin-Native GC/latest callback; Busy/controlled
duplicate terminal input/reentrant replacement; disposal in separately observed real UIKit
presenting and presented phases; actual simulator source absence/library fallback/foreign modal
refusal; controlled tiny real UIImage through real delegate/PNG-JPEG write/public file readback.

The delegate is weakly referenced, never test-retained strongly across the GC variant.
No test sets production transition state, injects UIKit completion, replaces the encoder or
fabricates an encoded Captured result. Disposal is admitted only if the requested native flags
are actually witnessed at composition forgetting. Final teardown checks both native ownership
directions, presenting/dismissing flags and current root reappearance; idle uses an earlier
root appearance plus SideEffect generation/recomposer work so a covering modal cannot deadlock it.
Independent cleanup preserves the original refusal and does not grant custody of foreign roots.

## Host enrollment still required

- Entrypoint: `com.mohamedrejeb.calf.camerapicker.internal.nativeCameraApplicationMain`.
- Exported delegate: `NativecmpkitCameraLibraryTestDelegate`.
- Both nonempty `NSCameraUsageDescription` and `NSPhotoLibraryUsageDescription` are required.
- Require actual native camera source unavailable and actual photo-library source available;
  do not infer either from a simulator name. The controlled fallback needs a legitimate host
  photo-library authorization/privacy setup; it does not verify denied/restricted outcomes.
- GeneratedSuites must be nonempty, UIApplication active, owned UIWindow visible/key/attached.
- Tests run on one owned Worker while UIApplicationMain remains live. Actual Worker termination,
  native XML and held before/after inputs remain required; an entrypoint return is a failure.
- Shared controller/workflow/receipt enrollment remains lead-owned, as does compilation/dispatch.

## Narrow first-terminal/native-completion source controls

`scripts/ci/test_camera_ios_terminal_barrier_source.py` contains five genuinely NEW source
controls. They read comment/string-free owning Kotlin code and explicit callback boundaries.
They do not execute Kotlin, UIKit, the worker, file IO or a permission interaction.
The first run must retain the original production bytes and owning red/refusal before repair.
Only failed/changed controls may recover; unchanged accepted Android/Common/browser/native
results remain their original executions. Source controls cannot measure native dismiss-call
counts; the controlled native test observes owner/outcome/teardown, not an instrumented call count.

## Original requirements retained verbatim

### NATIVE-020

- Change callback from A to B while capture is active and assert agreed callback semantics.
- Repeated ordinary recompositions do not replace iOS active operation owner.
- Force Kotlin/Native GC/memory pressure during presentation and verify delegate callbacks still arrive.

### NATIVE-021

- Every platform produces one defined terminal outcome for cancel/unavailable/error.
- No camera app, feature absent, permission denied and iOS simulator library fallback.
- Desktop/Web capability checks align with launcher behavior.

### NATIVE-023

- Double tap launch, callback launches again, callback throws, owner navigates away.
- Denied permissions, camera unavailable, simulator fallback and presentation over another modal.
- Exactly one active picker and no old delegate cleanup clears a replacement operation.

### NATIVE-024

- Real-device 12/48MP capture latency, peak resident memory and UI responsiveness.
- Disk-full/write-failure/cancel/repeated capture and cache eviction.
- File remains readable for expected consumer lifetime; cleanup never deletes another request file.

## Still-open gates / no issue closure

All four issues (#76, #77, #79, #80) remain open even if the five controlled methods later pass.
Physical capture/orientation/metadata; genuine denied/restricted authorization; desktop/Web
capability launchers; native throwing-callback boundaries; 12/48MP latency/RSS/responsiveness;
real disk-full/cache eviction; and cancellation before/after observed actual native writer
entry and return remain separate requirements. A sleep, isActive or a controlled invalid
owned path is not a mid-write, disk-full or physical-camera result.
No new autorelease-pool/memory-performance claim follows from background dispatch.
Successful Camera output stays caller-owned; no implicit TTL or picker-only release contract
change is allowed. Default PNG/JPEG 0.9/photo fallback and all public signatures stay unchanged.

No shared CI/AGENTS/dependency/API/source-set/publication/main/history/GitHub edits are part
of this isolated Camera patch. All established acceptance/release/security gates remain.
