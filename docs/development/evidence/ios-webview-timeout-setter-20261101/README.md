# iOS request timeout — exact compiler-owning source repair

Actual `41272449374` at `57057813` stays **failed**: Gradle1/685.46s,
`IosWebViewRequestAcceptanceTest.kt:237` reports `'val' cannot be reassigned`;
**ZERO native executions/original native XML**. The lead supplied that reviewed
actual result; this agent did not execute or replay it.

Apple's official mutable request declaration is
[`@property NSTimeInterval timeoutInterval;`](https://developer.apple.com/documentation/foundation/nsmutableurlrequest/timeoutinterval),
whereas [`NSURLRequest`](https://developer.apple.com/documentation/foundation/nsurlrequest/timeoutinterval)
marks the property `readonly`. The timeout is in seconds. Passive same-version
Kotlin/Native2.4.20 **ios_simulator_arm64** Foundation metadata, decoded with the
[exact official schema](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.20/core/metadata/src/metadata.proto),
exports the member `NSMutableURLRequest.setTimeoutInterval(timeoutInterval:
NSTimeInterval /* kotlin.Double */): Unit`. It inherits `NSURLRequest`, whose
`timeoutInterval` property flags518 mean **val/getter/no setter**. Exact selected
metadata/manifest/source hashes and decoded declarations are retained. This is
not a certification of the actual macOS toolchain/SDK bytes or a Kotlin typecheck.

Replace only `timeoutInterval = 2.0` with `setTimeoutInterval(2.0)` in private
`Fixture.control`. Mechanically rebase only the native-source pin in the combined
DNS/request guard and `OUTSIDE_HELPER_SHA256` in the callback guard. The async
helper identity remains `5b6123f2a968ccd06e4ca3ec2725a5c1e3666cd212a49a8aa28e3012fb73e6bd`.
All three forward/inverse fragments are byte-exact. **Both native methods, Worker,
NSURL response/error pointers, control protocol/ports/token/action/body bounds,
HTTP200/null-error requirements,10s/50ms waits and scope/host cleanup are unchanged.**
The DNS native source and Python listener fixture keep their original exact pins.

One genuinely new source-only guard first fails once on the old spelling, then
passes **4/4 new methods/0skips/0errors/0.004183s**, with27 unsafe variants refused.
That is four distinct methods/five executions total, not27 native tests. The new
guard restores the full old fixture and both old guard hashes when only these
three fragments are inverted, refusing native assertion/Worker/bounds/error/
cleanup changes, stale pins and guard weakening. Original synthetic XML/JSON and
held selected input maps are retained; XML is copied byte-exactly without adding
its absent terminal LF. The owning existing callback/DNS suites were **not rerun**.

The first passive reader refused an absent optional protobuf Package; that local
parser error and schema-correct empty-package recovery are retained separately.
It is not a Kotlin/source/native failure and did not trigger any build or SDK call.
The new source-only test results have not been replayed during packaging.

Gradle/Kotlin compiler/SDK/Apple/native/dispatch0. The optional tiny same-version
Foundation-only library probe is **prepared, not executed**, and is for lead-owned
finite orchestration only. No app/signing/simulator/network/native method is in it.
This is a narrow three-existing-file plus one-new-guard freeze, **not** a full
library or combined input map. The three actual request2/DNS1 methods remain
unaccepted; all issue, native, capacity, security, publishing and readiness gates
remain unchanged. No full native request replay is justified before the exact
compiler repair is integrated and genuinely compiled.
