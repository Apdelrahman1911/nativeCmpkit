# Windows development-index portability: original failure and owning correction

**2026-11-02, solo. No new library/native execution or issue closure.**

[Original41415588780](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41415588780)
at `7445615ba3a30500b706004f6975ef6d555bf727` fails before the public Windows
Stop test. SDK23 selection passes; `validate_resolutions.py --check` exits **2**
with both generated status indexes stale. Cache/plan/candidate/Gradle/native
steps are unreached. Evidence upload independently fails because no allowed
output file exists. All original logs/metadata are cached from one acquisition;
no archive is downloaded again or failed native result invented.

## Confirmed source cause and fix

`scripts/development/validate_resolutions.py::discover`, previously line168,
used `str(path.relative_to(root))`. Windows emits backslash paths, unlike the
canonical POSIX repository keys used on Linux. Identical ledger bytes therefore
produce different input sets/hash keys/fingerprints, baseline/owner paths and
Markdown links. Regenerating on the runner would hide the divergence and dirty
the checkout rather than fix it.

The owning correction is **`.relative_to(root).as_posix()`**, with no other
validator behavior changed. The index is regenerated once in development for
the changed generator hash; actual CI remains read-only `--check`. Structural,
stale-input/output, original-criteria and no-automatic-closure gates remain.

The workflow now creates allowed preflight output before SDK validation, records
the exact SDK package/presence and preserves the index check's log using `tee`.
The shell's existing `-e -o pipefail` still propagates rejection. Receipt uploads
include those logs, never JARs/classes/source packages. No permission increases,
runtime selector changes, default dependency adoption or publishing occurs.

## Important verification

- **286 NEW1 preimage red:** actual `PureWindowsPath` semantics emit the observed
  backslash inventory; the targeted test fails as expected. Source held.
- **287 failed1+NEW3 green: 4/4**, unittest0.040s/wrapper0.463594s; actionlint0.
  Actual isolated fixture JSON bytes and generated outputs are identical under
  controlled Windows/POSIX discovery. Ledger-byte/index staleness still refuses;
  the workflow records preflight failure evidence without a `--write` or
  continue-on-error path. All1,203 canonical library inputs hold.
- [288 source/results qualification](REVIEW288.json) accepts exactly the one
  owning conversion/comment delta and original red/green results. **Windows path
  views are controlled, not an actual Windows filesystem or hosted execution.**
  Actual Windows index acceptance and the original native Stop case remain next.

Previous27 candidate controls, Linux/Windows dependency-native4 and accepted
library subsets are reused, not replayed. Original285 and earlier native failures
remain failed. #64 stays open with its other Desktop/offline-browser, ordinary
adoption/legal/security/consumer/API-ABI criteria. Counts/statuses remain last
verified97closed/75open/172total and22implemented/42partial/95verified/five unresolved.

Scope is a CI/development tooling correction, not complete BUILD-006 or release
readiness. Continue solo; serial local heavy/8GiB and max2 combined hosted-heavy
reservations including queued work. No packages/releases/Pages/main deployment.
