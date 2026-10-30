// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.sharerecipient;

import android.app.Service;
import android.content.ClipData;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.ParcelFileDescriptor;
import android.os.Process;
import android.os.RemoteException;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.UUID;

/** Finite nonce-correlated native grant observer; no arbitrary URI or file-writing RPC. */
public final class ShareRecipientService extends Service {
    static final String REPORTER = "com.mohamedrejeb.calf.calfshare.test";
    private static Intent received;
    private static String caller;
    private static String packet;
    private static int intents;
    private static int reads;
    private final String generation = UUID.randomUUID().toString();
    private final Messenger endpoint = new Messenger(new Handler(Looper.getMainLooper(), message -> {
        handle(message); return true;
    }));

    static void receiveIntent(Intent intent, String source) {
        received = intent; caller = source; packet = intent.getStringExtra("nativecmpkit.packet");
        intents++; reads = 0;
    }

    @Override public IBinder onBind(Intent intent) { return endpoint.getBinder(); }

    private void handle(Message request) {
        String[] packages = getPackageManager().getPackagesForUid(request.sendingUid);
        if (request.replyTo == null || packages == null || !Arrays.asList(packages).contains(REPORTER) ||
                getPackageManager().checkSignatures(REPORTER, getPackageName()) != PackageManager.SIGNATURE_MATCH) return;
        String nonce = request.getData().getString("nonce", "");
        if (!nonce.matches("[a-f0-9]{32}")) return;
        String operation = request.getData().getString("operation", "");
        Bundle result = snapshot();
        if ("read".equals(operation)) {
            ArrayList<Bundle> reports = new ArrayList<>();
            for (Uri uri : streams()) reports.add(read(uri));
            reads++;
            result.putParcelableArrayList("reports", reports);
            result.putInt("reads", reads);
        } else if ("clear".equals(operation)) {
            ShareRecipientActivity activity = ShareRecipientActivity.current.get();
            if (activity != null) activity.finish();
            received = null; caller = null; packet = null; reads = 0;
            result = snapshot();
        } else if (!"snapshot".equals(operation)) result.putString("protocolError", "Unknown operation");
        result.putString("nonce", nonce);
        Message reply = Message.obtain(); reply.setData(result);
        try { request.replyTo.send(reply); } catch (RemoteException disconnected) { /* Reporter owns its bounded timeout. */ }
        finally { reply.recycle(); }
    }

    @SuppressWarnings("deprecation")
    private static ArrayList<Uri> streams() {
        ArrayList<Uri> result = new ArrayList<>();
        if (received == null) return result;
        if (Intent.ACTION_SEND.equals(received.getAction())) {
            Uri uri = received.getParcelableExtra(Intent.EXTRA_STREAM);
            if (uri != null) result.add(uri);
        } else if (Intent.ACTION_SEND_MULTIPLE.equals(received.getAction())) {
            ArrayList<Uri> values = received.getParcelableArrayListExtra(Intent.EXTRA_STREAM);
            if (values != null) result.addAll(values);
        }
        return result;
    }

    private Bundle snapshot() {
        Bundle result = new Bundle();
        result.putInt("uid", Process.myUid()); result.putInt("pid", Process.myPid());
        result.putString("generation", generation); result.putInt("intents", intents); result.putInt("reads", reads);
        result.putBoolean("received", received != null); result.putString("caller", caller); result.putString("packet", packet);
        if (received != null) {
            result.putString("action", received.getAction()); result.putString("mime", received.getType());
            result.putString("subject", received.getStringExtra(Intent.EXTRA_SUBJECT)); result.putInt("flags", received.getFlags());
            ArrayList<String> values = new ArrayList<>();
            for (Uri uri : streams()) values.add(uri.toString());
            result.putStringArrayList("streams", values);
            ArrayList<String> clips = new ArrayList<>(); ClipData clip = received.getClipData();
            if (clip != null) for (int i = 0; i < clip.getItemCount(); i++) clips.add(String.valueOf(clip.getItemAt(i).getUri()));
            result.putStringArrayList("clips", clips);
        }
        return result;
    }

    private Bundle read(Uri uri) {
        Bundle result = new Bundle(); result.putString("uri", uri.toString());
        result.putBoolean("readGranted", checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED);
        result.putBoolean("writeGranted", checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_WRITE_URI_PERMISSION) == PackageManager.PERMISSION_GRANTED);
        try {
            ParcelFileDescriptor descriptor = getContentResolver().openFileDescriptor(uri, "r");
            if (descriptor == null) throw new IOException("Null native descriptor");
            // AutoCloseInputStream is the sole descriptor owner, including all failing reads.
            try (ParcelFileDescriptor.AutoCloseInputStream input = new ParcelFileDescriptor.AutoCloseInputStream(descriptor)) {
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                byte[] buffer = new byte[1024]; int total = 0; int count;
                while ((count = input.read(buffer)) != -1) {
                    total += count; if (total > 8192) throw new IOException("Fixture read cap");
                    digest.update(buffer, 0, count);
                }
                StringBuilder hash = new StringBuilder();
                for (byte value : digest.digest()) hash.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
                result.putString("sha256", hash.toString()); result.putInt("bytes", total);
            }
        } catch (SecurityException failure) { result.putString("readError", "SecurityException"); }
          catch (FileNotFoundException failure) { result.putString("readError", "FileNotFoundException"); }
          catch (Exception failure) { result.putString("readError", "UnexpectedNativeError"); }
        try (ParcelFileDescriptor ignored = getContentResolver().openFileDescriptor(uri, "w")) {
            result.putString("writeError", ignored == null ? "NullDescriptor" : "UnexpectedWriteAccess");
        } catch (SecurityException failure) { result.putString("writeError", "SecurityException"); }
          catch (FileNotFoundException failure) { result.putString("writeError", "FileNotFoundException"); }
          catch (Exception failure) { result.putString("writeError", "UnexpectedNativeError"); }
        return result;
    }
}
