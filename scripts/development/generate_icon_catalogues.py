#!/usr/bin/env python3
"""Reproduce current Kotlin catalogues from pinned, reviewed source snapshots.

Pure standard library; no network, Apple font extraction, or invented OS metadata.
Default/--check compares bytes without writing. --write rewrites only three named
outputs after validating hashes, identifiers, assignments and actual font glyphs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
INPUTS = Path("tools/icon-catalogues")
CUPERTINO = Path("calf-cupertino-icons/src/commonMain/kotlin/com/mohamedrejeb/calf/cupertino/icons/CupertinoIcons.kt")
SAMPLE = Path("sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/CupertinoIconsCatalogData.kt")
SF = Path("calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/sf/symbols/SFSymbol.kt")
IDENTIFIER = re.compile(r"(?:[A-Za-z_]\w*|`[A-Za-z_]\w*`)", re.ASCII)
# Preserve the reviewed historical notice; regeneration must not replace its date.
MODIFICATION_NOTICE = (
    "// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.\n"
)


def unicode_glyphs(data: bytes) -> set[int]:
    """Inspect the current font's Unicode cmap, never Mac Roman tables."""
    def u16(offset):
        return struct.unpack_from(">H", data, offset)[0]
    tables = {struct.unpack_from(">4sIII", data, 12 + 16 * i)[0]:
              struct.unpack_from(">4sIII", data, 12 + 16 * i)[2:]
              for i in range(u16(4))}
    start, _ = tables[b"cmap"]
    mappings = set()
    for i in range(u16(start + 2)):
        platform, _, offset = struct.unpack_from(">HHI", data, start + 4 + 8 * i)
        if platform not in (0, 3):
            continue
        offset += start
        fmt = u16(offset)
        if fmt == 4:
            count = u16(offset + 6) // 2
            endoff = offset + 14
            startoff = endoff + count * 2 + 2
            deltaoff = startoff + count * 2
            rangeoff = deltaoff + count * 2
            for j in range(count):
                end, begin = u16(endoff + 2 * j), u16(startoff + 2 * j)
                delta = struct.unpack_from(">h", data, deltaoff + 2 * j)[0]
                roff = u16(rangeoff + 2 * j)
                for code in range(begin, min(end, 0xfffe) + 1):
                    glyph = (code + delta) & 0xffff if not roff else u16(rangeoff + 2 * j + roff + 2 * (code - begin))
                    if roff and glyph:
                        glyph = (glyph + delta) & 0xffff
                    if glyph:
                        mappings.add(code)
        elif fmt == 6:
            first, count = u16(offset + 6), u16(offset + 8)
            mappings.update(first + j for j in range(count) if u16(offset + 10 + 2 * j))
        elif fmt == 12:
            groups = struct.unpack_from(">I", data, offset + 12)[0]
            for j in range(groups):
                first, last, glyph = struct.unpack_from(">III", data, offset + 16 + 12 * j)
                if last > 0x10ffff or last < first:
                    raise ValueError("Invalid Unicode cmap range")
                mappings.update(code for code in range(first, last + 1) if glyph + code - first)
        else:
            raise ValueError(f"Unsupported Unicode cmap format {fmt}; review before adding a new font")
    return mappings


def validate_records(cupertino: list[dict], symbols: list[dict], glyphs: set[int]) -> None:
    for entries in (cupertino, symbols):
        identifiers = [entry["identifier"] for entry in entries]
        if len(identifiers) != len(set(identifiers)) or not all(IDENTIFIER.fullmatch(v) for v in identifiers):
            raise ValueError("Duplicate or invalid Kotlin identifier")
    if len({entry["catalogue_name"] for entry in cupertino}) != len(cupertino):
        raise ValueError("Duplicate Cupertino catalogue name")
    if sorted(entry["catalogue_index"] for entry in cupertino) != list(range(len(cupertino))):
        raise ValueError("Catalogue ordering must be a complete permutation")
    for entry in cupertino:
        if entry["codepoint"] not in glyphs or not 0 <= entry["codepoint"] <= 0xffff:
            raise ValueError(f"Missing/BMP-incompatible font glyph: {entry['identifier']}")
        if not re.fullmatch(r"[a-z0-9_]+", entry["catalogue_name"]):
            raise ValueError("Unexpected Cupertino display name")
        if not re.fullmatch(r"[A-Za-z ]+", entry["category"]):
            raise ValueError("Unexpected Cupertino category")
    names = [entry["system_name"] for entry in symbols]
    if len(names) != len(set(names)) or not all(re.fullmatch(r"[a-zA-Z0-9_.]+", n) for n in names):
        raise ValueError("Duplicate or invalid SF system name")
    for entry in symbols:
        # No authoritative per-symbol minimum versions have been obtained. Do not
        # let guesses become generated support promises without a schema review.
        if entry["introduced_ios"] is not None:
            raise ValueError("OS availability requires authoritative provenance, currently unknown")


