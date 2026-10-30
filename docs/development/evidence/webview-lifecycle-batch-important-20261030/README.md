# Shared native WebView lifecycle verification candidate

**Candidate only: no Apple compile, link or native execution yet.** No production
implementation/public API changes. Six new library-owned UIKit/WebKit methods
share the existing proven genuine-UIApplication/owned-Worker transport; four
owning host methods verify its new module integration. This is not the sample
application or a mocked WebKit delegate.

| New native method area | Original findings supported, not yet closed |
| --- | --- |
| Configured native identity inside creation; retained-state remount and release | NATIVE-003 |
| Stable stateA/stateB replacement, native identity, current callbacks/navigator | NATIVE-037 |
| Real typed WebKit values/errors, Worker invocation, main delivery, detach/exactly-once | NATIVE-015 |
| Capture/setting truth table on the same native view and real HTML loads | NATIVE-009 |
| True/false initial inline setting, visible runtime rejection and new-owner remount | NATIVE-017 |
| Unicode state/navigator HTML, relative base URL, visible unsupported encoding/history | NATIVE-016 |
| Actual native title/loading/KVO/terminal state during those real loads | NATIVE-005, bounded subset only |

`ios-webview-lifecycle` selects **one** existing Arm64 macOS/iPhone slot and exactly
**ten** fresh methods of `:calf-webview:iosSimulatorArm64ApplicationTest`. All eleven
full-library slots remain. Accepted UIImage/picker/Android-history/browser/desktop
methods are not replayed. No added sanitizer settings or public framework changes.

The [shared important tooling receipt](local-important001/shared-important001.json)
passes **173/173 Python methods, 0 failures/errors/skips, 8.542 s**, with all
**972** sample/library/tool inputs held. These are synthetic/lexical controller
methods, not native/library executions or 173 fixed issues. Counts overlap prior
tooling. One owning guard was first red; the expanded fixture then had two
failures, retained in [first-important.json](local-important001/first-important.json).
Correcting the synthetic receipt owner and its false whole-suite expectation
does not relax any native protocol/XML/binary/install/Worker/cleanup gate.

Actual physical swipes/video playback, provisional DNS/TLS errors, authenticated
headers/redirects, minimum OS/provider, other engines/platforms and consumer/ABI
checks remain separate original acceptance requirements. The `.invalid` HTML
base is never fetched. Do not batch-close unverified members or replace those
requirements with configuration inspection. Review actual immutable native
results before immediately closing any fully verified subset. Single agent,
maximum two combined heavy hosted requests, 8 GiB local reserve; publishing,
Pages, main/history and independent release/security gates remain unchanged.
