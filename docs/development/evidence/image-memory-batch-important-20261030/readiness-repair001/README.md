# Owning image-profile readiness repair (2026-10-30)

The previous real Darwin attempt remains failed: two accepted stress methods,
one profile-workload timeout, and **zero Instruments/leaks commands**. Its generic
preflight failure and late buffered request did not identify a proven native defect.

The actual native workload now exclusively creates a unique mode0600 app-private
PID witness using pinned bytes, a bounded write and guaranteed descriptor close.
The host polls that file independently of buffered console output, verifies its
regularity, UID/mode, unchanged inode/mtime/size and bounded PID, and correlates
the native-console/launch/tool PID. Exact installed executable/path/hash checks
remain intact. Errors name a fixed preflight stage without exposing private text.
Owned readiness/ack/private-tree cleanup is required. Original210-second/4096-round
GC, pixel, color-space and allocation assertions are unchanged.

Important tooling: initial red1 retained; shared165 remains **failed** (163passes,
two stale fixture expectations); only the two owning corrections rerun, **2/2pass**.
The successful163 methods are not replayed. All980 selected inputs held. The
real Python pipe/file handoff uses **synthetic** native PID/frames/Apple tools.
Exact Kotlin2.4.20 POSIX metadata inspection is not compilation.

**Zero new local Gradle/KLIB/native/Instruments/leaks executions.** The new finite
`ios-image-profile-recovery` requests only the failed profile workload under
explicit Darwin tools. Two accepted native stress bodies/shared helpers remain
byte-identical; the independent three-case and failed strict-startup profiles stay.
#140/#141 remain open. No sanitizer, native profile, issue or release pass inferred.
Single agent, maximum two heavy hosted requests,8GiB reserve; no publication,
releases, deployments, Pages, history/main changes or release/security-gate waiver.
