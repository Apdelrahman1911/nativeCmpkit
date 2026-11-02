# Hosted249: Share accepted; Windows Stop still fails

The **solo source/results review257** accepts the bounded results below. The
original logs and artifacts were acquired once, retained privately and reused;
no original was downloaded again and no accepted test population was replayed.
[The review receipt](hosted-review257.json) records **47 passive checks**, not
47 library tests. Both actual **1,203-file** before/after maps match the exact
`c21a4c59d46aa1ef935e80af88227626c8a54e37` Git blobs and current source files.
The **1,281-file canonical combined map is predispatch provenance only**, not
an actual runtime attestation. The first reviewer's raw-JSON versus canonical
file-map digest mistake is retained in [its refusal](first-reviewer-refusal257.json).

## Genuine iOS Share: one method passes

[Run41398699513](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41398699513)
is **SUCCESS:1/1**, one fresh original XML, Gradle exit0/1,067.15s. The application
protocol independently records9.44s, main Worker1/owned Worker2, runner exit0 and
Worker termination; transport9.46s and owned application cleanup also qualify.
The XML testcase0.272s is a buffered-report clock, not full native elapsed time.
[Original summary256](share-original256.json) binds runtime, native executable,
signed/installed bytes and simulator identity: iPhone Air/iOS26.5, Arm64 macOS,
Xcode26.6.

`IosSharePresentationOwnershipTest.publicRememberedShareMainDefaultIoReentryAndDisposalUseCurrentCallbacks`
executes the four new **expressly controlled Request barrier scenarios inside
one JUnit method**, followed by the real remembered-public Main/Default/IO,
current-callback, reentry and composition-disposal assertions. Production must
acknowledge genuine UIKit presentation/dismissal before releasing ownership and
delivering the pending result. The first `Completed` activity inputs are deliberate
fixture inputs, **not evidence of successful sharing to an OS recipient**.
The twelve accepted Share188 methods remain reusable, not newly executed here.

This completes the missing bounded Share lifecycle method, **not all original
criteria of #81/#88**, nor the saver/sample criteria of #48/#100. Main Thread
Checker, successful security-scope balancing, delayed/cross-process recipients,
macOS/Android sharing stages, full native concurrency and physical/minimum/iPad
coverage remain independent work. No public ABI/consumer/security/release gate
is inferred.

## Genuine Windows Stop: one method fails

[Run41398651975](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41398651975)
is **FAILURE:0/1**, one fresh original XML, Gradle exit1/293.78s.
[Original summary255](windows-original255.json) preserves the actual refusal:

```text
worker=CANCELLED; running=false; finished=true; cancellations=1;
peerEofs=0; pending=1; arrivals=1; responses=0; closing=false
```

The original six predicates and10s deadline remain. The native Worker cancelled
and the library reported Finished, but the peer did not observe EOF before any
response. The recovery tail was **not reached**. These are sequential last-poll
values, not an atomic or historical snapshot. After-timeout zero matching frames
do not establish an absent loader, its historical route or the root cause.
The owned AWT/FX cleanup waiting is bounded; blocked native code is not preempted.
Keep #64 open; do not inject EOF, tear down the fixture to manufacture success,
disable a private JavaFX route property or retry the unchanged case blindly.

## Dependency investigation258–260

[Analysis](dependency-analysis.md) separates the source-confirmed JavaFX internal
loader cancellation defect from the unobserved historical Windows instance.
[Diagnostic receipts](javafx-diagnostics258-260.json) retain failed258/259 and
the corrected260 tail. The actual260 program exits0 and observes natural peer
EOF1, with no response bytes or prior server cleanup, after cancelling the stored
response future. This is **direct internal JavaFX/JDK loopback evidence on
Linux/Xvfb**, not a NativeCmpKit public Stop fix or Windows acceptance. No cached
JAR, dependency declaration, production code or private routing property changed.

No issue closes in this checkpoint: the last verified state remains **97 closed /
75 open /172 total**. Work remains solo; serial local heavy builds/8GiB reserve,
max2 combined hosted-heavy reservations including queued work, read-only Actions
without mandatory SHA pinning, history/main preservation and every publishing/
Pages/native/consumer/API-ABI/dependency/legal/security/readiness gate remain.

