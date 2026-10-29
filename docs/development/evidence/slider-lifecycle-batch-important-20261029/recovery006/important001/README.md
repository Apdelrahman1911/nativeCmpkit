# Related remaining native methods isolated; assertions retained

Both structural methods still fail/timeout; their root cause is unknown.
The next patch records finite started/changed/drag-observer facts **before** the
original assertions. It resets injector and real scene only after a failed
held pointer, preserves/rethrows the primary error and attaches cleanup errors.
Failure-only cleanup can never become a passing structural result. Every
original per-axis current-domain, stale-writer, observer and exact-cancel check
remains. The two enable/callback methods and tap/Renderer bodies stay unchanged.

Two still-never-started tap/cancel methods now have one separate finite job;
both structural methods share another finite job so a stalled one cannot hide
unrelated tap outcomes. Important synthetic/tooling142/142 passes, then only
the independently owning picker/UI receipt count fixture changes and its exact
failed guard reruns1/1. All873 selected inputs are held per run; source plans for
all three relevant profiles pass. These are **zero native/KLIB/link executions**,
not issue closure. A maximum of two combined heavy native jobs remains.

#34/UI-027 and #137/UI-034 stay open. No publishing, releases, deployments, Pages,
main/history changes or device/minimum/ABI/consumer/security/legal gate waiver.
