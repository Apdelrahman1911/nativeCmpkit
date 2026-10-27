# Explicitly partial Core/IO desktop Maven consumer

This standalone JVM fixture resolves **only** `nativecmpkit-core` and
`nativecmpkit-io` from a supplied local Maven repository, through their actual
published KMP root metadata/desktop variants. It has no producer project,
composite, source, old-Calf, `mavenLocal` or candidate-group remote fallback.
Every selected compile/runtime/test classpath must resolve both roots and match
the exact staged artifact bytes. Missing coordinates fail.

The six filesystem/stream scenarios are byte-identical to
`../src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt`.
They exercise both empty-read overloads, byte boundaries/large streams, 16
independent concurrent sources, directory/missing-file semantics, Unicode names
and 64 repeated stream closes. They are **not six newly invented scenarios**
in addition to the full consumer's existing functions. No mock/native stub or
sample application participates. Tests always execute and empty/missing matching
suites fail. Reports record exact candidate bytes and explicit incomplete scope.

A seventh, new `PublishedArtifactOriginTest` method checks the **actual loaded**
Core/IO class protection-domain locations, exact desktop JAR filenames and SHA256
against task-provided, byte-verified staged artifacts. A class directory or old
artifact must not satisfy that assertion. All seven methods must execute with
zero skips; the six existing IO scenarios remain unchanged.

From an independently copied fixture directory, using installed Gradle9.7.1:

```sh
gradle --no-daemon --no-parallel --no-configuration-cache --max-workers=2 \
  verifyCandidateResolution test \
  -PnativecmpkitRepository=/absolute/isolated/candidate-maven-repository \
  -PnativecmpkitVersion=0.1.0-preview.1
```

The exact draft version is local/unpublished; this is not a registry consumer.
The main `../build.gradle.kts` **still requires all21 roots** and remains the
full-matrix gate. This two-root desktop diagnostic does not certify the missing
roots, KMP metadata/common consumption, Android/Apple/browser/native behavior,
minimum-platform compatibility, ABI, complete dependency/legal provenance or
release readiness. A successful Gradle build alone is not executed test evidence:
inspect fresh XML, all seven named outcomes, resolved-byte receipts and source/
staging bindings. Record failures instead of weakening the main consumer.

The finite `consumer-core-io` profile in `.github/workflows/gradle.yml` runs
`scripts/ci/core_io_consumer.py` at a clean immutable checkout. Its explicit
init adapter selects four real local publication tasks, preserves the producer's
publishing interlocks, copies this fixture independently and uploads JSON/XML
only. The controller owns a bounded process group, **not detached Gradle daemons
or ordinary dependency trust**. At the2026-10-27 tooling checkpoint, the actual
adapter/Kotlin staging/consumer remains unexecuted; Python/synthetic/static
checks are not a seven-method library pass or a release gate.
