# [Medium][UI-037] Bitmap-to-UIImage bridge has unverified byte-order, premultiplication and buffer-lifetime assumptions

<!-- nativecmpkit-item:audit:UI-037 -->
## Classification
- **Finding:** UI-037
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt:71-100`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt#L71-L100) — `ImageBitmap.toUIImage`

## Root cause
PixelMap Color.toArgb values are copied to UIntArray and handed as raw bytes to a context configured as kCGImageAlphaPremultipliedLast without an explicit matching byte-order/premultiplication conversion. data.refTo(0) is scoped to the create call even though the context uses external pixel storage until snapshotting.

## Impact and preconditions
Little-endian ARGB words occupy B,G,R,A bytes, so the requested CoreGraphics interpretation may swap channels and blend translucent pixels incorrectly. Pointer-lifetime assumptions deserve a pinned ownership check; actual use-after-free is not established.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- data is pixelMap.buffer.toUIntArray() and bitmapInfo is kCGImageAlphaPremultipliedLast.
- The buffer address is supplied via data.refTo(0), with no enclosing usePinned region.

## Recommended solution
Specify one exact pixel format, explicitly convert/premultiply as needed, use matching CoreGraphics flags, and keep the buffer pinned for context creation through snapshot/release. Validate the result rather than assuming flag names match Kotlin integer layout.

## Risks and compatibility
This is a portability/native-interop risk, not a confirmed memory-safety vulnerability. Kotlin/Native GC behavior and CoreGraphics byte-order semantics must be verified on the real target.

## Required tests / acceptance criteria
- Known1x1 red/blue/green/transparent/half-alpha pixels roundtrip to UIImage and composite over black/white.
- Stress GC while converting, larger buffers, allocation failures and color-space assumptions.
- Apple Address Sanitizer/native diagnostics where supported.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
