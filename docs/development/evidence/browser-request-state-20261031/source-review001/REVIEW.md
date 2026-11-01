# Independent #64 browser request source and cleanup review

The reviewed Reload correction and the integrated owning fixture repair are ready
for the finite browser request. No remaining concrete source blocker was found in
this bounded review. **#64 remains open:** compiler and localhost HTTP results do
not satisfy its complete native acceptance criteria.

This review covers the browser Reload branch, the three new shared JS/Wasm request
methods, the separate request HTTP middleware, and the finite request controller
route. It does not expand Android/Desktop/iOS matrices, repeat accepted suites,
dispatch CI, or authorize publishing/security/readiness changes.

## Frozen source and preservation

- The initial review froze 85 selected inputs at
  `69a93c6d879435d4c620979b992a77161baae615`.
- The initial browser source matched the lead's successful dirty compile. The
  whole 1,100-input combined map had subsequently changed only at the two Apple
  capability tooling files; this is recorded separately and is not a browser
  source mismatch or a fresh execution.
- Twelve accepted #63 support files are byte-identical to the accepted identities
  at `6eaac5e01e5631d567e571c32d6523d663a8a184`. The only changed accepted production
  file differs exclusively inside Reload. The accepted content methods and
  iframe/CSP/XFO fixture remain unchanged. Existing #65 and #11 acceptance is
  retained without replay or reopening.
- The lead integrated the exact three cleanup postimages. The final readback
  matches their hashes. The three native method bodies remain byte-identical;
  the Kotlin changes affect only fixture acquisition and receipt polling.

The earlier shared compile was Gradle exit 0 in 103.03 s with 1,023 library and 1,100
combined inputs held, and zero native executions. The lead subsequently reports
the two owning browser compiler tasks exit 0 in 38.01 s on the integrated cleanup
sources with the same counts held; the unchanged camera APK was not rebuilt.
These are separate compiler observations. The independent reviewer ran no
Gradle or browser task.

## Owning blockers and repair

The original request middleware enforced its 128-request budget before processing
`close`. Receipt polling every 10 ms for 15 s could exhaust that budget and strand an
acquired session: later close returned 409, and held responses could only expire
at 20 s. The session map was never deleted. This was reproduced using actual
localhost HTTP requests and a genuinely unfinished response. It is a fixture
defect, not an observed cause of a native CI failure.

The repair keeps `close` available for an existing non-closing session after the
work budget is spent. Work requests still refuse above 128. The original response
close promises, pending-map identity checks, and exact zero-pending close receipt
remain required.

The original Kotlin fixture also closed unconditionally when open failed. A
duplicate token could produce `open-refused` and then close another invocation's
existing session. A private acquisition flag is now set only after the exact
`opened` receipt. Unacquired cleanup returns without a close request; successful
cleanup clears the flag only after the exact `closed` receipt. An uncertain open
is not promoted to an acquired lease or a cleanup success.

Receipt waits now have an explicit maximum 32 attempts, 500 ms spacing and the
existing 15 s timeout. The current native methods have at most two waits per
session: 64 polls plus fixed controls fit below 128. Unexpected exhaustion still
fails the operation while leaving owned close available.

## Observed regressions

Exactly three new owning tooling methods were run against frozen originals and
private corrected postimages. Accepted request guards and accepted browser suites
were not replayed.

- Final original-source run: 3/3 expected failures. The actual HTTP case observes
  work budget 128, the additional receipt 409, and close 409.
- Corrected run: 3/3 pass, exit 0. One method uses Node's built-in HTTP server/client
  and the real middleware; two methods check acquisition ordering and the finite
  Kotlin polling policy. The source guards are not Kotlin runtime tests.
- The corrected HTTP case observes extra work 409, owned close 200, actual held
  response abortion, successful exact-token reopening, duplicate-open refusal,
  the existing owner's continued readability, and final close. It sends 135
  bounded requests to its exclusively owned 127.0.0.1 ephemeral listener.
- Both final red and green HTTP harness runs wait for every owned server-response,
  socket and client-request close callback, then verify server closed and zero
  sockets/requests/timers. Buffers are limited to 8 KiB; individual HTTP requests
  have 2 s timeouts and the Node subprocess has 20 s timeout. No external connection,
  browser, Gradle or service is used. The added tooling test requires Node.

