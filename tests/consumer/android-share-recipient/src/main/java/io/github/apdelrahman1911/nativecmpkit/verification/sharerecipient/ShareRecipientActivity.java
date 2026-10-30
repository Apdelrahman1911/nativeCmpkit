// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.sharerecipient;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.widget.TextView;
import java.lang.ref.WeakReference;

/** Actual separate-UID recipient. It never reads a URI until the reporter asks. */
public final class ShareRecipientActivity extends Activity {
    static WeakReference<ShareRecipientActivity> current = new WeakReference<>(null);

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String caller = getCallingPackage();
        if (!ShareRecipientService.REPORTER.equals(caller) ||
                getPackageManager().checkSignatures(caller, getPackageName()) != PackageManager.SIGNATURE_MATCH) {
            finish(); return;
        }
        current = new WeakReference<>(this);
        ShareRecipientService.receiveIntent(new Intent(getIntent()), caller);
        TextView view = new TextView(this);
        view.setText("NativeCmpKit owned read-only sharing verification");
        setContentView(view);
    }

    @Override public void onDestroy() {
        if (current.get() == this) current.clear();
        super.onDestroy();
    }
}
