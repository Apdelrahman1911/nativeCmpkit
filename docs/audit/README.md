# Technical audit

**Reviewed baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6` (Calf main,
2026-10-24). Findings cite that immutable commit, preserved in this repository.
Migration changes are additive commits, not rewritten evidence. This is an
implementation-level review and verification record, **not a production or
security certification**.

## Results and navigation

**164 findings: 0 Critical, 37 High, 106 Medium, 21 Low.** Of these, 105 are
source-confirmed, 23 have a scoped executable confirmation, 24 are risks and
12 are improvements. These labels describe evidence, not whether an issue is
currently fixed. Three baseline build findings were addressed during migration;
the remaining implementation findings are deliberately not silently repaired.

- [Every finding, priority and issue link](findings-index.md)
- [Final report and recommended next steps](final-report.md)
- [Complete ordered roadmap](../roadmap/backlog.md)
- [Executed checks and limitations](../testing/README.md)
- [Machine-readable counts](summary.json), [finding records](findings/),
  [issue plan](issue-plan.json), [migration resolutions](migration-resolutions.json)

| Area | Findings | High / Medium / Low | Implementation and evidence |
|---|---:|---|---|
| Adaptive UI | 45 | 12 / 25 / 8 | [Audit](ui.md), [module ledger](../modules/ui.md), [tests](../testing/ui.md) |
| Files, picker/saver, Coil | 26 | 5 / 19 / 2 | [Audit](io-and-file-picker.md), [module ledger](../modules/io-and-file-picker.md), [tests](../testing/io-and-file-picker.md) |
| Permissions and geo | 24 | 8 / 15 / 1 | [Audit](permissions-and-geo.md), [module ledger](../modules/permissions-and-geo.md), [tests](../testing/permissions-and-geo.md) |
| WebView, camera, share, prototypes | 39 | 6 / 29 / 4 | [Audit](native-features.md), [module ledger](../modules/native-features.md), [tests](../testing/native-features.md) |
| Core, navigation, icons, samples | 18 | 3 / 13 / 2 | [Audit](navigation-core-icons-sample.md), [module ledger](../modules/navigation-core-icons-sample.md), [tests](../testing/navigation-core-icons-sample.md) |
| Build, CI and supply chain | 12 | 3 / 5 / 4 | [Build/security](build-security.md), [central verification ledger](../testing/README.md) |
| Historical review | No duplicate findings | — | [Closed/open issues, PRs and design history](historical-review.md) |

## What was reviewed

The immutable [source inventory](source-inventory.json) covers **607 tracked
files**, including **479 source files** and **43,653 Kotlin/KTS/Rust physical
lines** (43,708 including Swift). It records hashes, source sets, dependencies,
lexical declarations and candidate expect/actual relationships. It is a
navigation/reproducibility tool, **not proof of semantic review by itself**.

The module ledgers independently describe implementation behavior, important
functions/classes, native ownership, callbacks, threading, error/cancel paths,
allocation patterns and platform divergences. Their scopes include:

- UI: all 141 tracked module files; 128 handwritten production files, 11 test or
  fixture files, the generated SF-symbol table and build configuration. Generated
  names are checked as data, not misrepresented as thousands of individually
  reasoned algorithms.
- IO/picker/Coil: 62/62 tracked files, including both Rust/native loader paths,
  filesystem/URI/NSURL/File semantics, cache, MIME resources and original tests.
- Permissions/geo: 132/132 files, including every feature registration/helper,
  platform stub, registry collision and location prototype.
- Native features: 47/47 files across WebView/cookies, camera, sharing and the
  empty/excluded maps/media/notifications projects.
- Navigation/core/icons/sample: the assigned 106-file ledger plus the generated
  SF-symbol catalogue review; sample platform shells, AOSP-derived code and font
  licensing are included, not just the reusable APIs.
- Build infrastructure, Gradle convention plugins, dependency catalogues,
  Android/Apple configuration, workflows, scripts, documentation and public
  upstream history are addressed by the build and architecture/history reports.

These area counts overlap where ownership was explicitly shared (build files,
generated resources, sample integration). **Do not add them into a fake coverage
percentage.** The [architecture map](../architecture/README.md) explains all
24 included library projects, 21 publishable projects, samples and excluded
scaffolds. No module is assumed functional because it is declared in Gradle.

## Evidence and severity rules

| Evidence status | Meaning | Does not prove |
|---|---|---|
| `confirmed-source` | Exact control/data-flow establishes the reported behavior or missing contract | Native runtime reproduction, prevalence, exploitability |
| `confirmed-test` | A preserved command/probe demonstrates the specific reported behavior | A complete framework/device pass; many probes use explicit adapters |
| `risk` | Concrete source/dependency boundary with unresolved environmental or adversarial preconditions | A demonstrated bug on every host or a working exploit |
| `unverified` | A historical report or hypothesis still needs a current reproduction | That the report remains a current defect |
| `improvement` | A documented capability, test, API or maintenance gap | That the gap is a security vulnerability |

`unverified` is used for separately recreated historical requests; none of the
164 audit records use that class at this snapshot. Priority is maintainer triage:
**Critical** would require exceptional confirmed impact and urgent response;
**High** covers material data/memory/lifecycle/permission failures or essential
release gates; **Medium** covers bounded correctness, compatibility, performance
and supply-chain concerns; **Low** covers polish or lower-impact maintenance.
No CVSS score or exploit claim is inferred from those labels.

Every finding includes exact baseline file/lines/symbol (or a real binary-asset
hash), root cause, impact/preconditions, recommendation, compatibility risks,
required tests, priority, effort, dependencies and upstream references. Validation
checks all **424 citation locations**, IDs, dependency cycles and entry-point
links. Passing that validator is structural evidence, not proof Kotlin compiles.

## Cross-cutting conclusions

1. **Data and ownership first:** oversized iOS `memcpy` length (IO-001), desktop
   self-save deletion (IO-004), Android pending-save content loss (IO-002), raw JNI
   handle races (IO-003), and incomplete native view/sheet disposal require focused
   regression tests before expanding feature scope.
2. **A common API hides unequal behavior:** camera/permissions/geo contain
   unsupported or no-op paths; web save does not call its result callback;
   multiple permission callbacks and native modal lifecycles are not uniform.
3. **UI is a native lifecycle integration library, not merely styling:** calendars,
   callbacks, safe areas, retained presenters, iPad popovers, gesture cancellation,
   keyboard and accessibility behavior must be tested on real platform surfaces.
4. **Desktop release metadata is not portable:** generated JavaFX dependencies
   capture the publisher OS (BUILD-001); native selection/provenance and ARM
   coverage need validation (BUILD-003/004), independently of Cargo compilation.
5. **Security findings are bounded:** one Low JavaFX advisory matched an exact
   coordinate; three Rust notices concern unmaintained crates. Neither demonstrates
   exploitation. Narrow secret-marker scans found no selected markers but are not
   an exhaustive secret scan. Inline-HTML isolation and arbitrary-opening fallbacks
   are explicitly conditional risks, not invented remote-code-execution claims.
6. **Performance is source-investigated, not benchmark-certified:** eager full-file
   copies, retained views/observers, per-frame work and repeated allocations are
   documented; no device CPU/memory/energy benchmark suite existed or was fabricated.

## Remediation and issue policy

Only BUILD-008, BUILD-009 and BUILD-011 are recorded as migration-resolved; their
original evidence and future-publication cautions remain visible. NAV-009's
repository notice repair does **not** certify license payloads in unbuilt artifacts.
No major architectural rewrite, release, package or deployment was performed.

The issue plan contains **164 audit issues plus six independent actionable
upstream topics**. Already implemented requests and historical reports covered
by findings are not blindly reopened. [All 17 open-item dispositions](../migration/upstream-actionable-decisions.json)
preserve upstream identities and rationale. Generated issue bodies do not
impersonate original authors/timestamps. Future synchronization preserves manual
lifecycle decisions/unmanaged labels and refuses ambiguous markers or conflicting
human edits.

Run `python3 scripts/audit/validate_audit.py` and regenerate indexes with
`python3 scripts/audit/render_knowledge_indexes.py` after changing finding data.
See [testing](../testing/README.md) for the distinction between feasible checks,
attempted-but-blocked builds and platform behavior still requiring devices.
