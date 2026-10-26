@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.navigation

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.*
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.UIKitInteropInteractionMode
import androidx.compose.ui.viewinterop.UIKitInteropProperties
import androidx.compose.ui.viewinterop.UIKitView
import kotlinx.cinterop.useContents
import platform.CoreGraphics.CGRectMake
import platform.CoreGraphics.CGSizeMake
import platform.UIKit.UITraitCollection
import platform.UIKit.UIView

/** Layout-scoped native bar, never attached directly to a screen's root controller. */
internal class NativeBarHost(private val bar: UIView) : UIView(frame = CGRectMake(0.0, 0.0, 0.0, 0.0)) {
    var onMeasuredHeight: ((Double) -> Unit)? = null
    private var lastHeight = 0.0

    init { addSubview(bar) }

    override fun layoutSubviews() {
        super.layoutSubviews()
        bar.setFrame(bounds)
        val height = bar.sizeThatFits(bounds.useContents { CGSizeMake(size.width, size.height) }).useContents { height }
        if (height.isFinite() && height > 0 && height != lastHeight) {
            lastHeight = height
            onMeasuredHeight?.invoke(height)
        }
    }

    override fun safeAreaInsetsDidChange() {
        super.safeAreaInsetsDidChange()
        setNeedsLayout()
    }

    override fun traitCollectionDidChange(previousTraitCollection: UITraitCollection?) {
        super.traitCollectionDidChange(previousTraitCollection)
        invalidateMeasurement()
    }

    fun invalidateMeasurement() {
        bar.invalidateIntrinsicContentSize()
        bar.setNeedsLayout()
        setNeedsLayout()
    }
}

@OptIn(ExperimentalComposeUiApi::class)
@Composable
internal fun NativeBar(bar: UIView, initialHeight: Dp, modifier: Modifier) {
    var height by remember(bar) { mutableStateOf(initialHeight) }
    val host = remember(bar) { NativeBarHost(bar) }
    DisposableEffect(host) {
        host.onMeasuredHeight = { height = it.dp }
        onDispose { host.onMeasuredHeight = null }
    }
    SideEffect { host.invalidateMeasurement() }
    key(host) {
        UIKitView(
            factory = { host },
            modifier = modifier.fillMaxWidth().height(height),
            properties = UIKitInteropProperties(
                interactionMode = UIKitInteropInteractionMode.NonCooperative,
                isNativeAccessibilityEnabled = true,
            ),
        )
    }
}
