# Separate Darwin/Instruments memory attempt, not a strict-mode repair

See [ADR0011](../../../../decisions/0011-independent-apple-memory-diagnostics.md).
The actual strict [40989310808 failure](../native-ci002/README.md) remains failed
with zero tests and no profile. No existing strict assertions are disabled or
overridden, and no third-party compiler/runtime/dependency is patched/downgraded.

`ios-image-memory-darwin` prepares a distinct **default-Kotlin-runtime** request
for the same **three unchanged** library GC/failure/profile methods and the
existing actual Darwin process heap requests/Instruments/leaks transport. Its
finite `--image-diagnostics darwin-tools` flag binds the mode before the generated
native registry; receipts explicitly do **not** attest strict runtime checks.
Nine accepted UIImage methods are not replayed; public frameworks/APIs stay.

One owning missing-profile guard was first **red1/1**. The shared important run
is still **FAILED: 176 methods /175 passes /one fixture KeyError(scope)**,
all973 inputs held. The owning correction reads actual `plan.scope`, retaining
the required distinct diagnostic scope. Only its **10 methods** rerun and pass
**10/10**, zero failures/errors/skips,0.554s; nine overlap the first run's successful
methods, not185 unique successes. Only that synthetic test file changed; all
other selected bytes and every original native method/assertion remain held.
Actionlint1.7.12 passes. **Zero local Gradle/KLIB/link/native/profile executions.**

The alternative is **native-unverified** until one immutable Apple attempt is
reviewed. Actual owned allocation rows and PID-specific zero leaked bytes are
still independently mandatory. Native tests/environment requests alone cannot
establish supported profiling, ASan, strict runtime checks, release readiness or
any closure. #140/#141 stay open, their strict-startup progress comments are
preserved. No publishing/Pages/main/history/security gates change; one unrelated
WebView native request40993609497 continues on its original16c9a530 inputs.
