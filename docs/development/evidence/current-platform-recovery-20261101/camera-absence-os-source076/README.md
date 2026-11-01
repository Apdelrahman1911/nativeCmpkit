# Android 15 Settings dump source-only review

## Decision

**Keep the current strict all-Activity absence gate and original refusal. No command or parser patch is qualified.**

- Immutable camera caller already uses correct leading `-p com.android.settings` for activities/recents. Processes intentionally remains global.
- Official Android15 reference code can print matched ActivityRecord bodies **and** `(nothing)`: TaskFragment/history-list producers discard returned printing booleans. Footer-only absence is unsafe.
- A matching record can include unrelated ActivityRecord references/client output. The original three marker rows identify neither Settings ownership nor root cause.
- The genuine reference no-match branch is exactly header + traversed Display rows + footer. Current reader accepts its expected nonzero-display subset and refuses every body/blank/unknown row. No harmless-global-body or blank-row allowance follows.
- `a` is plural activities alias. Literal `activity` is arbitrary selector. Direct `com.android.settings/` has a small reference server-side no-match branch, but leaf/component-only traversal lacks proved equivalence to the current full hierarchy + independent finishing/stopping domain. **Not qualified as replacement.**

## Evidence and scope

Official `android-15.0.0_r1` framework and modules-utils tags are byte/hash archived privately; exact URLs, transport records, source notices and excerpts are in this public-safe packet. These tags are reference sources, **not proved source identity for the actual Google APIs image revision9**. No original build fingerprint/source revision was observed.

`COMMAND-INVENTORY.json` binds every dumpsys/stack read in the immutable camera prerequisite/native Settings/always-finish helpers and passively checks the camera controller/receiver/batch paths for additional dumpsys calls. `SOURCE-EXCERPTS.json` records exact filter, traversal, producer-boolean, selector and fallback paths. `PASSIVE-BINDING-READBACK.json` is integrity/source binding only, not tests. `UNEXECUTED-CONTROLS.json` contains20 future finite controls: **zero executed**.

Original run41293310255/attempt1/e16268a68e6582a4cceeed3c18335789d99646d0 remains **FAILED, ZERO native methods/markers/XML/native Gradle invocations**. Its original prepare298/cleanup984/require48 refusals,218.06s assembly,1.0s AVD creation and independently graceful owned disposal are preserved; disposal does not compensate failed prerequisite cleanup. Raw rejected row, Settings liveness and cause remain unknown. No old originals reacquired.

No live edits, library tests, compiler builds, native commands, dispatch, Git/issue mutations, closure or release/readiness promotion occurred in this review. Missing #13 C1/Dont-keep remains; accepted camera009 C2/C3 are reused unchanged and never replayed. No destructive force-stop, broad parser waiver, immediate constructor deadline or new platform criterion. Lead owns any follow-on integration/verification. Named Actions remain authorized without mandatory SHA pinning; all publishing/security/legal/native/consumer gates remain.
