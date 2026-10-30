# Android geo permission/provider batch — native execution pending

For open#25/PERM-021, three new library-level AndroidJUnit4 methods:

1. Actual OS denied→coarse→fine grants for only the standalone private test UID;
   actual resumed ComponentActivity lifecycle and default FusedLocation registration
   Tasks from background/Main, duplicate starts and observed asynchronous removal.
2. Real native GMS Task/thread delivery with injected SecurityException/ApiException,
   failed removal, explicit retry and successful registration recovery.
3. Real native pending-start cancellation, duplicate admission, registration-after-
   removal race, replacement and actually queued main-Handler obsolete callbacks.

Only the first method uses the real default GMS transport. Others inject provider
failure/timing and permission accuracy deliberately. This does not cover GPS/fix
accuracy, actual permission revocation/process death, missing/outdated GMS,
settings-off, physical/minimum platforms or native power/heap certification.
Grants are not revoked mid-instrumentation (which can kill the reporter); this
case requires a fresh private standalone test package/disposable owned emulator,
with no background grant or production-manifest permission change.

Seven new synthetic methods pass; seven existing owner-profile compatibility
methods pass after planner changes. These are14 distinct synthetic checks, not
native successes. Preserve the initial7-error red and later6pass/one split-comment
assertion failure; source/criterion was not relaxed. Actual Actionlint1.7.12 and
both real planning CLIs pass. Original full six-module/all11-slot matrix retained.

Local JDK17 APK assembly passes0/40.01s with all1007 combined inputs held.
Device test compiler executes; unchanged production compile is UP-TO-DATE.
**ZERO native tests**; actual parsed APK contains two foreground permissions and
nonexported test Activity, targets the retainedcalfgeo.test namespace. Earlier
empty piped path attempt and incorrect private namespace assertion remain failed;
only discovered actual output inspection was repaired, no build/source replay.

Finiteandroid-geo-provider requests only these three methods, no accepted GC/
host/portable replay. #25 stays open until native/original-criteria review;
87closed/85open. Single-agent/max2heavy/8GiB; no package/release/deployment/Pages/
main/history or ABI/consumer/dependency/legal/security/readiness gate changed.
