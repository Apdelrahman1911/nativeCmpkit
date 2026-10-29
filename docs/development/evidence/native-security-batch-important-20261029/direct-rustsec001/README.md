# Actual direct RustSec native graph checks

Two real cargo-audit0.22.2 scans pass with **zero matched vulnerabilities and
zero warnings**, on complete93picker/48share committed lockfile unions. All
architectures/OSs and informational warnings are included; no ignore, severity,
stale or target filter. `--deny warnings` is enabled; yanked checking is not
explicitly disabled. This is a dated advisory result, not a proof of safe code.

The tool is source-installed with exact`=0.22.2`, `--locked` and Rust1.98.0:
exit0/383.1s. **That compilation is zero NativeCmpKit runtime tests.** The source
install/binary digests are recorded, not presented as independent bootstrap trust.
[Actual review](actual-scan-review.json) binds5native manifest/lock/toolchain inputs
to immutable67539481 and holds their bytes before/after both scans.

RustSec database commit`40f5be6fb12ed93fc591bf4ab23b7d793b3f2239` is clean before/
after, with all1381 loaded advisory markdown files independently byte-bound to
its Git tree:1361crate +20Rust-toolchain advisories. The initial independent
archive review incorrectly counted onlycrate files; that failure is preserved,
corrected using the actual layout, and neither successful scan is replayed.
Scans use`--no-fetch` against that exact owned checkout. The tool's
JSON`last-commit` and`last-updated` fields are **null** under this invocation;
our separate Git/byte check supplies the binding, not fabricated tool metadata.
Earlier OSV92unique exact public coordinates/zero matches remains separate evidence.

BUILD-012/#147 stays **OPEN**: actual portal open/save/folder/multiple/cancellation
and supported session-bus/functionality requirements are independent. Existing
JNI config/load or open/cancel tests do not cover that entire matrix. BUILD-007,
ordinary Gradle locks/verification, binary provenance, consumers/ABI, licenses,
native/device/minimum-platform and all security/release gates remain open.
No new issue closure or package/release/deployment/Pages. Raw JSON receipts only;
private logs, advisory clone, installed executable and compiler targets are not
committed/uploaded. Native sources/production locks are unchanged.
