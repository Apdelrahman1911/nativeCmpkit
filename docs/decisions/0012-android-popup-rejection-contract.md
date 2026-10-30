# ADR 0012 — Explicit Android popup rejection

**Status:** accepted implementation, 2026-10-30; actual verification recorded
separately. Scope: NATIVE-038/#90, not a child-window architecture rewrite.

The migrated native setting defaults to `supportMultipleWindows=true`. Our
existing `onCreateWindow` denied requests, but supplied no observable result;
login/payment content could silently fail. Android supplies no trustworthy
destination URL in this callback. A stale `hitTestResult` must not become an
origin or external-scheme authorization.

Retain the setting, native/public names and deny-only default. The current native
owner records one bounded, Compose-observable `AndroidPopupRejection` in
`settings.androidSettings.lastPopupRejection`, then returns false. The result
contains only a per-settings request number and Android's dialog/user-gesture
flags. It retains no native view/message/URL, never delivers the transport,
never launches an external application and never triggers another settings
application. Uninitialized, detached and predecessor callbacks cannot alter the
current owner's result. Engine-blocked requests produce no fabricated result.

`supportMultipleWindows=false` remains the **raw Android current-view fallback**,
not a rendered child-window opt-in or our rejection policy. It may navigate away
from the current page; callers choose that behavior explicitly. Documentation
must distinguish it from the safe deny-only default and must not promise origin
filtering, popup login/payment support or persistent event delivery.

Rejected alternatives: accepting every destination, forwarding a guessed URL to
an external handler, manufacturing child views solely to discover a destination,
or silently changing the retained native flag's semantics. Managed child-window
support requires a separately scoped origin/lifecycle/UI API and verification.

Required important tests: actual blank links and user/script `window.open` with
all JS/automatic/multiple-window flag combinations; default same/cross-origin and
untrusted-scheme rejection; explicit raw current-view navigation/back; replacement,
bounded/latest result and disposal. Host-injected callbacks only verify owning
guards, not native input. See [the implementation record](../development/android-popup-policy.md).
