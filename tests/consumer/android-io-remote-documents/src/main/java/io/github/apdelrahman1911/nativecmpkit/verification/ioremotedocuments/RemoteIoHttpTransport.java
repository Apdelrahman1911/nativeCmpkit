// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** Actual finite TCP, no DNS/proxy/redirect/HTTP-library or disk/body-cache fallback.
 * Raw Socket is deliberately test-only cleartext: NetworkSecurityConfig is NOT its boundary.
 */
final class RemoteIoHttpTransport {
    private RemoteIoHttpTransport() {}
    interface SocketOwner {
        void register(Socket socket) throws IOException;
        void connected(Socket socket) throws IOException;
        void headers(int length, String sha256);
        void closed(Socket socket, IOException failure);
    }
    static InetAddress loopback() throws IOException {
        return InetAddress.getByAddress(new byte[] {127, 0, 0, 1});
    }
    static void requireLoopback(Socket socket, int serverPort, boolean client) throws IOException {
        InetAddress expected = loopback();
        if (!expected.equals(socket.getLocalAddress()) || !expected.equals(socket.getInetAddress()) ||
            socket.getLocalPort() <= 0 || socket.getPort() <= 0 ||
            (client ? socket.getPort() : socket.getLocalPort()) != RemoteIoContract.port(serverPort))
            throw new IOException("Actual owned native loopback endpoints disagree");
    }

    /** Strict CRLF/ASCII, bounded bytes AND lines, rejecting duplicates and partial headers. */
    static final class Headers {
        final String first;
        final Map<String, String> values = new LinkedHashMap<>();
        private final Socket socket;
        private final long deadline;
        private int bytes, lines;
        Headers(InputStream input, Socket socket) throws IOException {
            this.socket = socket; deadline = System.nanoTime() + RemoteIoContract.READ_MS * 1_000_000L;
            int originalTimeout = socket.getSoTimeout(); Throwable primary = null;
            try {
                first = line(input);
                for (;;) {
                    String line = line(input);
                    if (line.isEmpty()) break;
                    int colon = line.indexOf(": ");
                    if (colon <= 0 || colon != line.indexOf(':') || line.charAt(0) == ' ' ||
                        !line.substring(0, colon).matches("[A-Za-z][A-Za-z0-9-]*"))
                        throw new IOException("Malformed bounded native HTTP header");
                    String name = line.substring(0, colon).toLowerCase(java.util.Locale.ROOT);
                    String value = line.substring(colon + 2);
                    if (value.isEmpty() || !value.equals(value.trim()) || values.put(name, value) != null)
                        throw new IOException("Duplicate or empty bounded native HTTP header");
                }
            } catch (IOException | RuntimeException failure) { primary = failure; throw failure; }
            finally {
                // Never leave a last-byte 1ms header timeout on the following ordinary/held body read.
                if (!socket.isClosed()) try { socket.setSoTimeout(originalTimeout); }
                catch (IOException cleanup) { if (primary != null) primary.addSuppressed(cleanup); else throw cleanup; }
            }
        }
        private int read(InputStream input) throws IOException {
            long remaining = deadline - System.nanoTime();
            if (remaining <= 0) throw new SocketTimeoutException("Owned HTTP aggregate header budget exhausted");
            socket.setSoTimeout((int) Math.max(1, Math.min(RemoteIoContract.READ_MS, (remaining + 999999L) / 1_000_000L)));
            int value = input.read();
            if (System.nanoTime() > deadline) throw new SocketTimeoutException("Late owned HTTP header byte refused");
            return value;
        }
        private String line(InputStream input) throws IOException {
            if (++lines > RemoteIoContract.MAX_HEADER_LINES) throw new IOException("Native HTTP line bound exceeded");
            ByteArrayOutputStream result = new ByteArrayOutputStream();
            for (;;) {
                int ch = read(input);
                if (++bytes > RemoteIoContract.MAX_HEADER_BYTES || ch < 0)
                    throw new IOException("Partial or oversized native HTTP headers");
                if (ch == '\r') {
                    int lf = read(input);
                    if (++bytes > RemoteIoContract.MAX_HEADER_BYTES || lf != '\n')
                        throw new IOException("Native HTTP requires exact CRLF");
                    return result.toString(StandardCharsets.US_ASCII.name());
                }
                if (ch < 32 || ch > 126) throw new IOException("Native HTTP header is not ASCII");
                result.write(ch);
            }
        }
        void keys(String... expected) throws IOException {
            if (!values.keySet().equals(Set.of(expected))) throw new IOException("Extra or missing native HTTP headers");
        }
    }

