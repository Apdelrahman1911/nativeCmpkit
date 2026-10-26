# IO-023: parent-window ownership design and verification boundary

**Disposition: unresolved. This is a design/source review, not an implemented or
executed fix.** No parenting behavior was removed to make this finding disappear.
The [baseline finding](../audit/findings/IO.json) remains unchanged.

## Direct answer: can the current dependencies support a safe repair?

A **synchronous AppKit ownership repair is feasible in principle** around the
current `rfd` API, provided a genuinely live native parent is acquired first and
its retained window/view are confined to the native main thread. Merely retaining
a pointer *after* dispatching does not satisfy that prerequisite. The current
`ComposeWindow.windowHandle: Long` bridge does not expose a transferable lease.

`raw-window-handle` and `rfd::set_parent` **do not by themselves provide** parent
ownership, generation validation, destruction coordination, cancel-on-parent-
close, or strict failure-if-parenting-is-unavailable. There is no single safe
`Arc`/thread/flag adjustment that establishes all of those guarantees on all
desktop platforms. A complete repair needs an explicit platform acquisition
boundary and, for strict native cancellation/error/backend policy, an adapter or
targeted dependency change plus native tests. Keep IO-023 open until those are
implemented and exercised.

## Reproducible evidence reviewed

[Source-review receipt](evidence/io/parent-window-review.json) records current
project hashes, crate archive checksums matching `Cargo.lock`, and hashes/line
ranges of the exact unpacked files compared with those archives. Versions:
**rfd 0.17.2, raw-window-handle 0.6.2, dispatch2 0.3.1**. No crate cache was edited.
[Selected JVM bytecode](evidence/io/parent-window-jvm-bytecode.txt) records
inspection of Compose UI 1.12.0 and Skiko 0.150.1. It is not a native test or a
complete consumer-resolution receipt.

| Location at this checkpoint | Source-confirmed property |
|---|---|
| `PlatformFilePicker.kt:16–44,58–109` | Current production `pick/save` enters `Dispatchers.IO`, reads `ComposeWindow.windowHandle` and creates/shows the config there. The Kotlin worker owns the **config**, not the native parent. |
| `native/src/lib.rs:122–175` | `ParentWindow` stores raw window/display values and uses unsafe `Send/Sync`. macOS calls `NSWindow.contentView` during creation, then drops the local retained window and view before returning. No native parent ownership is stored. |
| `native/src/lib.rs:178–203` | Windows wraps the number as `HWND`; Linux always wraps it as an Xlib XID with no display pointer. The Linux GTK comment is not the configured backend. |
| `native/src/lib.rs:233–263,403–470` | `DialogConfig::build` passes that raw parent to `set_parent`; the leased config survives the blocking show. This repairs configuration use-after-free, not the lifetime of its pointed-to objects. |
| `rfd/src/file_dialog.rs:20–33,91–102` | `FileDialog` copies raw handles; no lifetime parameter or owner is retained. `set_parent` converts handle errors to `None` with `.ok()`. A fallible adapter must validate **before** calling it or errors silently become no parent. |
| `rfd/src/backend/macos/file_dialog.rs:19–45` and `utils.rs:20–44` | The synchronous picker dispatches panel construction/show to the native main thread. The raw `NSView` is retained and its `window()` resolved **there**, later than our current acquisition. The async API has a different acquisition order and must not be assumed equivalent. |
| `rfd/src/backend/macos/file_dialog/panel_ffi.rs:23–28,52–77` | A panel retains its resolved `NSWindow` and starts a sheet/modal session. This later retention cannot repair an already invalid/detached `NSView` supplied by the caller. |
| `raw-window-handle/src/appkit.rs:47–50` and `borrowed.rs:202–247` | AppKit view access is main-thread-only; its handle is `!Send/!Sync`. Borrowed handles require valid pointers. XIDs explicitly do **not** carry the same lifetime guarantee and can be destroyed/reused externally. |
| `raw-window-handle/src/windows.rs:59–65` | The Win32 constructor documents the current/owning-thread assumption. Copying its number to an arbitrary coroutine worker does not establish it. |
| `rfd/src/backend/win_cid/file_dialog.rs:35–57`, `dialog_ffi.rs:115–117,148–172`, `utils.rs:15–34` | `rfd` initializes STA COM on the current caller thread, stores only the HWND, and passes it to `IModalWindow::Show`. It collapses all returned errors to `None`; the public result does not distinguish native failure from user cancel. |
| `rfd/Cargo.toml:39–58`, `xdg_desktop_portal/window_identifier/mod.rs:24–42` | Defaults enable portal + Wayland, not GTK. The Xlib portal path uses the XID without the display pointer; the Wayland path requires **both** live `wl_surface` and `wl_display` pointers. A bare Long cannot encode the backend/ownership contract. |
| `rfd/src/backend/xdg_desktop_portal.rs:82–113`, `linux/zenity.rs:80–108,142–154` | Failed/unavailable portal operation can invoke zenity. These zenity file/save commands do not forward the parent. Current public `rfd` has no strict-parent/no-unparented-fallback control. |
| `dispatch2/src/main_thread_bound.rs:8–97,145–173` | `MainThreadBound<T>` enforces marker-gated access and main-thread drop; `run_on_main` uses synchronous dispatch. Its documented caveats include missing runloop and lock/shutdown deadlock. It is a useful building block, not a lifetime acquisition proof. |

