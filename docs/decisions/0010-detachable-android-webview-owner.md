# 0010 — Detachable Android WebView ownership outside Compose caches

- Date: 2026-10-29
- Status: accepted; scoped Android runtime verification passed and #10 closed
- Scope: NATIVE-002 / [#10](https://github.com/Apdelrahman1911/nativeCmpkit/issues/10)
- Repair: `b3831693d968d6cd8ef80ba2729a000cca0374a6`

## Evidence and owning boundary

The earlier actual desktop heap proved that a retained state could keep a disposed
native view through predecessor Compose snapshot records. Android/desktop now
store the current native view in an `AtomicReference`, with a primitive observable
attachment version, not historical native-object MVCC values.

After this fix Android's media composition-only unmount still failed native-view
collection, despite passing real playback, slow-connection cancellation and
timer/network shutdown. An actual owned API35 ART heap in run40806868678 identifies
one **strong** retaining path:

```text
active Compose/accessibility owner (expected to live)
  -> AndroidComposeView.root
  -> LayoutNode cached _zSortedChildren / _unfoldedChildren vectors
  -> LayoutNode.interopViewFactoryHolder
  -> ViewFactoryHolder.typedView / AndroidViewHolder.view
  -> destroyed android.webkit.WebView
```

The still-RESUMED Activity's ActivityScenario ownership is expected, not an
Activity leak in this assertion. This is a nearest path, not every heap root or
native-allocation measurement. No raw heaps/values/parser payloads are archived.
See the [reviewed evidence](../development/evidence/webview-lifetime-important-20261029/README.md).

## Decision and execution

Give `AndroidView` an ordinary library-owned `AndroidWebViewContainer : FrameLayout`,
not the native WebView itself. The container has a nullable native owner and the
actual native child. Both are severed on release:

1. Create/configure the original or supplied custom WebView and attach it to the
   container. Publish the **native WebView**, restore its matching native Bundle,
   then call the existing application creation callback.
2. Compose sizes the container; the native child fills it. State, settings,
   navigator and JavaScript APIs still address the original native WebView.
3. Release takes/clears the container's native field exactly once, then saves the
   matching native state, invokes the latest callback, stops/detaches/destroys the
   native owner, and clears matching state without clearing a replacement.
4. An independent cleanup stage removes all container children even if a prior
   native/application stage throws. Preserve the first error and suppressed later
   failures. Failed creation unwinds without fabricating disposal or double destroy.

Source: `calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt`,
`createAndroidWebViewContainer` / `releaseAndroidWebViewContainer` and retained
`createAndroidWebView` / `releaseAndroidWebView` contracts. The holder may remain
cached, but its lightweight view cannot keep the released native resource.

## Alternatives rejected

- Reflection/mutation of Compose layout vectors or accessibility listeners:
  unrelated framework ownership, fragile internals and accessibility harm.
- Forcing another render/mount or closing/pausing the Activity to obtain GC:
  a fixture workaround, not cleanup by composition release.
- Weakening native collection or counting the heap dump's additional GC as a
  pass: hides the original failed runtime assertion.
- Exit the shared toolkit, use global timer pausing, or replace native rendering:
  breaks independent live views or defeats genuine functionality verification.

## Compatibility, risks and tests

Existing public packages, WebView/state/callback signatures and native WebView
reference remain. Android `WebViewState` public JVM descriptors match the pre-fix
compiled class. The additional private FrameLayout changes the native parent
hierarchy; callers must not depend on Compose's internal holder parent type.
This is not whole-library ABI certification. No JNI/framework/resource names,
coordinates, production network policy or publication automation change.

One extra view group per mounted WebView has layout/allocation cost, not a measured
performance claim. Verify actual native bounds and interaction on supported
devices before release; do not extrapolate API35 to all minimum/provider devices.
Robolectric ownership/failure tests are not Chromium memory tests. Current focused
host3/3 and APK assembly pass. The changed Android production path executed all
three important device methods again in immutable40808466133/b3831693:3/3,
one fresh XML, exit0/70.03s,831 own-Git inputs held, JDK17 and cleanly stopped
owned API35/x64 Enforcing emulator. Earlier Android positives were not reused.
Actual native bounds and composition-only collection while the Activity remains
RESUMED pass. Desktop production is unchanged and its20 accepted native
executions are reused. All three original criteria were reviewed before the
direct [completed closure](../development/evidence/webview-lifetime-important-20261029/android020/closure/verified-readback.json).

WKWebView, physical/minimum devices, accessibility/IME, complete API/ABI/consumer,
dependency/provenance/legal/security and release gates remain separate. Do not
apply this approach indiscriminately to other native controls without source and
ownership evidence.
