# Both isolated slider runs failed — 2026-10-29

Immutable revision `0efbd9fdf6807ad91d796ead78921fda2efc161f`:

| Run | Requested methods | Gradle | Actual completed native methods |
| --- | --- | --- | --- |
| [40884274274](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40884274274) | Cupertino structural + two tap/cancel | exit 1 / 2620.49s | 0 |
| [40884299049](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40884299049) | Liquid structural | exit 1 / 2035.13s | 0 |

Both have one fresh failed Unknown/interrupted XML case. Both reach exactly six
finite structural observations, ending at `axis=1 phase=dragged`, before the
first current-drag assertion/replacement witness. The 300s application deadlines
expire (301.46s / 301.67s). The root cause is **not established**; an assertion
followed by stuck pointer cleanup is a hypothesis, not a confirmed production bug.
The two tap/cancel methods in the first run never start.

Both independent reviews bind all 869 before/after inputs to historical Git,
real CLI plan/command/runtime, artifact digest and installed owned bytes.
External owned stop/uninstall/local cleanup succeeds, but final Worker/runtime/
binary-after certification is missing. Missing PID-bound crash evidence is not
proof that there was no crash. Native JSON and sanitized XML are archived; raw
console logs, ZIPs and distributable binaries are not committed here.

UI-027/#34 and UI-034/#137 remain **open**. The two previously completed,
unchanged enable/callback methods from run 40865834481 are explicitly reused,
not replayed or counted as fresh. No publishing, releases, deployments, Pages,
main/history modifications or independent release-gate waiver follows.
