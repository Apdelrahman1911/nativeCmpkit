// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.os.Process;
import android.provider.MediaStore;
import java.io.IOException;

/** A real different UID writes synthetic bytes through Android's actual URI grant. Not camera UX/hardware. */
public final class CameraReceiverActivity extends Activity {
    @SuppressWarnings("deprecation")
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String caller = getCallingPackage();
        if (!CameraReceiverService.REPORTER.equals(caller) ||
                getPackageManager().checkSignatures(caller, getPackageName()) != PackageManager.SIGNATURE_MATCH) {
            finish(); return;
        }
        Intent intent = getIntent();
        Bundle report = new Bundle();
        report.putString("caller", caller); report.putString("packet", intent.getStringExtra("nativecmpkit.packet"));
        report.putString("action", intent.getAction()); report.putInt("flags", intent.getFlags());
        Uri uri = intent.getParcelableExtra(MediaStore.EXTRA_OUTPUT);
        if (uri != null) {
            report.putString("uri", uri.toString());
            report.putBoolean("readGranted", checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED);
            report.putBoolean("writeGranted", checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_WRITE_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED);
            report.putBoolean("clipMatches", intent.getClipData() != null && intent.getClipData().getItemCount() == 1 &&
                    uri.equals(intent.getClipData().getItemAt(0).getUri()));
        }
        boolean cancel = intent.getBooleanExtra("nativecmpkit.cancel", false);
        if (!cancel) {
            // Never accept an arbitrary URI by RPC. Only the authorized Activity's actual EXTRA_OUTPUT is used.
            try {
                if (uri == null || !"content".equals(uri.getScheme()) || !MediaStore.ACTION_IMAGE_CAPTURE.equals(intent.getAction()))
                    throw new IOException("Invalid camera URI contract");
                ParcelFileDescriptor descriptor = getContentResolver().openFileDescriptor(uri, "w");
                if (descriptor == null) throw new IOException("Null native descriptor");
                report.putInt("opens", 1);
                // AutoCloseOutputStream is the sole descriptor owner, including exceptions.
                try (ParcelFileDescriptor.AutoCloseOutputStream stream = new ParcelFileDescriptor.AutoCloseOutputStream(descriptor)) {
                    stream.write(CameraReceiverService.BYTES);
                    stream.flush();
                }
                report.putInt("closes", 1);
            } catch (Exception failure) { report.putString("writeError", failure.getClass().getSimpleName()); }
        }
        report.putBoolean("cancelled", cancel);
        CameraReceiverService.receive(report);
        setResult(cancel || report.containsKey("writeError") ? RESULT_CANCELED : RESULT_OK);
        finish();
    }
}
