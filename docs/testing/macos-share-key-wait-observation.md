# AppKit owned-key readiness: failure-only late observation

Share650 (`41791895471`, source `ef6aae6da0c0879431d9c4712f8f914eaf6194ea`)
remains **failed**. Its first `missing_content_view` process reached the original
10-second `window.isKeyWindow()` wait and failed at `cases.rs:61`, before the
content-view/nil-content/native-admission body. The other five AppKit cases were
not executed. A successful GUI probe/opt-in is not key-window proof.

The existing Regular activation policy, `finishLaunching()` and
`activateIgnoringOtherApps(true)` calls are retained. Already-cached objc2
AppKit/Foundation 0.3.2 sources qualify the getter signatures, not this host's
activation or a native cause. No speculative activation, event-dequeue/send,
window-ordering or deadline change is made.

## What the additional evidence means

Only the exact `missing_content_view` primary panic payload
`Owned AppKit window did not become key` permits one observation, before the
independent original owned cleanup. The hook is protected by a separate Rust
panic boundary; its result never replaces the primary result or cleanup result.

On actual Main, the observer clones the single existing owned-window reference
and releases the RefCell borrow before read-only Objective-C getters. It emits
only finite fields: Main/owner availability, application active/running/policy,
owned-window visible/key/eligible/miniaturized state, key-window pointer relation
without exporting pointers, current/main run-loop relation and absent/default/
other current-mode classification. Each getter occurs at most once. There is no
window/event enumeration or raw title, identifier, mode name, recipient or body.

`unavailable` means a getter was not queryable; it is not `false`, absence or
zero. `absent` represents a returned nil/empty owner option only. A present key
window without an available owned reference is `present-unclassified`, not
guessed other ownership. The sample is **sequential, late and non-atomic**: it
does not capture the original failing predicate value and cannot prove its cause.
An Objective-C stall still relies on the unchanged outer owned-process timeout.

The owning runner consumes the same sealed bounded private stderr bytes once.
The whole stream remains limited to 4,096 bytes and the one fixed marker to 512
bytes. Exact source, original line/reason, failed-case and marker schema are
required; missing, ambiguous, malformed or inconsistent availability remains
unavailable. Existing source-pinned Share630 assertion readers remain unchanged;
they still refuse the new source hash. The new snapshot is a separately labelled
field, never a repaint of those original assertions or a native pass.

## Source custody and next execution

The local leaf carries exact inverse fragments for `cases.rs`, its AppKit driver
and two genuinely affected source-hash controls. All original harness/reader
hashes and assertion bodies are retained. Only the complete reviewed afterimage
can enter the current local driver; an exact ancestor is not current admission.
The fixture also holds the applicable unchanged native production/Cargo/main,
original recovery readers and JNI timeout test source. Source/model controls and
this plan are not a compiler, AppKit, recipient, stress or sanitizer result.

Read-only one-first-missing plan:

```sh
python3 scripts/ci/macos_share_appkit_lifecycle.py --plan --case missing_content_view
```

**Deferred lead integration gate:** the outer missing-only CI contract/shared
source ingress still pins the earlier driver/cases bytes. Those old pins are not
changed or bypassed by this leaf. The lead must review the exact composed source
admission/routing before freeze, capacity review, push and any hosted execution.
Prefer only this failed first missing case, not the unchanged six-case batch.

The accepted prior two AppKit/two JNI bodies are reused, not replayed. Share650's
new exact JNI timeout 1/1 accepted subset is also not requested by this AppKit
plan; its applicability uses unchanged production/test bytes, not a claim that
the entire later source-input map is unchanged. The remaining AppKit cases and
original failures, #84/#85/#150, stress/lifetime/native subject-payload/service/
recipient, consumer/API-ABI/dependency/legal/security/release/publication/Pages/
main/history gates remain open. Lead alone integrates, dispatches and accepts.
