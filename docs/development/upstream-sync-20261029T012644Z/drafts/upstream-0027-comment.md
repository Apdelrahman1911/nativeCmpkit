<!-- nativecmpkit-upstream-sync:674932206:27 -->
<!-- source-fingerprint:ad40f1cab773513f2d86df88043b8bc790ae5d5c28d931e34d76fdbf3f602738 -->
## Current upstream context: Calf #27

Original: [Add Maps Support](https://github.com/MohamedRejeb/Calf/issues/27) — [MohamedRejeb](https://github.com/MohamedRejeb); created `2023-09-28T20:22:43Z`, updated `2024-03-05T09:56:36Z`; upstream state **open**.
Original IDs: `1918218042` / `I_kwDOKDql7s5yVa86`. Original labels: `enhancement` (#a2eeef; New feature or request).

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.

The included calf-maps project contains only its build file and no source/API. This is a valid unimplemented feature request, not a regression in an existing Maps implementation.

**Next step:** Keep maps requirements in the scaffold/capability issue; define platform/API scope and feasibility before implementation.

Primary tracking: #151. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-maps/build.gradle.kts:1-13`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-maps/build.gradle.kts#L1-L13) — `build-only module`

### Original issue description (verbatim Markdown)
````markdown
- [ ] Android
- [ ] iOS
- [ ] Desktop
- [ ] Web
````

### Original public discussion (2 comments)

**[azlekov](https://github.com/azlekov)** — created `2024-03-04T14:45:26Z`, updated `2024-03-04T14:45:26Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/27#issuecomment-1976745817); IDs `1976745817` / `IC_kwDOKDql7s510r9Z`.
````markdown
Hello, great library! Is there any update on this, how you see it on the timeline?
````

**[MohamedRejeb](https://github.com/MohamedRejeb)** — created `2024-03-04T15:42:32Z`, updated `2024-03-04T15:42:32Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/27#issuecomment-1976875624); IDs `1976875624` / `IC_kwDOKDql7s511Lpo`.
````markdown
Thanks! @azlekov, the main priority now is to provide a media player that works at least for Android and iOS. Then I can start working on supporting maps.
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/27/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/27/comments.json)
- [Full public timeline: 6 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/27/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2023-09-28T20:22:43Z`: `labeled` by [MohamedRejeb](https://github.com/MohamedRejeb) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/10503946279)); label `enhancement`.
- `2026-10-24T16:24:07Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/27)); [[Low][NATIVE-035] Maps, media and notification scaffolds must not be represented as implemented features](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151).
