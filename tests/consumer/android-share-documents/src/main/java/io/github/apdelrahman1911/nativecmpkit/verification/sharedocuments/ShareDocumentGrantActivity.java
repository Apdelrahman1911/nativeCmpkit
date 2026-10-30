// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.sharedocuments;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import java.util.ArrayList;

/** Native Activity-result grant; no manual grant RPC or arbitrary path/URI input. */
public final class ShareDocumentGrantActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String caller = getCallingPackage();
        if (!OwnedShareDocumentsProvider.REPORTER.equals(caller) ||
                getPackageManager().checkSignatures(caller, getPackageName()) != PackageManager.SIGNATURE_MATCH) {
            setResult(RESULT_CANCELED); finish(); return;
        }
        ArrayList<Uri> uris = new ArrayList<>();
        for (String id : OwnedShareDocumentsProvider.IDS) uris.add(DocumentsContract.buildDocumentUri(getPackageName()+".documents", id));
        Intent result = new Intent().setType("*/*").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        ClipData clip = ClipData.newUri(getContentResolver(), "owned synthetic document selection", uris.get(0));
        clip.addItem(new ClipData.Item(uris.get(1))); result.setClipData(clip);
        result.putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris);
        setResult(RESULT_OK, result); finish(); // Android creates the actual reporter's incoming read grants.
    }
}
