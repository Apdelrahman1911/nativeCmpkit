# Android default-Coil decode candidate — 2026-10-31

**SOURCE PROPOSAL ONLY. ZERO Kotlin compilation, APK builds, Android/emulator,
default-Coil/BitmapFactory/EXIF/native/consumer executions or CI dispatches here.**
The lead owns integration, fresh input selection, serial compilation, immutable
native requests, original-criteria/results review and any GitHub mutation.
No issues are closed and no release/security/ABI/legal gate is cleared.

## What is frozen

- `patches/repaired-native-test.patch`: one new 370-line library-level Android
  class with three JUnit methods; includes the independently reviewed minimal
  bitmap failure-path cleanup repair. Source SHA256:
  `16081265d0b06b2f109c29fe0361c130a5bb5b49cfbc63c7301ce9155f408f7a`.
- `patches/repaired-new-modeled-guards.patch`: 18 original source/model guards
  plus one owning guard. Source SHA256:
  `e8e0cda7aacea25347e355d741ad8404de720e24faec5868a90f3e74addbb894`.
- `patches/finite-adapter.patch`: **unchanged** reviewed four-file finite adapter,
  rebased onto the lead's camera Dont-keep hooks. PATCH SHA256:
  `1ddf07d72cb85a4cfcccd759ab150a24efe8863d13a4089ba6d672635e657a5c`.
- `patches/owning-recovery.patch`: provenance delta only, not an extra patch to
  apply after the repaired new-file patches. Reverse it in memory to reconstruct
  the original red source/18-guard proposal; SHA256:
  `e5cb7043876217bc30ddddc32740162b84243a2592dc71992d7b9e359ec3627b`.

Source and patch hashes are distinct. `manifest.json` freezes the shipped payload;
`manifest.sha256` anchors that local manifest. Neither authenticates a publisher.
`records/source-freeze.json` retains the saved selected preimages/postimages,
protected-source identities and original input-schema scope. It is not a current
worktree/build receipt. The old author 1012→1014 input digests precede the owning
repair and must **not** be used as final repaired/runtime input identities.

## Actual saved modeled results — do not add overlapping runs

| Saved stage | Methods and result | Boundary |
| --- | --- | --- |
| Author original proposal | 18/18; unittest 0.331 s | Python/source/plan/synthetic receipt guards; initial adapter before camera rebase |
| Camera-rebased owning controls | 3/3; unittest 0.025 s | Overlapping subset of the same 18, not three new guards |
| Reviewer new owning guard: original source | exit1; one method/two PNG-JPEG subfailures | Process wall 0.065902 s; source-structure red only |
| Same new guard: repaired source | exit0; 1/1 | Process wall 0.064054 s; source-structure green only |

Both reviewer unittest elapsed values are 0.001 s. The standalone driver and
native/guard source hashes are retained. The earlier 18 methods/imports/setup/
helpers are AST-identical after the repair; they were not rerun by the reviewer
or archive assembler. **There is no fresh final-source 19/19 result.** Existing
five I/O lifecycle methods, helper, accepted oversize/host/native suites were not
requested or replayed. `red001/summary.json` preserves the failure categories and
original private-log hash without machine paths, source-body/local-value dumps or
traceback frames. Author stale-preimage and count-schema refusals remain in
`records/refusals001.json`; neither was a native/compiler failure.

## Confirmed candidate-only cleanup finding

`COIL-DEFAULT-CANDIDATE-001` — **Low**, original new native test lines80–82 and
125–127. A successful decode returns a test-owned bitmap; `dataSource` and
`isSampled` assertions ran before entering its deterministic recycling scope.
An assertion failure skipped that scope. Pinned Coil `RealImageLoader.kt:167–172`
shutdown cancels/clears references, not uncached returned bitmaps. Eventual GC is
possible: this is a confirmed **test failure-path ownership gap**, not a permanent
production leak or an observed native failure.

The repair moves the same two assertion statements into the existing bitmap
blocks. All 370 lines, nonblank stripped-line multiset, conditions, values,
public signatures, image geometry, decoder/source/grants and timeouts remain.
The new lexical guard red/green does not execute bitmap disposal, native GC or
heap profiling. No additional production defect is confirmed by this review.
Full root cause, impact, repair, risks and required tests are in
`records/findings.json` and `records/repair-applicability.json`.

## Three new native methods — still uncompiled and unexecuted

1. `defaultPngDecodeStreamsUnknownSizeBinaryAndPreservesEveryPixel`: native
   seeded257×193 PNG encode; actual separate-process **same-UID** FileProvider
   returns an explicit unknown-size binary row. Real source-only fetch/REG FD,
   non-consuming16-byte peek and partial encoded buffering are observed before
   the default decoder. Every opaque/transparent output pixel, dimensions/config,
   source bytes, DISK/unsampled result and ownership must pass natively.
