# [Low][IO-016] MIME lookup is locale-sensitive, parses only comma-space lists, and allocates per entry

<!-- nativecmpkit-item:audit:IO-016 -->
## Classification
- **Finding:** IO-016
- **Priority:** Low
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/desktopMain/kotlin/jodd/net/MimeTypes.kt:104-105,123-124,133-159`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/jodd/net/MimeTypes.kt#L104-L105) — `MIME registration/lookup/search`
- [`calf-file-picker/src/desktopMain/kotlin/jodd/util/Wildcard.kt:90-109`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/jodd/util/Wildcard.kt#L90-L109) — `recursive wildcard search`

## Root cause
MIME/extension normalization uses Locale.getDefault instead of protocol-stable ROOT. Multi-MIME parsing splits only the exact string comma-space. Each map entry recomputes lowercase, creates a vararg array and runs an unused findAnyOf; wildcard matching recursively backtracks without a complexity bound.

## Impact and preconditions
Under Turkish locale uppercase TIFF/MIME I letters can miss mappings; comma-separated MIME lists without spaces return no results. All searches scan the full map and allocate unnecessarily. Pathological caller-supplied wildcard patterns can consume disproportionate CPU; no remote attack surface was demonstrated.

## Supporting evidence
- Kotlin harness confirms lookupMimeType(TIFF) is null under tr-TR while lowercase tiff resolves, and image/jpeg,image/png yields no extensions but comma-space yields four.
- Lines 143 and 146 show unused work and per-entry vararg conversion; no performance benchmark was used to claim a regression.

## Recommended solution
Normalize with Locale.ROOT, split on comma and trim/filter empties, precompute pattern arrays/reverse MIME index, remove the unused search, and replace or bound general recursive wildcard matching. Either remove unused mutable registration or synchronize/copy-on-write if used concurrently.

## Risks and compatibility
These helpers are internal; optimize demonstrated common filters first. Do not claim a security vulnerability from internal worst-case matching alone. Case-sensitive extensions on native dialogs need a deliberate policy.

## Required tests / acceptance criteria
- tr-TR uppercase TIFF and IMAGE/PNG
- Comma lists with zero/multiple spaces
- Known scalar/wildcard equivalence
- Adversarial bounded wildcard performance
- Concurrent registration only if that API is retained

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
