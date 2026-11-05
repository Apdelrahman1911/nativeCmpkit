// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.picker.platform

import java.awt.Window
import java.lang.reflect.Modifier
import java.lang.reflect.Proxy

/**
 * JNI bridge to the native file picker library built with Rust + rfd.
 */
internal object NativeFilePickerBridge {

    init {
        loadNativeLibrary()
        check(abiVersion() == 1) { "Incompatible native file-picker ABI (expected 1)" }
    }

    /** Non-GUI version handshake; payload provenance is verified separately by packaging. */
    @JvmStatic
    external fun abiVersion(): Int

    /** No-op - forces the native library to load eagerly. */
    @JvmStatic
    external fun init()

    // -- Dialog creation (returns a handle for reuse) --

    /**
     * Create a file picker dialog config stored in native memory.
     * @return An opaque registry ID, not a pointer, to pass to [showFileDialog] / [destroyDialog].
     */
    @JvmStatic
    external fun createFileDialog(
        title: String?,
        initialDirectory: String?,
        extensions: Array<String>?,
        multiple: Boolean,
        parentWindow: Long,
    ): Long

    /**
     * Create a directory picker dialog config stored in native memory.
     * @return A handle to pass to [showDirectoryDialog] / [destroyDialog].
     */
    @JvmStatic
    external fun createDirectoryDialog(
        title: String?,
        initialDirectory: String?,
        parentWindow: Long,
    ): Long

    /**
     * Create a save-file dialog config stored in native memory.
     * @return A handle to pass to [showSaveDialog] / [destroyDialog].
     */
    @JvmStatic
    external fun createSaveDialog(
        title: String?,
        initialDirectory: String?,
        defaultName: String?,
        extension: String?,
        parentWindow: Long,
    ): Long

    // -- Additive owned-parent JNI capability (legacy ABI/descriptors remain 1) --

    fun createFileDialogForParent(
        title: String?, initialDirectory: String?, extensions: Array<String>?,
        multiple: Boolean, parentWindow: Window,
    ): Long = createForAwtParent(0, title, initialDirectory, extensions, multiple, null, parentWindow)

    fun createDirectoryDialogForParent(
        title: String?, initialDirectory: String?, parentWindow: Window,
    ): Long = createForAwtParent(1, title, initialDirectory, null, false, null, parentWindow)

    fun createSaveDialogForParent(
        title: String?, initialDirectory: String?, defaultName: String?,
        extension: String?, parentWindow: Window,
    ): Long = createForAwtParent(
        2, title, initialDirectory,
        extension?.takeIf { it.isNotEmpty() }?.let { arrayOf(it) }, false, defaultName, parentWindow,
    )

    private fun createForAwtParent(
        kind: Int, title: String?, initialDirectory: String?, extensions: Array<String>?,
        multiple: Boolean, defaultName: String?, parentWindow: Window,
    ): Long {
        val version = try {
            macOsParentLeaseAbiVersion()
        } catch (failure: UnsatisfiedLinkError) {
            throw IllegalStateException("Native payload lacks the owned macOS parent JNI capability", failure)
        }
        check(version == 1) { "Incompatible owned macOS parent JNI capability (expected 1)" }
        return createDialogWithAwtParent(
            kind, title, initialDirectory, extensions, multiple, defaultName, parentWindow,
        )
    }

    @JvmStatic
    private external fun macOsParentLeaseAbiVersion(): Int

    @JvmStatic
    private external fun createDialogWithAwtParent(
        kind: Int, title: String?, initialDirectory: String?, extensions: Array<String>?,
        multiple: Boolean, defaultName: String?, parentWindow: Window,
    ): Long

    /** Called only synchronously by the real JDK CFNativeAction read-lock borrow. */
    @JvmStatic
    private external fun retainMacOsParent(ticket: Long, pointer: Long)

    /**
     * Public Java Proxy APIs avoid importing or suppressing non-exported JDK/Skiko types.
     * Class/method qualification happens BEFORE entering execute's read-lock callback.
     * The ticket authorizes one callback; it never substitutes for native ownership.
     */
    @JvmStatic
    private fun newMacOsRetainAction(actionInterface: Class<*>, ticket: Long): Any {
        check(System.getProperty("java.specification.version") == "17") {
            "Owned macOS parenting currently requires the reviewed OpenJDK 17 peer contract"
        }
        check(
            actionInterface.name == "sun.lwawt.macosx.CFRetainedResource\$CFNativeAction" &&
                actionInterface.isInterface && Modifier.isPublic(actionInterface.modifiers) &&
                actionInterface.classLoader == null && actionInterface.module.name == "java.desktop" &&
                ticket > 0L
        ) { "Unsupported JDK native parent action interface" }
        val run = actionInterface.getMethod("run", java.lang.Long.TYPE)
        check(run.returnType == java.lang.Void.TYPE && actionInterface.declaredMethods.size == 1) {
            "Unsupported JDK native parent action signature"
        }
        return Proxy.newProxyInstance(
            NativeFilePickerBridge::class.java.classLoader, arrayOf(actionInterface),
        ) { proxy, method, arguments ->
            when {
                method == run -> {
                    val pointer = arguments?.singleOrNull() as? Long
                        ?: throw IllegalStateException("Mismatched native parent borrow arguments")
                    // No dispatch, registry operation or external lock in this callback.
                    retainMacOsParent(ticket, pointer)
                    null
                }
                method.declaringClass == Any::class.java -> when (method.name) {
                    "equals" -> proxy === arguments?.singleOrNull()
                    "hashCode" -> System.identityHashCode(proxy)
                    "toString" -> "NativeCmpKit CFNativeAction"
                    else -> throw IllegalStateException("Unexpected native parent action Object method")
                }
                else -> throw IllegalStateException("Unexpected native parent borrow method")
            }
        }
    }

    // -- Show dialog --

    /**
     * Show a file picker dialog using a previously created handle.
     * @return Array of selected file paths, or empty array if cancelled.
     */
    @JvmStatic
    external fun showFileDialog(handle: Long): Array<String>

    /**
     * Show a directory picker dialog using a previously created handle.
     * @return Selected directory path, or null if cancelled.
     */
    @JvmStatic
    external fun showDirectoryDialog(handle: Long): String?

    /**
     * Show a save-file dialog using a previously created handle.
     * @return Selected save path, or null if cancelled.
     */
    @JvmStatic
    external fun showSaveDialog(handle: Long): String?

    // -- Cleanup --

    /**
     * Free the native memory for a dialog config.
     * Must be called when the dialog is no longer needed.
     */
    @JvmStatic
    external fun destroyDialog(handle: Long)
}
