# Android camera verification: preserved Settings HOME affinity

## Scope and historical outcome

This is a **test/tooling correction**, not a production camera API change or a
receipt of Android camera behavior. Frozen source:
`ac487941316626cc4b19546ab70f939d98c1c52d`.

[Run 41762135079, attempt 1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41762135079)
remains **FAILED**. The original controller recorded `home-header`, inner
`parse_home_task:63`, caller `snapshot:948`, 19 recents rows and a 13-row task.
Framing and custody passed. The failure-only observation recorded failed
`home_header`, `home_affinity`, `header_rank_and_task_bounds`, and
`task_id_matches_header` predicates. The final two depend on the rejected header;
the independent tail observation recorded equal header/dump task IDs.

The actual raw header/affinity spelling was not exported and **is not known**.
Its reconstructed spelling, installed-image source revision, query ownership,
or actual native root cause must not be inferred from synthetic templates.
Boot handoff and startup hold passed separately. Startup/precompile preparation
and cleanup `close:1405` remained failed; original state was not acquired.
Owned guest disposal passed independently. There was **no Gradle, APK, Android
native testcase, XML, or camera behavior** in this original attempt. Issue #13
therefore remains open.

## Source-confirmed finite template gap

The cached public Android 15 (`android-15.0.0_r1`) Settings manifest explicitly
sets `.FallbackHome` task affinity to `com.android.settings.FallbackHome`.
`ActivityRecord.computeTaskAffinity` UID-qualifies that value; `Task.dump` and
`Task.toString` emit that affinity. Both old owning parsers admitted only the
package-affinity spelling and therefore excluded this source-qualified template.

Cached producer-source SHA-256 references:

| Source | SHA-256 |
|---|---|
| Settings `AndroidManifest.xml` | `79f830779f6d2317dfc97a658d7c1d71ea2b71397bc7b20b6a6a066807ff22ae` |
| Framework `Task.java` | `7892b50f8f82043e1d42f51385f574586489626aedb4706cc9a4632ed5c6ee15` |
| Framework `ActivityRecord.java` | `84266fe352c189be1fdf143a47e0fa5c3d3fee7eb05ac485f14a38e0575f75d3` |

These sources establish the template contract, **not** which bytes the installed
hosted image actually produced. No original payload was replayed through either
candidate parser.

## Owning contracts

| Owner | Change |
|---|---|
| `scripts/ci/android_camera_home_baseline.py` | Admit exactly `1000:com.android.settings` or `1000:com.android.settings.FallbackHome`; require body affinity to equal the captured header affinity. |
| `scripts/ci/android_camera_home_refusal_observation.py` | Observe the same exact equality only after a refusal, without a parser retry, query, admission, or exported raw record. |
| `calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaseline.kt` | Match the Python header/equality contract exactly. |

The header retains existing groups 1/2/3 (recent rank, full stable task header,
task ID); only group 4 (affinity) is new. Full matching rejects extra suffixes,
wrong UIDs, altered case, root affinity rows, and package/specific hybrids.

Every other contract remains: exactly thirteen ordered bounded ASCII rows,
bootstrap user/UID/caller, complete intent and component, no live activity,
finite policies, task/root/clock bounds, object identity, preserved source bytes,
same-epoch baseline equality, installed Settings identity, fresh guest, and
native-action/cleanup ownership. Only recent-list rank and elapsed inactivity
remain normalized. A parsed HOME baseline is **preserved/nonowned**, never a
removable Settings task or permission to launch/mutate native UI.

Public APIs, production sources, native controller actions, workflow, versions,
dependencies, attribution, and history are unchanged.

## Persistent source-history qualification

`scripts/ci/camera_home_affinity_source_projection.py` and
`scripts/ci/fixtures/camera-home-affinity-source-inverse.json` bind seven complete
frozen/current files through sixteen ordered reversible fragments. Final manifest
SHA-256: `51cc224488eb366034f8edea83f1a31465f8818059bad96a802a1fff0aa655ca`.

- `current_source_before_home_affinity` admits only a complete newest raw
  afterimage at the outer checkout boundary.
- `source_before_home_affinity` is an exact reversible ancestor view, not current
  admission.
- `peel_home_affinity_for_history` finitely peels only a known afterimage; unknown
  bytes remain for the next historical pin to refuse.

The shared geometry fixture admits current bytes **once**, then uses ancestor
recovery. Existing dated manifests, pin constants, test methods, and assertions
remain unchanged. Do not run strict newest ingress again on a restored ancestor;
do not replace historical pins with a generic current hash or waive unknown bytes.
These views are used only by source/history controls, not Kotlin compilation,
native task parsing, or CI admission to a real device.

## Important source tests and preserved refusals

First source execution selected 16 NEW + 7 affected methods exactly once:
**21 pass, one failure, one error, zero skips** in 0.288703079 s, with 1,343
inputs held. Both original refusals are retained:

1. The NEW displacement fixture reappended an already-EOF Kotlin fragment,
   yielding unchanged bytes. It now relocates an exact unique fragment to the
   opposite endpoint; no admission guard was relaxed.
2. The shared roundtrip applied strict current ingress twice. It now performs
   one raw-current admission followed by exact ancestor recovery, preserving
   all original assertions.

