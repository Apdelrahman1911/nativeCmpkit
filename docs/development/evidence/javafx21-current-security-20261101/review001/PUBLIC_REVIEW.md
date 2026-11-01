# BUILD-002 / #144: current JavaFX 21 update and applicability review

## Result: no version-only source update is justified

The current catalog already selects **JavaFX 21.0.13** and **JDK 17**. Fresh, bounded Maven metadata for all six modules (`base`, `graphics`, `controls`, `media`, `web`, `swing`) independently lists **21.0.13 as the highest stable 21 release** at the observation. The global Maven `latest`/`release` value is `28-ea+12`, which is not a stable JavaFX 21/JDK17 update. Upstream `jfx21u` master has moved to **development 21.0.14**; no stable 21.0.14 is listed in the held Maven metadata. A development branch is not an available patched artifact release.

The parent POM for 21.0.13 is available from Maven Central. The current upstream 21 branch declares minimum build Java17 and runtime target17; that mutable branch is not proof of the exact released binary. The accepted existing 21.0.13 evidence supplies all **30 six-module/five-classifier HTTP200 observations** and **10 sampled major61 classfiles**. Those observations are reused, not repeated or upgraded into all-classfile/native/security certification. Required classifiers remain `linux`, `linux-aarch64`, `mac`, `mac-aarch64`, `win`.

**No source/test repository delta is proposed.** Increasing the pin to a guessed future patch, using the development branch, selecting the global EA, or moving to a newer-Java release would be unjustified.

## Exact advisory boundary

The original **GHSA-47g3-mf24-6559 / CVE-2024-20925** explicitly includes media19 and fixes the relevant later branch at **21.0.2**. The existing 21.0.13 pin is outside that retained affected range. This resolves that historical *version match*, not all BUILD-002 criteria or every current advisory. The finding remains **LOW / CVSS3.1**, requires human interaction, and specifically concerns clients relying on the Java sandbox while running untrusted Java code. No exploit against NativeCmpKit is established.

Fresh Oracle October2026 Java SE matrix rows identify JavaFX **21.0.12** for WebKitGTK, GStreamer, JavaFX and ImageIO issues. They do not list 21.0.13; absence from the vendor table is not independent proof that every Maven/native payload is patched. The ImageIO row uses **Note2**, which includes attacks through data supplied to APIs. A trusted-Java-only policy therefore cannot blanket-exclude all embedded-engine advisories. JavaScript/page content and untrusted Java execution are different trust boundaries.

The reviewed desktop WebView source implements no Java sandbox or untrusted-Java loader. That is a bounded source observation, not proof about every embedding application. The supported untrusted-Java execution policy remains undocumented and needs an owner/lead decision before claiming the original policy criterion complete.

## Accepted graph reuse and remaining work

The accepted graph remains **24 projects / 72 configurations / 142 Maven coordinates / 79 observed artifact identities**, with **108+34 prior OSV observations / zero coordinate matches**, not bundled-engine or release clearance. No old OSV query or build was repeated. Eight key JavaFX/catalog/KMP/settings/build declarations match the accepted graph exactly. Of 73 declaration/convention paths read back,70 match; `calf-io/build.gradle.kts`, `calf-permissions/core/build.gradle.kts`, and `PublicationNotices.kt` differ. The historical graph is not relabeled as a freshly resolved complete current graph.

Remaining original criteria: complete relevant resolved JVM graph/advisory review, actual media/TLS/cookies/navigation/JavaScript/rendering across all five Desktop hosts, and an explicit supported sandbox/untrusted-code policy. Reuse accepted same-input runtime subsets, not unrelated suite replays. Root owns the exact future verification selection, consumers, source freeze, Git/GitHub operations and issue decisions.

## Verification scope

Seventeen distinct, bounded unauthenticated public GETs; no JAR/native payload download. One oversized Gluon body was refused and not saved; a release-notes URL and the October mail index returned404. Those limitations are retained, with no automatic retry. Eight **new private metadata consistency models** pass8/8 once on56 held evidence files. This is not compiler, runtime, consumer, patched-native-byte or security acceptance. **ZERO new builds/native/old-query replay/Git/installation/publishing/live edits. #144 stays open.**

Public authorities: Maven Central `org/openjfx/*/maven-metadata.xml` and `javafx/21.0.13/javafx-21.0.13.pom`; OpenJFX highlights/home; OpenJDK `jfx21u` build properties/source; Oracle January2024 and October2026 CPUs. Exact URLs, timestamps, bounded-body hashes and public source locations accompany the private delivery.
