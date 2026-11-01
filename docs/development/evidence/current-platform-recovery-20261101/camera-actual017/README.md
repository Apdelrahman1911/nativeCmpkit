# Camera actual017: independent terminal/source refusal review

Run 41276792692, attempt 1, immutable source
`55b1a8c361e0b6445e95df989f238310ca0a3eb0` is terminal FAILED.
Only tooling ran. Its offline discovery stopped at one stale owning AST hash guard.
Profile selection and all six downstream jobs, including library/native, were skipped.

## Exact observed refusal

`DocumentedDataDefaultTests.test_only_new_branch_is_exact_pair_and_fixed_launch_has_no_userdata_overrides`,
`scripts/ci/test_android_camera_documented_data_default.py:276`, compares the whole
helper AST after removing the single exact documented-default branch with its
fixed `BASE_MODULE_AST_SHA256`.

The once-acquired original log records actual AST hash
`d4962dd7a931e14522ab8d2cca15700cf0790fad45719793aa5db6e6af88d400`
versus expected
`16e759fc9e1aee42135199be886f8d18553e5264288cb4e0435448d7ae860c2e`.
Independent source-only reconstruction matches both exact log hashes: removal of
only the four added failure observation lines and exact appended
`require_call_origin` yields the old expected whole-module AST. No guarded
state/native/controller or launch change is needed or justified by this failure.

The scripts/ci discovery ran 1,811 methods in 77.403 s: 1,810 passed, one failed.
The three preceding discovery scopes are retained separately, not additive native
coverage. No local suite, accepted method, build, SDK/native or dispatch was run.

## Immutable source and original criteria

All 1,105 library / 1,182 combined frozen map identities match Git at the exact
source. There is no uploaded actual native map: the library job was skipped.
Compared with ff41a932, only the observer helper and its new regression file change
among these inputs; the other 1,180, including native/controller, are unchanged.
The three original issue 13 criteria remain intact and unmet by this run.

Only the original Dont-keep method was requested in committed routing. The three
accepted camera009 methods remain unselected and were not replayed. Actual017
has zero APK builds, AVD launches, native executions, original XML, prerequisite
receipts, source callsite observations or device-cleanup execution. None is accepted
by absence or by a source-only review. The foreground-recreation criterion remains.

## Original custody and privacy

Artifact metadata was acquired once after terminal and reports zero artifacts;
there was no artifact to download. Original run logs were acquired exactly once
and retained privately with SHA256/size readback. Their raw ZIP, console text and
traceback bodies are excluded from this sanitized delivery. The public source
callsite and two exact SHA256 comparisons are the only refusal provenance exposed.
No arbitrary argv, results, dumps, locals, environment or machine paths are copied.
An initial default gh lookup selected upstream and returned 404; the explicit
repository from retained dispatch evidence resolved correctly. The 404 is not an
actual-run failure and was not automatically retried.

This later tooling result does not diagnose earlier actual016's unknown predicate.
No issue closure, source mutation, native acceptance, publishing, Pages, branch or
history/security/readiness waiver is authorized. Lead owns any narrow guard repair.
All payloads/manifest are verified and sealed files 0400, directories 0500.
