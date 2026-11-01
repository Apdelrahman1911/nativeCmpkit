// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.storageprobe

import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Process
import android.system.Os
import android.system.OsConstants
import java.io.File
import java.security.MessageDigest

/** Read the actual installed APK and one certificate in this ordinary app UID. */
internal object StorageProbeIdentity {
    private const val LIMIT = 256L * 1024 * 1024
    private var cached: Bundle? = null

    @Synchronized fun read(context: Context): Bundle {
        check(Build.VERSION.SDK_INT in setOf(28, 29, 30, 35))
        cached?.let { return Bundle(it) }
        val info = context.packageManager.getPackageInfo(context.packageName, PackageManager.GET_SIGNING_CERTIFICATES)
        val app = checkNotNull(info.applicationInfo)
        check(app.uid == Process.myUid() && app.uid >= 10000)
        check(app.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
        check(info.splitNames.isNullOrEmpty() && app.splitSourceDirs.isNullOrEmpty())
        val signing = checkNotNull(info.signingInfo)
        check(!signing.hasMultipleSigners())
        check(signing.signingCertificateHistory?.size == 1)
        val certificate = signing.apkContentsSigners.single().toByteArray()
        val apk = File(app.sourceDir)
        val before = Os.lstat(apk.absolutePath)
        check(OsConstants.S_ISREG(before.st_mode) && before.st_size in 1 until LIMIT)
        val digest = MessageDigest.getInstance("SHA-256")
        var total = 0L
        apk.inputStream().use { stream ->
            val bytes = ByteArray(16384)
            while (true) {
                val count = stream.read(bytes)
                if (count < 0) break
                check(count > 0); total += count; check(total < LIMIT)
                digest.update(bytes, 0, count)
            }
        }
        val after = Os.lstat(apk.absolutePath)
        check(total == before.st_size && before.st_dev == after.st_dev && before.st_ino == after.st_ino &&
            before.st_size == after.st_size && before.st_mtime == after.st_mtime)
        return Bundle().apply {
            putString("apkSha256", hex(digest.digest()))
            putString("certificateSha256", hex(MessageDigest.getInstance("SHA-256").digest(certificate)))
            putBoolean("splitsAbsent", true)
        }.also { cached = Bundle(it) }
    }

    private fun hex(bytes: ByteArray) = bytes.joinToString("") { "%02x".format(it.toInt() and 255) }
}
