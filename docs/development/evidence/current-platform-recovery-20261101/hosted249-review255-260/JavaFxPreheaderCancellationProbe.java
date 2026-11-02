/* NativeCmpKit dependency diagnostic. No production/private-loader fallback or library acceptance. */
import java.io.ByteArrayOutputStream;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import javafx.application.Platform;
import javafx.scene.web.WebEngine;

public final class JavaFxPreheaderCancellationProbe {
    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    private static <T> T fx(java.util.concurrent.Callable<T> action) throws Exception {
        FutureTask<T> task = new FutureTask<>(action);
        Platform.runLater(task);
        return task.get(5, TimeUnit.SECONDS);
    }
    public static void main(String[] args) throws Exception {
        require(System.getProperty("com.sun.webkit.useHTTP2Loader") == null,
            "Probe does not change the private route property");
        CountDownLatch started = new CountDownLatch(1);
        Platform.startup(started::countDown);
        require(started.await(5, TimeUnit.SECONDS), "FX startup timeout");
        Platform.setImplicitExit(false);
        String nonce = java.util.UUID.randomUUID().toString().replace("-", "");
        String path = "/nativecmpkit-dependency-preheader-" + nonce;
        AtomicBoolean cleanup = new AtomicBoolean();
        AtomicInteger peerEofs = new AtomicInteger();
        AtomicInteger responseBytes = new AtomicInteger();
        AtomicReference<Throwable> peerFailure = new AtomicReference<>();
        AtomicReference<Socket> owned = new AtomicReference<>();
        CountDownLatch header = new CountDownLatch(1), ended = new CountDownLatch(1);
        Object page = null;
        AtomicReference<WebEngine> retainedEngine = new AtomicReference<>();
        CompletableFuture<?> response = null;
        Thread server = null;
        try (ServerSocket listener = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"))) {
            listener.setSoTimeout(5_000);
            int port = listener.getLocalPort();
            server = new Thread(() -> {
                try (Socket socket = listener.accept()) {
                    owned.set(socket); socket.setSoTimeout(5_000);
                    var in = socket.getInputStream();
                    var bytes = new ByteArrayOutputStream(); int tail = 0;
                    long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
                    for (;;) {
                        require(System.nanoTime() < deadline, "Request header timeout");
                        int value = in.read(); require(value >= 0 && bytes.size() < 8_192, "Malformed header");
                        bytes.write(value); tail = (tail << 8) | value;
                        if (tail == 0x0d0a0d0a) break;
                    }
                    String text = bytes.toString(StandardCharsets.US_ASCII);
                    require(text.startsWith("GET " + path + " HTTP/1.1\r\n"), "Unexpected request");
                    String[] lines = text.split("\r\n"); int hosts = 0;
                    for (String line: lines) if (line.regionMatches(true, 0, "Host:", 0, 5)) {
                        hosts++; require(line.substring(5).trim().equals("127.0.0.1:" + port), "Unexpected Host");
                    }
                    require(hosts == 1, "Host not singular");
                    // No OutputStream access: no response header or response body can authorize EOF.
                    header.countDown(); socket.setSoTimeout(100);
                    while (!cleanup.get()) {
                        try {
                            int value = in.read(); require(value == -1, "Unexpected post-header bytes");
                            peerEofs.incrementAndGet(); break;
                        } catch (SocketTimeoutException expected) { /* passive pre-header hold */ }
                    }
                } catch (Throwable error) { if (!cleanup.get()) peerFailure.set(error); }
                finally { ended.countDown(); }
            }, "nativecmpkit-owned-dependency-preheader");
            server.setDaemon(true); server.start();
            String url = "http://127.0.0.1:" + port + path;
            Class<?> accessor = Class.forName("com.sun.javafx.webkit.Accessor");
            Class<?> pageClass = Class.forName("com.sun.webkit.WebPage");
            Class<?> poolClass = Class.forName("com.sun.webkit.network.ByteBufferPool");
            Class<?> formArray = Class.forName("[Lcom.sun.webkit.network.FormDataElement;");
            Class<?> loaderClass = Class.forName("com.sun.webkit.network.HTTP2Loader");
            page = fx(() -> accessor.getMethod("getPageFor", WebEngine.class).invoke(null, retainedEngine.updateAndGet(old -> new WebEngine())));
            require(pageClass.isInstance(page), "No genuine WebPage");
            Method poolFactory = poolClass.getDeclaredMethod("newInstance", int.class); poolFactory.setAccessible(true);
            Object pool = poolFactory.invoke(null, 40_960);
            Method create = loaderClass.getDeclaredMethod("create", pageClass, poolClass, boolean.class,
                String.class, String.class, String.class, formArray, long.class); create.setAccessible(true);
            Object actualPage = page;
            Object loader = fx(() -> create.invoke(null, actualPage, pool, true, url, "GET",
                "User-Agent: NativeCmpKit-Dependency-Probe\n", null, 0L));
            require(loaderClass.isInstance(loader), "No actual held HTTP2Loader");
            require(header.await(5, TimeUnit.SECONDS), "No actual pre-header peer admission");
            Field canceled = loaderClass.getDeclaredField("canceled"); canceled.setAccessible(true);
            Field responseField = loaderClass.getDeclaredField("response"); responseField.setAccessible(true);
            response = (CompletableFuture<?>) responseField.get(loader);
            require(!response.isDone() && !canceled.getBoolean(loader) && peerEofs.get() == 0,
                "Initial owned request is not pending");
            Method cancel = loaderClass.getDeclaredMethod("fwkCancel"); cancel.setAccessible(true);
            fx(() -> { cancel.invoke(loader); return null; });
            // Only the failed future-cancellation tail is selected. Do not replay the first
            // probe's accepted 1500ms flag-only hold/observation. Keep the actual Engine strongly owned.
            long flagOnlyNanos = 0;
            // Controlled internal repair probe, NOT the library's public Stop and NOT an acceptance fallback.
            long cancelStarted = System.nanoTime();
            boolean futureCancel = response.cancel(true);
            require(futureCancel, "Actual response future refused cancellation");
            require(ended.await(5, TimeUnit.SECONDS), "Future cancellation did not end the peer");
            long futureNanos = System.nanoTime() - cancelStarted;
            require(response.isDone() && responseBytes.get() == 0 && !cleanup.get(),
                "Future-tail observation changed");
            Throwable peerError = peerFailure.get();
            String terminal = peerEofs.get() == 1 ? "eof" : peerError != null ? "read-exception" : "unknown";
            System.out.println("PEER_TERMINAL " + terminal + ";class=" +
                (peerError == null ? "none" : peerError.getClass().getName()) + ";message=" +
                (peerError == null ? "none" : peerError.getMessage()));
            System.out.println("{\"scope\":\"direct-internal-JavaFX-instance-not-library-acceptance\","
                + "\"javaVersion\":\"" + System.getProperty("java.version") + "\","
                + "\"loaderClass\":\"" + loader.getClass().getName() + "\","
                + "\"futureClass\":\"" + response.getClass().getName() + "\","
                + "\"flagOnlyPendingReplay\":false,\"flagOnlyPeerEofs\":0,\"flagOnlyObservationNanos\":" + flagOnlyNanos + ","
                + "\"responseFutureDone\":" + response.isDone() + ",\"responseFutureIsCancelled\":" + response.isCancelled() + ",\"cancelReturnedTrue\":true,\"futureCancelPeerEofs\":" + peerEofs.get() + ",\"futureCancelNanos\":" + futureNanos + ","
                + "\"responseBytes\":0,\"serverCleanupBeganBeforeEof\":false,\"privateRoutePropertyChanged\":false}");
        } finally {
            cleanup.set(true);
            Socket socket = owned.get(); if (socket != null) socket.close();
            if (response != null && !response.isDone()) response.cancel(true);
            if (server != null) { server.join(5_000); require(!server.isAlive(), "Owned peer thread remains"); }
            Object actualPage = page;
            try { if (actualPage != null) fx(() -> { actualPage.getClass().getMethod("dispose").invoke(actualPage); return null; }); }
            finally { Platform.exit(); }
        }
    }
}
