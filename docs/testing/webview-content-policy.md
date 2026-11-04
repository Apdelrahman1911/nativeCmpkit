# WebView save/restore and content-policy acceptance — #66 / #73

This isolated patch is **source preparation**, not a verified device fix or issue
closure. Four NEW platform classes author 14 methods, proposed as 17 executions
(the same three browser methods execute separately in JS and Wasm). No Gradle,
compiler, Android provider, JavaFX, browser or WKWebView execution has occurred in
this patch. Existing accepted native bodies/helpers and the accepted iOS request
fixture remain unchanged and unselected.

## Finite missing-criteria proposal

[`webview-content-policy-focuses.json`](webview-content-policy-focuses.json) binds
each proposal to one module, host, task, exact class and method list. These names
are **not yet registered** in the shared runner/workflow by this subagent. The
lead alone wires, freezes, pushes, dispatches, reviews and accepts actual results.

| Proposed profile / focus | Actual target task | Exact NEW cases |
| --- | --- | ---: |
| `webview-content-policy-linux` | `:calf-webview:desktopTest` — Linux x64 | 3 |
| `webview-content-policy-android` | `:calf-webview:connectedAndroidDeviceTest` — API35 | 4 |
| `webview-content-policy-js` | `:calf-webview:jsBrowserTest` | 3 |
| `webview-content-policy-wasm` | `:calf-webview:wasmJsBrowserTest` | 3 |
| `ios-webview-content-policy` | `:calf-webview:iosSimulatorArm64ApplicationTest` — iPhone | 4 |

The class prefix is `com.mohamedrejeb.calf.ui.web.`. Classes are
`DesktopWebViewContentPolicyAcceptanceTest`,
`AndroidWebViewContentPolicyAcceptanceTest`,
`BrowserWebViewContentPolicyAcceptanceTest` and
`IosWebViewContentPolicyAcceptanceTest`.

| Exact method | Targets | Real acceptance witness |
| --- | --- | --- |
| `savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory` | All five | Save → release real native owner → restore into a different state/real view. URL, HTML, navigator-loaded URL, final redirect URL and null URL rows; actual DOM/title, URL, native/public history and HTTP generations. Android excludes the already accepted plain-URL restore row and retains its native-history policy. |
| `documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved` | All five | Non-Android URL saver causes a second actual GET/document generation, not HTML/POST replay. A deliberately ordinary, non-saveable navigator-only state loads a one-time URL and submits a genuine HTML form POST. Its fresh blank remount and later real safe page leave GET/POST counts unchanged. |
| `initialHeadersRedirectsAndSubresourcesMatchStateAndNavigatorPolicy` | Android / iOS | Main-document authentication requires exact **dummy fixture-only** initial headers. Same-origin and different-port-origin HTTP302 forwarding is observed on the wire/DOM, not guessed. Later links and actual JS/CSS/SVG subresources carry no initial authentication; state/navigator policies must match. |
| `relativeResourcesPreserveSupportedUnicodeEncoding` | Android / iOS | Inline HTML resolves real relative JavaScript, stylesheet and SVG against a base URL; Unicode body/resource text, computed color and decoded 7×9 image agree under `utf-8` and `utf8` via both public entry points. |
| `unsupportedHeadersAndBaseUrlRefuseBeforeNetworkForBothEntryPoints` | Desktop / JS / Wasm | Each unsupported capability produces visible `WebViewError(-2)`, preserves the real current native DOM/owner and causes zero fixture requests. Supported plain Unicode HTML still loads through state/navigator for both encoding aliases. No header proxy or base-URL support is invented. |

## Honest restoration / replay policy

Non-Android `WebStateSaver` persists only a supported HTTP(S) GET URL. HTML, request
headers, POST bodies, form state, native history and scroll position are not saved.
Final redirect URLs are saved after completion; remount does not repeat the old
redirect entry. A discarded HTML/non-HTTP/null URL remount must not paint stale
metadata over its real blank native view and may explicitly load new content.
Sensitive or one-time requests should use an ordinary/non-saveable state and an
explicit navigator load: this test does not pretend to recognize token strings
or make a replay-safe application decision automatically.

Android remains distinct: its real `Bundle`/Parcelable native-history round trip
is retained, and display/form data are not promised by that Bundle. The NEW rows
use supported explicit Reload for restored HTTP history, or explicitly reprovide
HTML. They record the actual bounded initial-load/restore/Reload GET generation
(2–3), a source-derived allowance **not an observed provider fact**. Before asking
for the explicit new load, public nonblank metadata is compared to the actual
provider DOM and public history to native history. No OS process-death execution
is claimed by the Parcelable round trip.

The only production change removes two saved-title/final-URL assignments from
Android `WebStateSaver.restore`. Saving the old map keys and native Bundle,
loaders/actions, signatures and API are unchanged. A NEW source control first
failed on those assignments and passed only after their removal: this confirms a
**stale-metadata source hazard**, not a failure observed on a device. Actual native
callbacks, not saved metadata, repopulate fresh metadata.

## Owned test transports and source/identity boundary

