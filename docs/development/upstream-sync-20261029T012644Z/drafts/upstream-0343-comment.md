<!-- nativecmpkit-upstream-sync:674932206:343 -->
<!-- source-fingerprint:ea427aa2dd1a4d8c39c10eda634563c54c956b66484a56b81c4992b8d72c21a6 -->
## Current upstream context: Calf #343

Original: [Support native file preview](https://github.com/MohamedRejeb/Calf/issues/343) — [MohamedRejeb](https://github.com/MohamedRejeb); created `2025-07-20T12:41:26Z`, updated `2025-07-20T12:41:26Z`; upstream state **open**.
Original IDs: `3246327607` / `I_kwDOKDql7s7Bfwc3`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant improvement/remaining scope; partial existing support is identified below.

No dedicated native file-preview API/module exists. Desktop share opening a file is not a portable preview abstraction or iOS Quick Look implementation.

**Next step:** Record native preview as an opt-in future module: define unsupported/cancel/error behavior, file-access lifetime and platform viewer capabilities before selecting dependencies.

Primary tracking: #169. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`settings.gradle.kts:28-60`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/settings.gradle.kts#L28-L60) — `included modules`
- [`calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareContent.kt:1-59`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareContent.kt#L1-L59) — `share content API, not preview`

### Original issue description (verbatim Markdown)
````markdown
https://pub.dev/packages/native_file_preview
````

### Original public discussion (0 comments)
No public conversation comments were returned in this snapshot.

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/343/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/343/comments.json)
- [Full public timeline: 1 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/343/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:25:15Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/343)); [[Low][Upstream #343] Support native file preview](https://github.com/Apdelrahman1911/nativeCmpkit/issues/169).
