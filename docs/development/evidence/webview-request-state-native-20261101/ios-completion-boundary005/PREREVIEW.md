# #64 iOS request + DNS: private owning prereview

**Source-only, not Apple compiler/SDK/native acceptance.** No live edit, build,
SDK/native/network/Git/API/dispatch or issue mutation occurred here. Root owns
integration after its running Linux compiler completes, final source freeze,
one combined Mac request and original-source/results/cleanup review. #64 stays open.

## Confirmed boundary defect and minimal repair

The frozen request fixture `IosWebViewRequestAcceptanceTest.kt:173–180` asserts
main-thread inside the actual asynchronous WebKit completion. Production
`WebView.ios.kt:349–359` forwards `callback(result)` directly from
`WKWebView.evaluateJavaScript`; application callback exceptions are not caught.
The existing lifecycle contract at `IosWebViewLifecycleAcceptanceTest.kt:216–225`
explicitly forbids exceptions crossing a native asynchronous callback. This is
an unsafe source boundary, **not a demonstrated actual native failure cause**.

The exact helper replacement only records the bounded off-main fact, call count
and result inside that completion. The existing finite main predicate then returns
to `onApplicationMain` for the main-thread, exactly-once and non-null assertions.
`NativeWebViewApplicationHost.kt:52–57` catches that main-dispatched action and
rethrows the original failure on the generated Worker; `224–231` retains primary
failure and suppressed cleanup. The DNS helper already follows this protocol.

Authoritative delta: `fragments.json` contains exactly the request-helper fragment
and the one genuinely affected combined-guard native SHA literal. Apply those
only after exact source/mode checks; install the single new guard from postimages.
No production/DNS/transport/host/selector/declaration/timeout change. The entire
request source outside this helper retains SHA
`caed126d24aa87b2308dee1aac4f1af1b2a91cc3f1605bcb87dcbbde4768bb14`.
Repaired request SHA is
`569716cf0524d25b1b3c2712dbe040c0ec82cfe3db24f6dac3775e5ec15bd857`.

## Owning source verification, no old-suite replay

One new guard executed against the frozen old source once: one retained expected
failure at the native-completion assertion, no errors/skips. Before its first
green, a guard-only normalization mistake was repaired: remove exactly the
matched helper rather than deleting the retained following blank line. The
initial guard and all source-red records remain held; the red was not replayed.

The corrected owning guard executed once: **1/1 pass, 0.001836 s**, no errors/skips
or audit denials; 41 private identities/modes held. The guard checks facts-only
completion, off-main entry, finite completion predicate, main/once/non-null
assertions, exact outside-helper native bytes, repaired combined SHA pin and
Worker error/cleanup bridge. This is source proof, not an Objective-C or native
execution. Old accepted combined/profile/native models were not replayed.
The retained red used 39 inputs and 0.001197 s. Result summaries and input/log
hashes are included; raw logs and unchanged private source snapshots are excluded.

## Static contract observations (held sources)

- Request control at `IosWebViewRequestAcceptanceTest.kt:186–245` is Worker-only:
  typed `ObjCObjectVar<NSURLResponse?>`/`NSError?`, actual Foundation synchronous
  request, status 200L, finite 2 s timeout and 1–2048-byte records. The
  `NSMutableURLRequest().apply { setURL(...) }` pattern matches current production
  at `WebView.ios.kt:160–164`. No speculative API replacement is justified.
- The DNS five `WKNavigationDelegateProtocol` overrides (`:268–308`) mirror the
  current production signatures and `@ObjCSignatureOverride`. The owning
  forwarder records faults rather than throwing through callbacks (`:253–265`).
- DNS acquisition (`:310–321`) strongly retains the real normal forwarding
  delegate while WebKit's delegate property is weak. Its exact
  WK/state/observer/window lease is checked, the original delegate is restored
  in finally (`:103–113`, `:243–250`) without touching foreign ownership, and
  genuine host release still precedes post-release assertions (`:115–123`).
- Both DNS requests are actual retained-document links. Only framework
  NSURLErrorDomain/-1003 before any commit qualifies; no injected NSError,
  resolver override, certificate/ATS bypass, TLS/offline equivalence or timeout
  substitution is accepted.
- Original deadlines remain unchanged: native predicate 10 s, transport gate
  12 s, control 2 s, app host 1800 s, wrapper 1920 s and KGP task 2400 s.
  Full iOS inventory remains 14, combined selection remains 3, accepted 11 stay
  unselected. Native bodies and every external helper/control/cleanup byte in
  the 15-file original scope remain exact except this single request helper.

## Remaining actual-Mac obligations and Linux applicability

No additional confirmed cinterop/compiler/API defect was found in this bounded
source scope. That is not evidence of actual Apple compilation or availability.
Foundation deprecation/import availability, protocol overrides and NSNumber/data
bridges must be validated by the real Mac/iPhone SDK compiler. Reserved .invalid
resolution is nondeterministic; non--1003/timeout remains a refusal. Actual
provisional URL/error-reset timing, TLS classification/retries, native document
retention and held Stop client EOF still require the unchanged genuine methods.
Do not relax deadlines or substitute callbacks/server cleanup for native evidence.

The only Kotlin delta is in `src/iosTest`; the other delta and new guard are
Python source guards, not Gradle compiler inputs. The existing iOS application
task is `iosSimulatorArm64ApplicationTest` and explicitly requires macOS
(`calf-webview/build.gradle.kts:49–70`). Root's current four-task Linux compiler
cannot compile this iOS delta and must not be described as Apple acceptance.
After that compiler ends, root may preserve its unchanged Linux-task result
with this explicit applicability boundary, refreeze final inputs and own actual
Mac compilation/execution. This subagent has not rerun or accepted root's compiler.

Archive contains only the three required postimages, exact fragments, safe
identity/result summaries and this review. No credentials, environment values,
private runtime fixtures, raw terminal/native logs or unchanged source snapshots.
