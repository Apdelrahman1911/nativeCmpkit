package com.mohamedrejeb.calf.ui.timepicker

import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.SaverScope
import kotlin.test.*

class TimePickerStateContractTest {
    @Test fun rejectsInvalidHoursAndMinutes() {
        for (hour in listOf(-1, 24)) assertFailsWith<IllegalArgumentException> { AdaptiveTimePickerState(hour, 0, true) }
        for (minute in listOf(-1, 60)) assertFailsWith<IllegalArgumentException> { AdaptiveTimePickerState(0, minute, true) }
    }

    @Test fun acceptsBoundaryValues() {
        for (hour in listOf(0, 23)) for (minute in listOf(0, 59)) {
            val state = AdaptiveTimePickerState(hour, minute, false)
            assertEquals(hour, state.hour)
            assertEquals(minute, state.minute)
            assertFalse(state.is24hour)
        }
    }

    @Suppress("UNCHECKED_CAST")
    @Test fun saverRoundTripAndCorruptedInputValidation() {
        val saver = AdaptiveTimePickerState.Saver() as Saver<AdaptiveTimePickerState, Any>
        val original = AdaptiveTimePickerState(23, 59, true)
        val saved = requireNotNull(with(saver) { SaverScope { true }.save(original) })
        val restored = requireNotNull(saver.restore(saved))
        assertEquals(23, restored.hour)
        assertEquals(59, restored.minute)
        assertTrue(restored.is24hour)
        assertFailsWith<IllegalArgumentException> { saver.restore(listOf(0, 60, true)) }
    }
}
