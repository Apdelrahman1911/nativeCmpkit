// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.app.Activity
import android.content.ComponentName
import android.content.Intent
import android.os.Bundle
import android.widget.TextView

/** Native foreground caller receives the actual cross-UID Android grant result. */
class AndroidIoGrantActivity : Activity() {
    @Volatile var firstDraw = false
        private set
    @Volatile var ioDocumentResultCode: Int? = null
        private set
    @Volatile var ioDocumentResult: Intent? = null
        private set
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val view = TextView(this).apply { text = "NativeCmpKit owned IO verification" }
        view.viewTreeObserver.addOnDrawListener { firstDraw = true }
        setContentView(view)
    }
    fun selectOwnedTree() {
        check(hasWindowFocus() && firstDraw)
        startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).setComponent(ComponentName(
            AndroidIoProviderContract.PACKAGE, "${AndroidIoProviderContract.PACKAGE}.IoDocumentGrantActivity")), 4911)
    }
    override fun onActivityResult(requestCode: Int, code: Int, data: Intent?) {
        super.onActivityResult(requestCode, code, data)
        if (requestCode == 4911) { ioDocumentResult = data; ioDocumentResultCode = code }
    }
}
