# Current OpenJFX21u cancellation source — observation386

A new read-only GitHub metadata/source acquisition observed `openjdk/jfx21u`
`master` at `dd5bd597dc166a8b3807cde608109d0b6dc156be`, commit date
2026-10-21T19:17:38Z. The exact path is
`modules/javafx.web/src/main/java/com/sun/webkit/network/HTTP2Loader.java`.

Its SHA256 remains
`e2413d1ac8cb78be77f97fc6add5e17bee1859e1c5fcbb97481444eb62eac43f`,
identical to the already acquired official21.0.13 Java source. At current
lines419–424, `public void fwkCancel()` still logs and sets only
`canceled = true`; it does not cancel the pending response future. The newest
path-changing commit is `48f6f5ba5b1f38281b38cd1f29a215f795ba0309` dated
2022-12-22. See `OBSERVATION386.json`, original commit metadata and original
path history for exact IDs, messages, timestamps and links.

**Confirmed source observation only:** a current21u branch update cannot be
claimed to have fixed this defect based on version/date alone. This does not
prove a future release is unavailable, identify an official Maven/native binary
build commit, certify corresponding source, or change dependency adoption.
No source code was executed, no compiler/native test ran, and normal dependencies
and the private candidate remain unchanged. #64 remains open.

The first local post-acquisition parser assumed a private method; actual source
is public. That selector refusal is preserved in the receipt. The correction
reused the same original bytes and path history; no request or archive repeated.
The acquired third-party source remains private evidence with its full original
Oracle/GPLv2-with-Classpath-exception header. This repository archives hashes,
public Git metadata and the small relevant method excerpt, not a new distributed
OpenJFX source or binary artifact. Existing legal text/attribution is in
`tests/dependency/javafx-http2-cancellation/NOTICE.md` and its linked GPL texts.
Full native corresponding-source/third-party/security/consumer/API–ABI work is
still required before ordinary adoption. No release/package/deployment/Pages/main
or upstream mutation occurs; investigation continues solo.
