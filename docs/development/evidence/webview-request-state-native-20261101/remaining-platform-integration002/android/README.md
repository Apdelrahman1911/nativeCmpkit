# Android #64 public Stop and real redirect fixture proposal

Extends the existing `android-webview-request-state` focus to exactly two still
unexecuted methods in `AndroidWebViewRequestStateDeviceTest`:

1. Existing compiled fail/fail/recovery/native-Reload method, byte-identical.
2. `publicNavigatorStopClosesHeldTransportAndActual302RedirectReloadUsesCurrentOwner`.

The separate new method uses the genuine public navigator Stop against an actual
held zero-response Chromium request. Only peer EOF after Stop and before fixture
release, unmount or close is a cancellation witness; timeout/reset/cleanup EOF is
not substituted. It then follows an owned wire-level302/Location response to a
distinct held destination, observes actual forwarded callback/common metadata
and authored DOM, and Reloads a no-store replacement at the same actual final URL.
The declarative content remains the redirect URL: an extra redirect request fails
the Reload assertion. Every stage retains one attached real Activity/Compose/native
owner; all exact acquired socket/route leases drain before explicit owner disposal.

The original request source reconstructs exactly to SHA256
`a78930b54606b88fb9e4af3e9e3748d41f1abf5496f05dad84eb8a664afc1f40`
after removing only the separate member insertion and helper append. Every old
native method/helper byte is preserved. The reused Activity/lifetime helper remains
`eae30dcbcb7b5df1fc3fb38384b9238e23acdd75d90b8f40c27eef31c8a6db23`.

## Exact integration

Use `fragments.json`: 15 exact-once fragments against the held preimages in the
manifest (native 2, library 4, owning guard 8, controller 1). Do not overwrite shared
library/controller files or wholesale rebase. The controller fragment changes only
one diagnostic string from one-method to two-method; the complete remaining AST
and all KVM/API/module logic are unchanged. Desired repository modes are 100644.
No profile, matrix, workflow, SDK package, permission, production API or reused
native/helper source is changed. The existing focus explicitly filters both exact
methods and requires both identities in one original fresh XML.

## Fresh source-only verification

- Two expected missing-feature baseline reds: 1 failure/1 error, no skips. Original
  traces/XML remain private; the safe summary carries the original XML hash.
- 4 genuinely new and 4 changed owning guard methods pass once: 8/8, no failures,
  errors or skips, 0.278288 seconds. Original passing XML/receipts are included
  unchanged. These are miniature source-plan/synthetic XML models, not Chromium.
- All 15 literal applications/reversals are exact-once; all four complete reverse
  reconstructions return the held preimages. The old native method and every old
  request helper are byte-exact, and the controller delta is AST-string-only.
- Unchanged accepted guard methods and native bodies were not replayed.

New Kotlin is NOT compiled or executed. The earlier APK compiler pass applies to
the unchanged original method/source only, not this extended fixture. The lead
owns final shared composition/freeze, compiler verification and any finite native
request. No broad map, real preflight, Git/API/network call, build, SDK/AVD/native
execution, live mutation, dispatch or closure was performed. #64 and all existing
acceptance/release/security gates remain unchanged.
