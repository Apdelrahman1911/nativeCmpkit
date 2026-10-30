# Original Linux build-only recovery — failed, retained

Actual [40971665663](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40971665663) at `539ddc6473e98e11785d55f5ca9e205cb3df3b74`
**FAILED**: Gradle exit 1 / 1993.47 s, **zero tests requested or executed**.
[Independent build review](build-review.json) verifies all 960 BEFORE/AFTER inputs
against immutable Git, JDK17/Rust1.98.0/canonical Android37 runtime, the exact
build-only command and four actual compilation graphs. Targeted unused Navigation
groups/imports are absent; sample minSdk remains24, not device certification.

The actual Wasm webpack process selected Node26.2.0, despite a root-only24.16.0
pin. Its exact OS process-start errno is not established. The original aggregate
output observer rejected the batch and lost earlier per-target values: **no
Android/JVM/JS output hashes or app-build pass are inferred**. Original safe JSON
artifact bytes and verified digest are retained; private logs/binaries/ZIPs are
not committed. The subsequent
[owning Node/independent-target repair](../web-build-repair001/README.md) is separate
evidence, not a rewrite of this failure.

The original 50 accepted Linux sample methods are reused from the earlier run,
not replayed here. #100/#154 stay open pending their own complete criteria.
Sample builds do not establish library/native/consumer/release readiness.
