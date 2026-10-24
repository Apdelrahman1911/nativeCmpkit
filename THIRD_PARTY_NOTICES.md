# Third-party notices

nativeCmpkit retains Calf's Apache-2.0 source license and attribution; see
`LICENSE` and `NOTICE`. Third-party components keep their own licenses. This
document is not a certification of every transitive dependency's licensing.

## Embedded Jodd utilities and MIME database

The `jodd` sources/resources in `calf-file-picker` retain their complete
upstream two-clause BSD license headers:

- `src/desktopMain/kotlin/jodd/io/IOUtil.kt`
- `src/desktopMain/kotlin/jodd/net/MimeTypes.kt`
- `src/desktopMain/kotlin/jodd/util/Wildcard.kt`
- `src/desktopMain/resources/jodd/net/MimeTypes.properties`
- `src/desktopTest/kotlin/jodd/net/MimeTypesTest.kt`

Copyright (c) 2003-present, Jodd Team (http://jodd.org).
The five existing headers were compared and have identical license text
(after removing Kotlin/properties comment prefixes). A convenient full copy
is in [licenses/jodd-BSD-2-Clause.txt](licenses/jodd-BSD-2-Clause.txt).
This migration preserves the headers; it does **not** report them as missing.
Binary redistribution requires reproduction of the copyright, conditions,
and disclaimer in the accompanying documentation/materials. Verify that
artifact notice packaging includes them before future publication.

## Cupertino Icons font

`calf-cupertino-icons/src/commonMain/composeResources/font/sf_symbols.ttf` is
the **CupertinoIcons Version 1.08** font, not Apple's proprietary SF Symbols
font. On 2026-10-24 its 257,628 bytes were verified byte-for-byte against
Flutter's `cupertino_icons` package at commit
`23a05b6ad5d55bc0df5b9340623570b69064edf1`:

- [Pinned font source](https://github.com/flutter/packages/blob/23a05b6ad5d55bc0df5b9340623570b69064edf1/third_party/packages/cupertino_icons/assets/CupertinoIcons.ttf)
- [Pinned MIT license](https://github.com/flutter/packages/blob/23a05b6ad5d55bc0df5b9340623570b69064edf1/third_party/packages/cupertino_icons/LICENSE)
- SHA-256: `67c44fe9183b002e79dde7f6977e2988661c9a3e4a3c5fce968787efdbed823c`
- Copyright (c) 2016 Vladimir Kharlampidi
- Local, verbatim license: [licenses/cupertino-icons-MIT.txt](licenses/cupertino-icons-MIT.txt)
- Machine-readable verification: [licenses/cupertino-icons-provenance.json](licenses/cupertino-icons-provenance.json)

The MIT permission and copyright notice must accompany distributed copies
or substantial portions. Preserve the local license when packaging the font
in Android/JVM/Native/Web artifacts. **The migration adds source-tree notices;
packaged-artifact notice inclusion remains a pre-publication verification
gate.** No artifact publication was authorized or performed as part of this
notice addition.

## Apple SF Symbol name constants

`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/sf/symbols/SFSymbol.kt`
contains string identifiers passed to Apple's system image APIs; it does
not contain the Apple SF Symbols font or image outlines. The identifier
catalogue and Cupertino Icons font are different components. System symbol
availability and permitted uses depend on Apple's platform and applicable
terms; the Apache-2.0 project license does not grant rights to Apple's system
artwork. The catalogue's generation source/version mapping has not been
independently reconstructed; see `docs/audit/navigation-core-icons-sample.md`.
