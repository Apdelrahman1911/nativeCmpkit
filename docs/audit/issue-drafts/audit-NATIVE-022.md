# [Medium][NATIVE-022] Android camera hardcodes a host FileProvider authority without public setup or validation

<!-- nativecmpkit-item:audit:NATIVE-022 -->
## Classification
- **Finding:** NATIVE-022
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-camera-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt:35-43`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt#L35-L43) — `launch FileProvider URI creation`
- [`sample/android/src/main/AndroidManifest.xml:58-66`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/android/src/main/AndroidManifest.xml#L58-L66) — `sample FileProvider registration`
- [`sample/android/src/main/res/xml/filepaths.xml:2-6`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/android/src/main/res/xml/filepaths.xml#L2-L6) — `whole-cache provider path`

## Root cause
API24+ requires ${context.packageName}.provider and a provider path covering cacheDir, but the library ships no manifest/provider contract or dedicated camera setup guide. getUriForFile and launcher.launch are outside error handling. A device camera feature does not ensure an installed intent handler.

## Impact and preconditions
A host adding only the artifact can crash on first launch with missing provider metadata or unmatched path. Authority collisions or host-custom providers cannot be selected. Copying the sample exposes the whole cache tree as grantable rather than a camera-only subdirectory.

## Supporting evidence
- No camera AndroidManifest.xml exists in the baseline.
- Setup details survive in upstream PR274 body, while the current sample is the only in-repository provider example.

## Recommended solution
Document/validate a configurable authority/output provider, reserve a narrow camera cache subdirectory, and return explicit configuration/launch failure. If a manifest provider is bundled later, use a namespaced authority and preserve host override/backward compatibility.

## Risks and compatibility
The sample provider is exported=false with temporary grants: whole-cache path is not proof all cache files are publicly readable. Treat narrowing as defense in depth, not an existing unauthenticated data leak.

## Required tests / acceptance criteria
- Minimal consuming app with correct/missing/wrong provider setup on API23 and24+.
- Host with its own provider authority and no installed camera intent handler.
- Only camera-owned files can be granted through recommended provider configuration.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/274
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
