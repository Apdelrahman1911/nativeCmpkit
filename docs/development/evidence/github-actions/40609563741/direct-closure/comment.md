## Verified fix — direct closure after important-test review

All **six original IO-026 acceptance criteria** pass at immutable **63f377f678fa3d4f0e4def26099fb5e0a6c3247a**, [run40609563741](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40609563741): **JS22/22 + Wasm22/22**, 44 fresh target executions of22 authored methods, ten XML, zero failures/errors/skips. Five new public-Compose methods per target supplement all existing session tests.

1. Application success callback throws: cleanup happens first; no cancellation/second result.
2. Cancellation callback throws: input and both listeners still removed exactly once.
3. Actual public launcher composition disposal **and removal from a still-live composition** remove the input; captured late handlers and a retained launcher cannot deliver/reopen.
4. Two public launch attempts report one explicit overlap error and keep the first session usable; a new launch succeeds after completion.
5. Normal cancel delivers one empty result after cleanup; two fresh inputs reselect the **same actual File through real DataTransfer/FileLists**, both delivering it once.
6. Identical source/case sets pass on actual JS and Wasm runtime implementations, both delegating to the reviewed shared owner.

Root repair separates FileList conversion from application callback delivery, uses an exactly-once terminal session, and owns DOM/listeners through the production DisposableEffect. Existing public overloads and namespaces retained. Independent review checks **all741 exact own-Git input blobs**, before/after maps, artifact/every XML hash, fresh commands/test identities and actual Chrome155/SDK/runtime correspondence. No unrelated IO/full-browser suite replay.

**Scope:** real Compose composition/disposal and real DOM/FileList/events; only native OS chooser opening is intercepted. This does **not** certify native chooser UI/user activation/automatic OS cancel-event support, Safari/Firefox, minimum/physical platforms, sanitizers, ABI, dependency/legal/full-consumer or release readiness. Those wider gates remain open, not requirements silently waived for this source/lifecycle finding.

Required tests → source/results review → **close directly now** → repository evidence/index update afterward, per the owner's instruction. Original issue body/title/labels and failed historical reports preserved.

Evidence: `docs/development/evidence/github-actions/40609563741/`.
<!-- nativecmpkit:direct-acceptance:IO-026:63f377f6 -->
