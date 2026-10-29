# Cancelled initial slider run; no accepted native results

[40863015797](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40863015797)
at `e8a72cedcef3297fbbd00b71d0714a1920a4df57` is **CANCELLED**, not a test pass/failure.
A source review found the final discrete RTL drag can already reach `range.start`,
so the unchanged same-value tap correctly emits no value-change callback. The
fixture demanded a new value-change callback. No native assertion failure is claimed.

Cancellation was requested once while the suite step was pending; final readback
shows setup started before cancellation took effect. An initial reviewer assertion
expecting `skipped` failed; the pending-to-start race is preserved. The digest-checked
seven-member artifact has **zero XML and no native-application receipt**; this is
zero accepted methods, not proof zero partial host execution. All865 **before**
inputs match historical Git; no after snapshot or whole-run/hold claim.

The fixture now resets hoisted value to the current midpoint **after** exact
old-writer, cancellation/no-stop and dragged-observer assertions, then verifies the
reset itself emits neither callback nor completion. Original fresh-tap callback,
completion and endpoint assertions are retained. No production repair/refactor or
public API change. See [held local check](../local002/review.json): only the changed
owning guard reruns1/1, changed test KLIB0/44.01s/all865 held inputs; **zero local
native tests**. One finite immutable six-method replacement is pending. Neither
issue closes from compile or cancellation; accepted old hosts/controls are not replayed.

No packages, releases, deployments, Pages or release/native-minimum/ABI/consumer/
security gate changes. JSON only; no raw private logs, ZIP or binaries committed.
