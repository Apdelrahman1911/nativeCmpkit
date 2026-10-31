// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.iodocuments;

import android.app.Application;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Process;
import android.provider.DocumentsContract;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.UUID;

/** Only fixed synthetic fixtures, native identities and bounded diagnostic values. */
final class IoFixture {
    static final String PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.iodocuments";
    static final String REPORTER = "com.mohamedrejeb.calf.calfio.test";
    static final String AUTHORITY = PACKAGE + ".documents";
    static final String ROOT = "nativecmpkit-owned-root";
    static final String ROOT_NAME = "NativeCmpKit owned IO folder";
    static final String[] IDS = {"bookmark.txt", "decoder.bin", "cancel.bin", "survivor.bin"};
    static final String GENERATION = UUID.randomUUID().toString();
    static final String STATS = "nativecmpkit-io-stats", RESET = "nativecmpkit-io-reset";
    static Uri tree() { return DocumentsContract.buildTreeDocumentUri(AUTHORITY, ROOT); }
    static boolean known(String id) { return Arrays.asList(IDS).contains(id); }
    static byte[] body(String id) {
        if ("bookmark.txt".equals(id)) return "NativeCmpKit actual Android bookmark bytes".getBytes(StandardCharsets.UTF_8);
        int size;
        if ("decoder.bin".equals(id)) size = 32771;
        else if ("cancel.bin".equals(id)) size = 32779;
        else if ("survivor.bin".equals(id)) size = 8199;
        else throw new IllegalArgumentException("Unknown fixed owned document");
        byte[] bytes = new byte[size];
        for (int i = 0; i < size; i++) bytes[i] = (byte) (i % 251);
        return bytes;
    }
    static void requireReporter(Context context, int uid) {
        if (Build.VERSION.SDK_INT != 35) throw new IllegalStateException("Only the selected API35 fixture is permitted");
        String[] packages = context.getPackageManager().getPackagesForUid(uid);
        if (packages == null || !Arrays.asList(packages).contains(REPORTER) ||
            context.getPackageManager().checkSignatures(REPORTER, context.getPackageName()) != PackageManager.SIGNATURE_MATCH)
            throw new SecurityException("Only the native signature-authenticated IO reporter is permitted");
    }
    static void requireControlCaller(Context context, int uid) {
        if (uid != Process.myUid()) requireReporter(context, uid);
    }
    static Bundle stamp(Bundle result) {
        result.putInt("uid", Process.myUid()); result.putInt("pid", Process.myPid());
        result.putString("generation", GENERATION); result.putString("process", Application.getProcessName());
        return result;
    }
}