The JVM disassembly confirms this chain:

```text
ComposeWindow.getWindowHandle
  -> ComposeWindowPanel -> ComposeContainer -> rendering mediator/layer
  -> Skiko HardwareLayer.getWindowHandle
  -> useDrawingSurfacePlatformInfo / useDrawingSurfaceInfo
       lock drawing surface
       obtain native number inside callback
       close surface info, unlock, close surface
       return number
```

`ComposeWindow.dispose()` calls `JFrame.dispose()` and disposes its Compose panel.
Keeping the Java object alive therefore does not prevent explicit destruction of
its native peer. The drawing-surface borrow is already over when the getter
returns. JVM bytecode does **not** prove the native C/C++ pointer type, native
thread dispatch, or AWT-peer lifetime rules; those remain prerequisites for the
acquisition bridge.

## Required contract, before implementation

1. Distinguish an **explicitly absent parent** from an unavailable/stale/unsupported
   requested parent. The latter is a typed failure, not silently parent 0 or the
   currently focused unrelated window.
2. Bind each accepted launch to a logical parent identity and a native **generation**.
   Replacing/recreating the window invalidates its old binding. It must not cause
   an old launch to attach to another window that reuses the native number.
3. Acquire native ownership while the windowing system still guarantees the
   source borrow. An EDT snapshot/`isDisplayable` check, Java strong reference,
   mutex around the Long, or `dispatch_sync { retain(oldPointer) }` alone is not
   that guarantee.
4. Hold a valid binding through native show and result conversion. Release once,
   on the required native thread, after the final in-flight user of that binding.
5. Define parent-close behavior: reject a not-yet-shown launch; invalidate delivery
   and safely finish/cancel an already-visible sheet/dialog. If prompt native
   dismissal cannot be implemented using the chosen backend, state that limitation
   explicitly; coroutine cancellation is not native dialog dismissal.
6. Never synchronously wait for native-main work while holding a registry/AWT
   lock that the main thread needs. Never block the event thread through a wait
   that itself requires that event loop to complete. Shutdown/drain is part of
   ownership, not an untested destructor detail.

## Proposed bounded implementation sequence

### 1. Introduce an internal platform binding, keeping public facades

Use a conceptual `ParentBinding.None` or an owned `(platform, token, generation)`
binding, obtained from the actual `ComposeWindow`/peer on its supported acquisition
thread. A token is not a reinterpretation of the old raw Long. Keep public
packages, facade signatures, JNI names and legacy descriptors; any additive JNI
entry points/ABI version requirement need the build/consumer owner's review.

First verify the Skiko/AWT native peer API for an acquisition that extends the
borrow through ownership transfer. Possible approaches require review:

- A small JAWT/platform bridge that acquires/retains within the existing live
  drawing-surface/peer boundary, respecting its thread/lock restrictions.
- A registered native parent owner established while the window is known live,
  with a generation linked to the logical Java window and close/recreate events.

Enumerating live `NSApplication.windows` on main and matching a numeric pointer
before dereferencing can avoid blindly messaging an invalid address, but **does
not independently solve numeric reuse or prove it is the original logical parent**.
Do not present that shortcut as a complete acquisition/generation protocol.

### 2. AppKit: keep owners and borrowed use on native main

Once acquired safely, retain both `NSWindow` and its `NSView` in a marker-checked
main-thread owner, potentially `MainThreadBound`, rather than our unconditional
raw `Send/Sync` wrapper. Store only the owned binding/token in cross-thread config
state. At show time, on native main, validate generation, close state, and that the
retained view is still attached to the expected window **before** exposing a
temporary borrowed handle. Build and invoke the **synchronous** `rfd` path within
that same main-thread ownership scope; don't return a raw handle for later use.

