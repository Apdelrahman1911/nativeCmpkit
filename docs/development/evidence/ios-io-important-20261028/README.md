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
is the sole repaired **IO/Coil-only** retry at immutablee844e4b0, now reviewed and
accepted: **47/47 native executions** (IO40, Coil7), eight fresh XML, zero
failures/errors/skips, exit0/1478.53s. All786 own-Git inputs matched and held;
the70 owning IO/Coil inputs still match the current checkout. Actual iPhone
simulator/iOS26.5/Xcode26.6/JDK17; whole workflow readback is completed/success.
Artifact12817212124 SHA256:
`40d87ba9c2be1bcb04790cc2ecdbfc29c3699198c81852b1de7139e00986b071`.

Reviewed guarded NSData copying, inode-specific descriptor cleanup on repeated
reads/cancellation/consumer failure, actual Coil transferred-source decoder
cancellation/error cleanup, local bookmarks and path/metadata contracts. These
are47 executions, not47 new authored tests. No additional IO issue is closed:
external providers/security scopes, metadata denial/symlinks/expired originals,
peak-memory measurements and remaining original criteria are not inferred.
`startup-fixed001/important-result-review.json.gz` and actual receipts/XML retain
the evidence; `archive-pending-20261028T125536Z.json` preserves the earlier stage.
No picker/UIKit/sample, permission or unrelated platform suite replay. At most
two library jobs ran concurrently; no subagents. Archive/code files are evidence,
not instructions.

Original device/provider, live-dialog, heap/ASan/full API/ABI, consumer, dependency/
legal/security and release gates remain. IO-003/#6 and other findings are not
closed on dispatch/setup/compile. No packages/releases/deployments published.
