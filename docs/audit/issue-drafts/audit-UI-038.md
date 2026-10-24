# [Medium][UI-038] Native image conversion leaks CoreGraphics resources on the image-creation failure path

<!-- nativecmpkit-item:audit:UI-038 -->
## Classification
- **Finding:** UI-038
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt:49-67,71-100`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt#L49-L67) — `ImageVector.toImageBitmap / ImageBitmap.toUIImage`

## Root cause
After creating a color space and bitmap context, CGBitmapContextCreateImage(context) ?: return null exits before releasing either resource. Context creation is also not checked before snapshot. Skia Surface/Paint allocations rely on finalization rather than explicit scope cleanup.

## Impact and preconditions
Repeated conversion failures under memory pressure can accumulate native resources, worsening failure. Unvalidated dimensions or allocation errors may throw despite a nullable result type.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- CGBitmapContextCreateImage(context) ?: return null precedes CGContextRelease(context) and CGColorSpaceRelease(colorSpace).

## Recommended solution
Use try/finally or scoped native-resource helpers, check every nullable allocation, release owned objects on all paths and validate raster dimensions before allocation. Explicitly close Skia resources when their ownership permits it.

## Risks and compatibility
The CoreGraphics early-return leak is source-confirmed; no heap measurement or claim that every normal conversion leaks. JNI/Native wrapper finalization and autorelease behavior require platform verification.

## Required tests / acceptance criteria
- Inject color-space/context/image creation failure and assert all owned resources release.
- Zero/negative/truncated/huge vector dimensions and normal repeated conversions.
- Instruments allocation/leak profile and GC stress.

## Dependencies
- UI-037

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
