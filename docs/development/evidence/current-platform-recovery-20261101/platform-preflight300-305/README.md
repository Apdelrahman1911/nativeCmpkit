# Related Windows candidate and shared CI policy recovery

**2026-11-02, solo. Original failures retained; no native acceptance or closure.**

## Exact hosted originals

Both attempts are at `f9ad18de06c721ffe82d4de9c11899e9968b0391`.

- [Windows41418996640](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41418996640):
  SDK23/status index/source plan/runtime/exact dependency cache and **cache fence
  pass**. The corrected filename and uploaded safe cache receipt are verified on
  Windows. JDK Temurin17.0.20.1+1 javac **0/2.469s**, then exact candidate class
  inventory rejects before packaging/Gradle/public Stop/native/XML. Actual1,204
  library **before** hashes match Git/current; the original after-map is absent.
  Original class bytes/count/hashes were not uploaded before refusal and remain
  unobserved. [Acquisition300](ACQUISITION300.json) caches originals exactly once.
- [Alert41419207500](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41419207500):
  history/audit/current indexes pass. Tooling executes35+80+94 = **209 methods**,
  208 pass/one failed in the development directory, before later source directories,
  profile/Apple/Gradle/native. Not2376 executed. [Acquisition301](ACQUISITION301.json)
  retains the original once-acquired logs; zero artifacts/native executions.

## Confirmed owning causes and fixes

1. `build_runtime_candidate.py::build`, originally line220, used
   `str(p.relative_to(classes))` for compiled JAR member keys. Windows produces
   `com\sun\webkit\network\...`; expected pinned JAR members use `/`.
   **Only `.as_posix()` plus its comment changes.** Class SHA pins, Java source,
   compiler command, source/legal/native inventory, exact extra/missing/changed
   refusal, one-provider replacement and publishing restrictions are unchanged.
   Normalization is a necessary owning correction, not proof of the unuploaded
   original emitted class contents. The next actual Windows pin gate must pass.
2. `test_preview_boundary_batch.py` had a stale exact two-workflow inventory:
   it rejected the already-reviewed JavaFX dependency/candidate verification files.
   The replacement guard names **exactly four** workflows, requires read-only
   permissions and forbids publishing. The two JavaFX routes may auto-run only
   on `development/preview-hardening` and their exact existing3/2 owning paths;
   other workflows remain manual. New branches, broad paths/events, unknown files,
   write permissions and release commands all refuse. No workflow trigger or
   token permission changes are made by this recovery. The test method is renamed
   from `test_all_active_workflows_remain_manual_read_only_with_no_version_stamping_or_release_template`
   to `test_active_workflows_use_only_reviewed_read_only_triggers_without_publication`.

## Important verification and exact limits

- [302 preimage red](RECEIPT302.json): one NEW controlled Windows-path regression
  fails on literal backslash member keys over actual synthetic files. These are
  not JVM classes or an actual Windows filesystem execution.
- [303 green](RECEIPT303.json): only failed family/NEW controls, **3/3 class-path**
  (unittest0.030s) + **3/3 policy** (unittest0.012s). The exact reviewed local
  inventory/guard AST expressions execute; extra/missing/changed classes still
  reject. Seven adversarial workflow mutations reject expanded branches, broad
  paths, release events, package/OIDC write permissions, release commands and
  unknown files. All1,204 library source hashes hold. **Zero local compiler/native.**
  Accepted275 packaging, previous27 candidate controls and dependency-native4
  populations are reused, not replayed or called fresh.
- [304](REVIEW304.json) preserves one reviewer inventory-check mistake: that
  predicate was tautological and did not qualify artifact absence. [305](REVIEW305.json)
  corrects only that check on the original hash-bound19-member ZIP and excludes
  JAR/class/APK/AAR/nested-ZIP payloads. Other17 checks are reused: **18 accepted
  passive checks across17+1**, not a new18 invocation or native evidence.

The alert's four original methods,10s/genuine public accessibility activation,
181 bounded public-container observation and cleanup are unchanged. Its source
still hashes `c35f183d0a3107ae3cc00871cd6926d250f564187898f7323dbe78a47f19b66c`.
The first actual native execution of that observation is still missing.

Next freeze/push development only. The owning builder change auto-reserves **one
Windows Stop1 job**; do not duplicate manual dispatch. Only missing Alert4 may
coexist, within max2 combined hosted-heavy reservations INCLUDING queued jobs.
No public API, default dependencies, binary/source-package distribution, main or
original history changes. #64/#28/#3 remain open; last verified97closed/75open/
172total and22implemented/42partial/95verified/five unresolved. Every consumer/
API-ABI/corresponding-source/legal/security/readiness/publication gate remains.
