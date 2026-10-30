# Android popup policy — NATIVE-038/#90

## Contract

The common Android `WebView` does **not** implement child windows. With the
retained default `supportMultipleWindows=true`, actual requests reaching its
`onCreateWindow` handler are explicitly denied. The observable result is:

```kotlin
val rejection = state.settings.androidSettings.lastPopupRejection
LaunchedEffect(rejection?.requestNumber) {
    if (rejection != null) {
        // Show an application message or an explicitly chosen trusted fallback.
        // This event contains no destination URL or permission to open one.
    }
}
```

`AndroidPopupRejection(requestNumber, isDialog, isUserGesture)` keeps only the
latest event. Read it on the owner UI thread. The request number is not persisted,
not a security token and not a guarantee an observer consumed every event.
JavaScript-disabled/automatic-popup-blocked requests may never reach Android's
callback; no terminal event is fabricated for such requests.

Setting `supportMultipleWindows=false` deliberately uses Android's raw
**current-view navigation fallback**. It is not child-window support or our
rejection/origin policy, and can replace the current page. No application is
automatically opened by our handler. Full login/payment popup UI remains an
unsupported feature, not hidden behind a success value.

## Owning code and important tests

- `WebSettings.kt`: private-set Compose state; bounded metadata only; recording
  is not a settings update.
- `AndroidPopupRejection.kt`: additive public value type, no native/API rename.
- `WebView.android.kt`: current/native identity and initialized-state guards;
  records rejection and returns false without using `Message`/`hitTestResult`.
- `AndroidPopupRejectionTest.kt`: three host methods for unattached/uninitialized,
  1,000 latest-value events/no reapply, and replacement/detached callbacks. A
  shadow engine is not native popup execution.
- `AndroidWebViewPopupPolicyTest.kt`: three actual public composition methods,
  owned loopback HTTP servers, genuine DOM touches and native Android back input.
  Same/cross-origin/untrusted blank links; all eight native settings combinations;
  user and automatic script popups; explicit raw current-view navigation; retained
  parent history, replacement metadata and real native child removal on disposal.
- Finite `android-webview-popups` verification selects exactly those three device
  methods and no previously accepted WebView identity/lifetime or other suites.
  Original eleven full workflow slots remain unchanged.

The source guard first failed against the unobservable handler. The
[important implementation checks](evidence/popup-policy-batch-important-20261030/implementation001/README.md)
pass 93 synthetic methods and **3/3 fresh actual Robolectric host methods**;
device APK compilation/assembly also passes, exit0/653.17s, all922/999 inputs held.
Host shadows are not native popup input: **zero device methods executed here**.
Immutable Chromium verification and original-criteria review remain pending;
#90 stays open. A source/tooling/compile pass does not close it.

No physical/minimum Android, child-window UI, heap/ABI/consumer/security/release
certification. No registry packages, release, deployment, Pages or main/history
changes. See [ADR0012](../decisions/0012-android-popup-rejection-contract.md).
