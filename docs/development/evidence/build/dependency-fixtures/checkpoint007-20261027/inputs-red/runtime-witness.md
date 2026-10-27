# Passive runtime witness for a future BUILD-007 fixture005

**Status: observer003 offline-only diagnostics correction; fixture005 not yet executed.**
Routine verification is now authorized by the owner's 2026-10-26
[policy update](../../docs/development/containment.md), without subagents.
That authority does not waive the reviewed runtime/ownership prerequisites.
The six checkpoint006 inputs remain frozen and independently reviewed. This
additional helper does not alter them or ordinary build policy. It must receive
independent review and an explicit lead-scheduled slot before the command below
is run. The lead currently owns the Gradle schedule.

Observer001 and its76-test archive remain immutable. Independent review found a
mocked identity-gate false positive: finding a later `-jar`/Gradle-main suffix
did not prove that Java selected it as the actual entrypoint; a prior foreign
main or overriding classpath could be accepted. No unrelated JVM was attached.
Observer002 requires the exact installed-script client argument vector and a
bounded daemon option grammar that consumes **every** argument up to the sole
expected main class. Earlier application targets, alternate launch modes,
argfiles, unknown options and duplicate/overriding classpaths are rejected.
The parser's successful client producer path was later observed in actual004;
the daemon path remains unverified.

## Actual004 and the separate003 diagnostics change

The [immutable actual004 archive](../../docs/development/evidence/build/dependency-fixtures/fixture004/archive-verification.json)
preserves suite exit1/26.715s and observer002 exit1/26.756s. Only bootstrap,
baseline and missing-host-lock ran, Gradle exits0/0/1. The external witness matched
all three installed-distribution clients but attempted **no daemon diagnostic**;
therefore no daemon identity/runtime binding was established.005's unchanged
init guards did compile/run and wrote matching selected Gradle-JVM/environment
receipts. Those receipts are not external daemon identity observations.

The original missing-host verdict is unverified because005 omitted the actual
`TypedResolveException` wrapper. Independently reviewed core006 adds only its
observed dependency-message pair; a read-only evaluation of retained004 then
matches that exact cause. This is not a newly executed fixture or rewritten
successful suite. The other three selected negatives never ran in004.

Observer002 discarded candidate validation failures. Its final generic
`required-observation-input-unavailable` code cannot reveal whether ancestry,
argument grammar, process lifetime or another gate prevented a daemon attempt.
**The actual004 cause remains unknown; no counters are reconstructed for it.**

Observer003 preserves exactly the same process ownership, command grammar,
pidfd checks, one-attempt-per-role rule and complete runtime/fixture gates. Its
only observation change is bounded diagnostics: six fixed stages and an explicit
finite reason-code enum, with each stage/reason count saturated at1024 and a
separate saturation flag. Unknown exception data is mapped to an enum category;
raw exception strings, argv, environments, properties, paths or candidate PIDs
are never added to counters. Counts represent **poll/validation events**, not
unique candidate processes or attach attempts. Earlier rejection counts survive
a later missing-process/input event, even when the last-reason field changes.
No ownership condition is relaxed and no failed diagnostic is retried.

The following command is a **future proposal only**. Source/offline review of
observer003 and a fresh lead GO are required; core006 review is not launch
authorization. Actual005, root/convention acquisition and source-wrapper
observation remain unverified.

## Scope and safety

`runtime_witness.py` never launches, stops or signals Gradle. Its only child is
the selected JDK17 `jcmd`, bounded to five seconds,128KiB diagnostic output and
64MiB maximum Java heap per attempt. It kills/reaps only that `Popen`-owned
diagnostic if needed. The original driver retains the fixture's six-invocation,
300-second total/90-second per-invocation bound, one worker, fresh per-case caches
and8GiB free-disk reserve. The observer itself has a320-second window (maximum330).
Neither helper imposes an OS RSS/network/filesystem sandbox.

The exact fixture suite must already be a sibling under the observer's parent:
same selected Python executable, checkout cwd, complete exact CLI, JDK selection
and live PID/start-tick identity. There is no arbitrary-PID observation mode.
Only six known case directories are read. Before an attach, the helper checks:

1. The current/snapshotted six006 inputs, fixture marker and launch receipt.
2. Current UID, Java executable and the complete exact Gradle client argument
   vector, including the JVM options and actual `-jar` entrypoint. The recorded
   client is a new process group/session directly parented by the exact suite.
3. The daemon's fully parsed JVM options, single exact classpath/instrumentation
   agent and actual main class/distribution, its direct client parent, inherited
   process group/session and start order. Children are enumerated only from this
   client's bounded thread list, not by a global JVM/process scan. Linux
   `/proc/<pid>/task/<tid>/children` is per-thread; the main thread alone is not
   complete.
4. Candidate-local cwd, all ten selected private environment paths, generated
   `JAVA_TOOL_OPTIONS`, selected JDK and absence of inherited JVM overrides.
