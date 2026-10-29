# Original sample batch 40962484420 — FAILED before builds

Immutable `a39a36e55b64d16c34ad7ed19eded0629ffbc3e5`; all 960 selected
preflight inputs match exact Git. Tooling reaches source planning, then the
actual workflow raises `AttributeError: module workflow_matrix has no attribute
ROOT`. `sample_platform_verification.ROOT` is the existing correct producer
root. **Zero sample Gradle/native executions or XML; all sample/library/consumer
jobs are skipped.** No issue/runtime/release acceptance follows this run.
The failed run is retained; do not redispatch its existing attempt receipt.
