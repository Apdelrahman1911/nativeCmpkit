# Actual Material dropdown matrix —15 accepted, one failed

[41015763086](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41015763086)
at `36ec139b2a0e6ead1b161abcd72afef493d7665d` remains **FAILED**.
[Independent review](review.json):16 fresh target executions,15 accepted.

| Actual target | Result | Gradle exit/time |
| --- | --- | --- |
| Linux Desktop |4/4pass|0/220.06s|
| Chromium JS |4/4pass|0/356.10s|
| Chromium Wasm |4/4pass|0/319.08s|
| API35/x86_64 Android, Enforcing |3pass/1fail|1/85.04s|

All917 library before/after inputs and994 combined inputs match exact historical
Git. The Android controller's owned-emulator clean shutdown passed. Actual offset/
RTL, caller long-menu scrolling and independent-Material raster comparisons pass
on all four targets; Desktop/browser focus/back/outside checks pass.

Android's failed `focusAndDismissalPropertiesControlActualBackAndPointerEvents`
fails at `MaterialDropdownPlatformTest.kt:46` on the **first input injection**
(shared scenarios187), before dismissal assertions: `injectInputEvent` returned
false. Its precise native rejection cause was not separately logged. Source
inspection establishes that the two-argument KeyEvent has zero timestamps/source;
that is a fixture defect, not a proven InputDispatcher diagnosis or popup defect.

[Owning Android repair](../android-native-input-repair001/README.md) prepares
current uptime/explicit keyboard identity and a single failed-method recovery.
Do not rerun the15 accepted executions. **#132 stays open** until that actual case
and all original criteria pass. Reports-only sanitized XML; no raw ZIPs/logs/
images/packages. No physical/minimum/other OS/browser/iOS/accessibility/ABI/
consumer/security/release certification or publication/Pages/main/history change.
