# Public Compose browser WebView — direct acceptance, 2026-10-28

[Run40613563594](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40613563594)
at immutable `b7ba5c802ee8c8a58e813d19b5a242770aac9675` passes **JS33/33 + Wasm33/33**:
66 fresh executions of33 authored methods,14 XML, zero failures/errors/skips.
Three new public-component methods run on both targets; all30 previous identities
remain. [Important review](important-result-review.json) accepts **all three
original NATIVE-006 criteria** before [#65 closure/readback](direct-closure/closure-readback.json),
before this archive. **28 issues closed total**.

Actual public WebView in real ComposeViewport/canvas/HTML interop verifies full
window disposal and removal/remount in the same live composition, exactly-once
callback and clearing of retained iframe/owner, real DOM removal and distinct
replacement identity. Native removal of original listener objects is observed;
queued original captured callback objects actually run after replacement without
altering its owner/node/loading/title/final URL/errors. Not a copied renderer or
fake UI applier. The test accesses dependency-internal LocalComposeWindow only to
close its own real viewport; ComposeViewport's Unit return is not called a handle.
Controlled trusted HTML enables real DOM readiness, not a production trust change.

All742 exact own-Git inputs, before/after maps, every XML/artifact hash, command,
33 testcase identities per target and Chrome155/SDK/runtime correspondence are
reviewed. First reviewer incorrectly required a class in zero-test helper files;
its original source/failure is retained, and annotation/identity/count checks
remain. Two initial GitHub lists omitted the already exact-readback-closed issue;
later read-only reconciliation confirms28 closures, with zero repeated mutations.
Original issue body/title/labels and historical failures preserved.

One accepted dispatch; only two selected browser/module jobs. Reports/receipts,
not private job logs. Later share changes are **not** this run's inputs. Historical
one-shot scripts must not be bypassed to claim otherwise. No Firefox/Safari/GC
profiling, other WebView/network/sandbox/cookie, physical/minimum/native sanitizer,
ABI/dependency/legal/full-consumer/security/release clearance. No publication.
