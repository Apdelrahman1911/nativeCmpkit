# macOS security originals and failed-only policy recovery — 385–395

## Actual originals: preserve the failed run, accept only its passing subsets

[Run 41532837164](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41532837164)
at `3a3a93bdee07f7568e6ff78c952efd6223c41df7` remains **FAILED**.
Each host executed exactly three native methods in three original XML reports:

| Host | Original native result | Gradle | Actual JDK / Gradle |
| --- | --- | --- | --- |
| macOS ARM64 | **2 pass / 1 fail**, no errors/skips/N/A | exit 1 / 145.58s | 17.0.21+9 / 9.7.1 |
| macOS x64 | **2 pass / 1 fail**, no errors/skips/N/A | exit 1 / 192.20s | 17.0.20.1+1 / 9.7.1 |

The **four passing TLS/rendering and cookie methods are accepted and excluded
from unchanged replay** after source/results review, not merely the runner status:

- `DesktopWebViewTlsRenderingAcceptanceTest.trustedHttpsPaintsTwoAuthoredDocumentsAndUntrustedCertificateFailsBeforeHttpOnTheSameOwner`:
  ordinary PKIX/hostname policy before JavaFX startup; actual mounted native
  ownership; two distinct real Node snapshots with authored opaque pixel pairs;
  genuine untrusted-certificate native failure before HTTP; same-owner trusted
  recovery; owned native-window/server/thread/trust/certificate cleanup.
  ARM64 method 7.635s; x64 11.693s.
- `JavaFxCookieIntegrationTest.realNativeLoginSurvivesLibraryCookieReadsAndHttpOnlyNeverLeaksIntoDocumentCookie`:
  genuine native cookie jar and loopback login/request; library reads preserve the
  login; Secure cookies stay off HTTP and HttpOnly cookies stay unavailable to
  actual `document.cookie`; owned-cookie/server/native cleanup. ARM64 2.649s;
  x64 3.102s. This is not a real-account or HTTPS cookie-login claim.

**57 passive checks** in [REVIEW388.json](388/REVIEW388.json) bind all six original
XML identities/outcomes, four native before/after maps of 1,215 inputs, frozen Git
blobs, actual host/runtime/daemon, original acquisition, and both graph captures.
They are zero new native tests. All original archives were acquired once under
the existing exclusive claim; cached originals were reused for review.

The security-worker all-green parser correctly rejects the policy failure and
remains unchanged. Its public event lines were not uploaded in this failed run;
fresh-worker isolation is enforced by the exact executed Test.doFirst source,
not an independently retained full worker-event/OS-PID/exit attestation. Do not
turn the receipts green or infer whole-job success. Original JavaFX unnamed-module
warnings remain; they alone do not establish an engine/security defect.

## Confirmed owning startup-admission defect

Both policy methods fail with original
`java.lang.IllegalStateException: Toolkit not initialized`:

- `DesktopWebViewIdentityAcceptanceTest.kt:141` called `host.awaitDocument`.
- Its original line 254 calls `onFxThread` / production `WebView.desktop.kt:88`.
- Public Compose creates `JFXPanel` asynchronously through `LaunchedEffect` and
  the next Swing event. Constructing `WindowHost` does **not** prove FX ready.
- The already-existing `awaitCreation(state)` observes the genuine public
  `onCreated` list and checks the fixture's original failure slot without calling
  FX prematurely. The other public-creation method already uses this admission.

The owning native-test correction is only **one comment and
`host.awaitCreation(owner)` before the original document wait**. All scripts,
typed values, callback counts/throw identity, off-main/native-thread assertions,
settings/disposal assertions, original timeouts and cleanup remain. There is no
`Platform.startup`, sleep-based readiness, exception swallowing or production/API
change. Native policy behavior is still unaccepted until the repaired methods run.

## Actual full host graphs and only new advisory queries

Each host independently acquired all **24 runtime + 48 compile/test** library
configurations before native execution. Both complete captures have 108 runtime
coordinates/54 artifacts and 142 compile/test coordinates/79 artifacts. Six
actual JavaFX21.0.13 classified modules match `mac-aarch64` or `mac`; JavaFX remains
absent from ordinary library runtime metadata by design.

