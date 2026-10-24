# [Medium][BUILD-008] Release version input is embedded directly in executable shell scripts

<!-- nativecmpkit-item:audit:BUILD-008 -->
## Classification
- **Finding:** BUILD-008
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `CI`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`.github/workflows/build-native-libs.yml:42-46`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L42-L46) — `Cargo version stamping`
- [`.github/workflows/build-native-libs.yml:102-107`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L102-L107) — `Windows version stamping`
- [`.github/workflows/build-native-libs.yml:156-160`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L156-L160) — `Linux version stamping`
- [`.github/workflows/deploy.yml:121-158`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/deploy.yml#L121-L158) — `version updates and release branch creation`

## Root cause
workflow_dispatch/workflow_call version strings are interpolated as ${{ inputs.version }} inside shell code before the shell parses it. Quoting the surrounding sed/git command does not make arbitrary GitHub expression text safe.

## Impact and preconditions
A crafted or malformed version may alter shell execution or corrupt manifests. Dispatchers are authenticated repository actors, so this is not an unauthenticated pull-request exploit. Release jobs also expose privileged credentials, increasing the value of a separate release-input boundary.

## Supporting evidence
- Expressions are present literally inside sed double-quoted programs and branch/commit command text at the cited baseline lines
- No malicious workflow input was sent to GitHub during this audit

## Recommended solution
Pass version via an environment variable, validate a narrowly specified version grammar before all use, and use TOML-aware updates or safe arguments rather than string-built shell code. Require explicit owner approval for publication. Migration disables/removes the unsafe release paths; do not restore them unchanged.

## Risks and compatibility
Version grammars must deliberately handle snapshots/prereleases without permitting arbitrary shell/sed metacharacters. Removing old workflows is mitigation, not proof a future release workflow is safe.

## Required tests / acceptance criteria
- Validate accepted semantic version/prerelease examples
- Reject command substitution, quotes, newlines, sed delimiters, branch path traversal and empty versions
- Exercise stamp/update helpers against temporary manifests without any credentials or remote publication

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)

## Migration remediation (baseline finding retained)
The inherited version-interpolating publication workflow is removed from active workflows and retained only as historical data. Current workflows accept no release/version shell input; Actions are restricted to explicitly pinned read-only verification and disabled outside supervised runs.

Verification files:
- .github/workflows/gradle.yml
- .github/workflows/build-native-libs.yml
- scripts/migration/verify_migration.py

Remaining caution: Any future publishing implementation must validate input through environment-safe argument handling; do not restore the archived workflow unchanged.
