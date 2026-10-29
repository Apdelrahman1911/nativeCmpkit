# Shared Apple image-memory batch: tool discovery only

The two owning issues **#140/UI-037 and #141/UI-038 stay open**. Their nine
accepted real UIImage pixel/conversion/failure/GC methods are not replayed. The
remaining original supported-native-diagnostics and Instruments allocation/leak
requirements require actual native execution, not release-call counters.

The bounded discovery helper uses a publicly defined, owned **macOS HOST C**
allocation probe on the existing Apple sample build-only host. It is not UIKit,
iOS, GC, ASan, a library test, a heap-profile fix or release certification. Only
actual command exits, schema names/counts, input hashes and fixed-probe-symbol
witness survive; private traces/binaries/logs/exported rows are removed locally.
No extra job or write permissions. Unsupported tooling remains explicit.

[Important tooling](final-important001/review.json) passes **108/108 synthetic
methods**, all **962 inputs held**, actionlint1.7.12 and whitespace. First9/five
fixture/wiring errors and subsequent9/9 are preserved. These counts overlap the
prior84 owning checks; not192 unique methods. ZERO new local Gradle/native/library
executions. Actual Apple profiler support has **not** been observed yet. The Linux
version-only compiler rejecting Xsanitize=address says nothing about Apple
capabilities or memory safety.

Recover only missing sample build evidence, never accepted method replay;
maximum two combined queued/running heavy requests, single agent,8GiB reserve.
Publishing/Pages/main/history and independent release/security gates unchanged.
