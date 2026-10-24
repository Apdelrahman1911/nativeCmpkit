# Technical audit — IO, file picker/saver, and Coil

## Scope and evidence boundary

Baseline: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6` (imported upstream main).
The review covers **all 62 tracked files, 5,360 physical lines**, across:

| Module | Tracked files | Kotlin files | Original desktop tests | Lines including resources/comments |
|---|---:|---:|---:|---:|
| calf-io | 20 | 19 | 6 in one file | 642 |
| calf-file-picker | 38 | 32 | 9 in two files | 4,650 |
| calf-file-picker-coil | 4 | 3 | 0 | 68 |

The [module report](../modules/io-and-file-picker.md) contains every important
API, implementation flow, target distinction, native helper/export and a
**62/62 behavior-specific per-file ledger**. The
[structured findings](findings/IO.json) contain exact baseline paths/line ranges,
root cause, impact, priority, evidence level, remediation, risks, required tests,
effort and dependencies for each issue. This report is not a substitute for that
evidence.

**26 findings:** 5 High, 19 Medium, 2 Low; none classified Critical. There are
20 confirmed findings (17 source-confirmed, 3 executable reproductions), 5 risks
requiring platform/deployment verification, and 1 improvement. No production
source fix was made as part of this area audit. No release/package was published.
An absence of a Critical classification is not a security certification.

### What was actually executed

* **15/15 original baseline JVM tests passed** with unchanged extracted source,
  real PlatformContext expect/actual, Kotlin 2.4.20, kotlinx-io 0.9.1 and
  coroutines 1.11.0. No platform stubs were used in this run.
* **10/10 additional characterization/positive probes passed**, compiling the
  actual desktop cache/Jodd/file-writing source with a **mocked native dialog**.
  These checks intentionally confirm existing bugs; “PASS” does not mean fixed.
  They were repeated with installed Kotlin 2.0.21 and 2.4.0 runtimes. The saved
  probe log records the 2.4.0 run.
* Lead-run GitHub Actions native validation completed on Windows, macOS and
  Linux. Its archived run/job conclusions and native log were inspected: the
  file-picker crate builds/tests complete successfully but run **zero Rust test
  cases**. This verifies compilation, not native UI/lifetime correctness.
* Full local Gradle desktop execution was attempted by the build reviewer, but
  disk headroom and missing offline artifacts prevented a full Gradle test
  verdict. See [build/security](build-security.md) and
  [test evidence](../testing/io-and-file-picker.md). Later central CI results
  should be read from the central testing report; do not turn these scoped
  results into an all-platform pass.

No iOS device/simulator, Android Activity/SAF provider, real browser/FileReader,
Coil decode/cancellation, native dialog, ASan, Valgrind or native parent-window
race was exercised in this review. Those limitations are explicit even where
the source proves an unsafe branch exists.

## Findings index

| ID | Priority | Evidence status | Finding |
|---|---|---|---|
| IO-001 | High | confirmed-source | iOS byte-array reads can overrun native destination memory and mishandle empty files |
| IO-002 | High | confirmed-source | Android saver loses pending content across recomposition and can report an empty export as success |
| IO-003 | High | confirmed-source | Desktop composition disposal races raw JNI handles; cancelled creation can leak handles |
| IO-004 | High | confirmed-test | Desktop save can delete its own source and does not reliably replace existing content |
| IO-005 | High | confirmed-source | iOS saver exports the original source with move semantics and ignores requested file names |
| IO-006 | Medium | confirmed-source | Save write failures can report success or escape without a completion/error result |
| IO-007 | Medium | confirmed-source | iOS picker completion is not exactly once and document swipe dismissal is not observed |
| IO-008 | Medium | risk | Picked-file access lifetime is not represented for security-scoped folders or persisted Android URIs |
| IO-009 | Medium | confirmed-source | Browser file reads treat DONE as success and do not cancel or propagate FileReader failures |
| IO-010 | Medium | confirmed-source | File-kind queries misclassify extensionless browser files and nonexistent paths |
| IO-011 | Medium | confirmed-source | Web saver accepts onResult but never calls it or exposes download-only capability |
| IO-012 | Medium | risk | Immediate web Blob URL revocation can race the browser download |
| IO-013 | Medium | confirmed-source | iOS picked-file copies have no ownership cleanup and are created before result limits are applied |
| IO-014 | Medium | confirmed-source | Portable path/name metadata exposes encoded or unreadable references instead of the readable file |
| IO-015 | Medium | confirmed-test | Desktop MIME filtering omits modern image formats and silently disables unknown custom filters |
| IO-016 | Low | confirmed-test | MIME lookup is locale-sensitive, parses only comma-space lists, and allocates per entry |
| IO-017 | Medium | confirmed-source | Some remembered launchers retain stale selection limits, image representation and parent windows |
| IO-018 | Medium | confirmed-source | Multiple selection accepts invalid limits and differs across platform fallback paths |
| IO-019 | Medium | risk | Android folder selections are wrapped using single-document metadata and stream-based existence |
| IO-020 | Medium | confirmed-source | Android whole-file read leaks its input stream if reading fails |
| IO-021 | Medium | improvement | Coil fetches eagerly copy whole files and the byte-array API needs explicit scheduling/size guidance |
| IO-022 | Low | risk | Native cache fallback can lose user isolation and loader trusts external search paths |
| IO-023 | Medium | risk | Native parent-window pointers have unproven lifetime and thread-affinity guarantees |
| IO-024 | Medium | confirmed-source | JNI path conversion silently replaces non-Unicode filenames |
| IO-025 | Medium | confirmed-source | iOS Document filter maps an application MIME wildcard to the application-bundle UTI |
| IO-026 | Medium | confirmed-source | Web picker catches application callback failures as cancellation and lacks disposal cleanup |

## 1. High-priority data integrity and memory ownership

### IO-001: iOS read length is not the allocation length

`KmpFile.ios.kt:35–41` reads an NSData, clamps its length for ByteArray allocation,
then sends the *unclamped* length to memcpy. This is not just excessive memory
usage: if the allocations succeed for a file above Int.MAX_VALUE, memcpy writes
beyond the destination. With empty NSData the same function addresses element
zero of an empty array. No simulator crash is claimed; the native preconditions
are violated in source. Missing data also becomes an apparently valid empty file.

The safe immediate remediation is narrow: validate sizes, handle zero before
pinning, copy the validated count and report read failures. Existing `source()`
provides a streaming alternative for large-file users. Coil reaches readByteArray
directly, so this should precede performance work. The unmerged upstream feature
branch still retains the unsafe memcpy pattern and is **not** a fix for IO-001.

### IO-002: `remember { null }` is not remembered mutable storage

Android saver `pendingSource` is a local variable initialized from a remembered
null. The returned launcher is remembered once, while the Activity result callback
is refreshed across recompositions. They therefore stop sharing the same local
reference cell. The resulting null causes all content writes to be skipped, yet
the result callback reports a file. The upstream author independently describes
this exact failure in PR #551 / commit be274cc; that branch was not merged into
the audited main commit.

Do not “fix” this by placing a potentially multi-megabyte ByteArray in a Bundle.
Use a remembered request holder, explicit one-shot consumption and a separate
process-death policy. Lost request state must not be confused with intentional
null content. Test recomposition *between* launch and result, not merely two calls
within a single composition.

### IO-003: the native mutex contract excludes the destructor

The desktop picker serializes create/show with a Mutex, but DisposableEffect
destruction bypasses it. An IO show call may have captured a Long handle but not
yet dereferenced it when disposal frees the Box. Rust `ref_config` then creates
a reference from a freed pointer. The most direct failure window is queued show
entry or `config.build`, not a claim that the pointer is used continuously for
the whole visible dialog. Panic catching does not catch undefined behavior.

There is a second ownership handoff gap: `withContext(IO)` can finish allocating
a native handle whose return is discarded by prompt cancellation before the
Compose state owns it. An ownership-aware session/registry should solve both,
with tests that pause dispatch at these exact boundaries. Blocking the UI until
the user dismisses a native picker is not an acceptable disposal fix.

### IO-004: the real desktop write function deletes the source on self-save

The audit's mock supplies only the path the native dialog would have returned;
the source-writing code is the actual baseline `PlatformFilePicker.kt`.

Observed in an isolated temporary fixture:

```text
showSaveDialogWithFile(handle, source) where selected destination == source
=> FileNotFoundException
=> source.exists == false

