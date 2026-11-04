# Private ordinary-Maven JavaFX cancellation adoption — #64 / NATIVE-005

**Source implementation and NEW small parser/fixture controls only. No real JAR
staging, Gradle/compiler execution, ordinary-consumer/native acceptance, issue
closure or publication is established by this document.**

This is the implementation follow-up to the dated
[`javafx-ordinary-adoption-gap.md`](javafx-ordinary-adoption-gap.md) review, not a
rewrite of its historical results. The original request/Stop/offline cohort is
accepted and must remain excluded. The new test below addresses a different
activation/provenance graph; no old library/native/consumer test is repurposed.

## Decision and current boundaries

The private selection is deliberately exact and unpublished:

```text
nativecmpkit.private.javafx:javafx-web-<classifier>:21.0.13-nativecmpkit-cancel1-local
```

Each of `linux`, `linux-aarch64`, `mac`, `mac-aarch64`, and `win` is a distinct
ordinary module. There is no public registry, newly released artifact, automatic
transitive activation, wildcard classifier, shared-cache transform, runtime
`--patch-module`, private loader route flag or hidden application convention.
Windows ARM64 and other unsupported hosts still refuse.

An application supplies these **five** ordinary aligned companions explicitly:

```text
org.openjfx:javafx-base:21.0.13:<classifier>
org.openjfx:javafx-graphics:21.0.13:<classifier>
org.openjfx:javafx-controls:21.0.13:<classifier>
org.openjfx:javafx-media:21.0.13:<classifier>
org.openjfx:javafx-swing:21.0.13:<classifier>
```

It supplies **web only** from the private identity. Do not add the private web
alongside the ordinary `org.openjfx:javafx-web`. The ordinary web POM's upstream
self-dependency is the reason this tool generates a new POM without dependencies
instead of copying that POM. The generated Gradle `.module` has matching Java17
API/runtime variants and no original-web dependency.

The library's existing `compileOnly` contract, public package namespaces/API,
Maven identity and six-module normal application convention are unchanged.
**Default consumer-facing adoption is still incomplete** until the new graph
passes verification and a distributable dependency/update policy is qualified.
The private implementation is not a public installation recommendation. Updating
the application convention is a subsequent reviewed step, not an implicit
fallback to unavailable private coordinates.

## Executable ownership and execution flow

| File | Responsibility |
| --- | --- |
| `tests/dependency/javafx-http2-cancellation/stage_private_web.py` | Independently inspect an existing generated candidate and write an exact fresh private Maven repository. No download/compiler/native/publish command. |
| `tests/dependency/javafx-http2-cancellation/private_web_resolution.py` | Bind actual staged/resolved artifact bytes, four normal classpaths, candidate/original/source/legal pins and exactly-one web provider. It verifies supplied observations; it does not execute Gradle or prove their acquisition was genuine. |
| `tests/dependency/javafx-http2-cancellation/official-companion-supplement.json` | Fixed independently acquired699 Swing5/generic5 hashes, lengths and exact official URLs. It supplements, never rewrites, the existing four classified companion pins or original14 candidate inputs. These integrity observations are not signing/security/legal acceptance. |
| `tests/dependency/javafx-http2-cancellation/test_private_web_adoption.py` | Tiny expressly synthetic staging/resolution regression models. Production CLI pins reject fake class/native payloads; these controls are not consumers. |
| `tests/dependency/javafx-http2-cancellation/test_ordinary_consumer_fixture_contract.py` | NEW passive source-contract controls for the standalone fixture, not Kotlin compilation or native behavior. |
| `tests/dependency/javafx-http2-cancellation/test_official_companion_provenance.py` and `test_official_companion_fixture_contract.py` | NEW owning trusted-pin/refreshed-observation synthetic and source controls. Original51 accepted model/source methods remain historical and are not replayed to qualify this correction. |
| `tests/consumer/javafx-ordinary-webview/` | Separate ordinary-Maven fixture, normal dependency declarations, actual artifact-observation task and exactly one NEW public native test. No producer/project/composite/init-script/sample fallback. |

