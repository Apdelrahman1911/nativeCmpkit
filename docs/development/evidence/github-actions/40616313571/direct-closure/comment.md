## Verified fix — direct closure after important host/restoration tests

All **three original NAV-007 acceptance criteria** pass at immutable **c0f5cafcec1c53b10f93897533c3c3875afd8282**, [run40616313571](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40616313571): **59/59 actual desktop library methods**, seven fresh XML, zero failures/errors/skips. All16 real Compose-host methods run; four new regressions address the missing original requirements. Only calf-navigation ran.

1. Duplicate public host registrations throw the exact deterministic **Duplicate navigation route 'home'** diagnostic, rather than silently selecting the first content; no stack is initialized.
2. An unknown public start route fails before initialization. A genuine **public controller Saver + serialization round-trip** containing an app-removed route fails explicitly against the new graph and preserves every saved entry ID. Later unknown navigation against an attached valid graph rejects before changing its valid entry stack.
3. The documented **explicit application-selected, potentially lossy reset** is chosen before mounting the host. A distinct controller/new entry renders fresh home state, remains visible after a rejected unknown navigation and supports normal detail/back saved-state restoration. The old restored controller is not silently edited. Business data must be migrated independently and the selected controller persisted by the application; this is not automatic lossless library recovery.

Root repair: the graph builder rejects duplicate/blank routes; the public host validates start and all stacked/restored routes before rendering; attached controller navigation validates before stack mutation. Existing public package/factory/controller methods and legacy back-stack getter remain. Fail-fast errors are an intentional observable correction, documented with upgrade instructions in `docs/development/navigation-unknown-routes.md`/ADR0004.

Review verifies742 exact own-Git inputs, before/after maps, all59 authored testcase identities, XML/artifact hashes, actual Xvfb/JVM command and runtime/SDK correspondence. Required tests → source/results review → **direct closure now** → archive/index afterward. No unrelated browser/native/device/consumer suites replayed.

Scope: real public Compose host and saver on Linux/JVM. Not Android process recreation, UIKit gestures, browser history, business-data migration, native sanitizers, minimum devices, dependency/legal/full consumers/API-ABI or release certification. Those wider gates remain open. No packages/releases/deployments published.

Evidence: `docs/development/evidence/github-actions/40616313571/`. Original issue body/title/labels and earlier failures preserved.

<!-- nativecmpkit:direct-acceptance:NAV-007:c0f5cafc -->
