# Real component/process ownership repair; no new native pass

The first [actual restoration run41095539115](../restoration-ci001/README.md)
at `c54d0283` executes four methods, **0/4 pass**. Every method fails at
`AndroidCameraRestorationTest.kt:106` before client launch: component `pm enable`
stdout is empty; default-state cleanup also refuses. **The underlying empty reply
cause is unknown.** It is not an established library restoration or shell-quoting
failure. All prior failed results remain failed.

Only four test/controller guard sources change. The recipient's real UID now
controls **only** its own fixed disabled component using the actual SDK, with
signature/UID/nonce-bound finite operations, original DEFAULT/lease retained
before mutation, `DONT_KILL_APP`, exact state/effective-enabled readback, rejection
of foreign/unknown/live ownership, and restoration **before binding close**.
There is no root, generic component RPC, manual URI grant or silent fallback.

A separate source-confirmed fixture defect used quoted `run-as ... sh -c` through
UiAutomation. Android15's [public implementation](public-uiautomation-source.json)
uses `Runtime.exec(command)`, without shell-quote interpretation. Earlier methods
never reached it, so it did **not** cause their component failure. Replace it with
real kernel `Os.stat`, refusing EACCES/unknown errors as absence; bounded closed
cmdline reads verify same native UID and exact client name before SIGKILL.

Three initial synthetic reds are retained. Final **15/15 important synthetic
methods** and Actionlint pass; these overlap the earlier14, not29 unique tests.
`compile001` fails before Gradle because installed Rust was absent from the
login-shell PATH: **zero compiler/native executions**. With explicit known
Cargo/JDK17 paths, `compile002` compiles reporter0/33.01s and receiver0/12.0s.
After native process repair, `compile003` compiles reporter0/32.01s; unchanged
receiver compilation is **reused**, not replayed. All987 library/1064 combined
inputs match reviewed before/after snapshots; receiver applicability is explicit.

**Zero native executions of this repair; #13 remains implemented/open.** Next
request only the four failed API35 restoration scenarios, not accepted provider,
IO, host or unrelated suites. No production API, physical camera/minimum/vendor,
packaged/ABI/heap/security/release, publishing/Pages/main/history or single-agent/
8GiB/max-two-heavy-request gate change. Private logs/binaries stay outside Git;
failed outcomes, public source citation and private-log hashes are preserved.
