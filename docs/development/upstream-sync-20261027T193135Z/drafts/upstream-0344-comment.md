<!-- nativecmpkit-upstream-sync:674932206:344 -->
<!-- source-fingerprint:f1eff7e147d05b67dc047753f038fc0b1acd1715e53cbe2725a229418c9004ff -->
## Current upstream context: Calf #344

Original: [[BUG] WebView throwing error on configuration](https://github.com/MohamedRejeb/Calf/issues/344) — [StefanOltmann](https://github.com/StefanOltmann); created `2025-07-22T09:14:46Z`, updated `2025-07-24T10:19:43Z`; upstream state **open**.
Original IDs: `3251836511` / `I_kwDOKDql7s7B0xZf`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Source-addressed historical request; not a new confirmed bug, and not evidence of a device/runtime pass.

The historical stack shows direct JavaFX settings writes on AWT-EventQueue. Baseline applySettings now wraps writes in Platform.runLater at lines215-221, so this specific cause is source-addressed. That does not prove all current JavaFX lifecycle/thread paths are correct.

**Next step:** Keep a settings-on-EDT regression test in the desktop matrix; do not recreate the old wrong-thread-settings bug as confirmed. Track distinct startup/lifecycle risks through NATIVE-018/NATIVE-002.

Primary tracking: #75. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:200-221`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L200-L221) — `WebViewState.applySetting / WebView.applySettings`

### Original issue description (verbatim Markdown)
````markdown
Hi,

I encountered this Exception while trying to set properties to the WebView:

```
Exception in thread "AWT-EventQueue-0" java.lang.IllegalStateException: Not on FX application thread; currentThread = AWT-EventQueue-0
	at javafx.graphics/com.sun.javafx.tk.Toolkit.checkFxUserThread(Toolkit.java:294)
	at javafx.graphics/com.sun.javafx.tk.quantum.QuantumToolkit.checkFxUserThread(QuantumToolkit.java:481)
	at javafx.web/javafx.scene.web.WebEngine.checkThread(WebEngine.java:1220)
	at javafx.web/javafx.scene.web.WebEngine$1.invalidated(WebEngine.java:486)
	at javafx.base/javafx.beans.property.BooleanPropertyBase.markInvalid(BooleanPropertyBase.java:110)
	at javafx.base/javafx.beans.property.BooleanPropertyBase.set(BooleanPropertyBase.java:145)
	at javafx.web/javafx.scene.web.WebEngine.setJavaScriptEnabled(WebEngine.java:475)
	at com.mohamedrejeb.calf.ui.web.WebView_desktopKt.applySettings(WebView.desktop.kt:173)
```

We use the WebView like this in `commonMain` code:
```
val webViewState = rememberWebViewState(url)

LaunchedEffect(Unit) {

    webViewState.settings.javaScriptEnabled = true
    webViewState.settings.androidSettings.supportZoom = true
}

WebView(
    state = webViewState,
    modifier = Modifier.fillMaxSize()
)
```

What is the correct way to configure the WebView?

I assume that `Platform.runLater()` needs to be used, but I can't to that from `commonMain`.

What can I do to avoid this issue?
````

### Original public discussion (2 comments)

**[StefanOltmann](https://github.com/StefanOltmann)** — created `2025-07-24T06:15:31Z`, updated `2025-07-24T06:15:31Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/344#issuecomment-3112169108); IDs `3112169108` / `IC_kwDOKDql7s65f-6U`.
````markdown
@MohamedRejeb Would you consider the Desktop WebView as production ready or is it more experimental state?

Sometimes I get some other weird errors, too.
````

**[StefanOltmann](https://github.com/StefanOltmann)** — created `2025-07-24T09:03:08Z`, updated `2025-07-24T09:03:08Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/344#issuecomment-3112654147); IDs `3112654147` / `IC_kwDOKDql7s65h1VD`.
````markdown
Are settings only to be applied in `LaunchedEffect(state.isLoading)`?

Can there be a way to inject settings right in `rememberWebViewState()` to avoid these issues? 
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/344/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/344/comments.json)
- [Full public timeline: 6 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/344/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2025-07-24T10:19:43Z`: `renamed` by [StefanOltmann](https://github.com/StefanOltmann) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/18792341732)).
- `2026-10-24T16:19:11Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/344)); [[Medium][NATIVE-018] Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75).
