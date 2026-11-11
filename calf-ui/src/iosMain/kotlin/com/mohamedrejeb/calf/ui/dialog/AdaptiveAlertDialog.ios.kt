package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosActionStyle
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosStyle
import com.mohamedrejeb.calf.ui.dialog.uikit.LocalAlertDialogIosPopoverAnchor

@OptIn(InternalCalfApi::class)
@Composable
actual fun AdaptiveAlertDialog(
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
    confirmText: String,
    dismissText: String?,
    title: String,
    text: String,
    materialConfirmButton: @Composable (() -> Unit)?,
    materialDismissButton: @Composable (() -> Unit)?,
    materialIcon: @Composable (() -> Unit)?,
    materialTitle: @Composable (() -> Unit)?,
    materialText: @Composable (() -> Unit)?,
    shape: Shape,
    containerColor: Color,
    iconContentColor: Color,
    titleContentColor: Color,
    textContentColor: Color,
    tonalElevation: Dp,
    iosDialogStyle: AlertDialogIosStyle,
    iosConfirmButtonStyle: AlertDialogIosActionStyle,
    iosDismissButtonStyle: AlertDialogIosActionStyle,
    iosConfirmButtonIsPreferred: Boolean,
    properties: DialogProperties,
    modifier: Modifier,
) {
    val currentUIViewController = LocalUIViewController.current
    val layoutDirection = LocalLayoutDirection.current
    val popoverAnchor = LocalAlertDialogIosPopoverAnchor.current

    fun createIosDialogProperties(): AlertDialogIosProperties {
        return AlertDialogIosProperties(
            title = title,
            text = text,
            style = iosDialogStyle,
            actions = adaptiveAlertDialogIosActions(
                confirmText = confirmText,
                dismissText = dismissText,
                onConfirm = onConfirm,
                onDismiss = onDismiss,
                confirmStyle = iosConfirmButtonStyle,
                dismissStyle = iosDismissButtonStyle,
                confirmIsPreferred = iosConfirmButtonIsPreferred,
            ),
        )
    }

    val alertDialogManager = remember(currentUIViewController) {
        AlertDialogManager(
            parentUIViewController = currentUIViewController,
            onDismissRequest = onConfirm,
            iosProperties = createIosDialogProperties(),
            properties = properties,
            layoutDirection = layoutDirection,
        ).also {
            it.popoverAnchor = popoverAnchor
        }
    }

    LaunchedEffect(
        onConfirm,
        onDismiss,
        confirmText,
        dismissText,
        title,
        text,
        iosDialogStyle,
        iosConfirmButtonStyle,
        iosDismissButtonStyle,
        iosConfirmButtonIsPreferred,
        properties,
        layoutDirection,
        popoverAnchor,
    ) {
        alertDialogManager.onDismissRequest = onDismiss
        alertDialogManager.iosProperties = createIosDialogProperties()
        alertDialogManager.properties = properties
        alertDialogManager.layoutDirection = layoutDirection
        alertDialogManager.popoverAnchor = popoverAnchor
        alertDialogManager.updateDialogProperties()
    }

    DisposableEffect(Unit) {
        alertDialogManager.showAlertDialog()

        onDispose {
            alertDialogManager.dismiss()
        }
    }
}

@OptIn(InternalCalfApi::class)
@Composable
actual fun AdaptiveBasicAlertDialog(
    onDismissRequest: () -> Unit,
    modifier: Modifier,
    iosProperties: AlertDialogIosProperties,
    properties: DialogProperties,
    materialContent: @Composable () -> Unit,
) {
    val currentUIViewController = LocalUIViewController.current
    val layoutDirection = LocalLayoutDirection.current
    val popoverAnchor = LocalAlertDialogIosPopoverAnchor.current

    val alertDialogManager = remember(currentUIViewController) {
        AlertDialogManager(
            parentUIViewController = currentUIViewController,
            onDismissRequest = onDismissRequest,
            iosProperties = iosProperties,
            properties = properties,
            layoutDirection = layoutDirection,
        ).also {
            it.popoverAnchor = popoverAnchor
        }
    }

    LaunchedEffect(onDismissRequest, iosProperties, properties, layoutDirection, popoverAnchor) {
        alertDialogManager.onDismissRequest = onDismissRequest
        alertDialogManager.iosProperties = iosProperties
        alertDialogManager.properties = properties
        alertDialogManager.layoutDirection = layoutDirection
        alertDialogManager.popoverAnchor = popoverAnchor
        alertDialogManager.updateDialogProperties()
    }

    DisposableEffect(Unit) {
        alertDialogManager.showAlertDialog()

        onDispose {
            alertDialogManager.dismiss()
        }
    }
}
