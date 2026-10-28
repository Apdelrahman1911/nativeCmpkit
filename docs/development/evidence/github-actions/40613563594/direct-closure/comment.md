## Verified fix — direct closure after important public-component tests

All **three original NATIVE-006 acceptance criteria** pass at immutable **b7ba5c802ee8c8a58e813d19b5a242770aac9675**, [run40613563594](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40613563594): **JS33/33 + Wasm33/33**,66 fresh executions/14 XML, zero failures/errors/skips. Three new public Compose/DOM methods supplement all30 existing methods on each target.

1. Mount/remove/remount the **actual public WebView inside real ComposeViewport/canvas/HTML interop**. Full window disposal and removal from a still-live composition deliver exactly one onDispose per created view; repeated fixture close does not repeat it.
2. Retained state clears both old iframe and owner. Native DOM removal is observed through isConnected; remount uses a distinct node and owner, not a stale remembered instance.
3. Both old native event dispatches and the **original captured load/error callback objects** are delivered after removal and replacement. The callback delivery counter proves they actually ran; replacement owner/node/loading/title/final URL/errors remain untouched. Original listener identities are removed natively.

Owning source binds teardown to DisposableEffect, removes both listener objects, clears only matching state and guards late callbacks with disposed/current-frame identity. Public APIs and packages remain. Test code uses the real Compose dependency's internal window handle **only to release its own viewport**; no copied renderer or no-op/fake UI applier. Controlled trusted fixture HTML enables genuine DOM readiness, not a security-policy bypass in production.

Source/results review checks **all742 exact own-Git inputs**, before/after maps, every XML/artifact hash, all33 authored identities on both targets, command and Chrome155/SDK/runtime correspondence. Required tests → review → **direct closure now** → repository archive/index afterward. No unrelated IO/other modules/native-host replay.

Scope: actual Chrome JS/Wasm public-component lifecycle and native DOM/listeners. This does **not** certify Firefox/Safari, GC/native-memory profiling, other WebView/network/sandbox/cookie issues, physical/minimum/native sanitizers, ABI, dependency/legal/full consumers or release readiness. Wider gates stay open. No packages/releases/deployments published.

Evidence: `docs/development/evidence/github-actions/40613563594/`. Original issue body/title/labels and previous failed reports preserved.

<!-- nativecmpkit:direct-acceptance:NATIVE-006:b7ba5c80 -->