    static final class Exchange implements AutoCloseable {
        final Socket socket;
        final InputStream input;
        final int length;
        final String sha256, requestId;
        private final SocketOwner owner;
        private boolean closed;
        Exchange(Socket socket, InputStream input, int length, String sha256, String requestId, SocketOwner owner) {
            this.socket = socket; this.input = input; this.length = length;
            this.sha256 = sha256; this.requestId = requestId; this.owner = owner;
        }
        byte[] metadata() throws IOException {
            if (length <= 0 || length > RemoteIoContract.MAX_METADATA_BYTES)
                throw new IOException("Native metadata body bound exceeded");
            byte[] bytes = new byte[length]; int position = 0;
            while (position < bytes.length) {
                int count = input.read(bytes, position, bytes.length - position);
                if (count <= 0) throw new IOException("Partial native metadata body");
                position += count;
            }
            if (input.read() != -1 || !sha256.equals(RemoteIoContract.sha256(bytes)))
                throw new IOException("Native metadata EOF or hash disagrees");
            for (byte value : bytes) if (value != '\n' && value != '\t' && (value < 32 || value > 126))
                throw new IOException("Native metadata body is not bounded ASCII");
            return bytes;
        }
        @Override public synchronized void close() throws IOException {
            if (closed) return;
            closed = true; IOException failure = null;
            try { socket.close(); } catch (IOException error) { failure = error; throw error; }
            finally { owner.closed(socket, failure); }
        }
    }

    static Exchange open(String session, String token, int port, String route, String documentId,
                         String requestId, SocketOwner owner) throws IOException {
        RemoteIoContract.hexNonce(session); RemoteIoContract.hexNonce(token); RemoteIoContract.hexNonce(requestId);
        RemoteIoContract.port(port);
        if (!Set.of("root", "metadata", "children", "content").contains(route) ||
            !("root".equals(route) ? RemoteIoContract.root(session).equals(documentId) : RemoteIoContract.known(session, documentId)))
            throw new IOException("Foreign session or HTTP route refused");
        Socket socket = new Socket(); // The transfer already exists and immediately owns this unconnected socket.
        boolean registered = false;
        try {
            owner.register(socket); registered = true;
            socket.setSoTimeout("content".equals(route) && RemoteIoContract.held(session).equals(documentId) ?
                RemoteIoContract.HELD_READ_MS : RemoteIoContract.READ_MS);
            socket.connect(new InetSocketAddress(loopback(), port), RemoteIoContract.CONNECT_MS);
            requireLoopback(socket, port, true); socket.setTcpNoDelay(true); owner.connected(socket);
            String request = "GET /" + route + "/" + session + "/" + documentId + " HTTP/1.1\r\n" +
                "Host: 127.0.0.1:" + port + "\r\nConnection: close\r\n" +
                "X-NativeCmpKit-Session: " + session + "\r\nX-NativeCmpKit-Token: " + token + "\r\n" +
                "X-NativeCmpKit-Request: " + requestId + "\r\n\r\n";
            byte[] headers = RemoteIoContract.ascii(request);
            if (headers.length > RemoteIoContract.MAX_HEADER_BYTES) throw new IOException("Native request bound exceeded");
            socket.getOutputStream().write(headers); socket.getOutputStream().flush();
            InputStream input = socket.getInputStream(); Headers reply = new Headers(input, socket);
            reply.keys("connection", "content-type", "content-length", "x-nativecmpkit-session",
                "x-nativecmpkit-request", "x-nativecmpkit-transfer", "x-nativecmpkit-sha256");
            String size = reply.values.get("content-length"), hash = reply.values.get("x-nativecmpkit-sha256");
            if (!"HTTP/1.1 200 OK".equals(reply.first) || !"close".equals(reply.values.get("connection")) ||
                !session.equals(reply.values.get("x-nativecmpkit-session")) ||
                !requestId.equals(reply.values.get("x-nativecmpkit-request")) ||
                !requestId.equals(reply.values.get("x-nativecmpkit-transfer")) ||
                !size.matches("[1-9][0-9]{0,5}") || !hash.matches("[a-f0-9]{64}") ||
                !("content".equals(route) ? "application/octet-stream" : "application/vnd.nativecmpkit.io-metadata")
                    .equals(reply.values.get("content-type")))
                throw new IOException("Native response status/identity/schema refused");
            int length = Integer.parseInt(size);
            int maximum = "content".equals(route) ? RemoteIoContract.HELD_BYTES : RemoteIoContract.MAX_METADATA_BYTES;
            if (length > maximum || ("content".equals(route) && length !=
                (RemoteIoContract.held(session).equals(documentId) ? RemoteIoContract.HELD_BYTES : RemoteIoContract.PAYLOAD_BYTES)))
                throw new IOException("Native response content-length refused");
            owner.headers(length, hash);
            return new Exchange(socket, input, length, hash, requestId, owner);
        } catch (IOException | RuntimeException failure) {
            try { socket.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
            if (registered) owner.closed(socket, socket.isClosed() ? null : new IOException("Native socket close unverified"));
            throw failure;
        }
    }
}
