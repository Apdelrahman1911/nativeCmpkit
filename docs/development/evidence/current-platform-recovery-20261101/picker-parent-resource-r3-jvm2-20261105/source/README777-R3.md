# Picker lease777 R3 — JNI refusal and release-ownership source correction

2026-11-05 · **#58 / IO-023 remains open** · isolated proposal, not adopted.

This is the related five-part correction requested in independent743's sealed
R2 review. No ROOT read/write, Git/GitHub/network mutation, hosted dispatch,
library/target/native compiler invocation or native retry belongs to R3. The
lead alone owns adoption, Git, hosted work, acceptance and closure. This packet
is not part of the immutable Camera/WebView hosted cohort.

**At this seal: all NEW/changed controls, rustfmt and the two authored actual-JVM
methods are UNEXECUTED.** Review the complete source/lineage packet before any
NEW control is run. Results must be written to a separately named directory;
never edit this seal or replay the accepted R2 source13 / RetainSlot8.

## Scope and mixed lineage

Incremental R3 has **three modified input files + one NEW file**:

| Path under `proposed/` | Exact input authority | R3 change |
| --- | --- | --- |
| `calf-file-picker/native/src/lib.rs` | sealed R2 postimage | fallible parsing/conversion and success-only outer-entry cleanup |
| `calf-file-picker/native/src/macos_parent.rs` | sealed R2 postimage | checked global pins, guarded JNI/UI, bounded actual release ownership |
| `calf-file-picker/native/src/jni_path_tests.rs` | lead's original dependency784 | six scalar-result call sites adapted; two NEW genuine-JVM guard/parser tests |
| `calf-file-picker/native/src/macos_release_slots.rs` | NEW, explicitly0644 | exact production generic ownership protocol; 16 NEW numeric tests |

The other **five R2 sources remain byte/mode-identical**: Cargo.toml, Cargo.lock,
the two desktop Kotlin sources and `parent_retain_slot.rs`. These are held
inputs, not newly accepted compiler/native paths. The complete original-to-R3
adoption proposal is **six existing modifications + three NEW files / nine
candidate source paths**. It is not seven existing files, nor eight NEW files.

* `before-r2/` holds R2's seven exact postimages.
* `ancestor-before777/` holds the original five R2 preimages, copied from R2.
* `before-lead784/` and `dependencies784/` hold the exact original JNI dependency
  and the lead's receipt. Lead HEAD/blob/stat claims are attributed to that
  receipt; they are **not our fresh ROOT custody**.
* `ancestors/` holds R2's source/manifest seals, independent rejection, original
  README/checklist and the original failed/successful execution records.
* `SOURCE-PACKET777-R3.json` holds both incremental and complete original
  reversible byte transitions, full pre/post identities and explicit NEW modes.
* `PASSIVE-CUSTODY777-R3.json` and `MANIFEST777-R3.json` hold ordinary confined
  packet file identities. They do not authorize ROOT adoption or execution.

The first passive seal attempt refused a wrong NSApplicationAWT.m path before
any seal/control execution. Its original FileNotFoundError remains in
`PASSIVE-SEAL-FIRST-FAILURE777-R3.json`; the actual sealed R2 path is
`.../native/libosxapp/NSApplicationAWT.m`. Existing exact copied records are
passively verified, not recopied; only the missing authority is acquired next.

## Implementation changes

### Checked JNI strong refs / preserved exception precedence

`macos_parent.rs:106–121` wraps jni0.21.1's unchecked NewGlobalRef. It refuses
preexisting pending state and null input, checks pending state immediately after
the allocation and refuses an Ok(null) result. All four acquisition graph/release
pins and main exception transport use it. No pin failure can arm/CFRetain or
continue ordinary JNI work. DeleteGlobalRef for any created ref is legal while
pending; this is not a claim that every graph destructor is memory-only.

`ParentError::throw` borrows the nonnull, still-held global as `&JThrowable` and
does not allocate a NewLocalRef. A pending primary is preserved. Failed Throw is
diagnosed, not claimed delivered, and outer Err cleanup is skipped even if Throw
failed to seed a Java throwable. The boolean means "pending throwable", not
proof that this particular error was delivered.

Main starts clean before validation/UI. `transport_main_exception` transports
only a newly raised operation throwable, never a prior main-thread one. A new
transport allocation/OOM failure is cleared on that main operation and becomes
typed worker unavailability. **Exact original throwable delivery cannot be
promised if its strong transport ref cannot be allocated.** Java(null) and
Throw(null) are never intentional outcomes.

