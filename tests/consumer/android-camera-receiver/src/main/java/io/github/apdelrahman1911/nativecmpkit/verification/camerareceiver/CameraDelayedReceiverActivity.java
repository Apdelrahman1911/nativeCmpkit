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
import android.widget.TextView;
import java.io.IOException;
import java.util.UUID;

/**
 * Disabled-by-default, finite native external capture. Holds the actual foreground
 * Activity while Android destroys/recreates the caller. Only a signature/UID/nonce
 * bound completion can return its own Android result; no arbitrary URI or grant RPC.
 * Synthetic output bytes are not a claimed hardware photo or camera/vendor UX.
 */
public final class CameraDelayedReceiverActivity extends Activity {
    private static CameraDelayedReceiverActivity active;
    private Bundle report;

    @SuppressWarnings("deprecation")
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String caller = getCallingPackage();
        if (active != null || !CameraReceiverService.REPORTER.equals(caller) ||
                getPackageManager().checkSignatures(caller, getPackageName()) != PackageManager.SIGNATURE_MATCH) {
            finish(); return;
        }
        Intent intent = getIntent();
        Uri uri = intent.getParcelableExtra(MediaStore.EXTRA_OUTPUT);
        if (uri == null || !"content".equals(uri.getScheme()) || !MediaStore.ACTION_IMAGE_CAPTURE.equals(intent.getAction())) {
            finish(); return;
        }
        report = new Bundle();
        report.putString("caller", caller); report.putString("packet", UUID.randomUUID().toString().replace("-", ""));
        report.putString("uri", uri.toString()); report.putString("action", intent.getAction());
        report.putInt("flags", intent.getFlags()); report.putInt("activityPid", Process.myPid());
        report.putBoolean("readGranted", checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED);
        report.putBoolean("writeGranted", checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_WRITE_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED);
        report.putBoolean("clipMatches", intent.getClipData() != null && intent.getClipData().getItemCount() == 1 &&
                uri.equals(intent.getClipData().getItemAt(0).getUri()));
        active = this;
        CameraReceiverService.receive(report);
        TextView text = new TextView(this);
        text.setText("NativeCmpKit owned external capture — synthetic bytes, no hardware camera");
        setContentView(text);
    }

    static boolean isHolding() { return active != null; }

    static boolean complete(String packet, boolean cancel) {
        CameraDelayedReceiverActivity owner = active;
        if (owner == null || !packet.matches("[a-f0-9]{32}") || !packet.equals(owner.report.getString("packet"))) return false;
        active = null;
        if (!cancel) {
            // Sole descriptor owner; uses only this Activity's real incoming EXTRA_OUTPUT.
            try {
                Uri uri = Uri.parse(owner.report.getString("uri"));
                ParcelFileDescriptor descriptor = owner.getContentResolver().openFileDescriptor(uri, "w");
                if (descriptor == null) throw new IOException("Null native camera output descriptor");
                owner.report.putInt("opens", 1);
                try (ParcelFileDescriptor.AutoCloseOutputStream stream = new ParcelFileDescriptor.AutoCloseOutputStream(descriptor)) {
                    stream.write(CameraReceiverService.BYTES); stream.flush();
                }
                owner.report.putInt("closes", 1);
            } catch (Exception failure) { owner.report.putString("writeError", failure.getClass().getSimpleName()); }
        }
        owner.report.putBoolean("cancelled", cancel); owner.report.putBoolean("completed", true);
        CameraReceiverService.update(owner.report);
        owner.setResult(cancel || owner.report.containsKey("writeError") ? RESULT_CANCELED : RESULT_OK);
        owner.finish();
        return true;
    }

    @Override public void onDestroy() {
        if (active == this) active = null;
        super.onDestroy();
    }
}
