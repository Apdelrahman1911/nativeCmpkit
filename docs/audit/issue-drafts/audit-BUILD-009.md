# [Medium][BUILD-009] Pinned JetBrains-only daemon prevents use of installed JDK 17 and contradicts CI setup

<!-- nativecmpkit-item:audit:BUILD-009 -->
## Classification
- **Finding:** BUILD-009
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `build tooling`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`gradle/gradle-daemon-jvm.properties:2-13`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/gradle/gradle-daemon-jvm.properties#L2-L13) — `daemon vendor criteria`
- [`.github/workflows/gradle.yml:36-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/gradle.yml#L36-L40) — `Temurin 17 setup`

## Root cause
Gradle daemon JVM criteria require JETBRAINS 17 and override ordinary launcher selection. A machine with supported OpenJDK/Temurin 17 therefore needs another vendor download; the CI setup installs Temurin, not the specified vendor.

## Impact and preconditions
The unmodified baseline fails before project configuration in offline/no-provisioning environments despite JDK 17 being installed. Online provisioning may hide the issue but adds network/vendor dependence and startup downloads.

## Supporting evidence
- docs/testing/evidence/baseline-desktop-offline.log records Cannot find a Java installation matching vendor=JetBrains
- Renaming only the criteria file in the detached baseline allowed convention compilation and task/POM generation
- Migrated minimal toolchainVersion=17 criteria succeeded with the installed JDK17

## Recommended solution
Accept an installed compatible JDK 17 regardless of vendor unless a documented tested build requirement demands JetBrains. The migration already removes the vendor restriction; keep a JDK-install prerequisite rather than undocumented vendor-specific URLs.

## Risks and compatibility
Runtime recommendations for Compose applications may differ from the build daemon JDK and should be documented independently.

## Required tests / acceptance criteria
- Configure the unmodified migrated tree with installed Temurin/OpenJDK 17 and provisioning disabled
- Exercise CI runner JDK selection and record the actual daemon version

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)

## Migration remediation (baseline finding retained)
Migration daemon criteria require JDK 17 without pinning JetBrains or stale per-platform provisioning URLs. The migrated configuration and all 42 POM generations executed successfully using the installed JDK.

Verification files:
- gradle/gradle-daemon-jvm.properties
- docs/testing/evidence/migrated-coordinate-and-res-checks.json
- docs/testing/evidence/migrated-poms-and-resource-package.log

Remaining caution: A supported JDK 17 still must be installed. This result does not prove every platform or runtime test passes.
