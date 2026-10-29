# Actual native batch and Windows checkout failure

Run [40848333339](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40848333339),
attempt1, immutable `e009700f235c670f46b31c26df558cab741903d2`, is **FAILED**.

[Independent review](review.json) and [artifact review](archive-review.json)
verify Linuxx64/arm64 and macOSarm64/x64: **16 actual empty-cache builds**, four
per real host. Each host has42 held before/after native/recipe inputs matching
its exact Git revision. Both crates build twice with separate initially empty
Cargo homes/targets and exact Rust1.98.0/release/locked commands. Complete93picker/
48share conservative graphs/features and source/compiler/build metadata agree.
Actual offline unchanged→changed101locked-refusal→restored controls pass without
editing production manifests/locks. Owned temporary caches/binaries are removed.

Native byte hashes **differ** for several pairs despite equal size/graph/build
metadata. This is recorded, not described as byte-reproducibility or provenance
certification. **Zero native runtime/UI/JNI tests** execute in this profile.
SDK/Rust prerequisites are shared, not claimed initially empty.

[Windows failure](windows-checkout-failure.json):30 actual long-path checkout
errors precede the controller, zero Windows builds and no reports. New job-local
`core.longpaths=true` and `core.autocrlf=false` before checkout preserve archive
paths/source bytes. The finite `native-lock-windows-source` recovery runs only
Windows and its changed guards; no accepted host replay. It is pending.

The first preflight's erroneous `has_pages=false` assertion failed **before any
POST** and is preserved. Configured `has_pages=true` is not published status:
actual Pages statusnull/workflow and the owner's verified #171 closure remain.
The initial independent reviewer also assumed an absent execution `reserve_mib`
field; that failed read-only review is retained, then corrected by inspecting the
actual immutable controller/default bounded invocation instead of inventing it.

BUILD-005/#39 still needs Windows verification. BUILD-003/#2,BUILD-004/#38,
BUILD-007/#40 and BUILD-012/#147 require their independent JAR/load/minimum/UI/
advisory/trust gates. No new closure or release/publication/Pages certification.
