@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.internal

import kotlinx.cinterop.objcPtr
import platform.darwin.NSObject

/**
 * Exact identity of retained native objects, not Kotlin wrapper identity or
 * NSObject value equality. Two nil objects never establish an ownership lease.
 * Keep both references alive and compare only during the owning native call;
 * native addresses are neither cached nor exported as persistent identities.
 */
internal fun sameNativeObject(first: NSObject?, second: NSObject?): Boolean =
    first != null && second != null && first.objcPtr() == second.objcPtr()
