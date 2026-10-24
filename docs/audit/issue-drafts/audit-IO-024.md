# [Medium][IO-024] JNI path conversion silently replaces non-Unicode filenames

<!-- nativecmpkit-item:audit:IO-024 -->
## Classification
- **Finding:** IO-024
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/native/src/lib.rs:39-68`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/native/src/lib.rs#L39-L68) — `paths_to_jstring_array/path_to_jstring`

## Root cause
Native paths not representable as Rust UTF-8 strings are converted with to_string_lossy and returned as ordinary Java paths. The original byte sequence is not preserved and no conversion error is reported.

## Impact and preconditions
On Unix filesystems with non-UTF-8 filenames, a chosen file can become an unopenable path or potentially refer to a distinct existing replacement-character name. Directory/save paths have the same lossy conversion. Public String/File APIs limit portable recovery.

## Supporting evidence
- Both helper fallbacks explicitly call to_string_lossy().into_owned().
- No real native file-picker selection of an invalid-UTF-8 name was run; the irreversible conversion is source-confirmed.

## Recommended solution
Define supported filename encoding explicitly; reject nonrepresentable paths with a typed error instead of silently substituting, or introduce an opaque/native path representation if preserving arbitrary Unix names is required.

## Risks and compatibility
JNI modified UTF-8 conversion and valid Unicode supplementary characters are a separate concern: jni crate handles ordinary Java/Rust strings. Do not claim all Unicode names are broken.

## Required tests / acceptance criteria
- Unix raw invalid-UTF-8 filename fixture
- Distinct replacement-character filename beside invalid-byte file
- Normal non-ASCII/emoji filenames
- Directory and save-path conversion errors
- JNI local-reference cleanup on conversion failure

## Dependencies
- IO-006

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
