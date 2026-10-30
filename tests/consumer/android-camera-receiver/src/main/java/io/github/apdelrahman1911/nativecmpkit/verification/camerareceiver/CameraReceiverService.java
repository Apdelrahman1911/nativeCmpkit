// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver;

import android.app.Service;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.Process;
import android.os.RemoteException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.UUID;

/** Signature/UID/nonce-bound observation only; no arbitrary capture, file access or grant command. */
public final class CameraReceiverService extends Service {
    static final String REPORTER = "com.mohamedrejeb.calf.calfcamerapicker.test";
    static final byte[] BYTES = "NativeCmpKit synthetic native camera output".getBytes(StandardCharsets.UTF_8);
    private static Bundle received;
    private static int intents;
    private final String generation = UUID.randomUUID().toString();
    private final Messenger endpoint = new Messenger(new Handler(Looper.getMainLooper(), message -> { handle(message); return true; }));
    static void receive(Bundle report) { received = new Bundle(report); intents++; }
    @Override public IBinder onBind(Intent intent) { return endpoint.getBinder(); }
    private void handle(Message request) {
        String[] packages = getPackageManager().getPackagesForUid(request.sendingUid);
        if (request.replyTo == null || packages == null || !Arrays.asList(packages).contains(REPORTER) ||
                getPackageManager().checkSignatures(REPORTER, getPackageName()) != PackageManager.SIGNATURE_MATCH) return;
        String nonce = request.getData().getString("nonce", "");
        if (!nonce.matches("[a-f0-9]{32}")) return;
        String operation = request.getData().getString("operation", "");
        if ("clear".equals(operation)) received = null;
        Bundle result = received == null ? new Bundle() : new Bundle(received);
        if (!"snapshot".equals(operation) && !"clear".equals(operation)) result.putString("protocolError", "Unknown operation");
        result.putString("nonce", nonce); result.putString("generation", generation);
        result.putInt("uid", Process.myUid()); result.putInt("pid", Process.myPid());
        result.putInt("intents", intents); result.putBoolean("received", received != null);
        Message reply = Message.obtain(); reply.setData(result);
        try { request.replyTo.send(reply); } catch (RemoteException disconnected) { /* Reporter owns its bounded timeout. */ }
        finally { reply.recycle(); }
    }
}
