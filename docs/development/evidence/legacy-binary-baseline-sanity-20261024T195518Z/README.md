# Baseline-only Java fixture sanity — 6 cases / 31 assertions

JDK17.0.20 `javac --release 17 -proc:none` compiled the legacy Java fixture
against all **21 source-bound baseline desktop JARs** at clean tracked
`94d2492e99d5cbc060409d94d9f88febd06222d5`. The actual Java invocation returned
0 and reported six completed cases / 31 assertions. The two compiled class
hashes and input JAR/source bytes remained unchanged. Commands, bounded logs,
tool/JAR/source hashes and inspected counts are in `result.json`.

**Candidate cases executed: zero.** This is fixture sanity against old APIs,
not a before/after compatibility test, a Maven artifact-consumer test, or native
UI/JNI execution. No Gradle, network, sample application, native dialog, staged
publication or release ran. The sole explicit third-party runtime was the actual
Kotlin2.4.20 stdlib JAR, checked for hidden Calf/Jodd fallback classes; its manifest
version and content SHA1 matched the public Gradle cache identity. That is a
local content/identity check, not a dependency authenticity attestation.

Cases: IO constructor/extension owners, picker factories and an old external
default-interface implementor, permissions/status, share values/results,
WebContent/Cookie, and old inlined icon constants against runtime fields. A
future candidate invocation must retain the same old-compiled bytecode and
third-party dependencies on both old/new runtimes. Recompilation against the
candidate is not equivalent.

The exact fixture source, two class bytes (in inert
`compiled-legacy-fixture.zip`) and helper source are preserved for review.
`SHA256SUMS` covers all preserved files except itself and the redundant local,
Git-ignored `classes/` tree. This receipt is not broader ABI certification or
authorization to lift containment.
