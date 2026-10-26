# Contained verification checkpoint — 2026-10-26

**Still contained and not release-ready.** Work remains local on
`development/preview-hardening`, based on
`94d2492e99d5cbc060409d94d9f88febd06222d5`. The working tree is deliberately
uncommitted; its diagnostic snapshots are not immutable release candidates.
No changes were staged, committed or pushed during this checkpoint. No issue
was updated or closed, and no release, package, deployment or dependency
acquisition was performed. No new Gradle/library test run was launched today.

The [previous checkpoint](checkpoint-20261025.md) retains the browser, desktop,
Android-host/device and IO-publication investigations. This additive report
records the later Python/tooling sweep and the documentation defect it exposed;
it does not relabel older failures or substitute tooling tests for native tests.

## Control-state observation

The [15:31 UTC read-only GitHub observation](evidence/containment-readback-20261026T153101Z.json)
made five GET requests and found:

- Actions disabled; the API's SHA-pinning flag is false while disabled. Restoring
  Actions still requires the explicit control-policy update and exact allowlist
  described in [AGENTS.md](../../AGENTS.md), not merely toggling it on.
- Pages REST status `null`, with its historical workflow configuration retained.
- Zero GitHub releases; Pages issue #171 still closed.
- `main` still at the synchronization commit above.

These are point-in-time API observations, not continuous monitoring, a fresh
public HTTP Pages check, or Maven/package-registry enumeration. The earlier
Pages unpublishing/closure evidence remains the historical live-site check.

## Tooling005: Python suites passed; the full sweep failed

The [preserved 20-command run](evidence/tooling-005/archive.json) completed between
15:14:08 and 15:14:51 UTC with **19 zero exits and one failure**. Its 13,231
nonignored Git-listed inputs were unchanged throughout. The only failed command
was strict MkDocs, which exited 1 after 8 seconds. This run remains **failed**,
even though a later focused repair passes.

All **737 Python tooling methods passed**, without skips:

| Suite | Executed methods |
|---|---:|
| Audit | 35 |
| Migration | 63 |
| Development | 70 |
| Upstream synchronization | 6 |
| CI helpers | 72 |
| Native packaging helpers | 24 |
| Dependency-integrity core | 164 |
| Dependency observer helpers | 108 |
| Yarn fixtures | 67 |
| Consumer tooling | 119 |
| Documentation lock tooling | 9 |

Source inventory, baseline finding validation, migration/bundle integrity,
resolution-index freshness, icon generator `--check`, installed documentation
versions, `pip check` and tracked-diff whitespace checks also exited 0.
The installed-version check is not independent dependency provenance. These
checks executed **zero Kotlin/native/Maven consumer methods** and are not a
hosted CI run. The separate upstream-sync tests did not apply remote updates.

## Documentation-link root cause and regression

Strict MkDocs reported three warnings: two generated `status.md` links and one
hand-maintained `upstream-status.md` link used `../../docs/...`. These paths can
resolve on the repository filesystem, but leave MkDocs' `docs_dir` before
re-entering it; MkDocs consequently cannot identify them as site-local links.
Two additional INFO diagnostics identified nonexistent double-hyphen anchors in
`BUILD.md` and `dependency-integrity.md`.

The owning correction is
[`doc_link`, lines 489–500](../../scripts/development/validate_resolutions.py):

- Preserve same-directory links for `docs/development/...`.
- Use `../...` for sibling/root `docs/...` paths.
- Preserve `../../...` for repository files outside `docs/`.
- Retain Markdown-label escaping and URL encoding unchanged.

The manual upstream-status link and the two live anchors were corrected.
Historical evidence copies were not edited. `status.{json,md}` were regenerated
through the owning tool, not manually patched. **No MkDocs policy, warning
severity, build configuration or test requirement was relaxed.**

The [repair archive](evidence/docs-link-repair-001/archive.json) binds the exact
before/after generator and tests, seven-file diff, failed/successful test logs,
input maps and concrete generated-output checks:

