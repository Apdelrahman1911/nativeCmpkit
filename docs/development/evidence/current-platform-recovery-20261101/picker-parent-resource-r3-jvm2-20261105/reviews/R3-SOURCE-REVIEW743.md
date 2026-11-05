# Independent R3 picker parent/release ownership source review743

## Verdict and scope

**Complete source composition qualified for lead-authorized NEW source15, followed by NEW std-only protocol16, once each.** There is no required source correction for this limited control scope. This is **not** ROOT adoption, whole-patch ingress, a macOS/JNI/JVM build, a binary ABI result, native release completion, a consumer result, or an issue/release acceptance. **#58 (IO-023) stays open.**

The review independently examined the sealed R3 implementation, retained R2 rejection and lead784 authority, complete original-to-R3 and incremental R2-to-R3 byte transformations, exact locked JNI dependency sources, the proposed control bodies and their immutable recipes. Complementary742 independently examined the JNI/parsing/primary-exception and authored real-JVM2 portions; its source-only verdict has no blocking correction for this scope. Neither reviewer ran the proposed controls, imported their testcases, invoked a library/JVM/native compiler, queried native state, used ROOT/Git/network/GitHub, or performed adoption/publication. This report records the already-completed passive source review; it does not replay its scripts.

## Exact evidence and custody

Packet: `/root/nativecmpkit-source-proposals-20261105/picker-native-parent-lease777-r3-jni-release-ownership`.

| Sealed authority | Bytes | SHA256 |
| --- | ---: | --- |
| `MANIFEST777-R3.json` | 17043 | `5f13c155d83a615ca3478961a19879e7b4cc011beb18c13a45944976a62690f9` |
| `SOURCE-PACKET777-R3.json` | 338366 | `141e16317171471ff95c0ddfa26764afeff395e9d8f9c0b6c1ee58598cd6fff6` |
| `PASSIVE-CUSTODY777-R3.json` | 40790 | `fa0f9be21a0ad9deb02f9d5baeacdfa065a15236a325a1d793addc61bb1dd807` |
| `PASSIVE-AUTHORITY-ACQUISITION777-R3.json` | 28173 | `7f8dde7eff5bc0e982d46f1d87b7655d044a5c4f00612de5703c0c505a2fcd8f` |
| independent `PASSIVE-SOURCE-REVIEW743.json` | 129982 | `c226ea7d01ae37c910f7fe9a91f50638f8fbf7600a74dc9237ff7a13ce06d7f3` |

The manifest lists **76 ordinary files / 1,181,639 bytes excluding itself**; there are 77 actual ordinary packet files, not a claimed 76-file whole packet. The independent receipt measures **94 finite inputs**:77 packet files, three immutable plan appendix files, 13 exact existing JNI cache sources, and one locked archive. All before/after FDstat9 identities, modes, byte lengths and SHA256 values hold. All 75 entries in the original retained custody record match exactly. These are separate finite source/dependency/packet populations, **not** a current ROOT, compiler, runtime, native or consumer map.

Incremental transition: **three existing changes + one NEW / 95 reversible fragments**, with five unchanged R2 sources held. Complete original proposal: **six existing changes + three NEW / nine source paths / 67 reversible fragments**. Both full-byte forward/inverse transformations reconstruct exactly; no broad repin or historical overwrite is authorized. Original source modes remain source-relative (existing0600 in retained trees, NEW0644), not proof of the current ROOT modes or NEW-path absence. R2 and lead784 identities are attributed to their captured authority, not recast as fresh ROOT custody.

The retained original R2 review is the unique manifest member `ancestors/R2-REVIEW743.md`, SHA256`92d7ca88812decc0e84828b0e774db423170e014f8d84e552295de3d4a25f0c3`. R2 source packet hash is `f981833a19d2d495d06ff9dbd17ee1c020a1b7be1d2bb283e96ac46c6ecfee62`; lead784 receipt hash is `12116e2e6b3a52cf9a44f2d03ac59b79e13b9c57dcceda74e5b85fcbe5df30f0`. Their original rejection/partial limits remain preserved.

### Candidate implementation identities

