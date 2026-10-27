<!-- nativecmpkit-upstream-sync:674932206:346 -->
<!-- source-fingerprint:b2931d46a90e97b9408a145943cf0b467106980621d34d718689d51db71669a9 -->
## Current upstream context: Calf #346

Original: [[BUG] Reentry into ignoringRedrawRequests is not allowed (WebView)](https://github.com/MohamedRejeb/Calf/issues/346) — [StefanOltmann](https://github.com/StefanOltmann); created `2025-07-24T10:18:02Z`, updated `2025-07-24T10:20:45Z`; upstream state **open**.
Original IDs: `3259354082` / `I_kwDOKDql7s7CRcvi`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.

The historical stack traces JFXPanel.initFx nested Swing event-loop reentry during Compose render. Baseline still constructs JFXPanel inside remember at line50, but the crash has not been reproduced with current Compose/Skiko/JavaFX/host versions.

**Next step:** Retain as risk/reproduction in NATIVE-018 with #39/#151; test cold/warm engine startup, composition reentry and explicit preinitialization on the correct threads.

Primary tracking: #75. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:42-57`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L42-L57) — `remember { JFXPanel() }`

### Original issue description (verbatim Markdown)
````markdown
The Desktop version sometimes throws this error for me.

```
Exception in thread "AWT-EventQueue-0" java.lang.IllegalStateException: Reentry into ignoringRedrawRequests is not allowed
	at androidx.compose.ui.viewinterop.SwingInteropContainer.postponingExecutingScheduledUpdates(SwingInteropContainer.desktop.kt:285)
	at androidx.compose.ui.scene.ComposeSceneMediator.onRender(ComposeSceneMediator.desktop.kt:598)
	at org.jetbrains.skiko.SkiaLayer.update$skiko(SkiaLayer.awt.kt:558)
	at org.jetbrains.skiko.redrawer.AWTRedrawer.update(AWTRedrawer.kt:54)
	at org.jetbrains.skiko.redrawer.MetalRedrawer$frameDispatcher$1.invokeSuspend(MetalRedrawer.kt:83)
	at org.jetbrains.skiko.redrawer.MetalRedrawer$frameDispatcher$1.invoke(MetalRedrawer.kt)
	at org.jetbrains.skiko.redrawer.MetalRedrawer$frameDispatcher$1.invoke(MetalRedrawer.kt)
	at org.jetbrains.skiko.FrameDispatcher$job$1.invokeSuspend(FrameDispatcher.kt:33)
	at kotlin.coroutines.jvm.internal.BaseContinuationImpl.resumeWith(ContinuationImpl.kt:33)
	at kotlinx.coroutines.DispatchedTask.run(DispatchedTask.kt:100)
	at java.desktop/java.awt.event.InvocationEvent.dispatch(InvocationEvent.java:318)
	at java.desktop/java.awt.EventQueue.dispatchEventImpl(EventQueue.java:773)
	at java.desktop/java.awt.EventQueue$4.run(EventQueue.java:720)
	at java.desktop/java.awt.EventQueue$4.run(EventQueue.java:714)
	at java.base/java.security.AccessController.doPrivileged(AccessController.java:400)
	at java.base/java.security.ProtectionDomain$JavaSecurityAccessImpl.doIntersectionPrivilege(ProtectionDomain.java:87)
	at java.desktop/java.awt.EventQueue.dispatchEvent(EventQueue.java:742)
	at java.desktop/java.awt.EventDispatchThread.pumpOneEventForFilters(EventDispatchThread.java:203)
	at java.desktop/java.awt.EventDispatchThread.pumpEventsForFilter(EventDispatchThread.java:124)
	at java.desktop/java.awt.EventDispatchThread.pumpEventsForHierarchy(EventDispatchThread.java:113)
	at java.desktop/java.awt.EventDispatchThread.pumpEvents(EventDispatchThread.java:109)
	at java.desktop/java.awt.EventDispatchThread.pumpEvents(EventDispatchThread.java:101)
	at java.desktop/java.awt.WaitDispatchSupport$2.run(WaitDispatchSupport.java:189)
	at java.desktop/java.awt.WaitDispatchSupport$4.run(WaitDispatchSupport.java:236)
	at java.desktop/java.awt.WaitDispatchSupport$4.run(WaitDispatchSupport.java:234)
	at java.base/java.security.AccessController.doPrivileged(AccessController.java:319)
	at java.desktop/java.awt.WaitDispatchSupport.enter(WaitDispatchSupport.java:234)
	at javafx.swing/javafx.embed.swing.JFXPanel.initFx(JFXPanel.java:257)
	at javafx.swing/javafx.embed.swing.JFXPanel.<init>(JFXPanel.java:283)
	at com.mohamedrejeb.calf.ui.web.WebView_desktopKt.WebView(WebView.desktop.kt:53)
	at com.software_rangers.base.ui.RangerBaseViewKt.RangerBaseView(RangerBaseView.kt:141)
	at com.software_rangers.base.ui.RangerBaseViewKt.RangerBaseView$lambda$8(RangerBaseView.kt)
	at androidx.compose.runtime.RecomposeScopeImpl.compose(RecomposeScopeImpl.kt:235)
	at androidx.compose.runtime.ComposerImpl.recomposeToGroupEnd(Composer.kt:2838)
	at androidx.compose.runtime.ComposerImpl.skipCurrentGroup(Composer.kt:3158)
	at androidx.compose.runtime.ComposerImpl.doCompose-aFTiNEg(Composer.kt:3706)
	at androidx.compose.runtime.ComposerImpl.recompose-aFTiNEg$runtime(Composer.kt:3648)
	at androidx.compose.runtime.CompositionImpl.recompose(Composition.kt:1002)
	at androidx.compose.runtime.Recomposer.performRecompose(Recomposer.kt:1271)
	at androidx.compose.runtime.Recomposer.access$performRecompose(Recomposer.kt:142)
	at androidx.compose.runtime.Recomposer$runRecomposeAndApplyChanges$2.invokeSuspend$lambda$21(Recomposer.kt:607)
	at androidx.compose.runtime.BroadcastFrameClock$FrameAwaiter.resume(BroadcastFrameClock.kt:56)
	at androidx.compose.runtime.BroadcastFrameClock.sendFrame(BroadcastFrameClock.kt:89)
	at androidx.compose.ui.scene.BaseComposeScene.render(BaseComposeScene.skiko.kt:174)
	at androidx.compose.ui.scene.ComposeSceneMediator.onRender$lambda$20$lambda$19(ComposeSceneMediator.desktop.kt:600)
	at androidx.compose.ui.viewinterop.SwingInteropContainer.postponingExecutingScheduledUpdates(SwingInteropContainer.desktop.kt:251)
	at androidx.compose.ui.scene.ComposeSceneMediator.onRender(ComposeSceneMediator.desktop.kt:598)
	at org.jetbrains.skiko.SkiaLayer.update$skiko(SkiaLayer.awt.kt:558)
	at org.jetbrains.skiko.redrawer.AWTRedrawer.update(AWTRedrawer.kt:54)
	at org.jetbrains.skiko.redrawer.MetalRedrawer.redrawImmediately(MetalRedrawer.kt:115)
	at org.jetbrains.skiko.SkiaLayer.tryRedrawImmediately(SkiaLayer.awt.kt:394)
	at org.jetbrains.skiko.SkiaLayer.paint(SkiaLayer.awt.kt:367)
	at androidx.compose.ui.scene.skia.WindowSkiaLayerComponent$contentComponent$1.paint(WindowSkiaLayerComponent.desktop.kt:64)
	at java.desktop/javax.swing.JComponent.paintChildren(JComponent.java:961)
	at java.desktop/javax.swing.JComponent.paint(JComponent.java:1137)
	at java.desktop/javax.swing.JLayeredPane.paint(JLayeredPane.java:586)
	at androidx.compose.ui.awt.JLayeredPaneWithTransparencyHack.paint(Utils.desktop.kt:142)
	at java.desktop/javax.swing.JComponent.paintChildren(JComponent.java:961)
	at java.desktop/javax.swing.JComponent.paint(JComponent.java:1137)
	at java.desktop/javax.swing.JComponent.paintChildren(JComponent.java:961)
	at java.desktop/javax.swing.JComponent.paint(JComponent.java:1137)
	at java.desktop/javax.swing.JLayeredPane.paint(JLayeredPane.java:586)
	at java.desktop/javax.swing.JComponent.paintChildren(JComponent.java:961)
	at java.desktop/javax.swing.JComponent.paintToOffscreen(JComponent.java:5331)
	at java.desktop/javax.swing.RepaintManager$PaintManager.paintDoubleBufferedImpl(RepaintManager.java:1656)
	at java.desktop/javax.swing.RepaintManager$PaintManager.paintDoubleBuffered(RepaintManager.java:1631)
	at java.desktop/javax.swing.RepaintManager$PaintManager.paint(RepaintManager.java:1569)
	at java.desktop/javax.swing.RepaintManager.paint(RepaintManager.java:1336)
	at java.desktop/javax.swing.JComponent.paint(JComponent.java:1114)
	at java.desktop/java.awt.GraphicsCallback$PaintCallback.run(GraphicsCallback.java:39)
	at java.desktop/sun.awt.SunGraphicsCallback.runOneComponent(SunGraphicsCallback.java:75)
	at java.desktop/sun.awt.SunGraphicsCallback.runComponents(SunGraphicsCallback.java:112)
	at java.desktop/java.awt.Container.paint(Container.java:2005)
	at java.desktop/java.awt.Window.paint(Window.java:3964)
	at java.desktop/javax.swing.RepaintManager$4.run(RepaintManager.java:889)
	at java.desktop/javax.swing.RepaintManager$4.run(RepaintManager.java:861)
	at java.base/java.security.AccessController.doPrivileged(AccessController.java:400)
	at java.base/java.security.ProtectionDomain$JavaSecurityAccessImpl.doIntersectionPrivilege(ProtectionDomain.java:87)
	at java.desktop/javax.swing.RepaintManager.paintDirtyRegions(RepaintManager.java:861)
	at java.desktop/javax.swing.RepaintManager.paintDirtyRegions(RepaintManager.java:834)
	at java.desktop/javax.swing.RepaintManager.prePaintDirtyRegions(RepaintManager.java:784)
	at java.desktop/javax.swing.RepaintManager$ProcessingRunnable.run(RepaintManager.java:1897)
	at java.desktop/java.awt.event.InvocationEvent.dispatch(InvocationEvent.java:318)
	at java.desktop/java.awt.EventQueue.dispatchEventImpl(EventQueue.java:773)
	at java.desktop/java.awt.EventQueue$4.run(EventQueue.java:720)
	at java.desktop/java.awt.EventQueue$4.run(EventQueue.java:714)
	at java.base/java.security.AccessController.doPrivileged(AccessController.java:400)
	at java.base/java.security.ProtectionDomain$JavaSecurityAccessImpl.doIntersectionPrivilege(ProtectionDomain.java:87)
	at java.desktop/java.awt.EventQueue.dispatchEvent(EventQueue.java:742)
	at java.desktop/java.awt.EventDispatchThread.pumpOneEventForFilters(EventDispatchThread.java:203)
	at java.desktop/java.awt.EventDispatchThread.pumpEventsForFilter(EventDispatchThread.java:124)
	at java.desktop/java.awt.EventDispatchThread.pumpEventsForHierarchy(EventDispatchThread.java:113)
	at java.desktop/java.awt.EventDispatchThread.pumpEvents(EventDispatchThread.java:109)
	at java.desktop/java.awt.EventDispatchThread.pumpEvents(EventDispatchThread.java:101)
	at java.desktop/java.awt.EventDispatchThread.run(EventDispatchThread.java:90)
```
````

### Original public discussion (0 comments)
No public conversation comments were returned in this snapshot.

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/346/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/346/comments.json)
- [Full public timeline: 2 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/source/issues/346/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261027T193135Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2025-07-24T10:20:45Z`: `renamed` by [StefanOltmann](https://github.com/StefanOltmann) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/18792358958)).
- `2026-10-24T16:19:11Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/346)); [[Medium][NATIVE-018] Desktop initializes JFXPanel during composition despite historical nested-event-loop crashes](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75).
