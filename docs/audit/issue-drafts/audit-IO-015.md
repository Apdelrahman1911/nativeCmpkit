# [Medium][IO-015] Desktop MIME filtering omits modern image formats and silently disables unknown custom filters

<!-- nativecmpkit-item:audit:IO-015 -->
## Classification
- **Finding:** IO-015
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt:130-144`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt#L130-L144) — `resolveExtensions`
- [`calf-file-picker/src/desktopMain/resources/jodd/net/MimeTypes.properties:651-696`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/resources/jodd/net/MimeTypes.properties#L651-L696) — `image MIME records`
- [`calf-file-picker/src/desktopMain/kotlin/jodd/net/MimeTypes.kt:133-159`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/jodd/net/MimeTypes.kt#L133-L159) — `findExtensionsByMimeTypes`

## Root cause
Desktop filters translate MIME types through a fixed embedded extension table that has no HEIC, HEIF or AVIF entries. If a requested custom MIME has no extension mapping, resolveExtensions returns null, meaning no filter rather than an unsupported/empty filter.

## Impact and preconditions
Image mode excludes commonly produced image files on Desktop, while Custom(image/avif) unexpectedly permits every file. File-picker filters are UI hints, not security validation; callers must still validate content.

## Supporting evidence
- scripts/audit/io_jvm_probes.py initializes all 981 unique extensions in the unchanged table.
- Probe verifies none of avif/heic/heif occur in image/*, and actual resolveExtensions via a mocked bridge sends null for Custom(image/avif).

## Recommended solution
Update/provenance-pin the MIME data and test contemporary formats. Make unknown MIME behavior explicit and choose a documented fallback/error; preserve the direct Extension path for types the MIME database does not know. Never represent filters as a security boundary.

## Risks and compatibility
Adding extensions does not make every decoder support those formats. Avoid huge wildcard filter overhead and maintain the embedded data license.

## Required tests / acceptance criteria
- AVIF/HEIC/HEIF present in image filter
- Unknown MIME policy
- Mixed known/unknown custom types
- Extension-only bypass
- Native dialog format acceptance on Linux/Windows/macOS

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
