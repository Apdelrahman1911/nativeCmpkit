# NativeCmpKit cookie wire acceptance — missing-only #69 / #70

**Status (2026-11-04): source/model preparation only.** No Kotlin compiler,
JDK regression, JavaFX, iOS, browser, DNS, certificate generation or TLS run is
accepted by this preparation. Do not close either issue from these controls.
The lead owns integration, routing, original-result acceptance and closure.

## Why this patch exists

The original [#69 / NATIVE-011](https://github.com/Apdelrahman1911/nativeCmpkit/issues/69)
requires actual Chromium, Firefox and WebKit session/expiry, URL/path/domain,
unsupported HttpOnly writes, delimiter validation and server HttpOnly logout.
[#70 / NATIVE-012](https://github.com/Apdelrahman1911/nativeCmpkit/issues/70)
also requires exact/subdomain/host-only, private/public and foo/foobar,
Secure HTTP/HTTPS, expiry, and returned-set parity with **real native request
headers**, including duplicate names on different paths. Original issue bodies,
classification (Medium), historical PR references and acceptance criteria remain
unchanged in `docs/audit/issue-drafts/audit-NATIVE-011.md` and
`audit-NATIVE-012.md`.

Earlier immutable macOS JavaFX login/HttpOnly method results are retained in run
[41532837164](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41532837164),
commit `3a3a93bdee07f7568e6ff78c952efd6223c41df7`. That **whole run failed** for an
unrelated policy startup. The accepted method used distinct names and maps, not
duplicate-name parity. It is not iOS, Firefox, WebKit, current-tree, security or
release proof. Do not replay that accepted method or accepted common scalar tests.

### Narrow production correction

`CookieManager.desktop.kt#getCookies` previously used
`sent.any { name/value match }` for every eligible JDK-store cookie. An
application-owned `java.net.CookieManager` subclass sending one of two
same-name/same-value/different-path cookies could therefore yield **two** library
results for **one** request occurrence.

The draft consumes a `(name, value)` multiset once per returned occurrence.
When eligible metadata candidates outnumber transmitted indistinguishable
occurrences, it returns header-only `Cookie(name, value)`, not guessed
path/domain/expiry metadata. Attributes are unavailable in that ambiguous case;
apply returned values only to the queried URL. The generic JavaFX branch, handler
ownership, constructor signatures, package namespace and common/iOS/browser
production files remain untouched. ABI/consumer validation has not run.

## Exact NEW test population

| Scope | Exact fully qualified selector | Evidence required |
| --- | --- | --- |
| Common scalar 1 | `com.mohamedrejeb.calf.ui.web.CookieHeaderMultiplicityTest.requestCookieParsingRetainsDuplicateNamesAndEqualValues` | Real common-test execution; not native proof |
| Common scalar 2 | `com.mohamedrejeb.calf.ui.web.CookieHeaderMultiplicityTest.nestedPathAndDomainScopeStillApplyToDuplicateCookieIdentities` | Includes private/public and private-extra boundaries |
| Owned JDK 1 | `com.mohamedrejeb.calf.ui.web.DesktopCookieRequestParityTest.realJdkRequestHeadersAndLibraryResultsKeepDuplicateNamesAcrossPathAndDomainScopes` | Actual JDK store/header construction, no network/JavaFX claim |
| Controlled JDK 2 | `com.mohamedrejeb.calf.ui.web.DesktopCookieRequestParityTest.anOwnedJdkHandlerSelectingOneEqualValueOccurrenceDoesNotInventTwoResults` | Real `super.get` serialization, deliberate application selection, null ambiguous metadata |
| Native Desktop 1 | `com.mohamedrejeb.calf.ui.web.DesktopCookieWireAcceptanceTest.realJavaFxScopedCookieHeadersKeepNativeMultiplicityAcrossHttpAndTrustedHttps` | Fresh isolated JavaFX worker, real HTTP and trusted HTTPS/native headers/DOM |
| Native iOS 1 | `com.mohamedrejeb.calf.ui.web.IosCookieWireAcceptanceTest.realWkScopedCookieHeadersKeepNativeMultiplicityAcrossHttpAndTrustedHttps` | Owned UIApplication/Worker/window, actual WKWebView/default jar, normal TLS trust |
| Browser 1 per target/engine | `com.mohamedrejeb.calf.ui.web.BrowserCookieWireAcceptanceTest.realScopedDuplicateSessionAndExpiryCookiesRequireServerHttpOnlyLogout` | Independently run on actual Chromium, Firefox and WebKit; JS/Wasm compatibility must be verified |

The lead must register finite selectors and normal-profile exclusions. Never add
`@Ignore`, bypass a missing fixture, infer a native run from compilation, or
silently include these environment-dependent bodies in an ordinary profile.
Browser/native fixtures are test infrastructure, not sample applications.

## Fixed wire protocol and independent oracle

`scripts/ci/fixtures/cookie-wire-v1.json` is the single server definition. Its
current SHA-256 is:

```text
7b675f4ac252be68dd2c690be90d9c97555308305bf479cdbcaf6914158d16ad
```

It contains 14 cookie definitions in 12 name/value buckets. `scope` has root,
foo, foo/child and private identities; `equal=same` has two different paths.
Other buckets cover host-only, Domain, HttpOnly, session, future, past, Secure
and manager-owned writes. Expected vectors in `CookieWireContract.kt` are
independent literal RFC scopes, not derived from production matching code.
Do not replace lists/count vectors with `.associate`, `.toMap`, a name-keyed
map, or sorted unique sets: those discard occurrences.

Each native body performs 32 actual page loads over 14 finite stages:

* root `foo`, `foo/child`, `foobar`, `private`, `public` on HTTP and HTTPS;
* subhost `foo` and `public` on HTTP and HTTPS;
* the same scope sweep after server logout;
* four extra HTTPS root `foo/child` managed session/future/past/session loads.

`https-root-foo-child` must have six closed requests; every other stage exactly
two. The server never decides whether a native cookie vector is correct.
Kotlin compares actual incoming-header counts, actual authored document-cookie
counts and public-library results against the separate expected vector. Native
Foundation domain normalization is observed, not assumed or patched beforehand.

## Browser ownership and routing obligations

The lead's cookie-only Karma invocation must provide:

```text
NATIVECMPKIT_COOKIE_WIRE_FOCUS=remaining-v1
NATIVECMPKIT_COOKIE_WIRE_HOST=r<fresh 32 lowercase hex>.nativecmpkit.test
NATIVECMPKIT_COOKIE_WIRE_SPEC=<absolute reviewed checkout>/scripts/ci/fixtures/cookie-wire-v1.json
```

The generated KGP config directory is **not** the source directory. Middleware
requires the explicit absolute spec path, bounded regular-file ingress and exact
SHA; there is no guessed relative-directory or network fallback. Without this
focus it adds nothing to the normal Karma configuration.

Before launch, the lead acquires and later restores an exact owned DNS/hosts lease
for the root host and `sub.<root>` to `127.0.0.1`. Use genuine name resolution,
not Cookie/Host header injection, origin substitution or ignored DNS errors.
The middleware uses Karma's existing loopback listener and owns only each nonce's
responses. A separate fresh control owner token permits cleanup after an
uncertain open response without destroying another owner's session.

The real test uses native credentialed `XMLHttpRequest`. Actual server
`Set-Cookie` establishes scoped/HttpOnly cookies, actual subhost CORS receives
only explicit Domain cookies, and the actual current document's pathname moves
with `history.replaceState`. The exact original URL/history state and foreign
visible cookies are restored independently of managed-cookie cleanup and fixture
closure. Whole-jar deletion and HttpOnly writes must explicitly refuse. Limited
manager deletion must retain the server's HttpOnly auth cookie until **server
logout** expires every owned path/domain identity.

Active Kotlin/KGP is **2.4.20**, not cached 2.4.21. Exact launcher syntax,
dependencies/locks/advisories and actual binaries remain lead verification work.
`useFirefoxHeadless`/`useSafari` names alone are not launcher compatibility proof.
Genuine macOS Safari is WebKit; never relabel Chromium/Playwright execution as
WebKit. Record actual engine/version/target and fresh XML for each selected body.

## Native startup contract

`cookie_native_wire_fixture.py` supplies a pure finite model and a separate
runtime `OwnedCookieNativeWireFixture`. Its constructor creates no sockets,
DNS, trust or keys. The lead must perform, in order:

1. Generate a fresh 128-bit nonce; acquire an exact root/subhost DNS lease and
   independently preserve all pre-existing/foreign hosts entries.
2. Call test-only `OwnedCookieTlsMaterial.create(token=..., openssl=<actual
   regular owning executable>)` at **runtime**. All key/CSR/config/CA/leaf files
   stay in one owner-only, uncommitted temporary directory. The fixed commands
   generate a CA and SAN-matching serverAuth leaf and perform ordinary CA/purpose/
   hostname verification. No shell or command output is captured.
3. Construct/start the owned HTTP+HTTPS fixture with its exact public leaf,
   private key and CA paths. Real DNS must resolve each host only to loopback.
   Do not start its lifetime while waiting for an expensive build; the 180-second
   native session begins at its actual process `open` claim.
4. Bind exact actual binary/source inputs and the one finite platform selector.
   For iOS, bind the actual application identifier, executable/Info.plist and
   owned simulator identifier before process-local launch environment handoff.
5. iOS needs an **owned disposable simulator**, normal CA trust via its owning
   `simctl keychain add-root-cert` operation, and this exact test-only ATS map:

   ```text
   NSAllowsLocalNetworking = true
   NSExceptionDomains = {
     <exact root>: { NSExceptionAllowsInsecureHTTPLoads: true, NSIncludesSubdomains: false },
     <exact subhost>: { NSExceptionAllowsInsecureHTTPLoads: true, NSIncludesSubdomains: false }
   }
   ```

   No arbitrary-load flag, wildcard exception, trust challenge override,
   hostname bypass or production ATS change is allowed. Never reset a shared
   simulator keychain to remove the test CA; dispose only the originally owned
   simulator and preserve foreign devices/resources.
6. Desktop requires `nativecmpkit.desktop.cookie-wire.worker=one-selected-class`,
   one finite selected method, serial forks and a **fresh worker**. Its standard
   PKIX/one-owned-CA SSLContext is installed before JavaFX/HTTP2Loader initialization.
   It restores each exact original context/factory independently, refusing to
   overwrite a foreign replacement; the original hostname verifier is unchanged.
7. Execute the actual library body, acquire each original result once, and
   compare native process/runtime/window signals and fresh XML with the fixture's
   exact process/binary/source binding. A fixture receipt/model completion alone
   is **not** native proof.
8. Independently close fixture peers/listeners/workers, restore DNS, dispose only
   owned simulator resources, and delete only the six exact owned material
   files/directory. Retain the primary failure and every cleanup failure. Archive
   only count/source/provenance receipts, **never** private keys, raw Cookie
   headers, environment, foreign jar values or temporary certificate paths.

All native cookie deletion is nonce/domain/path scoped. iOS compares the full
foreign WK-store snapshot privately; JavaFX's generic handler can compare only
the relevant request-URL jar snapshots, not enumerate all foreign domains.
The test APIs never call `removeAllCookies` for a global native jar.

### Remaining platform prerequisites, not N/A

* Shared routing/Gradle/workflows/manifests, generated status and exact source
  qualifications are lead-owned and not changed here.
* No DNS/trust/ATS lease or native/compiler run has been performed in this patch.
* The material helper currently refuses non-POSIX startup: Windows needs a
  separately verified owner-only private-directory ACL/material provider and
  genuine owning DNS setup. This is a remaining Windows blocker, not a platform
  exclusion, a successful test or an accepted security assumption.
* Browser engine/target runs and their dependency/security checks remain missing.
* Session transmission is covered inside an actual live session. Browser/process
  restart persistence, real-account authentication, minimum-version Apple links,
  all-platform security and release consumer verification are not inferred.

## Source/model controls already performed — do not replay accepted populations

The owning evidence packet retains the originals:

* FIRST672: NEW Python14 = 13 pass / one new assignment-regex failure; NEW Node8
  = 8 pass. A complete 33,514 Git-file/evidence hash inventory held before/after;
  this is not the lead's executable-source map and not native evidence.
* RECOVERY673: only failed1 plus new classifier soundness1 = 2/2. Equality
  `document.cookie == foreignVisible` is not an assignment; real cookie writes
  remain forbidden. Twenty-two effective input hashes held. Accepted first13
  Python and eight Node controls were not replayed.
* PRIVATE674: the original issue's explicit private/public criterion adds one
  definition/path without changing bucket width. Only affected Python4 + NEW1
  and affected Node2 + NEW1 execute, 8/8 total; 22 effective inputs held.
  Prior old-spec results retain their original scope and timestamps.

These controls check finite protocol/occurrence/cleanup/source properties only.
They use explicitly labelled mock requests/headers and dummy model files, not
browser/native connections or real generated keys. No Gradle, Kotlin, actual JDK
header regression, DNS, TLS or native platform test was executed. Fully verify
the corresponding issue subset, then close it together; keep release/security/
publishing gates and unverified criteria open.
