# Coil caller-revision memory-cache policy — patch613 / runtime615

Issue **#57 / IO-021.C4** only. **#57 remains open:** IO-021.C1's per-target
large-image peak-memory benchmark is not provided by this small cache regression.
No previously accepted failure/cancellation/parity/guidance/native tests were rerun.

## Source custody

- Isolated worktree: `/root/nativecmpkit-worktrees/coil-cache-policy613`.
- Branch: `development/batch-coil-cache-policy613-20261104`.
- Base: `eed200402458fceed7082e1ddba27b2f683c8bd6`.
- Exactly four authorized files: the new desktop test, the owning module's
  test-only Gradle runtime block, `docs/development/IO.md`, and the additive
  `docs/modules/io-and-file-picker.md` header. The latter's baseline body is unchanged.
- No production fetcher/keyer/decoder/public API/version changes. The existing
  `compose.desktop.currentOs` selector is added with **desktopTest `runtimeOnly`**,
  not published as a library consumer's host-classified dependency.
- The diagnostic614 test/docs are byte-identical at runtime615. One exact Gradle
  fragment inverse recovers the entire pre615 build file.
- All **1,348 actual selected inputs** are identical before/after runtime615.
  Digest: `0f57b9e1928f44c5344da2733cf5b2804f226033f36fcb2ea894ba53f61c2834`.

## Original executions, kept distinct

| Original | Exact new/failed method | Result | Bounded elapsed | Interpretation |
| --- | --- | --- | --- | --- |
| 613 | 1 | 1 failure; exit 1 | 40.01 s | `ErrorResult` reached an `assertIs<SuccessResult>` assertion. Its underlying cause was not retained and remains unknown. |
| diagnostic614 | 1 | 1 failure; exit 1 | 32.01 s | One observation-only change preserves the actual throwable: `ExceptionInInitializerError` → `LibraryLoadException`, missing `libskiko-linux-x64.so.sha256` at the default Skia decoder. No cache behavior accepted. |
| runtime615 | 1 | **1 passed**, no failure/error/skip; exit **0** | **35.01 s** | Test-only host native runtime correction; six actual requests and all cleanup assertions complete on Linux x64/JVM/Skia. |

Each original has its own bounded log/result, exact source maps, reviewed receipt,
and once-preserved XML/source archive. Do not replace or relabel 613 with 614's
cause, or either failure with the later success.

Runtime615's fresh XML timestamp/mtime lies inside its own bounded wrapper window;
`library_tests.junit_cases` verifies the one exact method and declared counts.
Fresh XML SHA-256:
`309a4141c1ea1574e8df7d2759fcdf4a4da2bb5b429d19c88e0a95640cb8e2bd`.
The original method's JUnit time is 0.339 s; this is **not a memory benchmark**.

## Actual accepted scenario

An owned 8×6 real PNG and its different, **equal-encoded-length** replacement use
an application-namespaced content identity with caller-owned revisions:

1. Revision 1: actual default `SkiaImageDecoder`, DISK fetch, original pixels.
2. Fresh file wrapper / revision 1: MEMORY_CACHE hit and the same image.
3. Same-path equal-length replacement with intentionally stale revision 1:
   MEMORY_CACHE returns the original pixels. This demonstrates the policy's
   boundary, not automatic file invalidation.
4. Revision 2: DISK/default decode returns replacement pixels and a distinct key;
   the old cache entry remains until its exact returned key is removed.
5. Unknown revision, original bytes: fresh DISK decode, null cache key.
6. Unknown revision, replacement bytes: fresh DISK decode, null cache key;
   existing revision-2 cache entries remain unchanged.

Four real fetch/decode pairs and two cache hits are witnessed. Every returned
bitmap pixel is asserted. No custom decoder/keyer/mapper/interceptor is injected.
Transferred `ImageSource` and its original `BufferedSource` are closed after each
fresh decode. Linux additionally witnesses exact owned device/inode descriptors
**0 → 1 → 0**; unavailable procfs is a failure, not reported as zero. The method
returns only after clearing its owned cache, shutting its owned loader, closing
unique native bitmaps, verifying descriptor balance, and deleting its owned file.
The source keeps cleanup failures/suppressed exceptions. Other JVM hosts can
exercise source closure, but do not inherit Linux descriptor evidence.

Docs require a new revision after every mutation/replacement (including equal
length), coordinated mutation/request ownership, and output-changing variant
options in the key. Unknown revisions disable memory caching even if a custom
keyer exists. Keys are not access-grant, temporary-copy lifetime, readability,
old-entry eviction, or disk-invalidation contracts.

## Runtime prerequisite and warnings

The locked Coil JVM metadata supplies the Skiko API, not the host native runtime.
The existing Compose 1.12.0 Linux host selector supplies
`skiko-awt-runtime-linux-x64:0.150.1`. The exact cached declared runtime jar contains
both `.so` and `.sha256`; its SHA-256 is
`920c1cb033abfb79202f9f455fb86491bec5e45c156f186c0125b10fce97e093`.
The earlier passive inspection also saw a **different cached 0.150.2 jar**; its
preserved observation is not relabelled as the selected 0.150.1 execution input.
This correction supplies a test prerequisite, not dependency-trust or packaged
consumer acceptance.

Runtime615's production **and test compilers are UP-TO-DATE**: zero fresh compiler
executions. Its unchanged test compiler result is reused from diagnostic614.
Four current host native-disabled/cinterop warnings are preserved. The historical
line-115 `ExperimentalCoilApi` opt-in warning from 613/614 remains uncorrected;
it was not freshly printed by the UP-TO-DATE compiler in 615. No warning waiver is
inferred.

The authorized failed-method-only command was offline, no-parallel, one worker,
with 8 GiB reserve; before/after free bytes were 11,298,160,640 / 11,296,305,152.
The lead was notified immediately after the terminal poll to release the serial
heavy slot. No automatic retry, online fallback, subsequent heavy execution,
GitHub mutation, hosted dispatch, integration, push, publication, or issue closure
was performed by this child.

## Evidence and limitations

- `runtime-review615.json`: **28 passive source/result checks**, actual command,
  counts, freshness, warnings, scope and source hashes; not 28 runtime methods.
- `runtime-inputs-before615.json` / `runtime-inputs-after615.json`: actual source
  custody for this execution, not historical compiler/native maps from another run.
- `runtime-correction-delta615.json`: 10 accepted passive correction controls;
  `diagnostic-delta614.json` preserves the observation-only inverse separately.
- `original-runtime613/`, `original-runtime614/`, `original-runtime615/`: exact
  distinct originals. Accepted previous source controls are reused, not reexecuted.
- `source-controls613.py` preserves its original three-file domain and therefore
  is not rerun against the later four-file scope. `review-runtime615.py` is the
  passive reviewer for the actual recovery scope, not a test runner.

No Android/browser/Apple cache runtime, large-image memory profiling, native UI,
minimum-API/device/consumer/API–ABI/release-readiness or dependency/legal/security
clearance follows. All corresponding gates and the lead's integration review remain.
