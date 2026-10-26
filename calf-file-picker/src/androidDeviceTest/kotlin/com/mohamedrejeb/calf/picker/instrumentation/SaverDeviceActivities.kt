package com.mohamedrejeb.calf.picker.instrumentation

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Looper
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import java.lang.ref.WeakReference
import java.util.concurrent.atomic.AtomicInteger

/** Test-only host; unlike a sample, it mounts the public library launcher directly. */
class SaverHostActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { SaverDeviceContent.body() }
        latest = WeakReference(this)
        creations.incrementAndGet()
    }

    companion object {
        val creations = AtomicInteger()
        @Volatile var latest = WeakReference<SaverHostActivity>(null)
    }
}

/** Retaining test setup across a real Activity recreation is not an OS process-death simulation. */
object SaverDeviceContent {
    var body by mutableStateOf<@Composable () -> Unit>({ })
}

/**
 * A real Android Activity that returns through the framework, never a registry.dispatchResult stub.
 * Instrumentation routes only ACTION_CREATE_DOCUMENT to it; actual system DocumentsUI is not tested.
 */
class SaveDestinationActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(TextView(this).apply { text = "nativeCmpkit device-test destination fixture" })
    }

    fun complete(uri: Uri?) {
        check(Looper.myLooper() == Looper.getMainLooper())
        if (uri == null) {
            setResult(RESULT_CANCELED)
        } else {
            setResult(RESULT_OK, Intent().setData(uri).addFlags(
                Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
            ))
        }
        finish()
    }
}
