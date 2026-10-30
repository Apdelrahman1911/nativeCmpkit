# Exact simulator target and safe failure diagnosis

Actual41002405707 failed `xctrace record` with exit21/zero exports/zero leaks
invocations; its44-byte private log was deleted by owned cleanup. Its exact cause
remains **unknown**. The command omitted `--device`, leaving default tool targeting
implicit despite knowing the actual UIKit simulator UUID. Public CLI examples are
not evidence that this omission caused that specific failure.

The small owning patch:

- Requires the **one exact selected UUID** in actual bounded `xctrace list devices`
  before launch, and supplies `--device <that UUID>` to the existing bounded
  Allocations/12s/owned-PID recording. No display-name/default/foreign fallback.
- Reads actual installed `codesign --display --entitlements :-` flags. Missing
  flags are observations, **not an authorization diagnosis**. No debug entitlement,
  signing, privileges, native binary or public-framework change.
- Before deleting a failed tool's private log, retains only bounded bytes/hash/
  fixed categories (process-not-found, authorization-refused, attach-refused,
  debug-entitlement-refused, unknown-option). Unknown stays unknown; no raw paths,
  transcripts, addresses, device inventory, entitlements, heaps or traces exported.
  Descriptor ownership, type/link/size and metadata checks plus bounded reread
  reject a same-sized rewrite that the synthetic timestamp-only check missed.

The original native GC/pixel/failure/Worker/request/210s/4096-round checks and180s
tool-attempt bound stay. Actual useful owned allocation rows **and actual PID-specific
zero leaks** remain mandatory. #141/UI-038 stays open; #140's accepted native scope
and strict40989310808 failure remain independent.

## Important results, not native execution

- Initial red:7 methods/5 failure and14 error events (subtests included).
- First shared command **FAILED31:30 pass/one nonexistent caller module**. Shipped
  code was not changed for that caller typo. Only the unexecuted correct module
  and two new guards were run next.
- That command **FAILED12:11 pass/one same-sized diagnostic-rewrite failure**.
  Metadata alone did not catch the observed payload rewrite; owning bounded reread
  repairs the reader without weakening the guard.
- Only five affected reader methods recovered, **5/5**, not a30/11-success replay.
  Combined accepted coverage: **42 distinct synthetic methods**, with four repeated
  methods in the final five, not46 distinct tests. All982 combined/905 library inputs
  held in each source-bound checkpoint. Private logs remain private.

Only the failed profiling workload needs one immutable `ios-image-profile-recovery`
request; nine original image/two accepted GC-failure methods are not replayed.
The two-case WebView request41007203221 continues independently at a189bcb9.
Zero new local Gradle/Kotlin/native/profile executions. Single-agent/max2 heavy
requests/8GiB reserve and publishing/Pages/main/history/release/security gates stay.
