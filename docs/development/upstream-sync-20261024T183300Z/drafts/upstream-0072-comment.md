<!-- nativecmpkit-upstream-sync:674932206:72 -->
<!-- source-fingerprint:bd1659482e7579d4c17299a7c70be175bd5829f818234a5216e04d3994542bb3 -->
## Current upstream context: Calf #72

Original: [Zoom in/out in browser](https://github.com/MohamedRejeb/Calf/issues/72) — [rcd27](https://github.com/rcd27); created `2024-03-04T06:59:09Z`, updated `2024-03-04T07:28:53Z`; upstream state **open**.
Original IDs: `2166082242` / `I_kwDOKDql7s6BG8rC`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant as an unverified reproduction target; the original report does not establish a current root cause.

Browser zoom/focus mismatch was reported against the 2024 rendering stack. The baseline sample now enters ComposeViewport and no exact current library-level coordinate bug is demonstrated by the report. The maintainer asked whether this was Desktop in comment1975890950; the actual host remains ambiguous in the archived exchange.

**Next step:** Add current JS/Wasm zoom/devicePixelRatio/pointer/keyboard smoke reproduction on Chromium, Firefox and Safari; route to Compose/Skiko if library-independent. First confirm whether the original reporter meant browser or desktop WebView zoom.

Primary tracking: #170. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`sample/web-js/src/jsMain/kotlin/Main.kt:1-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/web-js/src/jsMain/kotlin/Main.kt#L1-L20) — `ComposeViewport sample entrypoint`
- [`sample/web-wasm/src/wasmJsMain/kotlin/Main.kt:1-17`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/web-wasm/src/wasmJsMain/kotlin/Main.kt#L1-L17) — `ComposeViewport Wasm sample entrypoint`

### Original issue description (verbatim Markdown)
````markdown
Zooming in/out in browser: experiencing bug. View stays the same, mouse focuses wrong items.
````

### Original public discussion (1 comments)

**[MohamedRejeb](https://github.com/MohamedRejeb)** — created `2024-03-04T07:28:52Z`, updated `2024-03-04T07:28:52Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/72#issuecomment-1975890950); IDs `1975890950` / `IC_kwDOKDql7s51xbQG`.
````markdown
Thanks for reposting this issue, I'll check it out.
This is happening is Desktop right?
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/72/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/72/comments.json)
- [Full public timeline: 2 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/72/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:25:18Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/72)); [[Low][Upstream #72] Zoom in/out in browser](https://github.com/Apdelrahman1911/nativeCmpkit/issues/170).
