# [Low][BUILD-002] Pinned JavaFX media 19 matches a published low-severity security advisory

<!-- nativecmpkit-item:audit:BUILD-002 -->
## Classification
- **Finding:** BUILD-002
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/build.gradle.kts:42-47`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/build.gradle.kts#L42-L47) — `JavaFX 19 dependencies`

## Root cause
All JavaFX modules are fixed at 19; OSV/GitHub-reviewed GHSA-47g3-mf24-6559 explicitly lists org.openjfx:javafx-media:19 as affected by CVE-2024-20925.

## Impact and preconditions
A dependency-advisory match is confirmed, NOT exploitation in this library. The advisory is LOW, CVSS 3.1, requires human interaction, and describes sandboxed clients executing untrusted code; applicability to ordinary trusted desktop applications must be separately assessed.

## Supporting evidence
- 45 exact direct Maven name/version queries returned one match
- docs/testing/evidence/osv-direct-maven-query.json
- docs/testing/evidence/advisory-GHSA-47g3-mf24-6559.json

## Recommended solution
Choose a maintained, JDK-compatible JavaFX line, upgrade all JavaFX modules together and verify its current advisories. Advisory fixed branches include 17.0.10 and 21.0.2, but these historical minima are not a recommendation to stop updating there.

## Risks and compatibility
JavaFX/JDK minimum versions and WebKit behavior can change. Do not describe an old dependency as arbitrary-code execution without a reachable, verified exploit path.

## Required tests / acceptance criteria
- Repeat OSV/advisory checks against the full resolved JVM graph
- Regression-test media, TLS, cookies, navigation, JavaScript policy and rendering on all desktop hosts
- Document whether sandboxed untrusted-code execution is supported

## Dependencies
- BUILD-001

## Historical context
- https://osv.dev/vulnerability/GHSA-47g3-mf24-6559
- https://www.oracle.com/security-alerts/cpujan2024.html
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
