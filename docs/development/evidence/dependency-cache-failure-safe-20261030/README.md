# Preserve safe library registry caches after native assertion failures

Earlier workflow `actions/cache` implicitly saved only on whole-job success. A
new dependency key followed by a native/fixture failure therefore reacquired
unchanged registry/compiler dependencies on each continuation. This is a
source-confirmed efficiency limitation, **not a measured speedup or bad cache**.

Library jobs now use explicit **restore/save** with the same exact primary key
and fixed wrapper/modules-2/Cargo-registry/Konan-dependency paths. No prefix restore,
compiled project/build/native target outputs, XML, APK, signing, consumer or candidate
artifact cache is added. Before work and again after work, require the exact Git
revision, configured declarations/validator/key/module selection and **absence of
known nativeCmpKit candidate payload and every recognized metadata descriptor group**.
Unknown metadata layouts, symlinks, overlarge inventories/input receipts, changed
keys, foreign Gradle homes, duplicate JSON and candidate data fail closed, preserve
all data and write bounded non-certifying receipts. Save never runs after cancellation
or failed restore/precheck/postcheck; an exact existing hit is not saved again.
A native assertion failure remains red; it cannot create passing XML or issue closure.

The validator itself enters the dependency recipe. Registry dependencies remain
untrusted; this is a narrow known-group/path snapshot, **not** independent checksum
provenance, arbitrary-content/OS isolation or detached-process certification.
Core/IO and WebView packaged consumers keep fresh uncached child homes and their
stronger **success-only** producer cache policy. Sample caches also stay unchanged.
Read-only workflow permissions and the owner's no-required-SHA-pinning decision stay.

Initial eight synthetic methods produce **two failures**, preserved. After repair,
**26 important cache/key methods and34 disjoint workflow-matrix methods pass**,
60 distinct functions, including13 new CLI/safety methods; Actionlint passes.
The existing local cache's two known-group paths are observed absent without reading
artifact bodies or deleting anything;81 actual configured declarations bind the key.
These are local tooling/read-only checks, **zero Actions cache executions**.
Current camera run41107030315 at9f249b7e uses the **earlier workflow** and does not
validate this later patch. Hosted restore/precheck/save/postcheck/readback still need
review; no measured timing benefit, BUILD-007/#40, ordinary dependency/security,
full-platform/consumer/ABI/legal/release or publishing/Pages/main/history gate clears.
