# [High][BUILD-001] Desktop WebView POM hard-codes the publisher OS in JavaFX dependencies

<!-- nativecmpkit-item:audit:BUILD-001 -->
## Classification
- **Finding:** BUILD-001
- **Priority:** High
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/build.gradle.kts:9-18`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/build.gradle.kts#L9-L18) — `platform`
- [`calf-webview/build.gradle.kts:41-47`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/build.gradle.kts#L41-L47) — `desktopMain.dependencies`

## Root cause
The desktop dependency classifiers are chosen from OperatingSystem.current() and os.arch during producer configuration, not the consumer runtime or a published OS-specific variant.

## Impact and preconditions
The same calf-webview-desktop coordinate encodes one operating system. A consumer on another OS receives the wrong JavaFX native artifacts unless it overrides dependency selection. The audit-generated Linux POM proves host capture; a cross-OS application launch was not executed.

## Supporting evidence
- Baseline local task :calf-webview:generatePomFileForDesktopPublication passed; no publication occurred
- docs/testing/evidence/baseline-webview-desktop-linux.pom contains classifier linux on all six JavaFX 19 modules
- docs/testing/evidence/baseline-task-inventory-and-webview-pom.log records the successful command

## Recommended solution
Model OS/architecture-aware desktop variants or require an explicit consumer JavaFX runtime dependency. Keep JavaFX modules aligned and add isolated published-metadata consumer fixtures for Linux/macOS/Windows; do not simply replace every classifier with the current migration host.

## Risks and compatibility
Changing Maven/Gradle metadata can affect existing consumers and duplicate transitive JavaFX modules. Validate both POM-only and Gradle-module-metadata clients.

## Required tests / acceptance criteria
- Generate POM and Gradle module metadata on two different hosts and compare dependency selectors
- Resolve and launch a desktop WebView consumer on Linux x64, macOS arm64/x64 and Windows x64
- Verify native classifier availability for every advertised architecture

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
