# Actual JDK17 daemon and disabled-provisioning verification

BUILD-009/[#42](https://github.com/Apdelrahman1911/nativeCmpkit/issues/42) was already
closed2026-10-24 at16:17:03UTC during migration: **not a new closure**.

[Installed OpenJDK proof](review.json): unchanged migrated checkout at immutable
e6a8ada7,776 inputs matching own Git blobs, actual Gradle help offline with
auto-download=false, auto-detect=false, and only the installed OpenJDK17 path.
The additional reviewed init observes those actual settings and requires that
the requested installation is the real root daemon, not a shell/setup assertion.
Exit0/48.01s, **zero library tests**. Vendor-neutral daemon criteria remain17.

[Actual CI daemons](actual-ci-daemons.json) were observed during five real library
targets (Linux/macOS/Windows desktop, JS/Wasm): actual Eclipse Adoptium17.0.20.1
daemons match selected launcher versions/homes. Accepted permission receipts are
archived separately, not extra JDK-specific tests. The witness exports versions/
vendor and correspondence booleans, not home paths/environment dumps.

This completes the finding's two original installed-JDK/CI-selection requirements,
not complete toolchain, dependency, native/minimum-platform, ABI/consumer, security
or release certification. No version downgrade or publishing.
