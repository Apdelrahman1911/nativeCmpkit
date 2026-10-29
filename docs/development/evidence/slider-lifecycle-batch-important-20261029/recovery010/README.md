# Shared slider observer subscription repair — native verification pending

Owning batch: UI-027/#34 and UI-034/#137, both production Liquid/Cupertino renderers.
The [prior serial native recovery](../recovery009/serial-native-ci001/README.md)
remains failed. Its tap/opposite-tap assertions completed; do not invent a new
production comparator fault. Published Foundation1.12.0 source and the fixture
confirm an eagerly-read State subscription was missing: a delegated local read
only in SideEffect runs outside composition's read observation.

The smallest fixture repair reads each real source's State.value during
composition, preserving both stable source collectors across source replacement.
Old-source and current-source cancellation must both clear; no shadow reset,
stub, action removal, assertion weakening or library/public API change. Finite
actual source Start/Cancel/Stop/observer/finish snapshots precede waits and the
original assertions, so a failure is observable even if teardown then stalls.
All62 structural/24 tap phases,512ms writer checks and300s app deadlines remain.

Important synthetic results (not native tests): first2 red methods yield1failure/
1error; standalone5 pass without a pre-snapshot, not source-held. Shared104 includes
103pass/one incorrect module-loader error. Only actual archive13 and current
owning6 methods execute next: **19/19**, all878 inputs held. Five methods overlap
103;117 distinct successful methods across these shared/final runs, not123 unique.
Only one synthetic guard changed between held snapshots; all other877 hashes remain
exact. No repeated accepted library methods, local KLIB/link or native execution.

Only four unfinished native methods need replacement on one shared host in two
independently cleaned applications. Two completed enable/callback methods remain
unchanged and explicitly reused, not replayed. Close each original-criteria verified
subset immediately when actual results permit; #34/#137 are not yet verified.
Single-agent/max2 combined heavy requests, no heavy local build below8GiB; no
publishing/Pages/main/history or independent release/security gate changes.
