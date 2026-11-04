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

/** Genuine implicit system tree UX; never fabricates a result or grants a URI itself. */
class AndroidIoRemoteTreeGrantActivity : Activity() {
    @Volatile var firstDraw = false; private set
    @Volatile var resultCode: Int? = null; private set
    @Volatile var result: Intent? = null; private set
    @Volatile var resultCount = 0; private set
    @Volatile var destroyed = false; private set
    var documentsUiPackage: String? = null; private set
    private var requested = false
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val view = TextView(this).apply { text = "NativeCmpKit controlled remote provider verification" }
        view.viewTreeObserver.addOnDrawListener { firstDraw = true }; setContentView(view)
    }
    fun selectRemoteTree(session: String) {
        check(firstDraw && hasWindowFocus() && !requested && resultCount == 0 && resultCode == null)
        val initialRoot: Uri = DocumentsContract.buildRootUri(RemoteIoContract.AUTHORITY, RemoteIoContract.root(session))
        check(initialRoot.scheme == "content" && initialRoot.authority == RemoteIoContract.AUTHORITY)
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).putExtra(DocumentsContract.EXTRA_INITIAL_URI, initialRoot)
        check(intent.component == null && intent.`package` == null && intent.selector == null)
        val resolved = checkNotNull(packageManager.resolveActivity(intent, PackageManager.MATCH_DEFAULT_ONLY)).activityInfo
        check(resolved.packageName in AndroidIoSystemTreeGrantActivity.SYSTEM_DOCUMENTS_UI)
        check(resolved.applicationInfo.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
        check(resolved.applicationInfo.uid != Process.myUid() && resolved.exported)
        documentsUiPackage = resolved.packageName; requested = true
        startActivityForResult(intent, REQUEST)
    }
    override fun onActivityResult(requestCode: Int, code: Int, data: Intent?) {
        super.onActivityResult(requestCode, code, data)
        if (requestCode != REQUEST) return
        check(requested && resultCount == 0 && resultCode == null) { "Duplicate or unrequested remote tree callback" }
        result = data; resultCount = 1; resultCode = code
    }
    override fun onDestroy() { destroyed = true; super.onDestroy() }
    companion object { private const val REQUEST = 5955 }
}