| Relative source | Bytes | SHA256 |
| --- | ---: | --- |
| `calf-file-picker/native/src/lib.rs` |31583|`9002e8d901e138d537ac2520d3c49925b298eaa58f4223d890d36c43059469b0`|
| `calf-file-picker/native/src/macos_parent.rs` |27637|`b60cbed17e8a38229391aa9a371657b41b53935dbb8246287eff771ca4af38ae`|
| `calf-file-picker/native/src/jni_path_tests.rs` |22164|`7671d22565ad37783a3734142b99016de57d59599d0121ca94d20a5eaaed8bd7`|
| `calf-file-picker/native/src/macos_release_slots.rs` |22193|`70ed4377ce37dc3f6fd7e35a970c2cdb0de3ff10a1ce2c34a83fabd068103ac5`|
| `calf-file-picker/native/src/parent_retain_slot.rs` |8110|`87f1fe1011c2115e07491ed430c628b9a01e8c664ec161cbf3b7c3fd49eec109`|

Held R2 Cargo manifests/lock and Kotlin bridge/launcher sources form the other four paths. The private native implementation adds **no changed JNI export source descriptor**:original nine plus R2 additive three remain the exact12. This is a source signature observation, **not** successful symbol resolution, binary ABI validation, Kotlin compilation, actual invocation or public compatibility verification.

## Implementation-level release and exception analysis

Line numbers below refer to the **sealed R3 proposed** files, not a current ROOT capture.

### `native/src/macos_parent.rs`

- **62–102, `ParentError::throw`:** the held global throwable is borrowed directly as `&JThrowable`. The exact JNI blanket descriptor path accepts this borrow without a `NewLocalRef` allocation. A pending primary is preserved; inability to deliver `Throw` is not falsely reported as delivery. This fixes the reviewed R2 secondary-local-allocation path at source level; actual OOM/transport fault delivery remains missing.
- **106–121, checked global pin helper:** clean environment and non-null input precede `NewGlobalRef`; both immediate pending-exception and null-result checks follow it. The object graph and prepared policy obtain all four pins before any retain. Null or pending failures do not continue to later graph/method/retain work. No `.ok()` converts this failure to absent data.
- **123–145, owner/policy representation:** an actual native pointer and its prepared VM/class/method policy travel together. A reservation ticket alone is not called an owner. The policy Arc/global references are prepared before retain, avoiding fallible policy construction after ownership acquisition.
- **269–449, acquisition:** one of the finite64 release-storage slots is reserved before callback arming or `CFRetain`. Immediately after `RetainSlot.finish`, any actual retained pointer is bound to that reservation with its real release policy, **before** execution, borrow or validation errors can propagate. Consequently the reviewed post-retain failure paths have an actual owner record to park; a logging-only loss is not substituted. The existing one-shot retained-child mechanism remains separate.
- **167–244, entry drain:** only a clean, live JNI environment matching the stored VM key can move eligible records. One pass examines each physical slot at most once. The potential-invocation flag is set **before** entering the JNI call wrapper; later failure or unwind cannot prove no call occurred and becomes Unknown. KnownUnscheduled records alone remain eligible for later retry. `nativeCFRelease(JZ)V` retains `true`; no new generic main-queue `CFRelease` fallback is introduced.
- **531–570, worker/main dispatch:** clean matching worker state is checked before dispatch. A preexisting main-thread pending exception refuses work and is not transported as a newly created operation exception. Newly created operation exceptions are transported on their distinct path. Fault injection/real thread behavior is unexecuted.
- **680–697, retain callback:** the callback is only the pending guard and TLS one-shot `CFRetain` handoff. It does not acquire the release-recovery mutex, drain pending records, or dispatch release work while the JDK read lock protects the retain.

### `native/src/macos_release_slots.rs`

This NEW production kernel is std-only:261 production lines plus the numeric protocol tests. It does not pretend to be a JNI/AppKit emulator.

The private linear path is **Vacant → Reserved → Owned**. Owner Drop parks the *actual owner record* into already-reserved storage using memory/state work; neither failed attach nor unwind discards that record. A KnownUnscheduled record moves to an InFlight guard outside the storage lock. Refusal/unwind provably before invocation reinstates the same KnownUnscheduled owner. Once invocation might have begun, error/unwind produces **Unknown quarantine**, with neither retry nor eviction. Request-transferred records become terminal; request metadata destructors run outside locks, and even destructor unwind does not restore a record after transfer. The slot can become Vacant after this transfer cleanup.

