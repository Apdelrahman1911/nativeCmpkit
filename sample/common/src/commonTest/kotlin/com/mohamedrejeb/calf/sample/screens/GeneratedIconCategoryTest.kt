// Modified for NativeCmpKit (2026-10-29): regression for a generator-dropped sample declaration.
package com.mohamedrejeb.calf.sample.screens

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class GeneratedIconCategoryTest {
    @Test fun generatedTabsContainEveryActualCategoryExactlyOnceInOriginalOrder() {
        assertEquals(listOf("Arrows", "Communication", "Devices", "Editing", "General",
            "Media", "Nature", "Objects", "Shapes"), IconCategories)
        assertEquals(AllCupertinoIcons.map { it.category }.distinct().sorted(), IconCategories)
        assertTrue(IconCategories.all { category -> AllCupertinoIcons.any { it.category == category } })
    }
}
