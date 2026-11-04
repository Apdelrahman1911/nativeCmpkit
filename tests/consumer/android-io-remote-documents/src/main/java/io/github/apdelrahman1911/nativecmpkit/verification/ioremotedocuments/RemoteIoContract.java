// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments;

import android.app.Application;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Process;
import android.os.UserHandle;
import android.provider.DocumentsContract;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/** Finite test-only identities and protocol. Never a payload or local-file fallback. */
final class RemoteIoContract {
    static final String PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments";
    static final String REPORTER = "com.mohamedrejeb.calf.calfio.test";
    static final String AUTHORITY = PACKAGE + ".documents";
    static final String PERMISSION = PACKAGE + ".CONTROL_REMOTE_IO";
    static final String PROVIDER_PROCESS = PACKAGE + ":nativecmpkit_io_remote_provider";
    static final String GENERATION = UUID.randomUUID().toString();
    static final int PAYLOAD_BYTES = 4097, HELD_BYTES = 131073;
    static final int MAX_HEADER_BYTES = 8192, MAX_HEADER_LINES = 64, MAX_METADATA_BYTES = 8192;
    static final int MAX_JOURNAL = 128, MAX_CONNECTIONS = 4, ACCEPT_BACKLOG = 8;
    static final int CONNECT_MS = 2000, READ_MS = 5000, HELD_READ_MS = 15000;
    static final int HELD_WATCHDOG_MS = 20000, JOIN_MS = 10000;
    private RemoteIoContract() {}

    static String hexNonce(String value) {
        if (value == null || !value.matches("[a-f0-9]{32}"))
            throw new IllegalArgumentException("Exact owned nonce required");
        return value;
    }
    static int port(int value) {
        if (value < 1024 || value > 65535) throw new IllegalArgumentException("Owned ephemeral port refused");
        return value;
    }
    static String root(String session) { return "remote-root-" + hexNonce(session); }
    static String home(String session) { return "remote-home-" + hexNonce(session); }
    static String folder(String session) { return "remote-folder-" + hexNonce(session); }
    static String folderName(String session) { return "NativeCmpKitIo55-" + hexNonce(session); }
    static String payload(String session) { return "remote-payload-" + hexNonce(session); }
    static String held(String session) { return "remote-held-" + hexNonce(session); }
    static Uri tree(String session) { return DocumentsContract.buildTreeDocumentUri(AUTHORITY, folder(session)); }
    static boolean known(String session, String id) {
        return home(session).equals(id) || folder(session).equals(id) || payload(session).equals(id) || held(session).equals(id);
    }
    static void requireReporter(Context context, int uid, String process) {
        if (Build.VERSION.SDK_INT != 35 || !Process.myUserHandle().equals(UserHandle.getUserHandleForUid(0)) ||
            !PACKAGE.equals(context.getPackageName()) || !process.equals(Application.getProcessName()))
            throw new SecurityException("Exact native API35 user-zero helper process required");
        String[] packages = context.getPackageManager().getPackagesForUid(uid);
        if (uid == Process.myUid() || packages == null || packages.length != 1 || !REPORTER.equals(packages[0]) ||
            context.getPackageManager().checkSignatures(REPORTER, PACKAGE) != PackageManager.SIGNATURE_MATCH)
            throw new SecurityException("Only the separate-UID signature-authenticated reporter is permitted");
    }
    static void keys(Bundle request, String... additional) {
        Set<String> expected = new HashSet<>(Arrays.asList(additional));
        expected.add("nonce"); expected.add("operation");
        if (!request.keySet().equals(expected) || !(request.get("nonce") instanceof String) ||
            !(request.get("operation") instanceof String))
            throw new IllegalArgumentException("Partial or extra native control fields refused");
        hexNonce(request.getString("nonce"));
    }
    static String string(Bundle request, String key) {
        if (!(request.get(key) instanceof String)) throw new IllegalArgumentException("Typed native string required");
        return hexNonce(request.getString(key));
    }
    static int integer(Bundle request, String key) {
        if (!(request.get(key) instanceof Integer)) throw new IllegalArgumentException("Typed native integer required");
        return request.getInt(key);
    }
    static Bundle stamp(Bundle reply) {
        reply.putInt("uid", Process.myUid()); reply.putInt("pid", Process.myPid());
        reply.putString("process", Application.getProcessName()); reply.putString("generation", GENERATION);
        return reply;
    }
    static MessageDigest digest() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException("Native SHA-256 unavailable", failure); }
    }
    static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder(bytes.length * 2);
        for (byte value : bytes) result.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
        return result.toString();
    }
    static String sha256(byte[] bytes) { return hex(digest().digest(bytes)); }
    static byte[] ascii(String value) {
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (ch != '\r' && ch != '\n' && ch != '\t' && (ch < 32 || ch > 126))
                throw new IllegalArgumentException("Only bounded ASCII protocol fields are permitted");
        }
        return value.getBytes(StandardCharsets.US_ASCII);
    }
    static String error(Throwable failure) { return failure.getClass().getSimpleName(); }
}