def load_inputs(root: Path = ROOT) -> tuple[dict, list[dict], list[dict]]:
    manifest = json.loads((root / INPUTS / "manifest.json").read_text())
    if manifest["schema"] != 1:
        raise ValueError("Unsupported catalogue manifest")
    data = {}
    for name in ("cupertino.json", "sf-symbols.json"):
        raw = (root / INPUTS / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["inputs"][name]:
            raise ValueError(f"Input hash mismatch: {name}")
        data[name] = json.loads(raw)
    font = (root / manifest["font"]["path"]).read_bytes()
    if hashlib.sha256(font).hexdigest() != manifest["font"]["sha256"]:
        raise ValueError("Font hash mismatch; update provenance before changing the font")
    validate_records(data["cupertino.json"], data["sf-symbols.json"], unicode_glyphs(font))
    return manifest, data["cupertino.json"], data["sf-symbols.json"]


def render(cupertino: list[dict], symbols: list[dict]) -> dict[Path, str]:
    icons = '''@file:Suppress("unused", "MemberVisibilityCanBePrivate")

package com.mohamedrejeb.calf.cupertino.icons

/**
 * Codepoints for the bundled MIT-licensed Flutter CupertinoIcons font (not Apple SF Symbols).
 *
 * Generated by scripts/development/generate_icon_catalogues.py from the pinned
 * tools/icon-catalogues manifest. Do not edit manually. See THIRD_PARTY_NOTICES.md.
 */
object CupertinoIcons {
'''
    icons += "".join(f"    const val {e['identifier']}: Int = 0x{e['codepoint']:04X}\n" for e in cupertino)
    icons += "}\n"
    sample = '''@file:Suppress("unused")

package com.mohamedrejeb.calf.sample.screens

import com.mohamedrejeb.calf.cupertino.icons.CupertinoIcons

internal data class IconEntry(
    val name: String,
    val codepoint: Int,
    val category: String,
)

/** Generated from tools/icon-catalogues by generate_icon_catalogues.py; do not edit manually. */
internal val AllCupertinoIcons: List<IconEntry> = listOf(
'''
    sample += "".join(f'    IconEntry("{e["catalogue_name"]}", CupertinoIcons.{e["identifier"]}, "{e["category"]}"),\n'
                      for e in sorted(cupertino, key=lambda e: e["catalogue_index"]))
    sample += ")\n"
    # The catalogue screen consumes this original internal declaration too.
    # Derive it from the same pinned entries rather than silently dropping it
    # or maintaining a second, potentially stale list in the screen.
    sample += "\ninternal val IconCategories: List<String> = listOf(\n"
    sample += "".join(f'    "{category}",\n' for category in sorted({e["category"] for e in cupertino}))
    sample += ")\n"
    sf = '''@file:Suppress("unused", "MemberVisibilityCanBePrivate")

package com.mohamedrejeb.calf.sf.symbols

/**
 * Type-safe names accepted by UIImage.systemImageNamed on supporting iOS versions.
 * Presence here is NOT an OS/device availability guarantee: per-symbol minimum OS
 * versions have not been authoritatively verified. Handle unavailable UIImage results.
 *
 * Generated by scripts/development/generate_icon_catalogues.py from the imported
 * source-name snapshot in tools/icon-catalogues. Original generator/source-version
 * provenance remains incomplete; do not invent availability annotations.
 *
 * These system names are separate from the bundled Flutter CupertinoIcons font.
 */
object SFSymbol {
'''
    sf += "".join(f'    const val {e["identifier"]} = "{e["system_name"]}"\n' for e in symbols)
    sf += "}\n"
    return {path: MODIFICATION_NOTICE + text
            for path, text in ((CUPERTINO, icons), (SAMPLE, sample), (SF, sf))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="compare generated bytes (default)")
    mode.add_argument("--write", action="store_true", help="write only the three fixed generated outputs")
    args = parser.parse_args()
    manifest, cupertino, symbols = load_inputs()
    outputs = render(cupertino, symbols)
    mismatch = []
    for path, contents in outputs.items():
        encoded = contents.encode()
        if args.write:
            (ROOT / path).write_bytes(encoded)
        elif (ROOT / path).read_bytes() != encoded:
            mismatch.append(str(path))
    print(json.dumps({"mode": "write" if args.write else "check", "cupertino_constants": len(cupertino),
                      "cupertino_codepoints": len({e['codepoint'] for e in cupertino}),
                      "sf_names": len(symbols), "font_sha256": manifest["font"]["sha256"],
                      "unknown_sf_availability": sum(e["introduced_ios"] is None for e in symbols),
                      "mismatched_outputs": mismatch}, indent=2))
    return bool(mismatch)


if __name__ == "__main__":
    raise SystemExit(main())
