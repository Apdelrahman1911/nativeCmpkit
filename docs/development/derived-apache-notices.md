# NAV-018: inherited Apache source and artifact notice retention

**#103 is closed/completed** after all four original criteria, exact committed
inputs and [GitHub readback](evidence/derived-apache-notices-20261101/closure001/README.md).
The broader release/legal/native gates below remain separate.

This is a **narrow source/distribution contract**, not full legal clearance, a
native-dependency finding, runtime/API/ABI acceptance, or release authorization.
Original #103 criteria remain unchanged. No registry, Pages or release operation
is needed to perform these checks.

## Original source, Calf authorship and unknown copy revisions

- [AndroidX/AOSP comparison pins](../../licenses/navigation-aosp-provenance.json)
  identify established source headers, not the versions originally copied.
- [Compose Cupertino/Kyant correspondence](../../licenses/ui-derived-source-provenance.json)
  retains exact pinned license texts and source comparisons. The Cupertino slider
  moved from the historical iOS path to commonMain; its baseline path is not
  rewritten to pretend it was always common source.
- [Retained-Git introduction trace](../../licenses/derived-apache-introduction-history.json)
  records ten adapted files: exact introduced paths, original Calf commit authors,
  author/committer timestamps, source Git blob identities/SHA256 and rename events.
  Calf's initial navigation commit is authored by **M0Coding**, whereas the UI
  introduction commits are authored by **MohamedRejeb**. These commit authors are
  not substituted for the original AndroidX/Compose Cupertino/Kyant copyright
  holders.
- The common slider appears in `6eb7c66e` (author **abdelrahman fahmy**,
  2026-10-26): fixed `git log --follow` reports an **A** event, while the same
  commit's `diff-tree -M` reports separate commonMain **A** / historical iosMain
  **D** events. Exact parent/addition source hashes and public commit metadata
  are recorded. This is a source-path replacement/adaptation, **not** an observed
  Git rename, byte-identical move or recovered original third-party copy version.
- DragGestureInspector/InteractiveHighlight originated under iosArm64Main/button,
  then moved via R098/R096 in `01a070e9`. Querying their later paths at `caff0465`
  correctly refuses; trace the renamed path rather than fabricating a blob.
- Every exact originally copied third-party revision remains **unknown/null**.
  A Calf introduction date, an observation pin or a high-similarity comparison
  does not establish the original upstream copy revision.

The four NAV files retain their existing full Apache headers. The relocated
Cupertino slider and three Kyant utility adaptations retain known source
copyright/license headers, the original Calf modification notice, and references
to the complete license texts. The Compose Cupertino license's original
JetBrains attribution is retained verbatim, including its original wording.
No Kotlin package, declaration, body, API or Git history is changed by the notice
insertion. This source contract is not a blanket statement that every upstream
obligation or future distribution has been certified.

## Narrow artifact-family oracle

`tests/consumer/verify_artifacts.py` already checks POM/module metadata, exact
staged hashes, native/full accompanying license materials and module-qualified
archive notices. UI is one of the 21 declared publication roots. Navigation does
not apply publication and is absent from that identity allowlist; the default
inspector rejects `--module nativecmpkit-navigation`. Its adapted-source map is a
future archive policy exercised only by authored ZIP fixtures with a synthetic
identity scoped to verifier construction. It creates no NAV producer or accepted
binary distribution. The following rules apply to actual UI candidates and the
modeled future NAV archive policy:

| Actual staged family | Required retention |
|---|---|
| Source JAR for each selected UI coordinate; modeled future NAV source JAR | Required even if metadata omits the sources variant; module-qualified exact `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md` and complete `licenses/` bytes; exact applicable adapted Kotlin source/header bytes. |
| Metadata/desktop JAR and Android AAR | Existing module-qualified complete embedded notice bytes, not another module's equal-looking prefix. |
| JS/Wasm/iOS KLIB | Do **not** rewrite compiled payload to insert legal text. iOS publishes the direct compiler KLIB; JS/Wasm assemble compiler payload with existing resource/notice wrappers. The verifier requires the exact same-coordinate companion `-notices.zip` and byte-compares all complete canonical notice materials. |
| Companion notice ZIP | Canonical `META-INF/nativecmpkit/` layout, full texts and source-history/provenance JSON, including distinct original copyrights. |

