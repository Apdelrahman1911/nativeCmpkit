# [Medium][IO-013] iOS picked-file copies have no ownership cleanup and are created before result limits are applied

<!-- nativecmpkit-item:audit:IO-013 -->
## Classification
- **Finding:** IO-013
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-io`, `calf-file-picker`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/TempFile.kt:13-25`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/TempFile.kt#L13-L25) — `NSURL.createTempFile`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:105-124`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L105-L124) — `document result staging`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:185-197,266-285`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L185-L197) — `photo provider staging`
- [`calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt:15-27`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt#L15-L27) — `KmpFile ownership contract`

## Root cause
Every nonfolder selection creates a new UUID-named file in NSTemporaryDirectory. KmpFile exposes no dispose/release-owned-copy operation and no cleanup registry exists. Document multi-select stages every URL before take(maxItems); cancelled/late photo callbacks can stage files that no caller receives.

## Impact and preconditions
Repeated or very large picks consume unbounded temporary disk until external OS cleanup. Files excluded by maxItems still incur copy IO and survive. The property documentation calls a temp copy persistent even though the OS may purge it.

## Supporting evidence
- TempFile.kt only copies; no complementary delete exists for picker-created copies in these modules. Saver cleanup is a separate list and does not cover picked copies.
- Document list take occurs after mapNotNull and withContext copies at line 122.
- Photo cancellation calls progress.cancel but has no cleanup for copied results abandoned during coroutine delivery.

## Recommended solution
Define owned staging lifetimes and expose explicit release/copy-to-permanent-storage behavior without deleting caller-owned files. Apply limits before staging, remove unreturned copies on cancellation/error, and bound photo provider concurrency. Retain provider temporary content synchronously before the provider callback ends.

## Risks and compatibility
Never delete picked user originals. Automatic early cleanup must not invalidate returned KmpFiles still in use; ownership must be explicit and backwards-compatible. NSItemProvider callback URLs must be copied before callback return.

## Required tests / acceptance criteria
- Repeated pick/release disk accounting
- Select 100 files with maxItems=1 and assert only one staged
- Cancel during provider copy
- Failure halfway through multi-select
- Returned file lifetime and explicit persistence
- OS purge behavior documented

## Dependencies
- IO-007
- IO-008

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/495
- https://github.com/MohamedRejeb/Calf/pull/551
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
