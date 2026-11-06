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
