# nativeCmpkit

An independent **Kotlin Multiplatform native component toolkit**, derived from
[Calf](https://github.com/MohamedRejeb/Calf). Imported Git history, authorship,
branches, tags and an extensive public GitHub metadata snapshot are preserved
here; [unavailable records and archive boundaries](docs/migration/metadata-coverage.md)
are documented explicitly.

**Status: audited migration, not a production-readiness certification.** No
nativeCmpkit packages or releases have been published. Known defects and build /
device-verification limitations are tracked in the [technical audit](docs/audit/README.md)
and [roadmap](docs/roadmap/README.md). Imported `v0.*` tags are historical **Calf**
versions, not nativeCmpkit releases. Repository Actions are disabled outside
supervised read-only verification.

The audit records **164 findings (37 High)**. The [170 verified development issues](docs/migration/issues-verification.json)
include six actionable historical topics; 167 are open and three migration fixes
are closed. These counts describe the audit delivery, not future issue state.

## Library identity and compatibility

- Repository / project: **nativeCmpkit**
- Prospective Maven group: `io.github.apdelrahman1911.nativecmpkit`
- Prospective artifacts: `nativecmpkit-ui`, `nativecmpkit-io`,
  `nativecmpkit-file-picker`, and corresponding module suffixes.
- Development version: `0.1.0-SNAPSHOT` (**unpublished**).
- Public Kotlin packages remain **`com.mohamedrejeb.calf.*`**, including opt-in
  annotations and JNI names. Existing `calf-*` Gradle paths are intentionally
  retained. This avoids gratuitous API/ABI breaks; binary compatibility has not
  been certified. Do not put old and new artifacts with duplicate classes together.

See [installation](docs/installation.md), [coordinate mapping](docs/migration/identity.json),
and the [compatibility decision](docs/decisions/0001-independent-identity.md).

## Components

| Source module(s) | Implementation / qualification |
| --- | --- |
| `calf-core`, `calf-io` | Platform context, files and streaming; target-specific URI / URL / browser Blob semantics |
| `calf-ui` | Adaptive Compose / UIKit widgets, dates, dialogs, sheets, gestures, liquid glass |
| `calf-file-picker`, `calf-file-picker-coil` | Native pick/save dialogs, Rust/JNI desktop bridge, Coil integration |
| `calf-camera-picker`, `calf-share` | Mobile capture, platform-dependent sharing and desktop fallbacks |
| `calf-webview` | Android WebView, iOS WKWebView, desktop JavaFX, browser iframe; not equivalent APIs |
| `calf-permissions` and 11 subprojects | Per-feature Android/iOS permissions; desktop/web stubs are not permission checks |
| `calf-cupertino-icons` | Bundled MIT-licensed Cupertino icon font; distinct from Apple's SF Symbols |
| `calf-navigation`, `calf-geo` | Incomplete experimental implementations, not published by the build |
| `calf-maps`, `calf-media`, `calf-notifications` | Empty / excluded prototypes, **not working features** |

Android, iOS, desktop JVM, JavaScript and Wasm targets are not promises of full
feature parity. Read the [source-evidenced platform matrix](docs/platforms/README.md).

## Build from source

```sh
git clone https://github.com/Apdelrahman1911/nativeCmpkit.git
cd nativeCmpkit
# JDK 17, Android SDK 37, Rust and host native dependencies are required.
./gradlew :calf-io:desktopTest :calf-file-picker:desktopTest
```

The imported toolchain uses Kotlin **2.4.20**, Compose **1.12.0**, AGP **9.4.0**
and Gradle **9.7.1**; library Android minSdk is 23 (sample 24). These are configured
versions, not a claim every target passes. See [verified commands and limitations](docs/testing/README.md)
before building. No build requires the Calf repository to remain online, but
standard public dependency registries are still required for an uncached build.
Do **not** run publication / release / deployment tasks without explicit owner
authorization. Neither publishing credentials nor a Maven namespace claim are
created by this migration.

## Maintainer knowledge base

- [Architecture and execution flows](docs/architecture/README.md)
- [Detailed module reviews](docs/modules/README.md) and [platforms](docs/platforms/README.md)
- [Findings, evidence and review coverage](docs/audit/README.md)
- [Tests and reproduction procedures](docs/testing/README.md)
- [Design decisions](docs/decisions/README.md) and [prioritized roadmap](docs/roadmap/README.md)
- [Migration, Git archive and original GitHub metadata](docs/migration/README.md)
- [Instructions for future agents](AGENTS.md)
- [Final migration / audit report](docs/audit/final-report.md)

Feature usage guides are preserved under `docs/`; their historical examples do
not establish correctness. The source audit takes precedence where they disagree.
Use this repository's [issues](https://github.com/Apdelrahman1911/nativeCmpkit/issues)
for development. No nativeCmpkit demo/documentation site was intentionally
deployed. An [unintended legacy Pages deployment](docs/migration/pages-incident.md)
from the imported historical branch was discovered; branch publishing is disabled,
but removing the existing deployment requires the documented owner follow-up.

## License and attribution

**Copyright 2023 Mohamed Rejeb.** Original copyrights and contributor history
are retained. Migration additions: copyright 2026 nativeCmpkit contributors.
Licensed under [Apache-2.0](LICENSE), with [NOTICE](NOTICE) and
[third-party notices](THIRD_PARTY_NOTICES.md). Thanks to the original Calf authors,
[compose-cupertino](https://github.com/alexzhirkevich/compose-cupertino),
[AndroidLiquidGlass](https://github.com/Kyant0/AndroidLiquidGlass), Jodd and the
Cupertino icon font authors. This project is independently maintained and does
not imply their endorsement. The [unmodified original README](docs/migration/legacy/README.upstream.md)
and all historical documentation remain archived.
