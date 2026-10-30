// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver;

import android.app.Service;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
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

/** Signature/UID/nonce-bound observation/completion only; no arbitrary URI, file access or grant command. */
public final class CameraReceiverService extends Service {
    static final String REPORTER = "com.mohamedrejeb.calf.calfcamerapicker.test";
    static final byte[] BYTES = "NativeCmpKit synthetic native camera output".getBytes(StandardCharsets.UTF_8);
    private static Bundle received;
    private static int intents;
    private final String generation = UUID.randomUUID().toString();
    private String delayedLease;
    private Integer originalDelayedState;
    private final Messenger endpoint = new Messenger(new Handler(Looper.getMainLooper(), message -> { handle(message); return true; }));
    static void receive(Bundle report) { received = new Bundle(report); intents++; }
    static void update(Bundle report) { received = new Bundle(report); }
    @Override public IBinder onBind(Intent intent) { return endpoint.getBinder(); }
    private void handle(Message request) {
        String[] packages = getPackageManager().getPackagesForUid(request.sendingUid);
        if (request.replyTo == null || packages == null || !Arrays.asList(packages).contains(REPORTER) ||
                getPackageManager().checkSignatures(REPORTER, getPackageName()) != PackageManager.SIGNATURE_MATCH) return;
        String nonce = request.getData().getString("nonce", "");
        if (!nonce.matches("[a-f0-9]{32}")) return;
        String operation = request.getData().getString("operation", "");
        Bundle result;
        if ("arm-delayed".equals(operation) || "restore-delayed".equals(operation)) {
            result = delayedState(operation, request.getData().getString("lease", ""));
        } else {
            boolean refusedClear = "clear".equals(operation) &&
                    (delayedLease != null || CameraDelayedReceiverActivity.isHolding());
            if ("clear".equals(operation) && !refusedClear) received = null;
            boolean completion = "complete".equals(operation) && CameraDelayedReceiverActivity.complete(
                    request.getData().getString("packet", ""), request.getData().getBoolean("cancel", false));
            result = received == null ? new Bundle() : new Bundle(received);
            if (refusedClear || (!"snapshot".equals(operation) && !"clear".equals(operation) && !"complete".equals(operation)) ||
                    ("complete".equals(operation) && !completion)) result.putString("protocolError", "Unknown or live owned operation");
        }
        result.putString("nonce", nonce); result.putString("generation", generation);
        result.putInt("uid", Process.myUid()); result.putInt("pid", Process.myPid());
        result.putInt("intents", intents); result.putBoolean("received", received != null);
        result.putBoolean("holdingActivity", CameraDelayedReceiverActivity.isHolding());
        Message reply = Message.obtain(); reply.setData(result);
        try { request.replyTo.send(reply); } catch (RemoteException disconnected) { /* Reporter owns its bounded timeout. */ }
        finally { reply.recycle(); }
    }

    /** The native recipient UID owns only its fixed disabled component, never a foreign package. */
    @SuppressWarnings("deprecation")
    private Bundle delayedState(String operation, String lease) {
        Bundle result = new Bundle();
        if (!lease.matches("[a-f0-9]{32}") || Build.VERSION.SDK_INT != 35 ||
                Process.myUid() / 100000 != 0 || Looper.myLooper() != Looper.getMainLooper() ||
                CameraDelayedReceiverActivity.isHolding()) {
            result.putString("protocolError", "Refused native delayed-component control");
            return result;
        }
        final ComponentName component = new ComponentName(this, CameraDelayedReceiverActivity.class);
        final PackageManager pm = getPackageManager();
        try {
            if (pm.getActivityInfo(component, PackageManager.MATCH_DISABLED_COMPONENTS).applicationInfo.uid != Process.myUid()) {
                result.putString("protocolError", "Foreign component owner");
                return result;
            }
            final boolean arm = "arm-delayed".equals(operation);
            final int wanted;
            if (arm) {
                if (delayedLease != null || received != null ||
                        pm.getComponentEnabledSetting(component) != PackageManager.COMPONENT_ENABLED_STATE_DEFAULT ||
                        pm.getActivityInfo(component, PackageManager.MATCH_DISABLED_COMPONENTS).enabled) {
                    result.putString("protocolError", "Delayed component is not an unowned disabled default");
                    return result;
                }
                // Retain ownership before the native mutation or its reply can fail.
                originalDelayedState = PackageManager.COMPONENT_ENABLED_STATE_DEFAULT;
                delayedLease = lease;
                wanted = PackageManager.COMPONENT_ENABLED_STATE_ENABLED;
            } else {
                if (!lease.equals(delayedLease) || originalDelayedState == null ||
                        originalDelayedState != PackageManager.COMPONENT_ENABLED_STATE_DEFAULT) {
                    result.putString("protocolError", "Unknown delayed-component lease");
                    return result;
                }
                wanted = originalDelayedState;
            }
            // This is the recipient's real SDK operation. DONT_KILL_APP retains
            // its bound service/lease; no shell text, root, grant or state fallback.
            pm.setComponentEnabledSetting(component, wanted, PackageManager.DONT_KILL_APP);
            if (pm.getComponentEnabledSetting(component) != wanted ||
                    pm.getActivityInfo(component, PackageManager.MATCH_DISABLED_COMPONENTS).enabled != arm) {
                result.putString("protocolError", "Native delayed-component state not verified");
                return result;
            }
            result.putBoolean("delayedControlVerified", true);
            result.putString("controlledComponent", component.flattenToString());
            result.putString("controlledLease", lease);
            result.putString("controlledOperation", operation);
            result.putInt("componentOwnerUid", Process.myUid());
            result.putInt("componentState", wanted);
            result.putInt("originalComponentState", originalDelayedState);
            if (!arm) { delayedLease = null; originalDelayedState = null; }
        } catch (Exception failure) {
            // Preserve refusal and partial lease, never accept missing native readback.
            result.putString("protocolError", "Delayed component failed: " + failure.getClass().getSimpleName());
        }
        return result;
    }
}
