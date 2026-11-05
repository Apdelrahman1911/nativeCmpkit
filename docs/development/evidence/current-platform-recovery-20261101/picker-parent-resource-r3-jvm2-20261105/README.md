# Picker parent/JNI resource batch — 2026-11-05

## Current verified scope

The isolated `development/macos-parent-lease-20261105` worktree integrates the
R3 proposal and the reviewed finite JVM2 ingress: **nine existing modifications
and five new files** in total. The original R3 nine-file
readback succeeds; existing modes are preserved and additions are explicitly
0644. The original prewrite refusal wrote **zero** sources: the tracked JNI test
file was excluded by sparse checkout. Lead-owned sparse expansion restored that
tracked dependency, then the separate recovery applied each source once.

The reviewed original controls are reused, not replayed:

| Verification | Actual result | Boundary |
| --- | --- | --- |
| NEW Python source controls | 15/15; exit 0; 0.011s suite | Source/model only |
| Direct std-only production release-state compile | exit 0; 0.498534s outer | Not the library crate or JNI |
| NEW release-state protocol tests | 16/16; exit 0 | Numeric ownership/concurrency model only |
| NEW21 + changed owning1 JVM2 controls | 22/22 once; exit 0; 0.054s suite | Actual worktree imports; source/refusal only |
| Actionlint and Git whitespace check | exit 0 each | Workflow/source formatting only |
| Actual macOS/JDK JVM2 | 2/2; zero failures/errors/skips; 65.113223s total | Two exact methods in separate real-JVM processes only |

The FIRST22 execution retains 540 exact source identities, complete original
captures, an absent owned process group and an empty/removed owned runtime.
Independent saved-result acceptance agrees; the 0.688178956s enclosing source
supervision is not the future 600s native-operation budget. The optional local
supervisor required two pre-execution admission corrections: an explicit
`files`→`inputs` projection and use of the authorized NEW0644 adoption mode,
not the proposal transport's 0600. Neither correction changes library sources
or waives identity checks. Earlier R1/R2 source refusals remain preserved.

The five caught protocol-test panics and original failed/refused predecessors
remain in the archived records. The actual JVM2 result below supersedes the
earlier source-only checkpoint for those two methods only. There is no AppKit,
packaged consumer, binary ABI, security or release acceptance. **#58 remains open.**

## Actual macOS/JVM verification

[Run 42086043267 / attempt 1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42086043267)
completed successfully at immutable
`c1840df523fbd4a8e2298a12ea6bc0e04df62efc`, workflow `395188378`, job
`127451292702`, [artifact `13442856842`](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42086043267/artifacts/13442856842).
The following exact methods each passed once in separate genuine-JVM processes:

- `jni_path_tests::actual_jni_pending_primary_stops_parsers_results_and_picker_entry_body`
- `jni_path_tests::actual_jni_optional_nulls_and_unicode_parser_arguments_keep_their_meaning`

One locked, jobs=1, compile-only library build passed in **61.234887s**, executing
zero tests. The compile, two inventories and two method phases each exited 0 with
complete captures and absent original process groups. The shared operation used
**65.113223s / 600s**. Actual host: Darwin arm64, JDK 17.0.21, Rust 1.98.0,
Xcode 26.6, macOS SDK 26.5. Runtime identity held and the clean checkout's **1,538**
before/after hashes agreed, including the unchanged exact frozen **540** subset.
Hosted NEW21 + owning1 source controls also passed; this is not a second local run.

Independent review authenticates the original run/attempt/job/artifact, exact
byte-bound controller JSON and complete job logs against the reviewed unchanged
source. Private native subprocess logs and the executable were intentionally not
uploaded: their harness output/markers and compiler diagnostics cannot be
independently reparsed. Acceptance is therefore **source-qualified authenticated
controller-receipt acceptance**, not raw-trace or trusted-builder attestation.
The inherited `real_filesystem=true` marker is not filesystem or picker execution
for these methods. The 39 filtered tests per exact run did not execute and are not
additional accepted/skipped methods.

No native parent acquisition, CFRetain/CFRelease completion, AppKit modal/focus or
close/recreate behavior, VM shutdown/epoch safety, Windows/Linux parenting,
minimum-platform compatibility, binary ABI or packaged consumer test is inferred.
The five original issue acceptance criteria remain open.

## Implementation

- `calf-file-picker/native/src/lib.rs`: pending-exception-first admission,
  fallible scalar/array conversion and success-only outer-entry release drain.
- `native/src/macos_parent.rs`: checked strong JNI pins; reserve bounded recovery
  storage before a retain; preserve the actual retained pointer and prepared JDK
  release policy; no JNI/AppKit work while holding ownership-storage locks.
- `native/src/macos_release_slots.rs`: bounded 64-slot linear release ownership,
  known-unscheduled versus possibly-invoked quarantine, unwind-safe transitions
  and out-of-lock metadata disposal. Request transfer is **not** proof that the
  native retain was released; unknown work is never retried or evicted.
- `native/src/parent_retain_slot.rs`: exact generation/borrow ownership protocol.
- `native/src/jni_path_tests.rs`: six existing helper-call adaptations and two
  new genuine-JDK tests for pending-primary precedence and optional-null/Unicode
  argument meaning. Both new methods passed in the actual JVM2 result above.
- Desktop `NativeFilePickerBridge.kt` and `PlatformFilePicker.kt`: private
  parent-lease integration; existing public Kotlin APIs and original JNI
  descriptors remain preserved at source level, not yet binary-verified.

## Evidence and remaining work

`ARCHIVE795.json` indexes the byte-identical original R3 records;
`ARCHIVE800.json` separately indexes 23 byte-identical ingress, ancestor,
adoption, source-control and independent-review records. `source/` holds
the complete reversible source packet, original design/failure matrix and native
verification plan. `reviews/` contains independent complete-source and original
result acceptance. `controls/` retains genuine first-run records and streams.
`adoption/` preserves the original zero-write refusal and accepted recovery.
Historical absolute paths and transport modes are attributed original metadata;
the archive's 0644 modes are not original runtime modes.

`ARCHIVE805.json` indexes **11 byte-identical JSON artifact originals and two
independent review records** under `native42086043267/`. Original identities and
private 0600 modes remain held; archived copies are explicitly 0644. The sole
reviewer acquired one original job log and one ZIP once. No raw logs, native
payloads, binaries or signed download URLs are copied or published.

The finite JVM2 workflow/controller is adopted and its actual two-method request
is accepted within the boundary above. Do not replay these unchanged accepted
methods. Next work addresses the remaining original issue criteria. Real retain/release
completion, JVM lifecycle/shutdown and epoch safety, AppKit/modal/disposal races,
all binary JNI exports, consumer compatibility and dependency/legal/security
gates remain required. No release, package, Pages deployment or history rewrite.
