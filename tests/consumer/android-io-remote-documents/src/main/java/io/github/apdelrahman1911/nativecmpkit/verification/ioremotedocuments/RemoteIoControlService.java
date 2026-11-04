// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments;

import android.app.Service;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.Process;
import android.os.RemoteException;
import java.util.ArrayList;

/** Signature-authenticated backend owner. Socket/join work never blocks the Activity/main Looper. */
public final class RemoteIoControlService extends Service {
    private final Handler main = new Handler(Looper.getMainLooper());
    private HandlerThread thread;
    private Messenger endpoint;
    private RemoteIoHttpBackend backend;
    private boolean revoked;
    @Override public void onCreate() {
        super.onCreate(); thread = new HandlerThread("nativecmpkit-remote-io-control"); thread.start();
        endpoint = new Messenger(new Handler(thread.getLooper(), this::receive));
    }
    private boolean receive(Message message) {
        Bundle request = message.getData(); String nonce = request.getString("nonce");
        if (nonce == null || !nonce.matches("[a-f0-9]{32}") || message.replyTo == null) return true;
        Bundle reply = new Bundle(); reply.putString("nonce", nonce); boolean die = false;
        try {
            RemoteIoContract.requireReporter(this, message.sendingUid, RemoteIoContract.PACKAGE);
            String operation = request.getString("operation");
            if ("snapshot".equals(operation)) {
                RemoteIoContract.keys(request); reply.putBoolean("hasSession", backend != null);
            } else if ("prepare".equals(operation)) {
                RemoteIoContract.keys(request, "session", "token");
                if (backend != null) throw new IllegalStateException("Never replace an existing owned backend/tombstone");
                backend = new RemoteIoHttpBackend(RemoteIoContract.string(request, "session"), RemoteIoContract.string(request, "token"));
                backend.start(); reply.putBundle("backend", backend.snapshot());
            } else {
                RemoteIoContract.keys(request, "session");
                String session = RemoteIoContract.string(request, "session");
                if (backend == null || !session.equals(backend.session)) throw new IllegalArgumentException("Foreign or missing backend session");
                if ("stats".equals(operation)) reply.putBundle("backend", backend.snapshot());
                else if ("revoke".equals(operation)) {
                    revokeUriPermission(RemoteIoContract.tree(session), Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                    revoked = true; reply.putBoolean("ownerRevokeReturned", true); // Reporter independently checks actual denied access.
                } else if ("stop".equals(operation)) reply.putBundle("backend", backend.stop());
                else if ("die".equals(operation)) {
                    Bundle state = backend.snapshot();
                    if (!revoked || !state.getBoolean("stopped") || !state.getBoolean("dataCleared") ||
                        !state.getBoolean("listenerClosed") || !state.getBoolean("acceptorTerminal") || state.getInt("activeConnections") != 0)
                        throw new IllegalStateException("Owned backend/grant cleanup must be quiescent before self termination");
                    ArrayList<Bundle> journal = state.getParcelableArrayList("journal");
                    if (journal == null) throw new IllegalStateException("Native backend tombstones must remain");
                    for (Bundle record : journal) if (!record.getBoolean("workerTerminal") || !record.getBoolean("watchdogTerminal") || !record.getBoolean("socketClosed"))
                        throw new IllegalStateException("Owned backend worker/socket still alive");
                    reply.putInt("terminationSelfPid", Process.myPid()); reply.putBoolean("quiescentBeforeDeath", true); die = true;
                } else throw new IllegalArgumentException("Unknown finite backend operation");
            }
        } catch (Exception failure) { reply.putString("protocolError", RemoteIoContract.error(failure)); }
        RemoteIoContract.stamp(reply); Message response = Message.obtain(); response.setData(reply); boolean delivered = false;
        try { message.replyTo.send(response); delivered = true; }
        catch (RemoteException failure) { stopSelf(); }
        finally { response.recycle(); }
        // Only this own acknowledged PID/generation dies. Death is observed independently through its real Binder.
        if (die && delivered) main.postDelayed(() -> Process.killProcess(Process.myPid()), 100);
        return true;
    }
    @Override public IBinder onBind(Intent intent) { return endpoint.getBinder(); }
    @Override public void onDestroy() {
        if (thread != null) {
            thread.quitSafely();
            try { thread.join(RemoteIoContract.JOIN_MS); }
            catch (InterruptedException failure) { Thread.currentThread().interrupt(); }
        }
        super.onDestroy();
    }
}
