# [Medium][NAV-005] AdaptiveNavType inference and serialization are incomplete and not reliably round-trippable

<!-- nativecmpkit-item:audit:NAV-005 -->
## Classification
- **Finding:** NAV-005
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt:105-117`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt#L105-L117) — `serializeAsValue`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt:147-201`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt#L147-L201) — `fromArgType`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt:244-275`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt#L244-L275) — `inferFromValueType`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt:580-594`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt#L580-L594) — `StringType.parseValue/serializeAsValue`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt:604-625`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavType.kt#L604-L625) — `StringArrayType`

## Root cause
String-array inference is commented out even though StringArrayType exists; custom Parcelable/Serializable lookup is entirely commented. String serialization leaves URI delimiters unescaped despite its KDoc, uses "null" for null and literal "null", and arrays inherit object toString serialization rather than an array codec.

## Impact and preconditions
Supported explicit String arrays fail inferred construction; string values lose distinctions on parse/serialize and can violate a caller's URI encoding expectations. Array serialized values cannot be used to reconstruct the original arrays. These are helper-API defects, not an active deep-link injection exploit: the host does not currently parse routes.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Baseline JVM repro confirms StringArray inference throws while explicit StringArrayType put/get works.
- Baseline JVM repro confirms serializeAsValue("a/b?x=1&n=2#frag") returns the unescaped input.
- Array append copies appear at lines363-364,431-432,486-487,549-550,624-625.

## Recommended solution
Specify a small portable type/codec contract, implement consistent inference including String arrays, define null versus literal encoding and round-trip serialization, and remove unsupported Parcelable/XML claims. If URI encoding belongs in another layer, state that clearly and change the misleading contract.

## Risks and compatibility
Encoding changes can break stored routes and must not double-encode already encoded data. Adding runtime reflection to common code would sacrifice multiplatform compatibility. Repeated array parseValue(previous) calls allocate copies and are O(n²) across n values.

## Required tests / acceptance criteria
- StringArray inference succeeds for empty and nonempty arrays and rejects mixed arrays.
- Round-trip null, literal "null", Unicode, slash/query/hash/ampersand characters and every supported array type.
- Unknown/custom fromArgType fails with a truthful supported-types error.
- Benchmark/bound repeated-array parsing before adopting it for large external inputs.

## Dependencies
- NAV-003
- NAV-004

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
