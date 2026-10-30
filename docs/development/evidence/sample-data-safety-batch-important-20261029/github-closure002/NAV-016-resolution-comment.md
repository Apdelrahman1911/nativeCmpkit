<!-- nativecmpkit-resolution:NAV-016:20261030-shared-sample-builds -->
## Verified resolution — shared sample build patch
Removed the unused `libs.jetbrains.navigation.compose` dependency; retained the custom/adaptive implementation and **sample minSdk24**.

Reviewed all three original criteria:
1. Source/import checks and **six actual main compilation dependency graphs** (four Linux, two Apple) show the removed Navigation group is absent, the intended implementation retained, and no unresolved graph dependencies.
2. [Linux40979092763](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40979092763), immutable `01057aad57ec0ac34c28c1ef8ea59b716651e2c6`: actual Gradle **exit0/2787.56s** built Android/JVM/JS/Wasm. Fresh `:sample:desktop:jvmJar` TaskState is executed, not failed/skipped/NO-SOURCE/UP-TO-DATE. **The workflow/report remains failed at its JVM filename observer; no missing JAR hash or distribution pass is inferred.** [Apple40974963662](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40974963662), immutable `535b0353e2857d35ed799dbf997e3ab98e4c8684`: both Common frameworks built **exit0/3592.88s**, then the real unsigned Calf Xcode integration **exit0/58.75s**. Owner build files are unchanged between these runs/current. **ZERO tests requested/executed** in these build-only recoveries; prior accepted tests were not replayed.
3. **minSdk is not lowered.** No API23/device/merged-manifest, ABI or package-consumer certification is claimed.

Closing this dependency-cleanup issue using its actual original criteria, without waiting for unrelated report/native/distribution gates. NAV-008 and #100/NAV-013 remain open. Prior failed receipts and original issue body/history remain intact. No publishing, release, Pages or security gate is waived.

Additive reviewed evidence: `docs/development/evidence/sample-data-safety-batch-important-20261029/build-linux-ci002/`, `build-apple-ci001/`, and `github-closure002/NAV-016-original-criteria-acceptance.json` on `development/preview-hardening` (closure records committed afterward).
