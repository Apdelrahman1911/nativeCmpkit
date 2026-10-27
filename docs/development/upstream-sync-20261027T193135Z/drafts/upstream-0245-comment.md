<!-- nativecmpkit-upstream-sync:674932206:245 -->
<!-- source-fingerprint:c19af1b270d40d8bd4d5c70207fb918122e499d1bdfc4f5a6db565456e18eda7 -->
## Current upstream context: Calf #245

Original: [Custom data source media content](https://github.com/MohamedRejeb/Calf/issues/245) — [lemkoleg](https://github.com/lemkoleg); created `2025-01-12T18:32:03Z`, updated `2025-01-12T18:32:03Z`; upstream state **open**.
Original IDs: `2782624718` / `I_kwDOKDql7s6l23vO`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.

Media is an excluded build-only project. Custom Android DataSource or iOS AVAssetResourceLoader cannot be added to a functioning media module because none exists. Keep it as a future API requirement, not a current media defect.

**Next step:** Preserve custom/streaming resource injection as a media roadmap requirement under the scaffold/capability issue; evaluate module scope first.

Primary tracking: #151. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-media/build.gradle.kts:1-47`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-media/build.gradle.kts#L1-L47) — `excluded media scaffold`
- [`settings.gradle.kts:28-60`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/settings.gradle.kts#L28-L60) — `module inclusion list`

### Original issue description (verbatim Markdown)
````markdown
Hello. Very useful project. I see you have planned audio-video players. Please, provide for the use of custom resources (DataSource in Android and AVAssetResourceLoaderDelegateProtocol, AVURLAsset in iOS). Possibly through interface implementation. Thanks in advance.
````

### Original public discussion (0 comments)
No public conversation comments were returned in this snapshot.

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/245/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/245/comments.json)
- [Full public timeline: 1 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/245/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:24:07Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/245)); [[Low][NATIVE-035] Maps, media and notification scaffolds must not be represented as implemented features](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151).
