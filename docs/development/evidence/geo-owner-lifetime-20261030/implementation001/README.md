# Android geo: missing owner-lifetime/GC prerequisite

One new actual-Android method covers32 rebind/stop/restart/close cycles. Production
LifecycleRegistry/main Looper/GMS Tasks are used; only the native provider transport
is injected.160 weak tracker/caller-context/lifecycle references must collect while
192 obsolete callback roots and a positive control stay retained. All owner counts,
per-callback exactly-once removals and stale-callback/state assertions remain.
This is not a live GMS/GPS, Activity/process recreation or power profile.

Seven new finite-selection/source/XML guards and nine affected existing guards
pass:16 distinct synthetic methods, **zero ART/native outcomes**. Pre-implementation
seven-method red (six errors/one failure) is preserved. A private recorder mislabeled
8+1 existing methods as10; additive correction preserves original and proves9 without
replaying them. Current default eleven-host and six-module device coverage remain.

Actual held dirty-source APK assembly exits0/81.02s and compiles Android production
and instrumentation source;1004 combined inputs held. **Zero device tests**. APKs,
private logs and packages are not committed/uploaded. CLI preflight requests only
one new method, not88 accepted host or portable geo outcomes. #116/PERM-020 and
#25/PERM-021 remain open pending exact immutable runtime/original-criteria review.
All main/history/native/minimum/ABI/consumer/dependency/legal/security/release
and publishing/Pages gates remain independently unchanged.
