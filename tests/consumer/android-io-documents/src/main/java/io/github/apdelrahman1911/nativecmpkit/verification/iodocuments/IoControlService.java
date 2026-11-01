// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.iodocuments;

import android.app.Application;
import android.app.Service;
import android.content.ComponentName;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ProviderInfo;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Message;
import android.os.Messenger;
import android.os.Process;
import android.os.RemoteException;
import android.os.UserHandle;
import java.util.Map;

/** Fixed owner operations; the durable unavailable lease never targets another package or URI. */
public final class IoControlService extends Service {
    private static final ComponentName OWNED_PROVIDER = new ComponentName(IoFixture.PACKAGE,
        IoFixture.PACKAGE + ".OwnedIoDocumentsProvider");
    private static final String LEASE_PREFERENCES = "nativecmpkit-owned-provider-unavailable";
    private static final String LEASE_TOKEN = "leaseToken", ORIGINAL_SETTING = "originalSetting";

    private SharedPreferences leasePreferences() {
        return getSharedPreferences(LEASE_PREFERENCES, MODE_PRIVATE);
    }

    private void requireNoUnavailableLease() {
        if (!leasePreferences().getAll().isEmpty())
            throw new IllegalStateException("Restore the exact owned unavailable lease before any provider operation");
    }

    private void requireOwnedProvider() throws PackageManager.NameNotFoundException {
        if (!IoFixture.PACKAGE.equals(getPackageName()) ||
            !IoFixture.PACKAGE.equals(Application.getProcessName()) ||
            !Process.myUserHandle().equals(UserHandle.getUserHandleForUid(0)))
            throw new IllegalStateException("Only the exact own main control process in user zero is permitted");
        ProviderInfo declared = getPackageManager().getProviderInfo(OWNED_PROVIDER, PackageManager.MATCH_DISABLED_COMPONENTS);
        // ComponentInfo.enabled is the manifest field, not evidence of the actual component override.
        if (!IoFixture.PACKAGE.equals(declared.packageName) || !OWNED_PROVIDER.getClassName().equals(declared.name) ||
            !IoFixture.AUTHORITY.equals(declared.authority) || declared.applicationInfo.uid != Process.myUid() ||
            !declared.enabled || !declared.exported || !declared.grantUriPermissions ||
            !"android.permission.MANAGE_DOCUMENTS".equals(declared.readPermission) ||
            !"android.permission.MANAGE_DOCUMENTS".equals(declared.writePermission) ||
            !(IoFixture.PACKAGE + ":nativecmpkit_io_provider").equals(declared.processName))
            throw new IllegalStateException("The fixed owned provider manifest and UID must match exactly");
    }

    private void requireExactAuthority() {
        ProviderInfo resolved = getPackageManager().resolveContentProvider(IoFixture.AUTHORITY, 0);
        if (resolved == null || !IoFixture.PACKAGE.equals(resolved.packageName) ||
            !OWNED_PROVIDER.getClassName().equals(resolved.name) ||
            !IoFixture.AUTHORITY.equals(resolved.authority) || resolved.applicationInfo.uid != Process.myUid())
            throw new IllegalStateException("Ordinary authority resolution must name the exact owned component and UID");
    }

    private String requireLeaseRequest(Bundle request) {
        String token = request.getString(LEASE_TOKEN);
        if (token == null || !token.matches("[a-f0-9]{32}") || request.size() != 3 ||
            !request.containsKey("nonce") || !request.containsKey("operation"))
            throw new IllegalArgumentException("Only one exact nonce-bound owned lease token is permitted");
        return token;
    }

    private void requireMatchingLease(String token) {
        Map<String, ?> saved = leasePreferences().getAll();
        if (saved.size() != 2 || !token.equals(saved.get(LEASE_TOKEN)) ||
            !Integer.valueOf(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT).equals(saved.get(ORIGINAL_SETTING)))
            throw new IllegalStateException("A missing, partial or foreign owned lease cannot be restored");
    }

