<!-- nativecmpkit-resolution:NATIVE-001:40596231788 -->
## Verified resolution — NATIVE-001

`DesktopWebViewOwner.navigate(StopLoading)` now calls `engine.loadWorker.cancel()` explicitly on the FX thread. The stop branch has one direct native call and does not invoke `navigator.stopLoading()` or emit another event; public `stopLoading()` is retained.

**Both original criteria accepted:**
- The existing real slow-HTTP/JavaFX regression observes actual stopped loading and exactly one consumed stop command, without feedback.
- The new real native-window regression mounts the production JFXPanel/owner in a visible JFrame. Two blocked HTTP requests verify attached stop, detached queued stop delivered on reattachment, repeated idle stops and no replay on a later attachment. Actual Worker cancellation transitions and command counts are asserted; owned listeners, collectors, HTTP threads and window are cleaned up.

[Immutable Linux/Xvfb run40596231788](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40596231788) at `4fb7d886d533610c7e4bf55535ea980ff050a144`: **37/37 actual methods**, **seven fresh XML**, all eight JavaFX methods and both mandatory stop cases passed; Gradle exit0/245.07s. Reviewed all734 selected inputs against exact own-Git blobs, command/task execution, fresh XML hashes/timestamps, retained36 previous identities and matching setup/during-test SDK/runtime fingerprints.

Closing directly after required-test/source/result review, before documentation bookkeeping. This is actual JavaFX/AWT native-window integration, not public Compose disposal/GC certification. Cancellation transitions plus the one-call source branch are not instrumented counts of every Worker invocation. Other-host/minimum-platform, Chromium/Apple/ownership, cookie/security, legal/dependency, packaged consumer/API-ABI and release gates remain independent/open. No packages, releases or deployments published. Original issue body/title/labels/history preserved.
