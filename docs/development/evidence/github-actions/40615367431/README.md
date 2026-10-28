# Share callback direct acceptance — 2026-10-28

[Run40615367431](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40615367431)
at immutable `3b01b400864d5ceee2f542b7577b68c976df2d6a` passes **JS18/18 + Wasm18/18**,
36 fresh executions/four XML/zero failures, errors or skips. Both real share and
clipboard Promise helpers now test fulfilled and rejected application-callback
exceptions; Success is recorded exactly once and subsequent requests remain usable.

[Important source/results review](important-result-review.json) accepts all3 original
NATIVE-032 criteria,742 own-Git inputs, every XML/artifact digest, fresh18 identities
per target and actual Chrome/runtime correspondence. [Android reuse](android-reuse-review.json)
reviews16/16 actual host executions at6eb7c66e/run40414284598 against16 unchanged
relevant own-Git inputs; **zero new Android executions**. Actual ActivityNotFoundException
and callback separation under Robolectric, not device chooser/recipient permission.

[#87 was closed directly](direct-closure/closure-readback.json) after the review,
before this archive/index. Original body/title/labels retained. The initial closed
collection omitted #87 despite exact closed-state readback; cause unknown.
[Later read-only reconciliation](direct-closure/total-closed-review.json) confirms
**29 closed issues**, without repeated mutations. Previous failed archives remain.

No unrelated successful libraries or native-host suites were replayed. Controlled
navigator functions use real browser Promise jobs, not real OS permission/user
activation or share dialogs. Other-engine/native/device/security/legal/dependency/
API-ABI/full-consumer/release gates remain. No packages/releases/deployments published.
Public report ZIPs/JSON only; downloaded private console logs stay outside Git.

The initial local `actionlint` PATH lookup failed; the existing previously acquired
`/tmp/nativecmpkit-actionlint-1.7.12/actionlint` then executed successfully with the
same workflow.25 focused matrix-tool methods and resolution checks passed; these
are tooling outcomes, not additional library methods. Full hosted tooling also passed.
