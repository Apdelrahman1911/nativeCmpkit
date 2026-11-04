# Batch606 — native package provenance and loaded consumer origin

**2026-11-04; base `f566078507bbfc000244561ed925565913c3342b`.**
Related findings: **#2 / BUILD-003**, **#38 / BUILD-004**, supporting
**#3 / BUILD-006**. This is a related consumer-verification patch, not a native
production fix, full packaged-consumer pass, release approval or issue closure.
It was developed on `development/batch-native-consumer-20261104` in an isolated
worktree. The lead owns integration, hosted dispatch, review and issue updates.

## Confirmed boundaries repaired

| Location in this batch | Previous cause and impact | Implemented correction |
|---|---|---|
| `tests/consumer/verify_artifacts.py:326–361,509–523` | A manifest's revision only had to resemble a full SHA. A self-consistent stale or mixed-revision package could satisfy that check, and a recorded dirty producer did not fail the default gate. | Require an independently supplied expected revision for native desktop requests and exact equality in every inspected native manifest. Require a recorded clean producer by default. Explicit dirty diagnostics must select fewer than all five native slots and remain visible in receipts. |
| `tests/consumer/verify_artifacts.py:669–685` | Payload isolation did not equally constrain provenance-only entries. A foreign/unclaimed manifest could silently enter an owning desktop JAR; a nonnative desktop JAR could conceal a native manifest. | Restrict manifests to the owning native module and intended slots; reject native payloads **or** manifests in nonowning desktop JARs. |
| `tests/consumer/build.gradle.kts:211–230`; `PublishedNativeConsumerTest.kt:15–61` | Merely finding a `.jar` bridge and a `jar:` native resource did not show that either came from the independently staged candidate or from the same owning JAR. | Select exactly one picker/share desktop runtime artifact by candidate group/module/version, bind resolved bytes to staged Maven bytes, require actual Test classpath membership and pass its name/hash into the test. Before bridge initialization, require a regular loaded JAR of that name/hash and its same-owning-JAR native resource. |

The provenance corrections are **consistency checks, not trusted-builder or
actual-cleanliness attestation**. A dishonest manifest author can still lie
about cleanliness; independent source/run/input/output review remains mandatory.
Origin qualification still needs actual Gradle resolution and JNI execution.
It does not prove which binary a production loader ultimately initializes or
fix the separate share loader/system-library preference under another patch.

Hashing uses a closed input stream and a 64 KiB buffer, not an allocation of the
entire JAR. The resource connection is not opened/read as a JarFile, and caching
is disabled. The original three native test methods, all native actions,
assertions, 100 valid handles and `finally` disposal remain; only their helper's
owning-module argument was added. No public library API, Rust source, native
artifact producer, dependency, workflow, licensing or publishing policy changed.

## Accepted important verification — do not replay unchanged

| Retained first execution | Accepted result | Exact scope |
|---|---|---|
| `important-first606.json/.txt` | **17/17**, unittest **0.049 s**, wrapper **0.231525 s** | NEW15 synthetic ZIP/manifest controls + two affected existing native fixtures; three owning inputs held before/after. No Cargo, Gradle, compiled native payload or JNI. |
| `origin-first606.json/.txt` | **6/6**, unittest **0.001 s**, wrapper **0.073563 s** | NEW6 source-wiring controls; three owning inputs held. These inspect source text, not Gradle configuration or JVM behavior. |
| `compiler-first606.json`, `compiler-inputs606.json` | **exit 0 / 4.683248 s**, empty stdout/stderr | Genuine direct Kotlin **2.4.20** K2JVMCompiler / JDK **17.0.20** compilation of the exact changed reflective Kotlin test. **129** bound inputs, including **115** existing real picker/share classes, held before/after. No stubs, Gradle, candidate publication or test execution. |
| `REVIEW606.json` | **47 passive checks accepted** | Review of original fixture assertions, native bodies, one additive Gradle insertion, result/input/output hashes, 17 protected nonowned paths and whitespace. No accepted test/compiler replay. |

