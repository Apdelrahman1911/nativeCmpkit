# Direct important native incremental-build closure

**BUILD-010 / [#145](https://github.com/Apdelrahman1911/nativeCmpkit/issues/145)
closed2026-10-28 at09:49:35UTC**, directly after all three original criteria and
source/results review, before documentation. [Review](lead-source-and-results-review.json),
[actual phases](acceptance-review.json), [closure readback](issue-145-after.json),
[resolution](issue-145-resolution-comment.md). Original body/title/labels preserved.

Nine actual Gradle commands exit0 on actual JDK17, base1ceb9d68. Both picker/share
native build/prepare/resource tasks are **UP-TO-DATE** on the identical repeat.
Independent source/Cargo.lock mutations rebuild only picker, leaving share reused;
the shared toolchain-file mutation rebuilds both. Each mutation is restored before
the next independent experiment. [Exact recipes](fixture-recipes.json) append
nonsemantic comments: input tracking, not different dependency/compiler versions.
A README-only control holds sourceTreeDirty=true throughout, so changing the dirty
flag cannot fabricate invalidation. Native/owning build code is own Git source.

**360 hash comparisons,37 unique own-Git blobs** match exactly apart from the three
documented fixture additions, unchanged within each command. Every produced native
resource set is independently manifest/checksum/source/ABI/version/compiler-checked
as Linux-x64 only. Actual fresh JVM PickerContractTest **4/4**, one XML, zero failures/
errors/skips, uses reused host payloads and builds no foreign native/mobile/browser
targets. Cold native fixtures still require Rust/prerequisites; not Rust-free.

| Actual command | Seconds |
|---|---:|
| Baseline host resources |60.01|
| Identical resource repeat |20.00|
| Source mutation/restoration |25.00/26.00|
| Lock mutation/restoration |19.00/20.01|
| Toolchain mutation/restoration |26.01/21.01|
| Four fresh JVM methods |24.01|

These command durations are not a controlled performance benchmark. Native remote
Gradle binary caching remains disabled because linker/SDK inputs are not hermetic.
Host builds, explicit verified prebuilts and full release assembly remain separate.
Public/JNI/native identities and retained task aliases/versions stay unchanged.

Three local controller failures remain: guessed daemon prefix; treating repeated
interleaved active console headings as repeated task execution; mistaking shared
NonAndroidTest resource preparation for Android-target execution. The owning strict
daemon parser, equal-state repeated-heading plus exact native-response counts, and
actual target-task classification repair those fixtures. **Accepted baseline/final
JVM commands were reviewed from original same-input receipts, not reexecuted.**
No library failure or required missing-native check was suppressed.

This closes incremental host acceptance, not BUILD-003/005 complete verification,
full native/JNI/live-dialog/device/minimum-platform, dependency/legal/security/
consumer/ABI or release gates. **44 closed issues overall**; no publishing/deployment.
