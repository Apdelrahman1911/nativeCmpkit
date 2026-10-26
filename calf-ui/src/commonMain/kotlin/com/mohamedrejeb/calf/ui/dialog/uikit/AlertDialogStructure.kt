package com.mohamedrejeb.calf.ui.dialog.uikit

/** UIKit action titles/styles and field structure cannot be replaced in a presented controller. */
internal fun AlertDialogIosProperties.structure(): List<Any> = listOf(
    style,
    severity,
    actions.map { it.title to it.style },
    textFields.map { listOf(it.placeholder, it.keyboardType, it.isSecure) },
)
