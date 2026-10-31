# IO-023 / #58: native peer borrow and ownership bridge review

**No complete compatible bridge is proved by the selected Skiko/JAWT interface.
No production patch is prepared. IO-023 remains unresolved/open.**

The concrete minimum blocker is a supported, disposal-coordinated acquisition
hook that transfers the actual peer's native parent into an owned binding before
releasing the peer borrow. A callback inside Skiko's existing drawing-surface
scope does not supply that guarantee on macOS. Adding that callback to our JNI
call, moving creation to Swing EDT, or adding a delayed native retain would not
be a defensible ownership fix.

Only private files under this directory were written. Tracked project inputs
were captured at `7380a04674c2dc83583a45953418ec2c823b4258`; 18 exact inputs are
listed in [inputs/manifest.json](inputs/manifest.json). No Cargo, Gradle, native
compiler, JVM/JNI/UI run, CI dispatch, Git/GitHub mutation, unsafe stale-pointer
experiment, packaged consumer, security test, issue closure, or promotion ran.
The prior off-main refusal candidate remains private and is not reused as a fix.

## New source evidence

The JDK17 reference is OpenJDK `jdk-17.0.17+10`, dereferenced commit
`30ef840c3736270330fc0a26849c2456406facfe`. The prior local JDK21 reference is
`jdk-21.0.12+8`, commit `9de4f68c88a0a1510373f291d1a95b1f6b0db8c8`.
**The project workflows select Temurin 17 major, not an exact minor/runtime.**
Neither reference source is represented as proof of a hosted binary. Their
macOS `awt_DrawingSurface.m` files match byte-for-byte, SHA256
`04bb299be32e2c94a2734e77916b1295da571c0b7a17280ce95c16a231869383`.
Public read-only download receipts and pinned URLs are in
[research/download001.json](research/download001.json),
[download002.json](research/download002.json), and
[download003.json](research/download003.json). The three initial JDK21 macOS
source bodies also match their genuine saved Git tree blob identities.

| Exact source | Finding and implication |
|---|---|
| [macOS JAWT](research/openjdk17/src/java.desktop/macosx/native/libawt_lwawt/awt/awt_DrawingSurface.m), lines 72–88 and 116–126 | Both surface Lock/Unlock and global AWT Lock/Unlock are `TODO: implement` no-ops. Calling either does not exclude peer disposal. |
| Same source, lines 31–54; [CPlatformComponent](research/openjdk17/src/java.desktop/macosx/classes/sun/lwawt/macosx/CPlatformComponent.java), lines 50–52 | `GetDrawingSurfaceInfo` calls plain `getPointer()` and copies the result into `platformInfo`. The getter reads `ptr`; neither path acquires the resource read lock or transfers native ownership. |
| Same JAWT source, lines 93–111 | The drawing surface holds a `NewGlobalRef` to the Java target. That prevents collection of the Java object, not explicit native-peer disposal. |
| [CFRetainedResource](research/openjdk17/src/java.desktop/macosx/classes/sun/lwawt/macosx/CFRetainedResource.java), lines 75–90 and 130–140 | The real source-backed borrow is `execute`: read lock around the native action. Disposal obtains the matching write lock, clears `ptr`, unlocks, then schedules release. This internal guard is not exposed through the chosen Skiko/JAWT handoff. |
| [Skiko Drawlayer.mm](research/reused/skiko/skiko/src/awtMain/objectiveC/macos/Drawlayer.mm), lines 37 and 361–367 | `LayerHandler.window` is weak; `getWindowHandle` reads that cached field and returns its number. Its `platformInfoPtr` argument is not consumed in the getter. The returned `jlong` carries no native owner or generation. |
| [Skiko AWT.kt](research/reused/skiko/skiko/src/awtMain/kotlin/org/jetbrains/skiko/AWT.kt), lines 14–22 | The info/lock/surface scope ends before a downstream JNI creator receives the getter's number. The saved actual artifact bytecode agrees with this ordering. |
| [Skiko MainUIDispatcher](research/reused/skiko/skiko/src/awtMain/kotlin/org/jetbrains/skiko/MainUIDispatcher.awt.kt), lines 15–16 and 34–35 | It dispatches to Swing EDT. Its name does not establish AppKit main or the Windows native HWND owner thread. |
| [Component.removeNotify](research/openjdk17/src/java.desktop/share/classes/java/awt/Component.java), lines 7163–7195; [Window.doDispose](research/openjdk17/src/java.desktop/share/classes/java/awt/Window.java), lines 1185–1250 | Direct disposal clears the peer and calls `p.dispose()` before hierarchy notification; `WINDOW_CLOSED` is posted later. These events alone are not a before-dispose generation hook. |
| [CFRetainedResource.m](research/openjdk17/src/java.desktop/macosx/native/libawt_lwawt/awt/CFRetainedResource.m), lines 43–53 | The JDK schedules AppKit resource release on the main application message loop, specifically warning about nested-loop release. Ordinary main-queue RAII drop is not a release/drain proof. |

