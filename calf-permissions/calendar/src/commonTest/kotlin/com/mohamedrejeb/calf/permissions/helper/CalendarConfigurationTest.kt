package com.mohamedrejeb.calf.permissions.helper

import kotlin.test.*

/** New configuration regressions only; the five previously accepted capability-policy methods are not replayed. */
class CalendarConfigurationTest {
    @Test fun everyRequestKindRequiresItsOwnExactPurposeKey() {
        assertEquals("NSCalendarsUsageDescription", calendarUsageDescriptionKey(CalendarRequestKind.Legacy))
        assertEquals("NSCalendarsFullAccessUsageDescription", calendarUsageDescriptionKey(CalendarRequestKind.FullAccess))
        assertEquals("NSCalendarsWriteOnlyAccessUsageDescription", calendarUsageDescriptionKey(CalendarRequestKind.WriteOnly))
        assertEquals(3, CalendarRequestKind.entries.map(::calendarUsageDescriptionKey).toSet().size)
    }

    @Test fun absentBlankAndNonStringPurposeValuesCannotAuthorizeANativeRequest() {
        listOf(null, "", " ", "\n\t", "\u2003", false, 17, listOf("purpose"), mapOf("purpose" to "value"))
            .forEach { assertFalse(calendarUsageDescriptionValid(it)) }
        listOf("Add selected events", "  Ajouter les événements choisis  ", "カレンダーに予定を追加します")
            .forEach { assertTrue(calendarUsageDescriptionValid(it)) }
    }

    @Test fun aDifferentAccessKeyCannotSatisfyTheSelectedRequest() {
        for (kind in CalendarRequestKind.entries) {
            val selected = calendarUsageDescriptionKey(kind)
            for (other in CalendarRequestKind.entries.filter { it != kind }) {
                val dictionary = mapOf(calendarUsageDescriptionKey(other) to "The other access mode's purpose")
                assertFalse(calendarUsageDescriptionValid(dictionary[selected]))
            }
            assertTrue(calendarUsageDescriptionValid(mapOf(selected to "The selected purpose")[selected]))
        }
    }
}