No JNI/AppKit operation, owner-record destructor or formatting is placed under the slot mutex. Concurrency and boundedness are represented in NEW tests, not yet executed by this reviewer. Importantly, “memory-only Drop” applies to this owner record:it does **not** claim that every surrounding `ParentLease`/GlobalRef destructor is memory-only or JVM-lifecycle-safe.

### `native/src/lib.rs`

- **32–93:** scalar and array parsing become guarded, fallible operations. A valid optional null is still optional null. A JNI/reference/type error is not silently converted to null/empty/default. String class membership is explicitly checked before guarded `get_string_unchecked`, avoiding the reviewed hidden unchecked `GetObjectClass` path. Scoped locals and JavaStr UTF ownership are retained on error/success paths.
- **96–138:** result conversion returns JNI/path failures instead of continuing follow-up work after them. These private Result signatures do not alter the12 JNI source descriptors.
- **All picker bodies:** all arguments are parsed before legacy or owned parent acquisition. The error path therefore does not acquire a native retain merely to discover a malformed title/directory/filter argument afterward.
- **150–213:** the common panic/pending guard preserves primary precedence. Only explicit outer picker entry and a **successful clean exit** drain release records. Logical Err/panic skips exit drain even if attempting to throw its error failed; the plain retain-callback wrapper cannot drain under the JDK lock.

### JNI dependency and authored JVM tests

The **13 exact JNI cache files / 174,897 bytes** are independently identical to sealed copies and corresponding members in the existing locked `.crate` archive. The archive checksum `1a87aa2bb7d2af34197c04845522473242e1aa17c12f4935d5856491a7fb8c97` matches the retained Cargo.lock identity. Unchecked `IsInstanceOf`, `GetArrayLength`, `GetObjectClass` and `NewGlobalRef` semantics were reviewed, not guessed from another crate version. UTF allocation, new string/array, element and local-frame paths have the checked boundaries described above. Neither dependency compile nor vulnerability/legal acceptance follows from this byte identity.

The two NEW genuine JNI/JVM tests in `jni_path_tests.rs` are authored but **unexecuted**:

1. `actual_jni_pending_primary_stops_parsers_results_and_picker_entry_body`.
2. `actual_jni_optional_nulls_and_unicode_parser_arguments_keep_their_meaning`.

Complementary742's static review confirms the clean owned frame/pop, throwable identity comparison after the deliberate test clear, and preservation of all six earlier scalar assertions. These bodies do not supply a successful JVM run, OOM/transport/native/macOS execution, or parser-completeness certificate.

## Retained JDK policy: what `true` does and does not prove

The sealed retained sources are `CFRetainedResource.java`, `CFRetainedResource.m`, and `NSApplicationAWT.m` from the exact captured OpenJDK17u source authority. Calling the retained `nativeCFRelease(JZ)V` with `true` requests the JDK-owned release policy; the new Rust path does not implement its own generic release dispatch.

However, `CFRetainedResource.m:42–54` contains an internal embedding fallback when NSApp has no `postRunnableEvent:` implementation. Thus a request using this policy is **not a universal proof** that every embedding releases only after the top-level AppKit loop. “Requested/transfer completed” is distinct from **actual native release completion**. The exact JDK branch must be exercised with an ordinary supported consumer and relevant embedding behavior; no native event/run-loop/count trace has been acquired here.

## Remaining required gates and risks

