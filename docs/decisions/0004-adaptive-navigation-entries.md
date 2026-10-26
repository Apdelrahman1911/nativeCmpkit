# ADR 0004 — Entry-owned state in experimental adaptive navigation

**Status:** accepted for implementation, 2026-10-24; verification is recorded
separately in `docs/development/NAV.md`. Lead approved the compatibility strategy
before source changes. Applies to NAV-001–008, not a native navigation rewrite.

## Context

The unpublished `calf-navigation` module exposes a `SnapshotStateList<String>`.
Routes are destination identifiers, not visit identifiers. Using them as saved
state keys aliases duplicate visits, loses per-navigation arguments, and cannot
recognize a pop followed immediately by another visit to the same route.
The argument helpers also inherited Android-only documentation and unchecked
generic contracts that cannot be implemented as advertised in portable Kotlin.

## Decision

1. A controller owns a canonical, observable stack of `NavBackStackEntry` objects.
   Each entry has an ID, route and snapshotted, portable argument values. IDs are
   a saved controller namespace plus a monotonically increasing sequence; they
   are not security tokens. State retention, composition identity and cleanup use
   IDs, never sets of route strings. Controller operations are UI-thread confined.
2. Keep the **exact** `backStack: SnapshotStateList<String>` public getter as a
   deprecated compatibility mirror. Controlled `navigate`/`popBackStack` operations
   update the canonical entries and mirror in one snapshot. New code observes
   read-only `backStackEntries`/`currentBackStackEntry` and uses controlled methods.
   An observed legacy list change retains only its common prefix; the changed
   suffix receives fresh IDs and no inherited arguments/state. Direct net-equal
   remove/reinsert operations before an observation are **ambiguous and unsupported
   for entry identity**. No equality-based mirror can reconstruct those events.
3. Retain `navigate(route, Map<String, NavArgument>)`. Its supplied arguments must
   contain explicit defaults, which are interpreted as values rather than silently
   discarded. Add `navigateWithValues` for a value map. Destination `arguments`
   remain the schema; host content retains its old callback type but receives
   validated, resolved arguments. Supplied payloads belong to each entry; missing
   defaults come from the current graph. Only portable built-in values are saved.
   Values are saved by `rememberSaveable`: applications must not put secrets here.
4. Use a versioned, scalar/list saver with explicit type codecs. Restore the old
   route-array representation as fresh entries. Old route-keyed UI state cannot
   be reliably migrated for duplicates; only route order is migrated. IDs and
   payloads in the new format round-trip. Arbitrary objects/reflection and URI
   route matching/deep links are not part of this contract.
5. Rebuild the small graph specification on recomposition so closures are current.
   Require unique, nonempty routes and coverage of every stacked route. Initialize
   an empty controller when controller/start changes, but do not reset a nonempty
   stack. Bind one host per controller; dispose its graph binding when it leaves.
   Unknown routes and invalid arguments fail predictably instead of rendering blank.
6. `NavArgument` distinguishes absence of a default from an explicit null and
   validates construction. Its `defaultValue` becomes nullable (same JVM Object
   getter descriptor, but source callers assuming non-null must handle null).
   Built-in arrays are defensively copied at the navigation boundary. Bundle maps
   themselves remain mutable, in-memory, non-thread-safe containers, not Parcels.
7. Preserve the erased generic bundle `get<T>` method for old binaries, deprecate
   it and document its unchecked nature. Add separately named reified `getOrNull<T>`
   and use checked getters in library code. It cannot validate erased generic
   element types; use explicit collection accessors where available. Do **not**
   replace the existing method body with a reified marker that breaks old binaries.
8. Keep raw `parseValue` behavior where compatible. Add `parseSerializedValue` as
   the explicit inverse of URI-safe string/length-framed array serialization and
   bulk `parseValues` for arrays. Do not silently URI-decode arbitrary raw values.
   Old array object-toString output was not a usable persistent format; old raw
   strings are not automatically interpreted as the new serialized representation.
9. The adaptive controller remains an independent Compose stack. Android system
   back dispatch is integrated; UIKit interactive back, browser history, desktop
   back shortcuts and per-entry ViewModel/lifecycle owners are not implemented.
   Keep the separate legacy `NavHostController` platform bridge, document its
   different AndroidX identity, and offer an explicitly named adaptive factory.

## Rejected alternatives

- Replacing the public `SnapshotStateList` getter with `MutableList`: ordinary
  callers may work, but it changes the getter's binary descriptor and breaks
  explicitly typed consumers without being necessary to fix supported operations.
- Continuing to key state by routes or trying to recover complete mutation history
  from equal route lists. Neither distinguishes duplicate visits reliably.
- Keying a saveable holder by controller object identity: process restoration
  creates a new controller object and must still find its saved entry IDs.
- Pretending an erased `<T>` cast is runtime-safe on all targets, or treating a
  passing old defect-confirmation probe as a new regression test.
- Adopting native platform stacks, AndroidX internals, custom serializers or route
  pattern matching as an incidental repair of these findings.

## Compatibility and verification consequences

Existing packages, class names, ordinary navigate/pop calls, the exact legacy
back-stack getter type and erased bundle getter descriptor remain. Corrected
fail-fast validation, entry argument delivery, nullability and helper serialization
are intentional observable changes; this is **not a full ABI certification**.
The deprecated raw-mutation and unchecked-get limitations remain explicit.

Required regression coverage includes duplicate and consecutive visits, same-frame
pop/revisit, cleanup, replacement controllers/current callbacks, schema validation,
legacy mirror imports and getter type, old/new saver formats, value snapshots,
nullable defaults, checked bundle access, codec malformed/Unicode/null/array cases,
and multi-target common tests. Compose host tests must exercise actual library code.
Native/browser navigation integration is not inferred from JVM test success.
