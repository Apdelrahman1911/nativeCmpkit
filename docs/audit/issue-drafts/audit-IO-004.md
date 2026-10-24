# [High][IO-004] Desktop save can delete its own source and does not reliably replace existing content

<!-- nativecmpkit-item:audit:IO-004 -->
## Classification
- **Finding:** IO-004
- **Priority:** High
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt:95-115`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt#L95-L115) — `showSaveDialog/showSaveDialogWithFile`
- [`calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.kt:31-49`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.kt#L31-L49) — `launch content contract`

## Root cause
The file overload uses sourceFile.copyTo(destFile, overwrite=true) without same-file detection; Kotlin deletes an existing target before opening the source. For identical paths this deletes the source. The null-content overload calls createNewFile(), which does nothing when a target already exists.

## Impact and preconditions
Choosing the source file as the destination destroys the only source and then raises FileNotFoundException. Saving null to an existing nonempty destination returns success while preserving its old contents instead of the documented empty-file semantics. Other failed overwrites can leave a deleted or partial destination.

## Supporting evidence
- scripts/audit/io_jvm_probes.py compiled the unchanged baseline PlatformFilePicker.kt with a fake native dialog returning a temporary source path.
- Observed FileNotFoundException and source.exists=false after self-copy.
- Observed 13 old bytes still present after a successful null-content save.
- The same harness passed normal copy/cancel/new-empty-file paths on installed Kotlin2.0.21/coroutines1.6.4 and Kotlin2.4.0/coroutines1.10.2; this was not the pinned full Gradle build.

## Recommended solution
Detect same files with filesystem identity checks (including aliases) before destructive work, define a no-op or explicit error for self-copy, and implement deliberate overwrite semantics. Stage content into a sibling temporary file and replace atomically where possible; explicitly truncate if null is defined as empty content.

## Risks and compatibility
Consider symlinks, hard links, permission changes, atomic-move availability and cancellation. The reproduction used only audit-owned temporary files. Do not add file deletion to a generic error path without proving ownership.

## Required tests / acceptance criteria
- Source equals destination
- Relative/absolute alias, symlink and hard-link destinations
- Null content with existing and absent target
- Read/write failure preserves old destination
- Large streamed copy and cancellation
- Normal save/cancel

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
