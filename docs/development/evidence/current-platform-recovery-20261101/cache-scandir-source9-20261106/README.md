# Bounded dependency-cache directory scans — 2026-11-06

This isolated patch repairs one confirmed verification-tool resource defect in
three related consumers. It does not change Kotlin APIs, package coordinates,
dependency trust, native functionality or release readiness.

## Root cause and implementation

Python 3.12 `Path.iterdir()` obtains an eager `os.listdir()` inventory. The
existing 256-entry guards in `scripts/ci/core_io_consumer.py` (producer cache
observation), `scripts/ci/webview_consumer.py` (consumer cache observation), and
`scripts/ci/library_dependency_cache.py` (library cache observation) therefore
ran after potentially unbounded enumeration/allocation. An outer `islice` around
`Path.iterdir()` did not bound that eager operation.

All three now use context-managed `os.scandir()` with `islice(..., 257)`: at most
256 admitted names and one refusal sentinel. Existing candidate-name predicates,
error propagation, refusal thresholds and no-delete behavior are preserved. The
iterator closes on success, refusal and enumeration errors; only `DirEntry.name`
is used after close. Six files/eight reversible spans preserve all 70 previous
test-method ASTs.

## Focused verification

Nine NEW source regression methods executed once: **9 passed, 0 failures,
0 errors, 0 skips**. They cover the 0/256/257/million-entry synthetic bounds,
iterator closure and exact exception propagation, real filesystem layout
predicates, sentinel refusal with an unconsumed entry, and preservation of
foreign/candidate bytes and the declared metadata fields. Previous 70 methods
were not replayed; their AST preservation is a separate source observation.

The complete source footer/EOF, child and terminal driver exits (both 0),
29 held sources (848261 bytes), 43 held sealed inputs, process-group absence
and owned runtime removal were independently reviewed. Suite: 0.411554859s;
source phase: 1.197481225s; cleanup: 0.023175716s; final driver: 1.223199099s.
The fixed Q300/source270/cleanup30 budget was not increased.

See `SOURCE-RESULTS.json` for exact selectors, pins and scoped outcomes. Original
logs, complete result/transport data, source packet and independent reviews are
retained outside the checkout, with their immutable hashes cited there.

## Limits and integration

Tests ran on Linux in finite owned source fixtures, not packaged Kotlin
consumers or native platform tests. Held synthetic-file assertions exclude
atime/uid/gid; they are not full10 source-custody assertions. No registry
provenance, signer, dependency-admission, consumer, platform or release gate is
cleared. This does **not** close #40 or establish a hosted timeout cause/capacity.

The branch is additive above `0c7a909e734ec34f2d305b13270a8dfaed03b74e`. It is
prepared using a temporary index and only six explicit source blobs plus these
documents; no working-tree checkout, broad status/discovery or protected-file
access is used. The active development checkout/cohort is left unchanged.
Further integration must deliberately reconcile any owning source-domain pins;
no historical hash is overwritten. No package, release or deployment is made.