### Real retain and pre-reserved recovery storage

`macos_parent.rs:123–145,269–449` separates precomputed `ReleasePolicy` from the
actual retained `ReleaseJob { pointer, policy }`. Finite static storage has
**64 entries**, reserved from the live JNI entry VM key before class work,
TLS arm or CFRetain. Policy allocation and checked graph pins precede the retain.
After execute/finish, the real pointer and already prepared policy are bound to
that reservation **before** propagating execution, borrow or generation errors.

`OwnedWindow` owns an `OwnedRecord`, not merely a ticket. Its field Drop only
parks the actual record into its reserved slot: no allocation, attach, JNI,
AppKit or scheduling. Other `ParentLease` graph GlobalRefs still use jni's own
DeleteGlobalRef metadata Drop; do not generalize the memory-only claim.

The NEW production `macos_release_slots.rs` uses linear private reservations,
memory-only transitions, wrong-VM refusal before moving any record, and unwind
guards. No destructor/formatting/JNI/AppKit call spans a slot mutex. Unknown
records are retained without dereference, eviction or retry. A successful
request drops only release metadata outside the mutex and returns the slot to
Vacant; it does **not** prove the native retain was finally released.

### Explicit, bounded, clean-entry/successful-exit drain

`lib.rs:186–213` admits recovery only at explicit outer create/show/destroy
boundaries, after the common wrapper's pending guard. A successful clean result
can drain after closure locals drop. **Err or panic skips exit drain**, including
logical Rust errors whose Java Throw failed. The retain callback uses the plain
panic wrapper only; it cannot drain while the JDK read lock is held.

`macos_parent.rs:167–249` obtains a VM from the current live JNI env, matches its
key before moving work, visits each physical slot at most once, and performs JNI
outside locks. A refusal before invocation leaves KnownUnscheduled; the attempt
is marked possibly invoked **before** entering the call wrapper. Wrapper/Java
failure or panic after that boundary is conservatively Unknown/no retry.

The checked JDK `nativeCFRelease(JZ)V` request still receives **true**. It is the
retained OpenJDK17 top-level-event policy; public main-queue CFRelease or generic
CFRunLoop/default-mode dispatch is not a qualified substitute. No speculative
native-call bypass, saved-VM liveness probe, raw-parent fallback or parent0
substitution is added.

### Fallible private boundaries, unchanged public JNI signatures

`lib.rs:32–140` returns Result from scalar/array parser and path converter,
keeps optional null semantics, releases scoped locals/UTF chars, and propagates
before further ordinary JNI. String validation explicitly checks IsInstanceOf
and pending state before get_string_unchecked; it avoids jni0.21.1 get_string's
hidden unchecked GetObjectClass allocation path. Array length is checked after
the unchecked JNI call, converted fallibly, and Rust capacity reserved fallibly.

All caller strings/filters/defaultName are parsed before legacy or owned parent
creation. Create/show/callback/worker-main paths refuse pending state before
resource acquisition, result allocation or UI dispatch. PushLocalFrame and
PopLocalFrame remain permitted with pending exceptions; the prohibited work is
ordinary object/class JNI and UI that would follow a failed operation.

The original nine JNI exports and R2's three additive entries keep their source
signatures and ABI1. Kotlin public APIs, namespaces, Apache attribution and crate
identity are unchanged in R3. Only private Rust helper return types change.
The six existing scalar-result JNI tests are adapted without weakening their
type/identity, valid peer bytes, filesystem EILSEQ or frame/GC assertions.

## What remains unverified / unresolved

See [failure matrix](FAILURE-MATRIX777-R3.md) and
[execution/acceptance plan](VERIFICATION-PLAN777-R3.md). Numeric protocol models
are not AppKit/JNI/native counts. The two actual-JVM methods are not executed by
Python or the standalone state-module driver. There is no new JNI/ABI, Apple,
native/consumer, security, issue-closure or publication acceptance.

Shutdown/no-future-entry drain, private JDK/vendor equivalence, true top-level
completion, parent disposal/focus/modal races, close-driven panel cancellation,
native framework/type/Send bounds and fail-each-pin/OOM/transport identity remain
required. Quarantine can permanently consume capacity; no background actor or
automatic eviction pretends otherwise. Windows/Linux raw-parent assumptions
remain unverified under IO-023. **#58 stays open; no release/package/deployment.**
