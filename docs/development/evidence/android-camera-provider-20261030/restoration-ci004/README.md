# Actual fourth restoration request: receipt/save timeout remains unverified

[Run 41107030315](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41107030315),
attempt1 at `9f249b7ebbbb1489d91e337110a38758146b2abc`, **FAILED**.
Tooling passes; API35 executes **4/4 failed methods in one fresh XML**, Gradle
exit1/161.04s. All987 library/1064 combined inputs match exact historical Git.
Reporter APK0/278.09s and owned AVD0/2.0s pass. Android15/x86_64 is Enforcing.
Installed receiver-byte identity, owned receiver removal, graceful emulator exit
and owned ADB transport removal are independently reviewed.

All four failures are the bounded initial wait at `capture:103` / `waitUntil:387`:
`received && caller.saves > 0`. Earlier recipient lease/state/component/UID
prechecks passed. **Neither individual conjunction value was recorded.** This
does not establish whether the caller launched, capture was received, state was
saved, or the underlying cause. Do not transplant the previous global-handler or
empty-CLI diagnosis onto this run. No original restoration criterion is accepted.
Original/sanitized XML copies are **one report**, not two executions.

The subsequent [foreground-contract fixture repair](../restoration-foreground001/README.md)
is source-confirmed but **not proven to explain this timeout**. Native execution
of that repair still requires a fresh immutable request. This run predates the
failure-safe dependency-cache workflow patch and does **not** verify that patch.
Provider/API23/host/unrelated accepted suites were not replayed. #13 stays open;
all native/consumer/API-ABI/heap/dependency/legal/security/release, publishing/Pages,
main/history and single-agent/capacity restrictions remain.
