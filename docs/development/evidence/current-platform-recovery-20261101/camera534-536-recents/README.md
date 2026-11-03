# Camera boot recovery passes; recent-task admission still fails — 534–536

[41729467621](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41729467621)
at `34a5b35c178fba2571450a2c2699ce98565c7e76` remains **FAILED**, with **zero
Gradle/APK/native/XML executions**. The sole selected original method is
`AndroidCameraRestorationTest.nativeDontKeepActivitiesRestoresOneReadableCapturedFile`.
Its POST executed once; do not redispatch unchanged bytes.

The repaired busy-boot readiness path now succeeds: eight original read-only
observations /seven waits, including retained busy-header300 and interior307
refusals, followed by the unchanged complete strict Settings-activity absence
parser. Two startup observations and the original readiness hold also succeed.
These are prerequisites, not a camera test or a complete prepared lease.

Original capture then refuses at
`android_camera_developer_prerequisite.py::parse_recents:324`:

- All seven framing/scalar shape operands match; only `exact_tail` is false.
- The single returned query has 19 rows /14 nonempty tail rows /1,124 bytes.
- Failure-only bounded role counts show one HOME-shaped task, one fixed
  `com.android.settings/.FallbackHome` component row, empty Activities, matching
  task-header/dump IDs, 14 recognized roles and zero unknown rows.
- Identity shapes include user0/effective UID1000/caller UID0; no recognized
  caller-package token and no true setup flag. They are **not** full task parsing,
  installed-image provenance, ownership, safe-ignore permission or root-cause proof.

The strict parser only admits an empty filtered recent-task list. The library's
native `OwnedDeveloperSettingsUi` separately rejects all preexisting Settings
recent tasks and parses owned task headers as `type=standard`. Simply removing
the Python refusal would not repair the underlying baseline/ownership contract.
Do not purge or silently ignore the observed preexisting task. A safe repair
must preserve nonowned baseline identities and refuse foreign changes, or prove
another legitimate initialization contract; it must retain nonce-bound owned
task cleanup and every original native/scalar restoration check.

Separate cleanup1375 remains failed because no exact original snapshot was
acquired. No master write, restoration, reboot, reporter install or camera body
occurs. Independent identity-confined owned guest disposal succeeds; it does not
waive the failed prerequisite or cleanup.

Once-acquired originals: 32 log members /17 JSON report members. Forty passive
source/results checks verify all 1,304 actual inputs against this run's own Git,
artifact/archive/member digests, runtime, selection and independent disposal.
Ten tooling scopes pass 3,595 invocations, including 2,655 CI methods in156.405 s;
these are not native passes. Original emulator/system transcripts are not exported.

**#13 stays open**; camera009 C2/C3 are already accepted and excluded from replay.
103 closed /69 open /172 total remains, with no closure or publication. This
terminal reservation is freed; fresh all-status capacity still precedes dispatch.
