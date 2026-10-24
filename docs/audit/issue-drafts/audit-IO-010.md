# [Medium][IO-010] File-kind queries misclassify extensionless browser files and nonexistent paths

<!-- nativecmpkit-item:audit:IO-010 -->
## Classification
- **Finding:** IO-010
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-io`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.web.kt:10-19`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.web.kt#L10-L19) — `exists/isDirectory`
- [`calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt:48-56,106-126`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt#L48-L56) — `isFile overloads`
- [`calf-io/src/desktopMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.desktop.kt:10-18`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/desktopMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.desktop.kt#L10-L18) — `desktop existence/kind queries`

## Root cause
Web isDirectory guesses from absence of a dot in file.name, although the representation is a File rather than a directory handle. Common isFile is simply !isDirectory and never establishes existence or a regular-file type.

## Impact and preconditions
A normal browser File named README is called a directory. A missing desktop file has isDirectory=false and therefore isFile=true; device/special-file distinctions are likewise lost. Callers can choose incorrect preview, traversal or validation behavior.

## Supporting evidence
- Web code at line 19 tests only file.name.contains(".").
- The negation at common line 56 evaluates true for desktop java.io.File.isDirectory=false on a missing path.

## Recommended solution
Return false for directories in the current browser File-only abstraction; add a separate directory representation if folder support is introduced. Specify whether isFile means regular existing file or merely not-a-directory, then implement consistent platform queries and compatibility documentation.

## Risks and compatibility
Changing previously permissive isFile semantics is observable. exists is a capability/snapshot question on browser File objects, not a live path probe; do not promise filesystem existence that browsers cannot expose.

## Required tests / acceptance criteria
- Browser README, LICENSE, dotfile and dotted ordinary filenames
- Missing desktop and iOS file
- Directory, regular file and symlink
- Permission-denied metadata
- Context and context-free overload parity

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
