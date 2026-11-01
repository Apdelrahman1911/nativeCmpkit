// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.iodocuments;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;

/** Actual result-only grant and actual owner revocation of ONE fixed ordinary document. */
public final class IoSingleDocumentGrantActivity extends Activity {
    private static final String REVOKE = IoFixture.PACKAGE + ".REVOKE_SINGLE_DOCUMENT";
    private static final String NONCE = "nativecmpkitSingleDocumentNonce";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        Intent result = new Intent();
        String nonce = getIntent().getStringExtra(NONCE);
        int code = RESULT_CANCELED;
        try {
            String caller = getCallingPackage();
            if (!IoFixture.REPORTER.equals(caller) || nonce == null || !nonce.matches("[a-f0-9]{32}") ||
                getPackageManager().checkSignatures(caller, getPackageName()) != PackageManager.SIGNATURE_MATCH)
                throw new SecurityException("Wrong native single-document reporter or nonce");
            IoFixture.requireReporter(this, getPackageManager().getApplicationInfo(caller, 0).uid);
            Uri document = DocumentsContract.buildDocumentUri(IoFixture.AUTHORITY, "bookmark.txt");
            if (!DocumentsContract.isDocumentUri(this, document) || DocumentsContract.isTreeUri(document))
                throw new IllegalStateException("Expected the fixed registered ordinary document URI");
            if (Intent.ACTION_OPEN_DOCUMENT.equals(getIntent().getAction())) {
                if (!getIntent().hasCategory(Intent.CATEGORY_OPENABLE) || !"text/plain".equals(getIntent().getType()))
                    throw new IllegalArgumentException("Wrong finite single-document request");
                result.setDataAndType(document, "text/plain");
                result.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                result.setClipData(ClipData.newRawUri("owned synthetic IO single document", document));
                result.putExtra("operation", "grant");
            } else if (REVOKE.equals(getIntent().getAction())) {
                // Framework source-owner revoke, not a grant substitute or broad tree operation.
                revokeUriPermission(document, Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                result.putExtra("operation", "revoke");
            } else throw new IllegalArgumentException("Unknown finite single-document operation");
            code = RESULT_OK;
        } catch (Exception failure) {
            // A failed grant/revoke cannot return any URI or success-looking grant flags.
            result = new Intent().putExtra("protocolError", failure.getClass().getSimpleName());
        }
        result.putExtra(NONCE, nonce);
        result.putExtras(IoFixture.stamp(new Bundle()));
        setResult(code, result);
        finish();
    }
}
