# Atomic native observation and conservative caller cleanup

The fixture previously polled the changing native SharedPreferences XML. Frozen
[Android15 source](public-shared-preferences-source.json) shows backup rename,
new-file creation and XML writing before sync/close and successful commit
publication. A raw reader can observe a missing or partial file. A fresh nonce's
missing receipt also could incorrectly hide a stale own-client task. Neither
finding establishes the cause of the [sixth request's empty shell readback](../restoration-ci006/README.md).

The test-only client keeps all ten actual native preference commits. Its sole
main-thread writer requires successful commit, reads the exact bounded native XML,
creates one nonce-owned pending file exclusively, fsyncs/closes it and publishes
the receipt through same-directory `Os.rename`. The reporter's existing bounded,
strict XML parser reads that immutable publication. The receipt contains actual
native observations; it does not fabricate state, grants, lifecycle or results.

Preflight now refuses pre-existing client tasks and unavailable TaskInfo. Missing
receipts cannot imply absence of an existing task; exact nonce/UID/task ownership
also refuses competing task IDs. Attempted launch is recorded before shell
readback. Cleanup requires actual kernel absence for a verified PID; an attempted
launch with PID0 refuses process absence. Only after task and client termination
may the two exact nonce observation files and native preferences be removed.
Public launcher, real ComponentActivity registry/save/results, genuine Android
URI grants and all four original restoration criteria remain unchanged.

Five initial source failures remain preserved. The first private proposed green
remains **6/7**, with one guard incorrectly counting the helper definition as an
eleventh commit call. The owning guard was corrected. Final private equivalence
checks pass **9/9**; eight persistent checks cover observation/ownership and modeled
host publication/refusal behavior. Root integration then passes **66/66 current
camera-tooling methods**, including the eight new methods and prior58. These
overlapping checks are **not added together** and establish no Android runtime
result. Private console bodies, machine paths and observed receipt contents stay
private; only safe facts and digests are archived.

Fresh serial reporter APK assembly passes **exit0/48.01s**, with all **989 library/
1066 combined inputs held and rechecked** from current guards through compilation.
Only two test Kotlin files and the existing camera CI-test file differ from the
shell-entry candidate. Unchanged receiver compile **0/14.0s** is reused, not fresh.
Exact source-plan/runtime/input maps and completed compile receipt are archived.

**Zero native executions of this patch; #13 remains implemented/open.** Only the
four still-unverified API35 scenarios need a fresh immutable request and review.
Accepted provider/API23/host/unrelated evidence is not replayed. No production or
public-API change, issue closure, publishing/Pages/main/history mutation or native/
consumer/API-ABI/heap/dependency/legal/security/release clearance follows.