showSaveDialog(handle, bytes = null) where destination contains 13 bytes
=> returns a File
=> all 13 previous bytes remain
```

Kotlin `File.copyTo(overwrite=true)` removes an existing target before opening
its input, so identical paths destroy the original. Null content instead calls
`createNewFile`, which does not truncate an existing file. Both arise from
incomplete existing-destination semantics. Check identity/aliases before writing,
stage atomically where possible, and specify intentional empty overwrites.

### IO-005: the iOS save contract can move the original

The file overload presents the original URL without staging; the export
initializer does not explicitly request copy behavior. Requested filenames are
ignored in that overload and prefixed with a UUID in the byte/data overload.
Named private staging plus `asCopy=true` prevents the source-move surprise and
fixes the filename contract together. IO-006/007/008 remain important after that
change: staging failure, dismissal and external-file access each require their
own lifecycle handling.

## 2. Result delivery and error channels

The common picker/saver API does not distinguish success, cancellation,
unsupported capability, provider failure and started-but-unobservable download.
This is visible in implementation, not a hypothetical API-style preference:

* Android saver nullable stream opens can skip all IO and still return success
  (IO-006), independent of the recomposition defect.
* iOS ignores the Boolean from NSData.writeToURL. Document/photo failures may
  be filtered into an empty or partial result with no diagnostic.
* PHPicker's duplicate guard gates only empty callbacks; nonempty results still
  process repeatedly. Document/save swipe dismissal is not registered (IO-007).
* Web FileReader reaches DONE for both success and failure, but the code treats
  DONE as success and cannot cancel the read (IO-009).
* Web save never calls its accepted onResult parameter (IO-011). Anchor download
  completion is not observable; the correct contract cannot fabricate a saved
  file simply to satisfy a callback.
* Web picker catches exceptions thrown by application onResult and calls the
  same callback again with an empty list, while cancel callback exceptions bypass
  cleanup (IO-026).

The recommended direction is backward-compatible typed error/result overloads
and a per-launch state machine with exactly one terminal event. Keep user
cancellation, coroutine cancellation and platform failure distinct. Do not catch
all Throwable around arbitrary application callbacks. A new API should expose
unsupported capabilities explicitly rather than quietly treating them as cancel.

PR #551 contains prior work for error overloads and some browser save support.
Its implementation and tests are candidates to review/cherry-pick, not authority
to assume all these remaining state-machine cases are handled.

## 3. File identity, access, filtering and platform parity

KmpFile wraps heterogeneous capabilities rather than a universal filesystem file.
Problems arise where that difference is hidden:

* iOS folder/external URLs need security-scoped lifetime management; Android URI
  grants may expire without explicit persistence (risk IO-008).
* Browser Files are not directory handles, but extensionless names are marked
  directories. Common isFile is true for a missing non-directory path (IO-010).
* iOS names remain percent-encoded and getPath points at the original URL rather
  than the readable copy. Android/Web path meanings are different (IO-014).
* Android folder URI metadata is queried as a single document and exists attempts
  to open content rather than query a directory (risk IO-019).
* Non-UTF-8 native paths are silently changed before returning to Java (IO-024).

File-kind, display-name, serializable URI, readable local path, access grant and
owned temporary copy are different concepts. Future APIs should separate them
without immediately rewriting every public package. `source()` is the existing
safe abstraction for content; it must not be implemented by guessing filesystem
paths from arbitrary getPath strings.

Filtering also differs materially. Desktop uses a finite MIME→extension table
and silently removes the filter for unknown types; modern AVIF/HEIC/HEIF are
missing (IO-015). Locale-sensitive normalization and exact comma-space splitting
produce additional misses (IO-016). iOS Document maps application/* to the UTI
for application bundles (IO-025). Android custom unknown extensions can resolve
to an empty MIME array; browser accept is advisory. No filter should be treated
as proof that content is safe or decodable.

## 4. Performance and resource budgets

Observed implementation costs (not benchmark claims):

| Path | Allocation / IO behavior | Concrete next measurement |
|---|---|---|
| Android/Desktop readByteArray | Whole file buffered; blocking on caller | UI-thread latency and cancellation on slow providers/disks |
| iOS readByteArray | NSData plus ByteArray native copy | Peak resident memory versus source(); size boundary safety first |
| Web read/source | ArrayBuffer/typed-array view→ByteArray; source adds Buffer copy | Main-thread copy time and heap peak for 10/100/500MB inputs |
| Coil | readByteArray plus Okio Buffer before image decoder | Encoded copies + decoded bitmap peak; cancellation and source closure |
| iOS document Multiple | Copies every selected file before truncating | Disk bytes/copy count with maxItems=1 and many selected documents |
| iOS photo Multiple | One async item load per selected result | Provider concurrency and temp-file count under cancellation |
| Desktop MIME filter | Full 981-extension scan, per-entry lowercase/array allocation | Cold init and repeated filter changes; pathological wildcard bound |
| Desktop native loader | Reads bundled bytes, reads cached bytes and hashes; saver can initialize on UI | Cold/warm startup with external library and extracted cache paths |

The clearest optimization with immediate correctness benefits is to limit files
before staging and clean up unreturned owned copies (IO-013). Streaming Coil
fetching is an improvement (IO-021), not a measured regression or a reason to
rewrite all modules before fixing the High defects. The historical discussion
about separate kotlinx-io/Okio adapters is a proposal, not an accepted migration
decision.

## 5. Security/native interoperability review

The concrete memory-unsafety paths are IO-001 and IO-003. Separate risks are
raw parent lifetime/thread affinity (IO-023) and native extraction/search-path
trust (IO-022). Private user-home caching is safer than a fixed global temp path;
the loader's missing-home fallback loses that assumption. A same-user writable
path alone is not evidence of privilege escalation.

Positive JNI details: nullable input strings are handled, element/string local
references are deleted in conversion loops, and Rust panics are translated to a
Java RuntimeException in most exports. Negative boundary details: Long handles
have no generation/type registry, show routines assume nonzero live pointers,
some conversion failures are treated as null/empty, and lossy filenames change
identity. The UI wrappers do not form a native-memory sandbox.

Resolved direct Rust dependencies in the archived metadata are jni 0.21.1,
raw-window-handle 0.6.2, rfd 0.15.4, objc2 0.6.5 and objc2-app-kit 0.3.2. The rfd
feature resolution includes **xdg-portal + async-std**, not the GTK backend claimed
by a Linux parent-window comment. This was read from
`calf-file-picker-cargo-dependencies-online.json`; runtime backend operation was
not exercised. The build/security audit owns the resolved dependency/advisory
scan and supply-chain findings: do not infer “no vulnerabilities” from successful
compilation or from this direct-dependency list.

Jodd code and MIME resource have their own BSD-style attribution in addition to
Apache-2.0. Native crate dependencies introduce additional third-party notices;
retain complete license material in distribution. The picker content-hashed
cache is a useful in-repo remediation for the separate older constant-path share
cache finding NATIVE-031, not evidence that the share cache is already fixed.

## 6. Historical evidence and incomplete fixes

The full Git objects and public metadata are preserved by the migration. These
references explain implementation decisions without relying on upstream remaining
online; find the commits in the imported Git history and the PR/issue bodies in
`docs/migration` archives.

| Imported history | Current interpretation |
|---|---|
| #84 / 69ea560: Coil fetcher introduced | The fetcher still reads entire files; later source() work has not been integrated into it. |
| #85/#86 and later iOS file-copy fixes | Provider callback URLs are transient. The current provider copy-inside-callback is important positive behavior, not expendable overhead. |
| #178; desktop AWT/JNA to Rust/JNI work, 5f8af29/470bce4 | Feature parity/installer-size motivations explain native bridge; current raw-handle ownership must still be audited independently. |
| 69770fb: maxItems; c0c2278: updated state | Limits exist across platforms, but input validation and several retained captures remain incomplete (IO-017/018). |
| e927149: iOS result fix | Moving copies off main improved responsiveness, but changing the guard left nonempty duplicate completion unguarded (IO-007). |
| a02c559 / #495: readable copy vs original URL | `url` switched to the temp copy; path/name/kind and cleanup semantics did not all follow that distinction (IO-013/014). |
| 6331db2: system-library-first loading | Deliberate packager compatibility, not inherently an unsafe feature to remove blindly. |
| befc455: immutable native cache reuse | Picker cache tests and audit probes verify same-byte reuse; this fix is not automatically present in other loaders. |
| #537 / c5b8c59: streaming source | Six original desktop source tests passed. Web remains eager-buffered by documented design. Comment 5653462009 discusses future module splits, not a decision to break ABI. |
| **Open PR #551**, branch `fix/file-picker-export-and-path` | Candidate fixes for Android empty export, iOS named/copy export, paths, dismissal, error overloads, real supported-browser saves and bookmarks. It is **not part of the baseline**; its author-reported tests are not our test results. |
| #551 / 66e345a: delayed URL revoke | Independently corroborates Safari concern IO-012; no Safari run was available here. |
| Open #309, #343 | File interop and native preview needs remain roadmap input rather than proof of a current failing code path. |

Do not wholesale merge PR #551 solely because it fixes several issues: it also
adds public APIs and platform behaviors. Review commit dependencies, preserve
backward compatibility, run its new tests on supported targets, and separately
fix defects such as the retained unsafe memcpy.

## 7. Implementation sequence

1. **Safety gate:** IO-001 checked native copies; IO-002 Android request storage;
   IO-003 handle ownership; IO-004 safe desktop overwrite; IO-005 non-destructive
   named iOS export. Add their regression tests before behavioral refactors.
2. **Reliable sessions:** IO-006 typed errors; IO-007/009/026 single completion and
   cancellation; IO-008 access ownership; IO-013 staging cleanup. Integrate
   verified subsets of PR #551 where appropriate.
3. **Portable contracts:** IO-010/014/019 file metadata; IO-017/018 configuration
   updates/limits; IO-015/025 filters. Explicitly document compatibility changes.
4. **Browser/native parity:** IO-011/012 download/save capabilities and URL
   lifecycle; IO-023 parent-window ownership; IO-024 filename error policy.
5. **Efficiency/hardening:** IO-016 MIME hot path, IO-020 read cleanup, IO-021
   streaming Coil and benchmarks, IO-022 cache fallback trust. IO-020 is small
   enough to land earlier alongside the safety gate.

Effort estimates and dependency IDs are in IO.json; final issue deduplication and
the combined cross-module roadmap are maintained by the lead. This report does
not authorize a release or major architectural rewrite.
