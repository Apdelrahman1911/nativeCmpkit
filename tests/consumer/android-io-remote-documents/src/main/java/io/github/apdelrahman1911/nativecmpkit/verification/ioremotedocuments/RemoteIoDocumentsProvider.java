// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments;

import android.content.Context;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.OperationCanceledException;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.DocumentsProvider;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Separate native process. Only immutable HTTP-provisioned root/ancestry is cached.
 * ALL document metadata, listings and bytes use the real backend. fdinfo is diagnostic only.
 */
public final class RemoteIoDocumentsProvider extends DocumentsProvider {
    private static volatile State state;
    private static final String[] ROOT_COLUMNS = {DocumentsContract.Root.COLUMN_ROOT_ID,
        DocumentsContract.Root.COLUMN_DOCUMENT_ID, DocumentsContract.Root.COLUMN_TITLE, DocumentsContract.Root.COLUMN_FLAGS,
        DocumentsContract.Root.COLUMN_ICON, DocumentsContract.Root.COLUMN_MIME_TYPES};
    private static final String[] DOCUMENT_COLUMNS = {DocumentsContract.Document.COLUMN_DOCUMENT_ID,
        DocumentsContract.Document.COLUMN_DISPLAY_NAME, DocumentsContract.Document.COLUMN_MIME_TYPE,
        DocumentsContract.Document.COLUMN_SIZE, DocumentsContract.Document.COLUMN_FLAGS};
    @Override public boolean onCreate() { return true; }

