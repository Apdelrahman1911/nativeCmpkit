# IO-019 / #55 — controlled remote source-only preparation

The source plan sealed on 2026-11-04 was adopted by the lead before these leaf
edits. This adds a new **test-only** separate-UID, two-process HTTP-backed provider
and two library-level native methods, not a production fix or whole-issue closure.
Read [the fixture](../../tests/consumer/android-io-remote-documents/README.md) for
protocol, bounds, ownership and explicit scope limitations.

## Why separate from accepted fixed-provider tests

The existing `android-io-documents` fixture is local synthetic content with cached
regular files/LOCAL_ONLY flags. Relabelling it cloud would be incorrect. Its Java
source, accepted Kotlin tests, `OwnedIoEndpoint`, `DeviceDescriptorProbe`,
`NamedSystemDocumentsUi` and named-system caller remain byte-identical. The new
backend exclusively owns nonce-random bytes in memory, and the new provider's
metadata/listings/byte reads genuinely traverse actual loopback TCP.

Four exact additive reporter-manifest fragments declare only the NEW signature
control permission, package/authority visibility and nonexported caller. Their
inverse yields the exact original manifest SHA256
`397d45d9201637e6a696b3c4148376bb02fe5c4bb1070c541616bdcdaefeeb19`.
Old reporter-union admission is **not** loosened. Shared snapshot/selector/matrix,
workflow and always-finalizer integration remains lead-owned; source readiness is
not an executable native profile until that integration is qualified.

## New native execution flows

```text
reporter (different UID) --signature Binder--> backend/main helper process
      |                     owns nonce + ServerSocket + random arrays
      +--signature Binder--> provider witness/second helper process
      |                     provisions immutable root/ancestry by real TCP
      +--implicit ACTION_OPEN_DOCUMENT_TREE--> actual system DocumentsUI
      |                     Use/Allow returns actual tree/grants
      +--public KmpFile metadata/source--> ContentResolver --> DocumentsProvider
                                                |              |
                                   actual reliable FIFO <--- HTTP Socket
                                                |              |
                                 bounded hash, EOF, close    real backend
```

Positive method requires folder metadata immediately and after actual caller
Activity destruction/bookmark restoration. It separately requires backend/provider
native identity and socket endpoint pairs, real transferred FIFO stat/fdinfo,
bounded digest/one-byte EOF, retained caller FIFO at EOF, explicit close/FIFO0,
producer/server/socket termination and unconditional data/grant/process cleanup.

Cancellation method uses an actual framework `CancellationSignal` during a
background pending native `openFileDescriptor`. Headers are live but the backend
holds the first body byte before provider pipe allocation. Actual signal closes
only the registered socket; caller must receive `OperationCanceledException` and
no PFD. Source counters alone, an empty unknown-inode scan, thread interruption,
socket timeout and forced cleanup are not passing substitutes.

## Original issue criteria and accepted reuse

| Original unchanged criterion | This new source's possible subset | Still not established |
|---|---|---|
| ExternalStorageProvider, Downloads and cloud-provider folder URIs | Generic remote DocumentsProvider contract within explicit controlled-loopback scope | Downloads remains source-refused, not N/A; no vendor/account/OEM/physical compatibility |
| Folder exists/name/isDirectory immediately and after restart | Immediate metadata and caller Activity destruction/bookmark restoration | Activity destruction is not process/provider/app/device restart; accepted fixed-provider restart scope remains fixed |
| Single-document and file:// regression tests | Tree-child file metadata/read/close only | Existing accepted IO3 is reused, not selected or replayed |
| Permission denial and unavailable provider | Pregrant/after-cleanup access denial, pending native network cancellation | Cancellation is not unavailable provider; accepted fixed-provider revoke/outage scope remains fixed |

Accepted populations remain run `41510126699`/`260ea5dc` (ExternalStorage),
`41245152018`/`5585edac` (fixed secondary-client restart/revoke),
`41265408309`/`1c74cb9a` (IO3 three methods) and `41294135981`/`e16268a6` (outage).
No accepted population is replayed or reclassified as remote from these edits.
Lead review, not this fixture, decides applicable criterion scope. Commercial
cloud and Downloads/restart/whole-issue requirements are explicitly unverified.

## Source qualification and future native verification

`scripts/ci/android_io_remote_documents.py` contains bounded manifest/protocol/API
source guards, a complete source receipt, an exact new APK-metadata pair reader
(the old pair allowlist is unchanged), existing byte-identity/owned-AVD cleanup
primitives and API35-only compiled-manifest/private-key signer requirements.
`test_android_io_remote_documents.py` tests only NEW/owning source/refusal controls.
These are lexical/model controls, not executed Android/platform functionality.

Three **leaf-only** focuses are proposed:

* `android-io-controlled-remote`: exactly both NEW identities.
* `android-io-controlled-remote-positive`: only the first if that remains missing.
* `android-io-controlled-remote-cancel`: only the second if that remains missing.

Before first native execution, the lead must integrate complete reversible
reporter union admission, new helper ownership before prepare and independent
always cleanup, finite library/controller/matrix/workflow discovery/source maps,
actual helper/reporter APK compilation, signer/installed manifest/byte identity,
fresh XML identity agreement and current max-two combined hosted reservations
including queued work. Local heavy builds remain serial with an 8GiB reserve.
Important NEW controls are frozen before their first execution; red controls stay
red historically, and only failed/changed controls may recover. Compiler output
is zero native execution and cannot close #55. No publishing/Pages/main/history,
consumer/API–ABI/security/dependency/legal/release-readiness gate is weakened.
