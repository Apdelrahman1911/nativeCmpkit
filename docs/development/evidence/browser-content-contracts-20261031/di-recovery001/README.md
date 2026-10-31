# Karma middleware startup — owning two-file repair

[Actual run41245182190](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41245182190)
at5585edac remains FAILED: JS Gradle1/229.07s and Wasm1/273.09s,
**zero browser methods/XML**. Both stop in Karma before the content/CSP/XFO tests.

## Confirmed source cause and fix

`calf-webview/karma.config.d/nativecmpkit-iframe-fixture.js:7` uses a zero-argument
arrow factory. Legacy `di@0.0.1` automatic annotation only matches classic
`function(...)`; `annotation.js:28-29` dereferences a null match. Karma resolves
the middleware while creating webServer; failed provider construction leaves
its resolving stack populated, explaining the later cleanup cycle diagnostic.

The exact original factory independently reproduces the same TypeError through
the observed installed Injector. Explicit `middleware.$inject = []` at line50
uses its actual supported API; the same Injector returns the owned three-argument
middleware with zero injected services. Observed local package bytes are not
CI package provenance or dependency/security certification.

Two owning files change: factory metadata before registration and one synthetic
guard in `scripts/ci/test_webview_content_focus.py`. Original guard red retained;
repaired1/1 plus five distinct unsafe metadata refusals pass. Their exact selected
postimages are integrated and prior results reused, not repeated. All HTTP paths,
headers, tokens, native methods, filters, assertions and production code remain.

## Required actual recovery

Only the four unexecuted JS/Wasm content-transition cases need a fresh immutable
request. Cross-origin unreadability alone is not CSP/XFO acceptance: require trusted
positive control, real header/request receipt, new load, old-document/metadata
clearance, absence of denied message after receipt barrier and inline recovery.
#63 stays open until all original criteria/source/results/cleanup are reviewed.

Structured observations retain source/framework hashes, counts and refusals;
private path prefixes are replaced only in public copies. Raw logs, source
archives, Node packages and ZIPs stay private. No native/HTTP/compiler test replay,
release/security or issue closure is inferred.
