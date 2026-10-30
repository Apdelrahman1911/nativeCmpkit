# Shared failed-case WebView recovery (2026-10-30)

The original shared run remains failed (six accepted cross-platform executions,
one FX fixture failure, Android zero-start), and iOS recovery remains failed
(six accepted native methods/one removal-predicate timeout). No passing unrelated
methods are replayed: the new finite `webview-identity-recovery` asks for only
**four executions**: Desktop failed1, iOS failed1, Android unexecuted2.

## Owning changes

- Actual Android controller now accepts the reviewed focus and offers backward-
  compatible read-only `plan`. Workflow preflight exercises **that actual parser**,
  not the different library CLI. Existing emulator identity/reserve/cleanup and
  real library execution gates remain.
- Only the failed public Desktop method waits for its **actual onCreated** before
  calling FX. Existing callback/error/timeout/settings/remount assertions stay;
  no artificial toolkit startup, test-order dependence or successful FX replay.
- Final iOS release explicitly detaches the WKWebView child before clearing its
  owner. Actual Compose1.12 source removes the grouping wrapper, not the child;
  a retained parent must not postpone cleanup until deallocation. The failed
  state-null/child-superview-null predicate stays and a real retained-wrapper
  assertion strengthens it. The original XML did **not** establish which conjunct
  failed; native recovery must verify the proposed repair.

Initial4 guards fail2/error2; owning7 stays failed6pass/one prose-versus-call guard
error, corrected guard alone1/1pass. Shared **164/164 important synthetic methods**
pass with **981 held inputs**. The six unchanged owning successes are not replayed
there. Accepted prior browser/Android source and two FX method bodies/helpers,
plus six iOS successful bodies/helpers, remain unchanged. These are overlapping
tooling counts, **zero new local Kotlin/library/native executions**, not runtime
or automatic #62/#72/#89/release certification.

Memory recovery41002405707 remains independent on de6c1618; no redispatch. All
original full profiles/all11 slots, single-agent/max2 heavy requests/8GiB reserve,
publishing/Pages/main/history and independent release/security gates remain.