The explicit adapted-source map contains four common NAV files, the common UI
slider and five iOS UI component/utilities. Metadata source archives include all
inherited source sets; the two iOS targets include commonMain/iosMain; ordinary
Android/desktop/JS/Wasm source archives require the common adaptation only.
No iOS source applicability is fabricated on non-Apple targets.

ZIP CRC/path/link/duplicate/size safety and all existing independent POM/module,
native dependency, companion and publishing gates remain. Source expected bytes
are captured once with the notice snapshot, not reread separately per archive.
Unrelated modules do not acquire NAV/UI source rules. An inspection result is
**static evidence only**: an authored ZIP fixture is neither a compiled JAR/KLIB
nor an isolated consumer or native test.

## Important guard batch

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/consumer -p 'test_derived_apache_notices.py' -v
```

The finite suite defines four source/history methods and ten artifact-fixture
methods. Git operations are read-only, fixed retained object queries; there is
no network, Gradle/compiler invocation, real artifact production or publication.
The synthetic tests cover two modules/seven source-set target shapes, exact
source headers/bodies, missing/truncated/foreign-prefixed notices, all archive
families, omitted source metadata, required same-coordinate companions and
unchanged unrelated-module policy. The NAV identity injection ends before archive
inspection or runner metadata parsing; its guard checks that the real 21-root
allowlist and default NAV/unknown-module rejection remain before and after it.
Select new/affected important methods and reuse accepted unchanged source,
license, Git and archive-parser results after owning input review.

## Actual staging and accepted static evidence

Use an immutable or exact held source/notice snapshot and the existing isolated
file-repository interlocks. Stage **only UI**, never the root
21-module staging aggregate or any remote/Central/Maven-local task. Navigation has
no owning publication task: its current acceptance is local source retention,
and its future binary archive policy remains synthetic/unobserved. Discover
actual UI publication task names first; retain every intended artifact family
and target. Use `-PnativecmpkitVerification=true` and an exact non-SNAPSHOT local
candidate version (for example `-PnativeCmpkit.version=0.1.0-preview.1`) because the
existing inspector deliberately rejects timestamped snapshot repositories. A
local candidate filename is **not** a released or published Preview artifact.

After serial local staging, inspect every produced UI target family:

```bash
python3 tests/consumer/verify_artifacts.py \
  --source-root . --repository build/verification-repo \
  --version 0.1.0-preview.1 \
  --module nativecmpkit-ui \
  --output build/ci-verification/derived-apache-notices/all-ui-review.json
```

The default target set includes metadata, source JARs, primary binaries and companion
notices, not compiler classes/build-directory substitutes. Complete actual
UI `iosArm64`/`iosSimulatorArm64` source/KLIB/companion archives can be inspected
after actual Linux cross-compilation. An Apple host/link/runtime is not an original
#103 static-distribution requirement. Never fabricate unavailable publications,
transfer candidates under reports-only policy, or call cross-produced KLIBs native
runtime/ABI passes. Report exact origins, held source/notices, task markers, hashes
and failures. JS/Wasm compiler payload identity and iOS whole-KLIB identity are
distinct observations.

The [actual owning repair and evidence](evidence/derived-apache-notices-20261101/README.md)
retain the initial **773 checks/140 failures**: all seven real source JARs omitted
20 complete notice files each. KGP2.4.20 creates the current
`org.gradle.jvm.tasks.Jar`; the deprecated bundling Jar is only a subclass, so the
old hook missed source archives. The current-base import fixes the producer rather
than relaxing the verifier. Corrected staging passes0/231.05s and all **773 static
checks** pass on1023library/1100combined/25legal held hashes. All14 primary/companion
archives retain exact initial bytes. This is local candidate verification only.

Closure requires every original #103 criterion to be reviewed
against implemented source/history and accepted actual artifact-family evidence
for current producers. NAV has no actual binary producer acceptance; synthetic
archive models do not establish future publication compliance.
C1 comparison evidence and exact preserved licenses may be reused after owning
source review; C2 records Calf introduction with honest unknown copy versions;
C3 retains its source/future-binary notice requirement, with actual UI
source/object distribution retention and explicit NAV future-policy limits;
C4 requires known
Compose/Kyant correspondence/copyright preservation. Broad navigation runtime,
objc2 license supplements, all-21-root consumers and security/release readiness
are independent gates, not silently appended #103 criteria or waived by it.
