# [Low][UI-044] Cupertino activity indicator ignores input alpha and draws the first spoke twice

<!-- nativecmpkit-item:audit:UI-044 -->
## Classification
- **Finding:** UI-044
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/cupertino/CupertinoCircularProgressIndicator.kt:77-100`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/cupertino/CupertinoCircularProgressIndicator.kt#L77-L100) — `CupertinoActivityIndicator drawBehind`

## Root cause
The drawing loop includes both0 and360 degrees, generating coincident first/last spokes. It uses color.copy(alpha=computedAlpha) rather than multiplying the incoming color alpha.

## Impact and preconditions
A transparent supplied color can produce a visible spinner; semi-transparent colors become too opaque and the coincident spoke is blended twice.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- for(i in0..360 step45) includes nine entries.
- Alpha assignment replaces, rather than combines with, the source color alpha.

## Recommended solution
Use eight distinct angles and multiply the per-spoke alpha by the caller color alpha. Preserve progress semantics and animation timing.

## Risks and compatibility
This is rendering correctness/polish, not a performance bottleneck or native UIActivityIndicator defect; the implementation is Compose.

## Required tests / acceptance criteria
- Transparent and half-alpha colors; pixel snapshots of the eight unique spoke positions.
- One animation cycle at fixed times and semantics retained.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
