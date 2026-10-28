# Direct permission closures — 2026-10-28

**#104/PERM-001 and #106/PERM-005 closed/completed at11:25UTC**, immediately after
reviewing all three/two original requirements and actual source/results. Issue
bodies/titles/labels are unchanged; see the two closure/readback JSON records and
resolution comments.47 closed issues are independently reconciled; the initial
46-item list observed GitHub indexing latency and is retained, not overwritten.

## Important results, not broad suite replays

| Evidence | Immutable source | Executions | Gradle exit/time |
|---|---|---:|---|
| [Android completions](../permission-android-important-20261028/review.json) |832b36b6|6|0/276.08s|
| [Android registry](../permission-registry-android-important-20261028/review.json) |c19b2bbf|1|0/64.02s|
| [Android singles](../permission-single-android-important-20261028/review.json) |f55d60dd|2|0/95.03s|
| [Actual iOS factories](../permission-ios-important-20261028/fixed001-attempt2/important-result-review.json) |bf14b333|7|0/1123.96s|

Combined16 executions/12 authored methods/four fresh XML,0failure-error-skip;
counts overlap between these findings. JDK17 and780/781/782 own-Git inputs held.
Registry concurrency means16 workers×200 rounds on each owning platform, not
thousands of test methods. Actual public factories, Compose, Android JVM locks,
Darwin queues/Foundation NSLock and lifecycle ownership were reviewed. Controlled
helper/grant completion is not an OS privacy-dialog/device/heap/ABI certificate.

**The whole iOS workflow remains failed.** All seven runtime methods passed;
the exact finite checker wrongly expected unadorned JVM identifiers. The raw
failed receipt remains unchanged. The repair accepts only the observed
`iosSimulatorArm64Test.` class prefix and `[iosSimulatorArm64]` method suffix;
the bare Gradle class filter remains unchanged. Eight focused regression methods
first failed four assertions, then60 combined focused tooling methods passed.
The original held XML passes; missing/extra/wrong-class/wrong-target/unadorned,
duplicate,failed,errored,skipped and missing-fresh-marker cases still fail.
[Verifier evidence](verifier-review.json) is tooling, not60 new native methods or
a hosted green-CI result. **No successful runtime job was rerun.**

Original requirements are explicitly matched in the
[acceptance review](../permission-ios-important-20261028/fixed001-attempt2/acceptance-review.json).
Device/native-dialog/minimum-platform, full consumer/ABI/dependency/legal/security
and release gates remain separate and unchanged. No publication/deployment.
