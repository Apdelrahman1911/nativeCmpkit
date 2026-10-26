# Reproducible icon catalogue inputs

`manifest.json` pins byte hashes and explains provenance. The JSON records were
losslessly extracted from Calf commit `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`:

- `cupertino.json`: all 1,322 public identifiers, 1,234 unique codepoints and every
  original sample name/category/order. The actual bundled Flutter CupertinoIcons
  1.08 font is checked for nonzero Unicode glyph mappings. The font is MIT, not
  Apple's proprietary SF Symbols font; see `licenses/cupertino-icons-provenance.json`.
- `sf-symbols.json`: all 6,984 public identifiers and Apple system-name strings.
  **Every `introduced_ios: null` means unknown, not universally available.**
  This is not an Apple availability database. `UIImage.systemImageNamed` must be
  allowed to return nil and callers must choose a suitable fallback if needed.

This makes the current catalogue reproducible independently of upstream, but does
not reconstruct the unidentified original generators or certify their input dates.
No font or platform symbols are downloaded by the generation process.

```sh
python3 scripts/development/generate_icon_catalogues.py --check
python3 -m unittest discover -s scripts/development -p 'test_icon_catalogues.py'
# Only when intentionally regenerating the three output files:
python3 scripts/development/generate_icon_catalogues.py --write
```

A legitimate update changes the relevant JSON, records its new source/provenance,
updates that input's SHA256 in `manifest.json`, then regenerates and reviews the
public constant diff. A font update additionally requires license/provenance and
rendering review. Do not update a hash just to bypass a mismatch. The validator
refuses non-null OS availability until an authoritative provenance schema and
verification procedure are added; guessed minimum versions are worse than unknowns.

Generated paths are fixed by the script: `CupertinoIcons.kt`,
`CupertinoIconsCatalogData.kt`, and `SFSymbol.kt`. Regeneration does not rename public
packages, resources, constants or sample entries. Font glyph mapping validation is
not a rendering, VoiceOver/TalkBack or native OS-availability test.
