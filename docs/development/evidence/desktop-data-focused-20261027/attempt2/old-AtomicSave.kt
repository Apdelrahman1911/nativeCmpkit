package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.io.IOException
import java.io.OutputStream
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption

/** Stage before replacement: read/write/close/cancellation failures never truncate the old target. */
internal interface AtomicSaveOperations {
    fun move(source: Path, target: Path)
    fun delete(path: Path)
}

internal object FileSystemAtomicSaveOperations : AtomicSaveOperations {
    override fun move(source: Path, target: Path) {
        // Fail closed if unsupported. A plain replacing move can destroy the old target on failure.
        Files.move(source, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING)
    }
    override fun delete(path: Path) { Files.deleteIfExists(path) }
}

internal fun replaceFileContents(
    destination: File,
    write: (OutputStream) -> Unit,
    operations: AtomicSaveOperations = FileSystemAtomicSaveOperations,
    checkActive: () -> Unit = {},
): File {
    val target = destination.toPath().toAbsolutePath().normalize()
    val parent = target.parent ?: throw IOException("Destination has no parent directory")
    val temporary = Files.createTempFile(parent, ".nativecmpkit-save-", ".tmp")
    var primary: Throwable? = null
    var committed = false
    try {
        Files.newOutputStream(temporary).use(write)
        checkActive()
        operations.move(temporary, target)
        committed = true
        return destination
    } catch (failure: Throwable) {
        primary = failure
        throw failure
    } finally {
        if (!committed) {
            try { operations.delete(temporary) } catch (cleanup: Throwable) {
                if (primary != null) primary.addSuppressed(cleanup) else throw cleanup
            }
        }
    }
}

internal fun saveBytes(destination: File, bytes: ByteArray?, checkActive: () -> Unit = {}): File =
    replaceFileContents(destination, { output ->
        val content = bytes ?: byteArrayOf()
        var offset = 0
        while (offset < content.size) {
            checkActive()
            val size = minOf(64 * 1024, content.size - offset)
            output.write(content, offset, size)
            offset += size
        }
    }, checkActive = checkActive)

/** A same-file export is a non-destructive no-op, including symlink/hard-link aliases. */
internal fun saveFileCopy(source: File, destination: File, checkActive: () -> Unit = {}): File {
    checkActive()
    if (!source.isFile) throw IOException("Source is not a readable regular file")
    if (Files.exists(destination.toPath()) && Files.isSameFile(source.toPath(), destination.toPath())) return destination
    return replaceFileContents(destination, { output ->
        source.inputStream().use { input ->
            val buffer = ByteArray(64 * 1024)
            while (true) {
                checkActive()
                val count = input.read(buffer)
                if (count == -1) break
                if (count == 0) throw IOException("Source made no progress")
                output.write(buffer, 0, count)
            }
        }
    }, checkActive = checkActive)
}
