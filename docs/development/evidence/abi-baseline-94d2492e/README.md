# Source-bound pre-development JVM baseline

**Completed producer compilation and API capture, not compatibility approval.**
The isolated detached worktree was exactly
`94d2492e99d5cbc060409d94d9f88febd06222d5`, the upstream synchronization commit
before production fixes. Tracked files were clean before/after the build and
after API capture. The candidate worktree's concurrent development was not used.

## Inspected results

- The bounded build started at `2026-10-24T18:54:08.472788Z`, exited **0** after
  **244.69 seconds**, and reported **151 tasks executed** with `--rerun-tasks`.
- **23 desktop JARs** were rebuilt: every one of the **21 published** modules,
  plus unpublished navigation and geo. Maps has no library API/output to include.
  No sample, publication or test tasks were requested; **zero tests executed**.
- JDK `javap` capture exited **0**, inspected **331 classes**, and retained
  **295 JVM-public/protected class surfaces / 9,961 member records**. The published
  subset is 296 inspected / 262 exported classes / 9,653 member records. The
  permission aggregator has zero classes, explicitly recorded rather than
  mistaken for a missing artifact.
- Every snapshot JAR digest/size was independently compared with
  `jar-inventory.json` and the actual fresh output after capture.
- The 369 selected production Kotlin/Rust/cinterop/font/MIME source blobs are
  identical between the original `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`
  audit baseline and `94d2492e`. This comparison **excludes build/Gradle/identity
  edits and tests**; it does not claim original published binary equivalence.

## Evidence

| File | Meaning |
|---|---|
| `plan.json` | Original pre-execution plan; its historical prepared status is not overwritten |
| `invocation.json` | Exact source/tree, tracked cleanliness, build arguments, tool versions and safe environment-override names |
| `gradle.log`, `gradle.log.result.json` | Observed command output and bounded-run exit/time/disk-reserve receipt |
| `jar-inventory.json` | All rebuilt JAR identities, relative paths, sizes and SHA256 digests |
| `source-boundary.json` | Exact 369 selected paths/Git blobs and source-comparison boundary |
| `cargo-resolution.json`, `*-generated-Cargo.lock` | Offline resolved native dependency graphs; **not originally tracked locks** |
| `abi-invocation.json` | Exact JDK invocation and capture-tool hashes |
| `tools/` | Copies of the two gate scripts whose bytes match that invocation; preserved only as evidence |
| `jvm-api.json` | Complete inspected JVM exported surface, per-JAR digests and explicit zero-class aggregation |
| `result.json`, `SHA256SUMS` | Independently checked scope/count/result ledger and evidence byte checksums |

Build inputs were JDK17.0.20, Gradle9.7.1, Kotlin2.4.20, Cargo/Rust1.98.0, with
two Gradle/Cargo workers, in-process Kotlin, no configuration cache or parallel
Gradle execution, 1,800-second cap and 4,096MiB disk reserve. The **original**
native manifests used semver ranges and ignored Cargo.lock; generated lockfiles
were copied before any cleanup. They record the observed cached/offline
resolution honestly, not a retrospectively pinned historical baseline.

Warnings are retained, including expect/actual Beta notices, the upstream sheet
deprecations, nullable navigation warning, and native unused imports/constants.
The source was not changed to silence them. Old build logic did not provide a
fully reproducible dependency/artifact scheme; a later rebuild is not promised
to reproduce all these byte hashes. The actual JARs currently remain in
`/tmp/nativecmpkit-release-baseline-94d2492e`, not in Git or a package registry.

## Remaining compatibility gates

The snapshot deliberately includes JVM-public Kotlin internal/generated members.
Before/after deltas need public/internal classification, compiler ABI checks and
reviewed intentional changes—not blanket exclusions. No candidate comparison,
old-binary/new-artifact execution, Kotlin metadata/inline/default-argument
semantics, Android public surface, JS/Wasm/KLIB/Swift compatibility, native GUI,
device or memory-sanitizer behavior was certified here. No artifact was published.

Use `tests/consumer/jvm_abi.py compare` against a separately source-bound candidate
snapshot; match all 23 artifact keys or explicitly preserve a reviewed narrower
scope. A same-source comparison or successful `javap` invocation is not evidence
that a later implementation remains compatible.
