# Android host CI owning-build repair — 2026-11-06

## Original failure and scope

[Run42157111562](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42157111562)
at `c5415b61acb68229d8c56e8b9f43c6a582251b13` failed in the init script
(line9): `Expected the exact Android host Test task in the selected execution graph`.
Job127693778583 produced zero artifacts. The guard refusal is confirmed; whether
the selected task was missing or wrong-type, and which build graph triggered it,
are **unknown**. Do not rerun the unchanged revision or treat this as a host-test pass.
The earlier R4 `BUILD SUCCESSFUL` observation remains separate; its fresh XML and
method outcomes are not established.

## Related root-cause repair

The global init graph guard had no owning-settings-build scope despite the declared
`includeBuild("convention-plugins")`. The repaired
[workflow](../../../../../.github/workflows/android-camera-lifecycle-host.yml)
qualifies the canonical invocation checkout before output/capacity setup and installs
the exact Test/JUnit hook only after the owning settings root is qualified. Only the
declared plugin composite is exempt; an alias that canonicalizes to the owning root
cannot bypass its guard. Foreign roots still fail. Missing/wrong-type owning tasks
are distinguished without exporting native payloads or weakening execution criteria.
This confirmed applicability gap is **not** asserted to be R5's actual cause.

The exact two method selectors, fresh no-cache execution, finalized required JUnit
location, no-match/failure refusal, strict two-case XML collector, and report-only
upload are unchanged. The original nine source/collector methods remain unchanged
and are reused, not reexecuted. Library APIs, packages, versions and production
sources are unchanged. Minimum `contents: read` permission is retained.

## Focused verification

Only NEW10/11/12 source controls executed once: **3/3**, no failures/errors/skips,
suite0.005005s/outer0.153914s, child0,
complete915B capture. Seven declared model/worktree endpoints
held all ten identity fields; the owned child group and runtime are absent.
Actionlint1.7.12 checked the exact changed workflow once: exit0,
0.006081s, zero diagnostics. These checks execute **zero Gradle,
Robolectric or device/native methods**. Independent777 source and saved-result review accepts this exact patch;
the changed immutable hosted request still remains required.

A guessed sparse build-file preflight refused before model creation or tests; its
unneeded dependency was removed, with no tree discovery or source application.
Original R6's unexecuted owner-alias weakness and all R5 failures remain preserved
in the private author/lead evidence; no source failure was rewritten as success.

## Required next

Authenticate changed hosted run/attempt/job and exactly two fresh passing host XML
cases before host acceptance. Host NEW2 does not itself close native Dont-keep C1
(#13), Android Camera current-owner A→B (#76), or their other original criteria.
ROOT remains isolated; producer42142584633 remains failed/nonreusable and cannot
authorize native reuse. The original164 audit findings remain
unchanged; no finding, issue, package, release, deployment or Pages closure/publication
is made by this source-only patch. Follow the grouped roadmap and preserve history.


## R6.1 host NEW2 authenticated at a34 — 2026-11-06

[Run42160522539/attempt1/job127704827219](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42160522539/job/127704827219)
**succeeds at immutable `a34a0abb5967959918a771d9ad7619124c24b8e5`**.
Artifact13477235688 has one allowlisted [732B raw JUnit XML](r61-host-new2-42160522539.xml):
two unique passing Android JVM/Robolectric host regressions, zero failures/errors/skips,
suite10.38s (cases6.336s and2.189s). Actual exact Test and owned report/scope markers
are fresh; the whole43-line init echo matches accepted R6.1 source, excluding command
echo from execution events. [Compact run/test/warning receipt](r61-host-new2-42160522539.json)
binds the exact run/attempt/job/artifact/HEAD and original hashes. Source/FIRST3/Actionlint
acceptance is reused, not replayed; this documentation adds no tests or acceptance gate.

Actual warnings are retained additively: **12 Kotlin `w:` heads +1 action warning**
(four unavailable native/cinterop heads with continuations, six expect/actual Beta heads,
two deprecated test-API heads, one Node20→24 setup-android runtime head). Lead's narrow
original `warning_count0` receipt stays unchanged; the build is not warning-free.
Neither warning suppression nor vulnerability/native-failure inference is justified.

Both passive reviewer write0 refusals remain recorded: leading UTF-8 BOM at log line1
and exact-empty YAML heredoc lines75/82/95; these are not hosted/source failures.
The failedR5 run42157111562 and earlier source-only records remain unchanged; R5's
actual root/selected-task operand is still UNKNOWN. Host NEW2 does **not** prove device/native
Dont-keep C1, active A→B capture, whole #13/#76/#19/#107 acceptance, or #58 recovery.
Empty XML properties do not independently encode SDK level. No closures, Apple/other-platform,
packaged-consumer, release/security-readiness or publication acceptance. Any later evidence
commit records this a34 result; it does not rebind the accepted execution to the docs HEAD.
