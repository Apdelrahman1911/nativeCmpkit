# [Medium][NATIVE-029] macOS share leaks both the Objective-C delegate and its Arc completion state on every presented picker

<!-- nativecmpkit-item:audit:NATIVE-029 -->
## Classification
- **Finding:** NATIVE-029
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/native/src/lib.rs:148-162,255-259,294-295`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/native/src/lib.rs#L148-L162) — `did_choose, Arc::into_raw and mem::forget(delegate)`

## Root cause
A cloned Arc is converted into a raw pointer in the delegate ivar, but no dealloc or completion cleanup ever consumes that owning raw reference. did_choose reconstructs it and immediately forgets it. The Objective-C delegate itself is mem::forget-ed permanently with no owner to release it.

## Impact and preconditions
Each picker that reaches delegate creation leaks a native object and its Rust mutex/condition-variable allocation, including dismissal and timeout. The source leak is definite, while the per-request memory size is not measured.

## Supporting evidence
- Arc::into_raw(ctx.pair.clone()) increments ownership at256; no matching owning drop exists.
- std::mem::forget(delegate) at295 has no later Retained::from_raw/release counterpart.

## Recommended solution
Use an explicit retained operation owner and balanced lifetime/teardown. Release the raw Arc exactly once from delegate dealloc or a safely synchronized completion path, clear the pointer, and release delegate/picker after callbacks can no longer occur. Handle late callbacks after timeout without use-after-free.

## Risks and compatibility
Naively dropping the delegate immediately or Arc after the waiting thread wakes risks a weak-delegate loss or use-after-free. ObjC callback lifetime, picker retention and duplicate callbacks require a real macOS design/test, not a one-line mem::forget removal.

## Required tests / acceptance criteria
- Thousands of share/cancel cycles show stable allocations under Instruments/leaks.
- Success, cancellation, timeout, no-window and late/duplicate callbacks drop each owner exactly once.
- ASan/native stress with concurrent requests validates no UAF or double-free after cleanup.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/508
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
