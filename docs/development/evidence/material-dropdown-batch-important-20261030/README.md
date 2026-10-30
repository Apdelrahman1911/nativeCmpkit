# Focused public Material dropdown contracts (#132/UI-026)

Four new library scenarios target Desktop, Android-device, JS and Wasm only:
live12dp/8dp offsets and LTR/RTL; caller scrolling over100 real items; actual
popup pixels against an independent actual Material call (shape, tonal/shadow
 elevation, container and border, with a live-style negative control); and
focus/back/outside policy with exactly-once callbacks. No sample substitutes,
production/public API edits, native/OS accessibility or minimum-platform claims.

[First local diagnostic](desktop-local001/review.json) **FAILED**, Gradle1 /
486.13s, fresh4-case XML: three passes, one input-route failure. All916 library /
993 combined dirty-snapshot inputs held. Compile passes, but the enabled-back
assertion leaves one node; the enabled-outside assertion was not reached.
No production bug is inferred. Compose1.12's popup registers a navigation-event
handler; a semantics Escape key skips its host navigation bridge. The owning
test repair uses an actual public `NavigationEventInput`/current dispatcher,
registered/removed through `DisposableEffect`, not a direct menu callback.
Android retains real UiAutomation Escape/touch and native screenshot APIs.
Skiko covers actual scene/pointer/dispatcher contracts, **not OS Escape routing**.
Only the failed Desktop method needs a local recovery; three unchanged diagnostic
methods are not replayed. An immutable target matrix is still required.

[Important tooling](important-tools001/review.json) retains all initial red/
caller errors and accepts eight original focus guards through7+1 executions,
three owning final-interop/back-route guards and25 shared adjacent methods, with
one overlapping source guard. All917/994 final source inputs held; actionlint1.7.12
and164-record status structure pass. These are synthetic/source/tooling checks,
not library/native passes. The back-route repair remains runtime-unverified at
this checkpoint; Android/JS/Wasm have not compiled/executed these new methods.

See the independent [failed native WebView recovery](../webview-identity-batch-important-20261030/mobile-remount-ci001/README.md).
The paired source candidate now waits for actual captured WKWebView final child/
window/delegate release while its test root remains attached, using the existing
10s bound. It never invokes production cleanup, relaxes the original regression,
or waits for GC. One new Apple-only profile selects just that failed method,
not the accepted Android or other WebView cases. Native recovery remains pending.

**#132/#62/#89 stay open;80 closed/92 open.** Single-agent/max2 combined heavy
requests/8GiB reserve. All publication/Pages/main/history and independent
native/minimum-platform/ABI/consumer/dependency/provenance/legal/security gates stay.
