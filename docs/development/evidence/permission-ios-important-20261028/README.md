# Important actual iOS public permission-factory checks — 2026-10-28

Seven focused tests added for the actual public factories, Compose Runtime, Foundation NSLock/LifecycleRegistry and real Darwin Main/background queues. No Dispatchers.setMain, substitute permission state or backend. Registered application helpers deliberately control completions; no native OS privacy UI, UIKit presentation, physical-device authority, heap/ABI or release claim.

A real Main-queue barrier follows each background callback so duplicate/late-delivery assertions cannot race an undelivered event. Test factories are released after each composition rather than retained globally. Missing-helper and throwing-helper outcomes must remain distinguishable. Both actual iOS wrappers, child/batch/empty/not-required paths and observer/owner replacement are selected; native registry contention uses16 actual Default workers ×200 registration/lookup iterations plus name collision/reentrant factories.

**Not yet executed or accepted.** The initial local offline KLIB command failed before compilation on uncached Kotlin2.4.20 native compiler metadata: exit1/28.01s, zero compiled new tests and zero runtime methods. The old2.4.10 compiler is not a substitute. Important source-bound hosted execution must be reviewed before any closure.

Existing Android47/47 and five nonmobile targets'30/30 results may be reused only after their target inputs/results are reviewed as unchanged. Original issues #104/#106 stay open until their actual acceptance criteria pass. No packages, releases or deployments authorized by a test-only diagnostic.

## Additive hosted failures and recovery — 10:48UTC

[Test-only40671696029](test-only-40671696029/failure-review.json) failed fixture
compilation on two missing Foundation extension imports: **zero runtime tests**,
exit1/716.02s, all778 own-Git inputs held. This immutable6cfe4649 source precedes
the production missing-helper repair; no missing-helper runtime reproduction is
claimed. Explicit imports and narrow source guards are repaired inbf14b333.

[Fixed-source40674343201 attempt1](fixed001-attempt1/failure-review.json) timed out
in the host's first `simctl list devices --json` call at60s, before plan/Gradle,
**zero tests** and no artifact JSON. Cold/transient service cause is not proven.
[Only that failed library job is rerun once](fixed001-attempt2/rerun-receipt.json)
on a fresh runner, same immutablebf14b333/seven methods; successful tooling is
reused. No accepted Android test is replayed. If startup repeats, investigate
bounded simulator readiness rather than changing platform or test expectations.
Source repair/dispatch/retry is not acceptance; #104/#106 remain open.
