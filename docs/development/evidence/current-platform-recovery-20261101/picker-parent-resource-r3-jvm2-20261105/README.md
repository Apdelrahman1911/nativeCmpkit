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

The FIRST22 execution retains 540 exact source identities, complete original
captures, an absent owned process group and an empty/removed owned runtime.
Independent saved-result acceptance agrees; the 0.688178956s enclosing source
supervision is not the future 600s native-operation budget. The optional local
supervisor required two pre-execution admission corrections: an explicit
`files`→`inputs` projection and use of the authorized NEW0644 adoption mode,
not the proposal transport's 0600. Neither correction changes library sources
or waives identity checks. Earlier R1/R2 source refusals remain preserved.

The five caught protocol-test panics and original failed/refused predecessors
remain in the archived records. There is no new macOS, JVM, AppKit, packaged
consumer, binary ABI, security or release acceptance. **#58 remains open.**

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
  argument meaning. Neither new JVM method has executed at this checkpoint.
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

The finite JVM2 workflow/controller is source-qualified and adopted. The next
development-only immutable request is `build-native-libs.yml`,
`profile=picker-jni-actual-jvm2`. It must compile once on actual macOS arm64 and
inventory/run each exact method
separately; source tests must not replace native execution. Real retain/release
completion, JVM lifecycle/shutdown and epoch safety, AppKit/modal/disposal races,
all binary JNI exports, consumer compatibility and dependency/legal/security
gates remain required. No release, package, Pages deployment or history rewrite.
