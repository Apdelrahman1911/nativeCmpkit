# Unknown routes and application-upgrade restoration

## Explicit library behavior

The repaired experimental adaptive host validates before rendering a destination:

- Duplicate graph registrations throw `IllegalArgumentException` naming the exact
  duplicate route; the first registration is not silently chosen.
- An unknown `startDestination` throws `IllegalArgumentException` before the host
  initializes a new stack.
- An already-attached controller rejects unknown `navigate` calls before changing
  the valid entry stack. Before attachment, nonblank routes may be prepared;
  mounting the host then checks every existing/restored entry against its graph.
- The public controller saver preserves saved entry identities and route order.
  It cannot know the application's new graph. A restored removed route therefore
  fails at host mounting; the library does **not** silently erase or skip entries.

Exact matching remains intentional. This is not pattern matching, deep-link
parsing, a native platform stack or automatic schema migration. Existing public
packages, factory/controller methods and the legacy back-stack descriptor remain;
fail-fast errors are an observable correction to the former blank-screen behavior.

## Deliberate application-selected fallback

An app upgrading its graph must migrate renamed/removed routes and changed argument
schemas **before mounting** the host. Preserve the business data independently;
navigation state is not a durable transaction or draft store.

If the app has explicitly chosen a reset when a removed route is restored, the
following policy can select a fresh controller. This reset is **potentially lossy**:
old navigation arguments and destination UI state are not transferred. Obtain user
consent or migrate/save important data according to the application's requirements.

```kotlin
import com.mohamedrejeb.calf.navigation.AdaptiveNavHostController

fun chooseControllerAfterUpgrade(
    restored: AdaptiveNavHostController,
    knownRoutes: Set<String>,
): AdaptiveNavHostController =
    if (restored.backStackEntries.any { it.route !in knownRoutes }) {
        AdaptiveNavHostController() // Explicit APP policy, never an automatic library reset.
    } else {
        restored
    }
```

Choose once in the application's restore/startup path, before `AdaptiveNavHost`;
use and persist the **selected** controller as the application's saved/navigation
owner thereafter. All navigation callbacks must refer to it. A plain `remember`
selection alone is not persistence across process recreation. Do not repeatedly
construct controllers during recomposition, delete individual saved entries to
hide an error, or catch an already-mounted host's composition failure as recovery.
The known-route set must reflect the same graph supplied to the host; route
presence alone does not validate a changed argument schema.

The regression exercises this exact removed-route selection policy with the
**public saver and a real serialization round-trip**, before mounting the public
Compose host. It checks preserved rejected entries, a distinct new controller and
entry ID, visible fresh home state, rejection of later unknown navigation without
stack mutation, and normal detail/back state restoration. It does not simulate
business-data recovery, Android process restoration, UIKit gestures or web history.

## Important verification

Four newly prepared real desktop Compose methods supplement the existing55-method
library suite: duplicate registration, unknown start, removed-route restore, and
explicit application-selected fallback/later invalid navigation. Hosted immutable
runtime results are still pending at this source checkpoint. Source inspection or
compilation alone does not close NAV-007. See
[ADR0004](../decisions/0004-adaptive-navigation-entries.md) and
[the library usage contract](../../calf-navigation/README.md).

## Accepted immutable execution — 2026-10-28

[Run40616313571](evidence/github-actions/40616313571/README.md) atc0f5cafc passes
59/59 actual desktop methods/seven fresh XML, including all16 public-host methods
and the four new required regressions.742 exact Git inputs, source identities,
XML/artifact digests and runtime reviewed. All3 original NAV-007 criteria accepted;
#95 closed **directly after review, before documentation**,30 closures total.
The prepared paragraph above describes the pre-run source checkpoint, not a
current pending test. Wider native/device/business-data/release limits remain.