### Staging integrity

The production contract reads the original owning assets from
`build_runtime_candidate.HERE`, so sparse source review uses the actual existing
builder assets; after integration this is the same directory as the new tool.

The stager requires an actual `candidate.json`, the before/after held maps, actual
candidate runtime/Java-source JARs, modified Java source, member reviews, eight
owning tool/legal inputs and six original inputs (five builder modules plus the
Java-source JAR): **14 original/owning files**, not a success-only JSON.
It rechecks full official input hashes/sizes, exact class/manifest pins, all548
original web and312 Java-source members, the four upstream-identical inner loader
classes, public classes, JPMS descriptor, native payload and unrelated sources.
Only the top-level `HTTP2Loader.class` and manifest may differ. The retained
member review has542 payloads because all five class replacements and the
manifest are excluded from that particular inventory; four class payloads are
also checked directly against originals. Added notices/patch/legal bytes are
checked in both outputs.

Runtime/source bytes are copied unchanged into the fresh repository. Staging
checks symlinks/shared regular files, traversal, duplicate/unsafe/signed ZIPs,
bounded payload/expanded sizes, source/class/provider substitution, output
overlap/overwrite and actual input changes during writing. Failed output is
preserved with a failed receipt, never overwritten or consumed.

The repository must be a **new direct child** of
`build/ci-verification/private-javafx-maven`; its parent is created explicitly.
The CLI offers only `--candidate-root` and `--repository`, not coordinate,
model-contract, download, publishing or release overrides.

### Resolution integrity

The verifier independently reconstructs the generated POM/module bytes, checks
actual staged hashes, cured owning classes and publication-ready=false manifest,
and re-inspects the actual original candidate in production. The staged source
and runtime JARs must match that candidate; producer success JSON does not stand
in for actual source/native/legal provenance.

All four compile/runtime/test configurations require one cured module and five
explicitly classified aligned companion modules. Legitimate generic companion
stubs may additionally resolve **only when their own fixed official bytes and
lengths match**; they cannot replace classified companions. Every classified
companion, including Swing, must likewise match its trusted digest **and** length.
Coordinates, classifier/filename labels and refreshed self-observed hashes are
not official byte authority. The original implementation omitted this comparison;
the NEW predecessor witness retained two failed methods/80 admissible tamper
subcases (five classified/five generic companions, both metadata modes, four
independently located classpaths), not an actual malicious artifact or native run.

Production uses the checked-in original `artifacts.json` SHA256
`246eb9bef73b24f2df53058f65344ff5ca81ba2b199d958f43997035c0cdf760`
and supplemental metadata SHA256
`a2cce99c5ad3a3628c9a042b454bc1e8b3f61eb308b392d78c5534687682e9d2`.
Both hashed documents are parsed from those same captured bytes. Missing,
changed, foreign-classifier, duplicated or malformed trusted pins refuse;
resolution/staging JSON and caller properties cannot inject replacements. The
explicit synthetic expected-pin parameter is unreachable from public verification
or the CLI and never promotes fake artifacts to official/ordinary acceptance.
Historical no-pin models remain explicitly synthetic, not official-byte proof.

Original `org.openjfx:javafx-web` is forbidden even as a generic empty stub.
Foreign/duplicate providers, including versioned public classes and nested or
case-varied native basenames, are refused. Consumer JAR inventories are read from
the same captured bytes that were hashed, not a separately reopened path. Actual
resolved, staged and candidate/original inputs are rechecked afterward.

Observed hashes now additionally match fixed independently acquired official
companion integrity pins; this is not trusted signing or advisory clearance.
Ordinary dependencies still need applicable security and
verification-metadata review. A graph-verifier result is not a command-execution,
native, full-source, public API/ABI or release attestation.

## Standalone genuinely NEW consumer

