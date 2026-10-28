@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.test.*

/** Actual synchronized Android registry on real JVM workers; no registry/backend substitute. */
class AndroidPermissionRegistryConcurrencyTest {
    @Test fun nameCollisionsAndConcurrentLookupsKeepValidatedMappingsAndRequestedIdentities() {
        val collision = Permission("android-important-registry-collision")
        val first = AndroidPermissionMapping("native-first", 23, 33)
        val second = AndroidPermissionMapping("native-second", 29, 37)
        AndroidPermissionRegistry.register(collision, first)
        assertSame(first, AndroidPermissionRegistry.getMapping(Permission(collision.name)))
        AndroidPermissionRegistry.register(Permission(collision.name), second)
        assertSame(second, AndroidPermissionRegistry.getMapping(collision))
        assertFailsWith<IllegalArgumentException> {
            AndroidPermissionRegistry.register(collision, AndroidPermissionMapping("invalid", 33, 29))
        }
        assertFailsWith<IllegalArgumentException> {
            AndroidPermissionRegistry.register(collision, AndroidPermissionMapping(" "))
        }
        assertSame(second, AndroidPermissionRegistry.getMapping(collision), "Invalid updates must not mutate the registry")

        val workers = 16
        val ready = CountDownLatch(workers)
        val start = CountDownLatch(1)
        val completed = AtomicInteger()
        val threads = CopyOnWriteArrayList<Thread>()
        val pool = Executors.newFixedThreadPool(workers) { task ->
            Thread(task, "nativecmpkit-registry-${threads.size}").apply { isDaemon = true; threads += this }
        }
        try {
            val futures = List(workers) { index ->
                pool.submit {
                    ready.countDown()
                    check(start.await(5, TimeUnit.SECONDS))
                    val requested = Permission("android-important-registry-worker-$index")
                    repeat(200) { iteration ->
                        val mapping = AndroidPermissionMapping("native-worker-$index", 23 + iteration % 2, 33)
                        AndroidPermissionRegistry.register(Permission(requested.name), mapping)
                        assertSame(mapping, AndroidPermissionRegistry.getMapping(requested))
                        assertEquals(requested, AndroidPermissionRegistry.findByAndroidString(mapping.permissionString, 29))
                        assertNull(AndroidPermissionRegistry.findByAndroidString(mapping.permissionString, 22))
                        AndroidPermissionRegistry.register(Permission(collision.name), if (iteration % 2 == 0) first else second)
                        val shared = AndroidPermissionRegistry.getMapping(collision)
                        assertTrue(shared === first || shared === second, "Concurrent lookup must return one complete validated mapping")
                        completed.incrementAndGet()
                    }
                }
            }
            assertTrue(ready.await(5, TimeUnit.SECONDS), "All real workers must reach the contention barrier")
            start.countDown()
            futures.forEach { it.get(10, TimeUnit.SECONDS) }
            assertEquals(workers * 200, completed.get())
        } finally {
            start.countDown()
            pool.shutdownNow()
            assertTrue(pool.awaitTermination(5, TimeUnit.SECONDS), "The test must release its executor")
            threads.forEach { it.join(2_000) }
            assertTrue(threads.none { it.isAlive }, "No registry-test worker may remain running")
        }
    }
}
