# ADR 0008 — NativeCmpKit display identity, compatible public names

- Date: 2026-10-27
- Status: accepted owner naming decision; distribution and ABI gates remain open
- Amends ADR 0001's current display/root name only; historical records are unchanged

## Decision

The library is **NativeCmpKit**. Use that exact spelling in the Gradle root,
publication POM display names, current entry-point documentation, workflow names,
sample application labels and the library-only UIKit verification application's
display name. Record the prior name additively in `docs/migration/identity.json`.

Retain the existing repository `Apdelrahman1911/nativeCmpkit`, lowercase Maven
group/artifact IDs, `calf-*` project paths, public `com.mohamedrejeb.calf.*`
packages, generated-resource namespaces, JNI/native/framework/executable names,
and `nativeCmpkit.version` / `nativeCmpkit.allowPublishing` Gradle properties.
The owner requested a library name, not a new GitHub repository or API rewrite.

Do not rewrite imported Git objects, old migration/audit observations, copyright,
attribution or archived user text. Native names must still move together if a
later separately reviewed migration changes them. Old and new Maven artifacts
must not share a classpath because the retained packages contain duplicate classes.

## Verification and consequences

- Five current-identity guards and the POM verifier enforce the display spelling;
  root and target POMs use the exact owning module's name. Coordinates do not change.
- Real copied-root Gradle help/KGP model and UIKit-test KLIB compilation pass at
  the [720-input source freeze](../development/evidence/current-root-klib-20261027/ui/receipt.json).
  This is configuration/typechecking, **zero native test executions**.
- New local-only staging and independent packaged-consumer execution must verify
  the changed POMs; historical static inspection is not reused as a new-name pass.
- No package, release, deployment or Pages publication is authorized by a rename.
  All [readiness/security gates](../development/release-readiness.md) remain.

## Rejected alternatives

- Mass package/native/resource renaming: unnecessary compatibility risk.
- Renaming historical records: misrepresents preserved evidence and attribution.
- Changing Maven coordinates or Gradle property keys for capitalization: breaks
  existing build scripts without improving the requested display identity.

See [the current checkpoint](../development/checkpoint-identity-closures-20261027.md)
for executed guard results, retained failures and pending immutable CI.
