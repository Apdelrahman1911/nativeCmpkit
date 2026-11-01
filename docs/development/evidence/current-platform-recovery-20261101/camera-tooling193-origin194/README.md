# Camera193 tooling failure / owning origin repair194

Actual [41361624566](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41361624566)
at `34c0ffc8` **FAILED in tooling**: 2,317 synthetic methods, 42 failure records
across eight methods, unittest 89.096s. **ZERO profile selection, Gradle, AVD, APK,
native tests, XML or artifacts.** This is not a new camera/platform failure.

The eight unchanged methods expected the original traversal refusal at line298.
Nine preceding helper lines moved the same `require` to307; original logs and
source equivalence prove that exact owning cause. Only three scalar expectations
are repaired, plus their two operational first-only driver hashes. The parser,
refusals, native assertions, controller, workflows, dependencies and public APIs
remain unchanged. Unknown native-state causes are not resolved by this patch.

Only the **eight actual failed methods** execute locally: **8/8 passed**,
zero failures/errors/skips, original unittest0.018s. Selection/import/run time
0.152695487s is separate, not additive test/native time. Both forbidden-action
lists are empty. All1,184 library/1,262 canonical combined inputs stay held during
the run. Independent exact inverse/source/results review accepts the owning patch.

Current46 driver pins plus the current driver hash bind47 current sources. The
older dated47 map/seals remain historical; they are **not claimed unchanged**.
Accepted camera186 first30 and camera009's three native cases are not replayed.
**#13 stays open**: only its genuine Dont-keepC1 still needs finite native execution
and original-criteria review. Compilation, restored-state cleanup, consumer/API-ABI,
dependency/legal/security/release and publishing gates do not pass here.

Raw originals and the full failed/accepted custody remain private and inert.
These small source/count-only exports are sealed by `SHA256SUMS`.
