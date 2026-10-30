# Library-owned iOS WebView application tests

The `calf-webview` iOS test sources now include a **test-only candidate** genuine
UIKit host. Execution is not yet verified; consult the
[batch evidence](evidence/webview-lifecycle-batch-important-20261030/README.md).

## Execution and ownership

1. `applicationDebugTest` links the library's real production/test code and local
   Apple KVO cinterop. Its entry point is
   `com.mohamedrejeb.calf.ui.web.internal.nativeApplicationMain`.
2. `iosSimulatorArm64ApplicationTest` uses the existing finite
   `scripts/ci/ios_ui_application.py` transport and KGP's actual JUnit parser.
   It requires macOS and an explicitly selected, observed booted simulator.
3. A uniquely named Objective-C delegate starts `UIApplicationMain`, waits for
   the active attached owned UIWindow, and runs the real generated test registry
   on one owned Worker. UIKit/Compose/WebKit actions and predicate checks run on
   the live native main loop, not a command-line Skiko scene.
4. Each test installs a real `ComposeUIViewController`, waits for actual
   appearance/committed composition/Recomposer idleness, and uses the public
   `WebView` to create real WKWebViews, delegates and KVO observers.
5. Assertion and cleanup failures preserve the primary cause. Cleanup restores
   only the owned root; the transport requires actual Worker termination, linked
   and installed-byte identities, same runtime/SDK/source, fresh exact XML and
   absence of the owned app after uninstall.

The host is derived from the accepted `calf-ui` host with package/delegate/class
renames and a provenance header only; a synthetic guard compares every remaining
statement. That byte correspondence is **not** certification of its new module
linking or runtime. The WebView owns the separate `native-webview-application`
receipt directory. Reports-only artifact upload excludes applications/private
logs. Public packages/frameworks remain unchanged.

## Focus and acceptance boundaries

Workflow profile `ios-webview-lifecycle`, focus `webview-ios-native-lifecycle`,
selects six WebView methods plus four owning host methods on one Apple host.
No accepted unrelated test replay. An unfiltered WebView application run still
requires all ten methods; missing/stale/duplicate/skipped/failed XML and partial
protocols fail closed.

Tests cover creation/remount, stable state/callback/navigator replacement,
native typed JavaScript including off-main invocation, actual configuration
truth tables and Unicode/base-URL content parity. Native configuration flags
are **not** physical swipe/video evidence. No network/authentication/redirect,
minimum-OS, device matrix, memory profile or packaged-consumer/ABI/release gate is
cleared by this candidate. Samples are not library test substitutes.
