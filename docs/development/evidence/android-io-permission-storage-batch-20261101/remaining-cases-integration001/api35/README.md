# Fixed API35 permission/storage recovery proposal

Profile: `android-permission-storage-api35-recovery`.

Exactly three existing routes, in order:
1. `android-permission-demo`
2. `android-storage-api35-normal`
3. `android-storage-api35-all-files`

These retain exactly five original API35 native method identities and exclude
`android-io-reference-regressions`. The new profile uses the existing generic
batch dispatch, one existing API35 host slot, `calf-permissions/core`, and only the
existing SDK tools plus the API35 system image. Original batches and all eleven
full slots are preserved. No controller, runner, helper, fixture, production API,
existing test or native assertion is changed.

## Integration

Use the eight `fragments.json` literals, each exactly once against the held
preimages in `manifest.json`, plus the one new focused test. Target repository
modes are `100644`; private delivery files remain `0600`.
Do not replace the three shared files wholesale: the manifest distinguishes the
own-profile postimages from the composed recovery/media/DNS shared postimages.
No conventional shared-YAML patch or new native execution is implied.

## Fresh source-only verification

- Two selected new guards are red on the unchanged baseline: one missing-profile
  KeyError and one absent-SDK-branch assertion. These are expected feature-absence
  controls, not diagnoses of any hosted/native failure. Raw traces stay private.
- All six genuinely new focused source guards pass once on the three composed
  shared-file postimages: 6/6, no failures/errors/skips, 0.056777 seconds. The
  original passing XML and held-input receipt are included unchanged.
- Static exact-literal composition covers recovery8 + media8 + shared DNS4
  fragments. All six group application orders agree, every anchor is exact-once,
  own reverse reconstruction returns the exact baseline, and the own Python AST
  differs only by the new profile declarations. Unrelated DNS files are excluded.
- Existing native fixture bodies were not executed. Permission identity metadata
  is parsed as AST data; only declarative storage/batch metadata and the unchanged
  matrix function are exercised. Media/DNS/accepted suites were not replayed.

No broad maps, real preflight, Git/API/network operations, builds, SDK/AVD/native
execution, live writes, verification requests or issue closures were performed.
This is a private source proposal; the lead owns final composition/freeze,
requests and acceptance. Existing failures and issue gates remain unchanged.
