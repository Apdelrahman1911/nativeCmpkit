package com.mohamedrejeb.calf.ui.slider

import kotlin.math.floor

/** One numeric contract for pointer, keyboard and accessibility input on the iOS sliders. */
internal class SliderValueDomain(
    val range: ClosedFloatingPointRange<Float>,
    val steps: Int,
) {
    init {
        require(range.start.isFinite() && range.endInclusive.isFinite()) {
            "Slider valueRange endpoints must be finite"
        }
        require(range.start <= range.endInclusive) { "Slider valueRange must not be reversed" }
        require(steps >= 0) { "steps should be >= 0" }
    }

    // Double intermediates also support finite Float endpoints whose difference overflows Float.
    private val start = range.start.toDouble()
    private val span = range.endInclusive.toDouble() - start
    val isConstant: Boolean get() = span == 0.0

    fun coerce(value: Float): Float {
        require(value.isFinite()) { "Slider value must be finite" }
        return value.coerceIn(range)
    }

    fun fraction(value: Float): Float =
        if (isConstant) 0f else ((coerce(value).toDouble() - start) / span).toFloat()

    fun valueAt(fraction: Float): Float {
        require(fraction.isFinite()) { "Slider fraction must be finite" }
        return (start + span * fraction.coerceIn(0f, 1f)).toFloat().coerceIn(range)
    }

    /** Nearest allowed value; exact ties consistently choose the greater value. No tick allocation. */
    fun snap(value: Float): Float {
        val coerced = coerce(value)
        if (steps == 0 || isConstant) return coerced
        val intervals = steps.toDouble() + 1.0
        val index = floor((coerced.toDouble() - start) / span * intervals + 0.5)
        return (start + span * (index / intervals)).toFloat().coerceIn(range)
    }

    fun offsetValue(x: Float, width: Int, thumbWidth: Int, isRtl: Boolean): Float {
        val halfThumb = (thumbWidth.coerceAtLeast(0) / 2f).coerceAtMost(width.coerceAtLeast(0) / 2f)
        val trackWidth = width - 2f * halfThumb
        if (trackWidth <= 0f || !x.isFinite()) return range.start
        val fraction = ((x - halfThumb) / trackWidth).coerceIn(0f, 1f)
        return snap(valueAt(if (isRtl) 1f - fraction else fraction))
    }

    fun keyboardValue(value: Float, direction: Int, page: Boolean = false): Float {
        val intervals = if (steps == 0) 100.0 else steps.toDouble() + 1.0
        val delta = span / intervals * direction * if (page) 10 else 1
        return snap((coerce(value).toDouble() + delta).coerceIn(start, start + span).toFloat())
    }
}

/** Dense steps retain snapping/semantics but omit indistinguishable tick marks instead of allocating O(steps). */
internal fun sliderTickFractions(steps: Int): FloatArray =
    if (steps == 0 || steps > 1_000) floatArrayOf()
    else FloatArray(steps + 2) { it.toFloat() / (steps + 1) }
