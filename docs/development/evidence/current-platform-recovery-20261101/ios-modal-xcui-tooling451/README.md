# Original real-interaction request451 — tooling failure, 2026-11-03

[Run41578428938](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41578428938)
at **7a9340a727a630d0f63f94aa746410d97d89c2f5** failed **before profile selection**.
Its eight original log members were acquired once; there are no artifacts.

## Confirmed shared cause

The original `scripts/ci/test_android_external337_fixture_recovery.py:212`
expected `exact current iOS modal Worker/startup recovery source` for all six
mutated/historical library inputs. The new, earlier same-operation current-source
guard correctly raised `A historical image cannot replace the exact current
sheet same-operation source`. The fixture confused a later component's wording
with the important invariant: **current-source refusal before historical digest**.

Actual tooling: **2,531methods/88.327s**, six failure records across **one method**;
seven downstream jobs skipped. **ZERO library Gradle/Apple/Swift/XCTest/native/
XML/input executions.**1,262 frozen own-Git inputs establish dispatch provenance,
not actual platform custody. Standalone XCTest startup remains independently
accepted; this run neither tests nor disproves it.

## Owning repair and verification

[Batch453](../ios-worker-completion453/README.md) replaces brittle message matching
with a causal barrier: a historical read of the mutated library would raise an
`AssertionError`, so it cannot satisfy the expected current-source `ValueError`.
The six cases also require **zero historical library-reader calls**. Other
owned paths delegate normally. Existing manifests/pins and all live admission
refusals remain unchanged; there is no blanket regex or native-gate waiver.

The failed method and an independent NEW barrier control pass in the important
local batch. Actual iPhone7 remains unexecuted; do not request iPad7 against an
unreviewed shared native transport failure.

Original [acquisition](acquisition.json), [review](review.json) and
[run metadata](run-summary.json) retain the FAILED outcome.
