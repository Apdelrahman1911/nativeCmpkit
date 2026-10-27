# ADR 0001 — Independent identity without rewriting public APIs or history

- Date: 2026-10-24
- Status: accepted for migration; first-release API/publishing checks remain open
- Upstream baseline: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`

**Later name amendment:** [ADR 0008](0008-library-display-name.md) adopts
**NativeCmpKit** for the current display/root/POM identity on2026-10-27.
This migration decision and its historical observations retain their original text.

## Context

The owner requested an independent `nativeCmpkit` repository based on Calf, with
complete accessible history, Apache attribution and maximum practical backwards
compatibility. Globally renaming `Calf` / `com.mohamedrejeb.calf` would break Kotlin
imports, experimental opt-ins, Swift exports, Android resource classes, JNI symbol
names, native libraries and build project accessors. Rewriting historical commits
would also destroy hashes, signed-commit validity and original authorship.

## Decision

1. Create `Apdelrahman1911/nativeCmpkit` with GitHub **fork=false**, not through the
   fork API. Mirror all advertised branches/tags without force-pushing; append
   migration commits on `main`. Keep original PR refs in a complete Git bundle.
2. Rename the root Gradle project and live documentation to **nativeCmpkit**.
   Prospective group: `io.github.apdelrahman1911.nativecmpkit`; artifact IDs map
   `calf-*` → `nativecmpkit-*`. New development line: `0.1.0-SNAPSHOT`. These
   coordinates are **not published**, and namespace ownership is not yet verified.
3. Retain existing public Kotlin/Java packages, opt-in annotations, Gradle module
   directory / project names, JNI names, native library filenames and cache paths.
   Pin Compose generated resources and Android library namespaces to their old
   values so changing Maven group cannot accidentally change their APIs.
4. Update sample display names, Android application ID and iOS bundle ID. Keep
   Xcode project/Swift class paths and framework `Common` for compatibility; remove
   the upstream sample signing team so a developer must configure their own.
5. Preserve `LICENSE` byte-for-byte. Add `NOTICE`, exact third-party notices and
   prominent modification comments; retain upstream POM developer credit alongside
   the new maintainer. Preserve original docs/workflows in history and selected
   unmodified snapshots under `docs/migration/legacy/`.
6. Disable repository Actions **before** pushing history. Remove active inherited
   publishing/deployment jobs (not historical files), keep only read-only build /
   audit workflows with pinned action revisions. No packages, snapshots, releases,
   Pages sites, Netlify deployments or signing operations are authorized.
7. Accept any installed JDK 17 vendor instead of forcing a particular JetBrains
   daemon distribution and upstream-generated download URLs. This narrowly scoped
   portability correction does not change the Kotlin/AGP/Compose versions.

## Consequences and required checks

- Existing source imports can be retained, but **binary compatibility is not yet
  certified**. GAV coordinates deliberately change. Do not load old and new
  artifacts simultaneously because they define duplicate classes.
- A new namespace-wide API facade is deferred until an API design / deprecation
  proposal, binary API dumps and consumer tests exist. No alias layer is fabricated
  during the audit.
- Gradle composite consumers need explicit project substitution for renamed
  artifacts. Publication POM/module metadata must be checked on every platform;
  the new group alone does not prove all variant coordinates are correct.
- Historical Calf tags/release descriptions retain their identities and dates.
  Recreating them as nativeCmpkit releases would misrepresent the release history
  and is disallowed. Original issues/reviews are archived, not impersonated.
- Source independence means the new repository contains source, history, docs,
  native bridge code and metadata without requiring Calf to remain online. It does
  not mean Maven, Google, Cargo, Node or platform SDK dependencies are vendored.
- Functional bug fixes and architectural rewrites are deferred to audited issues
  and the roadmap, except minimal migration/build-safety/license corrections.

## Alternatives rejected

- GitHub fork: does not satisfy independent repository identity.
- History filter/rebase: loses original object IDs and contradicts preservation.
- Mass public-package rename: creates unnecessary source/ABI/JNI breaks before an
  audit and adds no immediate native functionality.
- Reuse the original author's Maven group or credentials: not authorized.
- Recreate historical PRs/releases with current authors/timestamps as if original:
  GitHub cannot reproduce the metadata faithfully; raw archives and explicit links
  are more accurate.
