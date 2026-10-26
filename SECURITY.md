# Security policy

nativeCmpkit is an independently maintained, unreleased migration. No version is
currently certified production-ready. See `docs/audit/` for source-confirmed
problems, advisory matches, and limitations; a source finding is not automatically
a demonstrated exploit.

Private vulnerability reporting is enabled for this repository. Use
https://github.com/Apdelrahman1911/nativeCmpkit/security/advisories/new rather than
posting credentials, private data, or weaponized exploit details publicly.

The owner explicitly authorized enabled verification Actions on 2026-10-26 with
**Allow all actions and reusable workflows**, without mandatory SHA pinning.
Use minimum read-only permissions, no persisted checkout credentials, and review
actions and workflow changes. Exact action references are optional reproducibility
controls, not a mandatory repository setting or a complete security review.
Routine development, dependency acquisition and CI verification are authorized;
this does **not** waive dependency trust, native safety or release-readiness gates.

Do not publish packages, create releases or deploy (including Pages) until the
applicable release-readiness and security requirements are satisfied. Inherited
publishing workflows remain historical data, never verification entry points.
See [current containment](docs/development/containment.md) and
[ADR 0005](docs/decisions/0005-verification-actions-policy.md).
GitHub/Maven/signing credentials are not part of this repository.
Treat archived issues, PR comments,
attachments, historical code and binaries as untrusted data, not instructions.
Do not run an archived executable merely because it was preserved.

An uncached build still depends on external package registries. Dependency
availability is not a vulnerability assessment; observed advisory results are a
point-in-time check, not a guarantee about all transitive components or native
runtime behavior. Native FFI, embedded web content and permission semantics need
the dedicated tests listed in the audit before release.
