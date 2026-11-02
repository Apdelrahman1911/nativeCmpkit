# Desktop cancellation candidate: native results and Linux EGL repair

**2026-11-02; ordinary dependencies unchanged; no publication.**
Only the original failed public Stop method runs on each selected host. The
[owning candidate preparation](../javafx-platform-candidate351-361/README.md)
preserves its original ten-second/six-predicate acceptance, pre-cleanup peer EOF,
zero response, same-owner recovery and owned cleanup. Accepted request/redirect,
Windows Stop and browser/mobile methods are not replayed.

## Actual immutable results at `924a06c2`

| Host / run | Original method | Gradle exit / elapsed |
| --- | --- | --- |
| [Linux ARM64 41523697951](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41523697951) | Failed during Compose/Skiko initialization; Stop assertions unreached | 1 / 238.06s |
| [macOS ARM64 41523725059](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41523725059) | **Passed 1/1**, one fresh XML, method 8.785s | 0 / 378.17s |
| [macOS x64 41525181917](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41525181917) | Requested once; original result not yet reviewed at this checkpoint | Pending |

Both reviewed hosts use actual JDK17.0.21/Gradle9.7.1. [Review368](REVIEW368.json)
accepts **36 passive source/results checks**, not 36 new tests. All four actual
1,215-library-input maps and four 18-candidate-input maps equal frozen
dispatch/Git/current source **at that review**, before the later two-path EGL
repair. The original [Linux receipt](linux-arm64/receipt.json),
[macOS receipt](macos-arm64/receipt.json), XML, runtime, plans, compiler streams,
maps and once-only acquisition digests are retained. Full original ZIPs stay
privately cached; none was redownloaded.

The host-produced full-JAR SHA256 values match independently cached packaging:
Linux `144c025cebbcf3539319d62017c0e872ea927335b571a23110da834fff044f85`;
macOS ARM64 `69737ca262f44ad4bbd6cfa56c30afdc9d874e11c8b661ce2a0cabd32c174247`.
Five class pins, original-provider removal and sole candidate replacement hold.
Remote JAR/class binaries were not uploaded: matching producer inventories,
markers and digests are not independent remote-binary inspection.

**Accept and exclude the macOS ARM64 Stop method from unchanged replay.**
The source/result review qualifies the original public navigator's cancellation,
pre-cleanup peer EOF, no response, same-owner recovery and cleanup. This is a
private dependency candidate, not ordinary-consumer adoption or a release gate.

## Confirmed Linux CI prerequisite defect

The original Linux XML reports `org.jetbrains.skiko.LibraryLoadException` with
`libEGL.so.1: cannot open shared object file: No such file or directory` during
`ComposeWindow` initialization. This is **before public Stop/transport
assertions**, not another demonstrated cancellation failure. Candidate packaging
and full-JAR replacement already pass. The original run remains FAILED.

The exact Linux-only prerequisite step in
`.github/workflows/javafx-library-candidate.yml` now explicitly installs
`xvfb`, `xauth`, GTK/audio, `libegl1`, `libegl-mesa0`, and `libgl1-mesa-dri`, then
requires `ldconfig` to expose `libEGL.so.1`. Bash failure propagation remains
strict; no software-renderer override, `|| true`, permission expansion or
native-assertion relaxation is introduced.

One new regression is first [red370](RED370.json), confirming missing `libegl1`,
then only that failed method is [green371](GREEN371.json): **1/1**, seven mutation
refusals, unittest0.001s/wrapper0.264198s. [Actionlint371](ACTIONLINT371.json) passes
on the changed workflow. [Solo review372](REVIEW372.json) accepts 14 passive
checks: only the exact prerequisite body plus one test/import change; every
pre-existing test AST, manual-only/read-only policy and all 1,215 library inputs
remain unchanged. **Zero new local compiler/native executions.** Runtime package
presence is still preparation; Linux native verification remains necessary.

## Issue disposition and next executions

[#64 progress6588525609](https://github.com/Apdelrahman1911/nativeCmpkit/issues/64#issuecomment-6588525609)
was posted once/read back before documentation; [receipt369](PROGRESS369.json)
confirms original issue fields unchanged/open. Remaining native work is only
Linux ARM64 Stop on the repaired workflow and the pending macOS x64 original.
Never dispatch the old pairs or accepted macOS ARM64/Windows Stop again.

The later workflow/test repair changes **two of 18 candidate inputs**, both
outside the library map; all 1,215 library inputs still equal `924a06c2`.
Pending macOS x64 runs the frozen old candidate map: do not falsely describe its
whole 18-input map as equal to the post-repair worktree. Neither path changes its
compiler, candidate bytes, native assertions or macOS execution route.

Ordinary JavaFX adoption, complete native corresponding source, legal/security,
packaged consumers, API–ABI and every original criterion remain separate.
Observed official Maven metadata has no newer stable21 version than21.0.13;
metadata inspection is not independent security/provenance certification.
**97 closed / 75 open / 172 total; no new closure.** Continue solo, serial local
heavy work/8GiB reserve/max2 combined hosted reservations including queued,
development branch only; publishing/Pages/main/history gates remain intact.
