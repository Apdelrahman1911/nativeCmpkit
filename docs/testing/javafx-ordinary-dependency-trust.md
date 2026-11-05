# Ordinary Windows consumer1: dependency-trust blocker and finite qualification

**Plan and source-only preflight, not acquired dependencies, compiler/native
verification, an approved trust policy or #64/release clearance.** No checksum
writer, verification bypass, remote acquisition or artifact staging is added.
The accepted private Windows Stop must not be replayed.

## Confirmed blocker and the two invocation roots

The clean isolated `7d2029823b8a0fc9115a2c7a2387e08b1c9c332a` tree has no
`gradle/verification-metadata.xml` at ROOT, at `convention-plugins`, or at
`tests/consumer/javafx-ordinary-webview`. Historical synthetic Maven fixtures
contain XML; those are not production trust documents. Gradle's `strict` switch
without an applicable verification document is not checksum enforcement.

| Invocation | Required policy location and scope |
| --- | --- |
| ROOT wrapper / `stageWebViewVerificationPublications` | ROOT `gradle/verification-metadata.xml`; all downloaded artifacts used by plugin/settings/buildscript/configuration and selected task execution, including external dependencies of the `pluginManagement.includeBuild("convention-plugins")` composite. A library runtime-only graph does not cover these scopes. |
| Same wrapper with `-p tests/consumer/javafx-ordinary-webview` | That standalone root's `gradle/verification-metadata.xml`. The wrapper's location does not make ROOT's file this build's policy. Cover all three declared plugin families and all four ordinary compile/runtime/test configurations in both metadata modes. |
| A future `-p convention-plugins` invocation | It is another independent root and needs its own policy. This task does not invoke it separately or infer its policy from ROOT. |

Dependency verification is top-level/composite-wide within an invocation; an
included project's own file is not a substitute for the main invocation's
policy. The actual Gradle9.7.1 read locations and included-build external coverage
still require source/specification qualification and an affected negative
enforcement check. No real main/composite verification run is established here.

The new `--metadata-preflight-only` command reads the **two actually invoked**
roots, reports missing/malformed/unsafe documents without raw XML or credentials,
and starts no producer/compiler/native work. SHA256 structure can be usable
without being independently trusted; its report always distinguishes those
states. The workflow runs this before Rust/SDK setup. The actual controller
rechecks it before source/runtime acquisition and holds both documents in its
source maps. Current missing documents therefore stop native dispatch cheaply.

## Finite acquisition and review sequence — not executed

1. **Freeze a dependency-only intake.** Bind the actual source revision,
   catalog, root and convention settings/build files, producer task selection,
   fixture files and wrapper/JDK identities. Scope exactly the two actual
   invocation roots above. Record repository routing and no-init-script consumer
   policy. The historical193-coordinate runtime export is metadata-only and
   excludes compiler/plugin/test/native scopes; do not reuse it as a complete
   artifact trust list.
2. **Collect exact advertised metadata without pretending to trust it.** Use
   bounded official Maven Central, Google Maven and Gradle Plugin Portal
   coordinates/URLs, starting with the declared exact plugin marker POMs,
   implementations and catalog dependencies, and following actual POM/module/BOM
   references. Capture original status/headers/body/hash/length/time/URL once in
   a fresh quarantine, including applicable `.pom`, `.module`, binary, classifier
   and compiler/plugin artifacts. Do not send tokens, execute an upstream
   bootstrap script, overwrite a receipt or use a success-only JSON. Actual
   Gradle graph acquisition executes plugin/configuration code: schedule it only
   after the initial code-bearing bootstrap dependencies are individually
   reviewed. It is not a safe metadata-only download merely because it exports
   JSON.
3. **Corroborate bytes before approving expectations.** Compare independently
   captured publisher-advertised checksums and applicable detached signatures.
   Record algorithm, full signing fingerprint, how its publisher identity was
   independently anchored, signature verification result and any unsigned or
   uncorroborated artifact. Same-registry sidecars are an integrity observation,
   not an independent trust root; a locally recomputed SHA256 is also only an
   observation. Where signatures/independent advertised digests are unavailable,
   require a documented publisher/source/reproducible-build alternative or keep
   that row unresolved. No blanket TOFU promotion, wildcard trusted group,
   ignored verification failure, refreshed checksum acceptance or fabricated
   security approval.
