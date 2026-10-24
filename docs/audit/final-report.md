# nativeCmpkit migration and technical audit report

**Report baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`, reviewed on
2026-10-24 UTC. **Destination:**
[Apdelrahman1911/nativeCmpkit](https://github.com/Apdelrahman1911/nativeCmpkit).

> Integration snapshot: source review and metadata export are complete. Expanded
> Git recovery, full managed Gradle CI, issue synchronization and final remote
> receipt are being verified. This paragraph will be replaced by their observed
> outcomes; it is not a completion or all-platform-pass claim.

## Executive assessment

nativeCmpkit is an independently maintained copy of a substantial KMP native
integration library. It contains useful reusable APIs and working source-tested
logic, but **is not ready for an unqualified production release**. Many targets
share API shapes without equivalent capabilities; several native ownership,
file-safety, permission, accessibility and build-distribution paths have concrete
defects. “Compiles on a target” and “works correctly on that target” are materially
different claims here.

The audit documents **164 findings: 0 Critical, 37 High, 106 Medium and 21 Low**.
Evidence classes: **105 source-confirmed, 23 scoped test-confirmed, 24 risks and
12 improvements**. These are not 164 security vulnerabilities. Three baseline
build findings are migration-resolved, while functional changes are left for
reviewed follow-up rather than bundled into an uncontrolled migration rewrite.

## Deliverables

| Requested result | Delivered record |
|---|---|
| Independent repository and retained identity history | Destination non-fork repository; all 46 original branches/23 tags; original main is an ancestor of additive migration commits |
| GitHub history and offline recovery | [Migration/recovery guide](../migration/README.md), [metadata coverage](../migration/metadata-coverage.md), original and supplemental bundles, raw metadata and checksums |
| New library identity and attribution | [Identity map](../migration/identity.json), [modifications](../migration/MODIFICATIONS.md), LICENSE/NOTICE/third-party provenance, compatible public namespaces |
| Implementation-level audit | [Audit overview](README.md), [all findings](findings-index.md), subsystem reports, [source inventory](source-inventory.json) |
| Persistent project knowledge | [Architecture](../architecture/README.md), [modules](../modules/README.md), [platforms](../platforms/README.md), [decisions](../decisions/README.md), [AGENTS.md](../../AGENTS.md) |
| Tests and build investigation | [Exact execution ledger](../testing/README.md), original tests, scoped probes, CI logs, toolchain/dependency evidence |
| Organized work | [170-item issue plan](issue-plan.json), original-topic dispositions, [complete prioritized roadmap](../roadmap/README.md) |

No release, package or deployment was published. The new coordinates are
prospective, not installable published artifacts. Historical Calf tags/releases
are archives, not endorsed nativeCmpkit releases. No upstream GitHub setting,
issue, PR or Git history was modified.

## Highest-impact findings

| Area | Concrete concern | Recommended first action |
|---|---|---|
| IO | IO-001 oversized iOS native copy; IO-004 desktop self-save deletion; IO-002 Android pending-content loss | Define bounded reads and safe source/destination semantics; add failing boundary/recomposition tests before fixes |
| Native ownership | IO-003 raw JNI handle/disposal races; NATIVE-002 retained engines; UI-018 incomplete presentation teardown | Introduce explicit ownership/state transitions without broad API rewrites; instrument cancellation/disposal/late callbacks |
| Permissions | PERM-002 alias result assignment; PERM-008 concurrent incomplete batches; PERM-009 missing Always upgrade; PERM-011 iOS version gating | Test identity/prerequisites, sequence native requests, guarantee complete exactly-once results and API availability checks |
| UI | Native calendar interpretation, stale alert callbacks, iPad popover presentation, permanent bar-measurement stop, gesture/accessibility gaps | Platform fixtures across calendars/locales/iPad/rotation and real accessibility/pointer interaction |
| WebView/share | NATIVE-001 stop command re-enqueues; NATIVE-013 global cookie-handler overwrite; conditional isolation/arbitrary-opening risks | Separate commands from events, preserve cookie ownership, make trust/capability policies explicit |
| Navigation/geo | Dropped arguments and duplicate-route saved state; public location state never updated | Focused duplicate-entry and state/error propagation regressions; do not advertise unfinished modules as supported |
| Build/distribution | BUILD-001 publisher-host JavaFX classifiers; BUILD-003 incomplete native prebuilt detection | Consumer fixtures on every promised host/architecture and per-module native provenance/content manifests |

The [finding records](findings/) contain exact code locations, roots, impact,
recommendations, compatibility risks and required tests for **every** item.
Priorities and dependency ordering are in the [roadmap](../roadmap/backlog.md).

## Verification actually established

- Gradle wrapper JAR/distribution digests matched official metadata. Configured
  toolchain versions were checked as available rather than downgraded to manufacture
  a successful build.
- Migrated Gradle configuration compiled, **42 KMP/desktop POMs** matched the new
  group/artifact/version/dependency mapping, and generated Cupertino resource
  packaging retained its original namespace.
- **15 unchanged original IO/picker JVM tests passed**, using exact cached
  dependencies and real source, without platform stubs. This is not the complete
  Gradle/Compose test suite.
- UI's **32 original common assertion bodies plus three defect probes** passed
  with explicit framework type adapters. Permission/geo, navigation, IO and native
  feature probes provide separate, clearly scoped confirmations. Do not add these
  incompatible evidence levels into a single “all tests passed” total.
- Read-only native CI on Windows, macOS and Linux compiled both Rust crates;
  **all six cargo invocations ran zero tests**. Native GUI/JNI lifecycle behavior
  was not validated by those successful jobs.
- Local full Gradle attempts were honestly recorded: baseline JDK-vendor
  provisioning restriction, missing offline dependencies and bounded disk-reserve
  termination prevented test execution. The migrated JDK restriction was repaired.
- One direct JavaFX advisory match is Low severity; exploitability was not
  demonstrated. Rust graph notices concern three unmaintained crates. Selected
  secret-marker scans had no matches but were not exhaustive secret detection.

Managed full Gradle/Apple/browser results will be recorded in the final integration
ledger with run URL, commit, job conclusion and actual XML counts. No physical
device test, performance benchmark, sanitizer campaign, release signing or binary
compatibility certification is implied by the checks above.

## Preservation boundaries

The metadata archive preserves authors, timestamps, IDs, links, current bodies,
public edits, reviews and historical decisions as GitHub exposed them. It cannot
transplant GitHub authorship or recover unavailable/private/deleted content.
Wiki/projects/settings access failures, inconsistent star/fork counts, null edit
diffs, one 404 attachment and unarchived expired build artifacts are explicitly
documented. The source and Git/metadata copies are recoverable without Calf
remaining online; public dependency registries and platform SDKs are not vendored.

## Recommended next steps

1. Establish a supported-platform preview boundary and fix data/memory/ownership
   High findings with narrowly scoped regression tests.
2. Repair permission orchestration, native modal/input/bar behavior and desktop
   distribution metadata. Preserve existing APIs or document compatible adapters.
3. Add real device/native consumer tests, dependency locks/verification, API/ABI
   gates, and artifact license/provenance checks.
4. Follow the full roadmap before feature expansion or major architectural change.
   Obtain separate explicit owner authorization before publishing anything.
