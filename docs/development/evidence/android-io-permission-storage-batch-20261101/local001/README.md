# Android IO / permission / storage — held local source and manifests

On dirty `e9162681` + the reviewed 64-path test/tooling batch, all **1064
library / 1141 combined** input identities remained unchanged across five serial
commands. The accepted 41 applicable source/model outcomes were **reused**, not
replayed and not native executions.

| Actual command group | Exit | Seconds | Interpretation |
| --- | ---: | ---: | --- |
| IO helper assembly | 0 | 17.00 | Actual APK, no installation/tests |
| Permission helper assembly | 0 | 107.02 | Actual APK, no installation/tests |
| Six storage variants | 1 | 73.02 | Four owning compiler diagnostics; other variants unaccepted |
| Two library reporter assemblies | 1 | 103.02 | IO reporter completed; four permission compiler diagnostics |
| Debug/release sample merged manifests | 0 | 53.01 | Actual current generated XML, not library functionality |

Both generated manifests independently pass all **24 menu-row / 16-source-input**
correspondences. API status rows are source predictions, not OS observations.
The utility correctly does not itself claim it generated XML; the inspected
Gradle result separately establishes generation. Every merged extra declaration
is retained in the two correspondence reports. This satisfies the packaging
part of #102 C1, not its Call/picker/denial/media native criteria.

All eight real compiler diagnostics are preserved. The smallest five-Kotlin-file
repair uses public nullable `permissionToOp` with refusal on null, throwing
`Os.remove` with the original `lstat`/ENOENT/descriptor checks, the existing
permissions opt-in, equivalent forbidden-membership assertions and explicit
nullable heterogeneous array types. Recovery results belong to a later receipt.

Original six #102/#118 criteria remain literal; the independent source review
requires 13 actual permission/storage target executions, plus three separate IO
methods (16 total / 13 distinct methods). **ZERO new native executions** here.
No issue closure, packaged consumer/ABI/physical/vendor/minimum-device/security
or release clearance follows; publishing/Pages/main/history controls remain.
Raw build logs and signing material stay private; only hashes, commands, public
source identities and generated public manifest facts are archived.
