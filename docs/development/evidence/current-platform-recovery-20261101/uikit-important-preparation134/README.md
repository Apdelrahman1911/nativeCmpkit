# UIKit alerts and date-year policy — important preparation

Related **#26/UI-001 and #28/UI-012 remain open**. The owning date resolver now
checks the existing full `state.isDaySelectable` predicate, rather than only
`yearRange`. This prevents a raw wheels/compact pick from admitting a year whose
year predicate rejects it while its date predicate permits it. Public APIs,
coordinates, dependencies and programmatic-setter behavior are unchanged.

- Independent source review accepts the 19 exact fragments /four existing paths
  /five additions. Calendar/field/control delivery is explicitly controlled;
  fresh alert actions require one owned, attached, enabled native UIView and
  **public `accessibilityActivate()` returning true**, with no handler/dismiss
  fallback. The binding is source-qualified and actually KLIB-compiled; actual
  action availability/activation remains unverified.
- [Eight first important source controls](IMPORTANT-EIGHT-RESULT.json) pass8/8,
  zero failures/errors/skips in2.769891s; exact1157 library/1233 canonical combined
  before/after maps and nine source bindings hold. They are accepted and **not
  replayed**. The retained tool literal/pre-import assertions are not a separate
  launcher-file/numeric-startup snapshot or ambient/builder/security attestation.
- [Fresh serial compiler](COMPILER-RESULT.json) exits0/88.02s for production/test
  iOS Arm64 KLIB and Desktop-test Kotlin. All1157/1233 inputs hold; **zero native
  or Desktop tests executed**. Normal Linux/native/cinterop warnings remain.
- [Finite actual source CLIs/preflight and Actionlint1.7.12](SOURCE-PREFLIGHT.json)
  pass. Passive inspection of166 existing tooling test files identifies no new
  stale owning guard; it is an inventory, not166 executed files or full dynamic
  qualification. No accepted full registry/tooling/native population is replayed.

Next immutable route `ios-alert-date-important` requests one macos-26 Arm64
`ios-iphone`: **App10 (alert4+date6)**, then **serial independent Material2 on the
same host**, with different tasks and XML/receipt trees. Either failure remains
red; Material cannot mask native failure. Preserve and review original results
against every original criterion, then close only the verified subset directly.
Optional `ios-date-year-predicate-red` is parked, unexecuted, and not preimage-CI-
qualified. Draft provenance comments remain historical; these exact bindings are
preserved rather than silently changing the accepted compiler inputs.

#30/#131 outside/item touches remain parked. No physical/iPad/minimum-platform,
packaged-consumer/API-ABI/heap/security/release inference. Named-provider Android,
WindowsStop and Wasm clipboard originals failed separately; no blind native retry.
Publishing, Pages, main/history and all readiness/security gates stay unchanged.
Lead owns Git/dispatch/closure; serial local,8GiB reserve/max2 combined hosted-heavy
including queued/reserved; all Actions permitted/no mandatory SHA pinning/read-only.

This public packet contains safe summaries and original source/result hashes;
private original logs/reviewer packets are retained, not published here. No
accepted execution was recreated. Original manifest references are verified on
export, not a new trusted-builder attestation.
