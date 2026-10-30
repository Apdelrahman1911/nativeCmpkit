# Mobile remount recovery: Android accepted, final UIKit release failed

Actual [41007203221](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41007203221)
at `a189bcb9fe2c1a812f18236c3aa4506bebf89ead` **remains FAILED**. Review binds all
904 library / 981 combined historical Git inputs, actual commands, fresh XML,
real host/device runtime and independently owned cleanup. No accepted unrelated
method is rerun; this profile requested only the two failed/unexecuted mobile cases.

- **Android: 1/1 PASS**, Gradle exit0 /74.02s, actual API35/x86_64/Enforcing,
  native document-title readiness and remount regression. Owned emulator teardown
  is clean; not physical/minimum-platform or process-death certification.
- **iOS: 1/1 FAIL**, Gradle exit1 /1069.39s. Genuine UIApplication, current native
  app/Worker/binary/installation/final owned-app cleanup all complete. The actual
  remount method fails `Expected <2>, actual <1>` at its final direct main-thread
  disposal assertion. No separately passed native method or completed release
  criterion is inferred from earlier assertions in this failed method.

[Deferred-release source review](interop-deferred-release-source-review.json)
confirms Compose1.12 schedules UIKit interop `onRelease` until an actual rendered
transaction, while the test host only waits for committed composition/Recomposer
idle before detaching the root. A scoped host recovery must await actual final
native detachment/delegate cleanup **while the root is still attached**; it must
not call the production cleanup/callback itself, add sleeps, skip/relax assertions,
change public APIs, or rely on deallocation. Runtime recovery is still needed to
establish the causal repair. Only the failed iOS method needs another execution;
the accepted Android method is not replayed.

The independent GET reviewer initially double-qualified an identity already
normalized by the exact frozen helper. [Reducer failure](reviewer-qualified-identity-failure.json)
is retained; comparing direct helper identities repairs only the review, not the
workflow or failed native case. Original dispatcher preflight failure likewise
remains private and historical. Reports omit console/properties; raw logs/ZIPs/
private app bundles/packages are not committed.

**#62/#89 remain open.** No release, package, Pages/deployment, main/history,
minimum-platform/ABI/consumer/dependency/provenance/legal/security gate is cleared.