    static synchronized Bundle prepare(Context context, String session, String token, int port) throws IOException {
        if (state != null) throw new IllegalStateException("Never replace a prior provider session or tombstone");
        State owned = new State(session, token, port); state = owned; // Own before provisioning HTTP/socket side effects.
        Transfer provision = owned.transfer("root", RemoteIoContract.root(session), null);
        Throwable primary = null;
        try {
            try (RemoteIoHttpTransport.Exchange exchange = provision.open()) {
                String body = new String(exchange.metadata(), StandardCharsets.US_ASCII);
                String[] fields = body.endsWith("\n") ? body.substring(0, body.length() - 1).split("\t", -1) : new String[0];
                if (fields.length != 9 || !"R".equals(fields[0]) || !session.equals(fields[1]) ||
                    !RemoteIoContract.root(session).equals(fields[2]) || !RemoteIoContract.home(session).equals(fields[3]) ||
                    !"NativeCmpKit remote IO".equals(fields[4]) || !RemoteIoContract.folder(session).equals(fields[5]) ||
                    !RemoteIoContract.folderName(session).equals(fields[6]) || !RemoteIoContract.payload(session).equals(fields[7]) ||
                    !RemoteIoContract.held(session).equals(fields[8]))
                    throw new IOException("HTTP root descriptor/ancestry refused");
                synchronized (owned) { owned.rootDescriptor = fields; }
            }
        } catch (IOException | RuntimeException failure) { primary = failure; provision.failed(failure); throw failure; }
        finally { provision.finish(primary); }
        context.getContentResolver().notifyChange(DocumentsContract.buildRootsUri(RemoteIoContract.AUTHORITY), null);
        return owned.snapshot();
    }
    static State owned(String session) {
        State owned = state;
        if (owned == null || !owned.session.equals(RemoteIoContract.hexNonce(session)))
            throw new IllegalArgumentException("Missing or foreign provider session");
        return owned;
    }
    static Bundle snapshot(String session) { return owned(session).snapshot(); }
    static Bundle stop(Context context, String session) throws IOException, InterruptedException {
        Bundle receipt = owned(session).stop();
        context.getContentResolver().notifyChange(DocumentsContract.buildRootsUri(RemoteIoContract.AUTHORITY), null);
        return receipt;
    }
    private State live(String id) throws FileNotFoundException {
        State owned = state;
        if (owned == null || owned.rootDescriptor == null || owned.stopped || owned.stopping || !RemoteIoContract.known(owned.session, id))
            throw new FileNotFoundException("Owned remote document is not live");
        return owned;
    }
    @Override public Cursor queryRoots(String[] projection) {
        MatrixCursor cursor = new MatrixCursor(projection == null ? ROOT_COLUMNS : projection);
        State owned = state;
        if (owned != null && owned.rootDescriptor != null && !owned.stopping && !owned.stopped) {
            // Official DocumentsProvider recommends fast roots/ancestry. No LOCAL_ONLY or write/create claim.
            String[] root = owned.rootDescriptor;
            MatrixCursor.RowBuilder row = cursor.newRow();
            put(row, cursor, DocumentsContract.Root.COLUMN_ROOT_ID, root[2]);
            put(row, cursor, DocumentsContract.Root.COLUMN_DOCUMENT_ID, root[3]);
            put(row, cursor, DocumentsContract.Root.COLUMN_TITLE, root[4]);
            put(row, cursor, DocumentsContract.Root.COLUMN_FLAGS, DocumentsContract.Root.FLAG_SUPPORTS_IS_CHILD);
            put(row, cursor, DocumentsContract.Root.COLUMN_ICON, android.R.drawable.ic_menu_upload);
            put(row, cursor, DocumentsContract.Root.COLUMN_MIME_TYPES, "application/octet-stream");
        }
        cursor.setNotificationUri(getContext().getContentResolver(), DocumentsContract.buildRootsUri(RemoteIoContract.AUTHORITY));
        return cursor;
    }
    @Override public boolean isChildDocument(String parent, String child) throws FileNotFoundException {
        State owned = live(parent); String[] root = owned.rootDescriptor;
        // Only HTTP-provisioned immutable ID ancestry; never speculative remote listing/network in this method.
        if (root[3].equals(parent)) return root[5].equals(child) || root[7].equals(child) || root[8].equals(child);
        return root[5].equals(parent) && (root[7].equals(child) || root[8].equals(child));
    }
    @Override public Cursor queryDocument(String id, String[] projection) throws FileNotFoundException {
        State owned = live(id); String body = owned.metadata("metadata", id);
        MatrixCursor cursor = new MatrixCursor(projection == null ? DOCUMENT_COLUMNS : projection);
        add(cursor, parse(owned, body, id)); return cursor;
    }
    @Override public Cursor queryChildDocuments(String id, String[] projection, String sortOrder) throws FileNotFoundException {
        State owned = live(id); String body = owned.metadata("children", id);
        String[] lines = body.split("\n", -1);
        String[] expected = RemoteIoContract.home(owned.session).equals(id) ? new String[] {RemoteIoContract.folder(owned.session)} :
            RemoteIoContract.folder(owned.session).equals(id) ? new String[] {RemoteIoContract.payload(owned.session), RemoteIoContract.held(owned.session)} : new String[0];
        if (expected.length == 0 || lines.length != expected.length + 2 || !"L".equals(lines[0]) || !lines[lines.length - 1].isEmpty())
            throw new FileNotFoundException("Exact live HTTP child listing refused");
        MatrixCursor cursor = new MatrixCursor(projection == null ? DOCUMENT_COLUMNS : projection);
        for (int i = 0; i < expected.length; i++) add(cursor, parse(owned, lines[i + 1] + "\n", expected[i]));
        cursor.setNotificationUri(getContext().getContentResolver(), DocumentsContract.buildDocumentUri(RemoteIoContract.AUTHORITY, id));
        return cursor;
    }
    private static String[] parse(State owned, String body, String expectedId) throws FileNotFoundException {
        String[] fields = body.endsWith("\n") ? body.substring(0, body.length() - 1).split("\t", -1) : new String[0];
        if (fields.length != 5 || !"D".equals(fields[0]) || !expectedId.equals(fields[1]) || fields[2].isEmpty() || fields[2].length() > 128)
            throw new FileNotFoundException("Exact HTTP metadata schema refused");
        boolean directory = RemoteIoContract.home(owned.session).equals(expectedId) || RemoteIoContract.folder(owned.session).equals(expectedId);
        String expectedName = RemoteIoContract.home(owned.session).equals(expectedId) ? "NativeCmpKit remote IO" :
            RemoteIoContract.folder(owned.session).equals(expectedId) ? RemoteIoContract.folderName(owned.session) :
            RemoteIoContract.payload(owned.session).equals(expectedId) ? "payload.bin" : "held.bin";
        String size = directory ? "-" : Integer.toString(RemoteIoContract.payload(owned.session).equals(expectedId) ?
            RemoteIoContract.PAYLOAD_BYTES : RemoteIoContract.HELD_BYTES);
        if (!expectedName.equals(fields[2]) || !(directory ? DocumentsContract.Document.MIME_TYPE_DIR : "application/octet-stream").equals(fields[3]) ||
            !size.equals(fields[4])) throw new FileNotFoundException("Live HTTP metadata content refused");
        return fields;
    }
    private static void add(MatrixCursor cursor, String[] metadata) {
        MatrixCursor.RowBuilder row = cursor.newRow();
        put(row, cursor, DocumentsContract.Document.COLUMN_DOCUMENT_ID, metadata[1]);
        put(row, cursor, DocumentsContract.Document.COLUMN_DISPLAY_NAME, metadata[2]);
        put(row, cursor, DocumentsContract.Document.COLUMN_MIME_TYPE, metadata[3]);
        put(row, cursor, DocumentsContract.Document.COLUMN_SIZE, "-".equals(metadata[4]) ? null : Long.valueOf(metadata[4]));
        put(row, cursor, DocumentsContract.Document.COLUMN_FLAGS, 0);
    }
    private static void put(MatrixCursor.RowBuilder row, MatrixCursor cursor, String key, Object value) {
        if (cursor.getColumnIndex(key) >= 0) row.add(key, value);
    }

