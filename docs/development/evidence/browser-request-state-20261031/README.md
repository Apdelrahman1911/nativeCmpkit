# Browser #64 — request/reload metadata batch

The old readable-native Reload begins request state from `state.requestedUrl`
while reloading the actual current document. Rejection or redirect can leave
those URLs different. The minimal production correction reads actual native
`location.href`; existing opaque/cross-origin loader fallback and public APIs
remain unchanged (`WebView.web.kt`, Reload branch).

Three new genuine Compose/browser methods plus a separate bounded HTTP fixture
cover rejection/retry/reload, actual redirect/held-response native stop and
repeated real transport refusal/recovery. `webview-request-state` selects exactly
these three methods on JS and Wasm: **six future target executions**, serial,
127 profiles/all11 slots preserved. No accepted #63/#65/#11 test is altered/replayed.

The initial source red and **9 important modeled passes** are retained. Root
integration found one stale exact-four-clause workflow guard: selected2 methods,
1pass/1fail. Only its exact approved membership check was repaired;2/2 owning
checks and10 modeled controls pass. [Compilation](../camera-browser-settings-compile-20261031/README.md)
passes **0 / 103.03 s**, with **zero browser methods executed**.

Independent review then found two **fixture-only source blockers**, not observed
native failures: request-budget exhaustion could prevent owned-session cleanup;
an unconditionally attempted close after refused open could affect an existing
token's session. A three-file owning repair now exempts cleanup from the work
budget, acquires/releases a lease only after exact receipts, and caps polling
at32 attempts/500ms intervals with the original15s timeout.

Three new important regressions reproduce **3/3 reds**, including actual owned
localhost HTTP close409 after budget128, then pass **3/3** after repair. Actual
held-response abortion, exact session deletion/reuse and released harness server,
sockets/requests/timers are checked; this is fixture HTTP, **not browser execution**.
The initial harness snapshot-before-close-callback failure remains archived.
All three native method bodies and the accepted content fixture are unchanged.
Only fixture-helper Kotlin changes; the earlier compile is explicitly pre-repair.
[Two-target test-source recompilation](cleanup001/compile001/review.json) now
passes **0 / 38.01 s**, with1023/1100 held inputs and **zero browser executions**.
Unchanged camera APK is not rebuilt. Exactly six missing JS/Wasm executions are
the next browser request; no accepted test should be replayed.

**#64 remains open.** Complete Android/Desktop/iOS request matrices and genuine
WKWebView provisional DNS/TLS checks remain independent. A native iframe load
event is not proof of HTTP/framing/network success; server response destruction
is not global offline/DNS/TLS certification. Accepted transitions/framing results
are reused only on their exact applicable source.

No package/release/deployment/Pages, API/ABI, security or readiness gate changes.
