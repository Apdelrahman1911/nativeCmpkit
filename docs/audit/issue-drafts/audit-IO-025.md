# [Medium][IO-025] iOS Document filter maps an application MIME wildcard to the application-bundle UTI

<!-- nativecmpkit-item:audit:IO-025 -->
## Classification
- **Finding:** IO-025
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.kt:22,133-135`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.kt#L22) — `Document/DocumentContentType`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:295-319`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L295-L319) — `createUIDocumentPickerViewController contentTypes`

## Root cause
FilePickerFileType.Document carries application/*, but the iOS mapping converts it to UTTypeApplication, which describes application bundles rather than the MIME application category containing PDFs, Office documents, archives and other data.

## Impact and preconditions
Document mode can hide ordinary application/* documents on iOS while the same mode permits them on Android/Desktop/Web. Exact picker UI visibility has not been device-tested, but the type-semantic mismatch is in source.

## Supporting evidence
- Common DocumentContentType is application/*; iOS line 308 selects UTTypeApplication rather than a document/data category.
- The extension path already falls back to UTTypeData when resolution is empty, while Custom MIME mapping does not.

## Recommended solution
Define the intended Document set and map to explicit document UTTypes or a broad appropriate data/content type; do not equate MIME top-level categories with similarly named UTI constants. Retain specific Pdf/Word/Spreadsheet paths.

## Risks and compatibility
A broad UTTypeData fallback may include more than application/*; document the platform difference or supply a curated type list. Unknown Custom MIME types also need a deliberate empty-list fallback/error policy.

## Required tests / acceptance criteria
- Document mode allows PDF/DOCX/XLSX/ZIP as specified
- Explicit Pdf/Word/Spreadsheet unchanged
- Unknown custom MIME/extension behavior
- iOS versus Android/Desktop filter matrix

## Dependencies
- IO-015

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
