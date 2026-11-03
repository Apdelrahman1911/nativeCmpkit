# Shared iOS memory cleanup and real native-input preparation — 2026-11-03

Related batch: **#28/#30/#31/#125/#126**. No new closures or publishing clearance.

## Original lifecycle result, not an all-green run

[41561366636](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41561366636)
at `62cf1e974ece66b0e03db2e9d8b47648d9847e0b` remains **FAILED: three native
methods, one passed/two failed, one XML; Gradle1/1242.58s**. The once-acquired
[complete public JSON/XML and 72-check review](originals/41561366636/REVIEW.json)
retain all 1,234 frozen/own-Git input bindings and original failures.

Accept/exclude `hoistedStateReattachesToANewRealPresenterAndStaleOwnersCannotDetachItsReplacement`.
Both other methods fail their original captured-content weak-reference checks after
three Main GC calls. Native animation protocol, Main loop, Worker termination,
console and owned-app cleanup independently pass; they do not make JUnit green.
Two appearance-transition warnings remain unproven. **#31 stays open.** The result
is not proof of persistent heap growth or a particular ARC/Kotlin retention chain.

## Owning production repair

`BottomSheetManager.kt` now gives the Compose controller a separately held,
observable nullable content lease rather than a manager-capturing immutable
content closure. Disposal clears that lease while composition is live; terminal
Main cleanup clears owned delegate closures, including confirmation and detent
callbacks. Existing public delegate constructor/signatures remain; no dependency
or native-animation/waiter-policy change. Original lifecycle test and host bytes
are unchanged. This addresses source-visible retention edges; **the exact original
runtime retention root and recovery behavior are not yet verified**.

Dependency-source context was acquired once for Compose UI iOS simulator Arm64
1.12.0, SHA256 `db7a743cfdd14af5c2490f232bea0f53df166583b55d7fdc2a36ea0849089f5c`.
Its hosting controller retains immutable content and disposes its scene when it
leaves the window hierarchy. This is not source-to-binary equivalence or proof of
the failed run's retention cause. The earlier UIKit source JAR was a placeholder.

## Important checks, once; no accepted library-test replay

[Original controls and focused compiler receipts](local/) preserve the first
17 driver methods:15pass/onefail/oneerror. Descriptor ownership and nested JSON
were repaired; only failed2+NEW descriptor-close1 then pass3/3. **18 unique new
driver controls are qualified across20 invocations**, using real local loopback
HTTP/owned Python processes, not XCTest/native application input. Six NEW routing/
source controls plus two affected historical inverses pass8/8 once.

[Final compiler-log review](compiler-log-review.json) records XCUI four-source
production/test KLIB0/67.02s and lifecycle three-source test KLIB0/40.01s
(production UP-TO-DATE). Both hold1,245 actual input maps. One BetaInterop opt-in
warning remains. **ZERO Apple link, Swift compiler, XCTest or native executions
locally.** All three new profile source preflights and Actionlint1.7.12 pass;
optional shellcheck/pyflakes were not run. These are not measured hosted speedups.

The exact inverse has six bindings/22 reversible fragments; old lifecycle and
ownership manifest pins stay unchanged. Historical readers compose it offline;
live selectors never import source projections. The older AWT helper is unchanged.

## Next finite verification

1. `ios-modal-lifecycle-memory-recovery`: only the two failed original methods.
2. `ios-modal-xcui-batch`: seven new real input methods on one iPhone.
3. `ios-modal-xcui-batch-ipad`: same seven on one iPad after capacity frees.

The independent Swift XCTest runner attaches to the already-running, nonce-bound
library app. It delivers public taps/type/coordinate drags; no sample, private
activation, callback injection or second app launch. The original library host
owns Worker/app lifecycle; the input driver owns loopback authentication, runner,
process group and private workspace cleanup. Raw configs/logs/screenshots/results
bundles are excluded from uploads. Actual Xcode output format, Swift compilation,
real input, complete interaction/heap/trait criteria remain unverified.

Acquire terminal originals once; retain failed cases; accept/close every complete
sibling immediately after its original source/results criteria are checked. Reuse
accepted iPhone/iPad9 and the accepted replacement method, not blanket native replay.
**98 closed /74 open /172 total**; ledger22implemented/41partial/96verified/5unresolved.
SOLO/development only; serial local/8GiB; max2 hosted reservations INCLUDING queued.
Read-only Actions/all/no mandatory SHA pinning. No packages/releases/deployment,
Pages/main/history or legal/security/consumer/API–ABI/readiness waiver.
