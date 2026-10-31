// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.iodocuments;

import android.app.Service;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Message;
import android.os.Messenger;
import android.os.RemoteException;

/** Fixed owner revocation/reset and private-safe counters, never a manual grant or arbitrary URI RPC. */
public final class IoControlService extends Service {
    private final Messenger endpoint = new Messenger(new Handler(message -> {
        Bundle result = new Bundle(); String nonce = message.getData().getString("nonce");
        if (nonce == null || !nonce.matches("[a-f0-9]{32}") || message.replyTo == null) return true;
        result.putString("nonce", nonce);
        try {
            IoFixture.requireReporter(this, message.sendingUid);
            String operation = message.getData().getString("operation");
            if ("snapshot".equals(operation)) { /* Identity only. */ }
            else if ("stats".equals(operation)) {
                String id = message.getData().getString("id");
                if (!IoFixture.known(id)) throw new IllegalArgumentException("Unknown fixed owned document");
                result.putBundle("provider", getContentResolver().call(Uri.parse("content://" + IoFixture.AUTHORITY), IoFixture.STATS, id, null));
            } else if ("revoke".equals(operation) || "reset".equals(operation)) {
                // This app owns the fixed source URI. Revocation is an actual framework operation.
                revokeUriPermission(IoFixture.tree(), Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                if ("reset".equals(operation)) result.putBundle("provider", getContentResolver().call(
                    Uri.parse("content://" + IoFixture.AUTHORITY), IoFixture.RESET, null, null));
            } else throw new IllegalArgumentException("Unknown finite IO operation");
        } catch (Exception failure) { result.putString("protocolError", failure.getClass().getSimpleName()); }
        IoFixture.stamp(result); Message reply = Message.obtain(); reply.setData(result);
        try { message.replyTo.send(reply); } catch (RemoteException ignored) { stopSelf(); }
        finally { reply.recycle(); }
        return true;
    }));
    @Override public IBinder onBind(Intent intent) { return endpoint.getBinder(); }
}
