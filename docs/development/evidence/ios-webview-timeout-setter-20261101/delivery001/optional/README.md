# Optional same-version Foundation-only library probe — NOT EXECUTED

For the lead only, after serial/capacity and exact owned-command preflight.
Copy the included probe into a new lead-owned private directory. Supply the
**existing, positively identified Kotlin/Native2.4.20 installation** and that
private directory explicitly; do not guess a home/session, change target, fetch
tools/dependencies, or select a fallback. Refuse if prerequisites are absent.

The lead must use its established bounded/owned process harness. A suggested
work budget is120s; it is not an instruction to weaken ownership/cleanup or to
use an unbounded shell invocation. The one compiler argv, after checking the
Foundation manifest contains exact `compiler_version=2.4.20` and
`native_targets=ios_simulator_arm64`, is:

```sh
"$KONAN_HOME/bin/konanc" \
  "$PRIVATE_PROBE_DIR/FoundationTimeoutSetterSignatureProbe.kt" \
  -target ios_simulator_arm64 \
  -produce library \
  -library "$KONAN_HOME/klib/platform/ios_simulator_arm64/org.jetbrains.kotlin.native.platform.Foundation" \
  -o "$PRIVATE_PROBE_DIR/timeout-setter-probe"
```

The output path must be absent initially. Do not invoke `-run`, Gradle, linking
of an application, signing, simctl, SDK discovery or a full native request.
Record any target/dependency/tool refusal rather than downloading or rerouting.
If a library-only compile is unsupported or exceeds the lead's finite work
budget, preserve that failure; the passive declaration evidence is not a pass.
A successful tiny probe would prove this spelling/import/type in that toolchain,
not the full fixture, actual WK/DNS/TLS/Worker/control lifecycle, SDK identity,
application launch, native methods or issue acceptance.
