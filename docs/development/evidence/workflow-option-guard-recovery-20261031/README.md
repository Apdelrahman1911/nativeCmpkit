# Workflow-choice guard recovery — 2026-10-31

Both immutable attempt1 requests at `540c1c1e` remain **FAILED**:
[default Coil41249622333](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41249622333) and
[help-only Apple41249673735](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41249673735).
Each CI batch executes1301 methods:1300pass/one failed, before any Android native
or Apple SDK command, with zero artifacts. This is not a decoder or SDK failure.

Exact source: `scripts/ci/test_ios_image_darwin_focus.py:171` at the original
revision. The guard incorrectly requires four options to remain contiguous;
the independent `ios-appinfo-capability` insertion separates the last pair.
Only this guard changes: the existing strict literal-list parser plus individual
required-token membership preserves every original native mode and rejects
missing/duplicate/computed/multiple lists. Permissions/native tests/workflow/
profiles/expected cases and all11 slots/eight Android modules remain unchanged.

The repaired owning method passes1/1, exit0/0.189s. Eleven modeled variants
separately retain ten refusals and accept literal reordering; these are not eleven
new distinct library methods or native results. The accepted1300 models were not
locally replayed.1018 library/1095 combined hashes differ from the accepted
reporterAPK0/156.03s and3/3 Yarn JVM result only in this guard; compilation and
those original outcomes are reused, not rerun or promoted to device tests.
The initial pre-freeze reader dictionary typo failed at parsing before evaluation;
it is retained separately and is not a source/CI/native result.

Next: unchanged three-case API35 default decoder request and unchanged fixed
help-only Apple capability request on a fresh immutable revision. No appinfo
payload, simulator inventory/boot/install/launch/profile is justified. #45/#55/
#57/#141 remain open;91closed/81open. All publishing/Pages/main/history/native/
consumer/API-ABI/dependency/legal/security/readiness and capacity gates remain.
