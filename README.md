# NativeCmpKit

An independent **Kotlin Multiplatform native component toolkit**, derived from
[Calf](https://github.com/MohamedRejeb/Calf). Imported Git history, authorship,
branches, tags and an extensive public GitHub metadata snapshot are preserved
here; [unavailable records and archive boundaries](docs/migration/metadata-coverage.md)
are documented explicitly.

**Status: audited migration, not a production-readiness certification.** No
NativeCmpKit packages or releases have been published. Known defects and build /
device-verification limitations are tracked in the [technical audit](docs/audit/README.md)
and [roadmap](docs/roadmap/README.md). Imported `v0.*` tags are historical **Calf**
versions, not NativeCmpKit releases. The owner's 2026-10-26
[verification policy](docs/development/containment.md) permits enabled Actions,
all actions/reusable workflows and no mandatory SHA pinning. Verification uses
minimum permissions; publication and deployment remain gated.

Current contained work: [verified iOS memory-safety and Coil lifecycle fix](docs/development/native-io-verification.md).
**17 issues closed** as observed on2026-10-27, including [#4](https://github.com/Apdelrahman1911/nativeCmpkit/issues/4)
after reviewed47/47 native simulator tests and [#5's Android saver fix](docs/development/android-saver-verification.md).
This is a current development count;
the migration counts below are historical snapshots.
Specific verified fixes are not whole-library, native/device or release certification.

The audit records **164 findings (37 High)**. The [170 verified audit/history issues](docs/migration/issues-verification.json)
include six actionable historical topics; 167 are open and three migration fixes
are closed. A separate [Pages cleanup issue #171](https://github.com/Apdelrahman1911/nativeCmpkit/issues/171)
brings the delivery snapshot to **171 issues (168 open, three closed)**; it is not
an additional baseline library finding. Counts are observations, not future issue state.

[Verified CI](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40114966617)
passed **300 target/host test executions (86 distinct original functions)** across
desktop, Android-host, JS, Wasm and iOS simulator. Android/browser sample builds and
simulator framework linking also succeeded. These are not physical-device,
native-UI or ABI certifications; see the [execution ledger](docs/testing/README.md).

## Library identity and compatibility

- Library / root project: **NativeCmpKit** (owner spelling updated 2026-10-27).
- Existing repository URL: `Apdelrahman1911/nativeCmpkit`; no new repository or history rewrite.
- Prospective Maven group: `io.github.apdelrahman1911.nativecmpkit`
- Prospective artifacts: `nativecmpkit-ui`, `nativecmpkit-io`,
  `nativecmpkit-file-picker`, and corresponding module suffixes.
- Development version: `0.1.0-SNAPSHOT` (**unpublished**).
- Public Kotlin packages remain **`com.mohamedrejeb.calf.*`**, including opt-in
  annotations and JNI names. Existing `calf-*` Gradle paths are intentionally
  retained. This avoids gratuitous API/ABI breaks; binary compatibility has not
  been certified. Do not put old and new artifacts with duplicate classes together.

Only current display/root/POM names change; lowercase coordinates, public packages,
native/framework names and existing Gradle property keys remain compatible.
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
# JDK 17, SDK package platforms;android-37.0, Rust and host dependencies.
# Linux picker: cargo on PATH, pkg-config and libwayland-dev.
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
for development. No NativeCmpKit demo/documentation site was intentionally
deployed. An [unintended legacy Pages deployment](docs/migration/pages-incident.md)
from the imported historical branch was discovered. The owner completed Unpublish;
the [verified closure of #171](docs/development/evidence/pages-unpublishing-closure.json)
preserves that history. Pages redeployment remains prohibited.

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
