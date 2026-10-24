# [Medium][NAV-018] Derived Apache-2.0 source attribution needs reconstruction and artifact verification

<!-- nativecmpkit-item:audit:NAV-018 -->
## Classification
- **Finding:** NAV-018
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`, `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt:1-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt#L1-L22) — `AOSP-style bundle fields/documentation without source header`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBundle.kt:1-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBundle.kt#L1-L12) — `AOSP-derived Bundle description`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt:1-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt#L1-L20) — `AndroidX-style argument implementation/header`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt:1-15`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt#L1-L15) — `AndroidX-style NavType description/header`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt:76-80`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt#L76-L80) — `compose-cupertino attribution`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButton.kt:163-173`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButton.kt#L163-L173) — `AndroidLiquidGlass defaults attribution`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt:292-300`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt#L292-L300) — `AndroidLiquidGlass defaults attribution`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DragGestureInspector.kt:1-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DragGestureInspector.kt#L1-L20) — `package-adapted Kyant utility without original source header`

## Root cause
Navigation adaptations retain extensive distinctive AndroidX/AOSP documentation and structure without original source headers; UI CupertinoSlider and LiquidGlass components/utilities explicitly derive from Compose Cupertino/AndroidLiquidGlass but omit known source copyright text. Exact originally copied revisions are not established. Migration adds verified project-level notices/local licenses; per-source provenance and distribution packaging remain unverified.

## Impact and preconditions
The Apache-2.0 project license does not by itself establish that all required upstream copyright/attribution notices were preserved. This is a provenance/compliance risk, not a legal determination or evidence that the algorithms are malicious.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- AdaptiveBaseBundle retains mOwnsLazyValues/mFlags and references nonexistent mParcelledData/Parcelable/PersistableBundle, matching AOSP bundle lineage.
- Reference AndroidX headers identify Copyright2018 The Android Open Source Project; BaseBundle identifies2014 and Bundle2007.
- Read-only reference pins and SHA256 values are stored in licenses/navigation-aosp-provenance.json; original-copy revision remains explicitly unresolved.
- CupertinoSlider explicitly credits compose-cupertino at76-80. Observed source pin f66875aa6f3848b30c38e42a89fc99c9ac24a585 has Copyright(c)2023-2024 Compose Cupertino project and open source contributors under Apache-2.0. Its full LICENSE.txt also retains JetBrains2020-2021 attribution.
- AndroidLiquidGlass reference pin65ab177e90e5c1d8c62e70cf7755841982da65f6 has Apache-2.0 Copyright2025 Kyant. UI reviewer found DragGestureInspector exact after package normalization and closely adapted DampedDragAnimation/InteractiveHighlight.
- Source-tree notice restoration/local license additions are remediation evidence, not proof that all copied sources or any released binary comply. See licenses/ui-derived-source-provenance.json.

## Recommended solution
Preserve the verified AOSP, Compose Cupertino and Kyant copyright/license notices in THIRD_PARTY_NOTICES.md and licenses/; trace introduction commits to identify original source versions and restore appropriate source headers through a coordinated change. Verify artifact notice packaging and retain existing Calf change attribution. Remove misleading Android-only navigation KDoc as the API contract is clarified.

## Risks and compatibility
Current reference pins are observation snapshots, not a claim that Calf copied those exact future/current revisions. Do not invent authorship years or attribute unrelated Calf changes to AOSP.

## Required tests / acceptance criteria
- Compare distinctive source/docs against pinned AndroidX NavArgument/NavType and AOSP BaseBundle/Bundle headers.
- Trace original Calf introduction commits and record whether the exact imported revision can be established.
- Verify source and future binary distributions retain all established Apache notices.
- Verify Compose Cupertino/Kyant source and notice correspondence, preserving copyright text and recording whether exact original copy revisions can be recovered.

## Dependencies
- NAV-008

## Historical context
- https://github.com/androidx/androidx
- https://github.com/aosp-mirror/platform_frameworks_base
- https://github.com/alexzhirkevich/compose-cupertino/tree/f66875aa6f3848b30c38e42a89fc99c9ac24a585
- https://github.com/Kyant0/AndroidLiquidGlass/tree/65ab177e90e5c1d8c62e70cf7755841982da65f6
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
