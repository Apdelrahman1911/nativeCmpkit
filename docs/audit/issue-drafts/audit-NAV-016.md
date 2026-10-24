# [Low][NAV-016] Sample includes an unused second navigation library with an unnecessary compatibility burden

<!-- nativecmpkit-item:audit:NAV-016 -->
## Classification
- **Finding:** NAV-016
- **Priority:** Low
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `sample:common`, `sample:android`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`sample/common/build.gradle.kts:26-36`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/build.gradle.kts#L26-L36) — `sample navigation dependencies`
- [`sample/android/build.gradle.kts:12-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/android/build.gradle.kts#L12-L22) — `sample SDK configuration`
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/App.kt:11-21`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/App.kt#L11-L21) — `Adaptive controller/graph wiring`

## Root cause
The sample depends on libs.jetbrains.navigation.compose as well as projects.calfNavigation but its navigation code imports the custom Adaptive implementation, not JetBrains Navigation.

## Impact and preconditions
The unused library expands the dependency/compatibility surface and was a stated reason for raising the sample minSdk to24 during #546, while the actual navigation module deliberately uses an older AndroidX navigation version to retain minSdk23.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- sample/common/build.gradle.kts32 and33 include two navigation libraries; App and AppNavGraph use com.mohamedrejeb.calf.navigation APIs.
- Archived #546 explains navigation2.10.0-alpha05 in sample versus Android navigation2.9.7 in calf-navigation and minSDK24/23 constraints.

## Recommended solution
Confirm no generated/transitive requirement, remove the unused dependency, then re-evaluate rather than blindly lowering minSdk. Keep actual feature minimums separate from an optional example dependency.

## Risks and compatibility
Removing a dependency can change resolved versions; compare the complete dependency graph and build every sample target. This is a cleanup opportunity, not proof the sample works on API23.

## Required tests / acceptance criteria
- Search/import audit and dependency graph prove the library is unused.
- Build Android/JVM/JS/Wasm/iOS sample targets after removal.
- Only lower minSdk after merged-manifest/dependency and device verification.

## Dependencies
- NAV-008

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/546
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
