# Desktop native cache security: executed red and owning repair

This is current development analysis for baseline **IO-022** (picker) and
**NATIVE-031** (share), not a rewrite of their original records. Work is contained,
single-agent, and unverified artifacts cannot be published.

## Actual Windows baseline, not a POSIX substitution

The `windows-cache` profile at immutable
`9d0d920603d2b56943cdc04aa72faae768ef23d5` requested only picker/share desktop
library suites. Run [40425258898](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40425258898)
executed71 tests: **66 passed / 5 failed**, with one exact AppKit-only N/A and
**zero unexpected skips**. The newly authored Windows operations actually ran:
owner ACLs were set/read back, Everyone's well-known SID was translated by the
system instead of guessed as an English account, file symlinks were created,
and directory junctions were confirmed as `isOther=true`, `isSymbolicLink=false`.

Failed methods establish these concrete contract defects:

| Owning implementation | Actual failure |
|---|---|
| Picker `ensurePrivateDirectory` | Foreign writable ACL is accepted; its POSIX-only policy never checks Windows ACL grants |
| Picker `nativeCacheDirectory` fallback | Fresh fallback has foreign mutation ACL grants; the POSIX-only setter does nothing on Windows |
| Picker `ensurePrivateDirectory` | A directory junction redirects extraction; `Files.isSymbolicLink` alone misses it |
| Share `rejectSymlinkPath` | The same distinct junction is accepted as a directory and used for payload extraction |
| Share `extractShareNativeLibrary` | An already foreign-writable cache is trusted (and on POSIX silently chmodded), without an owning Windows ACL policy |

The [review](evidence/github-actions/40425258898/lead-independent-review.json)
binds Git source bytes, the exact ZIP SHA256, the two module plans/commands,
XML hashes, unique testcase identities, statuses and the native scenario policy.
It is deliberately a reviewed **failure**. Native share's real JNI ABI/diagnostic,
borrowed-pointer and unsupported-host contracts passed on Windows in this same
run; they do not turn unsafe filesystem extraction into a pass or certify a
packaged consumer. Test extraction bytes are not executable attack payloads;
**no cross-user compromise was demonstrated**.

## Minimal owning-source repair

Affected production files remain in their retained public-package directories:

- `calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCache.kt`
- `calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibCache.kt`

No public package, JNI symbol, framework name or library project identity moved.
Independent module-private helpers avoid introducing a new picker/share module
dependency or architectural rewrite. The owning contract is now:

1. Reject noncanonical dot-segment cache paths instead of validating a normalized
   directory and writing through a different original path.
2. Read actual no-follow `BasicFileAttributes` for **every path component**;
   reject both symbolic links and other reparse/device entries. A Windows junction
   can be a directory and an `isOther` entry simultaneously.
3. Measure the effective filesystem owner from an actually process-created,
   immediately deleted probe, not mutable `user.name` or `user.home` properties.
   Require that owner on the cache directory and regular payloads.
4. Reject group/other POSIX writes, or actual nonowner Windows ACL ALLOW grants
   for write/append/delete/attributes/named attributes/ACL/owner mutation. Inherited
   and INHERIT_ONLY grants are not silently excluded. Unknown/unverifiable
   permission stores fail closed.
5. Create missing directories and temporary files using explicit owner-only
   permission attributes. Only a directory actually created by this call, with
   its owner and nonalias identity checked, may have its initial permissions set.
   Read them back before extracting payloads. **Never repair an existing unsafe
   directory or payload's ACL/mode in order to trust it.**
6. Preserve valid existing identical-content reuse, immutable share full-digest
   identities, and private unique-file fallback when an actual filesystem move
   fails. Policy exceptions and fatal errors are not successful fallback paths.
   Post-move content/owner checks and no-follow bounded reads protect the return
   contract; `finally` attempts removal of unretained temporary files on failed
   writes or validation, and cleanup failures propagate rather than become success.

Existing cache contents are executable code, not confidential user data. Existing
owner-controlled/readable-but-not-foreign-writable directories remain acceptable;
fresh directories/files are owner-only. ALLOW/DENY evaluation is conservative:
any foreign mutation ALLOW is rejected rather than simulating Windows effective
access with reordered ACEs. A legitimate redundant denied grant can therefore
require an explicit owner-side ACL correction or a new trusted directory.

Observable compatibility changes are intentional security/error behavior:
foreign-writable/owned, aliased, unverifiable or dot-segment caches now throw;
empty picker payloads are rejected before extraction. Valid native basenames,
picker's retained short cache fingerprint, full share fingerprints, unchanged
reuse and loaded-library filename stability remain. This is **not ABI certification**.

## Regression scope and remaining gates

The first held-source Linux red executed19 (18pass/1fail), reproducing share's
silent chmod/trust. Final [source-held green](evidence/native-cache-tests/green-20261027-004/receipt.json)
executed25/25 without skips using actual JDK17/Kotlin2.4.20/JUnit4 cache sources,
no stubs. Six additive methods cover both modules' foreign-writable payloads,
actually private nested creation and dot-segment rejection. Prior passed
intermediate snapshots remain archived separately; they do not verify later edits.
All source-hash receipts say which702 library/build/CI inputs were held.

The Linux checks alone did **not** establish Windows correctness. The subsequent
immutable [Windows run40429039349](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40429039349)
at `6930e1732d12b36dece44171341a918cdde1234c` now executes **77/77** across
picker47/share30, in14 fresh XML reports. One exact AppKit-only case is N/A;
there are **zero unexpected skips**. The [independent review](evidence/github-actions/40429039349/lead-independent-review.json)
binds exact Git inputs, ZIP digest, commands, runtime and unique XML outcomes.
The [paired red/green review](evidence/github-actions/40429039349/paired-cache-review.json)
confirms all five originally failing methods pass, no original case was removed,
all other original outcomes are unchanged and six additive cache methods pass.
Required Windows cases ran instead of becoming skips or new N/A. This verifies
that defined Windows library-suite/cache scope, not all original requirements.

The full platform suite, DLL-already-loaded multi-process reuse, foreign-owner
impersonation, read-only/noexec homes/mounts, complete native payload provenance,
candidate JNI matrix and packaged consumers remain independent requirements.

No-follow metadata/readback is not a handle-bound `System.load` attestation.
Verification and path-based loading are still separate; same-user/privileged
attackers, mutable ancestor ownership and late ACL inheritance changes can defeat
a filesystem snapshot. Retained unique fallback files use best-effort exit cleanup;
loaded Windows DLLs and failed filesystem deletion can leave them behind.
Java17's inspected ACL setter does not explicitly protect
inheritance. Do not claim that a private ACL readback permanently locks an ACL,
that hashes establish authenticity, or that these tests reproduced an exploit.
Retain these conditional risks in release/security review. No issue is closed and
no legal, ABI, dependency, consumer or release gate is cleared by this document.
