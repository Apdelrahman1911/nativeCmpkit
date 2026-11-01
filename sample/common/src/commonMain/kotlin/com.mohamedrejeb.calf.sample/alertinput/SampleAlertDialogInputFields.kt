// SPDX-License-Identifier: Apache-2.0
// Original Calf authors (MohamedRejeb/Calf); preserved LICENSE/NOTICE govern this extraction.
// Source extracted from the attributed Calf sample; descriptor/callback bytes preserved.
// Modified for NativeCmpKit (2026-11-01): isolated test-only source seam; no sample app substitute.
package com.mohamedrejeb.calf.sample.alertinput

import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosTextField
import com.mohamedrejeb.calf.ui.uikit.IosKeyboardType

/** The unchanged two native alert input descriptors used by the real sample screen. */
internal fun sampleAlertDialogInputFields(): List<AlertDialogIosTextField> = listOf(
                AlertDialogIosTextField(
                    placeholder = "Enter your name",
                    initialValue = "John Doe",
                    keyboardType = IosKeyboardType.EmailAddress,
                    isSecure = false,
                    onValueChange = {
                        // Demonstration only: do not log or persist personal input.
                    }
                ),
                AlertDialogIosTextField(
                    placeholder = "Enter your password",
                    keyboardType = IosKeyboardType.NumberPad,
                    initialValue = "",
                    isSecure = true,
                    onValueChange = {
                        // Secure input must never be written to logs or retained by this demo.
                    }
                ),
            )
