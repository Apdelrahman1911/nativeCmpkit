// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.toggle

import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.material3.SwitchColors
import androidx.compose.material3.LocalContentColor
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import com.mohamedrejeb.calf.ui.utils.isIOS26OrAbove

@Composable
actual fun AdaptiveSwitch(
    checked: Boolean,
    onCheckedChange: ((Boolean) -> Unit)?,
    modifier: Modifier,
    thumbContent: (@Composable () -> Unit)?,
    enabled: Boolean,
    colors: SwitchColors,
    interactionSource: MutableInteractionSource,
) {
    if (isIOS26OrAbove()) {
        LiquidGlassSwitchImpl(
            checked = checked,
            onCheckedChange = onCheckedChange,
            modifier = modifier,
            thumbContent = thumbContent?.let { content ->
                {
                    val iconColor = if (enabled) {
                        if (checked) colors.checkedIconColor else colors.uncheckedIconColor
                    } else {
                        if (checked) colors.disabledCheckedIconColor else colors.disabledUncheckedIconColor
                    }
                    CompositionLocalProvider(LocalContentColor provides iconColor) { content() }
                }
            },
            enabled = enabled,
            colors = LiquidGlassSwitchDefaults.colors(
                checkedTrackColor = colors.checkedTrackColor,
                uncheckedTrackColor = colors.uncheckedTrackColor,
                checkedThumbColor = colors.checkedThumbColor,
                uncheckedThumbColor = colors.uncheckedThumbColor,
                checkedTrackBorderColor = colors.checkedBorderColor,
                uncheckedTrackBorderColor = colors.uncheckedBorderColor,
                disabledCheckedTrackColor = colors.disabledCheckedTrackColor,
                disabledUncheckedTrackColor = colors.disabledUncheckedTrackColor,
                disabledCheckedThumbColor = colors.disabledCheckedThumbColor,
                disabledUncheckedThumbColor = colors.disabledUncheckedThumbColor,
            ),
            interactionSource = interactionSource,
            disabledCheckedTrackBorderColor = colors.disabledCheckedBorderColor,
            disabledUncheckedTrackBorderColor = colors.disabledUncheckedBorderColor,
        )
    } else {
        CupertinoSwitch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            modifier = modifier,
            thumbContent = thumbContent,
            enabled = enabled,
            colors = colors,
            interactionSource = interactionSource,
        )
    }
}
