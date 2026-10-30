# Actual native workload pass; Instruments recording failed

[Run41002405707](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41002405707)
at `de6c161800fd027c99d0682484d588c0ba95fb4b` is green; the
[independent review](review.json) verifies **one fresh native testcase/XML**,
Gradle0/1484.68s,903 exact historical inputs and complete Worker/runtime/binary/
install/owned cleanup. Actual workload:369 rounds/738 conversions. Native readiness,
console, simctl launch and profiler target all match PID85680.

**The separate profile failed/unverified.** Actual `xctrace record` using
Allocations/12s/owned attach exits21 after20.25s:zero allocation exports and zero
leaks invocations.44-byte private tool log was deleted during verified owned
cleanup; exact cause is unknown. Debug entitlement/authorization is only a
hypothesis. No private logs/traces/heaps/binaries are committed or uploaded.

Nine prior image methods and two stress methods were not replayed. This native
workload supports the separately reviewed #140 closure, **not #141/UI-038's
mandatory allocation/leak profile**. Strict40989310808 remains failed/zero tests;
no ASan/all-allocator, device/minimum/ABI/consumer/security/release attestation.

