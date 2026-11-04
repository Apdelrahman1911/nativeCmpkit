# EventKit related permission batch —605, 2026-11-04

Owning isolated branch: `development/batch-permission-native-20261104`, based on
**f566078507bbfc000244561ed925565913c3342b**. Local source results are from the
held dirty candidate, not immutable release or hosted native evidence. The lead
coordinates integration/CI and reviews the actual native originals before any closure.

## Demonstrated source cause and minimal fix

#22/PERM-011's numeric iOS17 gate and #110/PERM-012's separate read/full versus
write-only modes were already implemented. Their remaining request boundary
still invoked EventKit with no selected host purpose-string check. A consumer
with missing/blank/non-string configuration could reach native privacy failure
outside Kotlin exception handling; the exact OS failure was **not reproduced here**.

Two production paths change:

* `CalendarPermissionPolicy.kt:16–22`: map each existing request kind to its one
  exact usage-description key and require a nonblank string, not another mode's
  key. The old `calendarRequestKind` and `calendarSnapshot` implementation bytes
  remain unchanged when the additive declarations are removed.
* `CalendarPermissionHelper.kt:12–70`: read `NSBundle.mainBundle` via localized
  `objectForInfoDictionaryKey`; check immediately before request selector dispatch.
  Refuse missing configuration once with Boolean `false`/`ConfigurationError`;
  subsequent snapshots expose `PrerequisiteRequired` only for otherwise-requestable
  native authorization. Already-granted/denied/restricted native gate semantics
  remain. Request, callback state and snapshot reads are Main-confined, including
  direct/background helper entry; public signatures/registrations are unchanged.

No legacy-key/broader-access fallback, replacement backend, sample test,
deployment minimum increase, dependency/API rewrite or workflow change is included.

## Important executions — actual originals retained

| Execution | Actual result | Scope |
|---|---|---|
| NEW8 `test_ios_calendar_configuration` |8/8 once; unittest0.002s/wrapper0.3519721s| Source guards only, not native |
| NEW3 `CalendarConfigurationTest` |3/3, one fresh XML, failures/errors/skips0, suite0.047s| Real JVM/common configuration code, not native approval |
| Calendar iOS production/test KLIB compiler + above Desktop task |Actual Gradle exit0/89.1429707s; JDK17.0.20/Gradle9.7.1; calendar compiler tasks execute, core Desktop FROM-CACHE is not a fresh compile| Linux typechecking, **ZERO Apple link/native execution** |

All **1,339 own-branch** library/build/tooling source hashes hold before/after
both source controls and compiler/common-test invocation. This map is not the
lead's different branch map merely because a count happens to match. Compiler
XML contains exactly the three new method identities; the previous five common
capability-policy methods/native populations are not replayed. Read actual
commands/exit/environment/disk values in `gradle-first.json`; originals/logs/XML
are retained. `review.json` records passive source/results checks, not more executions.

All six `w:` entries remain visible: one disabled-camera-iOS task, two WebView
cinterop/cross-compilation notices, one disabled-Native-target notice, unchanged
core `MutableMultiplePermissionsState.ios.kt:43` unused expression, and test-only
`NativeCalendarConfigurationTest.kt:188` **BetaInterop opt-in** warning from
`NSString.create`. No warning is suppressed or treated as compatibility/security
clearance. The 8GiB local reserve holds (11,233,914,880→11,207,897,088 free bytes).

## Prepared native coverage and explicit gates

The five new `NativeCalendarConfigurationTest` methods use actual EventKit
selectors/current authorization, public registrations, Foundation localized
fixture bundle lookup, real Darwin background/main queues and Main run-loop
barriers. Fresh actual `NotDetermined` plus no MainBundle calendar keys are
mandatory, fail rather than skip. Local fixture contents are synthetic, removed
in `finally` and never treated as the OS application's purpose strings. No events
or calendars are read/written; no privacy grant/request/Settings manipulation.
The 10-second run-loop waits are cooperative, not hard deadlines.

The exact [one-host selector proposal](../../../../testing/ios-calendar-permissions.md)
is ready for lead integration; workflow/`library_tests.py`/`workflow_matrix.py`
are untouched here. No actual native result exists yet. #22 still needs genuine
configured/legacy/minimum-OS/deny/restricted/Settings evidence; #110 still needs
genuine write-only/full approval/read-upgrade. Do not close either on this source,
JVM/compiler or future passive-native subset alone. #109/location is not changed
or diluted into this calendar patch. No GitHub mutation, push, CI dispatch,
package/release/deployment/Pages/main/history change or publication was performed
by this agent. All consumer/API–ABI/legal/dependency/security/readiness gates remain.
