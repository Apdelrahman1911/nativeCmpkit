# Shared popover CI prerequisite511–513 — repaired, not native-verified

Both original requests at `76a9c53569543d17d648636f949c72c74cd70132` failed
**before platform selection, Gradle, Apple linking or native execution**:

| Original run | Host requested | CI controls | Result |
|---|---|---|---|
| [41711039589](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41711039589) | iPhone |2,622 /154.474s |five errors |
| [41711096345](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41711096345) | iPad |2,622 /97.357s |same five errors |

The preceding three tooling scopes pass35/80/96 each. Eight original log members,
zero artifacts and zero XML per request are acquired once and hash-verified.
Each source/results review accepts16 passive checks. The1,293 frozen inputs match
their own original Git blobs; **there are no actual platform before/after maps**.
A first reviewer timestamp-normalization refusal is retained; corrected review
reuses the original logs without redownload. Neither original is a native failure
or a passing platform gate.

## Root cause and one related patch

All five failed methods enter the older Worker-completion current-stage reader
with the newer popover routing afterimage. Its original complete SHA guard rejects
those bytes before the older repeat/Worker readers. The new popover layer was
already composed in other modal readers, but this shared ancestor entry was missed.

Only `scripts/ci/ios_worker_completion_source_projection.py` changes: one import
and exact newest-afterimage peeling before the two older-stage admissions.
Three reversible fragments are bound by
`scripts/ci/fixtures/ios-popover-worker-history-composition.json`. Every older
manifest, SHA, refusal and inverse/forward round-trip remains unchanged.

This **ancestor adapter is not latest-source certification**. Only the exact
popover afterimage is peeled; other bytes must still satisfy the original older
stage. That stage may admit its own exact historical afterimage for composition,
but `current_source_before_popover_anchor` still rejects it as current. Partial,
foreign, drifted and wrong-type inputs remain refused. Live selectors never import
either inverse. Production, native test bodies, helpers, compiler inputs, workflow,
dependencies and public APIs are byte-unchanged.

## Important verification and next step

Only the five actual failed methods plus five new composition controls run:
**10/10 pass once**, unittest0.410s/wrapper0.410445385s. The new controls cover all
three shared postimages, exact three-fragment round-trip, ancestor/current boundary,
negative causal refusal and unchanged older pins/live-input separation.
All1,295 library inputs hold;1,292 existing inputs are unchanged, one old reader
changes and two inputs are added. Fifteen passive source/results checks accept.
No accepted controls or compilers are replayed. The exact four-source successful
test-KLIB507 remains applicable because every compiled source/helper/init-script
and production/dependency input is unchanged; this is **not Apple linking**.

Next: freeze/push and request only the five previously unexecuted methods per real
iPhone/iPad host, maximum two reservations INCLUDING queued. Reuse successful
unchanged evidence, repair only actual failures. **#29 remains open**: even green
controlled anchor cases do not prove actual OS rotation or iPad split view.
Counts103closed/69open/172 and ledger22implemented/36partial/101verified/five
unresolved remain. SOLO/development/read-only Actions/all/no mandatory SHA pinning,
serial local8GiB and every publication/Pages/main/history/native/consumer/API–ABI/
dependency/legal/security/readiness gate remain; no publication.
