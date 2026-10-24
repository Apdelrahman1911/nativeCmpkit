# [Medium][UI-036] ImageVector-to-UIImage conversion discards vector paints, transforms and clipping

<!-- nativecmpkit-item:audit:UI-036 -->
## Classification
- **Finding:** UI-036
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt:43-68,103-118`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt#L43-L68) — `ImageVector.toImageBitmap / toPath / traverseNodes`
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/uikit/UIKitImage.kt:27-39`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/uikit/UIKitImage.kt#L27-L39) — `UIKitImage.Vector`

## Root cause
The converter combines pathData from every VectorPath into one Compose Path and paints it solid black. It does not apply VectorGroup transforms/clips or per-path fill/stroke/alpha/fill rule/trim/tint/auto-mirroring.

## Impact and preconditions
Native bar/menu/FAB icons derived from stroked, transformed or multicolor ImageVectors are rendered incorrectly or disappear. Density scaling fixes sharpness but not vector fidelity.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- traverseNodes recurses groups but only adds child pathData; Paint is black and fill-only.
- Upstream#520/9a47e53 repaired density conversion, not these lost vector properties.

## Recommended solution
Use Compose vector painter rendering or a faithful renderer that preserves group and path properties; define native templating/tint policy separately. Cache rasterizations with correct density/theme/RTL identity after correctness is proven.

## Risks and compatibility
Simple filled monochrome vectors often work and are not evidence of full support. Avoid regressions to density scaling already fixed upstream.

## Required tests / acceptance criteria
- Nested translated/scaled/rotated groups, clips, even-odd fill, stroke-only paths, alpha and multiple colors.
- RTL autoMirror, tint/template rendering,2x/3x density and non-square viewport.
- Compare source ImageVector and resulting UIImage pixel snapshots on Apple.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/520
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
