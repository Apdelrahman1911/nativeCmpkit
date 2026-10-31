// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.iodocuments;

import android.app.Application;
import android.app.Service;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.Process;
import android.os.RemoteException;

/** Only this fixed fixture's provider process may deliberately die; the reporter stays alive. */
public final class IoProviderWitnessService extends Service {
    private final Handler main = new Handler(Looper.getMainLooper());
    private final Messenger endpoint = new Messenger(new Handler(message -> {
        Bundle result = new Bundle(); String nonce = message.getData().getString("nonce");
        if (nonce == null || !nonce.matches("[a-f0-9]{32}") || message.replyTo == null) return true;
        result.putString("nonce", nonce); boolean die = false;
        try {
            IoFixture.requireReporter(this, message.sendingUid);
            if (!(IoFixture.PACKAGE + ":nativecmpkit_io_provider").equals(Application.getProcessName()))
                throw new IllegalStateException("The exact owned provider process was not verified");
            String operation = message.getData().getString("operation");
            if ("snapshot".equals(operation)) { /* Native identity witness. */ }
            else if ("die".equals(operation)) die = true;
            else throw new IllegalArgumentException("Unknown finite witness operation");
        } catch (Exception failure) { result.putString("protocolError", failure.getClass().getSimpleName()); }
        IoFixture.stamp(result); Message reply = Message.obtain(); reply.setData(result);
        boolean delivered = false;
        try { message.replyTo.send(reply); delivered = true; } catch (RemoteException ignored) { stopSelf(); }
        finally { reply.recycle(); }
        if (die && delivered) main.postDelayed(() -> Process.killProcess(Process.myPid()), 100);
        return true;
    }));
    @Override public IBinder onBind(Intent intent) { return endpoint.getBinder(); }
}
