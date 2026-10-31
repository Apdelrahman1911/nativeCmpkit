# Browser content transitions actual native001 — server startup failed

[Run41245182190](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41245182190), attempt1 at immutable5585edacd97dfb0eb928507a9e9017630dfc7c14, **FAILED before any browser methods**. Tooling succeeds; serial JS and Wasm both fail during Karma server dependency-injection startup. **ZERO browser/native target executions, ZERO XML, ZERO accepted methods; #63/NATIVE-004 stays open.**

| Target | Actual job | Gradle | Actual cases | Original artifact |
|---|---|---|---|---|
| JS |124667345726|exit1 /229.07s|0|13058923373 /107283bytes /11JSON /0XML|
| Wasm |124667345725|exit1 /273.09s|0|13059263288 /107322bytes /11JSON /0XML|

Both original logs report `Server start failed on port 9876: TypeError: Cannot read properties of null (reading '1')`, followed by `Can not resolve circular dependency! (Resolving: webServer -> middleware:nativecmpkit-iframe-fixture -> webServer)`. The secondary server-close diagnostic is retained; **successful native/HTTP cleanup is not inferred**.

## Independent evidence

`independent-actual-review.json` records16 acceptance checks and original-criteria mapping. Both actual plans exactly match the frozen two-method calf-webview request; actual source/after-source SHA, clean tree, before/after1010 library maps, one fresh selected task marker and runtime/daemon hashes agree. The independently verified1087 combined immutable Git inputs and30 reviewed unchanged source files are retained. Each original artifact ZIP and all11 entry hashes match the downloaded metadata; both receipts independently agree on zero cases/reports.

The queried binaries are JS Google Chrome155.0.8059.84 and Wasm Google Chrome156.0.8078.47; **this is configured identity, not an executed browser workload**. JS uses JDK17.0.20.1 and Wasm17.0.21; both launcher/daemon major17 agree. No Java minor-version cause, browser version cause, Node dependency-byte/security clearance, successful header delivery or native enforcement is inferred.

The owned fixture has a confirmed incompatible unannotated arrow factory: the independently observed local `di@0.0.1` annotation parser only accepts classic function syntax and reproduces the exact original TypeError. A separately reviewed minimal explicit `middleware.$inject=[]` declaration before registration succeeds through the actual local Injector. This local framework observation is **not CI browser success**. HTTP headers/script/order, Kotlin tests and production API remain unchanged by that repair; four still-unexecuted target methods need a fresh immutable request after lead integration.

## Scope and preservation

Every original criterion remains unmet at runtime: direct/remembered Data→Url→Data, state/navigator native document equivalence, and genuine CSP/XFO refusal with positive cross-origin control, actual header/request receipts, trusted load, cleared old state and later recovery/message barrier. No selected method finally/session/listener/viewport cleanup ran. No accepted earlier suite or compiler task was replayed by this review.

Original ZIPs and raw logs are retained privately. Public copies withhold precisely two runner-path-containing excerpt text bodies and retain their original SHA256/byte lengths; safe exact original startup/runtime lines and raw log hashes are in `failure-origin.json`. `archive.json` distinguishes original and sanitized bytes. Remaining20 artifact JSON records are unchanged copies. The initial archive reader incorrectly assumed the JS browser identity applied to Wasm; its owning refusal is preserved separately and is not a CI/browser failure cause. Two exact source-CLI checkout-path arguments are qualified as repository-relative with original field/file hashes retained. The initial privacy-reader refusal and its decoded-string correction are retained; no unsafe field is ignored. No publishing, Pages, main/history, consumer/ABI, dependency/legal/security/readiness gates or adjacent issues are cleared. Parent owns Git/GitHub integration and closure.
