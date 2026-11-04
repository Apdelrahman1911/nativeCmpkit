// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments;

import android.os.Bundle;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Main-process owner of random in-memory bytes. All provider data travels on real sockets.
 * One nonce session; no host listener, account, disk seeding, hidden daemon or cached body.
 */
final class RemoteIoHttpBackend {
    final String session;
    private final String token;
    private final Map<Socket, Connection> active = new LinkedHashMap<>();
    private final ArrayList<Connection> journal = new ArrayList<>();
    private final Set<String> requestIds = new java.util.HashSet<>();
    private ServerSocket listener;
    private Thread acceptor;
    private byte[] payload, held;
    private String payloadHash, heldHash;
    private int port, errors, cleanupErrors;
    private boolean started, stopping, stopped, dataCleared;
    RemoteIoHttpBackend(String session, String token) {
        this.session = RemoteIoContract.hexNonce(session); this.token = RemoteIoContract.hexNonce(token);
    }
    synchronized void start() throws IOException {
        if (started || stopping || listener != null) throw new IllegalStateException("Owned backend must be new");
        started = true;
        payload = new byte[RemoteIoContract.PAYLOAD_BYTES]; held = new byte[RemoteIoContract.HELD_BYTES];
        SecureRandom random = new SecureRandom(); random.nextBytes(payload); random.nextBytes(held);
        payloadHash = RemoteIoContract.sha256(payload); heldHash = RemoteIoContract.sha256(held);
        listener = new ServerSocket(); // This pre-registered session owns the listener before bind.
        listener.setReuseAddress(false);
        listener.bind(new java.net.InetSocketAddress(RemoteIoHttpTransport.loopback(), 0), RemoteIoContract.ACCEPT_BACKLOG);
        port = RemoteIoContract.port(listener.getLocalPort()); listener.setSoTimeout(1000);
        if (!RemoteIoHttpTransport.loopback().equals(listener.getInetAddress()))
            throw new IOException("Backend listener is not literal loopback");
        acceptor = new Thread(this::accept, "nativecmpkit-remote-io-accept"); acceptor.start();
    }
    private void accept() {
        try {
            for (;;) {
                synchronized (this) { if (stopping) return; }
                Socket socket;
                try { socket = listener.accept(); }
                catch (SocketTimeoutException expected) { continue; }
                Connection connection = new Connection(socket);
                synchronized (this) {
                    // Ownership is recorded before endpoint validation or worker start.
                    if (stopping || active.size() >= RemoteIoContract.MAX_CONNECTIONS || journal.size() >= RemoteIoContract.MAX_JOURNAL) {
                        errors++; socket.close(); continue;
                    }
                    active.put(socket, connection); journal.add(connection);
                    connection.worker = new Thread(() -> serve(connection), "nativecmpkit-remote-io-http");
                }
                try { connection.worker.start(); }
                catch (RuntimeException failure) {
                    synchronized (this) { errors++; connection.error = RemoteIoContract.error(failure); }
                    try { socket.close(); } catch (IOException closeFailure) { synchronized (this) { cleanupErrors++; } }
                    synchronized (this) { connection.socketClosed = socket.isClosed(); connection.terminal = true; active.remove(socket); }
                }
            }
        } catch (IOException | RuntimeException failure) {
            synchronized (this) { if (!stopping) errors++; }
        }
    }
    private void serve(Connection connection) {
        try {
            Socket socket = connection.socket;
            RemoteIoHttpTransport.requireLoopback(socket, port, false);
            socket.setSoTimeout(RemoteIoContract.READ_MS); socket.setTcpNoDelay(true);
            synchronized (this) {
                connection.localPort = socket.getLocalPort(); connection.peerPort = socket.getPort();
                connection.nativeLoopback = true;
            }
            InputStream input = socket.getInputStream();
            RemoteIoHttpTransport.Headers request = new RemoteIoHttpTransport.Headers(input, socket);
            request.keys("host", "connection", "x-nativecmpkit-session", "x-nativecmpkit-token", "x-nativecmpkit-request");
            String[] target = request.first.split(" ", -1);
            if (target.length != 3 || !"GET".equals(target[0]) || !"HTTP/1.1".equals(target[2]) ||
                !"127.0.0.1:".concat(Integer.toString(port)).equals(request.values.get("host")) ||
                !"close".equals(request.values.get("connection")) ||
                !session.equals(request.values.get("x-nativecmpkit-session")) ||
                !token.equals(request.values.get("x-nativecmpkit-token")))
                throw new IOException("Native HTTP request/session origin refused");
            String[] path = target[1].split("/", -1);
            if (path.length != 4 || !path[0].isEmpty() || !session.equals(path[2]) ||
                !Set.of("root", "metadata", "children", "content").contains(path[1]) ||
                !("root".equals(path[1]) ? RemoteIoContract.root(session).equals(path[3]) : RemoteIoContract.known(session, path[3])))
                throw new IOException("Native HTTP owned route refused");
            String requestId = RemoteIoContract.hexNonce(request.values.get("x-nativecmpkit-request"));
            synchronized (this) {
                if (!requestIds.add(requestId)) throw new IOException("Duplicate native request refused");
                connection.requestId = requestId; connection.route = path[1]; connection.documentId = path[3];
            }
            boolean content = "content".equals(path[1]);
            byte[] body = body(path[1], path[3]); String hash = RemoteIoContract.sha256(body);
            String reply = "HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Type: " +
                (content ? "application/octet-stream" : "application/vnd.nativecmpkit.io-metadata") +
                "\r\nContent-Length: " + body.length + "\r\nX-NativeCmpKit-Session: " + session +
                "\r\nX-NativeCmpKit-Request: " + requestId + "\r\nX-NativeCmpKit-Transfer: " + requestId +
                "\r\nX-NativeCmpKit-SHA256: " + hash + "\r\n\r\n";
            byte[] headers = RemoteIoContract.ascii(reply);
            if (headers.length > RemoteIoContract.MAX_HEADER_BYTES) throw new IOException("Native response header bound exceeded");
            OutputStream output = socket.getOutputStream(); output.write(headers); output.flush();
            synchronized (this) { connection.headersSent = true; connection.expectedBytes = body.length; }
            if (content && RemoteIoContract.held(session).equals(path[3])) {
                // The real headers are delivered, but NO body byte is delivered before cancellation.
                socket.setSoTimeout(RemoteIoContract.HELD_READ_MS);
                synchronized (this) {
                    connection.heldWaiting = true;
                    connection.watchdog = new Thread(() -> watchdog(connection), "nativecmpkit-remote-io-watchdog");
                    connection.watchdog.start();
                }
                if (input.read() != -1) throw new IOException("Held request sent unexpected client body");
                synchronized (this) { connection.peerEof = true; connection.heldWaiting = false; }
            } else {
                MessageDigest sent = RemoteIoContract.digest();
                for (int position = 0; position < body.length;) {
                    int count = Math.min(1024, body.length - position);
                    output.write(body, position, count); sent.update(body, position, count); position += count;
                    synchronized (this) { connection.bytesWritten = position; }
                }
                output.flush(); socket.shutdownOutput();
                synchronized (this) { connection.bodyHash = RemoteIoContract.hex(sent.digest()); }
                if (input.read() != -1) throw new IOException("Unexpected native client trailing bytes");
                synchronized (this) { connection.peerEof = true; }
            }
        } catch (IOException | RuntimeException failure) {
            synchronized (this) { connection.error = RemoteIoContract.error(failure); errors++; }
        } finally {
            try { connection.socket.close(); }
            catch (IOException failure) { synchronized (this) { cleanupErrors++; } }
            synchronized (this) {
                connection.socketClosed = connection.socket.isClosed(); connection.terminal = true;
                active.remove(connection.socket); connection.done.countDown();
            }
        }
    }
    private void watchdog(Connection connection) {
        try {
            if (!connection.done.await(RemoteIoContract.HELD_WATCHDOG_MS, TimeUnit.MILLISECONDS)) {
                synchronized (this) { connection.watchdogForced = true; errors++; }
                try { connection.socket.close(); }
                catch (IOException failure) { synchronized (this) { cleanupErrors++; } }
            }
        } catch (InterruptedException failure) {
            Thread.currentThread().interrupt(); synchronized (this) { errors++; }
        } finally { synchronized (this) { connection.watchdogTerminal = true; } }
    }
    private synchronized byte[] body(String route, String id) throws IOException {
        if (stopping || payload == null || held == null) throw new IOException("Owned backend data is unavailable");
        if ("content".equals(route)) {
            if (RemoteIoContract.payload(session).equals(id)) return payload;
            if (RemoteIoContract.held(session).equals(id)) return held;
            throw new IOException("Directory content open refused");
        }
        String value;
        if ("root".equals(route)) {
            value = "R\t" + session + "\t" + RemoteIoContract.root(session) + "\t" + RemoteIoContract.home(session) +
                "\tNativeCmpKit remote IO\t" + RemoteIoContract.folder(session) + "\t" + RemoteIoContract.folderName(session) +
                "\t" + RemoteIoContract.payload(session) + "\t" + RemoteIoContract.held(session) + "\n";
        } else if ("metadata".equals(route)) value = metadata(id);
        else if ("children".equals(route) && RemoteIoContract.home(session).equals(id)) value = "L\n" + metadata(RemoteIoContract.folder(session));
        else if ("children".equals(route) && RemoteIoContract.folder(session).equals(id))
            value = "L\n" + metadata(RemoteIoContract.payload(session)) + metadata(RemoteIoContract.held(session));
        else throw new IOException("Owned directory listing refused");
        byte[] bytes = RemoteIoContract.ascii(value);
        if (bytes.length > RemoteIoContract.MAX_METADATA_BYTES) throw new IOException("Owned metadata bound exceeded");
        return bytes;
    }
    private String metadata(String id) throws IOException {
        String name, mime, size;
        if (RemoteIoContract.home(session).equals(id)) { name = "NativeCmpKit remote IO"; mime = "vnd.android.document/directory"; size = "-"; }
        else if (RemoteIoContract.folder(session).equals(id)) { name = RemoteIoContract.folderName(session); mime = "vnd.android.document/directory"; size = "-"; }
        else if (RemoteIoContract.payload(session).equals(id)) { name = "payload.bin"; mime = "application/octet-stream"; size = Integer.toString(payload.length); }
        else if (RemoteIoContract.held(session).equals(id)) { name = "held.bin"; mime = "application/octet-stream"; size = Integer.toString(held.length); }
        else throw new IOException("Foreign metadata refused");
        return "D\t" + id + "\t" + name + "\t" + mime + "\t" + size + "\n";
    }

