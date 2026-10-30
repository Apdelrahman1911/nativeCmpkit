// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import android.os.Handler
import android.os.Looper
import android.os.Message
import android.webkit.WebView
import androidx.test.core.app.ApplicationProvider
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows
import org.robolectric.annotation.Config
import kotlin.test.*

/** Real production handler/state with a shadow engine, not popup UI/native input. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], manifest = Config.NONE)
class AndroidPopupRejectionTest {
    @Test fun unattachedOrUninitializedHandlerRejectsWithoutTouchingTheTransport() {
        val native = WebView(ApplicationProvider.getApplicationContext())
        var transportDeliveries = 0
        val message = Message.obtain(Handler(Looper.getMainLooper()) { transportDeliveries++; true })
        try {
            val client = AccompanistWebChromeClient()
            assertFalse(client.onCreateWindow(native, false, true, message))
            val state = WebViewState(WebContent.NavigatorOnly)
            client.state = state
            assertFalse(client.onCreateWindow(native, true, false, message))
            assertNull(state.settings.androidSettings.lastPopupRejection)
            Shadows.shadowOf(Looper.getMainLooper()).idle()
            assertEquals(0, transportDeliveries)
            assertNull((message.obj as? WebView.WebViewTransport)?.webView)
        } finally { message.recycle(); native.destroy() }
    }

    @Test fun repeatedRejectionsRetainOnlyTheLatestValueWithoutReapplyingSettings() {
        var settingChanges = 0
        val settings = WebSettings { settingChanges++ }
        assertTrue(settings.androidSettings.supportMultipleWindows)
        for (request in 1L..1_000L) {
            settings.androidSettings.recordPopupRejection(isDialog = request % 2L == 0L, isUserGesture = request % 3L == 0L)
            assertEquals(AndroidPopupRejection(request, request % 2L == 0L, request % 3L == 0L),
                settings.androidSettings.lastPopupRejection)
        }
        assertEquals(0, settingChanges, "A native result must not trigger a settings update or a new window")
        settings.androidSettings.supportMultipleWindows = false
        assertEquals(1, settingChanges)
        assertEquals(1_000L, settings.androidSettings.lastPopupRejection?.requestNumber)
    }

    @Test fun staleNativeRequestsCannotOverwriteTheReplacementOwnersResult() {
        val first = WebView(ApplicationProvider.getApplicationContext())
        val current = WebView(ApplicationProvider.getApplicationContext())
        val owner = WebViewState(WebContent.NavigatorOnly)
        val client = AccompanistWebChromeClient().apply { state = owner }
        try {
            owner.webView = first
            assertFalse(client.onCreateWindow(first, false, true, null))
            assertEquals(AndroidPopupRejection(1L, false, true), owner.settings.androidSettings.lastPopupRejection)
            owner.webView = current
            assertFalse(client.onCreateWindow(first, true, false, null))
            assertEquals(AndroidPopupRejection(1L, false, true), owner.settings.androidSettings.lastPopupRejection)
            assertFalse(client.onCreateWindow(current, true, false, null))
            assertEquals(AndroidPopupRejection(2L, true, false), owner.settings.androidSettings.lastPopupRejection)
            owner.webView = null
            assertFalse(client.onCreateWindow(current, false, true, null))
            assertEquals(AndroidPopupRejection(2L, true, false), owner.settings.androidSettings.lastPopupRejection)
        } finally { owner.webView = null; first.destroy(); current.destroy() }
    }
}