The initial owning manifest and full before-recovery sources are retained in
the private owning evidence packet. It originally bound seventeen fragments;
the adjacent shared assignments now coalesce into one, yielding sixteen.
Only failed2 + genuinely affected metadata/obligation3 then executed:
**5/5 pass, zero failures/errors/skips**, 0.105142221 s, 1,343 inputs held.
Eighteen applicable first accepted methods are reused, not relabelled fresh
executions. A separate passive source/results review verified 2,768 checks,
including independent complete source enumeration and exact frozen/current
roundtrips. These are **passive checks, not native tests**.

NEW Python parser/controller controls cover both forms, both hybrid directions,
every row, malformed/unknown/unsafe input, bounds, stable-byte normalization,
failure-only observation, Python/Kotlin regex parity, same-owner epoch drift,
and pre-action refusal before any mutating IPC. The controller fixtures are
explicitly inert; they are not Android integration tests.

All eight original Kotlin `SettingsHomeTaskBaselineTest` methods remain
byte-identical. Five NEW library common regressions cover exact forms, hybrids,
finite affinities, live/caller/component/identity/row bounds, and normalization.

## Compiler verification and pending native gates

The explicitly lead-granted serial local slot executed only the five NEW JVM
methods, then the genuinely changed Android test compiler/APK. Both used actual
JDK17.0.20/Gradle9.7.1, exact dependencies from offline caches, two bounded workers,
in-process Kotlin, no parallel Gradle projects, an owned-process 8 GiB disk guard,
and matching 1,343-entry before/after source maps. No forced production rebuilds
or unrelated test executions occurred.

| Verification | Actual outcome |
|---|---|
| `:calf-camera-picker:desktopTest`, five exact NEW method filters | Gradle0 / 34.01 s; fresh `compileTestKotlinDesktop`; one fresh original XML / 5 pass / zero failures/errors/skips. Production restored from cache. |
| `:calf-camera-picker:assembleAndroidDeviceTest` | Gradle0 / 49.02 s; fresh `compileAndroidDeviceTest`; production restored from cache; one local 9,781,149-byte test APK, SHA-256 `53eb9487aff2705e709029783b4e2debd3fe790687556f741406f7073dd509ec`. ZERO Android native executions. |

The first private JVM identity collector returned1 because it incorrectly
expected undecorated XML names, while Gradle returned0 and all five original
testcases passed. That refusal is preserved. A separate passive qualification
inspected the cached KGP2.4.20 `KotlinJvmTest` descriptor bytecode: display names
append `[` + exact target name + `]`, and `Targets.kt` declares `desktop`. It
matched the five exact `method[desktop]` identities, original XML hash, real daemon
and task marker, and held source maps. **No JVM method was replayed**, no generic
suffix stripping was accepted, and neither original result was overwritten.

All four JVM native-configuration warning starts and all nine APK warning starts
are retained. The APK has the same four unsupported-host/cinterop configuration
warnings plus five unchanged device-fixture warnings (parameter names and
deprecated overrides at `AndroidCameraProviderTest.kt:62,73` and
`CameraRestorationVerificationActivity.kt:90,124,175`). No warning was suppressed
or treated as iOS verification. Static APK bytecode inspection finds the parser
class and all five NEW method names; this is **compilation evidence, not Android
execution, signer/security acceptance, consumer integration, or API–ABI proof**.

Original outcomes and source/compile scopes are persisted in
[`evidence/android-settings-home-affinity-20261104/`](evidence/android-settings-home-affinity-20261104/).
The full original NEW5 XML and one complete shared owning source map are retained;
APKs, private paths, full terminal logs, and local machine files are not published.

The five executed methods were:

```text
SettingsHomeTaskBaselineTest.manifestSpecificHomeAffinityAndPreviousPackageFormRemainCompletePreservedRecords
SettingsHomeTaskBaselineTest.bothDirectionsOfHeaderBodyAffinityMismatchRefuseWithoutNormalizingOrMutatingInput
SettingsHomeTaskBaselineTest.onlyTheTwoExactUidQualifiedHomeAffinitiesCanBecomeBaselines
SettingsHomeTaskBaselineTest.manifestAffinityNeverWaivesLiveCallerComponentRowAndIdentityBounds
SettingsHomeTaskBaselineTest.manifestAffinityOnlyIgnoresRankElapsedTimeAndPreservesEveryOtherByte
```

Reuse these accepted NEW5/compiler/APK results only while their applicable
sources, dependencies, configuration, and execution contracts remain unchanged.
Do not rerun them for unrelated iOS selector/documentation deltas, or replay the
old eight methods, camera009 C2/C3, or other unchanged successful populations.
Compiler or APK success remains zero Android native execution.

Only the lead integrates, pushes, and dispatches the remaining C1 on the frozen
development branch after source/results acceptance and a fresh capacity read.
Maximum two combined hosted-heavy reservations **includes queued/reserved work**.
Issue #13 cannot close until all original required native criteria actually pass.
All native/consumer/API–ABI/dependency/legal/security/release-readiness and
publishing/Pages/main/history gates remain unchanged. No packages, releases,
deployments, or Pages publication are authorized by this source correction.
