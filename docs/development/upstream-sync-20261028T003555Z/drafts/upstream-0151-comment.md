<!-- nativecmpkit-upstream-sync:674932206:151 -->
<!-- source-fingerprint:f3149619619b9bd31457736d23c64efe6b9fc57fa874fdd75758e8194ef5e812 -->
## Current upstream context: Calf #151

Original: [Webview not work on Linux](https://github.com/MohamedRejeb/Calf/issues/151) — [AnthonyGambache](https://github.com/AnthonyGambache); created `2024-08-17T19:17:19Z`, updated `2024-08-17T19:17:19Z`; upstream state **open**.
Original IDs: `2471638473` / `I_kwDOKDql7s6TUjXJ`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.

Ubuntu24.04 JavaFX QuantumRenderer startup failure is a credible historical report but has not been reproduced in the current baseline environment. Native-feature startup risk and host classifier/build investigation cover it; it is not a second confirmed root cause.

**Next step:** Retest packaged JavaFX19 on clean Ubuntu/display/CPU combinations and collect rendering-native-dependency evidence; consolidate with #39/#346.

Primary tracking: #75. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:42-57`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L42-L57) — `WebView/JFXPanel initialization`
- [`calf-webview/build.gradle.kts:9-18,41-49`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/build.gradle.kts#L9-L18) — `host classifier and JavaFX dependencies`

### Original issue description (verbatim Markdown)
````markdown
Hi,
I tried to make a webview work on linux (Ubuntu 24.04), but I get the following error: 

```
août 17, 2024 10:14:58 PM com.sun.javafx.application.PlatformImpl startup
AVERTISSEMENT: Unsupported JavaFX configuration: classes were loaded from 'unnamed module @692ee343'
Graphics Device initialization failed for :  es2, sw
Error initializing QuantumRenderer: no suitable pipeline found
java.lang.RuntimeException: java.lang.RuntimeException: Error initializing QuantumRenderer: no suitable pipeline found
	at com.sun.javafx.tk.quantum.QuantumRenderer.getInstance(QuantumRenderer.java:283)
	at com.sun.javafx.tk.quantum.QuantumToolkit.init(QuantumToolkit.java:253)
	at com.sun.javafx.tk.Toolkit.getToolkit(Toolkit.java:268)
	at com.sun.javafx.application.PlatformImpl.startup(PlatformImpl.java:291)
	at com.sun.javafx.application.PlatformImpl.startup(PlatformImpl.java:163)
	at javafx.embed.swing.JFXPanel.lambda$initFx$1(JFXPanel.java:225)
	at java.base/java.lang.Thread.run(Thread.java:840)
Caused by: java.lang.RuntimeException: Error initializing QuantumRenderer: no suitable pipeline found
	at com.sun.javafx.tk.quantum.QuantumRenderer$PipelineRunnable.init(QuantumRenderer.java:95)
	at com.sun.javafx.tk.quantum.QuantumRenderer$PipelineRunnable.run(QuantumRenderer.java:125)
	... 1 more
Caused by: java.lang.RuntimeException: Error initializing QuantumRenderer: no suitable pipeline found

Exception in thread "main" java.lang.RuntimeException: No toolkit found
	at com.sun.javafx.tk.Toolkit.getToolkit(Toolkit.java:280)
	at com.sun.javafx.application.PlatformImpl.startup(PlatformImpl.java:291)
	at com.sun.javafx.application.PlatformImpl.startup(PlatformImpl.java:163)
	at javafx.embed.swing.JFXPanel.lambda$initFx$1(JFXPanel.java:225)
	at java.base/java.lang.Thread.run(Thread.java:840)

> Task :composeApp:run FAILED
```
````

### Original public discussion (0 comments)
No public conversation comments were returned in this snapshot.

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/source/issues/151/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/source/issues/151/comments.json)
- [Full public timeline: 1 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/source/issues/151/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:19:11Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/151)); [[Medium][NATIVE-018] Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75).
