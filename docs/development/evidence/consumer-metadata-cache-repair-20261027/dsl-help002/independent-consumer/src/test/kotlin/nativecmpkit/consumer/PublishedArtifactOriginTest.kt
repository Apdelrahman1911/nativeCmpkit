package nativecmpkit.consumer

import com.mohamedrejeb.calf.core.PlatformContext
import com.mohamedrejeb.calf.io.KmpFile
import java.nio.file.Files
import java.nio.file.Path
import java.security.MessageDigest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/** Checks the actual loaded library classes, not merely the compile resolution graph. */
class PublishedArtifactOriginTest {
    @Test fun runtimeLibraryClassesComeFromExactStagedDesktopJars() {
        for ((root, type) in listOf("core" to PlatformContext::class.java, "io" to KmpFile::class.java)) {
            val location = assertNotNull(type.protectionDomain.codeSource?.location)
            assertEquals("file", location.protocol)
            val jar = Path.of(location.toURI())
            assertTrue(Files.isRegularFile(jar), "A producer class directory must not satisfy the consumer")
            assertEquals(System.getProperty("nativecmpkit.expected.$root.name"), jar.fileName.toString())
            val hash = MessageDigest.getInstance("SHA-256")
            Files.newInputStream(jar).use { stream ->
                val buffer = ByteArray(64 * 1024)
                while (true) {
                    val count = stream.read(buffer)
                    if (count < 0) break
                    hash.update(buffer, 0, count)
                }
            }
            val expected = assertNotNull(System.getProperty("nativecmpkit.expected.$root.sha256"))
            assertEquals(expected, hash.digest().joinToString("") { "%02x".format(it) })
        }
    }
}
