# Contained development with authorized verification CI

## Current owner decisions — 2026-10-26–27

The owner explicitly enabled **Allow all actions and reusable workflows** and
authorized that configuration **without mandatory SHA pinning**, automatic CI
configuration/fixes/execution with minimum permissions, and continued development,
Android/Apple/Windows/dependency/consumer verification. Routine development and
verification require no further approval. The final instruction is **contain
without using agents**: work single-agent, with no spawned/resumed subagents.

On **2026-10-27** the owner reaffirmed **contain without using subagents**.
Historical agent handles are not authorization to restart or delegate work.
Routine verification remains authorized; publishing/security gates are unchanged.

This **supersedes** the earlier disabled-Actions, exact-six-action allowlist,
mandatory SHA-pinning and routine-verification approval instructions. Historical
receipts and checkpoints retain their actual observations; they are not current
policy. See [ADR 0005](../decisions/0005-verification-actions-policy.md).

### Authorized now

- Repair source/tests/build tooling; acquire necessary dependencies and run
  bounded local or hosted verification, including local-only Maven staging and
  independent packaged consumers. Local staging is not registry publication.
- Configure and execute reviewed verification workflows automatically. Actions
  may remain enabled with `allowed_actions=all`, `sha_pinning_required=false`.
  Existing exact references may remain voluntarily. No new mandatory action
  allowlist is imposed. Review third-party actions and use minimum permissions.
- Commit and push additive development revisions for immutable CI evidence on
  `development/preview-hardening`. Preserve `main` at the completed issue-sync
  checkpoint until reviewed integration. Never rewrite imported refs/history,
  attribution or the upstream repository.
- Select necessary CI jobs, bound concurrency, reuse valid input-bound dependency
  and compilation caches, and rerun failed jobs instead of repeating successful
  unchanged jobs. Never restore old XML as fresh test execution.

### Still restricted

- **No packages, releases, snapshots, deployments or Pages** until applicable
  [release-readiness](release-readiness.md) and security requirements pass.
  Conditional preview authorization is not a waiver of any gate.
- Verification jobs keep read-only `GITHUB_TOKEN` permissions; no package,
  deployment, release or OIDC write scope. Do not persist checkout credentials,
  expose secrets, run archived workflows, or dispatch imported historical refs.
  Upload selected test evidence only, not distributable candidate binaries.
- No automatic issue closure on a source patch, compile, stale/empty report or
  unrelated passing suite. Native/device, consumer, ABI, legal and dependency
  gates require their own reviewed execution and exact scope.
- No subagents, destructive history changes or unrelated feature/refactor work.
  Preserve all other projects/caches; local builds retain an 8 GiB disk reserve.

## Observed controls and evidence boundaries

The [read-only transition observation](evidence/ci-policy-transition-20261026/observation.json)
at 2026-10-26 17:09 UTC confirms Actions enabled/all/no-required-pinning, default
workflow permissions `read` with PR-review approval disabled, two active
verification workflows, no in-progress run in the returned page, zero GitHub
releases and unchanged `main`. Pages status remains null, with legacy branch
publishing off (`build_type=workflow`). This is not a fresh public-HTTP Pages
measurement or package-registry enumeration. Pages #171's earlier verified
closure and historical deployment remain preserved.

Earlier `evidence/gradle/` and local diagnostic receipts bind commands, source
hashes and actual reports to **dirty development snapshots**, not immutable release
candidates. New hosted runs must record exact commit, run/attempt URL, host/SDK,
task exits and nonzero fresh test counts. Preserve failures and report missing
coverage; repeated target executions are not distinct source test methods.

Actions availability authorizes verification, **not a final-delivery or release
success claim**. No current release gate is lifted merely by this policy change.
