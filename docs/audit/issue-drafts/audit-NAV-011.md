# [Medium][NAV-011] Generated icon/symbol catalogues lack a reproducible generator and Apple availability metadata

<!-- nativecmpkit-item:audit:NAV-011 -->
## Classification
- **Finding:** NAV-011
- **Priority:** Medium
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-cupertino-icons`, `calf-ui`, `sample:common`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-cupertino-icons/src/commonMain/kotlin/com/mohamedrejeb/calf/cupertino/icons/CupertinoIcons.kt:3-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-cupertino-icons/src/commonMain/kotlin/com/mohamedrejeb/calf/cupertino/icons/CupertinoIcons.kt#L3-L12) — `generated catalogue header/object`
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/sf/symbols/SFSymbol.kt:3-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/sf/symbols/SFSymbol.kt#L3-L20) — `generated SF symbol names`
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/CupertinoIconsCatalogData.kt:1-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/CupertinoIconsCatalogData.kt#L1-L30) — `sample catalogue data`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt:36-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt#L36-L40) — `UIKitImage.SystemName resolution`

## Root cause
Generated declarations claim SF/Cupertino coverage but the repository contains no generator/source manifest capable of reproducing names, aliases, categories and version mapping. SF names cover versions1.0-7.0 without per-symbol minimum-OS/variant/fallback metadata.

## Impact and preconditions
Future updates cannot be mechanically reviewed against a canonical source, and newer Apple names may resolve to no system image on older supported OS versions. This is not proof of an unconditional crash: the underlying UIImage lookup is nullable.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Persistent catalogue-result.json:1322 Cupertino declarations,1234 distinct codepoints, all covered by the font;1322 unique sample entries;6984 unique SF identifiers and values.
- The parser validates every declaration, including Kotlin escaped identifiers repeat/case/return; zero unparsed declarations.
- Git history reviewed for PRs510,511,514 does not introduce a generator.

## Recommended solution
Store generator code, pinned permitted input provenance and deterministic outputs; keep Cupertino font and Apple system name catalogues distinct. Add per-symbol availability or documented fallback/feature detection at the UIKit boundary.

## Risks and compatibility
Apple artwork licensing is separate from identifier strings. Font/codepoint validation proves mapping consistency, not glyph meaning, visual layout or OS availability of SF names.

## Required tests / acceptance criteria
- Regenerate all catalogues deterministically with zero unexplained diff.
- Retain checks for unique identifiers, aliases, valid referenced names and cmap coverage.
- Resolve representative/newest SF names on oldest/current supported iOS versions with a deliberate missing-symbol fallback.
- Render glyph snapshots and check icon alignment, tint and accessibility.

## Dependencies
- NAV-009

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/510
- https://github.com/MohamedRejeb/Calf/pull/511
- https://github.com/MohamedRejeb/Calf/pull/514
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