Skiko source is pinned at tag `v0.150.1`, commit
`3956e988e6e93eaf1ee985d725049443e7845807`. The reused actual Skiko 0.150.1
and Compose UI 1.12.0 jars match their saved SHA256 values. Selected rfd 0.17.2,
raw-window-handle 0.6.2 and dispatch2 0.3.1 archives match current Cargo.lock;
all 15 reviewed crate files match those archives. See
[research/source-reuse-manifest.json](research/source-reuse-manifest.json).
This is source/bytecode provenance, not native payload equivalence or a runtime pass.

## Why the small apparent bridges are insufficient

- **JNI retain inside existing Skiko callback:** macOS JAWT still has no real
  disposal exclusion. Retaining its `platformInfo` or `windowLayer` there merely
  moves the unproved lifetime assumption earlier.
- **Retain a CALayer, then search AppKit windows by exact layer on main:** if a
  real guarded layer ownership transfer were available, owning the layer could
  prevent pointer reuse and make main-thread lookup safer than a bare window
  number. That prerequisite is absent here. Retaining a layer also does not
  itself retain its NSWindow, establish the logical Java peer generation, or
  reject a moved/detached layer. No patch is based on that incomplete route.
- **Hold tree lock / drawing-surface lock through native-main dispatch:** this
  violates the task's lock restriction. JAWT operations also require the same
  acquisition thread. Moving the surface across dispatch is not an API shortcut.
- **Acquire AWT tree lock after dispatching to native main:** blocking main on a
  Java lock is not proven safe when AWT code can already be waiting for main.
  A supported nonblocking peer borrow is required; this review does not add one.
- **Use internal `CFRetainedResource.execute`:** this identifies a real guard,
  but reaching the exact peer/resource and invoking the action is a separate
  JDK-specific interop contract. `sun.lwawt.macosx` is not exported by JDK17's
  module descriptor. Native JNI access is not categorically forbidden by that;
  however, hard-coded private fields, reflective/proxy callbacks, module flags,
  or a runtime-specific JNI accessor need explicit design and runtime review.
  They are not a proved public Skiko/JAWT bridge or a routine two-file repair.

## Minimum acquisition plan after that hook exists

This is a concrete conditional contract, not pseudocode claimed to be implemented:

1. Carry the actual `ComposeWindow`/Java peer identity into acquisition, with a
   unique logical parent token and monotonic native generation. Resolve the
   current peer through the chosen supported adapter. Do not carry a previously
   read `windowHandle` Long into the ownership callback.
2. Admit acquisition on the actual native owner thread. On macOS, dispatch before
   acquiring any peer/AWT/registry lock. A supported guard must reject or defer
   without blocking native main if disposal or another operation owns the guard.
   Once on main and inside that live guard, verify the Java peer identity and
   generation, retain the NSWindow and exact NSView, and confirm attachment.
   **Both native owners must exist before the guarded source borrow ends.**
3. Release the peer guard before registering the result, invoking rfd, or waiting
   on another event loop. Register only a token for the retained main-thread
   owner. Cross-thread DialogConfig state holds that token/lease, not raw AppKit
   values with unconditional Send/Sync.
4. The peer adapter must invalidate generation at actual detach/dispose/recreate,
   before destroying the peer's native resource. Native content-view detachment
   or replacement invalidates the binding too. Java window/hierarchy callbacks
   may report lifecycle changes, but do not supply the sole invalidation barrier.
   Never rebind an old launch to a new peer or matching reused native number.
5. On native main, validate the retained view still belongs to the retained
   window and the generation remains current immediately before the temporary
   borrowed handle is passed to synchronous rfd construction/show. No registry
   or AWT lock spans that call. Keep both owners until native show, result
   extraction, and JNI conversion are finished, even after cancellation.
