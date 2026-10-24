# [High][BUILD-006] Verification pipeline does not gate platform behavior, consumer compatibility, or native correctness

<!-- nativecmpkit-item:audit:BUILD-006 -->
## Classification
- **Finding:** BUILD-006
- **Priority:** High
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `all modules`, `CI`
- **Estimated complexity:** XL
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`.github/workflows/gradle.yml:20-61`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/gradle.yml#L20-L61) — `build job and allTests invocation`
- [`.github/workflows/build-native-libs.yml:49-64`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L49-L64) — `native build-only tasks`
- [`convention-plugins/src/main/kotlin/Android.kt:33-37`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/convention-plugins/src/main/kotlin/Android.kt#L33-L37) — `withHostTest`
- [`convention-plugins/src/main/kotlin/Targets.kt:11-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/convention-plugins/src/main/kotlin/Targets.kt#L11-L22) — `declared targets`

## Root cause
Only 86 upstream Kotlin @Test functions exist (69 UI, 9 picker, 6 IO, 2 navigation), with no Rust test functions, Android device tests or iOS-specific test sources. The baseline main CI runs allTests on one macOS host and compiles native libraries without behavioral tests. No API/ABI snapshot or external consumer gate is configured.

## Impact and preconditions
A green task aggregate cannot establish platform parity, JNI lifecycle safety, Android permissions/device behavior, iOS delegate correctness, browser functionality, or binary/source compatibility. The audit found real defects in areas outside this test surface.

## Supporting evidence
- docs/testing/evidence/baseline-test-inventory.json enumerates all 86 annotations in 13 executable test files plus 2 helper files
- Both native src/lib.rs files contain zero #[test] annotations
- Baseline build workflow invokes only ./gradlew allTests; no external consumer fixture or device runner is configured

## Recommended solution
Create layered CI: common unit tests; Linux/macOS/Windows desktop tests and native smoke tests; JS/Wasm browser tests; Android host plus device/API-matrix tests; Apple simulator/device lifecycle tests; sample builds; candidate-artifact consumer and API/ABI compatibility checks. Retain machine-readable results and distinguish NO-SOURCE/SKIPPED from tests passed.

## Risks and compatibility
GUI tests require deterministic dialogs, timezone, locale and UI-thread scheduling. A much larger matrix should be phased by risk and avoid publishing as part of verification.

## Required tests / acceptance criteria
- Verify per-module test counts are nonzero where expected
- Exercise all regressions listed in module finding required_tests
- Build isolated minimum-supported-SDK and Kotlin/Compose-version consumers
- Assert Kotlin/JNI/Swift API compatibility against the retained compatibility surface

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/546
- https://github.com/MohamedRejeb/Calf/issues/23
- https://github.com/MohamedRejeb/Calf/issues/528
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