- New byte-identical Android/Desktop raw HTTP helpers own two IPv4 loopback
  listeners, their actual sockets and finite workers. They report fixed stage
  names/numeric GET, POST, page, redirect, header, asset and closed/pending counts
  only; no request/response bodies, URLs, nonce or dummy header values are logged.
  Cleanup attempts every owned stage independently and retains failures.
- The new Karma middleware owns **only its nonce's route/response leases**. It
  never stops Karma's listener or global socket pool. Claims/spent nonces cannot
  reopen. Trusted messages must originate from the exact owned control iframe and
  same actual local Karma origin. Browser tests opt into Trusted only for owned
  test documents; the production Isolated/security policy is unchanged.
- The separate iOS Python fixture owns two IPv4 loopback origins. The accepted
  `ios_webview_request_fixture.py`, real UIApplication host and normal source-set
  inheritance remain unchanged. The lead must enable only the existing
  test-app local-network ATS lease (`NSAllowsLocalNetworking`), never arbitrary
  loads, a trust bypass, system network mutation or public application policy.

All HTTP fixtures use finite method/stage/asset registries, connection512 and
stage12 budgets, header8192/body512 limits and bounded own work/cleanup. Initial
authentication gates only the main page, **not** its subresources. Main plus three
real asset GETs are counted as four GETs, not one. A socket-control pass alone is
not a native DOM/document pass.

### iOS lead-owned wiring contract

After independently verifying the actual installed test application, the new
`OwnedContentPolicyFixture` supports this private process-local handoff:

```python
fixture = OwnedContentPolicyFixture()  # exactly restore/replay/headers/resources
fixture.bind_application(root, bundle_id=bundle_id,
                         signed_hash=signed_hash, plist_hash=plist_hash)
nonce_hash = fixture.nonce_sha256
launch_environment = fixture.launch_environment(inherited_environment)
```

Bind once **before any ingress**, using actual installed executable/plist hashes.
The binding freezes the current new Kotlin test/helper and Python fixture hashes.
The one launch-environment call sets only its three `SIMCTL_CHILD_` selectors in
a returned copy; conflicting plain/child selectors refuse without mutating the
inherited environment. Each Kotlin method claims its actual `getpid()`; all four
must belong to the same original application process and complete after their
real UI/native teardown. Generic socket-only controls can exercise an unbound
lease but can never validate as an installed/native attempt.

Always close this fixture independently, including after native failure. Then
retain `fixture.receipt()` and call `validate_receipt` with actual caller witnesses:
`bundle_id`, `signed_hash`, `plist_hash`, `native_pid=protocol.observed_launch_pid`,
`fixture_hash`, `native_hash`, `helper_hash`, and the original `nonce_hash`.
Validation requires the exact four-method wire matrix, actual process digest,
strict identity/source hashes, zero refusals/errors/pending work and observed
owned listener/socket/acceptor/worker cleanup. It emits no raw PID, nonce, URLs,
environment or header/body data. A source drift or wrong PID is refusal, not
permission to retry a spent method.

**This is transport ownership only.** The lead's existing current-source/binary/
runtime/Worker/KGP native-case/XML agreement and installed-app disposal checks
remain separately mandatory. Do not manufacture an XML/result from fixture stats.
The shared runner, application transport and workflow are lead-owned and are not
modified by this isolated patch.

## Important affected compilation / result plan

No heavy slot was granted to this subagent. After a fresh serial-local slot and
at least 8 GiB free, the lead should qualify the new target compilers separately:

- Desktop test compilation (`:calf-webview:compileTestKotlinDesktop`).
- Android production saver + instrumentation APK
  (`:calf-webview:assembleAndroidDeviceTest`).
- iOS test KLIB (`:calf-webview:compileTestKotlinIosSimulatorArm64`); it is not an
  Apple link, UIApplication launch or native result.
- JS and Wasm test compilers (`:calf-webview:compileTestKotlinJs` and
  `:calf-webview:compileTestKotlinWasmJs`); neither is a real browser execution.

The important existing affected saver seam is
`AndroidWebViewLifetimeDeviceTest.retainedStateReleasesRepeatedRealActivitiesAndViewsAndRestoresSerializedNativeState`.
Its body is byte-identical and still requires a native Bundle, real Parcelable
round trip, real navigator Reload and genuine title/URL completion. Historical
accepted evidence is not a fresh pass against the changed restore boundary. The
lead decides the necessary affected selection; do not blindly replay all accepted
Android lifetime/history or other target methods. Common URL-saver tests do not
exercise this Android saver.

After registration/freeze, only the exact missing NEW classes/methods should enter
the proposed five jobs, at most two hosted-heavy reservations **including** queued
or reserved work. Reuse unchanged accepted results; retry only genuinely failed
or source-affected cases. Compiler/native/source evidence must be independently
reviewed before accepting any original #66/#73 criteria or closing a verified
subset. No unrelated broad release gate is invented as an individual criterion.
Existing API/ABI, dependency, legal, security, consumer, publishing/Pages,
main/history and release-readiness gates remain unchanged.
