# Shared XCTest foreground recovery463–464 — 2026-11-03

## Both original hosts are failed, not partially accepted

| Original run at `b73a1078777f37a2bff547073aafef2e4cb58c74` | Native XML | Gradle | Native protocol |
|---|---|---|---|
| [iPhone41587733015](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41587733015) | 7 failed /0 passed /1 fresh XML | exit1 /1,568.14s | 215.14s /console0 |
| [iPad41587765229](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41587765229) | 7 failed /0 passed /1 fresh XML | exit1 /1,863.82s | 220.25s /console0 |

Each original was acquired **once** and independently checked against all **1,267
actual own-Git before/after inputs**, its exact four compiler sources and fresh
XML/protocol identities/counts. Mandatory runner0/Worker termination, all six
ordered lifecycle phases and all four owned-app cleanup witnesses pass separately.
The independent input runner also cleans up its four owned resources. These are
not passing library tests: actual XCTest input, input completion and post-runtime
custody are not accepted.

Both first requests (`alert-field`, sequence1) receive the fixed
`foreignOrInactiveApplication` refusal. The other six methods fail waiting for
their later input acknowledgments after that runner exits. The original immediate
guard observed **not foreground**; its particular enum value and underlying
discovery/foreground cause were not recorded. Do not attribute these failures to
alert/sheet production behavior or claim that all their assertions ran.

[Originals/reviews](originals/) and [exact report provenance](public-report-provenance.json)
retain all **30 original JSON/XML report members**. Whole-log/member hashes remain
in acquisition receipts; no full logs, private XCTest configuration, screenshots,
packages or binaries are published. Both reservations are freed. Never retry the
old request scripts or replay the already-accepted modal/cancellation populations.

## One shared source repair; no relaxed input or ownership gate

The confirmed source defect is an immediate read of `XCUIApplication.state` even
though Apple's [public state contract](https://developer.apple.com/documentation/xcuiautomation/xcuiapplication/state-swift.property)
states that the system updates it **asynchronously**. The independent runner is
ready before the original controller launches the library app. An external launch
does not guarantee that this separate XCTest object's state has already caught up.
This establishes a source-level readiness gap, **not the exact original hosted
delay/cause**.

At `tests/native-ui-input/NativeCmpKitInputTests.swift::deliver`, only a public
`wait(for: .runningForeground, timeout: 5)` is added. It must succeed and the final
state must still be foreground **before any input**. There is **no activate,
launch/relaunch, private selector, manager/delegate callback or fake input fallback**.
All original unique/hittable/enabled/tap/type/drag assertions remain unchanged.
Unknown/background/not-running states still fail closed.

Failure-only logging preserves exact initial/final **raw enum scalars**, whether
the wait was attempted and its result. `scripts/ci/native_ui_input.py` admits only
bounded, fixed-format observations; private credentials/session strings and
arbitrary logs are excluded. These observations never admit native success.

The exact two-path/three-fragment source inverse composes at the offline Worker
reader. Its original **six paths/23 fragments and old pins remain immutable**.
The first three source-control errors are preserved: the initial new inverse was
placed before the old stage's exact idempotence check. Moving it **after** that
check repairs historical reading while current-source admission remains strict.
The older project-root control now qualifies its owning stage after the new exact
inverse instead of falsely calling the newer file the old one-line postimage.

## Important source/results review and evidence reuse

[Important results](important-control-results.json) and
[source/results review](SOURCE-RESULTS-REVIEW.json) accept **14 unique controls**
across **18 invocations**: initial source red1, first10 (7 pass/3 history errors),
only failed3 plus two affected controls5/5, and two affected source-aware
diagnostic/admission controls2/2. Accepted controls were not replayed. The
[review-label correction](review-label-correction.json) clarifies that six Python
sources were parsed; it does not repeat qualification.

All **1,270 current library/tooling inputs** hold. Every Kotlin native method,
the exact four-source compiler route, production/API/lifecycle/dependency bytes,
Xcode project/scheme and workflow remain unchanged. Reuse the original applicable
compiler receipts; **ZERO new Kotlin compilers or native executions** locally.
Swift compilation and the actual readiness recovery remain unverified until the
new immutable native batch executes.

## Next: missing interactive criteria only

Run the same seven missing methods once per actual iPhone/iPad at the new frozen
development revision, within **maximum two combined reservations including queued**.
The original [four-issue criteria](original-source-criteria.json) remain mandatory:
**#28/UI-012, #30/UI-014, #125/UI-016 and #126/UI-017 stay open**. Close genuinely
complete siblings immediately after their own original input, assertions, full
protocol and cleanup qualify; a batch failure or green XML is not a waiver.

#31, #144 and #171 are already closed; do not repeat their closures. The last
issue-state readback remains **99 closed /73 open /172 total**, with
22 implemented /40 partially-verified /97 verified /5 unresolved. No status
promotion or issue closure occurs in this source-only repair.

SOLO; serial local heavy/8GiB reserve; development only; read-only Actions/all/
no mandatory SHA pinning. All publishing/Pages/main/history/legal/security/
consumer/API–ABI/release-readiness gates remain. **No release, package or deployment.**