The new controls cover independent-revision absence/format, rehashed stale and
mixed revisions, five intended slots in both native modules, default dirty
refusal, truthful partial dirty mode/full-matrix refusal, missing slot, invalid
Boolean dirtiness, foreign/unclaimed/nonnative manifests, staged runtime binding,
pre-initialization checking, stream ownership, same owning resource and preserved
serial/JNI-check/handle-disposal behavior. Synthetic headers are **not** executable
ELF/Mach-O/PE binaries, and synthetic legal fixtures are not legal material.

**23 source/fixture controls; zero native methods executed.** Reflection means
the successful compiler does not check bridge method-name/signature strings.
The Gradle script is hash-bound in the compile inventory but was **not compiled**
by that command. The build slot was lead-granted, used serially with >8 GiB free,
and released after compilation. Class outputs remain ignored local build files;
only their hashes/sizes are committed, not binaries or native payloads.

Original private receipts, both compiler maps, logs and reviewer script remain
retained once. `retained-originals606.json` records their hashes. The committed
compiler command/map use `<worktree>`, `<producer>` and `<gradle-cache>` labels
instead of private absolute roots; identities and hashes are unchanged.
`source-inputs606.json` binds the seven owned source/doc paths at review time.

## How the caller must supply provenance

Use `--expected-native-revision FULL_SHA` from an independently reviewed producer
source/run/input receipt, **never from the candidate's manifest**. Nonnative
partial Core/IO and WebView controllers need no new option and are unchanged.
Existing synthetic native fixtures explicitly opt into a partial dirty diagnostic.

`--allow-dirty-native-diagnostic` is only an expressly authorized local,
partial-slot diagnostic. A full five-slot request refuses the flag even if a
manifest claims to be clean. Never forward that option to release verification
or treat its static receipt as a clean producer, native pass or trusted builder.
The added verifier arguments are keyword-only; omitting the revision now
intentionally fails native desktop requests. This is tooling tightening, not a
public Kotlin API break.

## Exact issue closure remains conditional

The retained original bodies/criteria are in
[`release-consumer-triage040/original-criteria-readback.json`](../release-consumer-triage040/original-criteria-readback.json).
Their historical state snapshot is not a fresh GitHub observation.

| Finding | Evidence this patch adds | Still required before closure |
|---|---|---|
| #2 / BUILD-003 | Stronger packaged revision/clean-producer/isolation controls. Existing malformed-directory controls remain retained, not replayed. | Verify real complete artifact manifests **before** candidate desktop JAR assembly; load each candidate binary and check JNI symbols on its intended host. Synthetic manifests and a reflective compiler cannot substitute. |
| #38 / BUILD-004 | Independent five-slot/two-module synthetic matrix, missing-slot and unclaimed Windows ARM64 refusal. | Real packaged required paths, Linux ARM64 JNI/dialog cancellation and verified glibc/SDK minimum compatibility. Windows ARM64 and musl remain unclaimed. Do not invent or reduce support minima for green checks. |
| #3 / BUILD-006 | Prepared exact loaded picker/share origin binding. | Actual nonzero per-module platform regressions, full 21-root / seven-coordinate candidate and isolated minimum-SDK/Kotlin/Compose consumers; retained Kotlin/JNI/Swift API–ABI comparison and real resource/native behavior. |

[`missing-host-plan606.json`](missing-host-plan606.json) is a finite, conditional
plan, not a dispatch or completion claim. Real native legal/notice/material,
clean producer, input/output and package provenance gates must pass first.
No staged repository is overwritten/deleted and no guard is disabled to stage
artifacts. The five-host bundle assembly/handoff and full native consumer driver
do not currently exist; reports-only workflows cannot silently transport
candidate/native binaries.

Existing `all` native verification has three heavy host rows and
`native-lock-reproducibility` has five; `max-parallel: 2` does not reduce the
**INCLUDING queued/reserved** count to two. Prepare single-host routes under
lead coordination rather than dispatch either wholesale. Only the lead may
dispatch, after freezing/integrating reviewed sources and checking fresh capacity.

`calf-file-picker/native/build-all-targets.sh:24,35,61` is still an old helper:
it writes source resources, invokes unlocked Cargo and omits Linux ARM64. It is
unchanged here; deprecate or replace it with the canonical verified build-dir
producer as a separate related patch, never use it as candidate provenance.

No issue was created/closed; no workflow was dispatched; no package, release,
deployment or Pages publication occurred. This batch alone proposes **no issue
closure** and does not certify release readiness.
