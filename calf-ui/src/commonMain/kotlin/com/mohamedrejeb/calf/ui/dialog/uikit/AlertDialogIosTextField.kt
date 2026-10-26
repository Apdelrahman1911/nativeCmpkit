// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.dialog.uikit

import com.mohamedrejeb.calf.ui.uikit.IosKeyboardType

/**
 * Represents a text field in an iOS alert dialog.
 *
 * @param placeholder The placeholder of the text field.
 * @param initialValue The initial value of the text field when its native controller is created.
 * This is not a controlled text property; changing it does not overwrite in-progress user input.
 * @param keyboardType The keyboard type of the text field.
 * @param isSecure Indicates whether the text field is secure or not.
 * @param onValueChange The lambda that is invoked when the text field value changes.
 *
 *
 * See [UITextField](https://developer.apple.com/documentation/uikit/uitextfield?language=objc)
 */
data class AlertDialogIosTextField(
    val placeholder: String = "",
    val initialValue: String = "",
    val keyboardType: IosKeyboardType = IosKeyboardType.Default,
    val isSecure: Boolean = false,
    val onValueChange: (String) -> Unit,
)
