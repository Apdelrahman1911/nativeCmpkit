package com.mohamedrejeb.calf.picker

import android.net.Uri
import com.mohamedrejeb.calf.io.KmpFile
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNull

@RunWith(RobolectricTestRunner::class)
class PendingSaveSourceTest {
    @Test fun consumeIsExactlyOnceAndRejectsOverlapUntilWriteFinishes() {
        val pending = PendingSaveSource()
        val first = SaveSource.Bytes(byteArrayOf(1))
        pending.set(first)
        assertFailsWith<IllegalStateException> { pending.set(SaveSource.Bytes(byteArrayOf(2))) }
        assertEquals(first, pending.consume()?.source)
        assertNull(pending.consume())
        assertFailsWith<IllegalStateException> { pending.set(first) }
        pending.finish()
        pending.set(first)
        assertEquals(first, pending.consume()?.source)
    }
    @Test fun restorationKeepsUriButRecordsBytesAsLostWithoutSavingThem() {
        val uri = Uri.parse("content://test/document/1")
        val file = PendingSaveSource().apply { set(SaveSource.File(KmpFile(uri))) }
        val restoredFile = PendingSaveSource.restore(file.savedState())
        assertEquals(uri, assertIs<SaveSource.File>(restoredFile.consume()?.source).file.uri)
        val bytes = PendingSaveSource().apply { set(SaveSource.Bytes(ByteArray(2_000_000))) }
        assertEquals("bytes-lost", bytes.savedState())
        val restoredBytes = PendingSaveSource.restore(bytes.savedState())
        assertNull(assertNotNull(restoredBytes.consume()).source)
    }
    @Test fun aCompletedRequestDoesNotRestoreAsAnotherOutstandingSave() {
        val holder = PendingSaveSource().apply { set(SaveSource.Bytes(byteArrayOf())) }
        holder.consume(); holder.finish()
        assertNull(PendingSaveSource.restore(holder.savedState()).consume())
    }
}
