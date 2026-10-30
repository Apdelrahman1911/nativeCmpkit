# Owning Android input repair and failed-case-only recovery

The actual [matrix](../platform-ci001/README.md) remains FAILED15pass/1fail.
The first Android key injection was rejected before dismissal assertions. Tagged
[API35 public-source inspection](public-source-inspection.json) confirms the old
two-argument KeyEvent supplied zero timestamps/source; the exact native rejection
reason is still unknown. No confirmed popup bug is inferred.

The smallest fixture repair supplies current monotonic down/event times,
virtual-keyboard identity, FROM_SYSTEM and keyboard source. Pointer event times
are actual uptime, not invented future milliseconds. The same native Escape/
touch delivery assertions and MotionEvent/screenshot recycling remain. No direct
menu callback, synthetic passing report, native missing-check waiver or production/
public API change. The accepted raster/scroll/offset/shared/Skiko bytes remain.

A finite `ui-dropdown-android-recovery` profile selects exactly the previously
failed method on Android-device/calf-ui, using the runner's correct `Class#method`
syntax; the original four-method matrix and all11 full slots remain. The prototype
guard's desktop `Class.method` syntax and tautology were corrected during fixture
review before execution. Foreign modules/suites/wildcards/full-suite claims,
missing/duplicate/extra/failed/skipped/unexecuted XML remain rejected.

Actual [one-method source red](first-red.log) failed before repair. Important
[17/17 tooling](important001.log) then passes: eight new owning guards plus nine
existing dropdown guards; [two shared matrix guards](shared002.log) pass separately.
[actionlint1.7.12](actionlint001.log) exits0. These are synthetic/source checks,
**ZERO local library/device/native executions**. `library-before.json` and
`combined-before.json` are pre-repair delta baselines, not runtime freezes. Final
immutable dispatch binds the post-repair inputs separately. No15-pass runtime
replay or full971-success local tooling replay.

**#132 remains open** until the new actual one-case recovery passes and all three
original criteria are reviewed. #62/#89 have independently closed;82closed/90open.
Single-agent/max2 combined heavy requests/8GiB reserve. No publication/Pages/main/
history or independent minimum-platform/native/ABI/consumer/dependency/provenance/
legal/security/release gate change.
