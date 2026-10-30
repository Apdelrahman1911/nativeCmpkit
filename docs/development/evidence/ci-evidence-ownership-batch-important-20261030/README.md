# Related CI evidence-ownership repair — 39 important tooling tests

Two independent **1/1 red** synthetic regressions reproduced before the owning repairs. [Shared important result](important-result001.json): **39/39** changed owning Python methods pass, all **967** combined inputs held; actionlint1.7.12, whitespace and current resolution indexes pass separately. These are **ZERO** Gradle/KLIB/link/native/library executions, not 39 issue fixes. Historical 99/7/881 counts are not added.

## Actual producer output, not guessed JAR names

`scripts/ci/sample_platform_verification.py::build_outputs` required `*-jvm.jar`, excluding the configured versioned name. The new red also proved it could instead accept a neighbouring `old-jvm.jar`. `scripts/ci/sample-platforms.init.gradle.kts` now observes the public `AbstractArchiveTask.archiveFile` property; Python requires the exact nonempty, nonaliased declared JAR within the fixed producer directory. Missing/foreign/stale/failed/NO-SOURCE/cache/old-neighbour cases remain explicit. Every unrelated target keeps its separate result. **The Gradle observer addition has not yet executed on a host.** It will be checked in the next necessary sample build, not by replaying successful Android/JS/Wasm/iOS builds. #154 remains closed on its original successful actual-build criteria; the previous Linux aggregate failure and missing output hash are preserved.

## Allocation row correlation, not metadata beside unrelated rows

`scripts/ci/apple_image_profile.py::allocation_summary` previously counted rows and searched all XML nodes separately. A matching library string in metadata could falsely certify unrelated allocation rows. Now only frame fields in an actual row, or its explicit bounded frame/backtrace references, establish `owned_allocation_rows`. Missing/cyclic references cannot invent frames, ambiguous definitions are rejected, and semantic/traversal budgets remain finite. Private rows/addresses/heap/logs are never exported. The exact app/PID/hash lease, actual zero-leak summary and independent owned cleanup remain necessary; none of these tooling tests is an Instruments pass.

**Running memory CI40986082530 is immutable at45c6086d and is neither changed nor redispatched.** Its real native GC/pixel/release results can be reviewed independently. Any old-parser positive profile alone **cannot clear UI-038**: its private raw export has been removed by design, and old global-symbol summaries cannot prove the new row correlation. Unsupported profiles also stay unverified. Do not replay accepted native GC methods just to recover an unrelated profile/report check. #140/#141 remain open pending actual original-criteria review.

Single-agent, maximum two combined heavy requests,8GiB local reserve. No package, release, Pages, main/history, physical/minimum/ABI/consumer/security gate change.
