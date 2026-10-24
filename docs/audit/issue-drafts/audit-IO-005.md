# [High][IO-005] iOS saver exports the original source with move semantics and ignores requested file names

<!-- nativecmpkit-item:audit:IO-005 -->
## Classification
- **Finding:** IO-005
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt:94-113`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt#L94-L113) — `onLaunch/onLaunchFile/onLaunchData`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt:119-123`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt#L119-L123) — `writeTempFile`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt:137-150`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt#L137-L150) — `presentExportPicker`

## Root cause
The KmpFile overload passes file.url directly, ignoring baseName/extension. The byte/data path prefixes the requested filename with a UUID in the filename itself. The one-argument forExportingURLs initializer uses move-style export instead of explicitly selecting asCopy=true.

## Impact and preconditions
The Save API can offer Move and transfer the source rather than leave it intact. Exported names can unexpectedly contain UUID prefixes or retain the original source name. Saved KmpFiles may also point outside ongoing security-scoped access.

## Supporting evidence
- Baseline passes file.url directly at 109 and constructs UUID-filename at 120.
- Unmerged commits 675d049 and be274cc in PR #551 implement named staging and asCopy=true; their existence corroborates the baseline defect, not its repair on main.
- No iOS device run was available.

## Recommended solution
Stage all exports in a unique private directory under the exact requested basename, preserve source contents, use the explicit copy export initializer, and remove only owned staging after terminal completion. Validate/normalize filename components.

## Risks and compatibility
Staging adds disk IO but not whole-file heap buffering. Handle scope acquisition and failure before presenting a picker. Prevent path separators from escaping or corrupting the staging layout.

## Required tests / acceptance criteria
- Verify source remains after successful save
- Bytes/NSData/KmpFile/NSURL export has exact suggested name
- Cancel and interactive dismissal cleanup
- Unicode and separator-containing names
- Read-only/disk-full staging
- Destination access after callback

## Dependencies
- IO-008

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
- https://github.com/MohamedRejeb/Calf/commit/675d049
- https://github.com/MohamedRejeb/Calf/commit/be274cc
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
