@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import kotlinx.cinterop.CValue
import platform.CoreGraphics.CGSize
import platform.UIKit.UIDatePicker
import platform.UIKit.UIView

/**
 * Owns the compact field's background without depending on UIDatePicker's
 * style-specific background setter. The real system control still owns input,
 * selection, accessibility and its popover; no private subviews are modified.
 */
internal class CompactDatePickerContainer(val picker: UIDatePicker) : UIView(frame = picker.frame) {
    init {
        addSubview(picker)
    }

    // DatePickerManager remeasures on selection changes. Delegate to the actual
    // control instead of UIView's empty default sizeThatFits implementation.
    override fun sizeThatFits(size: CValue<CGSize>): CValue<CGSize> = picker.sizeThatFits(size)

    override fun layoutSubviews() {
        super.layoutSubviews()
        picker.setFrame(bounds)
    }
}
