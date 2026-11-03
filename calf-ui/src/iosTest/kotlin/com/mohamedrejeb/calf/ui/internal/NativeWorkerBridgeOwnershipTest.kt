// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    kotlin.experimental.ExperimentalNativeApi::class,
    kotlin.native.runtime.NativeRuntimeApi::class)

package com.mohamedrejeb.calf.ui.internal

import kotlin.native.ref.WeakReference
import kotlin.native.runtime.GC
import platform.Foundation.NSThread
import kotlin.test.Test
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Library-level control: no sheet, manager, delegate or modal can own this capture. */
class NativeWorkerBridgeOwnershipTest {
    @Test fun replacedPlainCompositionReleasesAnOwnerCreatedOnTheWorker() = runApplicationUiTest {
        val owner = installPlainContent()
        waitForIdle()
        setContent { }
        waitForIdle()
        repeat(3) { runOnIdle { GC.collect() } }
        runOnIdle { assertNull(owner.get(), "Replaced plain root must release its Worker-created capture") }
    }

    @Test fun pooledWorkerBridgePreservesMainResultAndExactThrowableIdentity() {
        assertTrue(!NSThread.isMainThread)
        val result = Any()
        assertSame(result, onApplicationMain { assertTrue(NSThread.isMainThread); result })
        val original = IllegalArgumentException("fixed owned bridge failure")
        val actual = assertFailsWith<IllegalArgumentException> {
            onApplicationMain { assertTrue(NSThread.isMainThread); throw original }
        }
        assertSame(original, actual)
    }

    private class Owner { private var calls = 0; fun touch() { calls++ } }

    // A separate frame avoids keeping a strong owner in the GC assertion's frame.
    private fun NativeApplicationUiTest.installPlainContent(): WeakReference<Owner> {
        val owner = Owner()
        setContent { owner.touch() }
        return WeakReference(owner)
    }
}
