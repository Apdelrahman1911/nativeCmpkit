# Related sample data-safety/compiler batch — verification preparation

NAV-011/013/014/016 remain open. [Desktop001](desktop001/review.json) FAILED at
immutable1f8f1671: Gradle1/158.04s, generator-dropped original IconCategories
declaration, zero XML/tests; all878 library+75 sample inputs held and exact Git.
The original declaration is in baseline CupertinoIconsCatalogData.kt, not a
separate AllCupertinoIcons.kt file. Full log remains private; compiler evidence
and before/after source/input hashes are preserved.

The smallest generator repair restores the original internal category list from
the same pinned entries. Public Cupertino/SF outputs are byte-identical, original
notices/font/mappings remain. [Owning tooling](tools001/review.json): new category
guard initially1failure, then10 catalogue methods and1 new owner wiring guard
pass; generator check has zero unexplained diff. No prior-source snapshot was
captured for those synthetic checks; no held-run or native-runtime claim. Original
SF provenance/availability/glyph/assistive requirements remain unresolved.

The exact screen streaming owner snapshots the selection, serializes cancellation,
checks active/current ownership before publication and invalidates on composition
disposal. Lazy job registration also prevents synchronous reentrant publication
from clobbering its replacement. Six common regressions, actual desktop composition
disposal and two real64MiB JVM read/close/cancellation fixtures are prepared. The
second models an owned blocking read and requires less than1s after it is released;
it does not promise arbitrary OS/provider reads are interruptible.

Only these sample-specific tasks verify sample findings. They never substitute for
library-level IO/picker/native/consumer suites. Apple/browser/device encoder, exact
peak memory/latency, provider, all-target sample/minimum, ABI/legal/dependency and
release/security gates remain. No packages/releases/deployment/Pages.

## Additive immutable desktop002 result

[Desktop002](desktop002/review.json), immutablec14caa1e, FAILED overall: Gradle1/
63.02s,7fresh XML,19reported cases/18passed/one initializationError. All878
library+80sample inputs held/exact Git, clean source before/after. Every actual
common owner/stream, composition disposal, codec/bounds and category method
completed. Both real-file methods **did not execute**: first inferred Throwable
from its trailing assertFails, not JUnit4-required void (actual javap confirms).
The smallest fixture repair appends Unit; production and all18 completed method
bodies stay byte-identical. Only the two previously unexecuted real-file methods
need recovery; retain failed whole run and original XML, do not replay18 passes.
No issue closure from the failed run; sample-specific evidence, not library/native
consumer or release certification.
