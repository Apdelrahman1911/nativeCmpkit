# [Medium][UI-042] Damped drag animation launches overlapping jobs per update and tracks velocity with wall-clock time

<!-- nativecmpkit-item:audit:UI-042 -->
## Classification
- **Finding:** UI-042
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt:86-140`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt#L86-L140) — `press / release / updateValue / animateToValue / updateVelocity`

## Root cause
Every external value update starts animation jobs and every animated value callback starts another velocity animation. Release jobs delay/wait and are not cancelled on the next press. MutatorMutex in animateToValue does not cover the separate updateValue path or its externally scoped release/press launches. Velocity timestamps use Clock.System rather than a monotonic/frame clock.

## Impact and preconditions
Fast updates/re-presses can accumulate work and let an old release reset a new press. Wall-clock adjustments can distort velocity. Persistent memory leakage or visible jank has not been measured.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- updateVelocity creates animationScope.launch on each animation callback.
- release waits then launches reset animations independently; press has no release-job cancellation.

## Recommended solution
Use structured, single-owner jobs for value/velocity/press state, cancel obsolete release jobs on new interaction and synchronize all mutation paths. Use monotonic pointer/frame timestamps and profile coroutine/allocation counts before optimizing constants.

## Risks and compatibility
Compose Animatable already cancels conflicting animations, which limits some overlap; that does not automatically cancel all sibling/external jobs. Avoid asserting an unbounded leak without measurements.

## Required tests / acceptance criteria
- Rapid press-release-press, high-frequency value updates, tap animation interrupted by drag.
- Coroutine/job counts and frame-time/allocation trace under sustained interaction.
- Clock changes, cancellation/disposal and range changes without pending release waits.

## Dependencies
- UI-031
- UI-032

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
