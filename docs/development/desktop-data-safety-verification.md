# Focused desktop data safety

## Important checks, not another whole-library preflight

IO-004/#7 and NATIVE-027/#14 remain open until required results are reviewed.
The new finite `desktop-data-safety` profile selects **only file-picker/share**
on Linux x64, macOS arm64 and Windows x64, maximum two simultaneous jobs. It
retains complete/full-profile coverage, read-only tokens and report-only uploads.

The owning save path now uses NIO file streams and `runInterruptible` **after**
native selection. Cooperative checks alone cannot interrupt a blocked read.
All three existing desktop native save entry points share the selected-path
contract; canceled launchers check their Job before callback delivery. Public
signatures/packages/JNI remain unchanged. Native modal cancellation/parent
ownership is not made interruptible by this file-copy change.

## Actual narrow Linux execution

[Configured2.4.20/JDK17/coroutines1.10.2 receipt](evidence/desktop-data-focused-20261027/attempt2/receipt.json):
**14/14 current real filesystem methods** (10 AtomicSave +4 selected-path/stream).
Five are newly authored; nine existing methods are retained. Four input hashes
hold across direct compilation/execution; bounded outputs stay in tmpfs.

- Same source/normalized/symlink/hard-link aliases, null empty saves, large copy,
  staging/atomic-move/cleanup failures retain existing regressions.
- Both read and write errors after one real64KiB chunk close both streams,
  preserve the original destination and remove only owned staging.
- Cancellation while genuinely blocked inside a wrapped real NIO source read
  interrupts without releasing the fixture's gate, closes both streams, performs
  no commit and preserves source/destination bytes. The copied old cooperative
  dispatcher control **fails** the exact method; its gate is released only in
  failure cleanup so the test does not strand a worker.
- Native **selected-path/null-result boundary** saves and cancellation pass;
  this is not a visible OS save-dialog or composed-launcher integration test.

The first harness incorrectly expected self-suppression to fail on old source.
The actual old-source method already passes: Kotlin's suppression adapter guards
identity. [Correction/history](evidence/desktop-data-focused-20261027/original-control-correction.json)
preserves that result; the unnecessary source guard was removed. No such defect
or fix is claimed. The positive regression remains useful.

## Share policy and remaining acceptance

Three new source methods cover unavailable native payload vs unsupported host,
partially unreadable actual file batches, and no implicit clipboard fallback after
native dismissal/failure. The production adapter retains JNI/AWT; its internal
policy has no OS-open/browse handler. These three methods have **not yet executed**.
No guessed count is used: discovery reports52 picker/34 share authored
methods; platform-specific N/A is not a passing method.

The narrow Linux pass is not immutable full-module/other-OS/native-dialog,
network-provider/kernel-blocking/crash-durability, native-parent/sanitizer,
packaged consumer/API-ABI/legal/dependency or release evidence. Review actual
important CI outcomes then close individually; update the ledger afterward.
No release, package, Pages or deployment publication.
