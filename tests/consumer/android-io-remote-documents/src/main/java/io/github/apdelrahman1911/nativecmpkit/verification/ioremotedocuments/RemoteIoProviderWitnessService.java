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

/** Actual provider-process identity and bounded registered transfer observations; no global PID/FD scan. */
public final class RemoteIoProviderWitnessService extends Service {
    private final Handler main = new Handler(Looper.getMainLooper());
    private HandlerThread thread;
    private Messenger endpoint;
    @Override public void onCreate() {
        super.onCreate(); thread = new HandlerThread("nativecmpkit-remote-io-witness"); thread.start();
        endpoint = new Messenger(new Handler(thread.getLooper(), this::receive));
    }
    private boolean receive(Message message) {
        Bundle request = message.getData(); String nonce = request.getString("nonce");
        if (nonce == null || !nonce.matches("[a-f0-9]{32}") || message.replyTo == null) return true;
        Bundle reply = new Bundle(); reply.putString("nonce", nonce); boolean die = false;
        try {
            RemoteIoContract.requireReporter(this, message.sendingUid, RemoteIoContract.PROVIDER_PROCESS);
            String operation = request.getString("operation");
            if ("snapshot".equals(operation)) RemoteIoContract.keys(request);
            else if ("prepare".equals(operation)) {
                RemoteIoContract.keys(request, "session", "token", "port");
                reply.putBundle("provider", RemoteIoDocumentsProvider.prepare(this, RemoteIoContract.string(request, "session"),
                    RemoteIoContract.string(request, "token"), RemoteIoContract.integer(request, "port")));
            } else {
                RemoteIoContract.keys(request, "session"); String session = RemoteIoContract.string(request, "session");
                if ("stats".equals(operation)) reply.putBundle("provider", RemoteIoDocumentsProvider.snapshot(session));
                else if ("stop".equals(operation)) reply.putBundle("provider", RemoteIoDocumentsProvider.stop(this, session));
                else if ("die".equals(operation)) {
                    Bundle state = RemoteIoDocumentsProvider.snapshot(session);
                    if (!state.getBoolean("stopped") || state.getInt("activeTransfers") != 0 ||
                        state.getInt("activeSockets") != 0 || state.getInt("activeWorkers") != 0)
                        throw new IllegalStateException("Owned provider must be quiescent before self termination");
                    ArrayList<Bundle> journal = state.getParcelableArrayList("journal");
                    if (journal == null) throw new IllegalStateException("Native provider tombstones must remain");
                    for (Bundle record : journal) if (!record.getBoolean("terminal") || !record.getBoolean("openingTerminal") ||
                        !record.getBoolean("workerTerminal") || record.getBoolean("readNativeOpen") || record.getBoolean("writeNativeOpen"))
                        throw new IllegalStateException("Owned provider native descriptor/worker still alive");
                    reply.putInt("terminationSelfPid", Process.myPid()); reply.putBoolean("quiescentBeforeDeath", true); die = true;
                } else throw new IllegalArgumentException("Unknown finite provider witness operation");
            }
        } catch (Exception failure) { reply.putString("protocolError", RemoteIoContract.error(failure)); }
        RemoteIoContract.stamp(reply); Message response = Message.obtain(); response.setData(reply); boolean delivered = false;
        try { message.replyTo.send(response); delivered = true; }
        catch (RemoteException failure) { stopSelf(); }
        finally { response.recycle(); }
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
