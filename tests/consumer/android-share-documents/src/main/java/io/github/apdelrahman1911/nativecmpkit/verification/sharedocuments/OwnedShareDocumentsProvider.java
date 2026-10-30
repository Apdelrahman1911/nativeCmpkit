// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.sharedocuments;

import android.content.pm.PackageManager;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.os.Binder;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelFileDescriptor;
import android.os.Process;
import android.provider.DocumentsContract.Document;
import android.provider.DocumentsContract.Root;
import android.provider.DocumentsProvider;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** Actual third-UID read-only DocumentsProvider with finite fixed synthetic bytes. */
public final class OwnedShareDocumentsProvider extends DocumentsProvider {
    static final String REPORTER = "com.mohamedrejeb.calf.calfshare.test";
    static final String[] IDS = {"nativecmpkit-owned.txt", "nativecmpkit-owned.png"};
    private static final String[] COLUMNS = {Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,
        Document.COLUMN_MIME_TYPE, Document.COLUMN_SIZE, Document.COLUMN_FLAGS};
    private static final String[] ROOT_COLUMNS = {Root.COLUMN_ROOT_ID, Root.COLUMN_DOCUMENT_ID, Root.COLUMN_TITLE, Root.COLUMN_FLAGS};
    private static final class Record {
        final AtomicInteger opens = new AtomicInteger(), closes = new AtomicInteger(), closeErrors = new AtomicInteger(), writes = new AtomicInteger();
    }
    private final HashMap<String, Record> records = new HashMap<>();
    private File root;
    private final Handler closeHandler = new Handler(Looper.getMainLooper());

    @Override public boolean onCreate() {
        root = new File(getContext().getCacheDir(), "owned-share-documents");
        if (!root.isDirectory() && !root.mkdirs()) return false;
        byte[][] bodies = {"NativeCmpKit synthetic SAF document".getBytes(StandardCharsets.UTF_8),
            android.util.Base64.decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==", android.util.Base64.DEFAULT)};
        try {
            for (int i = 0; i < IDS.length; i++) {
                File file = new File(root, IDS[i]);
                try (FileOutputStream out = new FileOutputStream(file)) { out.write(bodies[i]); }
                records.put(IDS[i], new Record());
            }
        } catch (IOException failure) { return false; }
        return true;
    }

    private File resolve(String id) throws FileNotFoundException {
        if ("root".equals(id)) return root;
        if (!Arrays.asList(IDS).contains(id)) throw new FileNotFoundException("Only fixed owned synthetic documents exist");
        return new File(root, id);
    }

    @Override public ParcelFileDescriptor openDocument(String id, String mode, CancellationSignal signal) throws FileNotFoundException {
        if (signal != null) signal.throwIfCanceled();
        File file = resolve(id); Record record = records.get(id);
        if (record == null) throw new FileNotFoundException("No directory descriptor");
        if (!"r".equals(mode)) { record.writes.incrementAndGet(); throw new SecurityException("Read-only synthetic document"); }
        try {
            ParcelFileDescriptor descriptor = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY, closeHandler, error -> {
                record.closes.incrementAndGet(); if (error != null) record.closeErrors.incrementAndGet();
            });
            record.opens.incrementAndGet(); return descriptor;
        } catch (IOException failure) { throw new FileNotFoundException("Owned document descriptor unavailable"); }
    }

    private void addDocument(MatrixCursor cursor, String id) throws FileNotFoundException {
        File file = resolve(id); MatrixCursor.RowBuilder row = cursor.newRow();
        for (String column : cursor.getColumnNames()) {
            if (Document.COLUMN_DOCUMENT_ID.equals(column)) row.add(id);
            else if (Document.COLUMN_DISPLAY_NAME.equals(column)) row.add(file.getName());
            else if (Document.COLUMN_MIME_TYPE.equals(column)) row.add(file.isDirectory() ? Document.MIME_TYPE_DIR : id.endsWith(".png") ? "image/png" : "text/plain");
            else if (Document.COLUMN_SIZE.equals(column)) row.add(file.isDirectory() ? null : file.length());
            else if (Document.COLUMN_FLAGS.equals(column)) row.add(0);
            else row.add(null);
        }
    }

    @Override public Cursor queryDocument(String id, String[] projection) throws FileNotFoundException {
        MatrixCursor cursor = new MatrixCursor(projection == null ? COLUMNS : projection);
        addDocument(cursor, id); return cursor;
    }

    @Override public Cursor queryChildDocuments(String id, String[] projection, String order) throws FileNotFoundException {
        if (!"root".equals(id)) throw new FileNotFoundException("Only one owned root");
        MatrixCursor cursor = new MatrixCursor(projection == null ? COLUMNS : projection);
        for (String document : IDS) addDocument(cursor, document); return cursor;
    }

    @Override public Cursor queryRoots(String[] projection) {
        MatrixCursor cursor = new MatrixCursor(projection == null ? ROOT_COLUMNS : projection); MatrixCursor.RowBuilder row = cursor.newRow();
        for (String column : cursor.getColumnNames()) {
            if (Root.COLUMN_ROOT_ID.equals(column) || Root.COLUMN_DOCUMENT_ID.equals(column)) row.add("root");
            else if (Root.COLUMN_TITLE.equals(column)) row.add("NativeCmpKit owned third-UID documents");
            else if (Root.COLUMN_FLAGS.equals(column)) row.add(Root.FLAG_LOCAL_ONLY);
            else row.add(null);
        }
        return cursor;
    }

    @Override public Bundle call(String method, String arg, Bundle extras) {
        if (!"nativecmpkit-share-document-stats".equals(method)) return super.call(method, arg, extras);
        String[] packages = getContext().getPackageManager().getPackagesForUid(Binder.getCallingUid());
        if (packages == null || !Arrays.asList(packages).contains(REPORTER) ||
                getContext().getPackageManager().checkSignatures(REPORTER, getContext().getPackageName()) != PackageManager.SIGNATURE_MATCH)
            throw new SecurityException("Only the signature-authenticated owning reporter can query counts");
        Record record = records.get(arg); if (record == null) throw new IllegalArgumentException("Unknown fixed document");
        Bundle result = new Bundle(); result.putInt("uid", Process.myUid()); result.putInt("pid", Process.myPid());
        result.putInt("opens", record.opens.get()); result.putInt("closes", record.closes.get());
        result.putInt("closeErrors", record.closeErrors.get()); result.putInt("writes", record.writes.get()); return result;
    }
}
