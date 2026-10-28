package nativecmpkit.consumer

import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.awt.ComposePanel
import com.mohamedrejeb.calf.ui.web.JavascriptResult
import com.mohamedrejeb.calf.ui.web.LoadingState
import com.mohamedrejeb.calf.ui.web.WebContent
import com.mohamedrejeb.calf.ui.web.WebView
import com.mohamedrejeb.calf.ui.web.WebViewState
import com.mohamedrejeb.calf.ui.web.evaluateJavascriptResult
import com.mohamedrejeb.calf.ui.web.isDesktopWebViewAvailable
import javafx.application.Platform
import javafx.embed.swing.JFXPanel
import java.awt.Component
import java.awt.Container
import java.awt.GraphicsEnvironment
import java.nio.file.Files
import java.nio.file.Path
import java.security.MessageDigest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.FutureTask
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import javax.swing.JFrame
import javax.swing.SwingUtilities
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Independent Maven consumer: public Compose API and an actual attached JavaFX WebEngine. */
class PublishedWebViewConsumerTest {
    @Test fun loadedPublicClassesComeFromTheExactStagedJar() {
        for (type in listOf(WebViewState::class.java, WebContent::class.java, JavascriptResult::class.java)) {
            val location = assertNotNull(type.protectionDomain.codeSource?.location)
            assertEquals("file", location.protocol)
            val jar = Path.of(location.toURI())
            assertTrue(Files.isRegularFile(jar), "Loose producer classes must not satisfy a Maven consumer")
            assertEquals(System.getProperty("nativecmpkit.expected.webview.name"), jar.fileName.toString())
            val digest = MessageDigest.getInstance("SHA-256")
            Files.newInputStream(jar).use { stream ->
                val buffer = ByteArray(64 * 1024)
                while (true) {
                    val count = stream.read(buffer)
                    if (count < 0) break
                    digest.update(buffer, 0, count)
                }
            }
            assertEquals(assertNotNull(System.getProperty("nativecmpkit.expected.webview.sha256")),
                digest.digest().joinToString("") { "%02x".format(it) })
        }
    }

    // Compose 1.12.0 marks the panel's explicit disposal API experimental.
    // Retain real owner cleanup rather than omitting it to compile the fixture.
    @OptIn(ExperimentalComposeUiApi::class)
    @Test fun publicComposableLoadsEvaluatesAndReleasesTheRealNativeView() {
        assertTrue(!GraphicsEnvironment.isHeadless(), "A real graphical session is required; no assumption skip")
        assertTrue(isDesktopWebViewAvailable(), "The consuming host must supply its own JavaFX runtime")
        val state = WebViewState(WebContent.Data("<html><title>NativeCmpKit 消費者</title><body>native consumer</body></html>"))
        state.settings.javaScriptEnabled = true
        val created = AtomicInteger()
        val disposed = AtomicInteger()
        val panel = onEdt { ComposePanel() }
        val frame = onEdt {
            JFrame("NativeCmpKit packaged WebView verification").apply {
                defaultCloseOperation = JFrame.DISPOSE_ON_CLOSE
                contentPane.add(panel)
                setSize(480, 320)
            }
        }
        try {
            onEdt {
                panel.setContent { WebView(state, onCreated = { created.incrementAndGet() }, onDispose = { disposed.incrementAndGet() }) }
                frame.isVisible = true
            }
            awaitCondition("Public WebView creation") { created.get() == 1 }
            awaitCondition("Real attached Swing/JavaFX panel") { onEdt { nativePanels(frame).singleOrNull()?.isShowing == true } }
            val actualPanel = onEdt { nativePanels(frame).single() }
            awaitCondition("Real native HTML load") {
                onFx {
                    state.loadingState == LoadingState.Finished && state.pageTitle == "NativeCmpKit 消費者" &&
                        state.webView?.engine?.executeScript("document.title") == "NativeCmpKit 消費者"
                }
            }
            onEdt { assertTrue(frame.isShowing && panel.isShowing) }
            val actualView = onFx { assertNotNull(state.webView) }
            onFx { assertEquals(actualView.scene, assertNotNull(actualPanel.scene)) }
            assertEquals(JavascriptResult.Value("{\"answer\":42}"), evaluate(state, "({answer:42})"))
            assertEquals(JavascriptResult.Value("null"), evaluate(state, "null"))
            assertEquals(JavascriptResult.Undefined, evaluate(state, "undefined"))
            assertIs<JavascriptResult.Error>(evaluate(state, "throw new Error('intentional consumer check')"))
            assertEquals(1, created.get())
            onEdt { panel.setContent { } }
            awaitCondition("Public composable disposal") { disposed.get() == 1 && onFx { state.webView == null } }
            // A caller retaining a Node also retains its Scene root. Inspect the
            // actual embedding panel's ownership, not an invented Node.scene contract.
            onFx { assertNull(actualPanel.scene, "Disposal must release the actual embedding Scene") }
            assertIs<JavascriptResult.Unavailable>(evaluate(state, "1"))
            assertEquals(1, disposed.get())
        } finally {
            // The fixture owns this panel/window only, not the process-global JavaFX toolkit.
            onEdt { panel.dispose(); frame.dispose() }
        }
        awaitCondition("Native owner teardown") { state.webView == null && disposed.get() == 1 }
        onEdt { assertTrue(!frame.isDisplayable) }
    }

    private fun evaluate(state: WebViewState, script: String): JavascriptResult {
        val result = AtomicReference<JavascriptResult>()
        val callbacks = AtomicInteger()
        val completed = CountDownLatch(1)
        onEdt {
            state.evaluateJavascriptResult(script) {
                result.set(it)
                callbacks.incrementAndGet()
                completed.countDown()
            }
        }
        assertTrue(completed.await(15, TimeUnit.SECONDS), "Public evaluation callback must complete")
        onFx { } // Drain work queued by this evaluation before checking exactly-once delivery.
        assertEquals(1, callbacks.get())
        return assertNotNull(result.get())
    }

    private fun awaitCondition(description: String, ready: () -> Boolean) {
        val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(30)
        while (!ready()) {
            assertTrue(System.nanoTime() < deadline, "$description timed out")
            Thread.sleep(10)
        }
    }

    private fun nativePanels(component: Component): List<JFXPanel> = when (component) {
        is JFXPanel -> listOf(component)
        is Container -> component.components.flatMap { nativePanels(it) }
        else -> emptyList()
    }

    private fun <T> onEdt(action: () -> T): T {
        if (SwingUtilities.isEventDispatchThread()) return action()
        val task = FutureTask(action)
        SwingUtilities.invokeLater(task)
        return task.get(15, TimeUnit.SECONDS)
    }

    private fun <T> onFx(action: () -> T): T {
        if (Platform.isFxApplicationThread()) return action()
        val task = FutureTask(action)
        Platform.runLater(task)
        return task.get(15, TimeUnit.SECONDS)
    }
}
