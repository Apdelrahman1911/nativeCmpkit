// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.iodocuments;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.provider.DocumentsContract;

/** Real Android Activity result creates the read-only persistable tree grant. */
public final class IoDocumentGrantActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String caller = getCallingPackage();
        if (!IoFixture.REPORTER.equals(caller) || !Intent.ACTION_OPEN_DOCUMENT_TREE.equals(getIntent().getAction()) ||
            getPackageManager().checkSignatures(caller, getPackageName()) != PackageManager.SIGNATURE_MATCH) {
            setResult(RESULT_CANCELED); finish(); return;
        }
        Intent result = new Intent().setDataAndType(IoFixture.tree(), DocumentsContract.Document.MIME_TYPE_DIR)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION |
                Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        result.setClipData(ClipData.newRawUri("owned synthetic IO folder", IoFixture.tree()));
        setResult(RESULT_OK, result); finish();
    }
}
