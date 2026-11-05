# Related failure-path correction matrix — lease777 R3

2026-11-05 · proposal-source locations under `proposed/`, not current ROOT.
The five original discrepancies are confirmed from R2 and locked API source;
none is a reproduced macOS/OOM/native failure. Every R3 runtime claim is still
unverified. No control has run at this seal.

## R3-A · High · NewGlobalRef null/pending failure

**R2 affected code:** `macos_parent.rs:244–247,433–443`.
**Root cause:** jni0.21.1 `jnienv.rs:600–607` uses `jni_unchecked!` and returns
Ok(GlobalRef), even when NewGlobalRef yields null or leaves OOM pending. `?`
alone is not successful allocation. Continued pins/JNI and Java(null) transport
were possible source paths; runtime occurrence is not established.

**R3 candidate:** `macos_parent.rs:106–121,374–391,594–640`.
Checked helper runs a no-clear precondition, rejects null input, allocates once,
immediately checks pending state and validates nonnull. Four acquisition pins
and exception transport use it. Acquisition preserves a Java primary, returns
before the next pin and before arm/retain. A null/no-exception result is typed
unavailability. Transport begins only after clearing this clean-start operation's
own primary, and clears only a newly raised transport allocation error on main.

| Allocation observation | Candidate disposition | Required verification |
| --- | --- | --- |
| preexisting pending | refuse before allocation; preserve primary | real JVM pending identity (NEW method planned), macOS main/worker entry cases |
| null argument | typed refusal before allocation | null argument/transport native boundary |
| nonnull result, clean | held checked GlobalRef | actual fail-each-pin positive control |
| null + pending OOM | Err JavaException, no later pin/arm/retain | actual JNI fault injection; zero forbidden calls/retains |
| nonnull + pending | Err JavaException; created ref deleted legally | actual injection/reference cleanup |
| null, no pending | typed unavailability; no Java(null) | controlled JNI seam plus genuine JNI boundary checks |
| transport allocation fails | new main allocation throwable cleared; typed worker failure | actual transport OOM; main restored clean; no false exact-identity claim |

**Impact:** prevents source-demonstrated invalid-ref and subsequent-JNI paths.
**Risk:** helper adds ExceptionCheck operations; String parsing adds bounded
class/type checks. Transport identity under OOM is unavailable rather than
silently substituted. Rust global-wrapper/allocation abort behavior is not cured
by Result or catch_unwind. Required JNI/macOS tests cannot be replaced by Python.

## R3-B · High · known-unscheduled retained owner was discarded

**R2 affected code:** `macos_parent.rs:88–96,136–147`.
**Root cause:** owner was taken before attach; attach/state refusal returned
without release or recoverable ownership. A possible-invocation release cannot
be safely retried, but a known-uninvoked retain cannot be silently discarded.

**R3 candidate:** `macos_parent.rs:123–145,167–249,269–449` and NEW
`macos_release_slots.rs:6–261`. No attach occurs in owner Drop or drain. Finite
storage and checked policy are prepared before retain. The actual record is
linearly tied to storage and parked on Drop; no new recovery allocation follows
CFRetain. All error propagation after execute/finish follows the binding.

| State / transition | Ownership and permitted operations |
| --- | --- |
| Vacant → Reserved | one exclusive empty storage entry, no native resource; full refuses before retain |
| Reserved → Owned | the inseparable OwnedRecord holds actual pointer/policy; no drain accessor |
| Owned/Reserved+record → KnownUnscheduled | memory-only park; actual T survives owner Drop/unwind |
| Known, different VM/pending env | no move/no JNI attempt; key comparison while locked |
| Known, matching clean entry → InFlight | move one actual record and unlock before JNI/destructors |
| InFlight, provably before invocation refusal/unwind | guard restores exactly that Known record |
| InFlight → MayHaveInvoked | set before potentially invoking wrapper; conservative boundary |
| MayHaveInvoked, error/panic | Unknown owns metadata; no retry/dereference/eviction |
| MayHaveInvoked, checked request return clean | Requested, metadata Drop outside mutex, slot Vacant |

Requested is a **request-transfer observation**, not actual CFRelease/native
completion. Even a wrapper failure that might have occurred before the JVM call
is conservatively Unknown after the marked boundary; this trades bounded retained
metadata/capacity for avoiding possible double release. Unknown entries in static
storage have no normal-lifecycle destructor or eviction path.

**Risks / remaining causes:** at most64 owned/reserved/recovery records can
coexist. Unknown can consume capacity permanently, and no-future-entry known
records have no proven shutdown drain. JVM pointer equality is a live-entry key,
not a measured shutdown/recreation lifecycle epoch. No saved-VM probe or retry
after destruction is proposed. Exact framework/type/Send compilation is missing.
Registry close removes config ownership, but does not cancel an active rfd panel.
These limitations keep #58 open.

**Required tests:** exact NEW production numeric protocol16 is planned, including
8 concurrent reservations,4 concurrent drain passes, cap64, wrong VM, pre/post-call
unwind, owner unwind, destructor reentry and request-metadata destructor unwind.
It demonstrates Rust state ownership only. Native criteria additionally require
real CFRetain balances, known refusal then live-entry drain once, Unknown no
double release, JDK top-level-loop completion, last-retain disposal/modal behavior,
shutdown/no-next-entry and appropriate process/global-ref lifecycle checks.

## R3-C · Medium · avoid unchecked NewLocalRef before Throw

