# NativeCmpKit: immutable NAV-006 acceptance and complete SDK context

Single-agent contained development; verification remains read-only, Actions
enabled/all allowed/no required SHA pinning. Preserve `main` and imported history.
**No package, release, deployment or Pages gate is lifted.**

## Actual immutable navigation and SDK verification

[Run 40576835737](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40576835737)
at exact `6ada26d3c47096ad0750a111c7e807b03230d844`, attempt 1, passes **55 / 55
actual desktop methods, seven fresh XML**, zero errors/failures/skips. The
[independent review](evidence/github-actions/40576835737/lead-independent-review.json)
reconstructs this run's **727 own-Git inputs**, exact plans/commands/runtime and
fresh task/XML hashes/timestamps. Gradle exits **0 after 217.06 seconds**.
All **54 prior testcase identities** are retained, plus the new same-controller
empty/nonempty start-policy method; complete real Compose host class **12 / 12**.

The official `platforms;android-37.0` metadata and **global runtime fingerprints
now match setup and actual test capture**; observation time is the only context
difference. This actually verifies the owning SDK capture repair on Linux desktop,
not merely its three synthetic methods. Other suites still need their own runtime
correspondence evidence. The historical Windows capture omission is not rewritten.

The canonical cache **misses then saves**. No cache hit/dependency-trust or old-test
reuse is claimed. One narrow job, no unchanged Windows/Core-IO/UIKit/browser/geo
redispatch. Twelve finite JVM allocation rows repeat earlier probes without
certifying portable latency, native performance, peak heap or input limits.

## Every original NAV-006 criterion

The [original acceptance review](evidence/navhost-original-acceptance-20261027/lead-original-acceptance-review.json)
checks the baseline finding remains byte-identical to the completed issue-sync
checkpoint and maps all three requirements to current **passing immutable** methods:

| Original requirement | Actual evidence |
|---|---|
| Replace the controller at one composition site, verify initialization/current routing | `replacement controller is initialized and receives updated graph callbacks` retains the original controller's route while the replacement handles the new callback. |
| Outer callback/state changes reach graph content | `updated closures do not lose entry state or reset a nonempty stack` shows the new label and preserves saved state/current route. |
| Explicit empty/nonempty `startDestination` policy | New `changing start route initializes an explicitly emptied stack at the same host` verifies fresh identity/single route/no stale UI, then a later start change cannot reset it. The preceding method separately preserves an already nonempty stack. |

Production builds the graph on recomposition, attaches/disposes the keyed controller,
updates graph ownership in `SideEffect`, and keys initialization on controller/start
only when `currentBackStackEntry == null`. The
[ADR 0004 policy](../decisions/0004-adaptive-navigation-entries.md) and actual source
hashes are checked. No production navigation edit was needed in this continuation.
The prior copied-old-effect **one-method failure** and original-host **12-method
green** diagnostic remain preserved, not substituted for immutable CI.

Ledger: **67 implemented / 78 partially verified / 8 unresolved / 11 verified**.
Only NAV-006's original shared-host scope is promoted. NAV-001/002 broader entry/
ownership/restoration and NAV-004 erased getter remain separate. This is real Compose
desktop, **not Android/iOS host-UI integration or native navigation parity**.

**[#94 is now readback-closed](evidence/navhost-issue-closure-20261027/lead-final-readback.json)**
after the acceptance/evidence was pushed at `a8ed58a7`. Exactly one additive comment
and state-only PATCH; **15 total closed issues, one new closure**. Fourteen prior
closures and original issue body/title/labels/history remain unchanged. NAV-001/002
were already verified/#15/#16 closed; their broader platform gates are not cleared
here. An initial dry-run reviewer incorrectly assumed those records were unverified;
it stopped before any mutation and is preserved with the corrected owning checks.

## Preserved review failures and next work

The [fresh held preflight030 review](evidence/ci-preflight-20261027-030/lead-review.json)
checks five lightweight audit/index/strict-MkDocs/whitespace commands, **18,407
held inputs** and **58 actual anchors in 23 new HTML outputs**. It executes zero
Python/library/native methods, not another full 1,286-method preflight029 run.
All prior executable inputs match029; this additive archive/link follows the
freeze and does not self-certify a later commit.

- [Source-literal reviewer failure](evidence/navhost-acceptance-review-red001-20261027/failure.json):
  the reviewer expected `backStack.isEmpty()`, while current code explicitly tests
  `currentBackStackEntry == null`. Correct exact source checks retain all three
  runtime criteria and hashes; no library assertion was weakened.
- [Ledger-format rejection](evidence/navhost-ledger-review-red001-20261027/failure.json):
  unrelated broader gates/issue closure were wrongly placed in a verified record's
  `remaining` checks. They stay explicit compatibility/scope limits; original
  criteria are complete and the validator remains strict.

Next add fresh actual iOS IO guarded-copy, unreadable-file, stream/resource and Coil
propagation coverage without samples or unnecessary UIKit reruns. Current fifteen
objc2 text/Apple-SDK gaps, native parents, Android/provider/device/minimum-platform,
ordinary dependency trust, native payloads, full/minimum-platform consumers and
API/ABI remain [release blockers](release-readiness.md). Neither this closure nor
the 55-method suite certifies the first Preview Release.
