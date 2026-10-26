package com.mohamedrejeb.calf.geo

import java.lang.reflect.Modifier
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertSame

class LatLngJvmCompatibilityTest {
    @Test
    fun legacyEarthRadiusRemainsAJavaVisiblePublicStaticFinalDouble() {
        // Direct constant access can be inlined and would miss a removed JVM field.
        // Do not use getDeclaredField or override accessibility: Java callers need
        // the actual public field, including source visibility (not HIDDEN/synthetic).
        val owner = LatLng::class.java
        val field = owner.getField("EarthRadius")

        assertSame(owner, field.declaringClass)
        assertSame(java.lang.Double.TYPE, field.type)
        assertEquals(Modifier.PUBLIC or Modifier.STATIC or Modifier.FINAL, field.modifiers)
        assertFalse(field.isSynthetic)
        assertEquals(6371.00, field.getDouble(null))
    }
}
