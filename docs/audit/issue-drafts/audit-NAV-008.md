# [Medium][NAV-008] Navigation exposes two incompatible controller abstractions and lacks a declared platform capability contract

<!-- nativecmpkit-item:audit:NAV-008 -->
## Classification
- **Finding:** NAV-008
- **Priority:** Medium
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavHostController.kt:3-7`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavHostController.kt#L3-L7) — `expect NavHostController and extensions`
- [`calf-navigation/src/androidMain/kotlin/com/mohamedrejeb/calf/navigation/NavHostController.android.kt:3-13`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/androidMain/kotlin/com/mohamedrejeb/calf/navigation/NavHostController.android.kt#L3-L13) — `AndroidX actual typealias`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt:8-16`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt#L8-L16) — `rememberNavController/AdaptiveNavHostController`
- [`calf-navigation/src/iosMain/kotlin/com.mohamedrejeb.calf/navigation/AndroidBackHandler.ios.kt:5-11`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/iosMain/kotlin/com.mohamedrejeb.calf/navigation/AndroidBackHandler.ios.kt#L5-L11) — `iOS no-op back handler`
- [`calf-navigation/build.gradle.kts:1-23`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/build.gradle.kts#L1-L23) — `prototype module configuration`

## Root cause
The expect NavHostController is AndroidX on Android and Adaptive elsewhere, while the public rememberNavController and AdaptiveNavHost use Adaptive on every platform. Non-Android AndroidBackHandler actuals are no-ops and no browser/native stack adapter exists.

## Impact and preconditions
Consumers may assume AndroidX lifecycle/back-stack ownership, iOS native interactive gestures or browser history support that the Adaptive API does not implement. The module is included but intentionally not published and was described as coming soon.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- All ten navigation actual files were read; desktop/iOS/JS/Wasm back handlers explicitly contain only no-op comments.
- The actual controller extensions delegate to existing member methods; there is no evidence of infinite recursion from their same-named calls.
- Navigation build lacks module.publication.

## Recommended solution
Keep navigation experimental/unpublished. Record an ADR selecting an adapter to a mature navigation library or a deliberately minimal independent stack; publish an explicit capability matrix and an API migration plan before implementation.

## Risks and compatibility
A rewrite during identity migration would create unnecessary compatibility and licensing risk. No-op platform behavior is source-confirmed, but absence of a promised advanced feature is tracked as an improvement rather than an invented runtime vulnerability.

## Required tests / acceptance criteria
- Compile a common consumer using the supported controller factory/host API on every target.
- Android system/predictive back, iOS app-provided back/gesture behavior, desktop keyboard back and web history are tested according to the declared contract.
- Per-entry lifecycle/viewmodel/restoration requirements are specified before release.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/139
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
