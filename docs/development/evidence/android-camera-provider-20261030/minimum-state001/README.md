# Owning API23 camera state restoration / one-case recovery

Actual [41087017676](../minimum-ci004/README.md) runs all four API23 native
methods: **three pass, one fails**; Gradle1/61.02s. Exact camera DEFAULT restoration
fails because Android6 `pm` has no `default-state`. Its finally failure may mask
an earlier assertion: do not accept any part of that fourth method. The previous
installed-path refusal remains an unknown response, not retrospectively diagnosed.

The test-only repair invokes Android6's exact PackageManager Binder operation
from the existing shell identity, for fixed system-camera package/user0/DEFAULT
only. It verifies the running framework's method signature and transaction field
(no hardcoded code), exact void no-exception reply and native state/handler readback.
No `enable`-instead-of-default, root, uninstall, unknown ABI fallback or warnings/
SELinux suppression. The API35 CLI route remains. All cleanup attempts run and
failures remain primary or suppressed failures, never success. Public Android6
source hashes/URLs and the unavailable wrong Debug.cpp-path observation are retained.

Three new source/selection/XML probes initially fail. **12+48+49 disjoint synthetic
host methods pass**; the middle command also fails on an accidentally nonexistent
module. Only the corrected workflow methods are run afterward; no 48-method replay.
Actionlint passes. Held **984 library/1061 combined inputs** compile the actual
reporter APK exit0/34.01s, **zero new native/library executions**. Compilation is
not closure; logs stay private and hashes/commands/outcomes are retained.

`android-camera-no-handler-minimum` requests **one** fresh API23 method using the
exact `Class#method` filter. Accepted API23 three/API35 four/host22 are reused after
source applicability review, not rerun or called fresh. All eleven full slots,
eight Android modules, installed-byte/UID/signature/grant/ownership/refusal gates
remain. #78 and #13 stay open pending their original criteria. Publishing, Pages,
main/history and independent native/device/consumer/ABI/legal/security/readiness
gates remain unchanged. The API23 private-platform operation exists only in this
disposable verification test, not the distributed library.
