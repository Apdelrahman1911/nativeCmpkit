# [High][NAV-009] Embedded Cupertino font requires MIT notices in distributed artifacts; baseline notice gap partially repaired

<!-- nativecmpkit-item:audit:NAV-009 -->
## Classification
- **Finding:** NAV-009
- **Priority:** High
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-cupertino-icons`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-cupertino-icons/src/commonMain/composeResources/font/sf_symbols.ttf:binary (entire font file)`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-cupertino-icons/src/commonMain/composeResources/font/sf_symbols.ttf) — `CupertinoIcons Version 1.08 font`
- [`docs/sf-symbols.md:64-68`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/docs/sf-symbols.md#L64-L68) — `baseline Cupertino font license claim`
- [`calf-cupertino-icons/build.gradle.kts:1-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-cupertino-icons/build.gradle.kts#L1-L12) — `resource publication configuration`

## Root cause
The baseline bundles the CupertinoIcons font but includes no copy of its MIT copyright/permission notice. Calling it MIT in documentation is not the notice itself. The font filename also misleadingly suggests Apple's SF Symbols font.

## Impact and preconditions
Redistribution without the required notice risks failing the font's MIT conditions. The bytes are the open-source Flutter Cupertino font, not proof of bundled proprietary Apple artwork. Migration source-tree notices now repair the known source archive gap; packaged artifacts are not yet verified.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Font bytes SHA256=67c44fe9183b002e79dde7f6977e2988661c9a3e4a3c5fce968787efdbed823c match Flutter/packages commit23a05b6ad5d55bc0df5b9340623570b69064edf1 byte-for-byte.
- Pinned MIT license copyright is (c)2016 Vladimir Kharlampidi; license SHA256=310d6ab6483280280c9db122bded0a63c09558bc5743720f61dbcbb494db370a.
- See licenses/cupertino-icons-provenance.json and THIRD_PARTY_NOTICES.md; no publishing command was run for this check.

## Recommended solution
Retain THIRD_PARTY_NOTICES.md and licenses/cupertino-icons-MIT.txt plus the pinned provenance JSON. Rename/descriptively document the font without breaking the generated resource API. Verify license inclusion in every actual published package, framework/web distribution and sample binary before authorization to publish.

## Risks and compatibility
Do not claim a legal certification or assume an upstream source-tree notice automatically enters AAR/JAR/KLIB/web outputs. Root-source remediation is already recorded and should not be opened as an entirely unfixed source notice issue.

## Required tests / acceptance criteria
- Verify the local font SHA256 equals the pinned Flutter font; the existing catalogue script checks baseline bytes.
- Inspect future AAR/JAR/KLIB/native/web artifact contents or accompanying distributions for the complete MIT copyright and permission text.
- Verify documentation clearly distinguishes Cupertino glyph assets from Apple system-symbol names.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/511
- https://github.com/flutter/packages/blob/23a05b6ad5d55bc0df5b9340623570b69064edf1/third_party/packages/cupertino_icons/LICENSE
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
