# Unfinished rendering-only fixture recovery

Actual d299 run40918825821 preserves source0/hierarchy11/isolated-layer0 at
3x/pixel366/channel0 after all2x original/template assertions completed.
This contrast does **not** by itself establish a converter defect. The test
previously requested a3x capture without explicitly binding the attached view
backing scale. The candidate uses UIKit's actual typed post-attachment setter
and asserts both view.contentScaleFactor and layer.contentsScale match each
requested2x/3x density. All original hierarchy/template channels, narrow3
tolerance, attachment checks and both densities remain; no nearest filter,
isolated-layer fallback, assertion suppression or production repair.

Initial two new guards fail with two errors; shared53 tools pass. That shared
run did not capture a pre-run source snapshot and is not called source-held.
Only the two changed guards rerun2/2 with all877 actual inputs held; they
overlap the53 methods. The exact rendering-only CLI plan passes; one host, one
unfinished native method, no accepted system/sibling/sheet/popover/component
replay. Full11 slots and300s application deadlines remain.

**ZERO local KLIB/link/application tests. Native candidate unverified.**
#143 is already verified/closed; #139 stays open until actual candidate results
and original criteria review. No release/security/device/ABI/consumer/profiling
clearance or publishing/Pages/main/history change.
