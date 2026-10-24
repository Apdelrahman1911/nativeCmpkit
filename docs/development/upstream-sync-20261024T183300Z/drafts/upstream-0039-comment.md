<!-- nativecmpkit-upstream-sync:674932206:39 -->
<!-- source-fingerprint:38e659756e0a614e9bc9118c0ae28927f33635a318513461c845debf9a76ddc8 -->
## Current upstream context: Calf #39

Original: [Webview not loading html content](https://github.com/MohamedRejeb/Calf/issues/39) — [Utkarsh831](https://github.com/Utkarsh831); created `2023-12-01T07:20:12Z`, updated `2023-12-01T07:20:12Z`; upstream state **open**.
Original IDs: `2020270879` / `I_kwDOKDql7s54auMf`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.

The old Desktop QuantumRenderer/no-pipeline symptom remains a host-dependent reproduction target. The 2023 web-loading half predates the current 2026 iframe implementation and is not proof that the same bug remains. Native-feature startup risk already references this report.

**Next step:** Combine desktop startup checks with #151/#346 in NATIVE-018; separately retest the old web claim with an allowed-origin minimal iframe before calling it current.

Primary tracking: #75. Related existing tickets: #64.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:42-57`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L42-L57) — `WebView/JFXPanel initialization`
- [`calf-webview/build.gradle.kts:9-18,41-49`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/build.gradle.kts#L9-L18) — `host classifier and JavaFX dependencies`

### Original issue description (verbatim Markdown)
````markdown
I am trying to use web view on desktop and web. But on desktop, I am getting 
`Caused by: java.lang.RuntimeException: Error initializing QuantumRenderer: no suitable pipeline found`
and the web just keeps loading. Do I need to do additional setup for these platforms? Thank you for the help.
````

### Original public discussion (0 comments)
No public conversation comments were returned in this snapshot.

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/39/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/39/comments.json)
- [Full public timeline: 2 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/39/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:18:30Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/39)); [[Medium][NATIVE-005] WebView request state is not reset consistently on Desktop, iOS and Web](https://github.com/Apdelrahman1911/nativeCmpkit/issues/64).
- `2026-10-24T16:19:11Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/39)); [[Medium][NATIVE-018] Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75).