**R2 affected code:** `macos_parent.rs:53–61`.
**Root cause:** jni0.21.1 NewLocalRef likewise returns Ok(null) unchecked. That
unnecessary allocation could lead to Throw(null), potentially while OOM pending.

**R3 candidate:** `macos_parent.rs:62–102`. Nonnull checked global is borrowed
as `&JThrowable`. Locked `jthrowable.rs` reference conversion and Throw permit
it without local allocation. Pending state wins; failed Throw is diagnosed and
not reported as this error delivered. The still-held GlobalRef spans the call.

**Impact/risk:** reduces reference-allocation failure surfaces without public
descriptor changes. A failed Throw still cannot guarantee primary Java delivery;
outer Err/panic must not admit cleanup just because no throwable is pending.
Required real JNI tests: same type/cause/object on clean worker, preexisting
worker primary, null refusal, failed Throw identity/diagnostics, no NewLocalRef.
The authored NEW shared-JVM method checks only common pending guard identity;
it is not the macOS ParentError/transport test.

## R3-D · High · swallowed parser/pending state led to later JNI/UI work

**R2 affected code:** `lib.rs:29–50,354–433,452–500,551–620`,
`macos_parent.rs:165–199,363–400` and the retain callback entry.
**Root cause:** `.ok()`/unwrap converted JNI failure to absent/empty options.
Checked macros check after invocation, not before; this allowed subsequent
class/object calls or UI dispatch after failure. DefaultName could be parsed
after acquiring a parent. JNI local-frame push/pop themselves are permitted
while pending, unlike the subsequent ordinary object/class operations.

**R3 candidate:** `lib.rs:32–140,150–213,381–438,460–752`;
`macos_parent.rs:269–393,451–570,680–703`.

1. Scalar/array parsing returns Result, retains optional null/empty/Unicode
   semantics and uses AutoLocal/JavaStr teardown. String type checks have an
   immediate pending guard; get_string_unchecked receives only a checked String.
2. GetArrayLength's unchecked result has immediate pending/negative conversion
   guards and try_reserve. All elements propagate before the next element.
3. All caller strings/filters/defaultName are parsed before any parent creation.
   Path converters return Result and refuse result allocations on pending state.
4. Common panic wrapper's guard executes inside catch. Worker/env and matching VM
   checks precede main dispatch. Primitive GetLongField, class and identity
   unchecked results have immediate pending/null guards; object/method JNI macros
   retain their checked-postcall error propagation.
5. Callback has a narrow clean guard and only the original TLS authorization /
   CFRetain path. No release mutex/drain/UI dispatch is introduced under execute.

**Impact:** source-demonstrated error swallowing and follow-on work are removed
in these paths. Invalid parameter shape is a Rust JNI InvalidArguments failure
rather than ignored absence. Private scalar helper signature change adapts six
original test callers; public12 JNI source signatures remain unchanged.

**Risks/tests:** actual JNI failure/pin/method/UTF and main dispatch faults remain
unexecuted. Existing paths-length/index narrowing in result-array construction,
Windows/Linux handle assumptions and extreme Rust allocator-abort behavior are
not repaired by this scoped batch. Planned actual-JVM2 exercises pending primary
identity/zero parser-result/entry-body work and valid null/Unicode semantics;
it does not prove native parent's pipeline or fail-each-argument allocation.

## R3-E · Medium · cleanup throwable could mask logical Rust primary

**R2 affected code:** `macos_parent.rs:124–131,283–300`, `lib.rs:482–487`.
**Root cause:** a Rust Unavailable/Borrow/Panic could exist before outer Throw.
Dropping the native owner scheduled release during that interval; cleanup JNI
failure could become pending first and cause primary Throw to refuse replacement.

**R3 candidate:** memory-only owner park plus `lib.rs:150–213`. No scheduling
or attaching occurs in owner Drop. Only explicit outer clean-entry or successful
clean-exit boundaries may drain. Err/panic skips exit cleanup even if its Throw
failed; the common callback panic wrapper never drains. New cleanup failures
from a proven clean operation are diagnosed/cleared separately; a preexisting
Java primary is never suspended to run cleanup.

**Impact/risk:** ordering is source-established, not a native reproduction.
Cleanup records may await a later entry, so native completion remains missing.
Panic catches do not catch process abort. Main operation transport has separate
OOM limitations; no exact-primary identity claim under transport allocation
failure is made. Required native tests combine a logical generation/creation/
panic primary with release request failure, verify primary object/type/cause,
record state and pending restoration, and test original Java primary separately.

## Shared compatibility and policy gates

* Native ABI1 and original9+additive3 JNI source declarations retained; native
  resolution/symbol/consumer acceptance remains missing. All12 signatures are
  only a planned source control at this seal, not binary ABI analysis.
* Kotlin public signatures/namespaces, crate identity, Apache attribution,
  dependency package versions/checksums and R2's JDK17 restriction remain intact.
* `nativeCFRelease(JZ)V,true` top-level policy is retained. Public main-queue
  CFRelease/default-mode dispatch, raw-parent fallback, parent0 substitution,
  INTERNAL suppression/reflection and private native-call bypass are prohibited.
* Source13/RetainSlot8 R2 results remain historical and are not replayed. The
  original LLD failure/failed-object cleanup and changed-command recovery remain
  separate. All R3 controls and real JVM2 are UNEXECUTED at seal.
* No native/security/API–ABI/consumer/legal/release-readiness issue is closed.
  Parent/lead alone decides adoption and verification; **#58 stays open**.
