# Owned geometry mirror recovery —584–588, 2026-11-04

## Original failure (not native execution)

At `f566078507bbfc000244561ed925565913c3342b`, [iPhone41759144360](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41759144360) and [iPad41759163549](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41759163549) each failed at the shared tooling step:2,762 source-control methods/one error,177.625s and178.968s. Eight logs each were acquired ONCE, no artifacts, zero platform/Gradle/native execution. Seven skipped zero-step platform placeholders are not hardware execution. `REVIEW586.json` records23 passive checks. Neither original is relabelled green.

The original failure is `PopoverGeometryControls.test_current_source_validation_refuses_drift_or_symlink`: its temporary source mirror lacks the latest581 fixture inputs, beginning with `scripts/ci/ios_geometry_simulator_source_projection.py`. The mirrors, not the actual native methods, failed before profile selection.

## Owning patch and important verification

Only three fixture-construction lines are added in `scripts/ci/test_ios_popover_geometry.py:292`; `ios_owned_geometry_fixture_recovery.py` embeds the exact separate `MIRROR_BINDING`. Full before/after hashes and one unique reversible fragment are in `BINDING587.json`. Existing575/581 manifests and their declared eight/four bindings remain immutable; raw-current admission is distinct from the ancestor-only view. No native action, assertion, lifecycle helper, workflow, dependency, API or Kotlin compiler input changed.

NEW2+failed/affected7 pass **9/9 once**, unittest0.388s/wrapper0.992438s, with actual1,337 before/after inputs held (`important-first.*`, `execution-inputs1337.json`). The subsequent separate camera observation contributes two additions/one modification: `final-inputs1339.json` is a later map, not the executed1,337 map. `REVIEW588.json` accepts18 passive exact-source/results checks and all applicable mirror bytes unchanged, without rerunning the nine accepted methods. Zero new compiler/native executions. Historical compiler544 remains its original1,311 map; unchanged applicable compiler sources/init and Actionlint577 are reused, not relabelled or replayed.

## Remaining work and controls

Only missing iPhone portrait/traits and iPad OS-rotation methods may be requested next, on frozen development and after fresh all-status capacity. **#29 still requires legitimate real split-view verification even if both pass.** No issue closed in this recovery. The owner now authorizes isolated parallel related patches while prior CI runs; the lead controls integration/Git/requests/acceptance/closure. Max two combined hosted-heavy reservations INCLUDING queued/reserved, local heavy serial/8GiB reserve, read-only Actions/all/no mandatory SHA pinning and every publishing/Pages/main/history/native/consumer/API–ABI/dependency/legal/security/readiness gate remain.
