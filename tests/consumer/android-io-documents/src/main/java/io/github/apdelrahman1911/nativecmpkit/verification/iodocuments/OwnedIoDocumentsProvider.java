// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.iodocuments;

import android.database.Cursor;
import android.database.MatrixCursor;
import android.os.Binder;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract.Document;
import android.provider.DocumentsContract.Root;
import android.provider.DocumentsProvider;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** Real remote DocumentsProvider over fixed sandbox-owned bytes; no resolver or descriptor shadows. */
public final class OwnedIoDocumentsProvider extends DocumentsProvider {
    private static final String[] COLUMNS = {Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,
        Document.COLUMN_MIME_TYPE, Document.COLUMN_SIZE, Document.COLUMN_FLAGS};
    private static final String[] ROOT_COLUMNS = {Root.COLUMN_ROOT_ID, Root.COLUMN_DOCUMENT_ID, Root.COLUMN_TITLE, Root.COLUMN_FLAGS};
    private static final class Record {
        final AtomicInteger opens = new AtomicInteger(), closes = new AtomicInteger(), closeErrors = new AtomicInteger(), writes = new AtomicInteger();
        volatile long device, inode, fdInfoInode; volatile int mode;
    }
    private final ConcurrentHashMap<String, Record> records = new ConcurrentHashMap<>();
    private final Handler closeHandler = new Handler(Looper.getMainLooper());
    private File root;

    @Override public boolean onCreate() {
        root = new File(getContext().getCacheDir(), "nativecmpkit-owned-io-documents");
        if (!root.isDirectory() && !root.mkdirs()) return false;
        try { reset(); return true; } catch (IOException failure) { return false; }
    }

    private synchronized void reset() throws IOException {
        for (Record record : records.values()) {
            if (record.opens.get() != record.closes.get())
                throw new IllegalStateException("An owned document still has a transferred descriptor");
            if (record.closeErrors.get() != 0 || record.writes.get() != 0)
                throw new IllegalStateException("Owned native descriptor failure cannot be reset away");
        }
        for (String id : IoFixture.IDS) {
            File file = new File(root, id);
            if (!file.getCanonicalFile().getParentFile().equals(root.getCanonicalFile()))
                throw new IOException("Fixed fixture escaped its owned sandbox");
            try (FileOutputStream out = new FileOutputStream(file)) { out.write(IoFixture.body(id)); }
            records.put(id, new Record());
        }
    }

    private File resolve(String id) throws FileNotFoundException {
        if (IoFixture.ROOT.equals(id)) return root;
        if (!IoFixture.known(id)) throw new FileNotFoundException("Unknown fixed owned document");
        return new File(root, id);
    }

    @Override public ParcelFileDescriptor openDocument(String id, String mode, CancellationSignal signal) throws FileNotFoundException {
        if (signal != null) signal.throwIfCanceled();
        File file = resolve(id); Record record = records.get(id);
        if (record == null) throw new FileNotFoundException("A folder is not a byte stream");
        if (!"r".equals(mode)) { record.writes.incrementAndGet(); throw new SecurityException("Owned fixture is read-only"); }
        ParcelFileDescriptor descriptor = null;
        try {
            descriptor = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY, closeHandler, error -> {
                if (error != null) record.closeErrors.incrementAndGet();
                record.closes.incrementAndGet(); // Publish completion only after the error witness.
            });
            StructStat stat = Os.fstat(descriptor.getFileDescriptor());
            long kernelInode = fdInfoInode(descriptor.getFd());
            if (!OsConstants.S_ISREG(stat.st_mode) || stat.st_ino == 0 || kernelInode != stat.st_ino)
                throw new IllegalStateException("Native REG descriptor calibration failed");
            record.device = stat.st_dev; record.inode = stat.st_ino; record.mode = stat.st_mode; record.fdInfoInode = kernelInode;
            record.opens.incrementAndGet(); return descriptor;
        } catch (Exception failure) {
            if (descriptor != null) try { descriptor.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
            // The reporter receives a truthful setup refusal, never an uncalibrated success.
            FileNotFoundException reported = new FileNotFoundException("Owned native descriptor unavailable");
            reported.initCause(failure); throw reported;
        }
    }

