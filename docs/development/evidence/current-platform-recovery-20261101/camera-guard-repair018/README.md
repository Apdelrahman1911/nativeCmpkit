# Camera actual017: minimal owning guard repair

Private integration proposal, immutable base
`55b1a8c361e0b6445e95df989f238310ca0a3eb0`.
Only `scripts/ci/test_android_camera_documented_data_default.py` is proposed,
and its entire source delta is one exact `BASE_MODULE_AST_SHA256` literal:

- Old: `16e759fc9e1aee42135199be886f8d18553e5264288cb4e0435448d7ae860c2e`
- New: `d4962dd7a931e14522ab8d2cca15700cf0790fad45719793aa5db6e6af88d400`

The new value is the once-acquired actual017 whole helper-module AST after
removing the single exact documented-default branch. The observed mismatch is
retained from the sealed actual review; no local baseline rerun or reacquisition
occurred. Before/after normalized canonical AST files verify both exact hashes.
The sole helper AST delta underlying this advance is the four failure observation
lines plus the exact approved `require_call_origin` helper at the immutable base.

Every original test method body, whole-module assertion, fixed-launch assertion,
`BASE_LAUNCH_AST_SHA256`, helper, native and controller code stays unchanged.
No observer or native code is stripped from the real hash guard. The existing
full-module hash now requires the exact observer, so no additional committed
negative guard is needed; the proposed maps retain 1,105 / 1,182 inputs with only
this test file's hash changed. Those maps are private proposed identities, not
an uploaded actual native map or a claim about live HEAD.

## Only affected/new local controls

The actual failing owning method passes once on the final test postimage.
Eight distinct new private AST changed-input controls pass once and refuse:
observer removal; four-line observation removal; changed frame bound; changed
public filename; ValueError replacement; original exact cleanup-state weakening;
changed documented-default pair; and fixed-launch userdata override.
Mutant ASTs are never imported or executed. The controls are not proposed as
repo files and do not expand committed selection or alter production code.
Eleven source-only checks pass; their method/source/AST preservation evidence is
bound to the final postimage. No controls are rerun while sealing.

The seven accepted documented-default fixture cases and accepted 1,810 CI
remainder were not run. No live project module was imported. Python used `-B`;
no SDK, build, native, browser, install, dispatch, Git/GitHub mutation or live edit
occurred. Actual017 remains FAILED before native. Its original Dont-keep method,
new bounded failure callsite, native receipts/XML and owned cleanup remain
unexecuted. Earlier actual016's unknown predicate is not diagnosed.

## Integration

Require the exact preimage hash before applying the one-line `source.patch`.
Lead owns independent review, integration and any finite verification request.
This local guard pass does not authorize native acceptance, issue closure,
publishing, Pages, branch/history/security/readiness changes or dispatch.
Raw actual run logs remain privately retained outside all deliveries.
Payloads and manifest are read back and sealed files 0400/directories 0500.
