# Failed Apple profile: explicit test-only debug prerequisite candidate

Actual41008502211 remains native-workload PASS/profile NOT verified: selected
UUID/PID Allocations times out150s, zero rows/exports/leaks command, unknown cause.
Neither signed debug flag was present; that is **not a proven refusal diagnosis**.

[ADR0012](../../../decisions/0012-owned-profile-debug-signing.md) scopes one
verification prerequisite: only `ios-image-profile-recovery` ad-hoc signs its
unique disposable app with `get-task-allow=true`. Exclusive/no-follow0600 input,
exact signed readback and stable owned-input cleanup required. No credentials,
elevation, global debugger settings or public framework/package signing. Existing
strict/full/other modes retain exact previous signer and meaning.

Eight new policy/ownership guards plus two existing default lifecycle guards
pass10/10; two new actual caller-branch synthetic integrations pass2/2 separately.
Twelve distinct synthetic methods, no replay; final925/1002 selected inputs held.
No actual Codesign/Apple/native/profile executions. Source CLI selects exactly one
necessary workload for the still-failed profiler, not the two accepted stress/nine
conversion methods. TDD red38 events/eight methods and private invalid profile
spelling retained as failures; caller fixes do not relax finite selection.

#141 remains open. Only useful owned allocation rows and same-PID actual zero
leaks can certify profiling; signed flags/test success/green CI do not. Strict
startup40989310808 is neither repaired nor waived. No physical/minimum/ABI/
consumer/dependency/legal/security/release gate or publishing/Pages/main/history
change. Private logs/heap/trace/binaries not committed.