    private void leaseReceipt(Bundle result, String token, boolean held) {
        int expected = held ? PackageManager.COMPONENT_ENABLED_STATE_DISABLED : PackageManager.COMPONENT_ENABLED_STATE_DEFAULT;
        int actual = getPackageManager().getComponentEnabledSetting(OWNED_PROVIDER);
        if (actual != expected) throw new IllegalStateException("Exact native component setting readback did not match");
        if (held) {
            if (getPackageManager().resolveContentProvider(IoFixture.AUTHORITY, 0) != null)
                throw new IllegalStateException("The disabled owned authority must be absent from ordinary resolution");
            requireMatchingLease(token);
        } else {
            requireExactAuthority();
            requireNoUnavailableLease();
        }
        result.putString("unavailableComponent", OWNED_PROVIDER.flattenToString());
        result.putString("unavailableAuthority", IoFixture.AUTHORITY);
        result.putInt("unavailableOwnerUid", Process.myUid()); result.putInt("unavailableUserId", 0);
        result.putString("unavailableLeaseToken", token);
        result.putInt("unavailableOriginalSetting", PackageManager.COMPONENT_ENABLED_STATE_DEFAULT);
        result.putInt("unavailableActualSetting", actual);
        result.putBoolean("unavailableAuthorityPresent", !held); result.putBoolean("unavailableLeaseHeld", held);
    }

    private void acquireUnavailable(Bundle request, Bundle result) throws PackageManager.NameNotFoundException {
        String token = requireLeaseRequest(request);
        requireOwnedProvider(); requireNoUnavailableLease(); requireExactAuthority();
        if (getPackageManager().getComponentEnabledSetting(OWNED_PROVIDER) != PackageManager.COMPONENT_ENABLED_STATE_DEFAULT)
            throw new IllegalStateException("An enabled override is not the exact original manifest-default state");
        // Commit and exact readback precede mutation. Any failure keeps this test red and ownership intact.
        if (!leasePreferences().edit().putString(LEASE_TOKEN, token)
            .putInt(ORIGINAL_SETTING, PackageManager.COMPONENT_ENABLED_STATE_DEFAULT).commit())
            throw new IllegalStateException("The exact original-state lease could not be durably recorded");
        requireMatchingLease(token);
        getPackageManager().setComponentEnabledSetting(OWNED_PROVIDER, PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
            PackageManager.DONT_KILL_APP);
        leaseReceipt(result, token, true);
    }

    private void restoreUnavailable(Bundle request, Bundle result) throws PackageManager.NameNotFoundException {
        String token = requireLeaseRequest(request);
        requireOwnedProvider(); requireMatchingLease(token);
        int actual = getPackageManager().getComponentEnabledSetting(OWNED_PROVIDER);
        // DEFAULT also covers a failed acquire after lease commit but before the native mutation.
        if (actual != PackageManager.COMPONENT_ENABLED_STATE_DISABLED && actual != PackageManager.COMPONENT_ENABLED_STATE_DEFAULT)
            throw new IllegalStateException("Unknown or externally changed component state cannot be overwritten");
        getPackageManager().setComponentEnabledSetting(OWNED_PROVIDER, PackageManager.COMPONENT_ENABLED_STATE_DEFAULT,
            PackageManager.DONT_KILL_APP);
        if (getPackageManager().getComponentEnabledSetting(OWNED_PROVIDER) != PackageManager.COMPONENT_ENABLED_STATE_DEFAULT)
            throw new IllegalStateException("The exact original native component setting was not restored");
        requireExactAuthority(); // Never clear ownership before exact DEFAULT and authority/component/UID readback.
        if (!leasePreferences().edit().clear().commit())
            throw new IllegalStateException("The verified restored lease could not be durably cleared");
        leaseReceipt(result, token, false);
    }

    private final Messenger endpoint = new Messenger(new Handler(message -> {
        Bundle result = new Bundle(); String nonce = message.getData().getString("nonce");
        if (nonce == null || !nonce.matches("[a-f0-9]{32}") || message.replyTo == null) return true;
        result.putString("nonce", nonce);
        try {
            IoFixture.requireReporter(this, message.sendingUid);
            String operation = message.getData().getString("operation");
            if ("snapshot".equals(operation)) { /* Identity only. */ }
            else if ("acquire-unavailable".equals(operation)) acquireUnavailable(message.getData(), result);
            else if ("restore-unavailable".equals(operation)) restoreUnavailable(message.getData(), result);
            else if ("stats".equals(operation)) {
                requireNoUnavailableLease();
                String id = message.getData().getString("id");
                if (!IoFixture.known(id)) throw new IllegalArgumentException("Unknown fixed owned document");
                result.putBundle("provider", getContentResolver().call(Uri.parse("content://" + IoFixture.AUTHORITY), IoFixture.STATS, id, null));
            } else if ("revoke".equals(operation) || "reset".equals(operation)) {
                requireNoUnavailableLease();
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