2. `defaultJpegDecodeReplaysBoundsAndExifForRotationAndReflection`: native96×64
   JPEG and platform EXIF6/7 writes; independent64×96 quadrants test clockwise90
   rotation and reflection with RGB interior tolerance12. This verifies default
   buffered bounds/EXIF replay, **not kernel lseek or metadata ImageDecoder**.
3. `repeatedDefaultCorruptDecodesReleaseActualCrossUidDescriptors`: unchanged
   separate-UID helper, actual framework tree grant/bookmark and default loader;
   four actual corrupt decode errors must retain UID/PID/generation ownership,
   monotonic opens/closes, zero reporter FDs/errors/writes and owned cleanup.
   No injected decoder/manual grant or whole-corrupt-payload parity is claimed.

These are three methods with seven bounded image requests **if fully reached**;
seven is not an observed native execution count. Caches are disabled; tests use
explicit IO scheduling. No concurrent cancellation, process death, live cloud,
minimum/physical/vendor, peak-memory or request-key/invalidation claim follows.

## Pinned implementation correspondence

The unchanged catalog selects Coil3.6.2. Saved135520-byte source classifier SHA256
`06e9c9fa5dd76221ad3bbc936c6681288185bfeae012ff84cc5600658d213e2c`.
`records/pinned-source-correspondence.json` preserves exact selected entries,
source hashes and original public origin URL, **not raw classifier/classes**.
Saved-source matching is not authenticated publisher/runtime/compile/security or
licensing evidence. AndroidX EXIF bytecode orientation observations are read-only;
its original provenance and actual runtime class binding were not authenticated.

| Exact source | Reviewed flow / important limit |
| --- | --- |
| `KmpFileFetcher.kt:37–57`; `KmpFileSource.android.kt:8–10` | Actual blocking ContentResolver stream→kotlinx-io/Okio buffered source-only ImageSource, DISK, construction-error closure; consumer owns scheduling |
| Coil `RealImageLoader.kt:55–62`; `RealImageLoader.android.kt:87–108` | Additive user fetcher; default StaticImageDecoder before BitmapFactoryDecoder on API29+. Service-loaded components remain possible; actual decoder identity must pass |
| `StaticImageDecoder.kt:109–167`; `ImageSource.kt:141–176` | Plain source/null metadata/no existing file falls back to BitmapFactory; passive fileOrNull does not stage a file |
| `BitmapFactoryDecoder.kt:39–88`; `ExifOrientationStrategy.kt:40–48`; `ExifUtils.kt:21–69` | Separate non-consuming bounds/EXIF peeks, actual source decode/closure/default null-bitmap error; horizontal flip before clockwise rotation |
| `EngineInterceptor.kt:115–145,168–175,197–208` | SourceFetchResult closes in finally on actual success/error, and on failing fetch observer; errors do not fabricate decodeEnd |
| Candidate witness/pipeline:178–236; cleanup:247–280,321–365 | Observational listener/fetcher only, calibrated native REG ownership and deterministic bitmap/source/bookmark/endpoint/directory cleanup preserving primary errors |

## Integration/request discipline

Apply only the two **repaired** new-file patches and the unchanged adapter; do
not also apply the owning provenance delta. Recheck all adapter preimages and
freeze the current selected sources after integration. Reuse only applicable
unchanged helper/accepted evidence; no duplicate accepted-suite replay.

The finite `android-io-default-decode` profile admits one API35/calf-io/exact-class
slot and exactly three unique methods in **one fresh XML** with the actual task
marker. Missing/duplicate/foreign/failed/skipped methods refuse green. API23 is
refused for this focus; all11 full slots/eight Android modules remain. The unchanged
helper source/APK bytes/private signer/certificate/API35-only receipts remain
mandatory before reporter compilation/native work. Runner120000ms and owning
controller1800s deadlines and failure-safe cleanup are unchanged.

Lead next: serial reporter compilation on freshly held inputs, then exactly these
three actual API35 cases when a heavy slot is available; retain failures and
recover only failed/unexecuted new cases. Do not use the sample app as verification
or relax native/ownership requirements. No dependency/version/API/package/history,
Actions SHA policy/permissions/Pages/main/publishing/release gate changes.

## Verification and limits

From this archive directory, `python3 verify.py` performs only offline SHA256,
strict in-memory diff reconstruction/reversal and Python AST correspondence. It
never imports/runs the proposed models, calls Android/Coil, compiles Kotlin or
applies a patch to the repository. Its JSON output is the saved
`verification-result.json`; the checksum manifest excludes its own anchor and
receipt to avoid self-reference. Receipt integrity is tied to its manifest hash,
not an authenticated runtime builder.

#57/IO-021 remains open for per-target peak-memory, stable key/modified-file
invalidation, cancellation, scheduling guidance and broader target/consumer
criteria; original exact finding/requirements/upstream links are retained.
#55/IO-019 is broader than this same-UID unknown-size row; #45 and other provider
criteria are not automatically resolved. All native/consumer/API-ABI/dependency/
legal/security/readiness and release/publishing restrictions remain.
