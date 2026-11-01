# Windows Stop run 41335200671: authenticated original FAILED

Attempt 1 at `41c409c98ccacb7b24ad0cf11bc99be77124b65c` selected the original
Windows Stop method only. Accepted Windows request and Redirect/Reload methods
were excluded.

**One native test failed; zero passed; one original XML; Gradle exit 1 /333.59 s.**
XML suite 15.598 s and method 15.592 s are separate metrics. The original last
FX-poll sample is:

`worker=CANCELLED; running=false; finished=true; cancellations=1; peerEofs=0;
pending=1; arrivals=1; responses=0; closing=false`

Four worker/library comparisons match that sample; actual peer EOF 1 and pending
0 do not. These are sequential last-poll reads, not a simultaneous peer snapshot
or a root cause. The original owning timeout and 10000-ms deadline remain.
Recovery after the refused witness was not reached. Cleanup is source-identical;
no Suppressed cleanup error is in the original XML, and no per-stage native
cleanup readbacks were emitted. Teardown cannot repair the pre-cleanup witness.

Exact artifact 13094949165 matches GitHub ZIP SHA256
`bcce9bcd309f924925b6832d09a34ebd866d80fdffb48cdc144b00825d51e016`. Both actual
1152-path input maps equal the fixed predispatch library map with no differences.
The 1228-path combined map is predispatch-only. The 102 passive authentication
checks are not tests. Original main tooling 2151 /74.500 s is separate from native
outcomes.

Actual Windows Server 2025 /10.0.26100 /x64 and JDK 17.0.20.1 are observed.
The root-daemon receipt records Gradle 9.7.1 /Eclipse Adoptium 17.0.20.1+1 and a
matching configured launcher home. Windows JavaFX/WebKit backend frames are
observed. JavaFX 21.0.13 /`win` is source-declared only: actual loaded Windows
JAR/DLL hashes, resource origins, version readback and URLLoader runtime bytes or
cancel stack are unavailable. Earlier Linux bytecode is not Windows attribution;
JNI and unnamed-module warnings are not assumed to explain Stop.

Original attempt-1 logs and exact evidence were acquired once each. No accepted
method or original 117 was replayed/reacquired. This export performs no new
acquisition, review or execution and omits private acquisition/control filenames,
commands and host paths. Failure and exact scalar observations remain unchanged.

See `REPORT.json`, `CHECKS-SUMMARY.json`, `INPUT-MAP-REVIEW.json` and
`RUNTIME-RESOURCE-IDENTITY.json`. **Issue #64 stays open:** Stop 1, other Desktop 8
and browser offline 2 remain; no closure, readiness, security, consumer, API/ABI
or release gate is lifted.
