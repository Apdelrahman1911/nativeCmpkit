# Related Camera/WebView recovery and UI timeout preservation — 2026-11-04

Source endpoint: `30db3ed785e13013b5de3939fdd6eb70b6d4b25a`, development only.
Camera production ownership commit `4697c3ec65427a12e53645ecffac5e2b52821dd5`
is retained as its parent. No original history, upstream repository, main,
package, release, deployment or Pages mutation is included.

## Actual outcomes, without inflated accounting

| Verification | Actual result | Scope and exclusions |
|---|---|---|
| FIRST27 source controls | **25 pass / two NEW failures**, 14.804067s | 1,446 source-control inputs held; no compiler/native/browser execution |
| Failed NEW2 recovery | **2/2 pass**, 0.394286s | Only the two failed fixtures executed; accepted25 reused, **not a fresh27-green run** |
| Original Camera compiler658 | **FAILED**, Gradle1/44.01s | Seven test diagnostics retained; original production compile reached, zero Apple/native |
| Camera test compiler660 | **PASS**, Gradle0/41.01s | Fresh three-source/common0 test KLIB and manifest; production UP-TO-DATE reused, zero Apple links/native tests |
| Affected real JavaFX9 | **9/9 pass**, five fresh XML, Gradle0/48.01s | Real Linux JavaFX/Compose runtime; no skipped/missing/duplicate cases; unchanged GET/POST and HTTP-only populations excluded |
| Camera5 source preflight666 | **PASS**, one finite host row | Planning only; no hosted compiler/native result |
| Android WebView5 preflight666 | **REFUSED**, CLI2 | Exact stale owner identity detected before emulator/native; not a device/library failure |
| Original UI650 | **FAILED**, Gradle1/3816.14s | Button partial1, adaptive incomplete/Unknown, eight unexecuted; **zero fully accepted native methods** |

The actual Camera compiler and JavaFX invocation maps both contain1,443 tracked
inputs and are equal before/after. This does not mean1,443 files were compiled,
or that unrelated targets were verified. The separate1,446 source-control map
contains source/tooling/documentation custody, not compiler/runtime outcomes.

See `archive-manifest.json` for independently copied evidence hashes. The source
seal retains its original file inventory; not every cached proposal file or
compiled binary is copied into this documentation. Relevant code and exact
inverse fragments are persistent in Git and `source/bindings659.json`.

## Implemented source changes and confirmed causes

### Desktop inline Unicode and diagnostic payload ownership

`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt`
now loads inline HTML via JavaFX's official ASCII data-URL path containing exact
UTF-8/Base64 bytes. The original655 supplementary-Unicode assertion failed;
the retained ingress probe established document-ingress corruption, not an exact
JNI mechanism. No document rewrite, fake bridge, history emulation or base-URL
workaround replaces the native implementation.

The native data URL contains the entire document. Location/history listeners,
request state and failure handling therefore keep inline payloads out of public
`requestedUrl`, `lastLoadedUrl`, saver metadata and error messages.
`WebViewContracts.kt::acceptContent` prevents even transient Desktop data-URL
request publication. Normal supported URL behavior remains; unsupported options
remain refused. Supplementary Unicode, native round trips, remount/history,
owner replacement, detach, weak retention, typed JS and cookie policy are covered
by the genuinely ingress-affected nine-method batch. Tests are library-level,
not sample applications or substitutes for other-platform integration.

Critical-JNI-call, signal-handler and Skiko fallback warnings remain in the
original log. JUnit success is **not** native dependency memory-safety, security,
GPU, macOS, Windows, Android, iOS, browser, consumer or release certification.
Issues#66/#73 require their remaining applicable original criteria.

### Camera test compiler, not invented native acceptance

`IosCameraOwnershipAcceptanceTest.kt` adds the required `NativeRuntimeApi` opt-in,
two explicit assertion generic types and four explicit ObjC empty-map types.
These resolve the seven actual test compiler errors; no production behavior,
original assertion, native input or lifecycle criterion was weakened.
Corresponding owning focus/init source identities are qualified by exact
reversible fragments, while prior manifests and historical pins remain sealed.

The original ownership production fix retains the request through native
presentation and dismissal completion. That source and the new tests compiled,
but Camera5's actual UIKit callback/recomposition/GC/disposal/image results are
still required. Tiny controlled24x16 images cannot satisfy physical12/48MP,
profiling, denial, disk-full or other original criteria. #76/#77/#79/#80 are not
closed by a KLIB compiler result.

