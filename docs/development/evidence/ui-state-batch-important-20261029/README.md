# Related remembered native state acceptance — 2026-10-29

Shared important batch: **UI-010/#124 and UI-019/#127**. Both remain open until
the original criteria and actual native results are reviewed together.

## Owning changes and checks

- Time manager reads/writes a copied native calendar in the actual picker's
  explicit zone, or Foundation's live local zone, without mutating the supplied
  calendar. UIKit operations are main-confined. Disposal removes only this
  manager's native target/action and late dispatch cannot edit obsolete state.
- Two new genuine public time-control methods cover identical-state recomposition,
  two native locales, explicit fractional/DST zones, two process-default zone
  changes/restoration, state replacement, actual controller replacement and
  deliberately retained old native actions. These are not OS Settings locale,
  hour-cycle, native wheel touch, accessibility or physical-device certification.
- Two new genuine public sheet methods cover visible callback replacement/veto
  and subsequent actual hide, density changes without identity churn, actual
  `SaveableStateRegistry` save/restore into a new root and deliberate skip-policy
  replacement/old-owner teardown. Native iOS does not use Material's numerical
  drag thresholds; the tests do not invent iOS threshold parity or drag input.
- The UI host adopts the exact picker-host-proven native appearance/disappearance
  witness while retaining Worker/real Compose/plist/rendering/cleanup contracts.
  Four changed host methods are included with the four new state methods.
- `ios-ui-state` selects **eight exact actual application methods only**. It does
  not replay accepted dates, images, other controls, browser/Android/desktop or
  consumer suites. Native compilation and adapted tooling are not functionality.

## Evidence before immutable native verification

[Local review](local/review.json): initial production/test KLIB exit0/50.01s;
the final changed Foundation-default-zone test KLIB exit0/40.01s with864 held
dirty inputs. **Zero native runtime tests**. Five new finite selection/receipt
guards pass. Related guards initially113/114: one old exact lexical controller
call fails; its owning check is updated to the real configured lifecycle call
without relaxing strict plist policy, then only that method reruns1/1. Earlier113
successes are not replayed. A mistaken native-profile test selector is preserved
separately; its correct original method passes in a separate invocation.

The Python host-call guard changes **after** the held KLIB: an immutable binding
must disclose that one noninvoked recipe-input delta rather than claim all864
bytes were compiled at the final revision. Actual native8-method CI and original
criteria review are pending. No new closures, package/release/deployment/Pages,
main/history changes, or physical/minimum-platform/ABI/security/release promotion.

### Additive acceptance strengthening before dispatch

[Third held KLIB review](local/local-klib003/review.json) records exit0/50.01s
with all864 inputs held. The replacement picker now visibly starts at14:35,
then a different actual native9:18 edit must update onlyB and leaveA unchanged.
Process-default timezone restoration runs directly on the application main thread,
even if Compose idle fails. Only the changed owning source guard reruns1/1;
earlier accepted tooling is not replayed. Native runtime executions remainZERO.
The earlier post-KLIB input delta is retained rather than rewritten.
