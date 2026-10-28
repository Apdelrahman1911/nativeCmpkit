## Verified fix — direct closure after important native-session tests

All **three original NATIVE-013 acceptance criteria** pass at immutable **857088dd3de21258f65d2ba3f6a7dee62ad5540c**, [run40619253986](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40619253986): **43/43 actual desktop WebView methods**, eight fresh XML, zero failures/errors/skips. Three new native-cookie integration methods supplement the existing40; all11 actual JavaFX methods run. Only calf-webview on Linux/Xvfb ran.

1. A **real production JavaFX owner/WebEngine** loads a loopback login endpoint that sets an HttpOnly session in the actual JavaFX native jar. Library **getCookies** preserves the session and global handler identity; a real followup HTTP endpoint requires that same authenticated cookie. Native request headers and actual **document.cookie** prove HttpOnly is sent to HTTP but hidden from JavaScript; Secure cookies are not sent over HTTP or exposed to insecure document.cookie.
2. An application custom **CookieHandler is installed before a new native view**. Creation, library reads, unsupported full-store deletion and disposal retain its exact identity and cookie value. Toolkit is bootstrapped first; this does not claim completely fresh-JVM dependency cold initialization.
3. **Two managers run on two distinct overlapping worker threads**, storing32 values into the actual shared native jar. Both API reads, actual native HTTP request headers and actual WebEngine document.cookie retain every value. Fixture-owned cookies are individually expired and verified gone; HTTP threads terminate. No application-global store is cleared.

Root repair: CookieManager adapts the existing JavaFX/application handler without ever installing a replacement. Explicit-handler ownership is opt-in and not global; shared handler operations are synchronized. Generic handler metadata/full-store deletion limitations produce explicit unsupported behavior rather than fabricated capabilities. Existing public packages/constructor/API remain.

Review verifies743 exact own-Git inputs, before/after maps, all43 authored testcase identities, every XML/artifact hash, actual command and runtime/SDK correspondence. Required tests → source/results review → **direct closure now** → archive/index afterward. Original upstream #425 reference/body/title/labels remain intact.

Scope: actual JavaFX21/native jar/HTTP/document.cookie on Linux/Xvfb, controlled public loopback session rather than real-account/password login. Secure **HTTPS-URI cookie policy** is checked through the native handler, not an HTTPS-network/TLS certificate test. Other JavaFX/OS matrices, native sanitizers, minimum devices, dependency/legal/API-ABI/full consumers/security/release requirements remain open. No packages/releases/deployments published.

Evidence: `docs/development/evidence/github-actions/40619253986/`. Prior failed run40617556199 remains failed41/43; test-only HTML MIME correction keeps the10-second native title barriers, actual MIME assertion and every session/thread/cleanup assertion. No production change was needed for that fixture repair.

<!-- nativecmpkit:direct-acceptance:NATIVE-013:857088dd -->
