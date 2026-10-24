# [Medium][NAV-004] AdaptiveBundle violates documented runtime type and fallback contracts

<!-- nativecmpkit-item:audit:NAV-004 -->
## Classification
- **Finding:** NAV-004
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt:42-61`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt#L42-L61) — `operator get<T>`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt:94-109`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt#L94-L109) — `putObject`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt:556-582`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveBaseBundle.kt#L556-L582) — `getString overloads`

## Root cause
The generic get uses an erased as? T without a reified/type-token check, so JVM caller casts can throw despite the documented null-on-wrong-type behavior. getString calls toString on any value. putObject recognizes fewer types than the bundle's explicit setters, including omission of Float.

## Impact and preconditions
A wrong-type lookup may crash or silently coerce data rather than returning null/default. Generic insertion rejects values that explicit insertion supports. These inconsistencies impede reliable argument validation and migrations.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Baseline JVM checks reproduce wrong-type generic-get ClassCastException, Int-to-String coercion and putObject(Float) rejection.
- Specific primitive getters instead use explicit as? checks with default fallback, e.g. getDouble lines551-553.

## Recommended solution
Use well-defined typed accessors or a portable checked type strategy; align getString with its contract; decide and test the supported generic put set. Document this as an in-memory mutable map, not an Android Parcelable/PersistableBundle replacement.

## Risks and compatibility
Array/list values and mMap are exposed mutable references; deep-copy/thread-safety semantics are not currently provided. Kotlin/JS and Native generic-cast behavior must be tested rather than inferred from the JVM run.

## Required tests / acceptance criteria
- Wrong-type get<Int> from a String follows the chosen contract without an unexpected caller ClassCastException.
- getString of Int42 returns the documented fallback/null rather than "42".
- All explicitly supported scalar/array/list setters have consistent generic insertion and retrieval rules.
- Explicit null versus absent key, aliasing and mutation behavior are documented/tested.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
