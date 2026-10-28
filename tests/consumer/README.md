# Independent package consumer and release checks

This is **not a sample application or an included producer project**. It resolves
all 21 published nativeCmpkit module roots from an explicitly supplied **local
Maven repository**. It never uses `project(...)`, `includeBuild`, `mavenLocal`, a
producer source directory, or a remote fallback for the nativeCmpkit group.
Missing artifacts must fail. Third-party dependencies still come from Google,
Maven Central and the Gradle Plugin Portal.

**Status:** infrastructure under development. Tests added to this directory are
not execution evidence until the named command, revision and result are recorded
in [`docs/development/evidence/`](../../docs/development/evidence/).

## Scope

| Check | What it does | What it does not prove |
|---|---|---|
| `verify_artifacts.py` | POM/module identity, exact internal versions, target redirects, file hashes/sizes, safe archives, notices, no duplicate desktop classes, native byte/header/provenance contract | Correct runtime behavior, signing identity, legal clearance, release readiness |
| `verifyCandidateResolution` | Resolves selected classpaths to all 21 Maven roots; rejects original Calf/project substitutions | Any function was executed |
| `PublicApiConsumer.kt` | Compiles representative public Compose/Coil/core/IO/picker/camera/share/WebView and every modular permission API; retains exhaustive legacy sealed consumers | Rendering, permission prompts, launch/dismiss or all API/ABI compatibility |
| `PublishedCommonContractTest` | Eight executable packaged value/identity/default/API-linking tests | Native feature parity |
| `PublishedIoConsumerTest` | Six real filesystem/stream boundary, empty, Unicode, independent-concurrency and repeated-close tests | iOS security scope, Android providers, native save-dialog outcomes, exhaustive leak/sanitizer campaign |
| `PublishedNativeConsumerTest` | Three tests load real staged JNI libraries, initialize bridges, query native share capability and create/destroy 100 valid picker configurations | Displaying/cancelling a dialog, real AppKit sharing, stale/invalid handles, physical device behavior |
| `jvm_abi.py` | Public/protected JVM descriptors, class declarations and constants from actual JARs; reviewable before/after delta | Kotlin metadata/nullability/default/inline semantics, Swift ABI, Android/JS/Wasm/Native ABI |
| `binary_linkage.py` | Compiles a six-case Java fixture against source-bound baseline JARs; runs unchanged class bytes on baseline and staged artifacts, or explicitly separate receipt-bound local-JAR diagnostics | Complete Kotlin/default/inline/Compose or non-JVM ABI certification; two local candidates passed 6 cases / 31 assertions, but staged Maven execution remains pending |
| `collect_native_licenses.py` | Raw texts from checksum-verified public `.crate` archives; optional explicit reviewed pinned-VCS missing-text supplements retain exact origin/proofs | Signed authenticity, native functionality, or a legal determination that every obligation has been discharged |

There are **17 intended desktop test methods**, reusing the eight common methods
on other selected targets. Do not call 17 functions plus repeats on three targets
four independent libraries. Native test reflection intentionally crosses Kotlin
`internal` to verify retained JNI entry points from a real external artifact.
The test JVM has `-Xcheck:jni`, a task-owned empty `java.library.path`, and an
isolated user home; an installed old binary must not satisfy the test.

### Separate, deliberately partial Core/IO diagnostic

The [new standalone JVM fixture](io-desktop/README.md) selects only Core/IO
metadata+desktop and reuses all six IO methods **byte-identically**, plus one new
actual loaded-class JAR-origin/hash method. Finite `consumer-core-io` verification
stages four actual publications and copies that fixture independently; all seven
named methods/two fresh XML, four exact resolved classpaths and source/staging/
runtime bindings are mandatory. No project/composite/source/old-Calf/Maven-local
or remote candidate-group fallback is allowed. The full21-root build/settings
and17-method inventory above remain unchanged and unexecuted.

At [the contained2026-10-27 checkpoint](../../docs/development/checkpoint-consumer-uikit-20261027.md),
the adapter/Kotlin consumer remains uncompiled/unexecuted. Scoped201 Python
methods/actionlint and308 corrected static checks on older partial staging are
**not consumer execution or release evidence**. The partial controller bounds
its process group, not detached daemons or ordinary dependency trust. A future
partial pass does not replace the full native/KMP/ABI/legal/consumer gates.

The [2026-10-28 important Core/IO run](../../docs/development/evidence/consumer-core-io-important-20261028/README.md)
is now accepted **7/7 actual methods/two fresh XML** at immutable1ceb9d68,
run40666901460. Four actual metadata+desktop publications and four independent
classpaths, exact loaded staged-JAR origins/hashes,806 own-Git held inputs and376
partial static checks pass. This does not execute the full21-root/17-method/native
fixture or clear ABI/legal/security/dependency/release gates. No registry packages.

