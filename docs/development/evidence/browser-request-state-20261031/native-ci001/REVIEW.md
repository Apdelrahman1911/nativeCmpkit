# GET-only browser request-state actual review

**Accept the exact browser subset; do not close #64/NATIVE-005.**

Run [41255011146, attempt 1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41255011146), immutable commit `100d43ca0e7c5049631002e2bf6a2db49d4c2573`, finished **success** at `2026-11-01T00:15:12Z`.

| Target | Actual results | Gradle exit / wall time | Original XML SHA-256 |
|---|---:|---:|---|
| JS / Chrome | 3 passed; 0 failed/error/skipped | 0 / 261.08 s | `0ad2f53d13543259fa1b98b3716c7bfe29e89b0cbf62bf87d9f24a27cb0dec1f` |
| Wasm / Chrome | 3 passed; 0 failed/error/skipped | 0 / 271.07 s | `29e0027cefe322017b61c6dfebbb67011296228b321090a95b3c1cd3aac9c801` |

Exactly **three distinct new methods, six target executions, two original XMLs**. Both jobs were serial and used Google Chrome `156.0.8078.47`, Linux x64, JDK `17.0.21`, Rust `1.98.0`, Gradle `9.7.1`. Each exact class-filtered task has one fresh execution marker, no old report quarantine, clean immutable source before/after and no changed inputs. Tooling succeeded; four unrelated jobs were skipped. **No accepted #63/#65/#11 replay.**

## Original acquisition and immutable identity

The attempt-log archive and both original artifacts were acquired **once each, no retry**. All 75 ZIP members retain exact original bytes, confined unique regular paths and checked CRCs. Both artifact archive sizes/digests match GitHub metadata. Original archives, logs, hostnames and XML remain private; the two public XML mirrors replace **only** the hostname attribute, with original/transformed hashes recorded separately.

Read-only integrity review passes **69 gates**, not 69 library tests. Independent Git tree/blob reads verify all **1023 frozen library / 1100 frozen combined** SHA-256 identities. All four uploaded before/after maps exactly match the 1023-library map (`bc8f53c5252f4b76b30919e3539a880b30e33e243c633180932a6193775b3842`). The 1100-combined digest (`2a378e45dbfd9a0a20e0e8fe7cf01a6c30f6b8a0419d4724028008cf6783fb6f`) is **frozen source preflight only: ZERO uploaded actual combined maps**. The reviewer does not require unrelated lead live-tree legal changes to be clean. Seventeen inspected source identities match immutable Git; this is not legal/publishing clearance.

## Source-bound native witnesses

The original XML identities correspond only to:

1. `rejectedOptionsRetryAndNativeReloadResetErrorsAndRequestedMetadata`: native held-response and complete-document witnesses; header/encoding rejection with zero rejected HTTP page work; native Reload of the actual old readable URL rather than rejected request UI; second held request and clean successful retry.
2. `realRedirectReloadAndOwnedNativeStopHaveDistinctRequestAndTerminalMetadata`: actual emitted 302/Location and native terminal destination; requested versus terminal metadata; Reload without replaying redirect; actual native `window.stop()`, owned response cancellation/zero pending/no completed hold, then complete-document recovery.
3. `repeatedActualTransportRefusalsCannotRetainOldMetadataOrErrorsDuringRecovery`: two actual response destructions before headers/body, trusted native terminal events, inaccessible old document, correct native src, no executable response-page witness, actual abort/close receipts including retries, no stale metadata/errors, then real inline-document recovery.

The common begin-request reset and readable-native Reload implementation are checked against these witnesses. Native `load` or `Finished` is **not** interpreted as HTTP/framing/network success; absent iframe error reporting is not fabricated. Controlled Trusted pages do not weaken the production Isolated/CORS/CSP boundary. Detailed immutable paths/lines/hashes are in `source-witnesses.json`.

## Owned cleanup and limits

Every passing asynchronous method awaits failure-preserving NonCancellable cleanup: Compose viewport disposal, null state iframe plus native disconnection, listener/control-iframe removal, and exact acquired nonce-owned HTTP close. The server exempts close from exhausted work budget, destroys only owned leases, waits for actual response close, verifies zero pending/exact session before deletion and exact close acknowledgement, with a 2-second close cap. Receipt polling retains 32 polls/500 ms/original 15 s; session/stage/pending/work bounds and zero-expiry assertions remain. These are assertions within the six passing methods, **not separately uploaded per-response telemetry or Chromium PID/process-tree receipts**. Generic Actions orphan cleanup is not substituted as ownership proof.

Both XML suite times are `0.005` s, with method times `0.001/0/0`. These **do not measure native browser work**: matching-version static runner inspection shows Kotlin's Karma reporter buffers start/finish messages without timestamps, while KGP uses message arrival time rather than supplied duration; the returned runTest Promise is forwarded to Mocha. No premature asynchronous completion is inferred. `runner-timing-context.json` explicitly labels local context as explanatory, not the actual downloaded runner bundle. **Raw gradle.log/generated bundle was not uploaded**, so direct browser console and native per-method wall-time recovery remain unavailable. XML/receipt/runtime/immutable source are the actual evidence, not an invented console transcript.

Saved job logs have no Actions error markers. Node.js20 action deprecation warnings are retained. Three reviewer-only refusals are preserved: incorrect map-digest serialization, a guessed dispatch input key, and demanding byte-identical initial/later runtime timestamps. Only the independent read-only checker was corrected to the observed immutable definitions; originals stayed unchanged, with no tests/models rerun.

## Remaining original criteria

**#64 must remain open.** The full Android/Desktop/iOS fail→success/fail→fail/reload/stop/redirect matrices, actual offline destination, and actual WKWebView provisional DNS/TLS failures before commit remain independent and unverified. Owned pre-header TCP response refusal is not system-offline/DNS/TLS acceptance. Prior failures retain their original status/unknown causes; no accepted evidence is replayed or substituted.

The reviewer performed no live-source edit, project CLI/model/test/compiler/build/native dispatch, Git/GitHub write or issue mutation. No release/package/deployment, Pages, main/history, dependency/ABI/consumer/legal/security/readiness clearance or capacity-policy change is authorized by this review. Public-safe evidence/manifests and redacted XML are provided for lead-owned integration only.
