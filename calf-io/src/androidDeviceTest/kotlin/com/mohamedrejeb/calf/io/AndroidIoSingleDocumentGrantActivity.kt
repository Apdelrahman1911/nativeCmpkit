// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.app.Activity
import android.content.ComponentName
import android.content.Intent
import android.os.Bundle
import android.widget.TextView

/** One real foreground Activity-result transaction, never a manually granted URI. */
class AndroidIoSingleDocumentGrantActivity : Activity() {
    @Volatile var firstDraw = false
        private set
    @Volatile var resultCode: Int? = null
        private set
    @Volatile var result: Intent? = null
        private set
    @Volatile var resultCount = 0
        private set
    private var requested = false

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val view = TextView(this).apply { text = "NativeCmpKit owned single-document verification" }
        view.viewTreeObserver.addOnDrawListener { firstDraw = true }
        setContentView(view)
    }

    fun selectOwnedSingleDocument(nonce: String) = dispatch(Intent(Intent.ACTION_OPEN_DOCUMENT)
        .addCategory(Intent.CATEGORY_OPENABLE).setType("text/plain"), nonce)

    fun revokeOwnedSingleDocument(nonce: String) = dispatch(Intent(ACTION_REVOKE), nonce)

    private fun dispatch(intent: Intent, nonce: String) {
        check(!requested && resultCode == null && resultCount == 0 && firstDraw && hasWindowFocus())
        check(nonce.matches(Regex("[a-f0-9]{32}")))
        requested = true
        startActivityForResult(intent.setComponent(ComponentName(AndroidIoProviderContract.PACKAGE,
            "${AndroidIoProviderContract.PACKAGE}.IoSingleDocumentGrantActivity"))
            .putExtra(EXTRA_NONCE, nonce), REQUEST_CODE)
    }

    override fun onActivityResult(requestCode: Int, code: Int, data: Intent?) {
        super.onActivityResult(requestCode, code, data)
        if (requestCode != REQUEST_CODE) return
        check(requested && resultCount == 0) { "Duplicate or unrequested native single-document result" }
        result = data
        resultCount = 1
        resultCode = code // Volatile publication follows the real result and exact callback count.
    }

    companion object {
        const val ACTION_REVOKE = "${AndroidIoProviderContract.PACKAGE}.REVOKE_SINGLE_DOCUMENT"
        const val EXTRA_NONCE = "nativecmpkitSingleDocumentNonce"
        private const val REQUEST_CODE = 4926
    }
}