4. **Inventory the genuinely required artifact closure.** Root coverage includes
   settings/toolchain plugins, included convention dependencies, Android/Kotlin/
   Compose/publishing plugins loaded during configuration, the selected WebView
   producer compiler inputs and downloaded descriptors. Standalone coverage
   includes Kotlin JVM/Compose/compiler plugins, Compose Desktop/Material3,
   Kotlin/JUnit/coroutines test inputs, transitive modules and the actual
   Windows-x64 Skiko payload; catalog declarations alone are not the selected
   graph. Record exact group/module/version/classifier/extension/filename,
   origin, expected digest/length, scope and each artifact's corroboration basis.
   Missing/foreign/dynamic/changing coordinates remain explicit blockers.
5. **Reuse only applicable original JavaFX metadata.** Official699 already
   acquired Swing5/generic5 once and independent620 checked its literal
   hash/length/origin matches. Existing `artifacts.json` and
   `official-companion-supplement.json` bind25 classified and five generic
   companions; only five classified `win` and five generic companion entries
   apply to this consumer graph. Reuse these integrity observations where exact,
   not as new downloads, signatures, advisory clearance or native tests. The
   private cured web is separately bound to actual candidate/stager inputs;
   never substitute the original `org.openjfx:javafx-web` or duplicate a provider.
6. **Reconcile local packages explicitly.** Gradle's file-Maven downloads are
   not exempt merely because the repository is local. Independently bound local
   library/stager receipts must supply exact JAR/POM/module identities and
   digests. Generated bytes cannot have their digest guessed before staging.
   Either prepare exact reproducible local expectations in a separate accepted
   staging pass before freezing the cohort, or separately review a confined
   standalone working-metadata materialization from the held manifests. This
   patch implements neither option; the immutable source maps prohibit adding
   arbitrary checksums mid-run. A public-group/private-group trust exception is
   not an acceptable shortcut.
7. **Adopt explicit reviewed expectations, then prove enforcement.** The lead
   and independent reviewer reconcile each row and its declared trust level
   before installing the appropriate root policy. Keep original observations
   immutable. No `--write-verification-metadata` or refresh occurs in the native
   verification workflow. A fresh strict invocation must retain actual selected
   graph/verification output and unchanged metadata. In disposable controlled
   fixtures, alter one expected plugin/convention external artifact and one
   standalone companion/transitive artifact, omit a required expectation, and
   include a new dependency: require typed Gradle verification refusals for the
   affected owner before native code, not any generic failure. Verify that the
   standalone file—not ROOT's—is read and that the main composite's external
   dependencies are covered. These important enforcement checks have not run.
8. **Only then run the new consumer scope.** A reviewed strict ROOT producer,
   actual held local package inspection, both bound complete module/POM graphs
   and the supported Windows host are prerequisites. Compile the actual fixture;
   source/Python syntax and XML structure are not Kotlin compilation. Preserve
   originals, resource/runtime/command outcomes and fresh XML. Request exactly
   NEW ordinary consumer1, and reuse its result for POM only when the complete
   admitted runtime graph is identical. Separate packaged JNI3, the other four
   supported ordinary host graphs and all original missing criteria remain.

## Compiler evidence and remaining safety boundaries

`compile-diagnostics.json` selects existing bounded credential-filtered public
Kotlin source errors and Gradle failure locations/causes from only four owned
logs: producer, module/POM resolution and native child `consumer.log`. Original
hashes/lengths are retained; the files are not modified. It is uploaded on
controller completion/failure together with the early metadata JSON. Full logs,
packages and arbitrary application output are not uploaded. The existing4MiB
input/24-excerpt bounds can omit diagnostics and are disclosed; this is not a
general secret scrubber or a promise that abrupt process termination runs finally.

No actual compiler/native run or dependency acquisition was performed for this
patch. Local capacity was below8GiB free disk/compiler6GiB memory. Structural
metadata preflight never sets `independent_trust_qualified` or
`dependency_verification_metadata_qualified` true. Independent source review,
successful hosted verification, GPL/native complete corresponding-source,
API–ABI/JPMS, advisory/supply-chain, all-platform consumer, main/history/Pages and
release-readiness gates remain. No package/release/deployment publication or issue
closure follows from this change.
