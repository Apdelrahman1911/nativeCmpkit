<!-- nativecmpkit-upstream-sync:674932206:259 -->
<!-- source-fingerprint:e6398f541ac991aca01fe528ff8cba61ba2d90131582cea36e576b977d8ec4b0 -->
## Current upstream context: Calf #259

Original: [Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog](https://github.com/MohamedRejeb/Calf/issues/259) — [lemkoleg](https://github.com/lemkoleg); created `2025-02-18T17:11:00Z`, updated `2025-02-18T17:11:00Z`; upstream state **open**.
Original IDs: `2861084678` / `I_kwDOKDql7s6qiLAG`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant improvement/remaining scope; partial existing support is identified below.

Common alert exposes materialText/materialContent slots but iOS uses native UIAlertController descriptors and text. The requested adaptive busy/progress-dialog example is not available as a uniform arbitrary native Compose content slot.

**Next step:** Design/document an explicit busy-dialog example with cancel/accessibility semantics and a deliberate iOS presentation strategy; avoid silently inserting unsupported Material content into UIKit.

Primary tracking: #165. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.kt:65-122`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.kt#L65-L122) — `AdaptiveAlertDialog and AdaptiveBasicAlertDialog`

### Original issue description (verbatim Markdown)
````markdown
Hello. Very useful library. It would be nice to add demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog for the duration of the task. Or, even better, add a composable function. Instead of a parameter "text"
````

### Original public discussion (0 comments)
No public conversation comments were returned in this snapshot.

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/259/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/259/comments.json)
- [Full public timeline: 1 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/259/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:25:00Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/259)); [[Low][Upstream #259] Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog](https://github.com/Apdelrahman1911/nativeCmpkit/issues/165).