    @Override public ParcelFileDescriptor openDocument(String id, String mode, CancellationSignal signal) throws FileNotFoundException {
        State owned = live(id);
        if (!"r".equals(mode) || !(RemoteIoContract.payload(owned.session).equals(id) || RemoteIoContract.held(owned.session).equals(id)))
            throw new FileNotFoundException("Only exact remote readonly files may open");
        Transfer transfer = owned.transfer("content", id, signal); Throwable primary = null;
        try {
            if (signal != null) signal.throwIfCanceled();
            RemoteIoHttpTransport.Exchange exchange = transfer.open();
            synchronized (owned) { transfer.phase = "PENDING_FIRST_BODY"; }
            // Genuine blocking network open BEFORE pipe/PFD allocation or return. Backend holds this byte for held.bin.
            int first = exchange.input.read();
            if (signal != null) signal.throwIfCanceled();
            if (first < 0 || RemoteIoContract.held(owned.session).equals(id))
                throw new IOException("Remote body ended early or held body unexpectedly progressed");
            transfer.pipe = ParcelFileDescriptor.createReliablePipe();
            StructStat stat = Os.fstat(transfer.pipe[0].getFileDescriptor());
            long fdInfo = pipeInode(transfer.pipe[0]);
            if (!OsConstants.S_ISFIFO(stat.st_mode) || stat.st_ino == 0 || stat.st_ino != fdInfo)
                throw new IOException("Actual provider FIFO stat/fdinfo identity refused");
            synchronized (owned) {
                transfer.pipeDevice = stat.st_dev; transfer.pipeInode = stat.st_ino; transfer.pipeMode = stat.st_mode;
                transfer.fdInfoInode = fdInfo; transfer.phase = "PIPE_CREATED";
                transfer.worker = new Thread(() -> pump(transfer, first), "nativecmpkit-remote-io-pipe");
            }
            transfer.detachSignal(); // Cancellation fixture explicitly certifies pre-transfer only.
            synchronized (owned) {
                transfer.worker.start();
                transfer.descriptorReturned = true; owned.descriptorReturns++;
            }
            return transfer.pipe[0]; // The framework transfers this actual FIFO; caller independently calibrates it.
        } catch (OperationCanceledException failure) {
            primary = failure; transfer.failed(failure); throw failure;
        } catch (Exception failure) {
            if (signal != null && signal.isCanceled()) {
                try { signal.throwIfCanceled(); }
                catch (OperationCanceledException cancelled) {
                    cancelled.addSuppressed(failure); primary = cancelled; transfer.failed(cancelled); throw cancelled;
                }
            }
            primary = failure; transfer.failed(failure);
            FileNotFoundException error = new FileNotFoundException("Owned remote HTTP open failed"); error.initCause(failure); throw error;
        } finally { if (!transfer.descriptorReturned) transfer.finish(primary); }
    }
    private static void pump(Transfer transfer, int first) {
        Throwable primary = null;
        OutputStream output = null;
        try {
            output = new ParcelFileDescriptor.AutoCloseOutputStream(transfer.pipe[1]);
            RemoteIoHttpTransport.Exchange exchange = transfer.exchange;
            MessageDigest digest = RemoteIoContract.digest(); digest.update((byte) first); output.write(first);
            int total = 1; byte[] chunk = new byte[1024];
            synchronized (transfer.owner) { transfer.bytesPiped = 1; transfer.phase = "PIPE_PUMP"; }
            while (total < exchange.length) {
                int count = exchange.input.read(chunk, 0, Math.min(chunk.length, exchange.length - total));
                if (count <= 0) throw new IOException("Owned remote body made no progress");
                output.write(chunk, 0, count); digest.update(chunk, 0, count); total += count;
                synchronized (transfer.owner) { transfer.bytesPiped = total; }
            }
            if (exchange.input.read() != -1) throw new IOException("Owned remote body exceeded Content-Length");
            String observed = RemoteIoContract.hex(digest.digest());
            if (!exchange.sha256.equals(observed)) throw new IOException("Owned remote body digest disagrees");
            synchronized (transfer.owner) { transfer.producerSocketEof = true; transfer.bodyHash = observed; }
        } catch (IOException | RuntimeException failure) {
            primary = failure; transfer.failed(failure);
            // Deliver the reliable-pipe status while the owned writer is still live, before ordinary close.
            try { transfer.pipe[1].closeWithError("Owned remote producer failed"); }
            catch (IOException | RuntimeException | Error cleanup) {
                if (failure != cleanup) failure.addSuppressed(cleanup);
                synchronized (transfer.owner) { transfer.owner.cleanupErrors++; }
            }
        } catch (Error failure) { primary = failure; throw failure; }
        finally {
            // Stream construction may fail; either way, writer cleanup cannot skip owned transfer cleanup.
            try { if (output != null) output.close(); else transfer.pipe[1].close(); }
            catch (IOException | RuntimeException | Error cleanup) {
                if (primary == null) { primary = cleanup; transfer.failed(cleanup); }
                else if (primary != cleanup) primary.addSuppressed(cleanup);
                synchronized (transfer.owner) { transfer.owner.cleanupErrors++; }
                if (primary == cleanup && cleanup instanceof Error) throw (Error) cleanup;
            } finally { transfer.finish(primary); }
        }
    }
    /** The only filesystem read in the provider is its own calibrated kernel FIFO fdinfo. */
    private static long pipeInode(ParcelFileDescriptor pipe) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (FileInputStream input = new FileInputStream("/proc/self/fdinfo/" + pipe.getFd())) {
            byte[] chunk = new byte[1024]; int count;
            while ((count = input.read(chunk)) != -1) {
                if (count <= 0 || bytes.size() + count > 8192) throw new IOException("Owned fdinfo bound exceeded");
                bytes.write(chunk, 0, count);
            }
        }
        Long inode = null;
        for (String line : bytes.toString(StandardCharsets.US_ASCII.name()).split("\n", -1)) if (line.startsWith("ino:")) {
            String number = line.substring(4).trim();
            if (inode != null || !number.matches("[0-9]{1,19}")) throw new IOException("Owned fdinfo inode refused");
            try { inode = Long.valueOf(number); } catch (NumberFormatException failure) { throw new IOException("Owned fdinfo inode overflow", failure); }
        }
        if (inode == null || inode == 0) throw new IOException("Owned fdinfo inode missing");
        return inode;
    }

    static final class State {
        final String session, token; final int port;
        volatile String[] rootDescriptor;
        volatile boolean stopping, stopped;
        final Map<String, Transfer> active = new LinkedHashMap<>(); final ArrayList<Transfer> journal = new ArrayList<>();
        int errors, cleanupErrors, descriptorReturns;
        State(String session, String token, int port) {
            this.session = RemoteIoContract.hexNonce(session); this.token = RemoteIoContract.hexNonce(token); this.port = RemoteIoContract.port(port);
        }
        Transfer transfer(String route, String id, CancellationSignal signal) {
            Transfer transfer;
            synchronized (this) {
                if (stopping || stopped || active.size() >= RemoteIoContract.MAX_CONNECTIONS || journal.size() >= RemoteIoContract.MAX_JOURNAL)
                    throw new IllegalStateException("Provider transfer registry bound or stopped state refused");
                transfer = new Transfer(this, route, id, signal); active.put(transfer.requestId, transfer); journal.add(transfer);
            }
            transfer.attachSignal(); return transfer;
        }
        String metadata(String route, String id) throws FileNotFoundException {
            Transfer transfer = transfer(route, id, null); Throwable primary = null;
            try (RemoteIoHttpTransport.Exchange exchange = transfer.open()) {
                return new String(exchange.metadata(), StandardCharsets.US_ASCII);
            } catch (IOException | RuntimeException failure) {
                primary = failure; transfer.failed(failure); FileNotFoundException error = new FileNotFoundException("Live remote metadata unavailable");
                error.initCause(failure); throw error;
            } finally { transfer.finish(primary); }
        }
        synchronized Bundle snapshot() {
            Bundle result = new Bundle(); result.putString("session", session); result.putInt("port", port);
            result.putBoolean("rootProvisionedOverHttp", rootDescriptor != null); result.putBoolean("stopped", stopped);
            result.putInt("activeTransfers", active.size()); result.putInt("errors", errors); result.putInt("cleanupErrors", cleanupErrors);
            result.putInt("descriptorReturns", descriptorReturns);
            int sockets = 0, workers = 0;
            ArrayList<Bundle> records = new ArrayList<>();
            for (Transfer transfer : journal) {
                if (transfer.socket != null && !transfer.socket.isClosed()) sockets++;
                if (transfer.worker != null && transfer.worker.isAlive()) workers++;
                records.add(transfer.snapshot());
            }
            result.putInt("activeSockets", sockets); result.putInt("activeWorkers", workers); result.putParcelableArrayList("journal", records);
            return result;
        }
        Bundle stop() throws IOException, InterruptedException {
            ArrayList<Transfer> owned; synchronized (this) { stopping = true; owned = new ArrayList<>(journal); }
            Throwable primary = null;
            for (Transfer transfer : owned) try { transfer.forceCloseIfActive(); }
            catch (IOException failure) { if (primary == null) primary = failure; else primary.addSuppressed(failure); }
            for (Transfer transfer : owned) try {
                if (!transfer.done.await(RemoteIoContract.JOIN_MS, TimeUnit.MILLISECONDS)) throw new IOException("Owned provider invocation did not terminate");
                if (transfer.worker != null) {
                    transfer.worker.join(RemoteIoContract.JOIN_MS);
                    if (transfer.worker.isAlive()) throw new IOException("Owned producer did not terminate");
                }
            } catch (IOException | InterruptedException failure) { if (primary == null) primary = failure; else primary.addSuppressed(failure); }
            synchronized (this) {
                stopped = active.isEmpty() && snapshot().getInt("activeSockets") == 0 && snapshot().getInt("activeWorkers") == 0;
                if (!stopped || primary != null) cleanupErrors++;
                rootDescriptor = null; // Immutable descriptor only, never content data. Tombstones/counters stay.
            }
            if (primary instanceof InterruptedException) { Thread.currentThread().interrupt(); throw (InterruptedException) primary; }
            if (primary != null) throw new IOException("Owned provider cleanup failed", primary);
            if (!stopped) throw new IOException("Owned provider registry is not quiescent");
            return snapshot();
        }
    }

    private static final class Transfer implements RemoteIoHttpTransport.SocketOwner {
        final State owner; final String requestId = UUID.randomUUID().toString().replace("-", ""), route, documentId;
        final CancellationSignal signal; final CountDownLatch done = new CountDownLatch(1);
        Socket socket; RemoteIoHttpTransport.Exchange exchange; ParcelFileDescriptor[] pipe; Thread worker;
        String phase = "REGISTERED", expectedHash, bodyHash, error;
        int localPort, peerPort, expectedBytes, bytesPiped, cancellationAcknowledgments, pipeMode;
        long pipeDevice, pipeInode, fdInfoInode;
        boolean socketConnected, headersRead, socketClosed, descriptorReturned, producerSocketEof,
            cancelled, signalDetached, listenerClosedSocket, operationCanceledObserved, terminal, forcedCleanup;
        Transfer(State owner, String route, String documentId, CancellationSignal signal) {
            this.owner = owner; this.route = route; this.documentId = documentId; this.signal = signal;
        }
        void attachSignal() {
            if (signal != null) signal.setOnCancelListener(() -> {
                Socket ownSocket;
                synchronized (owner) {
                    if (cancelled) { owner.errors++; return; }
                    cancelled = true; cancellationAcknowledgments++; ownSocket = socket;
                }
                if (ownSocket != null) try {
                    ownSocket.close(); synchronized (owner) { listenerClosedSocket = ownSocket.isClosed(); socketClosed = ownSocket.isClosed(); }
                } catch (IOException failure) { synchronized (owner) { owner.cleanupErrors++; } }
            });
        }
        void detachSignal() { if (signal != null) signal.setOnCancelListener(null); synchronized (owner) { signalDetached = true; } }
        RemoteIoHttpTransport.Exchange open() throws IOException {
            RemoteIoHttpTransport.Exchange opened = RemoteIoHttpTransport.open(owner.session, owner.token, owner.port, route, documentId, requestId, this);
            synchronized (owner) { exchange = opened; } return opened;
        }
        @Override public void register(Socket socket) throws IOException {
            synchronized (owner) { if (this.socket != null || terminal) throw new IOException("Duplicate owned socket registration"); this.socket = socket; }
            if (signal != null) signal.throwIfCanceled();
        }
        @Override public void connected(Socket socket) throws IOException {
            synchronized (owner) {
                if (this.socket != socket || !socket.isConnected()) throw new IOException("Unregistered native socket refused");
                localPort = socket.getLocalPort(); peerPort = socket.getPort(); socketConnected = true; phase = "SOCKET_CONNECTED";
            }
            if (signal != null) signal.throwIfCanceled();
        }
        @Override public void headers(int length, String sha256) {
            synchronized (owner) { expectedBytes = length; expectedHash = sha256; headersRead = true; phase = "HEADERS_READ"; }
        }
        @Override public void closed(Socket socket, IOException failure) {
            synchronized (owner) { if (this.socket != socket) owner.errors++; socketClosed = socket.isClosed(); if (failure != null) owner.cleanupErrors++; }
        }
        void failed(Throwable failure) {
            synchronized (owner) {
                error = RemoteIoContract.error(failure);
                if (failure instanceof OperationCanceledException) { operationCanceledObserved = true; phase = "CANCELLED_BEFORE_TRANSFER"; }
                else owner.errors++;
            }
        }
        void finish(Throwable primary) {
            Throwable cleanup = null;
            try { detachSignal(); } catch (RuntimeException failure) { cleanup = failure; }
            try {
                if (exchange != null) exchange.close(); else if (socket != null) { socket.close(); closed(socket, null); }
            } catch (IOException failure) { if (cleanup == null) cleanup = failure; else cleanup.addSuppressed(failure); }
            if (!descriptorReturned && pipe != null) for (ParcelFileDescriptor descriptor : pipe) try { descriptor.close(); }
            catch (IOException failure) { if (cleanup == null) cleanup = failure; else cleanup.addSuppressed(failure); }
            synchronized (owner) {
                if (cleanup != null) owner.cleanupErrors++;
                terminal = true; owner.active.remove(requestId); done.countDown();
            }
            if (cleanup != null && primary != null) primary.addSuppressed(cleanup);
            if (cleanup != null && primary == null) throw new IllegalStateException("Owned transfer cleanup failed", cleanup);
        }
        void forceCloseIfActive() throws IOException {
            synchronized (owner) { if (terminal) return; forcedCleanup = true; owner.errors++; }
            IOException failure = null;
            if (socket != null) try { socket.close(); } catch (IOException error) { failure = error; }
            if (pipe != null) for (ParcelFileDescriptor descriptor : pipe) try { descriptor.close(); }
            catch (IOException error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
            if (failure != null) throw failure;
        }
        Bundle snapshot() {
            Bundle result = new Bundle(); result.putString("requestId", requestId); result.putString("route", route);
            result.putString("documentId", documentId); result.putString("phase", phase); result.putInt("localPort", localPort);
            result.putInt("peerPort", peerPort); result.putBoolean("socketConnected", socketConnected); result.putBoolean("headersRead", headersRead);
            result.putBoolean("socketClosed", socket != null && socket.isClosed() && socketClosed);
            result.putInt("expectedBytes", expectedBytes); result.putInt("bytesPiped", bytesPiped);
            result.putString("expectedHash", expectedHash); result.putString("bodyHash", bodyHash); result.putString("error", error);
            result.putBoolean("descriptorReturned", descriptorReturned); result.putBoolean("producerSocketEof", producerSocketEof);
            result.putBoolean("pipeAllocated", pipe != null);
            result.putInt("cancellationAcknowledgments", cancellationAcknowledgments); result.putBoolean("signalDetached", signalDetached);
            result.putBoolean("listenerClosedSocket", listenerClosedSocket); result.putBoolean("operationCanceledObserved", operationCanceledObserved);
            result.putBoolean("terminal", terminal); result.putBoolean("openingTerminal", done.getCount() == 0);
            result.putBoolean("workerTerminal", worker == null || !worker.isAlive()); result.putBoolean("forcedCleanup", forcedCleanup);
            result.putBoolean("readNativeOpen", pipe != null && pipe[0].getFileDescriptor().valid());
            result.putBoolean("writeNativeOpen", pipe != null && pipe[1].getFileDescriptor().valid());
            result.putLong("pipeDevice", pipeDevice); result.putLong("pipeInode", pipeInode); result.putInt("pipeMode", pipeMode);
            result.putLong("fdInfoInode", fdInfoInode); return result;
        }
    }
}
