<!-- nativecmpkit-upstream-sync:674932206:78 -->
<!-- source-fingerprint:b6b9cde300bb5e5e4483c8b86845ad0f15d959c765de91f18925fb709aca8099 -->
## Current upstream context: Calf #78

Original: [Contacts and OTP feature](https://github.com/MohamedRejeb/Calf/issues/78) — [Lilytreasure](https://github.com/Lilytreasure); created `2024-03-28T15:01:04Z`, updated `2026-03-16T13:03:18Z`; upstream state **open**.
Original IDs: `2213460082` / `I_kwDOKDql7s6D7rhy`. Original labels: `permissions` (#9F075D; no description).

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant improvement/remaining scope; partial existing support is identified below.

Read/write contacts and SMS permission properties exist, but permission authorization is not contacts retrieval or OTP reading/autofill. The upstream maintainer comment 2378840675 promised a contacts permission via PR181, not a complete contacts/OTP API.

**Next step:** Document partial fulfillment and decide separately whether contacts/OTP data APIs belong in scope; use least-privilege platform autofill/retriever approaches rather than blanket SMS reading.

Primary tracking: #166. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-permissions/contacts/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.kt:1-23`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/contacts/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.kt#L1-L23) — `ReadContacts and WriteContacts properties`
- [`calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.kt:1-34`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.kt#L1-L34) — `SMS permission properties`

### Original issue description (verbatim Markdown)
````markdown
Kindly Add Access contacts and read OTP support
````

### Original public discussion (1 comments)

**[MohamedRejeb](https://github.com/MohamedRejeb)** — created `2024-09-27T09:22:29Z`, updated `2024-09-27T09:22:29Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/78#issuecomment-2378840675); IDs `2378840675` / `IC_kwDOKDql7s6Nyjpj`.
````markdown
Read contacts permission is coming with the next version thanks to #181 
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/78/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/78/comments.json)
- [Full public timeline: 3 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/78/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-03-16T13:03:18Z`: `labeled` by [MohamedRejeb](https://github.com/MohamedRejeb) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/23606832816)); label `permissions`.
- `2026-10-24T16:25:04Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/78)); [[Low][Upstream #78] Contacts and OTP feature](https://github.com/Apdelrahman1911/nativeCmpkit/issues/166).
