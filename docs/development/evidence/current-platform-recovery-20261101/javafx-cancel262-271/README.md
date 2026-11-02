# JavaFX cancellation: Linux and Windows dependency fix qualified

**2026-11-02, solo review271. The patch is not active in the library.**

The owning change to exact OpenJFX21.0.13 is:

```java
canceled = true;
if (response != null) {
    response.cancel(true);
}
```

This cancels the pending HTTP exchange, instead of only suppressing callbacks.
It neither changes public NativeCmpKit APIs nor forces JavaFX's private loader
selection. [The maintained diagnostic source and legal notices](../../../../../tests/dependency/javafx-http2-cancellation/README.md)
are separate from ordinary library dependencies and publication.

## Actual outcomes; no native replay

| Original | Actual result | Scope |
|---|---|---|
| Linux263 unmodified dependency | Exit1/13.049950038s, zero-header peerEOF0 before cleanup | Retained intentional regression red; actual log names `HTTP2Loader fwkCancel`. Not historical Windows route attribution. |
| Linux263 explicit patched module | **4/4**, process0/3.533200393s | Genuine JavaFX public cancellation, native parsing and same-engine recovery; zero library methods. |
| [Windows267](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41409884370) | Checkout failure: `Filename too long`; **zero compiler/native** | Initial evidence upload also failed with no output files. Neither failure is a JavaFX outcome. |
| [Windows270](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41410458520) | **4/4**, process0/6.813s, probe compiler0/2.922s, patch compiler0/1.016s | Windows2025/x64, Temurin **17.0.20.1+1**, exact revision `3bda9234d9797aa1cb1b89d1753ea88355da3e44`; zero library methods/XML. |

Both accepted four-case populations cover:

1. A real request held before all response headers; public Worker cancellation
   must produce peer EOF **before** fixture cleanup, then recover on the same engine.
2. A partially delivered plain HTML body, native parsed title and incomplete response.
3. An incomplete gzip body with SYNC_FLUSH, native parsed title and no gzip trailer.
4. Two independent WebViews: cancel one pending request, repeat idle cancellation
   three times, leave the other pending until its controlled response, and recover.

Windows cancellation-to-observed-EOF clocks are13.4235/2.1864/2.5675ms for the
first three cases. These include observer/latch scheduling and are **not**
benchmarks, OS shutdown bounds or CPU profiling. Plain/gzip response counters
are24,237/306 bytes. The controlled complete response is not an EOF substitute.
Success rows precede cleanup; **whole process exit0** additionally witnesses that
the owned thread joins, Stage cleanup and JavaFX exit returned. No physical UI,
heap/GC/other-engine/full-platform/security inference follows.

## Source/results qualification

[REVIEW271](REVIEW271.json) passes **55 passive checks** on cached originals,
not55 tests. The current parser independently accepts the saved Windows stdout;
all command stream bytes/digests, selections, head, actual JDK and scopes match.

- All **11 actual source/JAR bindings** match immutable Git, exact acquired Maven
  bytes or the one owning generated source delta.
- All **10 reported Windows compiled-class hashes** exactly match independently
  retained Linux263 class bytes. The actual Windows binaries are not uploaded;
  this is a hash cross-check, not independent Windows binary extraction.
- The source-qualified runner checks before/after source and binary hashes in
  process. An independent actual after-map file is **not** an upload.
- Member descriptors are identical; normalized bytecode changes only `fwkCancel`.
  All four generated inner classes retain normalized code/descriptors. This is
  not full published-library or packaged-consumer API/ABI certification.
- Prior1,203-library/1,281-combined selectors **exclude these new diagnostic
  files**; the separate execution bindings cover them. Do not expand their scope.
- Original GPLv2/Classpath, assembly exception and additional-license bytes are
  preserved. Same-registry checksums provide consistency, **not** independent
  signing, vulnerability clearance or complete redistribution/legal acceptance.

The [24 unique source controls](source-controls-summary.json) comprise first18,
then NEW4, then checkout NEW2; they are not one fresh24-method invocation. The
first18 have observed terminal output only, without a retained original log or
immediate-before map. Subsequent exact receipts keep their stronger custody.
Accepted populations and the baseline were not replayed. Actionlint1.7.12 passes;
full whitespace exit0 is not claimed for preserved legal/patch/copied-source bytes.

## CI recovery and remaining owning work

The development-only workflow disables CRLF conversion **before** checkout,
enables Windows long paths and sparse-checks out only the dependency diagnostic.
One hosted job uses contents-read, no persisted credentials, no dependency/result
cache and no package/JAR/class upload. Manual dispatch by registered workflow ID
works without changing `main`. Docs/runner-only edits do not trigger an accepted
native replay. The sparse green run proves **no full-library checkout or build**.

**#64/NATIVE-005 stays open.** Original library Windows Stop41398651975 remains
failed at peerEOF0/pending1 despite WorkerCANCELLED/libraryFinished; recovery was
unreached. Next: create a maintained, explicitly identified dependency artifact
candidate with complete corresponding-source/notices/provenance, replace rather
than shadow the original web JAR, and execute only the failed original public
Compose/JFXPanel Stop method. Keep its original10s/six predicates and ownership.
Default dependency adoption, other Desktop and genuine browser-offline criteria,
platform consumers, API/ABI, vulnerability and release checks remain separate.

No issue closes here; last verified state is97closed/75open/172total and ledger
22implemented/42partial/95verified/five unresolved. Continue solo, serial local/
8GiB reserve/max2 combined hosted reservations including queued work. Publishing,
Pages, `main`, history and all native/consumer/legal/security/readiness gates stay.
