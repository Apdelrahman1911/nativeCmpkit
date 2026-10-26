package nativecmpkit.consumer

import kotlin.test.*

/**
 * Package/native ABI smoke and valid handle ownership, not native dialog/GUI certification.
 * Reflection is intentional: Kotlin `internal` bridges cannot be imported by a real consumer.
 * Original JNI entry points are compatibility-sensitive despite not being public Kotlin APIs.
 */
class PublishedNativeConsumerTest {
    private fun bridge(name: String, library: String): Class<*> {
        val loader = PublishedNativeConsumerTest::class.java.classLoader
        val os = System.getProperty("os.name").lowercase()
        val arch = System.getProperty("os.arch").lowercase()
        val platform = when {
            os.contains("mac") || os.contains("darwin") -> "macos"
            os.contains("win") -> "windows"
            os.contains("linux") -> "linux"
            else -> error("Unsupported native consumer host $os")
        }
        val cpu = when (arch) {
            "aarch64", "arm64" -> "arm64"
            "amd64", "x86_64" -> "x64"
            else -> error("Unsupported native consumer CPU $arch")
        }
        val filename = when (platform) {
            "windows" -> "$library.dll"
            "macos" -> "lib$library.dylib"
            else -> "lib$library.so"
        }
        val resources = loader.getResources("native/$platform-$cpu/$filename").toList()
        assertEquals(1, resources.size, "Native payload must exist exactly once in the candidate classpath")
        assertEquals("jar", resources.single().protocol, "Do not substitute loose producer resource directories")
        val type = Class.forName(name, false, loader)
        assertTrue(type.protectionDomain.codeSource.location.path.endsWith(".jar"), "Bridge must come from an artifact JAR")
        return type
    }

    @Test fun pickerNativeLibraryLoadsAndInitializes() {
        val type = bridge("com.mohamedrejeb.calf.picker.platform.NativeFilePickerBridge", "calf_filepicker_native")
        type.getMethod("init").invoke(null)
    }

    @Test fun packagedPickerCreatesAndReleasesValidHandles() {
        val type = bridge("com.mohamedrejeb.calf.picker.platform.NativeFilePickerBridge", "calf_filepicker_native")
        val create = type.getMethod("createDirectoryDialog", String::class.java, String::class.java, Long::class.javaPrimitiveType)
        val destroy = type.getMethod("destroyDialog", Long::class.javaPrimitiveType)
        repeat(100) {
            val handle = create.invoke(null, "Consumer lifecycle test", null, 0L) as Long
            assertNotEquals(0L, handle)
            try { /* No native modal is displayed. */ } finally { destroy.invoke(null, handle) }
        }
    }

    @Test fun shareNativeLibraryLoadsAndReportsActualHostCapability() {
        val type = bridge("com.mohamedrejeb.calf.share.platform.NativeShareBridge", "calf_share_native")
        type.getMethod("init").invoke(null)
        val supported = type.getMethod("isNativeShareSupported").invoke(null) as Boolean
        val os = System.getProperty("os.name").lowercase()
        assertEquals(os.contains("mac") || os.contains("darwin"), supported)
    }
}
