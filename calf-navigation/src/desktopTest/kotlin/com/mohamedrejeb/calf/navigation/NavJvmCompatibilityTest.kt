package com.mohamedrejeb.calf.navigation

import androidx.compose.runtime.snapshots.SnapshotStateList
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull

class NavJvmCompatibilityTest {
    @Test
    fun legacyGetterDescriptorsRemainAvailableToJvmConsumers() {
        assertEquals(SnapshotStateList::class.java,
            AdaptiveNavHostController::class.java.getMethod("getBackStack").returnType)
        val generic = AdaptiveBaseBundle::class.java.getMethod("get", String::class.java)
        assertEquals(Any::class.java, generic.returnType)
        assertFalse(generic.isSynthetic)
        val bundle = AdaptiveBundle().apply { putInt("id", 7) }
        assertEquals(7, generic.invoke(bundle, "id"))
    }

    @Test
    fun runtimeComponentTypePreventsEmptyAnyArrayFromInferringStringArrayOnJvm() {
        assertFailsWith<IllegalArgumentException> { AdaptiveNavType.inferFromValueType(emptyArray<Any>()) }
    }

    @Test
    fun runtimeComponentTypeAlsoRejectsObjectArraysContainingOnlyStrings() {
        val bundle = AdaptiveBundle()
        for (array in listOf(emptyArray<Any>(), arrayOf<Any>("string"))) {
            bundle.mMap["value"] = array
            assertNull(bundle.getStringArray("value"))
            assertNull(bundle.getCharSequenceArray("value"))
            assertFailsWith<IllegalArgumentException> { bundle.putObject("generic", array) }
            assertFailsWith<IllegalArgumentException> { AdaptiveNavType.inferFromValueType(array) }
        }
    }
}
