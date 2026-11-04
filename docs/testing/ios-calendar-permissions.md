# EventKit related-issue batch — #22 / #110

This library-level batch addresses the still-unprotected **request-time host
purpose-string boundary** for PERM-011 and retains PERM-012's separate read/full
and write-only paths. It is not a sample application and does not fake OS approval.

## What changed

`CalendarPermissionHelper` checks exactly the selected purpose key on the real
main bundle, using `objectForInfoDictionaryKey` to honor localized
`InfoPlist.strings`. Missing, blank or non-string values complete `false` with
`ConfigurationError` **before any EventKit request selector is invoked**. Subsequent
observations expose `PrerequisiteRequired`, not a permanent OS denial. An already
granted or settings-only/restricted native state retains its original short-circuit
semantics; purpose-key checks apply when a request would actually be attempted.
Both requests and status reads are Main-confined, including direct helper callers.

| Runtime/request | Required nonblank purpose string | Native request |
|---|---|---|
| iOS <17, either mode | `NSCalendarsUsageDescription` | `requestAccessToEntityType:completion:` |
| iOS 17+, `ReadCalendar` | `NSCalendarsFullAccessUsageDescription` | `requestFullAccessToEventsWithCompletion:` |
| iOS 17+, `WriteCalendar` | `NSCalendarsWriteOnlyAccessUsageDescription` | `requestWriteOnlyAccessToEventsWithCompletion:` |

The availability split and separate registrations already existed before this
batch. Their five common capability-policy tests remain unchanged and must not
be represented as new native execution. No public API or deployment minimum changes.

## Important new local tests

Run only the three new common configuration tests, plus the changed calendar
iOS production/test KLIB compiler. Do not use `--rerun` on prior accepted suites:

```sh
./gradlew --no-daemon --console=plain --no-configuration-cache --max-workers=2 \
  '-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8' \
  -Pkotlin.compiler.execution.strategy=in-process -Pkotlin.native.jvmArgs=-Xmx2048m \
  --init-script scripts/ci/fresh-tests.init.gradle.kts \
  :calf-permissions:calf-permissions-calendar:desktopTest \
  --tests com.mohamedrejeb.calf.permissions.helper.CalendarConfigurationTest \
  :calf-permissions:calf-permissions-calendar:compileTestKotlinIosSimulatorArm64
python3 -m unittest discover -s scripts/ci -p test_ios_calendar_configuration.py -v
```

KLIB typechecking on Linux is **zero Apple SDK links/native executions**.
The eight Python controls check source contracts only, not EventKit behavior.

## Finite native selector proposal

The lead owns workflow/registry integration. Register one exact iPhone iOS job
with **only `calf-permissions/calendar`**, using task
`:calf-permissions:calf-permissions-calendar:iosSimulatorArm64Test` and filter:

```text
--tests com.mohamedrejeb.calf.permissions.helper.NativeCalendarConfigurationTest
```

Require all **five** methods below, each reported exactly once by genuine KGP
native XML (`iosSimulatorArm64Test.` class prefix and `[iosSimulatorArm64]` method
suffix), fresh task execution and actual runtime/source/binary agreement:

1. `nativeSelectorsMatchTheRunningIOSVersionAndSelectedRequestKind`
2. `passivePublicHelpersMatchActualEventKitWithoutPromptingOrChangingAuthorization`
3. `freshUnconfiguredPublicRequestsFailOnceWithoutEnteringEventKitPrivacy`
4. `backgroundEntryAndReentrantConfigurationFailuresAreMainConfinedAndRecoverable`
5. `nativeBundleLookupHonorsLocalizedPurposeStringsAndRejectsOtherModeKeys`

The process must be the unconfigured library test executable: no calendar purpose
keys on `NSBundle.mainBundle` and **actual EventKit NotDetermined**, not a configured
sample or reused granted/denied app. These requirements fail rather than skip.
No privacy state is changed, no calendar/event contents are accessed, and the
localized synthetic fixture bundle is deleted in `finally`. The fixture is never
passed to EventKit as an alternative application identity. The main-loop 10-second
deadline is cooperative; it is not a hard scheduling or process-lifetime guarantee.

## Original acceptance criteria still required

| Issue | Required originals | This batch does / does not cover |
|---|---|---|
| #22 / PERM-011 | Fresh iOS16 and17+ legacy-only/full-key grant/deny/restricted/Settings; native linker/availability at documented minimum | Native no-key/selector/localized configuration probes prepared; actual result pending. No consent, Settings transition, old-OS or minimum-link proof. |
| #110 / PERM-012 | Fresh write request asks only for writes; native WriteOnly grants writes not reads; full grants both; denied/restricted stay denied | Existing common mode policy retained; real native selector/current-status probes prepared. Not write-only/full grant or upgrade UI proof. |

Neither issue may close merely because compilation, source controls or these
five passive/configuration native tests pass. Modern configured approval and
read-upgrade require an owned genuinely configured native consumer/application
with actual OS authorization evidence. A simctl fixture or enum injection alone
is not user consent. iOS16 execution requires an available legitimate runtime;
the current Compose/toolchain library minimum remains a separate documented
compatibility decision, not the sample's minimum or a default SDK inference.
Physical-device, all-OS privacy behavior, memory/leak, consumer/API–ABI, dependency,
security and release-readiness gates remain unchanged.

## Accepted current-runtime subset — Calendar 631, 2026-11-04

The preparation text above is retained as its original source checkpoint. The
lead has now accepted [run 41775507254's finite native originals](../development/evidence/current-platform-recovery-20261101/ios-calendar-native631/README.md)
at exact `6fb368eb77a0863cd3d725f75e85d59b41caee71`: **five required methods passed once**, one
fresh native XML with zero failure/error/skip/N/A/foreign cases, **Gradle 0 / 772.65 s**,
actual Darwin arm64/iPhone Air/iOS 26.5 and **1,373 unchanged own-source inputs**.
This documentation reuses the completed original review; it performs no replay.

The result covers only actual current-runtime selectors/passive registrations,
fresh no-purpose-key/NotDetermined refusal once on Main, controlled real Darwin
background/reentrant false delivery, and unique localized native-bundle lookup
with passing finally-removal/absence assertions. The fixture is not the main
application's EventKit identity, and false completion is not OS consent/grant.

Retain the original bootstatus Data Migration Failed before successful Booted
captures, one hosted Node20-to24 warning, missing archived `gradle.log`, and no
final simulator-restoration witness. No UIKit Worker/uninstall or geometry-owned
cleanup evidence is substituted. Compiler/native warning absence is not inferred.

**#22/PERM-011 and #110/PERM-012 remain open/partially verified.** Configured
write-only/full approval/read-upgrade, denied/restricted/Settings populations,
iOS16/17+ fresh configured installs and documented minimum-link/availability
criteria remain exactly as above. Both entries reference the same five-method
subset, not ten tests. No original criteria/state, production/API/dependency or
consumer/security/release-readiness gates change.