The existing synchronous `rfd` path can retain the window when building the panel,
but it does not expose the actual panel or a cancellation handle. Guaranteed
close-driven sheet cancellation/result classification may need a narrow native
panel adapter or a separately attributed `rfd` enhancement, not a generic
`AsyncFileDialog` substitution. A change must preserve focus/modality and handle
native main-loop reentrancy.

Retain/release notifications and the last config lease must not hold registry
locks during native-main dispatch. `MainThreadBound::drop` dispatches synchronously:
either arrange explicit main-thread disposal while the app loop is alive or
design a tested release/drain protocol. Moving a deadlock into `Drop` is not a fix.

### 3. Windows: prove the actual HWND owner thread and destruction contract

Do not assume AWT EDT equals the native HWND-owning toolkit thread. Measure the
actual owner, dispatch there through a supported peer/native mechanism, and keep
COM apartment requirements explicit. `IsWindow` is only a point-in-time query;
it neither retains an HWND nor prevents handle reuse. Holding a Java reference or
starting another STA worker is also not parent lifetime ownership.

Define and test how close/dispose/recreate is coordinated with modal use. If
cross-thread HWND use is intentionally supported by an adapter, its proof must
come from the relevant native contract and runtime tests rather than suppressing
`raw-window-handle`'s owning-thread premise. `rfd` currently discards HRESULT error
details, so strict failure-versus-cancel handling also needs an adapter/dependency
change. Windows is not certified by Linux Rust compilation.

### 4. Linux: identify backend; don't manufacture Wayland pointers

For an established X11/XWayland AWT backend, use the actual XID in the portal
identifier and exercise real compositor/portal parenting. XID destruction/reuse
is a protocol/runtime concern, not automatically a dangling-memory proof. Native
Wayland needs a supported source of both surface/display and an exported parent
handle lifetime; the current Long-only wrapper cannot provide that.

The existing zenity fallback does not preserve parenting. A strict parent promise
therefore requires a supported backend selection/error policy, parent-aware
fallback where supported, or a typed unsupported/unavailable result. Do not merely
set all Linux parents to 0 or advertise Wayland parenting because the Cargo
`wayland` feature compiles. Backend changes are separate from the config registry
and require focused review rather than a silent switch to GTK.

## Verification plan and acceptance evidence

| Layer | Required checks; none are claimed by this plan |
|---|---|
| Pure owner protocol | Deterministically stop before acquisition, after acquisition/before native show, during show and before final release. Race cancellation, double close, disposal and generation replacement. Assert exact acquisition/release counts, no stale token reuse, no delivery after disposal, and typed failure for requested-but-unavailable parent. These tests alone do not prove native ownership. |
| JVM/peer acquisition | Actual visible `ComposeWindow`, immediate launch, two parents, parent swap and dispose/recreate. Record EDT/native owner thread and native identity/generation without guessing. Verify the live borrow spans ownership transfer. Test direct `dispose()`, not only a cooperative close callback. |
| macOS native | Real NSWindow/NSView and visible pick/folder/save panels. Main Thread Checker plus supported sanitizer/lifetime instrumentation; close/recreate in every acquisition/show gap; detach/change content view; repeated modal cycles; nested callbacks; focus restoration; shutdown while work is pending. Track retained-owner release on native main after the last show lease. |
| Windows native | Real AWT parent HWND, recorded owner thread/COM apartment, visible owned dialogs, close/recreate and focus/stacking, forced native dialog failure distinct from cancel, repeat launches after cancellation and app shutdown. Include supported Windows architectures in packaged JNI consumers. |
| Linux native | X11 and XWayland with a real portal/compositor; native Wayland only if a valid surface/display acquisition is implemented. Inspect actual portal parent identifier and modality. Exercise portal unavailable, zenity fallback, parent destruction/reuse and no-parent launch; assert no silent unparented fallback under a strict-parent request. |
| Packaging/compatibility | Immutable source SHA, host-specific native payload hashes, new/retained JNI symbols, mismatched payload rejection, JVM facade/API dump and packaged consumer. Log exact backend/toolchain/test counts rather than using `NO-SOURCE` or compilation as runtime evidence. |

Current Linux evidence remains the five Rust registry/path tests and two
**parent-0, non-GUI** JNI smoke tests described in [IO.md](IO.md). They must remain
green, but they do not execute this plan's native-parent acceptance criteria.

**Implementation boundary still outstanding:** a supported, generation-safe
native-parent acquisition from the window peer, native close/dispose coordination,
strict backend/error behavior where promised, and actual platform runtime tests.
Do not close IO-023 or satisfy the preview gate with this document alone.
