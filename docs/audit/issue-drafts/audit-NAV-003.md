# [Medium][NAV-003] NavArgument builder rejects missing/null defaults and accepts mismatched typed defaults

<!-- nativecmpkit-item:audit:NAV-003 -->
## Classification
- **Finding:** NAV-003
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt:10-26`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt#L10-L26) — `NavArgument/defaultValue/putDefaultValue`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt:74-126`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt#L74-L126) — `NavArgument.Builder`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt:138-146`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavArgument.kt#L138-L146) — `missingRequiredArguments`

## Root cause
build() unconditionally requires defaultValue != null, even if a type was supplied, and NavArgument stores defaultValue as non-null Any. setDefaultValue accepts Any? but build never verifies compatibility with the declared type.

## Impact and preconditions
A valid typed required argument without a default cannot be constructed; a nullable String argument cannot explicitly default to null. An Int type with a String default builds and then throws ClassCastException from putDefaultValue. The missing-required-arguments helper cannot be reached through a normal default-absent builder configuration.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- JVM baseline reproductions compiled with cached Kotlin2.4.20 and exited0: first three named checks reproduce these defects.
- Evidence: docs/testing/evidence/navigation-core-icons/{Repro.kt,run_jvm_repros.py,jvm-repro-result.txt}.
- Compiler also warns that defaultValue?.hashCode() line66 uses an unnecessary safe call, consistent with the non-null field.

## Recommended solution
Represent default absence separately from an explicit null; permit declared types without defaults; reject incompatible defaults at construction and handle nullable defaults consistently. Keep required-argument detection separate from per-value verification.

## Risks and compatibility
Avoid relying on unchecked generic casts or platform-specific reflection to implement common type validation. Existing callers might rely on delayed failure, so document the fail-fast change.

## Required tests / acceptance criteria
- Typed Int without default builds and is required.
- Nullable String with explicit null builds and retains defaultValuePresent=true.
- Nonnullable Int with null or String default rejects at build, not later.
- All built-in scalar and array defaults, missing-required predicate and verify behavior are covered on JVM/JS/Wasm/Native.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