| Priority / limitation | Root cause or evidence | Consequence / required verification |
| --- | --- | --- |
| **High — actual Apple/JNI type and ABI build unverified** | Source/stdlib controls cannot compile framework bindings, Send assumptions, architecture ABI or exports. | Build the exact macOS library/JVM2 on supported architectures; exercise actual symbol loading, fail-each-pin/transport/OOM and primary preservation. Keep #58 open. |
| **High — request transfer is not native completion** | Deferred JDK policy and internal unsupported-embedding fallback above. | Native retain/release counts, modal/show/disposal/focus/last-retain traces and actual top-level-loop completion remain missing; no release claim. |
| **High — shutdown/no-future-entry** | Recovery drain depends on future live clean picker entries; surrounding global refs require a usable JVM. | Define and verify the supported shutdown boundary, retained records and global refs; no claim of unconditional cleanup or leak freedom. |
| **High — Unknown capacity quarantine** | Potentially invoked release cannot be safely retried or evicted. | Permanent capacity consumption is fail-closed, not solved native ownership. Fault tests must prove no double release, loss or retry; quantify finite capacity exhaustion. |
| **Medium — VM pointer is not lifecycle epoch** | Stored matching key is a VM address. | Destroy/recreate/address-reuse behavior unverified; do not call it an authenticated native lifecycle epoch. |
| **Medium — panel cancellation outside patch** | Registry/Arc close preserves an active show lease. | Close-driven panel cancellation is not implemented; verify/document active modal behavior separately. |
| **Medium — inherited lossy malformed scalar decode** | `lib.rs:62`→JNI `JavaStr:192–194`→`ffi_str:53–61` can fall back to `String::from_utf8_lossy` after CESU8 decoder failure. | Separate malformed/unpaired-surrogate semantics follow-up; do not claim comprehensive Unicode round-trip or block this limited R3 source-control scope on an unverified new regression. |
| **Medium — extreme array/allocator behavior** | Array length/index narrowing and allocator abort are not exhaustively addressed. | Boundary/error tests remain separate; neither NEW31 controls nor real-JVM2 static review proves extreme-resource handling. |
| **Inherited platform/consumer/security gates** | Windows/Linux parent assumptions and ordinary consumers are outside this source packet. | Preserve platform/API–ABI/dependency/legal/security and release-readiness gates; no issue closure/package/release/deployment. |

## Authorized NEW verification plan (not executed by743)

Immutable appendix: `/root/nativecmpkit-source-proposals-20261105/picker-native-parent-lease777-r3-lead-plan-readback`.

| Recipe | Bytes | SHA256 |
| --- | ---: | --- |
| source15 recipe |2728|`c9a34f781dd58a6d7379a4fb8061e3a5813ba63ff6a11f8b0be6788179b6e0e2`|
| std-only protocol16 recipe |4448|`f6bc4fe5e9a8aaf20bd266223370093371786bc7dc5aba5f449df509d824c4b1`|
| plan seal |694|`17e0efbbcceb48871220c917460c905b59b33852844044634829ee41648fea22`|

The exact15 source selectors and exact16 protocol selectors are recorded in the independent JSON receipt. Source15 uses Python`-B`,256MiB AS/CPU15/outer30. The single production std-only module may then be compiled only by the exact existing Rust1.98 path, opt0/debug0/LLD`--threads=1`,1GiB AS/CPU30/outer90. Protocol16 uses1GiB AS/CPU30/outer30, serial harness with intentional workers8/4. Author must tell the lead before rustc to avoid local compiler overlap. This plan authorizes neither Cargo nor library/JNI/JVM/native target compilation. Accepted R2 source13/protocol8 are **not** to be replayed.

A future results receipt must be independently accepted against its original outputs, exact test list, recorded exits/budgets, finite input custody and owned cleanup. Even successful NEW15+NEW16 would not satisfy the missing native gates above. This report remains source-only regardless of later author results.

## Original passive-reader refusals preserved

The first independent passive script refused its strict-positive byte bound on valid **zero-byte original stdout/stderr**. Its exact assertion/stderr are preserved in `ORIGINAL-PASSIVE-REFUSAL743.json`. The R2 metadata adapter permits only the manifest-declared zero-byte originals, then refused a guessed prior-review filename; that exact KeyError is retained in `SECOND-PASSIVE-REFUSAL743.json`. The R3 adapter resolves the unique prior-review member using its exact manifest SHA and produces the successful passive receipt.

The original scripts, refusals and successful adapter are all retained. No target/source/manifest/original was changed to obtain acceptance. These are reviewer metadata-reader refusals, **not target testcase failures, native causes or run evidence**. Do not rerun these exclusive-write receipt scripts merely to produce another green report.

## Lead handoff

Source31 planned controls are qualified **only** for their limited parent-authorized scope. Parent alone owns integration, current ROOT identity/mode/absence custody, joint ingress, Git/CI/native/consumer verification and any later issue disposition. Preserve both full lineages, all originals, the JDK embedding/shutdown/capacity/VM-epoch limits and #58 open. No NativeCmpKit release/package/deployment/publication is supported by this source review.
