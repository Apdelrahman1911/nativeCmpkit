# Independent actual native008 review — tooling failure / zero native

- Run **41240921685/attempt1**, immutable **5e9cfdd1126ba535475f920bdbba827d72eed535**, completed **failure** at2026-10-31T20:54:07Z. Read-only observation21:03:07UTC matches exact ID/attempt/SHA.
- Only tooling ran and failed; all downstream jobs/profile selection skipped. **ZERO compiler/APK/native methods/XML/artifacts/native dependency-cache actions.** Runtime, installed receiver identity and owned device/app/ADB cleanup receipts were **not reached**, not fresh passes.
- Original tooling log: **1190 scripts/ci methods/1189pass/one fail**,0errors,67.272seconds. Separate preceding35/80/84 synthetic groups pass; none are native/library outcomes or additive replay credit.
- Sole actual failure: `DesktopSaverStateFocusTests.test_real_fixture_keeps_visible_Compose_JNI_writer_disposal_and_disclosed_parent_boundary`, `scripts/ci/test_desktop_saver_state_focus.py:149`.
- The guard expects `inputs.profile == 'picker-saver-state') && 1 || 2`. Actual immutable workflow:228 adds `|| inputs.profile == 'webview-content-transitions'` after picker while retaining **picker-saver-state serial1/default2**. This is a stale synthetic adjacency guard, not an Android camera launch/runtime/cache failure. No shared source/test/expectation repair or replay was performed by this reviewer.
- Original job log555539bytes/SHA256 **2bcccc4166fa452dbb89514d892cf00d9eb02c0c9d2b1be4b2a78403df63866c**; safely bounded read-only GET. Exact immutable failed guard/workflow copies and their hashes retained privately (`tooling-failed-source.json`). Raw log is private; use bounded public-safe facts/excerpts for lead archival.
- **#13/NATIVE-019 remains open**, original title/body/all three required criteria unchanged. No four-case result exists here; do not promote local compile, prior native007 installed/runtime evidence, synthetic flags checks or this static checklist into native008 acceptance.

## Original criterion / static source disposition

See `../native007/preflight008/original-criteria-checklist.md` and `.json`: all ten frozen/live/native008 immutable Git source blobs equal; every remaining original TakePicture intent assertion is compatible with the pinned cached AndroidX1.13.0 bytecode and Android15 framework source reviewed. No additional definite launch-contract mismatch found, no actually caught exception site inferred.

Genuine public launcher/ComponentActivity registry/save/Android grant migration/foreign descriptor/native result/kernel death/restored cancellation/owned cleanup gates remain. **All three criteria are still pending actual native review.**

- Rotation is performed and display orientation changes while external capture is native foreground; caller recreation/changed orientation is asserted only after terminal return. Do not claim immediate/in-held caller recreation. Android15 may defer stopped/invisible configuration checks. This is an exact acceptance wording limitation, not an observed failure.
- Genuine task enumeration/taskInfo reads can race with genuine terminal finishAndRemoveTask; Android15 may throw if a task has disappeared. Current fixture conservatively refuses unknown state. This is only a potential test-only race, not a native008 or native007 diagnosis; never silently accept unknown as task absence.

Details: `review.json`, timestamped original GitHub metadata, original bounded tooling log, immutable failed-source identities. Lead owns the smallest owning synthetic guard repair/fresh finite request/archival/any eventual original-criteria closure. No reviewer build/dispatch/accepted replay/GitHub mutation; no hardware/vendor/minimum/physical/API-ABI/security/release inference.
