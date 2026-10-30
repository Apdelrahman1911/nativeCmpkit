// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

class WebSettings internal constructor(
    private val onSettingsChanged: () -> Unit
) {
    var javaScriptEnabled: Boolean = false
        set(value) {
            if (field == value) return
            field = value
            notifyChanged()
        }

    var javaScriptCanOpenWindowsAutomatically = true
        set(value) {
            if (field == value) return
            field = value
            notifyChanged()
        }

    val androidSettings = AndroidSettings(::notifyChanged)

    val iosSettings = IosSettings(::notifyChanged)

    val desktopSettings = DesktopSettings(::notifyChanged)

    /** Browser isolation is independent of JavaScript execution. Defaults to an opaque origin. */
    var browserSandboxPolicy: BrowserSandboxPolicy = BrowserSandboxPolicy.Isolated
        set(value) {
            if (field == value) return
            field = value
            notifyChanged()
        }

    private var batchDepth = 0
    private var changedInBatch = false

    /** Mutate settings on the owner UI thread. Nested batches apply once, including on exceptions. */
    fun batch(update: WebSettings.() -> Unit) {
        batchDepth++
        try { update() } finally {
            batchDepth--
            if (batchDepth == 0 && changedInBatch) {
                changedInBatch = false
                onSettingsChanged()
            }
        }
    }

    private fun notifyChanged() {
        if (batchDepth > 0) changedInBatch = true else onSettingsChanged()
    }

    class AndroidSettings internal constructor(
        private val onSettingsChanged: () -> Unit
    ) {
        /**
         * Latest child-window request rejected by the mounted common Android WebView.
         * Observe this Compose state to offer an explicit application fallback. Only
         * one value is retained: no WebView, Message, URI or unbounded event list.
         * Engine-blocked requests (e.g. JavaScript disabled) never reach the handler.
         * The raw [supportMultipleWindows] false mode does not intercept requests and
         * may navigate the current view instead; it is not a child-window opt-in.
         */
        var lastPopupRejection: AndroidPopupRejection? by mutableStateOf(null)
            private set

        internal fun recordPopupRejection(isDialog: Boolean, isUserGesture: Boolean) {
            lastPopupRejection = AndroidPopupRejection(
                requestNumber = (lastPopupRejection?.requestNumber ?: 0L) + 1L,
                isDialog = isDialog,
                isUserGesture = isUserGesture,
            )
            // This is a native result, not a setting mutation. Do not reapply settings.
        }

        var supportZoom = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var textZoom = 100
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var allowContentAccess = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var allowFileAccess = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var blockNetworkImage = false
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var blockNetworkLoads = false
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var databaseEnabled = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var domStorageEnabled = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var loadsImagesAutomatically = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var useWideViewPort = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var loadWithOverviewMode = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var mediaPlaybackRequiresUserGesture = false
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        /**
         * Retained Android native setting. The default true routes child-window
         * requests to our explicit deny-only handler and [lastPopupRejection].
         * No child-window UI is implemented. False uses Android's current-view
         * fallback, not our rejection policy; it may replace the current page.
         */
        var supportMultipleWindows = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var builtInZoomControls = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var displayZoomControls = false
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var setGeolocationEnabled = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var isAlgorithmicDarkeningAllowed = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        var safeBrowsingEnabled = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

    }

    class IosSettings internal constructor(
        private val onSettingsChanged: () -> Unit
    ) {
        /**
         * Whether the WKWebView allows back/forward navigation gestures.
         */
        var allowsBackForwardNavigationGestures = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }

        /**
         * Whether inline media playback is allowed (instead of fullscreen).
         * Creation-only on iOS: set before mounting; remount with a new state to change it.
         */
        var allowsInlineMediaPlayback = true
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }
    }

    class DesktopSettings internal constructor(
        private val onSettingsChanged: () -> Unit
    ) {
        /**
         * A custom user agent string. If null, the default user agent is used.
         */
        var customUserAgent: String? = null
            set(value) {
                if (field == value) return
                field = value
                onSettingsChanged()
            }
    }
}
/**
 * Browser iframe trust policy. Neither mode bypasses cross-origin/CSP restrictions.
 * [Trusted] deliberately permits same-origin parent access when JavaScript is enabled; only use
 * it for content controlled by the host application. Changing policy affects the next navigation.
 */
enum class BrowserSandboxPolicy { Isolated, Trusted }