## Local candidate consumption

Schedule Gradle with the lead. First populate the **isolated verification Maven
repository** using the producer's local-only staging tasks. See the build-owner
procedure in [`docs/development/BUILD.md`](../../docs/development/BUILD.md); never replace this with a remote publish
or `publishToMavenLocal`. A local candidate can use `0.1.0-preview.1` without
stamping a release/tag or sending artifacts to a registry.

The coordinated producer contract is the following (**not yet executed as
consumer evidence**). It stages metadata + desktop only, with unsigned output
allowed solely in the isolated local repository:

```sh
./gradlew stageVerificationPublications \
  -PnativecmpkitVerification=true \
  -PnativecmpkitVerificationTargets=desktop \
  -PnativeCmpkit.version=0.1.0-preview.1 \
  --max-workers=2 --no-configuration-cache
```

`nativecmpkitVerificationTargets=all` requires suitable trusted producer hosts
and the full target/native assembly described by the build owner. No remote or
Central publication may bypass signing/verification using this local-only flag.

From the repository root, after successful staging:

```sh
./gradlew -p tests/consumer verifyCandidateResolution desktopTest \
  -PnativecmpkitRepository="$PWD/build/verification-repo" \
  -PnativecmpkitVersion=0.1.0-preview.1 \
  -PconsumerTargets=desktop --max-workers=2 --no-configuration-cache

python3 tests/consumer/verify_artifacts.py \
  --repository "$PWD/build/verification-repo" --version 0.1.0-preview.1 \
  --target desktop --native-platform linux-x64 \
  --output build/consumer-static-linux.json
```

The second command is a **partial Linux/desktop scope**, not a release pass. It
still checks every publication root. Omit target/native-platform filters for the
full static 21 × 7-coordinate / five-native-slot matrix, after all host artifacts
are assembled. Timestamped SNAPSHOT repositories are deliberately excluded from
the static release check; use an exact non-SNAPSHOT local candidate version.

Additional target selection (same repository/version arguments):

```sh
# Android compileSdk37/minSdk23 fixture plus Android-host common assertions.
./gradlew -p tests/consumer verifyCandidateResolution allTests \
  -PconsumerTargets=android <same-repository-and-version-properties>

# Real browser runners; provide an installed Chrome suitable for this host.
./gradlew -p tests/consumer jsBrowserTest wasmJsBrowserTest \
  -PconsumerTargets=web <same-repository-and-version-properties>

# macOS/Apple SDK required; device framework linking is not device execution.
./gradlew -p tests/consumer iosSimulatorArm64Test linkDebugFrameworkIosSimulatorArm64 \
  -PconsumerTargets=ios <same-repository-and-version-properties>
```

The angle-bracket placeholders above are explanatory, not executable shell
fragments. Task names must be checked against the configured AGP/KGP version;
`allTests` on the Android-only fixture must produce populated XML, not `NO-SOURCE`.
No sample application participates. An Android-host test is **not** an emulator
test; an API23 emulator/consumer APK and actual native mobile interactions remain
separate acceptance gates. Likewise common browser/iOS assertions do not test
picker/security-scope/UI integration by themselves.

Desktop JavaFX **21.0.13** and Skiko are consumer-selected runtime dependencies.
The fixture's explicit five-classifier mapping is part of the documented
[dependency migration](../../docs/development/compatibility.md), not a workaround
that conceals producer-host classifier metadata. The static check rejects that
producer-host defect independently.

## ABI snapshots

```sh
python3 tests/consumer/jvm_abi.py snapshot \
  --jar nativecmpkit-io-desktop=/absolute/candidate/nativecmpkit-io-desktop-0.1.0-preview.1.jar \
  --revision <full-source-commit> --provenance '<inspected-build-receipt>' \
  --output build/candidate-jvm-abi.json

python3 tests/consumer/jvm_abi.py compare \
  --before /absolute/source-bound-baseline.json --after build/candidate-jvm-abi.json \
  --output build/jvm-abi-delta.json
```

Supply every selected artifact using repeated `--jar`. An artifact omitted from
the candidate is a removal. New methods are retained in the delta; removing or
changing exported surface fails the command. Do not use a broad exclusion list
to erase compatibility changes. `javap` includes JVM-public Kotlin internals, so
class/member deltas need a reviewed public/internal classification in addition to
compiler-generated Kotlin ABI checks. Merely asserting a source SHA in this tool
does not prove the supplied binary was built from it: retain the actual source
cleanliness/build/input/output receipt.

