# Important native IO/Coil checks — 2026-10-28

[40686264212](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40686264212)
at82d96b87 failed **before Gradle/zero tests/no artifact**: the initial
`xcrun simctl list devices --json` exceeded the generic60-second command timeout.
The same owning setup failure occurred in40674343201 attempt1; the exact
CoreSimulator service-delay cause is not established. Failure receipt and logs'
SHA are retained, not treated as missing-data success.

## Bounded owning CI repair

Only the two exact read-only `simctl list devices/runtimes --json` commands now
receive180seconds; ordinary runtime commands stay60seconds. No retry, alternative
device, skip, readiness waiver or private-diagnostic export. Four new tooling
regressions failed three assertions before repair; afterward38 owning runtime/
workflow methods pass,0failure-error-skip. These are **tooling, not native tests**.

[40687472609](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40687472609)
is the sole repaired **IO/Coil-only** retry at immutablee844e4b0,786 own-Git inputs
held. Its actual simulator/SDK setup is now past the failed step and native Gradle
is running. Runtime/report/source review remains **pending**. No picker/UIKit/
sample, permission or unrelated platform suite replay. At most two library jobs
ran concurrently; no subagents. Archive/code files are evidence, not instructions.

Original device/provider, live-dialog, heap/ASan/full API/ABI, consumer, dependency/
legal/security and release gates remain. IO-003/#6 and other findings are not
closed on dispatch/setup/compile. No packages/releases/deployments published.