### Tooling fixture recovery

The first27 failures were NEW fixture defects: an ambiguous owning `setUpClass`
selector and a prohibition scan confusing the exact singleton `re.compile`
regex with executable source compilation. Only those methods changed and ran
again. Existing20 bindings/43 inverse fragments held; the guard changed only
its exact manifest-SHA literal and the manifest changed the two NEW hashes.
Every executable guard byte is otherwise bound by its singleton template.

Independent658/610 source/result reviews and lead exact postimage/inverse checks
are archived. Their approval is source-control qualification, not verification
of blocked or unrelated native populations. Historical pending-selection wording
remains historical; the additive lead confirmation has its actual timestamp.

## Current Android routing blocker — confirmed, not guessed

`scripts/ci/library_tests.py:2347` invokes
`webview_content_policy_native_focus.py::configure_item`.
`source_contract` at214 refuses the owner script's raw hash because `_contract`
at201 takes the original WebView manifest's added-input owner hash, while659
changed that owner script. Exact target-native/helper source validation passes;
the current-contract owner identity is stale.

Impact: Android's finite native plan cannot be requested; the same shared owner
contract requires exact qualification for other affected focused platforms.
Recommended fix: an owning current identity/admission bridge with full-byte
source custody, original manifests/pins preserved, and finite important
positive/wrong/old/partial/foreign identity and real-CLI preflight checks.
Never use an unqualified dynamic self-hash or dispatch the known-failed profile.
Compiler/native assertions and production bytes do not need unrelated replay.
Repair667 is source-only preparation at this checkpoint.

## UI650 original preservation and next related batch

Run41790553079, attempt1, at
`ef6aae6da0c0879431d9c4712f8f914eaf6194ea` reached genuine compilation and Apple
linking but timed out at1920s in the native protocol. The button's partial pass
does not have complete Worker/PID/runtime-after witnesses. Adaptive is
Unknown/incomplete; eight methods never executed.1,417 actual input maps and252
trusted source copies hold. Owned stop/uninstall/absence cleanup passes;
final simulator-restoration receipt is absent. The original acquisition is reused
once, without download/replay or treating timeout as proof of its blocked call.

The exact Compose `ui-test:1.12.0` source JAR was acquired as bounded untrusted
ZIP data and inspected, never executed. `v2.runComposeUiTest` defaults to60s;
Skiko's idle timeout is checked after frame/render operations return, so it is
cooperative and not a hard native-call deadline. Screenshot capture includes
native redraw/snapshot/conversion. Cached1.12.2 sources do not establish1.12.0
behavior. The original hang's operation/root cause remains unknown.

Prepared single-leaf screenshot helpers close only freshly owned captures in
`finally`, using the existing supported `asSkiaBitmap().close()` contract. Fixed
first-row caller phases add diagnosis without changing waits/assertions/input.
Separate UI9/adaptive1 routes are being authored so one blocking test cannot
prevent the other nine missing outcomes. Existing exact10 remains intact.
No UI follow-up source integration, compiler or native acceptance is claimed here.

## Operational next steps and gates

1. Freeze/push development and request only Camera5 after fresh host-capacity
   readback; verify actual run SHA, not merely a dispatch response.
2. Repair the exact WebView owner contract; qualify finite important controls
   and failed source preflight, then request only Android's affected native5.
3. Continue disjoint UI9/adaptive1 and controlled-remote IO55 source preparation
   during CI. IO55 Downloads/restart/commercial-cloud criteria remain unresolved,
   never N/A or satisfied by a controlled loopback provider alone.
4. Accept original results and close complete original criteria promptly;
   no documentation or broad-suite waiting after actual qualifying evidence.

Retained counts (not a fresh GitHub query):103closed/69open/172total;
22implemented/36partial/101verified/five unresolved. No new issue closure.
Serial local heavy work requires>=8GiB **free disk**, compiler admission>=6GiB
MemAvailable. Maximum two combined hosted-heavy reservations includes queued and
reserved rows. Owner-authorized all Actions/no mandatory SHA pinning and minimum
`contents:read` permissions remain. Publication, deployment, Pages, main/history,
consumer, API/ABI, dependency, legal, security and release-readiness restrictions
remain. **No release or package has been published.**
