# Shared native slider lifecycle batch — UI-027/#34 and UI-034/#137

Both issues are grouped around the existing shared production `SliderInput` /
`SliderLayout` repair. No public API or architectural refactor. Six new actual
Liquid/Cupertino-renderer methods share one application build and cover:

- Initially disabled → enabled → disabled idle, then enable/disable during an
  actual publishing drag, live current change/finish callbacks, stale up and
  fresh re-enabled input. Exact old-owner cancellation, not user completion.
- **Individually** changing measured width, density/thumb geometry, RTL, range,
  steps and interaction source during a publishing drag. Each old start pairs
  with exactly one cancel/no stop; actual dragged-state observers clear; stale
  move/up cannot write; fresh input and semantic steps use the current contract.
- Tap → immediate drag → opposite taps, actual scene cancellation, no delayed
  caller-state writer after512ms of the real frame clock; discrete values,
  cancellation/dragged-state balance and subsequent semantic progress.

`ios-slider-lifecycle` selects only these six new methods. Accepted numeric,
controls, genuine host, date/state/time or other-platform suites are not replayed.
This is not a widget replacement or sample-application proxy. Direct Cupertino
on the selected host does **not** certify adaptive pre-26 OS selection, VoiceOver,
physical input, minimum-platform, graphics/profile or complete ABI/consumer gates.
UI-028 and the broader accessibility/branch/performance findings remain separate.

[Local review](local001/review.json): five new selection/receipt guards pass;
changed native test KLIB exit0/36.01s with865 source/recipe inputs held before/
after. **Zero local native executions**. Guards use disclosed synthetic receipt
fixtures, not actual UI functionality. Native immutable execution and both
original-criteria reviews are pending; **#34 and #137 remain open**.

No packages, releases, deployments, Pages, main/history or attribution changes.
