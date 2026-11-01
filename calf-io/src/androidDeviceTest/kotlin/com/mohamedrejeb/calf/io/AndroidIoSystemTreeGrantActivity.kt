// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.app.Activity
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Process
import android.provider.DocumentsContract
import android.widget.TextView

/** A genuine implicit system DocumentsUI transaction; it never fabricates or grants a result. */
class AndroidIoSystemTreeGrantActivity : Activity() {
    @Volatile var firstDraw = false
        private set
    @Volatile var resultCode: Int? = null
        private set
    @Volatile var result: Intent? = null
        private set
    @Volatile var resultCount = 0
        private set
    @Volatile var destroyed = false
        private set
    private var requested = false
    var documentsUiPackage: String? = null
        private set

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val view = TextView(this).apply { text = "NativeCmpKit named system-provider verification" }
        view.viewTreeObserver.addOnDrawListener { firstDraw = true }
        setContentView(view)
    }

    fun selectSystemTree(initialParent: Uri) {
        check(firstDraw && hasWindowFocus() && !requested && resultCount == 0 && resultCode == null)
        check(initialParent.scheme == "content" && initialParent.authority in SYSTEM_AUTHORITIES)
        // An initial URI is only a navigation hint. It is never a selected URI or a URI grant.
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            .putExtra(DocumentsContract.EXTRA_INITIAL_URI, initialParent)
        check(intent.component == null && intent.`package` == null && intent.selector == null)
        val resolved = checkNotNull(packageManager.resolveActivity(intent, PackageManager.MATCH_DEFAULT_ONLY))
        val activity = resolved.activityInfo
        check(activity.packageName in SYSTEM_DOCUMENTS_UI)
        check(activity.applicationInfo.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
        check(activity.applicationInfo.uid != Process.myUid() && activity.exported)
        documentsUiPackage = activity.packageName
        requested = true
        startActivityForResult(intent, REQUEST_CODE)
    }

    override fun onActivityResult(requestCode: Int, code: Int, data: Intent?) {
        super.onActivityResult(requestCode, code, data)
        if (requestCode != REQUEST_CODE) return
        check(requested && resultCount == 0 && resultCode == null) { "Duplicate or unrequested system tree callback" }
        result = data
        resultCount = 1
        resultCode = code // Volatile publication follows the actual result and its count.
    }

    override fun onDestroy() {
        destroyed = true
        super.onDestroy()
    }

    companion object {
        private const val REQUEST_CODE = 4955
        val SYSTEM_AUTHORITIES = setOf("com.android.externalstorage.documents", "com.android.providers.downloads.documents")
        val SYSTEM_DOCUMENTS_UI = setOf("com.android.documentsui", "com.google.android.documentsui")
    }
}