    synchronized Bundle snapshot() {
        Bundle result = new Bundle(); result.putString("session", session); result.putInt("port", port);
        result.putBoolean("listenerLoopback", listener != null && listener.getInetAddress() != null &&
            Arrays.equals(listener.getInetAddress().getAddress(), new byte[] {127, 0, 0, 1}));
        result.putBoolean("listenerClosed", listener == null || listener.isClosed());
        result.putBoolean("acceptorTerminal", acceptor == null || !acceptor.isAlive());
        result.putInt("activeConnections", active.size()); result.putInt("errors", errors); result.putInt("cleanupErrors", cleanupErrors);
        result.putBoolean("stopped", stopped); result.putBoolean("dataCleared", dataCleared);
        result.putInt("payloadBytes", RemoteIoContract.PAYLOAD_BYTES); result.putInt("heldBytes", RemoteIoContract.HELD_BYTES);
        result.putString("payloadHash", payloadHash); result.putString("heldHash", heldHash);
        ArrayList<Bundle> records = new ArrayList<>(); for (Connection connection : journal) records.add(connection.snapshot());
        result.putParcelableArrayList("journal", records); return result;
    }
    Bundle stop() throws IOException, InterruptedException {
        ArrayList<Connection> owned; ServerSocket ownListener; Thread ownAcceptor;
        synchronized (this) { stopping = true; owned = new ArrayList<>(journal); ownListener = listener; ownAcceptor = acceptor; }
        Throwable primary = null;
        if (ownListener != null) try { ownListener.close(); } catch (IOException failure) { primary = failure; }
        for (Connection connection : owned) try { connection.socket.close(); }
        catch (IOException failure) { if (primary == null) primary = failure; else primary.addSuppressed(failure); }
        ArrayList<Thread> threads = new ArrayList<>(); if (ownAcceptor != null) threads.add(ownAcceptor);
        for (Connection connection : owned) { if (connection.worker != null) threads.add(connection.worker); if (connection.watchdog != null) threads.add(connection.watchdog); }
        for (Thread thread : threads) try {
            thread.join(RemoteIoContract.JOIN_MS);
            if (thread.isAlive()) throw new IOException("Owned backend worker did not terminate");
        } catch (IOException | InterruptedException failure) {
            if (primary == null) primary = failure; else primary.addSuppressed(failure);
        }
        synchronized (this) {
            // Every join/close is attempted before nonce data wipe; counters/tombstones are retained.
            if (payload != null) Arrays.fill(payload, (byte) 0);
            if (held != null) Arrays.fill(held, (byte) 0);
            payload = null; held = null; dataCleared = true;
            stopped = active.isEmpty() && (listener == null || listener.isClosed()) && (acceptor == null || !acceptor.isAlive());
            if (!stopped || primary != null) cleanupErrors++;
        }
        if (primary instanceof InterruptedException) { Thread.currentThread().interrupt(); throw (InterruptedException) primary; }
        if (primary != null) throw new IOException("Owned backend cleanup failed", primary);
        if (!stopped) throw new IOException("Owned backend registry is not quiescent");
        return snapshot();
    }
    private static final class Connection {
        final Socket socket; final CountDownLatch done = new CountDownLatch(1);
        Thread worker, watchdog;
        String requestId, route, documentId, bodyHash, error;
        int localPort, peerPort, expectedBytes, bytesWritten;
        boolean nativeLoopback, headersSent, heldWaiting, peerEof, socketClosed, terminal, watchdogForced, watchdogTerminal;
        Connection(Socket socket) { this.socket = socket; }
        Bundle snapshot() {
            Bundle result = new Bundle(); result.putString("requestId", requestId); result.putString("route", route);
            result.putString("documentId", documentId); result.putInt("localPort", localPort); result.putInt("peerPort", peerPort);
            result.putBoolean("nativeLoopback", nativeLoopback); result.putBoolean("headersSent", headersSent);
            result.putInt("expectedBytes", expectedBytes); result.putInt("bytesWritten", bytesWritten);
            result.putString("bodyHash", bodyHash); result.putString("error", error); result.putBoolean("heldWaiting", heldWaiting);
            result.putBoolean("peerEof", peerEof); result.putBoolean("socketClosed", socketClosed); result.putBoolean("terminal", terminal);
            result.putBoolean("workerTerminal", worker == null || !worker.isAlive()); result.putBoolean("watchdogForced", watchdogForced);
            result.putBoolean("watchdogTerminal", watchdog == null || watchdogTerminal && !watchdog.isAlive()); return result;
        }
    }
}