    private static long fdInfoInode(int fd) throws IOException {
        String found = null; int lines = 0, bytes = 0;
        try (BufferedReader reader = new BufferedReader(new FileReader("/proc/self/fdinfo/" + fd))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (++lines > 64 || (bytes += line.length()) > 4096) throw new IOException("Unbounded owned fdinfo");
                if (!line.startsWith("ino:")) continue;
                if (found != null) throw new IOException("Duplicate owned fdinfo inode");
                found = line.substring(4).trim();
                if (!found.matches("[0-9]{1,20}")) throw new IOException("Invalid owned fdinfo inode");
            }
        }
        if (found == null) throw new IOException("Missing owned fdinfo inode");
        try { return Long.parseUnsignedLong(found); } catch (NumberFormatException failure) { throw new IOException("Out-of-range owned inode"); }
    }

    private void addDocument(MatrixCursor cursor, String id) throws FileNotFoundException {
        File file = resolve(id); MatrixCursor.RowBuilder row = cursor.newRow();
        for (String column : cursor.getColumnNames()) {
            if (Document.COLUMN_DOCUMENT_ID.equals(column)) row.add(id);
            else if (Document.COLUMN_DISPLAY_NAME.equals(column)) row.add(IoFixture.ROOT.equals(id) ? IoFixture.ROOT_NAME : id);
            else if (Document.COLUMN_MIME_TYPE.equals(column)) row.add(file.isDirectory() ? Document.MIME_TYPE_DIR : id.endsWith(".txt") ? "text/plain" : "application/octet-stream");
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
        if (!IoFixture.ROOT.equals(id)) throw new FileNotFoundException("Only one fixed owned folder");
        MatrixCursor cursor = new MatrixCursor(projection == null ? COLUMNS : projection);
        for (String child : IoFixture.IDS) addDocument(cursor, child); return cursor;
    }
    @Override public boolean isChildDocument(String parent, String child) {
        return IoFixture.ROOT.equals(parent) && IoFixture.known(child);
    }
    @Override public Cursor queryRoots(String[] projection) {
        MatrixCursor cursor = new MatrixCursor(projection == null ? ROOT_COLUMNS : projection); MatrixCursor.RowBuilder row = cursor.newRow();
        for (String column : cursor.getColumnNames()) {
            if (Root.COLUMN_ROOT_ID.equals(column) || Root.COLUMN_DOCUMENT_ID.equals(column)) row.add(IoFixture.ROOT);
            else if (Root.COLUMN_TITLE.equals(column)) row.add(IoFixture.ROOT_NAME);
            else if (Root.COLUMN_FLAGS.equals(column)) row.add(Root.FLAG_LOCAL_ONLY | Root.FLAG_SUPPORTS_IS_CHILD);
            else row.add(null);
        }
        return cursor;
    }
    @Override public Bundle call(String method, String arg, Bundle extras) {
        if (!IoFixture.STATS.equals(method) && !IoFixture.RESET.equals(method)) return super.call(method, arg, extras);
        IoFixture.requireControlCaller(getContext(), Binder.getCallingUid());
        if (IoFixture.RESET.equals(method)) {
            try { reset(); } catch (IOException failure) { throw new IllegalStateException("Owned reset failed", failure); }
            return IoFixture.stamp(new Bundle());
        }
        Record record = records.get(arg); if (record == null) throw new IllegalArgumentException("Unknown fixed owned document");
        Bundle result = new Bundle(); result.putInt("opens", record.opens.get()); result.putInt("closes", record.closes.get());
        result.putInt("closeErrors", record.closeErrors.get()); result.putInt("writes", record.writes.get());
        result.putLong("device", record.device); result.putLong("inode", record.inode); result.putInt("mode", record.mode);
        result.putLong("fdInfoInode", record.fdInfoInode); result.putLong("length", new File(root, arg).length());
        return IoFixture.stamp(result);
    }
}
