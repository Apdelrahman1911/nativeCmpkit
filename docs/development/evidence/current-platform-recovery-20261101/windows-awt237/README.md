# Bounded desktop AWT fixture ownership — actual237

The failed Windows199 run remains failed; its original artifacts are reused,
not downloaded again. Its timeout does **not** establish a particular deadlock
or a public Stop failure. Source nevertheless confirms unbounded
`SwingUtilities.invokeAndWait` calls in the selected fixture's setup/cleanup.

## Fix and regression results

`BoundedDesktopAwtWindow` replaces those calls with asynchronously scheduled,
owned AWT work. The caller waits at most30s for initialization and10s for disposal.
Pre-entry cancellation prevents allocation. A late constructor return after a
timeout disposes its exact object without configuring/showing it. Nested dispatch
cannot dispose during initialization. Disposal is attempted once; its exact
handle remains owned throughout the native call and after a throw, and clears
only after successful return. Primary setup/cleanup failures remain visible.
The failed public Stop method additionally bounds its FX listener-removal wait
to10s. Original Stop actions, six native/peer-EOF predicates and10s acceptance
deadline stay unchanged; HTTP/server and redirect method bodies are unchanged.

- First selection: **eight NEW controlled scheduler/concurrency tests pass**,
  one fresh XML, **Gradle0/34.01s**, XML suite0.156s.
- Subsequent refinement: handle retention through successful/throwing disposal;
  **only its one NEW regression executes/passes**, one fresh XML,
  **Gradle0/28.01s**, XML suite0.119s. The exact **1197 before/after inputs hold**
  for this second run.
- Original XMLs are preserved before another Test task can replace them.
  The cumulative8+1 results are **not a freshly executed full-nine suite**.

## Evidence limits

Tests use controlled objects/schedulers and real owned threads. **Zero JavaFX
or Windows native methods execute locally.** Timeouts do not interrupt/preempt
a blocked native AWT constructor or disposal call. A late native return, actual
window release, FX owner cleanup and final worker termination remain required.
Fixed-token timeout observations are not their cause or a successful receipt.

The first eight-test run's immediate-after input map was not captured before
the two-file handle-retention/NEW9 refinement. Its before map and original XML
are preserved, but do **not** claim original immediate-before/after1197 equality
or current whole-nine acceptance. [REPORT.json](REPORT.json) separates both
source versions. Current source/results review and native planner integration
are required before a meaningful Windows-only recovery request.

**#64 stays open.** No blind unchanged70-minute replay, accepted-case replay,
issue closure, consumer/API-ABI/dependency/security/readiness or publishing claim.
