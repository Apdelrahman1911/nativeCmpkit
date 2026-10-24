# [Low][NATIVE-035] Maps, media and notification scaffolds must not be represented as implemented features

<!-- nativecmpkit-item:audit:NATIVE-035 -->
## Classification
- **Finding:** NATIVE-035
- **Priority:** Low
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-maps`, `calf-media`, `calf-notifications`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-maps/build.gradle.kts:1-13`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-maps/build.gradle.kts#L1-L13) — `empty maps module`
- [`calf-media/build.gradle.kts:1-47`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-media/build.gradle.kts#L1-L47) — `excluded stale build script`
- [`calf-notifications/build.gradle.kts:1-47`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-notifications/build.gradle.kts#L1-L47) — `excluded stale build script`
- [`calf-notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/notifications/Main.kt:1-26`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/notifications/Main.kt#L1-L26) — `uncompilable notification experiment`
- [`settings.gradle.kts:28-61`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/settings.gradle.kts#L28-L61) — `included project list`

## Root cause
Maps is included but contains no source/API. Media has only an excluded old build script. Notifications is excluded and contains a top-level experiment with missing imports/undefined scope; both excluded scripts reference a removed androidLibrary plugin alias and old Android DSL.

## Impact and preconditions
Directory presence or stale roadmap checkboxes can imply usable functionality that does not exist. Enabling excluded modules without review will not simply produce functioning published libraries. Notification permissions are implemented in a different module and should not be confused with scheduling/delivery.

## Supporting evidence
- 47-file native feature baseline inventory includes one build-only maps file and no media source.
- Notification Main.kt references scope, Dispatchers and UN symbols without definitions/imports; settings does not include media/notifications.

## Recommended solution
Mark availability explicitly in docs/artifact matrices; preserve these historical stubs as such. Open scoped design/discovery work for maps, media and notification delivery with target/provider/licensing/privacy decisions before implementation.

## Risks and compatibility
No requirement to implement these major new subsystems during the audit. Keep imported history; removal/reorganization needs a maintainer decision and should not turn old scaffolds into silently published artifacts.

## Required tests / acceptance criteria
- Source/module inventory verifies empty/excluded status and published artifacts exclude incomplete APIs.
- Future enabling requires fresh supported Gradle configuration, actual API contract, platform privacy/provider setup and device tests.
- Roadmap links maps27 and media245 without claiming they are fixed.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/27
- https://github.com/MohamedRejeb/Calf/issues/245
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