All actual 1,218 capture-map entries equal the frozen 1,215 library inputs plus
the workflow and two exact collectors. Before/after, original/copied graph hashes,
runtime, collector pins, successful graph phases and owned-init cleanup qualify.
Original graph commands took ARM64 225.54s + 59.06s and x64 334.87s + 59.97s.
The runtime graph bytes equal the separately accepted Linux runtime graph; this
does not erase the two actual host acquisitions.

Reuse the 142 accepted Linux advisory queries. Only **four genuinely new** exact
Maven coordinates were queried once:

- `org.jetbrains.compose.desktop:desktop-jvm-macos-arm64:1.12.0`
- `org.jetbrains.compose.desktop:desktop-jvm-macos-x64:1.12.0`
- `org.jetbrains.skiko:skiko-awt-runtime-macos-arm64:0.150.1`
- `org.jetbrains.skiko:skiko-awt-runtime-macos-x64:0.150.1`

[ADVISORY389.json](389/ADVISORY389.json) records HTTP 200, four results and **zero
coordinate matches** in 1.031180s. Database nonmatches are not bundled
WebKit/GStreamer/native-code, independent trust, licensing or security clearance.
Do not reacquire these unchanged graphs or repeat these accepted queries for the
policy-only recovery.

## Important source tests, compiler and exact history composition

- First NEW **11/11** controls pass once, unittest **1.584s**.
- Passive review found a second independent old TLS `setUpClass` raw reader.
  Only that setup reader was composed through the same exact inverse. Its
  original hash expectations and every old test method remain unchanged.
- Only the **affected inverse1 + NEW setup2** then run: **3/3**, **0.514s**.
  There are **13 unique controls / 14 invocations**, not one fresh 14-test suite;
  the unchanged first ten controls are reused, not replayed.
- The seven-source history inverse has **18 exact ordered fragments**; the first
  accepted draft had 17 and is retained separately. Both earlier ARM64 and
  External328 complete-source pins/manifests remain intact. Historical complete
  preimages remain composable; raw current readers reject old/foreign/changed
  images. No blanket hash refresh, identity guessing or native selector fallback.
- Fresh local Desktop test compilation **exit 0 / 36.01s**, JDK17.0.20+8 Ubuntu,
  Gradle9.7.1, all 1,218 library inputs held; production compile UP-TO-DATE.
  Later four CI-only deltas do not change its Kotlin/Gradle/dependency inputs.
  **Zero local native execution**, no forced unchanged rebuild.
- Actionlint **0**, current exact workflow bytes. [REVIEW395.json](395/REVIEW395.json)
  accepts 25 additional **passive** source/results checks and both finite two-row
  source preflights; zero builds/native methods during that review.

Operational reviewer refusals are retained in
[reviewer-refusals.json](reviewer-refusals.json): canonical-map versus JSON-byte
digest, typed XML message decoration and the workflow's separate input scope.
Only reviewer operands were corrected; original failures/results/pins and native
criteria were not changed or reacquired.

## Next exact execution and remaining gates

After development-only freeze/push and a fresh capacity observation, request
**`webview-desktop-policy-macos-recovery` once**: the two failed original policy
methods only, one per actual macOS host, two XML reports. It preserves a fresh,
single-class sequential JVM worker and the original all-green worker parser.
The existing graph-capture condition deliberately does not include this profile.
Never dispatch the old macOS security pair again on unchanged accepted subsets.

After its terminal source/results review, the unexecuted
`webview-desktop-security-linux-arm64-windows-pair` remains seven required methods
and two actual host graphs; do not dispatch it against a known shared startup
defect. Previously accepted Stop/request/browser/mobile populations remain excluded.
Every pair reserves **both** combined hosted-heavy slots, including queued work.

#144/BUILD-002 and #64/NATIVE-005 stay open. Last verified issue totals remain
**97 closed / 75 open / 172 total**, ledger **22 implemented / 42 partial /
95 verified / 5 unresolved**. Work is solo, local-heavy serial, 8GiB disk reserve,
read-only verification tokens, all actions allowed and no mandatory SHA pinning.
No package/release/deployment, Pages/main change or imported-history rewrite.
Ordinary JavaFX candidate adoption, maintained artifact/corresponding source,
legal/security/consumer/API–ABI and release-readiness gates remain independent.