The first harness result reproduced close 409 but inspected resource counts before
close callbacks drained. Its source and result are preserved, followed by the
corrected event-waiting harness; no cleanup pass is inferred from that first
snapshot. A separate initial source reader refused an assumed multiline original
Reload shape. Exact accepted hashes and prefix/suffix comparison recovered that
reader without a source change or native-cause inference.

## Request, event and response ownership

Reload reads the mounted readable document's native `location.href` before
`beginRequest` and native reload. Thus rejected URL B cannot label reloaded
document A, and a redirect-start URL cannot label a reload of its final URL.
Opaque/cross-origin access still falls back to the existing accepted loader;
no sandbox or same-origin boundary is bypassed. A readable inline reload may
identify `about:srcdoc`; the HTTP(S)-GET saver policy remains unchanged.

The tests mount the public Compose WebView and use public state/navigator loaders.
They register trusted native load/error listeners on the exact mounted iframe.
Page and control witnesses validate native WindowProxy sender identity, actual
origin, trusted MessageEvent, session token and stage. Held/released HTTP responses
and stage markers distinguish loading, terminal documents and repeated reloads.
Redirect checks retain the actual emitted Location header and requested-versus-final
URL distinction. Stop requires actual cancellation/close of an unreleased owned
response; later idle checks also reject expiration as a stop success.

Repeated refusal uses response destruction before headers/body, actual per-stage
request/close receipts, native terminal events and an inaccessible current document.
The old readable document cannot serve as its failure witness. An iframe load
event alone is never treated as HTTP, framing, authentication or transport success;
empty native errors remain permissible when Chromium deliberately hides the error.
This is owned TCP-response refusal, not global offline, DNS/TLS testing, or reliable
iframe error reporting.

The existing request reset records the requested URL and clears terminal metadata
and errors before
loading or option rejection. Rejected headers and encoding retain distinct
single-request errors while the unchanged native document stays observable to
the test. Successful recovery requires actual stage-specific readable documents.

Cleanup runs under NonCancellable and preserves a primary failure while adding
cleanup failures as suppressed errors. Viewport disposal, native listener removal,
control iframe removal and session closure remain required. Middleware limits stay
32 sessions, 16 stages, 4 pending responses, 128 work requests, 20 s hold expiry and 2 s
close deadline; cleanup availability is the only budget exception.

## Finite route and original criteria

`webview-request-state` selects only calf-webview JS/Wasm, focus
`webview-browser-request-state`, and the exact three request methods: six future
target executions. Source admission retains exact declarations, the HTTP fixture,
no ignore annotations, and source snapshots that include module Karma fragments.
Result collection requires the exact target-qualified XML identities and existing
fresh-report/task-marker rules. The new serial profile preserves read-only
permissions and the existing full slots; source routing is not native acceptance.

The original criteria remain unchanged:

1. Fail→success, fail→fail, reload, stop and redirects on every target: the browser
   request methods remain pending actual JS/Wasm execution and independent result
   review. Complete Android/Desktop/iOS matrices remain required.
2. Browser same-origin→cross-origin→inline and blocked framing: accepted unchanged
   #63 evidence remains applicable. The new owned transport-refusal method is
   pending; a full offline-destination claim is not established.
3. iOS provisional DNS/TLS failure before commit resets prior errors: genuine
   WKWebView DNS/TLS execution remains unverified.

The lead retains immutable requests, actual source/result acceptance and closure.
No browser request was dispatched by this reviewer, and no native result,
publication, Pages, release, ABI, consumer, dependency, legal or security readiness
gate is cleared by this review.

## Review artifacts

`input-freeze.json`, `compile-input-applicability.json`,
`independent-preservation.json`, `production-reload-only.diff`,
`patch-manifest.json`, `browser-request-fixture-cleanup.patch`,
`red-regressions002.{json,log}`, `green-regressions001.{json,log}` and
`final-source-readback.json` retain the exact source identities and observations.
Initial harness and reader refusals are retained separately. Private raw working
paths should be redacted if underlying logs are copied into public evidence;
original source/result hashes must remain recorded.
