# Shared modal lifecycle completion and focused compiler — 2026-11-03

Companion to [batch416](../ios-modal-ownership-batch416/README.md), which fixes
shared causes across **#28/#30/#31/#125/#126**. Nine new cases are running at
`c5bc917a` on [iPhone](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41552604094)
and [iPad](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41553575992).
Their outcomes are not yet accepted; both reservations remain occupied.

Three additional library regressions complete missing #31 lifecycle coverage:
public disposal during native hide/reopen/content GC; hoisted state through two
actual presenters plus state replacement/stale-owner isolation; repeated admitted
show/hide disposal with cancelled waiters and weak-reference collection.

## Important local results

See [local-verification.json](local-verification.json) and retained originals.

- Default iOS test KLIB: **exit0 /40.01s**, 1,232 held inputs; production up-to-date.
- Focused KLIB: initial **exit1 /18.01s**, before library compilation, because the
  init script also visited convention builds. The scoped correction passes
  **exit0 /42.01s**, 1,233 held inputs and **exactly three effective Kotlin sources**.
  Only this new profile uses the opt-in compiler; ordinary/full source sets,
  production and dependencies are unchanged. This is not native execution or a
  measured end-to-end speedup.
- Seven new source controls qualify, plus affected/failed-only historical checks.
  Preserve the six strict refusal-message expectation failures and one erroneous
  positional-command fixture; only their failed methods were corrected/rechecked.
- Three routes/eight exact inverse fragments retain the original modal manifest
  and all historical pins. Live native routing does not use these projections.
  Both real profile preflights and Actionlint1.7.12 pass.

Next select only these three new methods with
`ios-modal-lifecycle-replacement` (or its separate `-ipad` profile), after a
reservation becomes available. Reuse successful nine-case/legacy evidence on
unchanged applicable bytes; never replay it as another fresh pass.

**Zero new native executions or closures here; 98 closed /74 open.** Original
alert activation, inside/outside input, interactive detents and iPad-specific
requirements remain independent acceptance gaps. Solo, development branch only,
serial local builds/8GiB reserve, maximum two hosted reservations including queued
work, read-only Actions and all release/security/publication gates remain.
