# Android Camera lifecycle/callback host batch — 2026-11-06

This isolated branch adds **two proper library-level Robolectric regressions** to
`AndroidCameraLifecycleTest` (API 23). They destroy a non-finishing real
ComponentActivity while a synthetic camera writer owns the output, reconstruct
from saved state, replace callback A with B without replacing the restored owner,
and deliver success/cancellation through the production ActivityResultRegistry.
Success checks one current callback and readable exact output; cancellation
checks one callback, removal of only the pending output and a surviving sibling.
Both suppress destroyed/replaced callbacks, disposed relaunch and duplicate result.
The five existing method bodies are byte-identical; they are not replayed here.
No production/API/native-criterion bytes are changed.

## Verification and scope

- Three new Python ingress controls passed **3/3 once**, suite0.014s,
  child0.11591022810898721s/outer0.2978749810718s, exit0/full EOF.
  Independent saved-results review accepts42 unchanged originals,137 finite runtime
  inputs,14 unchanged model copies and owned cleanup14files/28directories/group absent.
- First workflow Actionlint fails because `runner.temp` is not available in job.env.
  Four exact context edits move the binding to the two run steps and the artifact
  path. Changed Actionlint passes once, exit0/empty output. The original failure stays.
- **Robolectric NEW2 is still unexecuted at this source freeze.** The manual/exact-isolated-branch-push
  `android-camera-lifecycle-host.yml` runs only these two methods. Its owned init
  script disables cache/up-to-date only for that Test task, retaining production
  caching. Exactly one fresh XML report must contain the two declared methods
  once, without failures/errors/skips; no sample application or broad source suite.
- Actual hosted capacity must satisfy8GiB disk/6GiB MemAvailable. CI permissions
  are only contents:read, checkout credentials are not persisted, and no secrets,
  publication, deployment, package or release action is configured. The owner's
  Actions/all/no-mandatory-SHA-pinning policy is unchanged.

## Limits and other failed runs

Robolectric simulates the external camera/writer/result boundary. It does not
prove real Dont-keep-activities, native URI grants/process death, or active native
Android A→B semantics. #13/#76 stay open pending their original remaining native
criteria; accepted original Camera C2/C3 are not replayed or weakened.

ROOT0c7a909e is untouched by this branch. Its changed complete tooling producer
[42142584633](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42142584633)
failed the CI scope's time admission and produced zero artifacts. No reuse/native
request may use it. Changed macOS PREPARE-only
[42144077879](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42144077879)
also failed before native tests; diagnosis is not a #58 closure. Originals were
acquired once. The successful producer/four-ID-authenticated/same-HEAD cohort,
minimum permissions, history/main/API–ABI/native/consumer/dependency/legal/security/
readiness/Pages/publishing gates remain for their owning executions.

See `SOURCE-MANIFEST.json` and `IMPORTANT-RESULTS.json` for exact accepted scopes,
source pins and retained first failure. The baseline sparse-materialization refusal
was before source writes; recovery materialized only the declared baseline, then
adopted one existing/two new sources exactly once, preserving original mode/inode
and creating additions0644. A separate reviewed workflow is adopted once.

## Default-branch-safe execution bootstrap

The first REST lookup for the new workflow returns404; no dispatch was attempted.
To verify the tests without modifying protected `main`, a minimal successor adds
`push` for only `development/android-camera-lifecycle-20261106`, filtered to the
workflow, this host test and its production Android owner. The job additionally
checks the exact repository/ref/event. Unrelated/documentation-only pushes cannot
replay the tests. Its two source edits leave every command, selector, cache/XML
check and permission unchanged; changed Actionlint passes once/0/empty output.
The first lookup refusal and R2 identity remain preserved. This branch push is one
hosted reservation, not a producer/native request or release/deployment.
