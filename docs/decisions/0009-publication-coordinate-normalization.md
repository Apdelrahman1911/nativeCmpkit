# ADR0009 — Independent fallback coordinates at metadata generation

**Status:** accepted for contained verification, 2026-10-28. Distribution,
cross-host consumers and release gates are not waived.

## Context

Public Calf packages, Gradle project paths, resource/JNI/framework names remain
compatible; Maven coordinates use NativeCmpKit's independent identity. KGP2.4.20
does not create a MavenPublication for a native component that cannot build on
the producer's host, such as WebView's local Apple cinterop on Linux. It still
advertises that component in root module metadata, falling back to project.name
for its coordinates. Vanniktech0.37.0 cannot rename a nonexistent publication.
Actual Linux metadata and packaged static inspection reproduce eight wrong
Apple module/URL redirects. See the [preserved evidence](../development/evidence/webview-consumer-important-20261028/README.md).

## Decision and execution order

`configureIndependentPublicationCoordinates` uses public
`GenerateModuleMetadata.configureEach/doLast` and an independently tested finite
schema. Following Gradle's normal metadata generation, it validates format1.1,
owning group/version/module and each redirected target against the exact six
declared target suffixes. Only a canonical old same-project module and its exact
relative URL are normalized to the independent coordinate. Correct target/root
metadata is left byte-for-byte untouched. Unknown target, version, group, URL
alias or metadata format fails closed before rewritten output is written.

Explicit schema/map/group/version task inputs invalidate stale incremental
results. Downstream signing, Maven checksums and publication consume this task's
final output; no manual consumer-only JSON edit occurs. Existing dependency
selectors, variant attributes, resource variants, artifact display labels,
payload hashes and compiler/JNI identities are not changed. Target availability
is not enabled or misrepresented; Apple payloads must be built/verified on their
actual supported host before complete distribution.

## Rejected alternatives

- Eager publication-container renaming breaks Vanniktech's checked original-name
  migration; the actual failed configuration is retained.
- Deferred renaming still cannot affect absent target publications; actual
  successful generation with eight wrong redirects is retained.
- Private KGP reflection, fake empty target publications or enabling unsupported
  cinterop would misrepresent ownership/availability and expand version risk.
- Renaming compatible Gradle project paths or reconstructing KGP components is
  unnecessary architectural churn. Accepting Calf redirects in the verifier or
  dropping advertised targets would hide rather than repair the identity defect.

## Tests, risks and compatibility

Six actual Kotlin schema regressions cover both unavailable Apple targets,
idempotent correct metadata, preservation of all noncoordinate fields, foreign
group/version/URL/unknown-target rejection, owning-component/format changes and
all six mappings. Focused actual generation confirms only the eight expected
module/URL pairs change; all desktop metadata remains identical. These are
metadata/tooling tests, not native library runtime tests.

KGP/Gradle upgrades and new/custom targets require explicit schema review and
actual generated-metadata consumers. Cross-host selector equality, full artifact
matrix, module/POM resolution, real JavaFX/native launches, legal/dependency
integrity, API/ABI and minimum-platform gates remain required. Publishing remains
contained; no signing or remote-publication gate is bypassed by normalization.
