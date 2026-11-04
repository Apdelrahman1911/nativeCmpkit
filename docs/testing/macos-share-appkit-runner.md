# Fixed macOS AppKit lifecycle controller

This procedure adds safe first-execution custody for the **eight new native
cases** in [macOS share lifecycle](macos-share-lifecycle.md). It does not replace
their original issue closure requirements, the separate three Kotlin/JNI methods,
or any release/security/consumer gate. See [source/control evidence](../development/evidence/current-platform-recovery-20261101/macos-share-appkit-runner-20261104/README.md).

## Exact interface

On a reviewed, immutable, clean **macOS arm64 graphical host**, serially:

```sh
NATIVECMPKIT_NATIVE_UI_TESTS=true \
  python3 scripts/ci/macos_share_appkit_lifecycle.py \
  --output build/ci-verification/desktop-macos-arm64-appkit
```

The output must not exist. The only other mode is read-only `--plan`; a plan
does not inspect/admit the host and is never native verification. There is no
case, target, profile, toolchain, arbitrary command or publication selector.
The lead integrates/dispatches/reviews; agents do not mutate GitHub or publish.
Reserve hosted-heavy capacity including queued work and at least **8 GiB free
disk**. The controller monitors that reserve; it is not a filesystem sandbox.

## Build and execution custody

1. Exclusively create the output and checkout-local lock. Preserve every existing
   native report directory/file; reject aliases, symlinks and unsafe output paths.
2. Capture complete library/native inventories and clean full Git revision.
   Qualify the exact unchanged feature-gated harness bytes, including its separate
   failed-control assertion. Production Rust/Kotlin/JNI/API bodies are unchanged.
3. Require exact native GUI opt-in, real macOS arm64, Rust/Cargo **1.98.0** and
   `aarch64-apple-darwin` compiler host. Capture compiler/Cargo commits, effective
   Rustup/rustc/Cargo/Clang executable hashes, Xcode/SDK and macOS version/build.
   The bounded `launchctl print gui/<uid>` readiness probe discards **all** payload;
   exit zero does not prove visible presentation. Refuse custom native/compiler
   injection and ambient Cargo configuration rather than silently trusting it.
4. Build once with pinned `rustup run 1.98.0 cargo test --locked`, only the
   `appkit-lifecycle-tests` feature and `appkit_lifecycle` target, `--no-run`, Cargo
   JSON, explicit Apple target and a **fresh exclusively owned target directory**.
   The compilation budget is 1,200 seconds, two Cargo workers. No task outputs or
   previous test reports are restored; dependency cache provenance remains a
   separate supply-chain gate.
5. Require one fresh Cargo executable artifact, exact local package/manifest/
   source/feature/debug-test origin, successful terminal event and ordinary
   unaliased executable under that target's `debug/deps`. Verify single-arm64
   Mach-O **MH_EXECUTE**, not merely a Mach-O library, and hash its actual bytes.
6. Recheck source, revision, runtime/toolchain, executable and report baseline
   before launching that **exact artifact directly, with no arguments**. The
   default eight run once; `stress_2048`, old Rust suites and accepted tests are
   not selected. Native budget: 240 seconds. Each native case independently
   performs production-owned Main/registry/delegate/completion cleanup; it stops
   after the first failed/unknown native ownership state.
7. The external controller owns only its `start_new_session` process group.
   Timeout/disk/output refusal sends TERM, escalates to KILL when necessary and
   bounds the leader reap. A zero leader exit with surviving descendants is
   cleaned but remains **red**. Cleanup errors are retained independently of the
   primary compiler/native/context failure.
8. Bind the actual launched PID to a previously absent
   `share-appkit-native/process-<pid>` directory. Require exactly eight distinct,
   unsuffixed native XML cases and exact ordered console markers, zero live /
   registry observations and successful cleanup in both. No skipped/failed/missing
   or foreign population is accepted. A two-second filesystem/wall-clock envelope
   matches the library runner; **time alone never admits freshness** without the
   exclusive artifact/PID origins and complete identity/baseline custody.
9. Capture final complete library/native inputs, Git, toolchain/runtime, executable
   and native report inventories even on failures. All must match. Preserve
   compiler/native exit, process cleanup, diagnostics and reached red XML;
   unreached cases are missing, never passes.

## Artifacts and witness limits

Upload only the output's top-level sanitized `*.json` and
`fresh-reports/TEST-*.xml`. Exact **reached** original XML bytes are copied
exclusively after identity/checksum/freshness capture, including valid failed XML.
PID collisions never copy or delete baseline reports. Unknown files are preserved,
refused and not included in the XML artifact whitelist. Original compiler/native
logs, Cargo JSON path payloads, compiled executables and target outputs stay
private; receipts contain their checksums, sizes and repository-relative roles,
not raw path/environment/launchctl bodies.

`CONTROL_FAILED` is an actual independent native assertion gate, bound to the
unchanged compiled source. It is **not separately exported or independently read
by this controller**. Receipts explicitly retain both false export/observation
fields. Console/XML/zero-count/cleanup agreement is directly observed; weak-owner
release remains a source-qualified native assertion, not an invented external
counter. Controlled native callbacks do not prove service/recipient delivery,
Mail subject use or visible picker presentation.

The lead's `macos-share-lifecycle` profile runs this native component serially
before the independent `macos-share-coroutine-lifecycle` three-method library
focus on the same fixed macOS-arm64 host. The library component runs even if this
component fails, while the overall job remains red on either failure. The lead
must bind the actual **owning workflow/source Git** to each dispatched run; this
agent's old branch is not the subsequently integrated workflow's source map.

## What has and has not been verified

Local qualification is **source/mock/file-custody only**: 32 unique new Python
controls, with five original clock-admission failures preserved and only failed
five plus affected three recovered; one read-only CLI plan. **Zero local Cargo
build/link, AppKit/native execution, JNI/Kotlin test execution, GUI observation,
stress, Instruments/leaks, ASan or service delivery** occurred for this controller
assignment. Prior batch604 cross-target Rust checking and Desktop compilation
remain prior results, not fresh executions here.

#84, #85 and #150 remain open pending their real native, visible, instrumentation,
stress and service-platform criteria. A prepared controller, source pass or even
the finite native eight alone does not close those whole findings or authorize a
release/package/deployment/Pages publication.
