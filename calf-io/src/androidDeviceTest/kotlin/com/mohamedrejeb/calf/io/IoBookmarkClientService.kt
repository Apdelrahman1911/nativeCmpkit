// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.app.Application
import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.Looper
import android.os.Message
import android.os.Messenger
import android.os.Process
import java.security.MessageDigest
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking

/** Public bookmark and IO operations in an owned secondary reporter process. */
class IoBookmarkClientService : Service() {
    private val generation = UUID.randomUUID().toString()
    private val worker = HandlerThread("owned-io-bookmark-client").apply { start() }
    private val main = Handler(Looper.getMainLooper())
    private val endpoint = Messenger(Handler(worker.looper) { message ->
        val nonce = message.data.getString("nonce")
        if (nonce == null || !nonce.matches(Regex("[a-f0-9]{32}")) || message.replyTo == null) return@Handler true
        val result = Bundle().apply { putString("nonce", nonce) }; var die = false
        try {
            check(message.sendingUid == Process.myUid())
            check(Application.getProcessName() == "$packageName:nativecmpkit_io_client")
            val prefs = getSharedPreferences("nativecmpkit-owned-io-bookmark", MODE_PRIVATE)
            val file = KmpFile(AndroidIoProviderContract.tree)
            when (message.data.getString("operation")) {
                "snapshot" -> Unit
                "remember" -> {
                    val bookmark = checkNotNull(file.createBookmark(this))
                    check(bookmark == AndroidIoProviderContract.tree.toString())
                    check(prefs.edit().putString("bookmark", bookmark).commit())
                    result.putString("bookmark", bookmark)
                    describeBookmark(result, bookmark)
                }
                "restore" -> describeBookmark(result, checkNotNull(prefs.getString("bookmark", null)))
                "release" -> {
                    val bookmark = checkNotNull(prefs.getString("bookmark", null))
                    file.releaseBookmark(this)
                    describeBookmark(result, bookmark)
                }
                "clear" -> { file.releaseBookmark(this); check(prefs.edit().clear().commit()) }
                "die" -> die = true
                else -> error("Unknown finite bookmark client operation")
            }
        } catch (failure: Exception) { result.putString("protocolError", failure.javaClass.simpleName) }
        result.putInt("uid", Process.myUid()); result.putInt("pid", Process.myPid())
        result.putString("generation", generation); result.putString("process", Application.getProcessName())
        val response = Message.obtain().apply { data = result }; var delivered = false
        try { message.replyTo.send(response); delivered = true } finally { response.recycle() }
        if (die && delivered) main.postDelayed({ Process.killProcess(Process.myPid()) }, 100)
        true
    })
    private fun describeBookmark(result: Bundle, bookmark: String) {
        check(bookmark == AndroidIoProviderContract.tree.toString())
        val restored = KmpFile.fromBookmark(bookmark, this)
        result.putBoolean("restored", restored != null)
        val permission = contentResolver.persistedUriPermissions.singleOrNull { it.uri == AndroidIoProviderContract.tree }
        result.putBoolean("persistedRead", permission?.isReadPermission == true)
        result.putBoolean("persistedWrite", permission?.isWritePermission == true)
        result.putBoolean("readGranted", checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED)
        result.putBoolean("writeGranted", checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_WRITE_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED)
        result.putString("uri", restored?.toUriString())
        result.putBoolean("exists", restored?.exists(this) == true)
        result.putBoolean("directory", restored?.isDirectory(this) == true)
        result.putString("name", restored?.getName(this))
        val child = KmpFile(AndroidIoProviderContract.child("bookmark.txt"))
        try {
            val bytes = runBlocking(Dispatchers.IO) { child.readByteArray(this@IoBookmarkClientService) }
            result.putInt("bytes", bytes.size)
            result.putString("sha256", MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) })
        } catch (failure: Exception) { result.putString("readError", failure.javaClass.simpleName) }
    }
    override fun onBind(intent: Intent): IBinder = endpoint.binder
    override fun onDestroy() { worker.quitSafely(); worker.join(10_000); check(!worker.isAlive); super.onDestroy() }
}
