# Related iOS deferred-presentation ownership repair — 2026-10-29

The previous [seven-method recovery](../ios-picker-recovery-important-20261029/native-ci001/README.md)
remains failed. This additive repair removes the unsafe synchronous-link
rejection inference after UIKit's **void** presentation call, including its
exception path. A pending cancellation/finish retains controller, delegate and
export staging until a genuine native presentation/dismissal completion. No
timer, silent success or early deletion supplies a safe point. A native call
that never completes deliberately retains ownership fail-closed; OS/provider
refusal remains a separate unverified contract, not a solved gate.

## Important checks

- Production/test iOS simulator KLIB compilation: **0/49.01s**, JDK17,
  **856 ordinary inputs + explicit workflow =857** held dirty bytes. This is
  **zero executed native tests**, not an Apple pass.
- Initial owning tooling: **97/98 positive, one CLI-choice omission, overall
  failed**. Only the failed exact-profile CLI method reruns after the owning
  registration repair: **1/1**. Seventy distinct workflow/application-plan,
  receipt and diagnostic guards pass separately. Do not relabel the failed run
  as a current full pass or count the rerun as another authored test.
- Two new regressions hold a per-call scheduling boundary before a real UIKit
  export. Native controller/delegate, later presentation/completion/dismissal,
  Foundation source/staging files, exactly-once owner release and late-generation
  isolation are genuine; scheduling/exception input is explicitly controlled.
- The original real export test requires cancellation **before actual callback
  arrival** and later native completion/cleanup, instead of assuming immediate
  links. The public photo test checks presentation errors before nil-delegate
  assertions and retains all four live configuration/callback rounds.
- The unchanged BasicText host is not removed or substituted. Ten finite
  phase/thread witnesses and transport validation stage/known reason IDs
  diagnose the prior interruption without archiving arbitrary messages, stacks
  or private output. All protocol/Worker/runtime/binary/cleanup gates remain.

`ios-picker-admission` selects **seven changed owning/host methods plus two new
regressions**, on one actual Apple simulator host. The original26 and7 plans
remain intact; **19 completed Foundation/filter/copy/staging methods and all
accepted other hosts are not replayed**. See [local review](local/review.json).
Native acceptance and IO-017/#53's original-criteria review remain pending.
No issues are closed by source/compile/tooling alone. Independent provider,
swipe, native-parent, physical/minimum-platform, ABI, full consumer, dependency,
provenance, legal, security and release gates remain. Single-agent; main/history
and attribution preserved; no packages, releases, deployments or Pages.
