# Private iOS provisional DNS proposal — original #64 / NATIVE-005 criterion three

**Source/tooling preparation only. ZERO compiler, SDK, native, DNS, socket/network,
Git, API or dispatch executions here. #64 remains open.** Root owns integration,
refreeze, serial compile, immutable native request and original source/results review.

## Small finite native request

One separate method, `nativeProvisionalDnsFailFailResetsPreviousErrorBeforeCommitOnSameDocument`,
is declared in `IosWebViewProvisionalDnsAcceptanceTest.kt`. Profile
`ios-webview-provisional-dns` selects only that method through focus
`webview-ios-native-provisional-dns` and the existing genuine UIApplication/Worker
host. No simulator identity was guessed for a future request.

The initial document is real inline HTML without external resources. Two absolute
HTTPS links use separate host labels under a freshly NSUUID-nonce-qualified
`.nativecmpkit.invalid` name. Both navigation requests originate from actual DOM
link clicks, not state/content/navigator loaders that would hide a start-reset bug.
The first actual provisional DNS error seeds the preceding public error; the
second real start snapshots that preceding error before forwarding the framework
callback to the acquired production state, then requires empty errors/reset
public title/final URL in Loading before any commit. The five normal implemented
WK callbacks are forwarded; zero commit, finish and postcommit failure callbacks
are required. Only actual `NSURLErrorDomain` / `NSURLErrorCannotFindHost` / **−1003**
with the same retained native navigation can pass. Offline −1009, TLS −1200,
timeout, missing/duplicate callback, injected NSError and foreign owner cannot.

A strongly retained test-only forwarder observes normal framework callbacks and
retains the original native WK/state/observer/window lease. It records bounded
facts/faults instead of throwing through asynchronous Objective-C callbacks. Its
exact original state delegate is restored in `finally` only when the acquired
lease is still exact; cleanup errors preserve the primary failure. The unchanged
host then proves real Compose/WebKit delegate/window/superview release before
restoring the prior owned application root. The retained real DOM title, body and
`document.URL`, native title and current owner must survive both DNS failures.
No production API/body, fixture transport, KVO, UIApplication release or cleanup
implementation changed.

## Resolver limit — explicit, not a controlled fixture claim

The owner expressly allowed a fresh reserved-nonce `.invalid` URL and the existing
system resolver. No controlled resolver, DNS proxy, hosts file, packet capture,
uncached resolver query or on-wire DNS exchange is claimed. A fresh nonce avoids
reusing one previous destination but does not defeat all OS/WebKit/recursive cache
or runner policy behavior. Actual WK −1003 is the required classification witness;
an existing resolver can instead time out or return another error, which remains
red. HTTPS avoids adding an ATS exception, not a trust/TLS-failure substitute. No
resolver/network/system-offline state is mutated, and no retry/fallback converts
a non-DNS outcome into a pass. Existing genuine host waits remain bounded at 10s.

## Exact source scope and prior evidence

The proposal depends on the root's exact14-file #64 staged/live composition and
its unchanged sealed42 literal catalog. Its frozen pre-DNS base is 1078 library /
1155 combined inputs; this is a private source snapshot, not Git/actual-builder
attestation. Only six existing files change using 15 disjoint, single-occurrence
literal fragments; there are two source additions (native method and new CI guards).
The full unfiltered iOS WK inventory honestly expands **13 → 14**. Four affected
inventory methods and one profile-catalog method are fresh checks; old thirteen-case
acceptance is not relabeled as fourteen. Old finite ten/seven/one and two-method
localhost selections remain exact. `ios_ui_application.py` is byte-identical and
retains mode0755. Existing modified file modes are preserved; new source modes0644.

The sealed localhost native source SHA is
`4cd87f0294407f72733815a8c2558d405fa0de906968f52ff9bd71ef01c9f737`;
its fixture SHA is `a5b4780ab39822a4ee261c07d434bacb9ce9fe72943c1924eeaddcbbeb1e17a7`.
Both entire files/assertions and all sealed deliveries/model results are unchanged.
Desktop/Android/camera sources, batch plan/controller and all other frozen inputs
are unchanged. Android recovery/media and browser-offline agents received the
four iOS-only shared routing anchors; root owns final composition with their work.

## Once-only important models and retained refusals

- One genuinely new profile guard first observes the absent DNS profile in the
  pre-DNS matrix: one source red retained, not a runtime/native failure.
- Six new DNS source/real in-process generic plan/receipt models plus five newly
  affected inventory/catalog methods pass **11/11**, no failure/error/skip,
  **1.380101s**, **2335 private inputs held**. Unchanged accepted model methods
  are not replayed. Candidate maps are **1080 library / 1157 combined** and match
  before/after; these model results are not DNS/UIKit/SDK acceptance.
- The strict private audit retains **187 open + 89 remove denials**, not process,
  socket, compiler or network operations. All eleven methods complete successfully,
  all frozen source identities hold, and the synthetic fixture root is empty on
  post-run readback. Individual denial causes are not guessed from counters; raw
  paths/transcripts are excluded. These are not native cleanup results.
- An extra old42-against-live readback refused once because root had already
  integrated the exact14 composition. It is retained; no old42 reapply/retry or
  accepted model replay follows. The separately hashed staged14 base is used.

The unified patch is reproduced strictly in-process at exact offsets/ranges using
all preimages; no Git, external patch command, fuzzy search or whitespace repair.
`pre/` and `post/` contain only the six owning preimages/eight reviewed postimages,
not a frozen checkout. Hash/mode manifests and canonical maps permit independent
readback. The safe archive excludes raw logs, private roots, temporary receipts,
keys, credentials, binaries and machine/native diagnostics.

## Next owning action, not authorization

`future-compile-only.json` declares only
`:calf-webview:compileTestKotlinIosSimulatorArm64` on a real Darwin Arm64 host,
serial/no-parallel/one worker, bounded1800s/8192MiB reserve. It is not run or
submitted here and has no guessed simulator/native identity. Compiler/interface
availability remains unverified. Root must integrate/refreeze, compile, independently
review and request only this one new native method when appropriate. All two-heavy,
minimum/native/consumer/API-ABI/dependency/legal/security/readiness and
publishing/Pages/main/history gates stay. No issue closure or release is authorized.
