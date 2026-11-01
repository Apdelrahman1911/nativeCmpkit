# Verified Android subsets — no whole-issue closure

| Issue | Actual run | Fresh native result | Remaining original work |
|---|---|---|---|
| #102 /NAV-015 | [41293333402](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41293333402) | Denial1/1; Gradle0/39.02s | API33/API34 media, now requested serially |
| #55 /IO-019 | [41294135981](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41294135981) | Provider outage1/1; Gradle0/36.02s | C1 named system/cloud providers |
| #64 /NATIVE-005 | [41294331841](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41294331841) | Public Stop/302/Reload1/1; Gradle0/48.02s | Desktop10 and real JS/Wasm offline2 |

All three immutable e16268a6 results have independently reviewed original source,
XML/selection/runtime/cleanup witnesses and four actual1124 library maps.1201 is
combined predispatch-only. Passive39/69/49 integrity/source checks are not tests.
Accepted Call/picker/IO/held Android fail-fail-Reload/iOS/DNS results are reused,
never replayed. Post-restart IO counters do not prove zero outage opens; Android
Stop reporter install/uninstall and separate ADB removal readbacks remain unavailable.

[Denial packet](../permission-denial-original076/README.md),
[IO outage packet](../io-provider-unavailable-original076/README.md),
[Stop packet](../android-stop-original076/README.md) were byte/hash verified and
copied unchanged. Private originals were not reacquired or exported. One private
Stop source-slice preparation error is retained separately. No issue was closed
by packet copying; no release, publishing, main or security gate is cleared.

[Camera original075](../camera-absence-original075/README.md) remains failed before
native/XML. [Official Android15 source review](../camera-absence-os-source076/README.md)
qualifies no parser relaxation/replacement or blind retry. #13 C1 stays missing;
accepted camera009 C2/C3 stay unreplayed.
