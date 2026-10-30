# Android foreground location prerequisites — 2026-10-30

Issue [#25/PERM-021](https://github.com/Apdelrahman1911/nativeCmpkit/issues/25)
is now **verified and closed** after all original criteria were reviewed against
actual results. This is an owning contract repair, not a new geo architecture or
permission-prompt feature. The older observations below describe their own dates.

Actual[41051631302](evidence/geo-prerequisites-20261030/native-ci001/README.md)
fails before native invocation: both APKs/owned cleanup pass, zero tests/XML.
The owning[scalar PermissionManager query](evidence/geo-prerequisites-20261030/permission-service001/README.md)
replaces its fragile human-dump gate;17 important synthetic methods pass.
Production/app/compiler bytes remained unchanged; all three later native cases
passed in41054442019. Accepted two injected/five host methods were not replayed.

## Default provider execution

`LocationTracker.startTrackingWithResult()` still marshals to `Main.immediate`.
The existing controller rejects an unbound/inactive owner or missing coarse/fine
permission. The subscription rechecks permission and uses the explicit main Looper.

`DefaultAndroidLocationClient.request()` now checks actual
`GoogleApiAvailabilityLight.isGooglePlayServicesAvailable()` and
`LocationManagerCompat.isLocationEnabled()` on **every** start, before creating or
calling the fused provider. Unavailable GMS returns `ProviderUnavailable` with its
actual numeric status. Disabled/unavailable system settings return that reason
without inventing a GMS code. No dialog, settings change, background permission,
or silent-success fallback is introduced.

The typed pre-registration exception tells the subscription no request was issued.
Cleanup must not construct a provider, or remove a nonexistent subscription even
when an earlier subscription initialized the same client. Real provider Tasks
and TOCTOU security errors retain their existing observable completion/removal/
retry/cancellation handling. Injected clients retain their existing behavior.
All public signatures, packages and dependency versions remain unchanged.

## Why a separate test UID is necessary

Actual run41042004511 failed its initial denied assertion before provider work.
Configured AGP's `gradle-work-action:32.4.0` uses
`android-test-engine:1.0.1`; the official source explicitly installs the test APK
with `grantPermissions=true`, and its installer implements `-g`. An assertion
about that reporter's initial denial is therefore not a valid OS fixture.
See [the read-only source observation](evidence/geo-prerequisites-20261030/implementation001/official-installer-source-observation.json).

`tests/consumer/android-geo-probe` is a standalone Java **source** consumer of the
real public tracker. It runs a real foreground FragmentActivity in another UID.
The controller builds and installs it without `-g`/`-r`, checks installed APK bytes,
and reverifies/removes it before shutting down its owned AVD. Assembly, probe
and connected task share the same private debug-signing directory. Signatures,
exact reporter package, UID, nonce and connection lease guard the finite Messenger
protocol; the reporter owns its reply thread and death observer.

Only the explicit disposable API35 instrumentation fixture may mutate this UID or
its system-image prerequisites. The three methods cover denied/unbound/coarse/
fine/default-GMS starts; actual permission-revocation process death and restart;
disabled **and actually user-uninstalled** Play Services, settings off and recovery.
The system-image GMS copy is checked before mutation and restored locally with
`install-existing`, enable and settings restoration in `finally`. No registry
publication or user-device fallback exists. A missing dumpsys permission row is
**unknown**, not inferred denial: same-UID native reads still decide the tests.

ATE1.0.1 flattens runner arguments as CSV. The recovery therefore uses one actual
runtime annotation selecting exactly three methods, not a comma-containing class
filter. The collector still requires all three exact fresh XML cases, the actual
task marker, immutable inputs, enforcing runtime and owned cleanup. The two
already-passing injected native Task/Looper methods are deliberately excluded.

## Executed evidence and limits

[Native41054442019](evidence/geo-prerequisites-20261030/native-ci002/README.md)
at a6c16e09 passes3/3 actual native methods in one fresh XML, Gradle0/54.02s.
Exact945 library/1022 combined historical inputs, fresh filter/task, native runtime,
installed APK-byte/signature/UID identity and owned cleanup were reviewed. The
[original criteria/readback](evidence/geo-prerequisites-20261030/closure001/README.md)
close #25 before documentation; two prior native and five prior host cases reused.
Earlier failures stay failed. These three new methods are not ten new executions.


[Important evidence](evidence/geo-prerequisites-20261030/implementation001/README.md):
five new Robolectric methods pass; device APK and standalone Java source consumer
assemble. Actual signatures match and manifests declare min23/target37 and the
signature-protected protocol. **Zero new native device methods have run locally.**
The two accepted native methods from41042004511 are reused on byte-identical bodies.
No sample substitutes for these library tests. GPS delivery/accuracy, physical or
minimum-device, power/heap, packaged Maven consumer, ABI and release/security gates
remain separate. No package, release, deployment, Pages or main/history change.