The [separate old-binary fixture](binary/README.md) prevents recompilation against
the candidate from masquerading as binary compatibility. Its six Java cases /
31 assertions passed baseline sanity and **two real local-JAR candidate
diagnostics**, and are separate from the 17 unexecuted Kotlin Maven consumer
methods. The same six cases repeated are not 12 independent tests. Its
**staged-artifact mode** requires successful all-module
desktop static inspection; the separate explicitly labeled local-JAR diagnostic
mode does not clear artifact/distribution gates. Both keep exactly the same
third-party dependencies on the old/new runtime. See its README for the exact
source/receipt/JAR binding and limitations.

The [first actual raw delta](../../docs/development/evidence/jvm-diagnostic-20261024T223018Z/README.md)
failed with 19 removals and revealed a confirmed Java-source/reflection regression
for unpublished geo's `EarthRadius` field. The [second diagnostic](../../docs/development/evidence/jvm-diagnostic-20261024T224234Z-geo-repair/README.md)
verified its minimal repair using the original failing class bytes and separate
Java-source compilation. Its raw delta still exits1 with 18 individually reviewed
internal/generated/synchronization records; no whole-API claim follows. Both
diagnostics used receipt-bound dirty source snapshots, **not staged Maven
artifacts**, and preserved all original failures. The strict Maven build here
was not weakened or replaced with alternative source scaffolding.

## Rust dependency notice collection

After the native owner settles and fetches the exact lockfiles, export metadata
with `scripts/native/artifacts.py metadata --module calf-file-picker` (repeat for
share). This is locked/offline metadata, not a build. Then:

```sh
python3 tests/consumer/collect_native_licenses.py \
  --metadata build/native-metadata/calf-file-picker.json \
  --registry-cache /absolute/public-cargo-cache/registry/cache/<crates-io-index> \
  --output build/native-notices/calf-file-picker
```

Repeat for share. The output must be empty/new; no unrelated files are deleted.
The complete output directory is merged at the **root of that module's notices
ZIP**, not flattened. Missing archives/license text, altered checksums, links,
traversals and unreviewed sources fail; gaps remain in the report. Cache paths are
not exported. The collector reads bounded members without extracting tar archives
or executing their code. The report explicitly leaves legal review incomplete.
The exact sanitized metadata schema is validated **before any copying**; raw
Cargo fields (including manifest paths), unknown graph/package fields, filtered
target graphs and outside-package license paths are rejected. The static package
gate independently reconciles report, metadata, candidate Cargo hashes and every
locked registry package before checking the collected text bytes.

The [explicit pinned-VCS adapter](../../docs/development/native-license-supplements.md)
may be requested with `--vcs-supplements /absolute/reviewed/public/catalog`
(the source catalog is `licenses/native-dependency-supplements`). Default remains
archive-only. Only a validated missing-text gap may use this boundary; checksum,
declared-file, encoding, path/link and other errors never fall back. Every external
text and full crate/VCS/catalog proof is independently compared with reviewed
source bytes. Use canonical non-symlink public paths, not machine/private roots.
The fresh actual JNI supplement resolves one material identity only: both
collections still exit1 with15 shared objc2 gaps each, not legal clearance.
No incomplete output was installed into live `build/native-notices`.

The catalog is byte-bound public evidence: `.gitattributes` prevents newline
conversion. One exact author's Apache file retains its observed extra EOF LF
through a file-specific blank-at-EOF exception, not altered/rehashed text. Real
Git fixtures verify index/checkout bytes with `core.autocrlf=true` and retain
the other whitespace guards; this is not Windows runtime verification.

Accompanying ZIPs use `META-INF/nativecmpkit/{LICENSE,NOTICE,...}`. Embedded
JAR/AAR copies use `META-INF/nativecmpkit/<retained-project-name>/{LICENSE,NOTICE,...}`
to avoid introducing duplicate legal resource paths when several libraries are
packaged together. Native dependency texts are already scoped by owning module.

The [first actual locked collection](../../docs/development/evidence/native-license-material-20261024T193225Z/README.md)
is **blocked**, with preserved corrected text bytes and complete observations:
16 archive-text gaps per native module; pinned JNI supplemental material available
for one; 15 objc2-family material gaps and an upstream SDK/licensing ambiguity
remain. There is no live notice installation or legal clearance. The command
above describes the eventual installation location, **not authorization to copy
an incomplete collection there**. Further attempts must use new staged output
paths and retain their original failures.

## Tooling regressions

```sh
python3 -m unittest discover -s tests/consumer -p 'test_*.py' -v
```

These are adversarial **gate-tooling** fixtures, not Kotlin/native tests. They
exercise missing/tampered artifacts, classifier regressions, unsafe archive paths,
DTD/entities, checksum and notice loss, native object headers and JVM API deltas.
Fixture JAR/ELF/PE contents are synthetic; their successful inspection never
counts as successful consumer or native behavior.
