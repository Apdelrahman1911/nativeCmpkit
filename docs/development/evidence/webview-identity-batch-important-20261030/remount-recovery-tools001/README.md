# Two failed/unexecuted mobile WebView cases only

The related `webview-identity-remount-recovery` candidate selects **one Android
creation/remount method and one iOS creation/remount method**, not accepted Desktop,
value/browser/native methods. Original11 full slots and existing profiles stay.

- Android readiness retains native/state title/Finished predicates and15s bound,
  adds actual current-native `document.title` readiness and final exact JS result.
  Saved titles are not proof of a live document. At most one query in flight,
  each callback exactly once and correlated to its native owner; no clearing saved
  state, synthetic load or weaker expected title. Actual values method/evaluator
  stay unchanged; shared readiness helper is deliberately strengthened.
- iOS retained wrapper's child uses `assertIs<UIView>` before native identity
  comparison, fixing the observed Any?/NSObject? compiler mismatch without ignoring
  unexpected collection types. State-null/superview-null/retained-parent/disposal
  checks stay. Production final child detach still needs native execution.

[Initial red](important001/first-red.json):3 methods/2 failures/1 error.
[Important command](important001/important.json) **remains FAILED55:54 pass/one
stale unchanged-helper expectation**; [corrected owning guard](important001/owning-recovery.json)
alone passes1/1. The54 successes are not replayed.904 library/981 combined inputs
held; zero local Kotlin/Gradle/library/native executions. Source-only planning
and lint are not mobile runtime acceptance. #62/#89 remain open until original
criteria pass; #141 profiling and publishing/Pages/main/history/security gates stay.
