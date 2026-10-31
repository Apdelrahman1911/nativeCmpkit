# Native parent ownership — source-backed gap, #58 remains open

Fourteen source observations, **zero native/compiler/model tests**. OpenJDK macOS
JAWT Lock/Unlock are no-ops. The selected plain Skiko pointer getter bypasses its
actual `CFRetainedResource.execute` disposal guard. Public Skiko/JAWT callbacks do
not establish a borrowed platform peer becoming an independently retained owner.

A main-thread refusal alone is not a memory-safety/ownership fix. The minimum
blocker is scoped guarded peer acquisition plus a native ownership/thread/
generation protocol and actual dispose/remount/recreate/missing-parent platform
controls. See the preserved source review/test plan; no speculative production
patch, native/platform/security/consumer/ABI/readiness or closure is inferred.
