<!-- nativecmpkit-resolution:UI-037:focused-verified-subset:20261030:81ff78b5 -->
## Verified resolution — focused shared batch, verified subset only

1. Nine exact unchanged real UIImageConversionTest methods from immutable40522929974 attempt2 verify primary/transparent/half-alpha channels and compositing over black and white with explicit premultiplied sRGB RGBA; the CoreGraphics context owns a pinned-copy destination, not a borrowed Kotlin buffer.

2. Two exact unchanged accepted methods from40994702874 exercise a real1MP image and4MiB context, GC Worker gated at the real snapshot boundary with3 collections/6MiB pressure, five more collections after source closure, actual sRGB/scale/dimensions/pixels, and80 real failure/success conversions with exact allocation/release balancing. This is native runtime evidence, not synthetic counters alone.

3. On actual iOS26.5/Xcode26.6,41002405707 executes the owned native workload successfully under observed MallocScribble/MallocGuardEdges/MallocErrorAbort/MallocStackLogging requests:369 bounded rounds/738 real conversions, with fresh XML/distinct Worker/PID/binary/install/owned cleanup. Apple ASan is unsupported by the configured Kotlin compiler; no ASan/all-allocator-check attestation is claimed. The actual Instruments attach attempt exits21, no allocation rows or leaks command: profiling remains UNVERIFIED and UI-038/#141 stays open. This accepts the available native-diagnostic stress scope, not the separate mandatory allocation/leak profile.

Fresh native workload: immutable `de6c161800fd027c99d0682484d588c0ba95fb4b`, [run41002405707](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41002405707), **1/1**, one fresh XML, Gradle exit0/1484.68s, all903 before/after exact Git inputs; two accepted stress and nine accepted UIImage cases reused, not replayed (**1fresh+11reused=12 accepted executions**, not12 new methods). Signed binary/plist/native-console/readiness/launch PID agree; private ack/readiness/tree/app cleanup verified. Green native testcase is **not** a green Instruments profile.

Limitations and still-open related work:
- No ASan or every allocator option attestation; strict40989310808 remains FAILED/zero tests, not repaired or waived.
- Actual Instruments recording exits21: zero useful allocation rows/zero leaks invocations, no zero-leak assertion. UI-038/#141 stays open and remains a release gate.
- Real current iOS simulator/native UIKit/CoreGraphics/GC scope, not physical/minimum-platform, general heap/ABI/consumer/security/release certification.

Original technical body, labels, attribution and history remain unchanged. Readback and exact acceptance receipts are archived afterward under `docs/development/evidence/verified-webview-image-subsets-important-20261030/`. No packages/releases/deployments/Pages or main/history changes.
