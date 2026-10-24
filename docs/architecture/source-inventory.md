# Reproducible baseline inventory

## Reproduce and verify

From the repository root, using Python 3.11+ and Git:

```sh
python3 scripts/audit/source_inventory.py
python3 scripts/audit/source_inventory.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/audit -p 'test_source_inventory.py' -v
```

The default ref is the immutable imported upstream commit
`af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. The script uses `git ls-tree` and one
`git cat-file --batch` read, so concurrent migration edits, build outputs and
untracked files cannot change this baseline inventory. It does not build,
download dependencies, write outside its chosen output or contact upstream.
Use `--ref <commit> --output <separate-file>` to compare a future committed tree;
do not overwrite the baseline when assessing a fix.

The audit run regenerated the inventory twice, checked byte-identical output
with `--check`, and passed nine focused regression tests: nested comment/string
masking and offset preservation, class literals, a generic extension function,
an extension property, an actual typealias, an unnamed companion object,
build/native ownership, and Rust/Xcode file classification. Those checks verify
the inventory mechanism, not application behavior.

## Contents

[`docs/audit/source-inventory.json`](../audit/source-inventory.json) contains:

- Every tracked file's path, Git blob, SHA-256, byte size, mode and physical line
  count (binary files retain hashes/size but no guessed line count).
- Owning project, whether it is included in Gradle, source set, inferred target
  consumers, source language, generated-marker and test flags.
- Kotlin package/imports and lexical named-declaration candidates, with exact
  declaration lines and modifiers. Kotlin scripts and Rust functions/structures
  are included. Swift is counted but not parsed into Kotlin declarations.
- Build-file-declared project/catalog/literal dependencies and publication
  plugin presence. Version-catalog versions/artifact identifiers are retained.
- Same-module, same-name candidates for all 96 explicit `expect` declarations.
  All have at least one name candidate; that is **not** a compiler proof that
  every target has a compatible actual.
- Audit-area assignment for navigation to the detailed reports. Assignment is
  not a per-file “review passed” stamp.

## Baseline counts and interpretation

| Metric | Count |
|---|---:|
| Tracked files, including assets/docs/configuration | 607 |
| Kotlin source files | 437 |
| Kotlin build/convention scripts | 38 |
| Rust source files | 2 |
| Swift source files | 2 |
| Above source files combined | 479 |
| Kotlin/KTS/Rust physical lines, including blank/comment/test/generated lines | 43,653 |
| Above plus Swift physical lines | 43,708 |
| Explicitly generated Kotlin source files | 3 |
| Generated Kotlin source physical lines | 9,693 |
| Test-source files | 15 |
| Files declaring `@Test` / total lexical `@Test` annotations | 13 / 86 |
| Lexical named-declaration candidates, including locals and constant tables | 12,069 |
| Explicit lexical `expect` candidates | 96 |

One additional file, Gradle's daemon JVM properties, carries a generated marker
but is not counted as source. The Objective-C KVO `.def`, XML manifests,
Info.plist, workflows, Cargo TOML and MIME resources are all indexed even though
they are not counted in the language-line totals above. A count of Kotlin-only
`wc -l` results is not comparable to this count of physical `splitlines()` over
all Git blobs, especially for files without a terminating newline.

## Review assignment

| Owner | Assigned implementation areas |
|---|---|
| `audit_ui` | `calf-ui` controls/managers/state/helpers; SF constants also cross-reviewed by icons reviewer |
| `audit_io_picker` | `calf-io`, `calf-file-picker`, `calf-file-picker-coil`, including native Rust and MIME database |
| `audit_permissions_geo` | Permission core, all ten features, compatibility aggregate, geo |
| `audit_native_features` | WebView/cookies/KVO, camera, share/Rust, maps/media/notification stubs |
| `audit_navigation_core_icons` | Core, navigation, symbols/font, runtime sample code |
| `audit_build` | All Gradle/Cargo manifests, convention plugins, workflows, toolchain/dependency/publishing behavior |
| `audit_history_architecture` | Cross-module architecture, baseline index, platform map, history and metadata-derived decisions |

Area reports can cross-review files outside these assignments; the index picks
one primary owner per file to avoid falsely counting repeated review as extra
coverage. Cross-file call flows and tests remain in the prose reports.

## Known limitations (do not promote this into a compiler report)

The extractor masks comments and literals, then recognizes named Kotlin/Rust
declaration tokens. It does not type-check, resolve overloads, infer visibility,
parse anonymous declarations, enumerate implicit accessors, or analyze execution
paths. Kotlin string interpolation code is masked with its string. Locals and
primary-constructor properties count as declarations, so 12,069 is not an API
surface estimate. Generated constant tables dominate the property count.

The target mapping is inferred from the source hierarchy, not an evaluated
Gradle model; test source sets may be transformed by the plugin, and excluded
projects can still contain files named `iosMain`. The Xcode project is indexed
separately and is not marked an included Gradle project. A compatible source
declaration is not evidence that the OS capability exists, the native binary is
available, or the code was exercised on hardware. See the platform and testing
reports for those distinctions.
