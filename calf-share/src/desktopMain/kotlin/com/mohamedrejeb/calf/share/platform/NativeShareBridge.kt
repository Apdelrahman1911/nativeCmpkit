// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share.platform

/** JNI ABI1. New requests are asynchronous/cancellable; init/support and the old entrypoint remain. */
internal object NativeShareBridge {
    const val RESULT_PENDING = -1
    const val RESULT_SUCCESS = 0
    const val RESULT_DISMISSED = 1
    const val RESULT_UNAVAILABLE = 2
    const val RESULT_FAILED = 3
    const val REQUEST_BUSY = -1L
    init {
        loadNativeLibrary()
        check(abiVersion() == 1) { "Unsupported calf-share native ABI; use the library built with this nativeCmpkit version" }
    }
    @JvmStatic external fun init()
    @JvmStatic external fun abiVersion(): Int
    @JvmStatic external fun isNativeShareSupported(): Boolean
    /** Integration-test diagnostics: no private content is exposed. */
    @JvmStatic external fun activeRequestCount(): Int
    @JvmStatic external fun liveUiOperationCount(): Int
    /** Returns a positive operation ID, zero for unavailable or REQUEST_BUSY. No UI wait occurs. */
    @JvmStatic external fun beginShareSheet(text: String?, url: String?, filePaths: Array<String>?, subject: String?, parentWindow: Long): Long
    /** Nonblocking. A final result consumes the operation's registry entry. */
    @JvmStatic external fun takeShareResult(requestId: Long): Int
    /** Idempotent cancellation; all AppKit dismissal/destruction runs on Main. */
    @JvmStatic external fun cancelShare(requestId: Long)
    /** Compatibility entrypoint only. New code uses begin/take/cancel, never this blocking adapter. */
    @JvmStatic external fun showShareSheet(text: String?, url: String?, filePaths: Array<String>?, parentWindow: Long): Int
}
