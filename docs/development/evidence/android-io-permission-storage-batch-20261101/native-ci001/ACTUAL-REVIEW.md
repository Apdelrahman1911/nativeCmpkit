# Actual first-batch requests: tooling failure, no native execution

Both41262577203 and41262586150 at `a18532a4` **remain FAILED**. Each runs1501
scripts/ci model methods:1500 pass/one stale exact diagnostic-tree guard fails
(65.557s/81.416s). Native, SDK and compiler jobs are skipped; artifact API returns0.
The single source-confirmed cause is `test_failure_diagnostics.py:218`: its exact
old eight-module expected list omits both calf-permissions/core result trees.
Production `failure_diagnostics.capture` correctly enumerates the current nine
modules/18 trees. This is not a device, emulator, APK, permission or native failure.
Original raw-log hashes and completed run identities are preserved in JSON; raw
logs remain private. No passing model turns either workflow green retrospectively.

Recover only that test guard, retaining every exact old tree and adding the two
new exact paths. Do not weaken confinement, absence/symlink refusal, full-log or
success-inference assertions. All16 planned native executions remain unexecuted;
only the same two finite batches may be requested next, without accepted runtime
or compiler replay. #102/#118 remain open; publication and all other gates remain.
