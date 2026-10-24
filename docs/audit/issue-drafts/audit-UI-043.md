# [Low][UI-043] A delayed Cupertino button release animation can clear the next press highlight

<!-- nativecmpkit-item:audit:UI-043 -->
## Classification
- **Finding:** UI-043
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/button/CupertinoIndication.kt:64-108`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/button/CupertinoIndication.kt#L64-L108) — `CupertinoIndicationNode.onAttach`

## Root cause
Release/cancel handling launches a coroutine that waits until the100ms minimum press display time, then animates alpha back to1. A subsequent press starts a new alpha animation but does not cancel the previously scheduled delayed release.

## Impact and preconditions
Rapid release/re-press followed by a hold can lose the pressed highlight while the button remains pressed.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Release and Cancel each launch delayed alpha.animateTo(1f); Press does not cancel those delayed jobs.

## Recommended solution
Track and cancel the pending release job when a new press begins, or derive the animation from the set of active PressInteraction instances with a single serial state machine.

## Risks and compatibility
The scheduled-job ordering is source-confirmed; visual timing still needs a Compose clock-driven test. Keep the intentional minimum press duration.

## Required tests / acceptance criteria
- Press/release at20ms, re-press before100ms, hold; alpha stays pressed until final release.
- Cancel, multiple pointers and node detach with pending jobs.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
