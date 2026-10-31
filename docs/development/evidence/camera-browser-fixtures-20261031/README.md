# Important camera/browser compilation — one bounded invocation

On dirty61003963 plus the reviewed test/tooling corrections, JDK17/Rust1.98.0/
Android37.0 identities are captured. All994 library/1071 combined input hashes
remain held. One serial, no-daemon/no-parallel, max-workers2/in-process2GiB build
with8GiB disk reserve executes:

```
:calf-camera-picker:assembleAndroidDeviceTest
:calf-webview:compileTestKotlinJs
:calf-webview:compileTestKotlinWasmJs
```

**Exit0/58.01s. Zero native/browser/library test executions.** Normal NO-SOURCE,
SKIPPED and UP-TO-DATE auxiliary tasks are not test passes. `compile002/` preserves
command/log/runtime/before/after/review. Unchanged camera receiver compilation is
not rerun; its separate prior compilation evidence still needs applicability review.

`preflight-failure001/` preserves the first invocation stopping before Gradle at
missing `rustc` on PATH. Its original terminal traceback was not saved; a separate
bounded reproduction confirms the missing executable. The existing installed
Cargo bin and JDK17 are selected only for the new invocation; default system JDK21
or production policy is not changed. The first request directory is not rerun.

Compilation enables finite immutable native/browser requests; it does not close
#13/#63, prove physical/minimum/native memory/consumer/API-ABI behavior or certify
ordinary dependencies, legal/security/release readiness. No publishing/deploy/Pages.
