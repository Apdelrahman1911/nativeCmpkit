# Source-only review

The old c08b owning source remains byte-exact and is not included in any modification patch. Production/common contracts and the accepted JavaFx test source remain held unchanged. The separate new native class has exactly two `@Test` methods; no ignored annotations, manually collected navigation events, direct engine load/reload/cancel, synthetic `WebViewError` or common request metadata writes occur.

The Stop case seeds a real native document, acquires an owned connected pre-header held request, observes RUNNING and cleared old metadata, invokes the public Stop command, and requires CANCELLED plus actual client EOF/pending-zero/zero-responses while the server is not closing. It then loads a fresh recovery document on the same native view and owner. The cancellation observer is removed before native/window disposal, so teardown cannot create the cancellation witness.

The redirect/Reload case clicks an actual authored native DOM link; the owned server emits a literal 302 Location pointing to a distinct held target. Requested URL remains redirect origin until public Reload, which requests only the actual final target. Two target releases yield different authored native/document/library titles; the redirect origin is acquired only once. No history or repeated-stop criterion is inferred.

The raw fixture binds only 127.0.0.1 and exact nonce paths/Host/GET/protocols. Header bytes 8192/deadline 5 seconds; connections 64; worker pool 4/queue 8; hold deadline 15 seconds. No response/release/server-close can witness Stop. Socket close failures latch even during shutdown, and socket ownership is removed only after successful close/readback. Teardown closes admission/listener, joins its acceptor, closes owned sockets, drains workers, requires empty pending/ownership and reads sticky health. The existing primary-error-preserving all-stages native window cleanup protocol is retained.

This is lexical/source inspection and synthetic controller policy only. It is not Kotlin compilation, JavaFX/native HTTP/EOF/event observation, actual source-map/Git correlation, native fixture lifetime acceptance, packaged verification or #64 closure.
