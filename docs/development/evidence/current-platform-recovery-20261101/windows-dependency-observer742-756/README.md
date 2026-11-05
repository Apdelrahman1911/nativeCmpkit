# Windows dependency observation: reviewed related batch

This archive preserves original bytes (`SHA256SUMS`). It describes source
adoption above Windows branch `7d2029823b8a`, not runtime verification of the
commit storing this archive. ROOT preview-hardening is separate.

## Actual important checks

- Stage A NEW8: **8/8 PASS once**, 185 passing synthetic subcases, no skips,
  failures or errors. Suite0.569123934s; actual child/outer exits0. All36 finite
  inputs hold, full original streams and owned cleanup independently reviewed.
  Windows/network/Gradle/native executions were denied in these tests.
- JDK source controls: FIRST18 remains **17 PASS / 1 FAIL**; only failedNEW13
  then passes once. The17 unchanged successes are reused, not a fresh18green.
- Source7 adoption writes workflow/settings plus NEW5 once, preserves existing
  workflow0644/settings0600, explicitly creates NEW0644. Approved source3 and
  REVIEWED_EXPECTATIONS_SHA256=None remain unchanged. Unqualified
  `test_javafx_ordinary_success_trace.py` is excluded from the commit.
- Actionlint exits0 for the workflow; optional shellcheck/pyflakes were not run.
- Earlier source/result reviews658/752 are retained separately; applicable
  accepted populations are reused, not replayed. The archive copier's original
  full-stat comparison refusal before any file write is retained; source7 was
  not reapplied. Recovery explicitly compares identity9, excluding access time.

## Manual-only observation

The independent `windows-ordinary-dependency-observation1` choice/job in
`javafx-library-candidate.yml` runs only on
`development/javafx-ordinary-consumer1`, with contents:read and no persistent
credentials or publishing/deployment scope. Recorded inverses reconstruct
original native job bodies/conditions exactly.

The worker requests120 fixed public HTTPS text descriptors/checksums/signatures
for17 GAV roots/20 repository candidates. It never resolves a full graph,
runs Gradle/Java/native code, follows redirects, imports keys or bootstraps
verification policies. Windows Job assignment precedes GO; real child/Job/thread
cleanup must still be verified. Only the lead requests it after fresh capacity
and immutable-source checks (max2 combined reservations, including queued).

Original run/attempt/job/artifact identities and actual public results must be
authenticated before Stage B. This source archive has **zero actual Windows,
HTTPS, Gradle/native or ordinary-consumer executions**.

## Remaining gates

Same-registry signatures/checksums are untrusted observations, not independent
publisher provenance or approved policy. Both strict root/consumer XML policies,
transitive coverage, primary payloads, native/consumer/API–ABI/compatibility,
legal/security and release-readiness requirements remain. #64 stays open. No
package, release, snapshot, deployment or Pages. All actions are owner-allowed;
mandatory SHA pinning is not imposed.