6. For disposal while visible, invalidate result delivery and finish/close the
   native dialog safely using an owned native dialog operation. rfd's current
   public synchronous API does not expose its panel/cancellation handle or strict
   error classification. A narrow panel/backend adapter or reviewed dependency
   extension is required if prompt native dismissal and typed native failure are
   promised. Coroutine cancellation is not that operation.
7. Release owners exactly once after the final in-flight use, on the permitted
   AppKit application loop. Close admission before shutdown, enqueue explicit
   disposal while the loop is alive, and drain it before ending the loop. Do not
   let the last registry lease trigger synchronous main dispatch under its lock.

A supported peer acquisition/disposal hook plus a narrowly scoped native dialog
adapter is the minimum new capability needed. A wholesale UI rewrite is not
proposed. The alternative of binding directly to private OpenJDK resource locks
remains a separate architectural decision, including exact runtime support and
safe access semantics, rather than a patch based on field-layout guesses.

## Public facade and additive JNI boundary

Keep the existing Kotlin facades and JNI export descriptors. The existing Long
parameter means a raw native number; do not silently reinterpret it as an owner
token. A future private extension can add `acquireParentOwner(Component)` and
owner-aware creator exports using a distinct opaque token/generation contract.
Required capabilities and old-payload mismatch must be explicit; parented calls
must fail with a typed unavailable/incompatible result if the new bridge is
absent, while genuine explicit no-parent calls retain their supported behavior.

The lead/build owner must review the exact additive exports, capability/version
handshake, owning model, and per-target payload source before integration. This
review does not broaden legacy nonzero-parent guarantees or alter ABI version 1.

## Platform boundaries and remaining checks

| Platform | What the actual selected source establishes; remaining minimum |
|---|---|
| macOS arm64/x64 | Weak cached NSWindow number and no-op JAWT lock. Needs the guarded transfer and full main-thread session owner described above. Retained objects alone also do not establish direct disposal policy or generation. |
| Windows x64 | JAWT checks IsWindow and obtains a drawing DC; Skiko takes the parent HWND. Neither exposes an owner-thread destruction lease. Native owner-thread dispatch/COM apartment, destruction coordination and generation must be acquired through a supported native peer adapter. IsWindow, EDT or another STA thread alone is insufficient. rfd collapses HRESULT failures to None; native cancellation/error behavior needs the adapter. |
| Linux x64, established X11 or XWayland | Actual Skiko Linux path uses JAWT X11 data/XQueryTree; X11 JAWT does hold AWT_LOCK for the drawing borrow. This remains an XID identifier, not a native object retain. Needs logical generation/destruction coordination and real portal modality. A Wayland session environment variable does not turn this AWT XID into wl_surface. |
| Native Wayland parent | Unsupported safe acquisition in the selected Long-only bridge. Actual live surface/display plus export lifetime are missing; the Cargo Wayland feature is not a parent acquisition source. |
| Portal unavailable / zenity, strict requested parent | Current rfd fallback drops the parent. An explicit backend/error policy is required; a requested strict parent cannot silently succeed unparented. |
| Explicit no parent | Remains a separate supported path. Existing parent-0 configuration/cancellation evidence can be reused on exact applicable source, not substituted for parent ownership. |

The finite actual method plan is in [NATIVE_TEST_PLAN.md](NATIVE_TEST_PLAN.md).
None of those methods ran. Initial owning-source criteria remain all five original
#58 bullets; no Linux/Wayland, native thread, focus, close/recreate, heap, ABI,
consumer or security acceptance is inferred from this review.

## Private verification performed

[checks/source-contracts.json](checks/source-contracts.json) records 14 deterministic
source-contract observations from the actual captured bodies; all match. They
verify the review's concrete claims, **not** an implemented ownership protocol.
No new safe-model ownership suite is represented as native acceptance, and no
accepted test suite was replayed. Source check command:

`python3 -B checks/check_source_contracts.py`

Final held-input readback and private artifact hashes are recorded separately.
No refusal-only patch, tracked edit, closure or readiness promotion is delivered.

Final current-source applicability: all 18 frozen inputs remain exact. Seventeen
of the 18 current selected files also remain exact, including all parent-owning
production sources. The lead's concurrent IO integration changed only the selected
`.github/workflows/gradle.yml` input; its Java-version selection lines remain
unchanged, but the workflow is **not** full-file byte reuse. See
[checks/workflow-applicability.json](checks/workflow-applicability.json). This
review does not accept or certify that concurrent workflow change.