`observePrivateWebResolution` reads actual Gradle module artifacts on all four
classpaths, rejects source/project substitutes, binds the packaged library to
its held staged module metadata/Maven file, checks classified/generic companions
against the same fixed owning official pins, requires the actual supported host
classifier and writes `build/reports/private-javafx-ordinary-resolution-<mode>.json`.
Both exclusive local content routers are independent of Maven Central. Explicit
and automatically discovered init scripts are rejected. Java17/Gradle9.7.1 are
required. No production-host classifier is published by the library.

`ordinaryCuredWebStop` selects only:

```text
nativecmpkit.consumer.OrdinaryCuredWebStopConsumerTest
  .normalMavenActivationBindsCuredPublicStopTransportAndOwnedLifetime
```

The default `test` task is disabled so no old cohort is accidentally used. The new
method hashes loaded public NativeCmpKit/WebEngine JARs and the bounded owning
class resource and five actual public companion class origins (`SimpleStringProperty`,
`Scene`, `Control`, `Media`, `JFXPanel`). Their JAR names, lengths and hashes come
from trusted pins, and each loaded path must equal its exact admitted classified
test-runtime artifact. The five origins are rechecked after public disposal;
neither these Kotlin assertions nor their native execution is proved by source
controls. It verifies the owning resource's actual JAR URL, mounts a real Compose
WebView on an owned Swing/JavaFX window, seeds the same owner and starts one
loopback request held before any response. It calls **public navigator Stop**,
not a private engine/loader cancel, then requires the original six predicates:
native CANCELLED, not running, public Finished, exactly one CANCELLED transition,
exactly one actual peer EOF, and zero pending held requests. The absolute
ten-second deadline bounds queued FX/EDT waits too; fixture cleanup is still false
and held response count remains zero. Recovery uses the same native owner.

The test requires exactly-once public disposal, actual embedding Scene release,
owned window disposal and owned listener/socket/worker/acceptor cleanup. Queued UI
work is cancelled on scheduling failure, partial resources are retained for
independent finally cleanup, constructor/start failure cleans its own handles,
and teardown never increments the EOF witness. Nothing kills a foreign process
or the process-global JavaFX toolkit. A native event loop/process hang is not
proved fixed by these source controls; whole-process receipts/watchdog evidence
remain part of lead acceptance.

## Lead-only next verification sequence — NOT executed here

Keep local heavy execution serial and admit disk/memory capacity first. ROOT
integration/freeze/push/dispatch/acceptance/closure belongs to the lead; hosted
heavy reservations remain at most two including queued/reserved work.

1. Review/integrate these sparse sources and register a genuinely NEW finite
   ordinary-consumer focus. Reuse accepted unchanged library artifacts and source
   evidence only where applicable; never relabel earlier invocation maps.
2. Use actual retained/generated candidates, not synthetic tests, to stage each
   actual classifier. Preserve their original identities and full receipts:

   ```sh
   mkdir -p build/ci-verification/private-javafx-maven
   python3 tests/dependency/javafx-http2-cancellation/stage_private_web.py \
     --candidate-root "$ACTUAL_CANDIDATE" \
     --repository "$NEW_ABSOLUTE_PRIVATE_REPOSITORY"
   ```

3. On an actual supported host, resolve module and POM modes using the root's
   trusted Gradle9.7.1 wrapper and Java17, no init script:

   ```sh
   ./gradlew -p tests/consumer/javafx-ordinary-webview \
     --no-daemon --no-parallel --no-configuration-cache --no-build-cache \
     --max-workers=2 --dependency-verification strict \
     -PnativecmpkitRepository="$HELD_LIBRARY_REPOSITORY" \
     -PnativecmpkitVersion="$EXACT_HELD_LIBRARY_VERSION" \
     -PnativecmpkitPrivateJavafxRepository="$NEW_ABSOLUTE_PRIVATE_REPOSITORY" \
     -PnativecmpkitJavafxClassifier="$ACTUAL_HOST_CLASSIFIER" \
     -PnativecmpkitMetadataMode=module observePrivateWebResolution
   python3 tests/dependency/javafx-http2-cancellation/private_web_resolution.py \
     --repository "$NEW_ABSOLUTE_PRIVATE_REPOSITORY" \
     --resolution tests/consumer/javafx-ordinary-webview/build/reports/private-javafx-ordinary-resolution-module.json
   ```

   Repeat **resolution only** for `pom`. Keep original reports/commands/streams,
   fresh result acquisition and dependency/source maps. Actual dependency
   verification/security files must qualify; `strict` alone is not evidence.
