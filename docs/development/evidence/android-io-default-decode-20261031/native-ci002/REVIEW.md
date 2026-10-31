# Independent default-decoder source/results decision

**Accept exactly three whole API35 native methods. Keep #45/#55/#57 open.**
There is no failed/unexecuted method in this request to recover. Prior failed
runs stay failed; current unrelated dirty proposals are not verified by this run.

| Original method | Native acceptance | Important boundary |
| --- | --- | --- |
| `defaultPngDecodeStreamsUnknownSizeBinaryAndPreservesEveryPixel` | Default native PNG decode preserves all49601 pixels; actual unknown-size metadata does not open content; partial encoded buffering/source-only DISK/native FD1 then FD0 | Separate-process **same UID**; neither benchmark nor cloud/file:// acceptance |
| `defaultJpegDecodeReplaysBoundsAndExifForRotationAndReflection` | Two native EXIF6/7 JPEG decodes satisfy independent64x96 geometry/interior colors, actual default decoder and source closure | RGB tolerance12; not every orientation, internal-call logging, kernel seek or metadata ImageDecoder |
| `repeatedDefaultCorruptDecodesReleaseActualCrossUidDescriptors` | Four actual default null-bitmap errors; native cross-UID/real read-only tree grant; calibrated descriptor positive then FD0; provider opens/closes1..4, no errors/writes | Not cancellation/concurrency, whole corrupt-byte read, heap profiling, restart or every stage |

`source-assertion-review.json` provides exact production, provider, native
identity/grant, descriptor/calibration, cleanup and collector code locations.
`accepted-case-ledger.json` preserves each original method, immutable source
hash, source lines, XML duration and bounded acceptance. Each accepted method
counts once: internal requests or helper/reporter compilation do not add coverage.

## Why this is real default/native verification

The library ImageLoader adds only production `KmpFileFetcher.Factory`, not a
Decoder. Native event listeners check real `BitmapFactoryDecoder`, actual
`SourceFetchResult`/DISK MIME/no metadata/no staged file, real descriptor ownership
and exact success/error event counts. A16-byte `peek()` does not consume the
source. The native PNG encoder/EXIF writer and independent output geometry/pixels
are not injected decode results. The corrupt error has the default decoder's
actual null-bitmap origin; no synthesized error/cancel is substituted.

The helper's native control route checks the exact signature-protected owner,
Messenger sendingUid/nonces/PID/process/generation. Permission grant comes from
the real foreground Activity result and actual framework flags/ClipData, with
MANAGE_DOCUMENTS denied and initial URI grant denied. The local FileProvider
route checks same UID/different real provider process; do not call it cross-UID.
Regular-file stat device/inode and strict kernel fdinfo calibration back FD1/FD0;
remote close callback order and monotonic counters prevent reset/deletion from
concealing descriptor failure. Nothing here measures decoder/native heap leaks.

## Exact provenance/cleanup

Terminal exact-attempt GET metadata, sole artifact digest/size, full immutable
1018/1095 hashes, four actual1018 maps, source plans/marker/filter, runtime hash,
source-defined input/runtime fingerprints and original XML all agree. There is
**no actual uploaded combined1095 map** and no independent exported original-stat
or raw native UID/PID/generation record. Freshness acceptance is through immutable
passing collector/fresh-init/one-marker gates, not invented timestamp precision.

Actual signer inspection is strict36.0.0/API35-only; compiled content/permission
policy and own private certificate agree with installed/source APK identity.
Owned helper recheck/uninstall/absence, native endpoint/thread cleanup and owned
AVD graceful process/transport removal are mandatory and observed. Source-bound
normal cleanup succeeds; not every exceptional cleanup path is separately run.

## Original issue decisions

- **#45:** Earlier fixed Android release/revoke/secondary-client-restart subset
  stays accepted. Current corrupt method adds real grant/release prerequisites,
  not new restart/revocation coverage. Apple/iCloud scope/stale/save and public
  sandbox-local path requirements remain outside this run.
- **#55:** Earlier fixed folder metadata/restart/revocation/transient Binder
  death/recovery remains accepted. Openable PNG/JPEG metadata is not new
  system/cloud-folder, single-document/file:// or permanent-unavailability proof.
- **#57:** Current default errors strengthen source-failure ownership; PNG pixels
  and JPEG EXIF geometry strengthen binary/native compatibility. Earlier full
  fixed source parity and **injected** paused cancellation remain accepted on
 47 exact unchanged sources/declarations, without replay. Peak-memory-by-target,
  keys/invalidation and main-thread misuse guidance are unexecuted; default
  cancellation and broader targets/stages are not certified.

All16 original acceptance bullets and body hashes are retained. No whole-issue
closure, broader security/dependency/ABI/consumer/readiness waiver, new library
production fix, release or package mutation is justified. There is no basis to
retry this successful unchanged scope merely to obtain another green run.
