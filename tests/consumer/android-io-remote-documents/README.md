# Controlled remote Android document source (IO-019 / #55)

**Source fixture, not a published artifact, Maven consumer, sample application or
commercial cloud provider.** No native execution is implied by source guards or
by this README. The library's self-instrumenting `calf-io` tests are the real caller.

## Native ownership and data

* Helper package: `io.github.apdelrahman1911.nativecmpkit.verification.ioremotedocuments`.
* Its main process owns a real `ServerSocket` bound to literal `127.0.0.1` and a
  fresh ephemeral port, plus one nonce's random 4,097-byte/131,073-byte arrays.
* Its `:nativecmpkit_io_remote_provider` process runs `DocumentsProvider`, real
  `Socket` clients and reliable pipes. These two processes share the helper's UID,
  but that UID differs from the reporter's. They are not independent machines.
* Exported control/witness services require the exact signature permission and
  authenticate the reporter's actual UID/package/signature. Both supply genuine
  PID/process/generation Binder witnesses. HTTP headers do **not** prove PIDs.
* The standard exported provider requires `MANAGE_DOCUMENTS` or actual system URI
  grants. There are no helper Activities, shared UID or `grantUriPermission` calls.
* Only immutable root descriptor/ID ancestry is cached after actual HTTP
  provisioning. Every document metadata query, listing and byte open uses live
  HTTP. Provider storage is not a file/cache/canned-payload fallback. Its sole
  filesystem read is its own FIFO's kernel `/proc/self/fdinfo` diagnostic.

The real native implicit `ACTION_OPEN_DOCUMENT_TREE` opens stock DocumentsUI.
`EXTRA_INITIAL_URI` is only a navigation hint. Unchanged `NamedSystemDocumentsUi`
selects the uniquely owned `NativeCmpKitIo55-<nonce>` child folder and installed
Use/Allow controls; no drawer completeness, private navigation or synthetic grant.
The returned authority, folder ID and read/persistable/prefix grant are checked
before public metadata/persistence. Actual optional write grant is recorded.

## Exactly two NEW native methods

Class `com.mohamedrejeb.calf.io.AndroidIoRemoteDocumentsTest`:

1. `controlledRemoteTreeMetadataAndBoundedSourceCloseAreBackedByLiveHttp`:
   public folder metadata immediately and after Activity destruction/bookmark
   restoration; actual tree-child file source, bounded 4,097-byte hash and one-byte
   EOF, newly calibrated transferred FIFO still owned at EOF and zero caller FIFO
   after explicit close. Native endpoint pairs/request IDs, producer termination
   and backend peer EOF/closure are independently required.
2. `nativePendingRemoteOpenCancellationReleasesHttpSocketWithoutTransferringDescriptor`:
   actual background `ContentResolver.openFileDescriptor(..., CancellationSignal)`.
   Backend sends valid headers and holds the first body byte. Provider blocks on
   real socket input **before** allocating/returning a pipe. Only after that native
   admission does the actual signal close the registered owned socket. Genuine
   caller `OperationCanceledException`, one signal origin, no returned PFD, peer EOF
   and joined caller/producer/backend workers are required. Timeout or forced
   cleanup cannot pass this criterion.

The new focus helper exposes exact two-method, positive-only and cancel-only
identities, so a justified failure recovery need not replay an accepted method.
Shared Gradle/controller/workflow dispatch integration is lead-owned and must be
reviewed before execution. Existing accepted ExternalStorage, IO3, fixed-provider
restart/revoke/outage methods and helpers are not modified or selected here.

## Finite transport and cleanup

HTTP/1.1 is strict CRLF/ASCII: status 200, exact session/request/transfer IDs,
content length/hash/type, no duplicate/unknown headers, no redirect/chunked/encoding
fallback. Header/metadata limit 8,192 bytes, header lines 64, journals 128 per
process, active connections 4, accept backlog 8, connect 2s, ordinary read 5s,
held read 15s, held watchdog 20s and individual cleanup join 10s. Aggregate
request/response header budget is 5s, tightening each actual socket read to the
remaining budget; a slow peer cannot extend it indefinitely with single bytes.
The original ordinary/held body timeout is restored, preserving the primary
failure if that restoration fails. Native scheduling and Kotlin polling
and blocking/native scheduling are cooperative, **not** hard wall-clock deadlines.

Raw Java `Socket` is **not** governed by Android `NetworkSecurityConfig`'s HTTP
cleartext policy. The actual allowlist is the source guard plus literal loopback,
owned port, nonce and native endpoint validation. Cleartext here is intentional
test-only transport, never production TLS or security certification. There is no
DNS, proxy, remote host, adb reverse, host server or external network dependency.

Every failure independently attempts source/PFD/future cleanup and worker join,
caller/UI closure and accessibility flag restoration, own bookmark release and
provider-owner revoke with actual denied-access readback, provider/backend
socket/pipe/listener/thread cleanup, nonce-array wipe and acknowledged exact
self-PID death observed by real Binder death. Main backend/provider control
HandlerThreads are process infrastructure and are separately covered by owned
process death; a Binder pool thread's continued existence is not a pending-open
worker leak. Error counters, request journals and tombstones are never reset to
manufacture success. `Socket.isClosed` alone is not kernel socket-FD absence.

The external controller must own the new helper **before** preparation and run its
always-finalizer after partial failures. Actual source/APK/compiled manifest,
API35 signer/private-key and installed byte identity are required before reporter
compilation. Uninstall/force-stop require the current owned guest lease and exact
installed APK bytes; no preexisting/foreign app replacement. Owned guest disposal
is a separate witness, not a passing library test. Early unbound/unprepared
failures cannot invent self-PID/death receipts; controller cleanup still runs.

## Non-claims

Compilation uses the unchanged catalog's compileSdk37/minSdk23/JDK17, but native
selection is **API35 only**. No minimum/other API, OEM, physical device, Google
Drive/commercial account, remote host, TLS, all-network, API–ABI, consumer or
release/security certification is inferred. Activity destruction is **not process
restart**. Framework pending-open cancellation is **not** automatic KmpFile
coroutine cancellation or post-transfer disconnection.

Original #55 Downloads capability remains parked/source-refused, **not N/A**.
All four original issue criteria remain unchanged and the issue remains open.
No production/library/public API change or package/release/deployment occurs here.
