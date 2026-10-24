# Browser JS and WasmJS implementation guide

Both active web targets are browser builds. JS and Wasm share `webMain` APIs but
keep language-specific interop actuals for file buffers, promises, script
evaluation and Compose DOM hosting. There is no Node.js filesystem/permission
implementation. A shared source set does not remove browser security rules.

## Files, downloads and sharing

`KmpFile` wraps a browser `File`; `getPath` cannot supply a user filesystem path.
`readByteArray` buffers complete content. `source()` also obtains complete bytes
before exposing `RawSource`, because the chosen API is synchronous; it is not a
streaming browser fetch/readable-stream implementation. Memory use therefore
grows with the selected file. Coil adds another buffer path and the sample's
streaming explanation must not promise bounded-memory behavior on browsers.

Selection uses a hidden `<input>` with type/MIME/extension and multiple settings.
Folder mode is explicitly unsupported and returns an empty result immediately;
it does not use browser directory-input or filesystem-handle APIs. Programmatic launch must have suitable
user activation. Cancel/selection callbacks, DOM cleanup, user reselecting the
same file and multiple launchers need browser tests, not just Kotlin compilation.

Baseline save builds a Blob/object URL and clicks an anchor. The shared web saver
does not report its `onResult` on either JS or Wasm; neither can verify a physical
disk write. Object URL revocation timing can break downloads if too early or
leak if never cleaned. Open PR #551 proposes `showSaveFilePicker` and fallback
behavior; it is unmerged and its author explicitly still lists real browser UI
checks as outstanding. Do not advertise that proposed API as baseline behavior.

Sharing attempts Web Share (`navigator.share`) and/or clipboard fallbacks.
Support differs across browsers, secure contexts, embedded frames, file types
and user activation. A Promise must be awaited/handled before declaring its
operation successful; use native-feature findings for concrete missing rejection
and fallback paths. No remote recipient acknowledgement is provided.

## WebView means iframe, not an unconstrained native web engine

The shared web actual creates an iframe using `CalfWebElementView`; JS and Wasm
provide their respective host-view bridges. Content loads through URL or HTML
data, while same-origin restrictions constrain reading title/location, history,
cookies and evaluating script inside foreign pages. An iframe request cannot
arbitrarily attach the same custom HTTP headers supported by Android WebView.
Frame policy (`X-Frame-Options`, CSP `frame-ancestors`) can reject an otherwise
valid URL. Cross-origin failure is not solved by swallowing exceptions and
reporting a finished load.

`document.cookie` belongs to the accessible document/domain/path; it cannot read
HttpOnly cookies or operate on arbitrary remote stores. JS `eval` and Wasm
interop helpers need explicit error/result semantics. Do not treat page content,
cookie fields or URL/script inputs as trusted instructions, and do not claim
cookie parity across iframe/Android/WK/JavaFX backends.

## UI and unsupported services

Adaptive controls use Material actuals, rendered by Compose/Skiko rather than a
DOM-native widget library. Device pixel ratio, zoom, keyboard focus, canvas/DOM
overlay placement and accessibility require browser testing; historical #72's
zoom/pointer mismatch comes from an older engine and is not a reproduced baseline
defect. The sample enters `ComposeViewport("composeApp")`; JS waits for
`onWasmReady` for Skiko, while Wasm uses its native entrypoint path.

Camera is a no-op rather than a `getUserMedia` implementation. Permission
requests/settings/status refresh are denied/no-op rather than the browser
Permissions API. Geo is print-only rather than `navigator.geolocation`.
Adaptive navigation does not synchronize with `history.pushState`/`popstate`.
No active maps, media-player or notification-scheduling module exists. These
gaps remain even when JS/Wasm artifact resolution and compilation succeed.

## Required verification

Test JS **and** Wasm on current Chromium, Firefox and Safari under real browser
conditions. Cover secure/insecure contexts, sandboxed/third-party iframe,
blocked frame policy, user-gesture requirements, rejected clipboard/share
promises, unavailable Web Share, download cancel, multiple/folder input,
large files, typed-array/byte round-trips and resource cleanup. Validate UI zoom,
RTL, keyboard navigation and high-DPI DOM overlay alignment. Shared/common tests
need Skiko webpack bundling (`withBrowserTestBundling`); a Node/unit test or stub
of a browser API does not prove a real chooser or download worked.
