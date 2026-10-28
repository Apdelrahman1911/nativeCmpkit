# WebView settings and resource-error acceptance — 2026-10-28

**NATIVE-039 / [#153](https://github.com/Apdelrahman1911/nativeCmpkit/issues/153) is verified and closed.**
[Direct closure readback](direct-closure/closure-readback.json) follows
[all three original criteria/source/results review](direct-closure/important-result-review.json),
before this documentation. No original finding, issue body, label or history was removed.

## Important tests only

Immutable **`af107523f34a7810252bdbaf94a42b6cc919b01c`**:
**14/14 fresh target executions, ten authored methods, five XML reports**, zero
failures/errors/skips, exit 0 in 67.02 seconds. [Receipt](after002/receipt.json)
binds the exact filtered desktop/Android-host commands, reports and 757 unchanged
inputs, independently matched to that commit's Git blobs. No unrelated module replay.

- **Actual native work:** 1,000 equal assignments produce no extra native settings
  applications; a nested batch produces one, with only its final native User-Agent
  event. Behind a blocked real JavaFX queue, 1,000 complete UI notifications produce
  one application of the latest pair. The internal FX-confined counter increments
  after the actual WebEngine setters; no copied/fake queue.
- **Actual AWT→FX race:** AWT pauses inside a newer settings batch while an older
  completed notification waits on the real FX queue. Before repair, the native
  engine sees the incoherent `(false, A2)` pair instead of complete `(true, A2)`.
  The immutable-snapshot repair delivers complete A2, then complete B on completion.
  Initial creation also uses the published snapshot; notifications before mounting
  are retained. User-Agent null restoration remains per native owner.
- **Android-host resources:** production `AccompanistWebViewClient.onReceivedError`
  records all 5,000 controlled error code/Unicode-description pairs exactly.
  The collection identity stays stable; actual Compose observations invalidate on
  additions and next-page clearing. No silent truncation or copied collection loop.
- **Compatibility:** two real WebEngine/outgoing-HTTP User-Agent methods and four
  common settings methods execute on desktop; the common four also execute on
  Android host. Existing public setters, packages and descriptors remain.

## Measured allocation/time, not a performance promise

[One JDK17/Robolectric SDK34 sample](resource-benchmark.json):

| Measured loop | Thread allocation | Elapsed |
|---|---:|---:|
| Actual owning error callback, 5,000 inputs | 1,040,032 bytes | 20,788,023 ns |
| Original add/`toList` algorithm reference only | 50,415,328 bytes | 27,342,249 ns |

The reference copies 12,502,500 cumulative references. It is **not** an execution
of a historical APK/native WebView; there is no device/UI latency or universal
speedup claim, repeated statistical profile, or flaky wall-clock test threshold.
Controlled package-local `WebResourceError` producers exist only in host tests:
Android's constructor is package-private; no production/provider replacement.

## Failures retained

- [`before001`](before001/receipt.json): immutable `1e52e12d`, actual native
  **0/1 passed**, expected incoherent pair; exit 1 / 59.02 seconds.
- [`after001`](after001/receipt.json): immutable `c16d0473`, **zero tests**, exit 1 /
  77.02 seconds. New fixtures failed nullable-list type inference and Android's
  package-private error constructor. Fixture fixes retain all original assertions.
- [`after002`](after002/receipt.json): corrected focused result above.

The [manifest](archive-manifest.json) records original and archived hashes.
Derived XML retains every testcase identity/outcome and the original failure
message, without private console/stack/classpath bodies. Prior reports were
quarantined, not accepted as new executions. Raw console hashes and existing
JavaFX JNI critical-scope warnings remain in per-attempt observations; warnings
are **not** a native-memory/sanitizer pass.

## Boundaries and next work

Settings writers remain **owner-UI-thread confined**. Only completed immutable
pairs cross to JavaFX; arbitrary concurrent writers are not supported. Android
errors are a live observable read-only-typed list, not immutable per-update snapshots;
call `.toList()` when retaining a snapshot. No physical Android/Chromium/network,
Apple, native sanitizer/minimum-platform, consumer/ABI/dependency/legal or release
gate is lifted. No packages, releases, deployments, Pages or subagents.

**39 GitHub issues verified closed; ledger: 55 implemented, 66 partially verified,
35 verified, eight unresolved.** Continue focused native memory/ownership and
platform/consumer acceptance; close the owning issue directly when its actual
original criteria pass, without unrelated replay or documentation preflights.
