# [Medium][NAV-010] CupertinoIcon leaves the private-use glyph Text semantics exposed

<!-- nativecmpkit-item:audit:NAV-010 -->
## Classification
- **Finding:** NAV-010
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-cupertino-icons`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-cupertino-icons/src/commonMain/kotlin/com/mohamedrejeb/calf/cupertino/icons/CupertinoIcon.kt:43-83`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-cupertino-icons/src/commonMain/kotlin/com/mohamedrejeb/calf/cupertino/icons/CupertinoIcon.kt#L43-L83) — `CupertinoIcon semantics and Text`

## Root cause
The icon is a Material Text displaying a private-use character. A null contentDescription adds no semantics modifier, leaving the Text node; a non-null description adds parent image semantics without clearing the child text semantics.

## Impact and preconditions
Decorative icons are not reliably excluded from accessibility output, and labeled icons can retain a meaningless glyph-text node. The source-level semantics issue is confirmed; exact VoiceOver/TalkBack utterances and merged-node behavior were not executed here.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Lines55-62 only set contentDescription/Role.Image when non-null.
- The child Text at lines70-83 always uses iconChar; no clearAndSetSemantics or equivalent text suppression exists.
- All bundled codepoints are BMP and map to nonzero glyphs, so malformed catalogue codepoints are not the cause.

## Recommended solution
Implement explicit decorative-versus-labeled icon semantics, suppressing the glyph Text semantics while retaining one meaningful image description where provided. Follow Compose semantics guidance and test both merged/unmerged trees and real assistive technology.

## Risks and compatibility
Unconditionally clearing outer semantics could erase a caller's click action or label. Font glyph presence tests do not establish accessibility correctness.

## Required tests / acceptance criteria
- A null-description icon contributes no readable PUA text semantics.
- A labeled icon contributes one image label and no additional glyph announcement.
- Icons inside buttons preserve the button action/label in merged and unmerged trees.
- Run TalkBack, VoiceOver and desktop/browser accessibility checks at different font scales.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/511
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
