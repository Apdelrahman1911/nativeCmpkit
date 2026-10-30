// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.geoprobe;

import android.Manifest;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.Process;
import android.os.RemoteException;
import androidx.core.content.ContextCompat;
import androidx.core.location.LocationManagerCompat;
import androidx.lifecycle.Lifecycle;
import com.google.android.gms.common.GoogleApiAvailabilityLight;
import com.mohamedrejeb.calf.geo.LocationStartResult;
import com.mohamedrejeb.calf.geo.LocationTracker;
import com.mohamedrejeb.calf.geo.LocationTrackingError;
import com.mohamedrejeb.calf.geo.LocationTrackingSnapshot;
import java.util.Arrays;
import java.util.UUID;
import kotlin.ResultKt;
import kotlin.coroutines.Continuation;
import kotlin.coroutines.CoroutineContext;
import kotlin.coroutines.EmptyCoroutineContext;
import kotlin.coroutines.intrinsics.IntrinsicsKt;

/** Finite signature-protected probe of the real public tracker, not a fake provider. */
public final class GeoProbeService extends Service {
    private static final String REPORTER = "com.mohamedrejeb.calf.calfgeo.test";
    private final Handler main = new Handler(Looper.getMainLooper());
    private final String generation = UUID.randomUUID().toString();
    private LocationTracker tracker;
    private final Messenger endpoint = new Messenger(new Handler(Looper.getMainLooper()) {
        @Override public void handleMessage(Message message) { receive(message); }
    });

    @Override public IBinder onBind(Intent intent) { return endpoint.getBinder(); }

    private void receive(Message request) {
        String[] names = getPackageManager().getPackagesForUid(request.sendingUid);
        if (request.replyTo == null || names == null || !Arrays.asList(names).contains(REPORTER) ||
            getPackageManager().checkSignatures(getPackageName(), REPORTER) != PackageManager.SIGNATURE_MATCH) return;
        final Message message = Message.obtain(request);
        String nonce = message.getData().getString("nonce", "");
        String operation = message.getData().getString("operation", "");
        if (!nonce.matches("[a-f0-9]{32}")) { message.recycle(); return; }
        try {
            switch (operation) {
                case "snapshot": reply(message, null, null); break;
                case "create":
                    if (tracker != null) throw new IllegalStateException("Existing owned tracker");
                    tracker = new LocationTracker();
                    reply(message, null, null); break;
                case "bind":
                    GeoProbeActivity activity = GeoProbeActivity.active;
                    if (tracker == null || activity == null ||
                        !activity.getLifecycle().getCurrentState().isAtLeast(Lifecycle.State.STARTED)) {
                        throw new IllegalStateException("Actual foreground owner unavailable");
                    }
                    tracker.bind(activity.getLifecycle(), activity);
                    reply(message, null, null); break;
                case "start-main": start(message); break;
                case "start-background": new Thread(() -> start(message), "owned-geo-start").start(); break;
                case "stop":
                    if (tracker == null) throw new IllegalStateException("No tracker");
                    tracker.stopTracking(); reply(message, null, null); break;
                case "close":
                    if (tracker != null) { tracker.close(); tracker = null; }
                    reply(message, null, null); break;
                default: reply(message, null, "unknown-operation");
            }
        } catch (Exception failure) { reply(message, null, "probe-operation-failed"); }
        // For an asynchronous start, reply owns the copied message until completion.
    }

    private void start(Message message) {
        final LocationTracker current = tracker;
        if (current == null) { main.post(() -> reply(message, null, "no-tracker")); return; }
        try {
            Object immediate = current.startTrackingWithResult(new Continuation<LocationStartResult>() {
                @Override public CoroutineContext getContext() { return EmptyCoroutineContext.INSTANCE; }
                @Override public void resumeWith(Object result) {
                    main.post(() -> {
                        try { ResultKt.throwOnFailure(result); reply(message, (LocationStartResult) result, null); }
                        catch (Exception failure) { reply(message, null, "native-start-threw"); }
                    });
                }
            });
            if (immediate != IntrinsicsKt.getCOROUTINE_SUSPENDED()) {
                main.post(() -> reply(message, (LocationStartResult) immediate, null));
            }
        } catch (Exception failure) { main.post(() -> reply(message, null, "native-start-threw")); }
    }

    private void reply(Message request, LocationStartResult result, String error) {
        Bundle data = new Bundle();
        data.putString("nonce", request.getData().getString("nonce"));
        data.putInt("pid", Process.myPid()); data.putInt("uid", Process.myUid());
        data.putString("generation", generation);
        data.putBoolean("coarse", ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED);
        data.putBoolean("fine", ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED);
        data.putInt("gms", GoogleApiAvailabilityLight.getInstance().isGooglePlayServicesAvailable(this));
        try {
            ApplicationInfo gms = getPackageManager().getApplicationInfo("com.google.android.gms", 0);
            data.putBoolean("gmsInstalled", true);
            data.putBoolean("gmsSystem", (gms.flags & (ApplicationInfo.FLAG_SYSTEM | ApplicationInfo.FLAG_UPDATED_SYSTEM_APP)) != 0);
        } catch (PackageManager.NameNotFoundException absent) {
            data.putBoolean("gmsInstalled", false); data.putBoolean("gmsSystem", false);
        }
        LocationManager manager = (LocationManager) getSystemService(LOCATION_SERVICE);
        data.putBoolean("settings", manager != null && LocationManagerCompat.isLocationEnabled(manager));
        GeoProbeActivity activity = GeoProbeActivity.active;
        data.putBoolean("foreground", activity != null && activity.getLifecycle().getCurrentState().isAtLeast(Lifecycle.State.RESUMED));
        if (tracker != null) {
            LocationTrackingSnapshot snapshot = tracker.getSnapshotState().getValue();
            data.putString("phase", snapshot.getPhase().name());
            if (snapshot.getPermissionAccuracy() != null) data.putString("accuracy", snapshot.getPermissionAccuracy().name());
            if (snapshot.getCleanupError() != null) data.putString("cleanup", snapshot.getCleanupError().getReason().name());
        }
        if (result == LocationStartResult.Started.INSTANCE) data.putString("result", "Started");
        else if (result == LocationStartResult.AlreadyStarted.INSTANCE) data.putString("result", "AlreadyStarted");
        else if (result instanceof LocationStartResult.Failed) {
            LocationTrackingError failure = ((LocationStartResult.Failed) result).getError();
            data.putString("result", "Failed"); data.putString("reason", failure.getReason().name());
            if (failure.getPlatformCode() != null) data.putInt("platformCode", failure.getPlatformCode());
        } else if (result != null) data.putString("probeError", "unexpected-native-result");
        if (error != null) data.putString("probeError", error);
        Message response = Message.obtain(); response.setData(data);
        try { request.replyTo.send(response); } catch (RemoteException disconnected) { /* Reporter observes its own timeout/death. */ }
        finally { response.recycle(); request.recycle(); }
    }

    @Override public boolean onUnbind(Intent intent) {
        if (tracker != null) { tracker.close(); tracker = null; }
        return false;
    }
    @Override public void onDestroy() {
        if (tracker != null) { tracker.close(); tracker = null; }
        super.onDestroy();
    }
}
