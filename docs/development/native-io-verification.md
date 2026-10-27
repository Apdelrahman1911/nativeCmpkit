# NativeCmpKit iOS IO and Coil verification

## Current evidence and containment

**Pending Apple runtime verification.** IO-001 / [#4](https://github.com/Apdelrahman1911/nativeCmpkit/issues/4)
remains `partially-verified` and open. The [diagnostic review](evidence/ios-io-diagnostics-20261027/lead-diagnostic-review.json)
preserves the first failures and successful final typechecking. There are **47
authored methods** in eight selected test files: IO40 (35 iOS-specific plus five
common) and Coil7. Compilation executes **zero Native tests**. The new finite
`ios-io` CI profile requires 22 exact native cases within that selection, without
skips/N/A; actual XML must establish the execution count and outcomes.

No packages, releases, deployments, Pages, API/ABI certification, external-provider
access, physical-device behavior or complete release gate is implied.

## Source-owned Foundation copy

The original `af388bd3` defect allocated a clamped array but passed the original
larger length to `memcpy`, and acquired element zero's address even for an empty
array. Earlier hardening added the representability/empty checks. This follow-up
keeps Foundation's owning `NSData` receiver involved in the actual native copy:

1. `KmpFile.ios.kt:readByteArray` rejects non-file URLs before any content read.
2. A security-scoped block loads immutable `NSData`; a failed load throws
   `kotlinx.io.IOException`, never an empty-success value.
3. `NativeDataCopy.kt:toCheckedByteArray` calls the shared
   `BoundedRead.kt:checkedByteArraySize` before allocation or pinning. Lengths above
   `Int.MAX_VALUE` throw; empty data returns without acquiring a pointer.
4. The pinned nonempty array calls `copyToCheckedNativeBuffer`. That boundary
   independently rejects negative capacity, insufficient space and a null nonempty
   destination before the Foundation call.
5. `NSData.getBytes(destination, length = checkedCount)` copies exactly the checked
   count. The required binding is `platform.Foundation.getBytes`, a category
   extension, not an unimported instance member. No borrowed `data.bytes` pointer
   escapes its owner. Concurrent mutation of `NSMutableData` is not supported.

Both helpers are internal; public packages, overloads, descriptors, module names
and Maven coordinates are retained. Large whole-file allocations still consume
memory and perform blocking IO: use `source()` or the explicit bounded overload
on a suitable dispatcher. This is not a new maximum-allocation guarantee.

## Actual stream and Coil ownership

`KmpFileSource.ios.kt:source` validates a file path, acquires a security-scope lease
and opens the real `SystemFileSystem` source. Opening failure closes the lease;
the returned `RawSource.close` closes the underlying stream with lease cleanup
in `finally`. `readBounded` consumes through `use`, enforces the limit during reads
and yields between chunks so cancellation can close the owned source.

`KmpFileFetcher.fetch` transfers the real kotlinx-io → Okio stream to Coil's
`ImageSource`; a failure before transfer closes the stream. Native sources use
`DataSource.DISK`, not the browser buffering path. Exact configured Coil3.6.2
source was inspected from its Maven sources artifact:

- `Decoder.kt:20,28–29,40–44`: suspending nullable decode, consume only inside
  `decode`, and `Factory.create(SourceFetchResult, Options, ImageLoader)`.
- `EngineInterceptor.kt:142–144`: the transferred source closes in `finally`;
  lines170–175 separately protect an event-listener failure before return.
- `ImageRequest.kt:505–509,604–606`: request coroutine contexts and explicit
  decoder-factory selection used by deterministic test scheduling.
- Artifact origin/hash: [acquisition receipt](evidence/ios-io-diagnostics-20261027/coil-source-acquisition.json).
  Reading source is not an independent dependency-trust or distribution gate.

## Regression matrix

The source paths are below `calf-io/src/iosTest/kotlin/com/mohamedrejeb/calf/io/`
unless stated otherwise.

| Source | Real implementation exercised when executed | Mandatory cases |
|---|---|---|
| `NativeGuardedCopyTest.kt` | Darwin `mmap`/`mprotect`/`munmap`; payloads of1,6,page−1,page end at source/destination `PROT_NONE` pages; prefix sentinel and rejected undersized/null/negative destination; checked length0,`Int.MAX_VALUE`,+1,`ULong.MAX_VALUE` without giant allocation | 5 |
| `NativeReadSafetyTest.kt` | Foundation empty/one-byte/binary/missing reads; actual owned `chmod(0)` unreadability; retains non-file NSURL/local-path isolation and existing temporary-copy tests | 5 required of8 |
| `NativeSourceLifecycleTest.kt` | Real stream open/read/repeated close, limit failure, cancellation at first actual read yield, consumer exception and20 repeated whole-file/stream cycles | 5 |
| `calf-file-picker-coil/src/iosTest/kotlin/com/mohamedrejeb/calf/picker/coil/NativeKmpFileFetcherTest.kt` | Real300KB stream/bytes/DISK classification; actual `ImageLoader.execute` opening errors; URL isolation/pre-open cancellation;20 repeated fetch/read/close cycles; actual Coil decoder failure/cancellation after transfer | 7 |

Descriptor probes compare `stat`/`fstat` inode **and device** identity for the
owned file, not the process's fluctuating total descriptor count. They scan the
actual `getdtablesize` range and fail if unavailable/unbounded (>65,536), rather
than guessing or skipping. Unreadable-file tests require a non-root runner,
restore owned fixture permissions in `finally` and check cleanup. Guard-page
mapping/unmapping failures are real test failures, not a mocked safety pass.

The two decoder tests use the **production fetcher**, real `SourceFetchResult`,
actual Coil engine and real Native descriptors. A controlled decoder consumes
one actual byte, then either throws the exact `IOException` or suspends until
cancellation. The decoder never closes the source itself; the tests assert that
Coil propagates the outcome and its owning `finally` releases the descriptor.
This is fault-injection integration, not validation of every image codec.

## Preserved execution history

- Initial Python red:11 methods, three failures/eight errors. One synthetic
  missing-Coil fixture incorrectly omitted required UIKit source paths; corrected
  the fixture without relaxing the existing application-host gate.
- Corrected initial Python run:11 focused and414 full CI methods;11 are within414.
- KLIB compile001: exit1/65.02s,733 held inputs; unresolved `getBytes` binding.
- KLIB compile002: exit0/48.02s,733 held inputs; actual IO/Coil production and test
  compilation, before the explicit Beta interop opt-ins and two decoder tests.
- Final KLIB compile003: exit0/47.02s,733 held inputs at digest
  `eb487cbd8e4b3f01b2b6951f3a2b8462eb1fb6aa11923029212c3a465df54cdd`.
  Both test compile tasks executed; unchanged production KLIBs were `UP-TO-DATE`,
  not falsely recounted as fresh compilations. All47 authored methods typecheck
  with exact Kotlin2.4.20/real dependencies, no stubs. Source warnings are gone;
  four configured Linux native/cinterop/disabled-target warnings remain.
- Final held Python run repeats11 focused/414 full CI methods at the same digest;
  adversarial guards reject missing/duplicate/skipped/failed/wrong-task/wrong-target
  native cases and Linux cross-compilation advertised as Apple execution.

The byte-preserving archive contains logs, original red inputs, controllers,
compressed before/after source maps, KLIB manifests/hashes and issue4's open-state
observation. Later documentation/archive additions do not circularly certify
themselves or a future immutable revision.

[Final full lightweight preflight031](evidence/ci-preflight-20261027-031/lead-final-recount.json)
passes23 held commands/1,297 overlapping Python methods at18,590 inputs, strict
MkDocs/actionlint/both whitespace guards,66 actual anchors/25 distinct generated
HTML outputs. The first reviewer count24 assertion and hardcoded field error are
preserved; actual recount corrects them without dropping output checks.414 CI
methods/11 IO guards overlap1,297; this is not Native runtime evidence. Archive
and these context links are additive after the source freeze.

## Efficient next verification

Commit/push reviewed changes on `development/preview-hardening`, preserve `main`,
then dispatch **only `ios-io`** at the exact held development SHA. The finite
matrix selects `calf-io,calf-file-picker-coil` on one arm64 `macos-26` iPhone slot.
Use the existing real SDK/simulator selection, source/own-Git identity, read-only
token, fresh-test task markers, report collection and dependency-key guards.
Do not replay unchanged UIKit/Windows/browser/consumer jobs or old XML.

Inspect actual test identities/counts, SDK/runtime correspondence, task exits,
fresh XML hashes, source maps and all22 required native cases. Close #4 only after
mapping **each of its six original requirements** to accepted immutable results.
Guarded-buffer evidence satisfies its specified integration alternative; it is
not an ASan run or a proof all native memory operations are safe. Device/provider,
legal/notices/provenance, dependency trust, full/minimum consumers and API/ABI
remain independent release gates.
