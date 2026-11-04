# Offline tooling failure inventory

`scripts/ci/offline_tooling_failure_inventory.py` extracts bounded metadata from
the complete output already buffered by **one failed** offline scope. It runs
before the existing failure-only100-line tail; it does not rerun the scope,
change pass criteria, suppress a failure, or create a reuse certificate.

The JSON line starts with `[offline-failure-inventory] `. It contains validated
parent testcase identifiers, phase, failure/error counts, occurrence counts,
safe relative Python frame/line observations and error-class names. Subtest
values, exception messages and absolute path prefixes are omitted. Identifiers
are lexical observations, not authenticated source/test provenance; null fields
mean unknown, not an absent exception or proven root cause.

Bounds:16MiB input,200,000 lines,4,096 bytes per line,256 records and65,536 public
bytes. Invalid/decorated/missing summaries, unsupported headers and truncation
produce explicit `partial` or `unknown` status/reason codes. Helper or inventory
printing failure cannot replace the original failed outcome. It uses only pure
stdlib operations; no filesystem/environment/process/network access is required.

Regression evidence: NEW17 passed once, then a source-only portability defect
was corrected with only changed1+NEW1 passing. Unchanged16 were reused, not
replayed; the18 live controls are cumulatively qualified, not a fresh18-suite run.
The portable control requires only repository siblings, not external proposal
files. See [recovery701](../development/evidence/current-platform-recovery-20261101/tooling-producer698-recovery701/README.md).

Do not infer library/native execution, successful full tooling, safe dependency
distribution, consumer compatibility or release readiness from this inventory.
