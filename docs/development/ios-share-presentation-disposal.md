# iOS Share presentation/disposal ownership

This is a bounded fix for the Share part of #88/NATIVE-033. It does not close
the whole threading, sharing-stage, saver, or sample-resource findings.

## Owning implementation

`calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt`
retains a Request through these phases:

| Phase | Disposal behavior |
| --- | --- |
| Prepared | Release a request that has not entered presentation. |
| Presenting | Clear the result block, retain the controller/scopes, and await the actual UIKit presentation completion. |
| Presented | Start dismissal of the captured controller, not another modal on the presenter. |
| Dismissing | Await its actual dismissal completion. Repeated disposal does not dismiss twice. |
| Released | Ignore late completions; owner invalidation and cleanup occur once. |

Disposal while native presentation is queued or animated must not interpret nil
backlinks as completion. An already-running noncancelled native dismissal can
acknowledge completion; a cancelled transition queues an owned retry. There is no
timer or nil-link release fallback. If UIKit never acknowledges, the request
remains retained and verification fails rather than claiming cleanup.

The existing public constructor, remembered current callbacks, content snapshot,
main dispatch and activity-result mapping remain. The terminal-lifecycle repair
intentionally **defers result delivery until owned native cleanup completes**:
the first activity input initiates disposal, but is not itself a dismissal
acknowledgment. Owner disposal suppresses even an already pending result;
duplicates/late blocks cannot replace it. Controller/scopes stay owned through
the real presentation and dismissal completions, and owner invalidation precedes
callback/reentry. This is an observable timing correction, not an API-signature
change. If UIKit never acknowledges cleanup, the request remains retained rather
than reporting successful release. Internal,
main-confined read-only owner/request/presenter observations support verification;
they are not public APIs or native completion hooks. Actual packaged API/ABI
compatibility is a separate gate.

## Library-level native verification

`calf-share/src/iosTest/` contains a genuine UIApplication/Compose host and
13 finite application methods: four owning-host cases, four explicitly controlled
Request cases, and five UIKit/public-launcher cases. The controlled cases are not
OS-transition evidence. The real cases retain actual owners before launch and
capture Requests before native/deferred scheduling can throw.

The host refuses root restoration or source-file deletion before request release
and genuine presentation/dismissal acknowledgements. Stable DidAppear, a fresh
DidDisappear, exact restored root/window, and verified Worker completion are
separate cleanup obligations. Failed stages retain their leases; process exit is
not substituted for graceful cleanup.

The `ios-share-presentation-disposal` workflow profile selects only these
13 methods on the existing macOS Arm64 iPhone library host. KLIB compilation
executes zero native methods. Actual Apple link, callbacks, original fresh XML,
protocol agreement, held inputs, and owned cleanup are still required.

## Independent sample feedback repair

`sample/common/.../screens/FileSaverScreen.kt` now consumes the existing
`FileSaverEvent` API. Saved, Cancelled, DownloadStarted, and Failed all clear busy
state. Only Saved claims persistence; a browser download request is not a saved
file. Failures show generic recoverable feedback, not platform diagnostic text.
Four common and one Desktop mapping tests are separate sample checks, never
substitutes for library integration or real browser download verification.

## Evidence and remaining scope

The [Share227 original review](evidence/current-platform-recovery-20261101/share227-original238-239/README.md)
preserves run41390900453 **FAILED:0 pass/one fail**. Its finite trace and exact
source establish that the old fixture dismissed first and supplied its two true
inputs only inside dismissal completion, after a false terminal input had already
released the request. Ignoring those stale inputs was correct; the observer does
not independently attribute native-versus-fixture callback origin. Separately,
the old production callback released ownership before any owned dismissal barrier.
The corrected fixture supplies the deliberately controlled first true input while
presented and requires production's genuine UIKit dismissal before callback.
Four new controlled Request scenarios execute inside that one public method;
they are not four independent native JUnit executions or OS-recipient success.
The [terminal/AWT240–242 batch](evidence/current-platform-recovery-20261101/terminal-awt240-242/README.md)
records source controls and KLIB compilation only. Actual Apple verification
remains required; accepted earlier methods are not selected for replay.

Earlier [Share188](evidence/current-platform-recovery-20261101/share-original188/README.md)
at6c8684a3 remains **FAILED:12 pass/one fail**, three fresh XML, Gradle1/1230.61s.
Independent original source/results review accepts the twelve bounded methods
for reuse: four native host, four expressly controlled Request, three genuine
UIKit disposal, and one disposed-public Main/Default/IO inertness method.
The remembered-live method fails in FIRST/Main: expectedCompleted/actualDismissed;
live Default/IO, successful-result reentry and remembered disposal tail are not
reached. Individual UIKit terminal-input order/cause is unknown, not inferred
from a source-conditioned line. Native transport/Worker/owned cleanup passes
separately and does not override JUnit failure. Actual1179 inputs hold;1257 is
Git provenance only. Do not replay the accepted twelve or close #81/#88/#48/#100.

See [the owning batch](evidence/current-platform-recovery-20261101/share-owning168-179/README.md).
Main Thread Checker, a full Kotlin/Native concurrency suite, interactive rollback
occurrence, successful security-scope balancing, bookmarks, delayed/cross-process
recipient reads, other mobile APIs, macOS/Android sharing stages, browser runtime
parity, actual sample export/navigation cancellation, and physical/minimum/iPad
coverage remain unproved. No #88/#81/#48/#100 closure or release readiness follows.
