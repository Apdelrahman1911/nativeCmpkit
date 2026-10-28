# Important native configuration memory/ownership checks

**IO-003 remains open.** Immutable53e56c7e (native tests92f85f9c) executes8/8 real
Rust methods under Valgrind3.22 twice: stripped, then symbolized/debug1 release.
Both exit0/2s, no ignored/filtered methods, zero invalid-access/error contexts,
zero definite/indirect loss. **Not16 unique tests or zero heap residue.**

Three new scenarios pause inside actual `DialogConfig.build` after real
`FileDialog::new`, close the registry twice during the build and prove the leased
configuration survives then is freed; build/drop128 actual single/multi/directory/
save configurations with monotonic IDs and zero remaining strong leases; reenter
the registry from Drop, proving no registry mutex is held. The hook is test-only;
no production branch, public/JNI/native identity change. Existing methods cover
registry/Arc races/stale IDs and strict Unicode conversion.

[Review](review.json) binds27 native/build inputs to own Git blobs and unchanged
before/after binaries/sources. Cargo no-run compilation exit0 (25s stripped,
36.01s symbolized) means **zero tests**; actual executable runs supply evidence.

Preserve the first unsymbolized observation. Both exits show **48bytes possibly
lost,544 reachable**,592bytes/two blocks,5,230allocations/5,228frees/287,045bytes
allocated. [Symbolized stacks](valgrind-ownership-symbols002.log) locate the48-byte
Thread-inner allocation in std thread/mpmc initialization used by libtest's
CompletedTest receiver;544bytes is std Unix stack-overflow thread-info BTree
initialization. This is observed allocation attribution, not a suppression,
zero-residue claim, arbitrary lifetime proof or release waiver. No suppression.

No native parent or live dialog was opened. Real JNI/Compose disposal/settings,
cancellation during show, immediate relaunch/closed-window behavior and IO-023
native-parent retention/main-thread safety remain required. Native/device/minimum-
platform, legal/dependency/consumer/ABI/security/release gates remain. No publishing.