| Phase | Actual outcome |
|---|---|
| First regression run | 49 methods; exit 1, seven failed assertions including subtests. One was a new fixture mistake: an underscore in a Markdown display label was incorrectly expected to be unescaped. This was not a production defect. |
| Corrected regression run on the old generator | 49 methods; exit 1, six failed link assertions across three distinct methods. The corrected repository-URL control passed. |
| Entire development-tooling suite after repair | **73/73**, exit 0; the existing 70 methods plus three new methods. |
| Regenerate and independently `--check` the index | Both exit 0; all 164 findings and 530 original acceptance requirements preserved. |
| Strict local docs build and generated-target inspection | **Exit 0 in 7 seconds**, zero warnings or unresolved-anchor diagnostics, **5/5 actual file/anchor targets passed**. All 13,239 nonignored Git-listed inputs held unchanged. |

The three new methods cover sibling/root documentation links, repository-file
URL controls and special-character encoding. The HTML check verifies the actual
copied issue-map/backlog JSON destinations and both live dependency-plan anchor
targets; it is not merely a string assertion on Markdown source.

Only the generator-identity field changed in the generated JSON model. Owner
records, statuses, IDs, dependencies, mappings and requirements are identical to
the pre-repair model. All **693 selected library/build input paths and hashes**
still match the latest IO metadata003 snapshot; no library rebuild is implied
or needed for this documentation-only correction. The 13,239-input docs scope
also includes baseline/evidence files and is not the same scope as those 693.

The 737-method sweep and 73-method focused rerun overlap in 70 development
methods. Do not sum them as 810 unique tests or claim one new full-suite run.
INFO notices about deliberately excluded historical evidence remain expected;
the zero-warning result is not a claim that every link in every archived document
has been checked or deployed.

## Independent review and final local checks

Independent review examines the repair receipts, output targets and status
invariants, together with the post-metadata BUILD document/ledger. Its additive
record is under `evidence/review/docs-and-build-20261026/`; the earlier
`browser004-build-docs-readback.json` explicitly predates the IO metadata/payload
additions and must not be used to seal them.

Subsequent lightweight final checks and bounded candidate-byte inspection, when
recorded, live under `evidence/checkpoint-final-20261026/` and
`evidence/review/candidate-safety-20261026/`. Read the actual receipt outcomes;
directory names and this handoff text do not assert those later checks passed.
Their additive evidence is outside earlier snapshots and is inspected separately,
not circularly certified by its own hash. No unrelated cache cleanup, external
artifact execution or new dependency download is required for these checks.

## Acceptance and next work

The [owner-ledger status](status.md) remains **89 implemented, 67 partially
verified, 8 unresolved, 0 verified**. A source repair or a passing scoped test
does not mean its finding's original acceptance requirements are complete.
No GitHub issue closure or release authorization follows from this checkpoint.

Priorities remain those in the [existing roadmap](checkpoint-20261025.md#outstanding-acceptance-work):

1. Establish the Android-device metadata failure's root cause and finish the
   picker/device tests. IO16/17 and picker zero XML before timeout remain the
   last device outcome. Android-host21/21 is JVM/Robolectric, not a device fix.
2. Verify parent-window ownership/thread/lifetime, real Apple/Windows and minimum
   platform behavior, provider/security-scope/resource lifecycles, native
   permission/presentation/accessibility and WebView popup flows.
3. Complete dependency trust and actual negative/rejection scenarios. Offline
   IO root metadata still lacks 45 common artifacts; Android metadata lacks
   `lint-gradle:32.4.0`. Narrow desktop/JS/Wasm metadata results do not replace
   the missing root/Android/Apple graph. Observer003/fixture005 runtime remains
   unexecuted; no further acquisition was performed here.
4. Resolve the 15 objc2-family license-material gaps and separate Apple SDK
   ambiguity; verify packaged notices/native slots, compiler ABI and independent
   consumers. **Zero of the 17 strict Maven Kotlin consumer methods executed.**
5. Only after containment is explicitly lifted and prerequisites pass, establish
   immutable cross-platform CI evidence and consider the first preview. There
   are no published preview release/package links to report from this work.

See [release-readiness.md](release-readiness.md) for the complete gate ledger.
