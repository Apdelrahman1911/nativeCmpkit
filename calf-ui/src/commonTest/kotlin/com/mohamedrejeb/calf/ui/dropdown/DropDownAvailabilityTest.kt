package com.mohamedrejeb.calf.ui.dropdown

import kotlin.test.*

class DropDownAvailabilityTest {
    @Test fun comparesMajorAndMinorLexicographically() {
        for (version in listOf("17.4", "17.10", "18.0", "26.0", "26.4", "18"))
            assertTrue(supportsProgrammaticNativeMenu(version), version)
        for (version in listOf("16.9", "17", "17.3", "", "x.4", "18.x", "-1.0"))
            assertFalse(supportsProgrammaticNativeMenu(version), version)
    }
}