4. Compare complete actual runtime identities/sizes/hashes across modes, not just
   web. Run `ordinaryCuredWebStop` on one **new distinct held graph**, with an
   owned graphical/audio/host environment and whole-process timeout. Require
   exactly-one fresh native JUnit method, no skips, exact loaded provenance and
   complete resource/terminal receipts. If all runtime bytes match across modes,
   explicitly reuse that one native result for that graph; do not claim two runs.
   Different graphs require their missing/new native scope. All five actual
   supported host/CPU combinations remain unverified for this adoption path.
5. Only after ordinary adoption, applicable source/security/API–ABI/native and
   release requirements pass may the application convention/public installation
   instructions move to a qualified distributable identity. The `-local`
   coordinate/manifest cannot be renamed into release readiness.

## Current upstream and material evidence

Two narrowly authorized public responses were acquired once on2026-11-04 and
preserved privately, not copied as third-party source into this patch:

* Official Maven web metadata SHA256
  `cbbc45d76e6ce38b621621ca8f307cb84b72fde240c0aea17c4a30815d8a5e25`
  still lists21.0.13 as the highest stable21-line version. `latest/release` is
 28-ea+12, which does not prove a compatible cancellation fix.
* The moving `jfx21u/master` owning source SHA256
  `e2413d1ac8cb78be77f97fc6add5e17bee1859e1c5fcbb97481444eb62eac43f`
  remains flag-only and byte-identical to the pinned21.0.13 owning source.
  No new exact commit identity or fixed released binary was asserted.

The separate lead699 exact official HTTPS acquisition independently captured
Swing5/generic5 bodies and their same-registry SHA1 sidecars once. Its expected
literal pin document SHA256 is
`a93892b96ee4f0a3410b87158c14cc1cf70ddcd3b6e75e23ad046371248880ef`;
original acquisition receipt SHA256 is
`8e5d05260417d01ff915a9cc6806bc89e1446f3b04901145dc74ddb7b0bd91f3`.
Independent620 qualified ten exact hash/size/origin literals:450050 binary bytes,
400 sidecar bytes. No raw JAR or sidecar is copied into this source patch. The
original acquisition's terminal exit/console was not retained; successful JSON
completion is its authority, not an invented shell receipt. TLS and same-registry
checksums establish only this integrity observation, not signing, archive safety,
native execution, legal/source readiness or independent security certification.

Passive reads of retained member inventories351/373 confirm the stated held
public/JPMS/native payload hashes, not independent remote binary/source trust.
For example macOS x64 retains `WebEngine.class`
`3aca4f89b46bbf7da73195da81c6580767fcf6ebe1ad85f9633ac39fd42bac09`,
`module-info.class`
`9a549478b8b487865f519e8120f705f37dbba7c537dafcf4928fe40bd61bc151` and
`libjfxwebkit.dylib`
`399606a22fad3e442d2605e996e8367f3a64b52db85393fbefa84d00919b5f8e`.

JavaFX changed source/classes retain GPLv2 with the Classpath exception, original
headers, dated modification notice, GPL/additional-license/assembly texts and
patch. NativeCmpKit's independently authored tooling remains separately licensed.
The312-member Java-source JAR is **not** complete preferred corresponding source
for retained native/third-party payloads. Exact binary-to-source/build identity,
native/third-party source, interface definitions/build/install/generator scripts,
applicable distribution/source-access mechanism, independent security/provenance
and ordinary consumer/native/API–ABI gates remain unresolved. No blanket legal
certification, Apache relicensing of JavaFX, package/release/deployment publication
or issue closure follows from private staging/control success.
