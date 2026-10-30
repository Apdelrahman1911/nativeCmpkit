# Reviewed real-OS restoration fixtures — 2026-10-30

Seven original test-only drafts were retained unchanged outside Git and reviewed
before restoration. `draft-origin.json`/`reviewed-source.json` retain their hashes;
production library source is unchanged. See [owning scenario documentation](../../../android-camera-restoration.md).

Three finite-selection/ownership/XML synthetic guards first failed because the
profile/constants did not yet exist, then passed after explicit implementation.
They are included in the later **128/128** important synthetic methods; counts
overlap, not131 distinct tests. Actionlint1.7.12 also passed, with inputs held.

`compile001/review.json` retains the actual reporter compilation failure:
exit1/31.02s, five nullable `ActivityManager.RecentTaskInfo?` accesses,
**receiver not started, zero native executions**. `compiled-correction.json`
records explicit non-null refusal and single-snapshot task matching.
`compile002/review.json` then verifies reporterAPK0/34.01s and
independent receiverAPK0/11.0s with held987/1064 inputs. Compilation is not an
Android execution or #13 closure. Private full logs/binaries are not archived;
public diagnostics preserve exact source errors and raw-log hashes.

Actual installed APK byte identity, task/PID/lifecycle/grant/descriptor/result,
file ownership and every exact cleanup/state-restoration assertion still require
the four-case immutable API35 run. No physical hardware/minimum-API/API-ABI,
packaged/security/release result, publication or deployment is implied.
