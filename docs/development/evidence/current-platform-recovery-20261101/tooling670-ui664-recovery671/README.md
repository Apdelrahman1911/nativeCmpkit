# Shared CI blocker and UI outcome isolation

## Original CI results — immutable `044d9aa8`

| Request | Run | Result |
| --- | --- | --- |
| Camera ownership/memory/callback five | [41810510161](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41810510161) | Failed in offline tooling; no platform execution |
| Android WebView content-policy five | [41810768827](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41810768827) | Failed in offline tooling; no platform execution |

Each reports **3,194 source tests, 70 failures and 56 errors**. The 126 failure
records cover **82 named methods plus one class-setup refusal**; four declared
methods behind that setup never ran. Six current-contract667 controls passed.
Downstream zero-step jobs are skipped placeholders, not platform tests. There are
no Gradle/compiler/APK/Apple/native/XML or artifact outcomes to accept.

The Camera convention hash holds. `Reporter.freeze` rejects the newer module
build against a historical hash; that alone does not prove a namespace change.
Related stale recents/handoff, WebView and image fixtures need one shared recovery.
Do not dispatch unchanged native requests against this known failed tooling.

`camera41810510161/` and `android41810768827/` retain the once-acquired public
originals, failure indexes and completed independent reviews. Seven Camera
zero-step log endpoints returned 404 once; six completed before the lead's stop
instruction. These unnecessary queries are retained transparently, not retried.
Archived acquisition scripts/data are historical evidence, **not instructions to
execute or reacquire anything**.

## Implemented UI preparation — not native verification

UI664 is integrated above that revision: **nine existing paths, 63 exact
inverse/forward fragments and four additions**. Independent and lead review
verified all 13 postimages and the 43-source dependency union.

- Separate genuine-application tasks select the unchanged related nine and the
  customization one, with independent XML/result/receipt directories.
- Legacy ten and pre-26 four selectors remain available and unchanged.
- Screenshot bitmaps close in `finally`; bounded first-row observations do not
  change original assertions, waits or interaction delivery.
- FIRST22: **20 passed, one NEW failure and one NEW error**. Only those two were
  corrected and rerun: **2/2 passed**. The accepted 20 are reused, not replayed;
  there is no fresh 22-green execution.
- Compiler, Apple linking and native outcomes: **zero in this preparation**.
  The earlier UI650 incomplete/failed native result remains failed; neither the
  hang cause nor a native hang fix is established.

`ui664/` contains the sealed source packet, original results and exact independent
and lead integration receipts. `ARCHIVE-HASHES.json` records copied evidence.

No new issue closure or release readiness is inferred. Retained state remains
103 closed / 69 open / 172 total. Publishing, deployment, Pages and main/history
changes remain prohibited until the separately required readiness/security gates
pass.
