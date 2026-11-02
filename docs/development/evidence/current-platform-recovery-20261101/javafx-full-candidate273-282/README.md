# Private JavaFX full-JAR candidate: source, packaging and task admission

**2026-11-02, solo. Zero new native/library executions; no ordinary adoption.**

This prepares only the still-failed original Windows public Stop method for
#64/NATIVE-005. [Accepted dependency262–271](../javafx-cancel262-271/README.md)
is reused, not rerun. [ADR0013](../../../../decisions/0013-private-javafx-cancellation-candidate.md)
sets the separate adoption, legal/security and consumer/API-ABI prerequisites.

## Important results and retained failures

| Actual | Result | Scope |
|---|---|---|
| 273 | **21/21**, unittest0.105s/wrapper0.513833s | New synthetic archive/source/finite-selection controls; 1,203 library and14 candidate source inputs held. |
| 274 | **Exit1**, wrapper0.513440s | Correct pre-javac refusal: shell selected JDK21.0.12, not required17. Official cached artifacts copied; zero downloads/native. |
| 275 | **Exit0**, builder18.407707s/wrapper18.777616s | Explicit JDK17.0.20; private Linux full-JAR/Java-source packaging. All14 owning execution and1,203 library inputs held. |
| 276 | **Exit1/27.01s**, wrapper27.256512s | Init compiles but finite task admission refuses. Incorrect expectation omitted Gradle's task-specific `--tests` arguments. Zero native/tests. |
| 277 | **NEW5/5**, unittest0.003s/wrapper0.455004s | Exact cache reuse/refusal and one-task/workflow controls; accepted first21 AST bodies unchanged/not replayed. Initial actionlint correctly rejects unsupported setup-java@v4 signature input. |
| 278 | **NEW1/1**, unittest0.000s; actionlint0 | Voluntary reuse of the existing verified setup-java revision declares the signature input. Not a mandatory SHA policy or security certification. Accepted26 controls not replayed. |
| 279 | **Dry-run exit0/28.01s**, wrapper28.259916s | Correct exact task+`--tests`+selector admitted under actual Gradle9.7.1/JDK17.0.20; actual compiler/test tasks skipped. All1,203 library/15 candidate source inputs held. |

The **27 unique NEW controls** are three disjoint21+5+1 invocations, not one fresh
27-test suite. Previous dependency/native/control populations were not replayed.
Unittest XML/terminal clocks and enclosing wrappers have distinct scopes.
The dry-run uses the accepted Linux candidate digest only as a property; Windows
runtime guards do not execute. It proves **no Windows native/JAR replacement**.

## Full artifact evidence

Identity: `21.0.13-nativecmpkit-cancel1-local`; explicitly private/not ready to
publish. The retained Linux candidate SHA256 is
`3853d545d374db7cc623fb588dcd9b925821c96e1f7fb5d967c627b069efb552`.
Java-source candidate SHA256 is
`e461d22831521fdfb6505cc75c08e3bb4aea23fbfab99fb73123a0ed9d9a8b7a`.

- Exact official21.0.13 source/module artifacts are reused from private copies of
  verified caches; no cached JAR is edited and no new artifact is downloaded.
- **548 original web members:** five existing owning class members and the
  manifest are replaced; all542 nonowning payload members remain identical.
  All four emitted inner-class payloads are also **byte-identical to upstream**.
  Only `HTTP2Loader.class` and manifest actually differ. No extra/shadow provider
  is introduced; all public classes, JPMS descriptor and native library remain.
- All five emitted class hashes equal accepted263/270 bindings; the builder
  refuses changed or additional compiled classes instead of refreshing pins.
- **312 original Java-source members:** only the owning source differs; all311
  others remain identical. The original header is exact; a dated modification
  notice replaces a blank line outside it, preserving debug line numbering.
- Original GPLv2/Classpath/additional-license/assembly-exception bytes, exact
  modification and explicit limitations accompany both private candidates.
  **Full native corresponding source/third-party legal obligations are incomplete.**
- JARs/classes/source packages are retained privately, **not committed/uploaded
  or published**. Payload/member hashes are public evidence, not binary artifacts.

The source-qualified builder bounds archive inventories/expanded sizes and
refuses duplicate/traversing/encrypted/unknown-compression members, original
signatures, modified-candidate reuse and overwritten outputs. Hashes from the
same Maven registry are consistency checks, not independently trusted signing,
advisory or redistribution clearance.

## Solo passive qualification and correction

[280](280-REVIEW280.json) accepted26 passive checks then refused an overly strong
reviewer expectation: it wrongly expected all five replacement class payloads to
differ, though the four unchanged inner classes are stronger preservation evidence.
[281](281-REVIEW281.json) accepted21 further checks but looked for actionlint's
initial refusal in stderr; the actual diagnostic is retained in **stdout**.
Both original reviewer failures remain, with no candidate/source relaxation.
[282](282-REVIEW282.json) corrects only the failed receipt check and holds current
15 candidate/1,203 library bindings; accepted checks are reused. These are
passive source/artifact/result checks, **not additional tests or native executions**.
The later README addition is documentation-only; freeze receipts distinguish it
from the dated282 source map rather than pretending all15 bytes stayed unchanged.

## Exact missing-only CI route

`javafx-library-candidate.yml` uses one Windows2025 reservation, read-only contents,
no persisted checkout credentials/OIDC/publishing, and restore-only exact
dependency/runtime/selection caches without prefix fallback or cached results.
CRLF conversion is disabled and Git long paths enabled before full checkout.
The initial development push changing builder/init bytes starts **one** job;
do not also dispatch a duplicate. Documentation-only changes do not replay it.

`run_library_candidate.py` composes the existing finite source plan, fresh XML
quarantine/collector, actual runtime/daemon observations, process/disk guard and
checkout-local library-tests lock. The explicit init permits exactly:

```text
:calf-webview:desktopTest --tests
com.mohamedrejeb.calf.ui.web.DesktopWebViewStopRedirectAcceptanceTest.publicStopCancelsOneHeldNativeRequestBeforeAnyResponseAndRecoversOnTheSameOwner
```

It removes the only original pinned Windows web JAR and inserts the identified
candidate once after checking both digests. No runtime module patch, private
loader property, reflective native cancellation, test-body/ten-second/six-predicate
relaxation, sample substitute or ordinary dependency mutation is permitted.
Actual candidate replacement marker, fresh original XML, JDK17 daemon/runtime,
held sources/JAR, original native EOF/recovery and owned cleanup must be reviewed.
Workflow uploads JSON/log/XML receipts only, not candidate binaries or source packages.

## Issue state and limitations

The prior [#64 progress comment6572406697](https://github.com/Apdelrahman1911/nativeCmpkit/issues/64#issuecomment-6572406697)
was posted/read back once in272; original issue fields are unchanged. Do not
duplicate it. **#64 remains open**; preparation, dependency green cases or Windows
Stop1 alone do not complete its other Desktop/genuine browser-offline obligations.
No closure/status promotion or release-readiness/legal/security/consumer/API-ABI
inference follows. Last verified state remains97closed/75open/172total and
22implemented/42partial/95verified/five unresolved.

[Archive bindings](archive-file-bindings.json) preserve raw/private and public
digests separately; public copies redact local path prefixes only. All originals
remain cached; no CI original is reacquired. Continue solo, serial local heavy,
8GiB reserve/max2 combined hosted reservations including queued work. Publishing,
Pages, main/history and every native/consumer/security/readiness gate remain closed.