5. Recorded start identity and a live pidfd before and after the diagnostic,
   including revalidation of process ancestry, executable, command and environment.

There is one diagnostic attempt per role, no automatic attach retry. The daemon
can be observed early and is subsequently bound to the exact frozen init
script's `runtime.json`, PID, runtime version, input digest and path observations.
The client and daemon must be distinct in this fixture. Short-lived, missing,
unknown, changed or exited processes stay **unverified**, even if Gradle passed.

Only four selected JVM-property match results, a validated public JDK version,
private relative path names, scoped PID/start identities and evidence hashes are
exported. Raw `VM.system_properties`, command-line and `/proc/.../environ` bodies
are held in bounded memory and never archived/printed. Non-selected properties
cannot be promoted into the report. Java property continuation/escape handling
and duplicate/missing selected keys have explicit offline tests.

`jcmd VM.system_properties` is a diagnostic attach, not a zero-side-effect
filesystem read: HotSpot may start its attach listener/create an attach socket.
The attach API addresses a numeric PID, not the retained pidfd. Pre/post identity
checks and pidfd liveness fail the result on process exit/reuse; they are not a
kernel-level transaction preventing exit between the checks and attach. No
process is suspended or otherwise modified to mask this limitation.

The installed-distribution fixture does **not** execute the Gradle wrapper.
`wrapper_client_observed` and `non_gradle_cache_use_verified` stay false. Even a
successful selected-property witness does not establish Kotlin/Native/compiler
cache consumption, SDK/global-write isolation or production dependency trust.

## Exact paired command — PROPOSAL, NOT EXECUTED

Run only after verifying the independently reviewed helper/checkpoint hashes,
available memory/disk and an exclusive lead-scheduled Gradle slot. Both commands
must run under this same shell; the suite PID comes from `$!`, not a guessed or
globally discovered PID. Keep all source inputs frozen throughout.

```sh
cd /root/projects/nativeCmpKit
set +e
set -u
set -o noclobber
umask 077
destination=/root/nativecmpkit-build007-fixtures-005
witness=/root/nativecmpkit-build007-fixtures-005-runtime-witness.json
suite_stdout=/root/nativecmpkit-build007-fixtures-005-suite-stdout.json
witness_stdout=/root/nativecmpkit-build007-fixtures-005-witness-stdout.json
for path in "$destination" "$witness" "$suite_stdout" "$witness_stdout"; do
  if [ -e "$path" ] || [ -L "$path" ]; then
    printf '%s\n' 'Refusing to overwrite prior fixture/witness evidence.' >&2
    exit 1
  fi
done

JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
python3 scripts/dependencies/integrity.py fixtures \
  --destination "$destination" \
  --gradle-home /opt/gradle/gradle-9.7.1 \
  --case missing-host-lock \
  --case missing-configuration-lock \
  --case added-dependency \
  --case removed-dependency \
  --total-timeout 300 --timeout 90 --reserve-mib 8192 >"$suite_stdout" &
suite_pid=$!

python3 scripts/dependencies/runtime_witness.py \
  --destination "$destination" --output "$witness" \
  --suite-pid "$suite_pid" \
  --jdk-home /usr/lib/jvm/java-17-openjdk-amd64 \
  --gradle-home /opt/gradle/gradle-9.7.1 \
  --timeout 320 >"$witness_stdout"
witness_status=$?
wait "$suite_pid"
suite_status=$?
printf 'fixture_exit=%s runtime_witness_exit=%s\n' "$suite_status" "$witness_status"
test "$suite_status" -eq 0 && test "$witness_status" -eq 0
```

Do not wrap this sequence in `set -e`: the final `wait` must collect the original
bounded suite even if the passive witness fails. Interruption/terminal cleanup of
the fixture remains with the lead/original bounded driver; the observer is not a
second process controller. Never kill an unrelated JVM or the lead's emulator.

Both statuses and both receipts must be inspected. A successful witness requires
all six client/daemon/runtime bindings **and** the expected five selected case
results (ordinary baseline plus four exact lock rejections); an arbitrary nonzero
Gradle exit is not a pass. All-case coverage, wrapper execution, real root/
convention acquisition, independent trust and release readiness remain false.

## Offline checks

```sh
python3 -m unittest discover -s scripts/dependencies -p 'test_runtime_witness.py' -v
```

Tests use synthetic `/proc`/jcmd records plus tiny task-owned Python subprocesses
for pipe-size, timeout, nonzero and cleanup behavior. They invoke **no Gradle,
jcmd, Java or network**. Additional003 tests exercise enum sanitization/saturation
and the modeled outer loop with all proc/identity/attach operations mocked:
candidate rejection, multiple/ambiguous/absent children, later disappearance,
failed client/daemon diagnostics without retry, and complete synthetic bindings.
They do not diagnose actual004's missing daemon or establish a real005 witness.
Passing them is not evidence that an actual Gradle
daemon will satisfy the deliberately strict observed process shape.
