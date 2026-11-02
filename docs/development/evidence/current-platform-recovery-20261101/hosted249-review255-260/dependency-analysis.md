# JavaFX21.0.13 cancellation investigation

## Confirmed source behavior, not inferred Windows-instance attribution

The Windows failure observer binds the actual `javafx-web`21.0.13+2 archive and
the base entries for `WebEngine`, `LoadWorker`, `WebPage`, `NetworkContext`,
`HTTP2Loader`, `URLLoader` and `HTTP2BodySubscriber`. Its resource snapshots
are not an executing-loader-instance trace. Exact disassembly of the retained
21.0.13 classes shows:

1. `NetworkContext` normally enables `HTTP2Loader` on Java>=12; its factory
   accepts both `http://` and `https://`, including HTTP/1.1 fallback. The class
   name does not establish the request's negotiated HTTP version.
2. `HTTP2Loader.fwkCancel()` only assigns the volatile `canceled=true` flag.
   It does **not** cancel the stored response future or its HttpClient exchange.
3. The stored response derives from `HTTP_CLIENT.sendAsync(...).thenAccept(...)
   .exceptionally(...)`. Before response headers, no body subscriber exists to
   call its conditional cancellation path. Suppressing native result delivery
   is not equivalent to releasing the pending network operation.
4. The normal subscriber only notices cancellation at `onSubscribe`/`onNext`.
   A response or compressed stream stalled without new data also requires owning
   cancellation/lifecycle analysis; the preheader diagnostic does not verify it.

The once-acquired official sources agree at:

| Source | Exact source location | Observed Git blob |
| --- | --- | --- |
| [jfx21u HTTP2Loader](https://github.com/openjdk/jfx21u/blob/master/modules/javafx.web/src/main/java/com/sun/webkit/network/HTTP2Loader.java) | `fwkCancel`,419–425; response ownership,360–412; normal subscriber,314–353; compressed subscriber,257–312 | `4e1bec56985fec98e4ba6b0c3e00abab025c8f71` |
| [current jfx HTTP2Loader](https://github.com/openjdk/jfx/blob/master/modules/javafx.web/src/main/java/com/sun/webkit/network/HTTP2Loader.java) | `fwkCancel`; same flag-only behavior at acquisition | `bcce0610f7ab2183344c99748a66cda7c1531190` |

These branch links are navigation, not immutable source identities; the recorded
blob IDs and source SHA256 values in [the receipts](javafx-diagnostics258-260.json)
identify the acquisition. Branch contents are not proved byte-identical to the
21.0.13 binary's source tag; the binary disassembly independently establishes
flag-only behavior. The saved issue search returned no matches, **not proof that
no upstream issue exists**. Do not reacquire these sources or the original logs.

## Direct internal diagnostics: preserved failures and narrower recovery

All three owned probes use exact21.0.13 Linux JavaFX JARs/JDK17.0.20, a genuine
WebPage and a private loopback socket accepting only the nonce GET/Host. The
server never obtains an output stream, so it cannot send response headers/body.
The JVM/Xvfb/peer thread/socket are explicitly owned and bounded. These programs
use reflection **only for dependency diagnosis**, not in production or as a
public-API/native acceptance fallback.

- **258: exit1**. A1,500ms flag-only pending/zero-EOF prefix is reached, then the
  future-cancel assertion fails. It incorrectly requires the dependent future's
  `isCancelled()`. WebPage is retained, but an explicit strong WebEngine owner
  is absent; that lifetime limitation remains. Do not replay its accepted prefix.
- **259: exit1**. Only the failed tail is selected, adding strong WebEngine
  ownership and separate peer-read-error observation. The same incorrect
  `isCancelled()` requirement fails. No accepted1,500ms prefix replay.
- **260: exit0**, compile0/0.885743s, run2.639549s. The tail requires future
  completion, peer-thread termination, zero response bytes and no prior cleanup.
  Its actual output separately observes **natural EOF1/read error none**,
  `cancel(true)=true`, `isDone=true`, `isCancelled=false`,4,152,875ns from future
  cancellation to the returned peer latch. EOF versus read error is reported,
  not an assertion in this saved source; the reviewed actual observation must
  not be generalized into a stronger authored test. See the unchanged
  [executed source](JavaFxPreheaderCancellationProbe.java).

The saved JDK17 `MinimalFuture.cancel` disassembly calls the owning exchange
cancellation before superclass cancellation. A downstream `exceptionally`
handler can complete the dependent future normally during this call. Therefore
`cancel(true)` returning true need not imply that this dependent future's
`isCancelled()` is true. The corrected diagnostic checks `isDone()` and reviews
the separate actual peer observation instead. This is not a library fix.

## Required remediation and verification

**Priority: High resource-management blocker for the pending #64 Windows Stop
criterion.** The internal-loader defect is source-confirmed; Windows's actual
historical executing route remains unobserved. Keep that distinction.

The owning fix belongs in the dependency's network cancellation contract:
cancel the pending response/exchange as well as suppressing native callbacks,
preserve malformed-URL/null-future handling, and define idempotence and body/
upload ownership. A one-line future cancel is a candidate, **not a verified
complete patch**, especially across constructor/callback races, compressed
reads, already-completed futures and JDK versions.

Before selecting a patched distribution or local fork:

1. Qualify the corrected dependency build/source/provenance and a real public
   Worker cancellation route; never silently shadow an internal class or modify
   shared Gradle caches. No currently checked official branch has the fix.
2. Add strict dependency regressions for zero-header HTTP/1.1, real HTTP/2 stream
   cancellation, stalled plain/gzip/deflate bodies, redirect, upload streams,
   repeated cancellation, early completion and independent concurrent pages.
   Assert actual EOF/stream reset or release without server teardown, suppressed
   late native callbacks, and continued operation of unrelated requests.
3. Execute the unchanged failed NativeCmpKit Windows Stop method with the
   qualified dependency, retain all six predicates/10s and require its same-owner
   recovery tail. Reuse applicable other accepted results without replay.
4. Verify Linux/macOS/Windows and supported JDK compatibility, upstream/native
   binary consistency, checksums/signatures, dependency notices, consumer and
   API/ABI gates. OpenJFX's GPLv2-with-Classpath-exception obligations differ from
   NativeCmpKit's Apache-2.0 license; do not relabel copied dependency code.

Rejected shortcuts: private `com.sun.webkit.useHTTP2Loader` override, JVM-wide
HttpClient shutdown, an unverified version bump, per-request fake EOF,
frame-absence inference, classpath shadowing and unlicensed repackaging. No
dependency change or release-readiness approval has occurred in this checkpoint.

