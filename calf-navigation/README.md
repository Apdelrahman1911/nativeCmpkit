# Experimental adaptive navigation

This unpublished module supplies an independent Compose stack, **not** a
cross-platform wrapper around native UIKit/browser stacks. Android system back is
handled; browser history, UIKit interactive back, desktop back shortcuts and
per-entry ViewModel/lifecycle owners are not implemented.

```kotlin
val controller = rememberAdaptiveNavController()
AdaptiveNavHost(controller, startDestination = "home") {
    composable("home") {
        Button(onClick = {
            controller.navigateWithValues("detail", mapOf("id" to 42))
        }) { Text("Open item") }
    }
    composable(
        "detail",
        arguments = mapOf(
            "id" to NavArgument.Builder().setType(AdaptiveNavType.IntType).build(),
            "title" to NavArgument.Builder().setDefaultValue("Item").build(),
        ),
    ) { arguments ->
        Text("${arguments.getValue("title").defaultValue}: ${arguments.getValue("id").defaultValue}")
    }
}
```

The example uses the library's `com.mohamedrejeb.calf.navigation.*` types and
Compose's `Button`/`Text`. Schema definitions belong to `composable`; each content
callback receives validated resolved arguments in the retained `Map<String,
NavArgument>` callback shape. For a nullable default, use `setIsNullable(true)` and
`setDefaultValue(null)`. Not setting a default is different from setting null.

## Visits, values and state

- Each navigate creates a fresh entry ID, including consecutive visits to the same
  route. A destination's `rememberSaveable` state survives while its entry remains
  on the stack, and is dropped when that entry is popped. Plain `remember` is not
  retained while a destination is absent from composition.
- `backStackEntries` and `currentBackStackEntry` are read-only snapshots. Entry
  `arguments` are the values supplied to that visit, without the graph's current
  defaults. Built-in arrays are copied on insertion/access. A later graph-default
  change affects entries that did not supply that argument.
- Supported payloads are Int, Long, Float, Boolean, String/null and their built-in
  arrays. Arbitrary objects/Parcelable/reflection are not supported. Keep saved
  payloads small; store IDs rather than files/large data, and **never store secrets**.
- Navigation and graph updates are UI-thread confined. A controller has one active
  host. Graph closures refresh on recomposition; every stacked route must remain
  registered and valid. Changing the start route does not reset an existing stack.
  Blank/duplicate/unknown routes and invalid arguments fail with clear exceptions.
- Restoration preserves the new entry IDs/payloads. Old route-array saves preserve
  route order, but their ambiguous route-keyed UI state cannot be migrated safely.

## Legacy API migration

`rememberNavController()` remains an alias of the explicit adaptive factory. The
separate `NavHostController` expect/actual bridge still means **AndroidX** on Android
and adaptive elsewhere; do not mix it with this host on Android.

`navigate(route, arguments = mapOf("id" to NavArgument.Builder()
.setDefaultValue(42).build()))` remains available and now actually delivers values.
Passing a required schema without a value to `navigate` is an error; put it in the
graph instead.

The exact deprecated `backStack: SnapshotStateList<String>` getter remains for
compatibility. Use controlled methods for all mutations. An observed direct edit
can only retain the unchanged prefix; suffix state/arguments are conservatively
discarded. Net-equal direct pop/reinsert before observation cannot express a new
visit. This limitation is not present in `navigate`/`popBackStack`.

For bundles, replace unsafe erased `bundle.get<T>(key)` with `getOrNull<T>` or a
typed getter. The old erased method is retained, not falsely made runtime-safe.
Use `getStringArray`/`getCharSequenceArray` for checked object-array access: they
inspect current elements and return a borrowed reference. `getOrNull` alone cannot
validate erased generic elements. Bundle setters and `mMap` share references;
navigation entries/defaults instead take defensive copies. Create portable string
arrays with `arrayOf<String>(...)`/`emptyArray<String>()`: JVM component metadata
rejects `Array<Any>`, even if empty or string-filled; Native erases that metadata
and can only validate the current elements. An empty erased array therefore has
no invalid element and is accepted, while mixed/null String elements are rejected.
For serialized values, pair `serializeAsValue` with **`parseSerializedValue`**;
`parseValue` is still the raw-value parser. Use bulk `parseValues` for arrays rather
than repeatedly copying an ever-growing array.

See [ADR0004](../docs/decisions/0004-adaptive-navigation-entries.md),
[implementation/test evidence](../docs/development/NAV.md) and the
[baseline audit](../docs/audit/navigation-core-icons-sample.md). Retained signatures
are not whole-library ABI or platform-runtime certification.

## Removed routes after an application upgrade

The saver preserves routes but cannot know the new graph. A removed restored route
fails explicitly when the host mounts; it is never silently dropped. Migrate routes
and arguments **before mounting**, or deliberately select a fresh controller using
[the documented app fallback](../docs/development/navigation-unknown-routes.md).
A reset can lose navigation/UI state: preserve business data independently and
persist the selected controller. This is not automatic lossless library recovery.
