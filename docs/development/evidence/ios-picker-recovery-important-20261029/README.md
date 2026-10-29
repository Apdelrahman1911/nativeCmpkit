# Related iOS ownership recovery — 2026-10-29

**Apple runtime pending; no new issue closed by this compile/tooling checkpoint.**
The prior failed26-method run40826758875/0aa8fc10 remains immutable in the
[original batch evidence](../ios-picker-batch-important-20261029/README.md).

## Shared owning patch

- Production `IosDialogPresentation.kt` uses exact native identity to inspect both
  the controller backlink/flags and its owning presenter/containment ancestors'
  forward links. The same projection guards admission exceptions and dismissal.
  Absence of a backlink alone cannot certify native-consumer release. Real Apple
  observations are required before attributing the previous failures to this cause.
- The picker-only test host witnesses native `viewDidAppear` before initial idle and
  native root reappearance/disappearance during owning cleanup, retaining actual
  attachment, generation, Recomposer, BasicText, strict plist and Worker checks.
  The public Compose1.12.0 delegate API is explicitly deprecated/test-only; no
  copied dependency source, private API, timers-as-readiness or weakened renderer.
- Native transport preserves bounded known lifecycle failure stages/error types and
  finite test-correlated admission booleans. It still rejects those failures before
  forwarding; diagnostics are not completed testcase/Worker or security proof.
- `ios-picker-recovery`: all four changed host methods and all three owning runtime
  methods;19 completed filter/copy/staging methods and successful other-host suites
  are not replayed. Original26-method plan and every full native gate remain.

## Important local checks

[`local/review.json`](local/review.json), actual command/result receipts and853
before/after inputs retain source-held dirty execution at49ee0641, not a new
immutable native candidate.852 ordinary build inputs plus the explicit workflow
hash were held throughout.693 tooling methods pass0/25.01s; eleven focused guards
pass separately and **overlap**, not704 unique methods. Production/test iOS KLIB
compile passes0/38.01s under JDK17/Rust1.98 with an8GiB disk reserve. **Zero Apple
links or native runtime methods.** Existing impossible-cast warning is preserved.
Only finite JSON is archived; private logs/binaries/app payloads are not committed.

## Remaining batch gates

Actual export cancellation/native safe points; retained public PHPicker delegate/
per-launch configuration/current callback; complete BasicText root teardown and
caught assertion cleanup; exact XML/protocol/Worker/runtime/binary/owned cleanup.
Provider cancellation/relaunch, genuine swipe/successful save/destination grants,
actual parent acquisition/thread/backend leases, full limits/fallback/cap matrix,
physical/minimum-device, full consumer/ABI/dependency/provenance/notices/security
and release gates remain separate. No packages/releases/deployment/Pages; main
and imported attribution/history are preserved. Close only fully checked related
members immediately after original-criteria review, then document/read back.
