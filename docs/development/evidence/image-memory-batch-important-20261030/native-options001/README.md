# Configured Kotlin/Native diagnostics: precise source observation

[Read-only bytecode review](review.json) uses the actual cached **Linux-host**
2.4.20 compiler JAR and records JAR/class hashes. **Zero compiler builds, Apple
executions or sanitizer experiments.** The ADDRESS enum/configuration exists.
The actual second-stage configuration issues a **strong warning and disables**
non-THREAD sanitizer settings (unsupported branch returns null). It also disables
THREAD on targets not in the supported list. The inspected target function lists
Linux-x64 and macOS-x64/Arm64; iOS Arm64/simulator take its empty-list branch.

Do not report an unavailable enum, a compiler failure, an actual Apple ASan run,
or universal sanitizer unavailability across other compilers/versions. A successful
compile could silently lack the requested sanitizer. The new isolated native
memory focus requests runtime panic/external-call checks and observes Darwin
heap diagnostic requests in the actual app. Those are not ASan or an attestation
that every allocator/checker ran. Actual native tests and an independently useful
Instruments/leaks profile still require their own reviewed results.
