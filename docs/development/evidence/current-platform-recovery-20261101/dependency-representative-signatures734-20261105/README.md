# Representative dependency signatures — verified, not admitted

Three exact public POM/signature pairs passed isolated GPG verification once on
2026-11-05: Compose plugin 1.12.0, Kotlin plugin 2.4.20 and JUnit 4.13.2. Full
primary/signing fingerprints, signature digests and parsed coordinates match.
Compose/Kotlin use SHA-512; JUnit uses SHA-256. All report `TRUST_UNDEFINED`.

`public-verification.json` preserves the complete named signature status lines,
source/signature hashes, publisher anchors, exact JUnit tag-to-KEYS metadata
binding, command-result hashes and owned-process cleanup. The lead passively
checked the original three status streams against their stored hashes; no GPG,
network or accepted Windows/native test was replayed. Only validated public
metadata is archived here, not original response bodies, keyrings or binaries.

The initial GPG import attempt exited2 because its owned socket pathname was too
long. Its partial Compose import and original receipt remain preserved. Recovery
used a shorter isolated home and copied only the known public keybox, without
reimporting Compose, copying private/global trust state or starting key agents.
Eight owned GPG children were waited; zero remain and zero sockets remain.

## Authority and remaining gates

- Compose/Kotlin keyserver bytes are **not** independent authority. Their exact
  full-primary anchors come from separately pinned publisher security documents.
- JUnit's publisher-owned KEYS blob is present in exact `r4.13.2` source metadata.
  The tag is unsigned; this is metadata binding, not signed-tag verification.
- Three mathematical descriptor signatures do not verify JARs, module metadata,
  native binaries, plugin bootstrap, the transitive graph, reproducible builds,
  compromise/revocation freshness, or ordinary Gradle policy enforcement.
- Google Linux signing-key identity does not establish AGP artifact namespace
  authorization. Material3, Coroutines, OpenJFX and Vanniktech gaps remain.
- All normal120 refusals remain:18HTTP303 +44HTTP404. Same-registry checksums
  remain integrity-only observations. No automatic retrieval, ownertrust or
  admission-map promotion occurred; `REVIEWED_EXPECTATIONS_SHA256` stays null.

**#40 and #64 remain open.** No Gradle/native/consumer acceptance, package, release,
deployment or release-readiness claim is established. Continue bounded publisher
research, complete two-root dependency closure and real negative-policy enforcement
before the ordinary consumer. Do not replay accepted private Windows Stop tests.
