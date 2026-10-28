# NativeCmpKit packaged desktop WebView consumer

Independent **WebView-only** verification, not a sample, the successful Core/IO
consumer, or the full21-root release gate. Two real public tests run with both
Gradle module metadata and POM-only resolution in separate fresh Gradle/HOME/tmp
directories. Each consuming host explicitly selects its own six JavaFX21.0.13
classifiers. The public Compose WebView attaches to a real window and JavaFX
engine, loads Unicode HTML, evaluates typed JavaScript and disposes its owner.

Run `scripts/ci/webview_consumer.py` from a clean immutable producer with no
existing `build/verification-repo`. It refuses stale staging instead of deleting
it. Keep other staging evidence; use a separate clean worktree when necessary.
The controller stages two actual local publications, verifies held package and
resolution bytes and saves fresh XML/receipts only. No registry publication,
release, device/minimum-platform, exhaustive ABI or dependency-trust claim.

The configured five-host workflow requires Linux x64/arm64, macOS x64/arm64 and
Windows x64. Linux requires a real display, usually `xvfb-run -a`. A missing
graphical/native runtime fails; tests do not use assumption skips or substitute
internal owners. Cross-host dependency-selector comparison is reviewed separately.
