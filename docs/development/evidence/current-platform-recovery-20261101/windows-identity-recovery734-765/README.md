# Windows observer identity recovery — 2026-11-05

## Scope and confirmed failure

The isolated ordinary-dependency observation run [42017529396, attempt 1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42017529396)
failed in job `127211680966` at source `6d21150e9b0031377f6ed2e6cfe27b8e8126950b`:
`controller:663 → snapshot_sources:228 → read_regular:127`,
`ObservationRefusal: Opened source identity drift`.
The original output did **not** retain the pathname or differing stat field.
There was no worker, GO, descriptor download, native execution or artifact.
This is not evidence that a specific Windows field caused the hosted failure.
The original run is preserved under `original-failed-run42017529396/`; do not
retry its unchanged HEAD.

## Related source repair

`scripts/ci/windows_ordinary_dependency_observer742.py` now uses independent,
stable Python named-stat and descriptor-stat views on Windows. Required native
`FileBasicInfo0`, `FileStandardInfo1` and `FileIdInfo18` bridge them with full
64-bit volume/128-bit file identity. Regular-file, reparse, deletion, single-link,
size, parent and full before/after identity guards remain. There is no failed-query
fallback and borrowed CRT handles are never closed by the native metadata reader.
The existing POSIX bodies and original native/protocol assertions remain intact.

For an exclusively owned writer, only nondecreasing last-write/change times may
vary across its close interval. All other fields remain exact, followed by full
closed path/descriptor/native custody and exact content readback. A timestamp
transition does **not** identify an actor or establish intrinsic causation.

The new `scripts/ci/test_windows_observer_identity_recovery734.py` covers the
representation bridge, native-query/resource failures, identity changes, bounded
writer close behavior and exact readback with simulated native views and owned
POSIX temporary files. It does not substitute for actual Windows execution.

## Important tests and review

- **NEW9: 9/9 PASS**, 67 reported passing subcases, executed once.
- Suite `0.35238150297664106s`; executor envelope `0.6158763901330531s`.
- Child/outer exit0, finite31 before/after inputs held, complete output and owned
  process-group/empty-runtime cleanup accepted.
- Existing Stage A8/185 synthetic subcases are explicitly reused, not replayed.
- Independent742 accepted source/executor and original complete results.
- Lead765 adopted exactly the existing observer and one new test; both0644,
  existing inode/mode preserved, 22 other protected identities unchanged.
- Passive734 accepted actual exact2 and both inverse/forward fragments. This is
  source/result acceptance, not fresh Windows/native or consumer verification.

`first-NEW9/`, `independent742/`, `lead-adoption765/` and `passive-actual734/`
contain the exact original evidence. `ARCHIVE.json` records file hashes/modes.
All archived contents were scanned for common credential/private-key patterns;
no matches were found. An initial archive preflight refused a whole-stat equality
check before any writes; no differing field was retained. The corrected passive
archive check uses the explicit nine stable metadata fields recorded in its
manifest. No source or accepted test was reapplied/replayed.

## Next verification and limits

Freeze/push **this development branch only**, then run the exact existing manual
`windows-ordinary-dependency-observation1` choice. Recheck actual source SHA,
run/attempt/job, selected input and all combined hosted reservations immediately
before dispatch (maximum two including queued/reserved). The plan has 120 bounded
public-text observational requests. Missing/refused descriptors must remain
refusals, not dependency trust. Never stage the separate, unqualified
`scripts/ci/test_javafx_ordinary_success_trace.py`.

#64 remains open for ordinary corresponding-source/native consumer requirements;
#40 remains open for dependency provenance and the strict two-root trust policy.
No actual Windows/HTTPS, Gradle, native, consumer, legal, API–ABI, security or
release criterion passes here. ROOT's failed producer41938604356 and central
Camera/WebView cohort remain separate and nonreusable. No main/history change,
package, release, deployment or Pages publication is authorized by this evidence.
