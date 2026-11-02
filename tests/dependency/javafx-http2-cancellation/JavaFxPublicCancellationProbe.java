/*
 * Copyright (c) 2026 NativeCmpKit contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Dependency-level public JavaFX network cancellation regression.
 * Not NativeCmpKit public Stop, Windows, packaged-consumer or release acceptance.
 * There is no private loader property override or reflective cancellation.
 */
import java.io.ByteArrayOutputStream;
import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.zip.GZIPOutputStream;
import javafx.application.Platform;
import javafx.concurrent.Worker;
import javafx.scene.Scene;
import javafx.scene.layout.HBox;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;
import javafx.stage.Stage;

public final class JavaFxPublicCancellationProbe {
    static final List<String> ALLOWED = List.of("zero-header", "plain-body", "gzip-body", "concurrent");
    static final AtomicReference<WebView> FIRST = new AtomicReference<>(), SECOND = new AtomicReference<>();
    static final AtomicReference<Stage> STAGE = new AtomicReference<>();
    static final AtomicInteger CANCELLATIONS = new AtomicInteger(), OTHER_CANCELLATIONS = new AtomicInteger();
    static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    static <T> T fx(Callable<T> action) throws Exception {
        FutureTask<T> task = new FutureTask<>(action);
        Platform.runLater(task);
        return task.get(5, TimeUnit.SECONDS);
    }
    static void waitFor(Callable<Boolean> predicate, String label) throws Exception {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (System.nanoTime() < deadline) {
            boolean accepted = predicate.call();
            require(System.nanoTime() < deadline, "Late observation: " + label);
            if (accepted) return;
            Thread.sleep(10);
        }
        throw new AssertionError("Readiness deadline: " + label);
    }
    static WebEngine engine() { return FIRST.get().getEngine(); }
    static WebEngine otherEngine() { return SECOND.get().getEngine(); }
    static byte[] document(String title) {
        return ("<!doctype html><html><head><title>" + title
                + "</title></head><body>" + "x".repeat(24_000)).getBytes(StandardCharsets.US_ASCII);
    }
    static void readHeader(Socket socket, String path, int port) throws IOException {
        socket.setSoTimeout(5_000);
        InputStream in = socket.getInputStream();
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        int tail = 0;
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        for (;;) {
            require(System.nanoTime() < deadline, "Request header elapsed beyond bound");
            int value = in.read();
            require(value >= 0 && bytes.size() < 8_192, "Unexpected request header termination/bound");
            bytes.write(value);
            tail = (tail << 8) | value;
            if (tail == 0x0d0a0d0a) break;
        }
        String text = bytes.toString(StandardCharsets.US_ASCII);
        require(text.startsWith("GET " + path + " HTTP/1.1\r\n"), "Wrong owned request path or protocol");
        int hosts = 0;
        for (String line : text.split("\r\n")) {
            if (line.regionMatches(true, 0, "Host:", 0, 5)) {
                hosts++;
                require(line.substring(5).trim().equals("127.0.0.1:" + port), "Wrong owned Host");
            }
        }
        require(hosts == 1, "Host must occur exactly once");
    }
    static final class CountingOutput extends FilterOutputStream {
        final AtomicInteger bytes;
        CountingOutput(OutputStream output, AtomicInteger bytes) { super(output); this.bytes = bytes; }
        @Override public void write(int value) throws IOException {
            out.write(value); bytes.incrementAndGet();
        }
        @Override public void write(byte[] value, int offset, int length) throws IOException {
            out.write(value, offset, length); bytes.addAndGet(length);
        }
    }
    static final class OwnedGzip extends GZIPOutputStream {
        OwnedGzip(OutputStream output) throws IOException { super(output, 8_192, true); }
        void releaseEncoderWithoutWritingTrailer() { def.end(); }
    }
    static final class HeldPeer implements AutoCloseable {
        final String kind, title, path;
        final ServerSocket listener;
        final Thread thread;
        final AtomicReference<Socket> socket = new AtomicReference<>();
        final AtomicReference<Throwable> error = new AtomicReference<>();
        final AtomicBoolean cleanup = new AtomicBoolean();
        final AtomicInteger requests = new AtomicInteger(), responseBytes = new AtomicInteger(), eofs = new AtomicInteger();
        final CountDownLatch admitted = new CountDownLatch(1), ended = new CountDownLatch(1);
        HeldPeer(String kind) throws IOException {
            this.kind = kind;
            String nonce = UUID.randomUUID().toString().replace("-", "");
            title = "NativeCmpKitDependency" + nonce;
            path = "/held-" + nonce;
            listener = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"));
            listener.setSoTimeout(5_000);
            thread = new Thread(this::serve, "nativecmpkit-owned-held-" + nonce);
            thread.setDaemon(true);
            thread.start();
        }
        String url() { return "http://127.0.0.1:" + listener.getLocalPort() + path; }
        void serve() {
            OwnedGzip gzip = null;
            try (Socket peer = listener.accept()) {
                socket.set(peer);
                readHeader(peer, path, listener.getLocalPort());
                requests.incrementAndGet();
                if (!kind.equals("zero-header")) {
                    CountingOutput out = new CountingOutput(peer.getOutputStream(), responseBytes);
                    String headers = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\n"
                            + "Cache-Control: no-store\r\nConnection: close\r\nContent-Length: 1048576\r\n"
                            + (kind.equals("gzip-body") ? "Content-Encoding: gzip\r\n" : "") + "\r\n";
                    out.write(headers.getBytes(StandardCharsets.US_ASCII));
                    if (kind.equals("gzip-body")) {
                        gzip = new OwnedGzip(out);
                        gzip.write(document(title));
                        gzip.flush(); // SYNC_FLUSH only; no trailer, response completion or socket close.
                    } else {
                        out.write(document(title));
                        out.flush();
                    }
                } // zero-header NEVER obtains an OutputStream.
                admitted.countDown();
                peer.setSoTimeout(100);
                InputStream in = peer.getInputStream();
                while (!cleanup.get()) {
                    try {
                        int value = in.read();
                        require(value == -1, "Unexpected post-header request bytes");
                        eofs.incrementAndGet();
                        break; // Only the client's real EOF authorizes this success observation.
                    } catch (SocketTimeoutException expected) { /* finite passive hold */ }
                }
            } catch (Throwable failure) {
                if (!cleanup.get()) error.set(failure);
            } finally {
                if (gzip != null) gzip.releaseEncoderWithoutWritingTrailer();
                ended.countDown();
            }
        }
        void awaitAdmission() throws Exception {
            require(admitted.await(5, TimeUnit.SECONDS), "Owned request was not admitted");
            require(error.get() == null && requests.get() == 1 && eofs.get() == 0 && !cleanup.get(),
                    "Owned peer admission changed");
        }
        void awaitRealEof() throws Exception {
            boolean finished = ended.await(10, TimeUnit.SECONDS);
            require(finished && eofs.get() == 1 && error.get() == null && !cleanup.get(),
                    "Public cancellation did not establish real peer EOF before cleanup; finished=" + finished
                    + ";eofs=" + eofs.get() + ";responseBytes=" + responseBytes.get()
                    + ";peerError=" + (error.get() == null ? "none" : error.get().getClass().getName()));
        }
        @Override public void close() throws Exception {
            cleanup.set(true);
            listener.close();
            Socket peer = socket.get();
            if (peer != null) peer.close();
            thread.join(5_000);
            require(!thread.isAlive(), "Owned held peer thread remains");
        }
    }
    static final class CompletePeer implements AutoCloseable {
        final String title, path;
        final ServerSocket listener;
        final Thread thread;
        final AtomicReference<Socket> socket = new AtomicReference<>();
        final AtomicReference<Throwable> error = new AtomicReference<>();
        final AtomicBoolean cleanup = new AtomicBoolean();
        final AtomicInteger requests = new AtomicInteger(), responseBytes = new AtomicInteger();
        final CountDownLatch admitted = new CountDownLatch(1), release = new CountDownLatch(1), ended = new CountDownLatch(1);
        CompletePeer(boolean gated) throws IOException {
            String nonce = UUID.randomUUID().toString().replace("-", "");
            title = "NativeCmpKitRecovery" + nonce; path = "/recovery-" + nonce;
            listener = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1")); listener.setSoTimeout(5_000);
            if (!gated) release.countDown();
            thread = new Thread(this::serve, "nativecmpkit-owned-complete-" + nonce);
            thread.setDaemon(true); thread.start();
        }
        String url() { return "http://127.0.0.1:" + listener.getLocalPort() + path; }
        void serve() {
            try (Socket peer = listener.accept()) {
                socket.set(peer); readHeader(peer, path, listener.getLocalPort());
                requests.incrementAndGet(); admitted.countDown();
                require(release.await(10, TimeUnit.SECONDS) && !cleanup.get(), "Owned response release was not authorized");
                byte[] body = ("<html><head><title>" + title + "</title></head><body>ok</body></html>")
                        .getBytes(StandardCharsets.US_ASCII);
                CountingOutput out = new CountingOutput(peer.getOutputStream(), responseBytes);
                out.write(("HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nCache-Control: no-store\r\n"
                        + "Connection: close\r\nContent-Length: " + body.length + "\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
                out.write(body); out.flush();
            } catch (Throwable failure) {
                if (!cleanup.get()) error.set(failure);
            } finally { ended.countDown(); }
        }
        void awaitAdmission() throws Exception {
            require(admitted.await(5, TimeUnit.SECONDS) && requests.get() == 1 && error.get() == null && !cleanup.get(),
                    "Other request not admitted");
        }
        void awaitCompletion() throws Exception {
            require(ended.await(5, TimeUnit.SECONDS) && error.get() == null && responseBytes.get() > 0 && !cleanup.get(),
                    "Owned complete response did not finish");
        }
        @Override public void close() throws Exception {
            cleanup.set(true); release.countDown(); listener.close();
            Socket peer = socket.get(); if (peer != null) peer.close();
            thread.join(5_000); require(!thread.isAlive(), "Owned complete peer thread remains");
        }
    }
    static int recoverOnSameEngine() throws Exception {
        try (CompletePeer peer = new CompletePeer(false)) {
            fx(() -> { engine().load(peer.url()); return null; });
            peer.awaitAdmission();
            waitFor(() -> fx(() -> engine().getLoadWorker().getState() == Worker.State.SUCCEEDED
                    && peer.title.equals(engine().getTitle()) && engine().getDocument() != null), "same-engine recovery");
            peer.awaitCompletion();
            return peer.requests.get();
        }
    }
    static void runCase(String kind) throws Exception {
        long started = System.nanoTime();
        int before = CANCELLATIONS.get();
        try (HeldPeer peer = new HeldPeer(kind)) {
            fx(() -> { engine().load(peer.url()); return null; });
            peer.awaitAdmission();
            waitFor(() -> fx(() -> engine().getLoadWorker().getState() == Worker.State.RUNNING
                    && engine().getLoadWorker().isRunning()), "actual RUNNING worker");
            boolean actualParsedTitle = false;
            if (!kind.equals("zero-header")) {
                waitFor(() -> fx(() -> peer.title.equals(engine().getTitle())
                        && engine().getLoadWorker().getState() == Worker.State.RUNNING), "actual native parsed body title");
                actualParsedTitle = true;
            }
            int sentBeforeCancel = peer.responseBytes.get();
            long cancelAt = System.nanoTime();
            require(fx(() -> engine().getLoadWorker().cancel()), "Actual public worker refused cancellation");
            peer.awaitRealEof();
            long eofNanos = System.nanoTime() - cancelAt;
            require(fx(() -> engine().getLoadWorker().getState() == Worker.State.CANCELLED
                    && !engine().getLoadWorker().isRunning()), "Actual public worker not CANCELLED");
            require(CANCELLATIONS.get() - before == 1 && peer.responseBytes.get() == sentBeforeCancel,
                    "Cancellation count or held response bytes changed");
            if (kind.equals("zero-header")) require(sentBeforeCancel == 0, "Zero-header response wrote bytes");
            int recovered = recoverOnSameEngine();
            require(CANCELLATIONS.get() - before == 1, "Recovery replayed cancellation");
            System.out.println("{\"case\":\"" + kind + "\",\"passed\":true,\"peerEofs\":1,\"responseBytes\":"
                    + sentBeforeCancel + ",\"parsedNativeTitle\":" + actualParsedTitle + ",\"cancellations\":1,"
                    + "\"cleanupBeganBeforeEof\":false,\"sameEngineRecoveryRequests\":" + recovered
                    + ",\"cancelToPeerNanos\":" + eofNanos + ",\"caseElapsedNanos\":" + (System.nanoTime() - started) + "}");
        }
    }
    static void concurrentCase() throws Exception {
        long started = System.nanoTime();
        int before = CANCELLATIONS.get(), otherBefore = OTHER_CANCELLATIONS.get();
        try (HeldPeer held = new HeldPeer("zero-header"); CompletePeer other = new CompletePeer(true)) {
            fx(() -> { engine().load(held.url()); otherEngine().load(other.url()); return null; });
            held.awaitAdmission(); other.awaitAdmission();
            waitFor(() -> fx(() -> engine().getLoadWorker().getState() == Worker.State.RUNNING
                    && otherEngine().getLoadWorker().getState() == Worker.State.RUNNING), "both actual pending workers");
            require(fx(() -> engine().getLoadWorker().cancel()), "First actual concurrent cancel refused");
            held.awaitRealEof();
            require(held.responseBytes.get() == 0 && CANCELLATIONS.get() - before == 1, "First concurrent witness changed");
            for (int i = 0; i < 3; i++) require(!fx(() -> engine().getLoadWorker().cancel()), "Idle cancel unexpectedly restarted work");
            require(CANCELLATIONS.get() - before == 1, "Repeated Stop generated duplicate transition");
            require(fx(() -> otherEngine().getLoadWorker().getState() == Worker.State.RUNNING
                    && otherEngine().getLoadWorker().isRunning()) && other.responseBytes.get() == 0
                    && OTHER_CANCELLATIONS.get() == otherBefore, "Cancel affected independent pending request");
            other.release.countDown(); // Explicit fixture response, never an EOF substitute for cancelled held peer.
            waitFor(() -> fx(() -> otherEngine().getLoadWorker().getState() == Worker.State.SUCCEEDED
                    && other.title.equals(otherEngine().getTitle()) && otherEngine().getDocument() != null), "independent request success");
            other.awaitCompletion();
            require(OTHER_CANCELLATIONS.get() == otherBefore, "Independent request cancelled");
            int recovered = recoverOnSameEngine();
            System.out.println("{\"case\":\"concurrent\",\"passed\":true,\"peerEofs\":1,\"responseBytes\":0,"
                    + "\"cancellations\":1,\"repeatedIdleCancels\":3,\"independentRequestPassed\":true,"
                    + "\"otherCancellations\":0,\"cleanupBeganBeforeEof\":false,\"sameEngineRecoveryRequests\":"
                    + recovered + ",\"caseElapsedNanos\":" + (System.nanoTime() - started) + "}");
        }
    }
    public static void main(String[] args) throws Exception {
        require(args.length == 1, "One explicit finite scenario selection is required");
        List<String> selected = Arrays.asList(args[0].split(",", -1));
        require(!selected.isEmpty() && selected.size() <= 4
                && new LinkedHashSet<>(selected).size() == selected.size() && ALLOWED.containsAll(selected),
                "Unknown or duplicate dependency scenario");
        require(System.getProperty("com.sun.webkit.useHTTP2Loader") == null, "Private route override refused");
        CountDownLatch startup = new CountDownLatch(1);
        Platform.startup(startup::countDown);
        require(startup.await(5, TimeUnit.SECONDS), "JavaFX startup deadline");
        Platform.setImplicitExit(false);
        try {
            fx(() -> {
                WebView first = new WebView(), second = new WebView();
                FIRST.set(first); SECOND.set(second);
                first.getEngine().getLoadWorker().stateProperty().addListener((p, old, state) -> {
                    if (state == Worker.State.CANCELLED) CANCELLATIONS.incrementAndGet();
                });
                second.getEngine().getLoadWorker().stateProperty().addListener((p, old, state) -> {
                    if (state == Worker.State.CANCELLED) OTHER_CANCELLATIONS.incrementAndGet();
                });
                Stage stage = new Stage();
                STAGE.set(stage); stage.setScene(new Scene(new HBox(first, second), 900, 400)); stage.show();
                return null;
            });
            for (String kind : selected) {
                if (kind.equals("concurrent")) concurrentCase(); else runCase(kind);
            }
            System.out.println("{\"summary\":true,\"scenarioCount\":" + selected.size()
                    + ",\"passed\":" + selected.size() + ",\"libraryTests\":0,\"privateRouteOverride\":false}");
        } finally {
            try {
                fx(() -> {
                    if (FIRST.get() != null) { engine().getLoadWorker().cancel(); engine().load("about:blank"); }
                    if (SECOND.get() != null) { otherEngine().getLoadWorker().cancel(); otherEngine().load("about:blank"); }
                    if (STAGE.get() != null) STAGE.get().close();
                    return null;
                });
            } finally {
                Platform.exit();
            }
        }
    }
}

