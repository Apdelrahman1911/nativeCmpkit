# Direct public Unsupported-permission acceptance

**PERM-017 / [#114](https://github.com/Apdelrahman1911/nativeCmpkit/issues/114)
closed2026-10-28 at09:09:40UTC**, directly after important tests and source/results
review, before this documentation. [Acceptance](acceptance-review.json),
[closure readback](issue-114-after.json), [resolution](issue-114-resolution-comment.md).
Original issue body/title/labels and upstream Calf#31 remain unchanged.

| Actual target | Fresh accepted executions | Immutable run |
|---|---|---|
| Linux desktop |6/6|e6a8ada7 / [40658374590](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40658374590)|
| macOS Arm64 desktop |6/6, actual Seatbelt child|same original run|
| JS Chrome |6/6|same original run|
| Wasm Chrome |6/6|same original run|
| Windows x64 desktop |6/6|53e56c7e / [40660400990](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40660400990)|

**30 target-method pairs, six authored scenarios, five fresh XML**, zero failures/
errors/skips. Each target's776 captured inputs match its own Git blobs and remain
unchanged; actual JDK17 daemons/launcher correspondence were inspected. Tests mount
real public factories/platform actuals with real Compose Runtime and explicitly
false inspection mode. NoNodes omits unrelated rendering, not permission code.

Criterion1 verifies the recommended **explicit Unsupported policy**. macOS
executes real factories inside Seatbelt with an actual OS-denied canonical-path
write and successful outside-sandbox before/after witnesses. Network/TCC lookup
denials are policy entries, not separately attempted operations. Browser wrappers
guard/restore real global services under missing/false secure-context and denied
fixtures, requiring zero reads/prompts. This is not actual OS permission denial,
insecure-origin navigation, TCC/App-Sandbox entitlement grants, feature parity or
new browser/desktop permission backends. PERM-016's mobile requirements stay open.

Criterion2 covers named/core/custom singles, normalized duplicate/child/empty
batches, callback/selection recomposition, throwing/reentrant callbacks, synthetic
legacy Granted flags and nonnavigating settings. Results are false once
synchronously per explicit request, with Unsupported details before callbacks.
Existing public signatures remain; `docs/permissions.md` documents the contract.

The **whole original workflow stays FAILED**: Windows checkout hit a preserved
historical filename-length limit before Gradle, zero tests/no artifact. Job-local
Git longpaths is now set before checkout, not machine-wide. Windows-only recovery
succeeds; four accepted targets were reused. Their owning permission/tests/daemon/
fresh-test inputs are unchanged. [Archive map](archive.json) preserves original
artifact paths using shorter evidence filenames; ZIP hashes are retained, not
candidate packages or full checkout/environment transcripts.

Original Wasm annotation compile failure remains; corrected compilation exit0/
27.01s ran zero tests. Initial local desktop6/6 is a dirty diagnostic, not part of
the30 accepted executions. Tooling initially failed on stale synthetic fixtures;
repaired463/463 includes eight focus methods. Windows guards54/54 overlap tooling,
not additional library tests. **43 actual closed issues overall.** Native/device/
minimum-platform, legal/dependency/security/consumer/ABI/release gates remain;
no packages, releases, snapshots, deployments or Pages were published.
