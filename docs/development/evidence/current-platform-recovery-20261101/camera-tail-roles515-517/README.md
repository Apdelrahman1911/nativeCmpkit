# Camera recent-task observation batch — 2026-11-03

**No camera issue closure or new native pass.** The original
[41706153561](../camera-recents-original502-505/README.md) remains failed before
Gradle/APK/native work. Both ongoing iPhone/iPad requests retain their own
`570edb509a62b6e85502edc8932340389e7caaa8` inputs; this batch is not their source.

## What is established, and what is not

- Original row 5's 15-byte SHA-256 is an exact match for the public literal
  `  Recent tasks:`. Row 6/7 fingerprints alone do **not** identify task contents,
  their ownership, an OS producer or a safe prerequisite exception.
- A read-only acquisition of Android's `android-15.0.0_r1` `Task.java` is held at
  SHA-256 `7892b50f8f82043e1d42f51385f574586489626aedb4706cc9a4632ed5c6ee15`.
  `Task.dump:3798–3903` and `Task.toString:3933–3953`, together with the previously
  held `RecentTasks.dump:1865–1978`, describe row templates. The package filter
  also considers the calling package. **This is not installed-image provenance
  or an explanation of the original task.** Acquisition metadata is archived;
  no second original download or dump reconstruction was performed.

## Changed implementation

Only `scripts/ci/android_camera_recents_observation.py` changes. Its new
`tail_structure` observes the **same already-returned query from the genuine
refusing parser frame**. It reports fixed row-role/type/identity-match counts,
fixed component matches, an empty-activities count and nullable single
header/dump-ID equality. It never exports actual IDs, callers, components,
intent bodies, paths or unknown rows.

The whole-tail limit is 64 rows; each row is at most 2,048 UTF-8 bytes, inside
the original 16-KiB query bound. Exhaustion is explicitly unavailable, not
partial/zero/absence. Bounds are cooperative, not hard deadlines. A matched
HOME/standard shape is **not** a complete task parser, ownership decision or
authorization to ignore/remove that task.

The original `recents_refusal` function is AST-identical after removing its one
new output entry. All original query identities, unsafe-byte refusals, compound
operands, primary exception and optional-observer error handling remain.
`android_camera_developer_prerequisite.py`, `android_device_tests.py` and
`OwnedDeveloperSettingsUi.kt` are byte-identical to their owning Git preimages.
In particular, Python `parse_recents:319–330` still requires an empty filtered
list; Kotlin `openSettings:130–168` still refuses pre-existing/competing recent
and live Settings tasks and owns only a nonce-bound exact new task. No purge,
namespace guess, parser normalization/retry, Settings mutation or waiver.

## Important checks and review

1. NEW eight method obligations first fail at the missing observation field:
   **8 methods / 15 error records / 0 passes**, 0.010 s. This is a synthetic
   regression, not an Android reproduction or acceptance.
2. Only those failed eight plus two affected existing bounded/privacy/source
   checks run once after implementation: **10/10 PASS**, 0.016 s
   (wrapper 0.016155819 s). Successful older native/control populations were not
   replayed. There are **zero Gradle/native executions**.
3. **19 passive source/results checks** accept the owning unchanged contracts,
   one additive call, unmodified imports, red/green provenance and **1,296 held
   library inputs**. Red-to-green only the existing observer changes; the new
   test source is identical across both checks. This is source/results review,
   not another executed test population or release/security certification.

Files: `red516.json`, `green516.json`, `review517.json`, `source-before.json`,
`held-inputs.json`, `archive.json`, and the AOSP template acquisition receipt.
The archive removes only repository absolute-root prefixes from text reports;
original and archived SHA-256 values are explicit.

## Next and unchanged gates

After capacity frees, freeze/push and request **only the missing C1 method** with
these new observation bytes. Do not retry the unchanged failed request or replay
accepted camera009 C2/C3. Qualify the actual structural observation and an
ownership-preserving solution before changing either owning prerequisite.
Counts remain **103 closed /69 open /172 total**; no package/release/deployment.
SOLO, serial local heavy work with 8-GiB reserve, maximum two combined hosted-heavy
reservations **including queued work**, read-only Actions/all/no mandatory SHA
pinning, and all main/history/Pages/native/consumer/API–ABI/dependency/legal/
security/readiness/publication gates remain.
