# #55 local named-provider original native failure

Run **41309673782 / attempt1**, job **124857866404**, immutable
`df5fd436090966b8ad8cc3cff59c57ba576dd9d2` is **FAILED**. One original native XML
contains exactly two new methods: **0passed/2failed/0skipped**, Gradle1/58.03s.
APK assembly passes0/249.08s; native suite8.554s (4.202+4.352), not the XML
container0.000s or Gradle duration. **Zero complete new methods are accepted.**

## Confirmed owning boundary

Both complete original failure traces identify
`NamedSystemDocumentsUi.resource:68` → `selectOwnedFolder:32` →
`AndroidIoNamedSystemProviderTest.namedProviderCase:71`:
**“The exact stock DocumentsUI control resource is unavailable.”**
The exact requested resource is `dir_list`, authored namespace
`com.android.documentsui`; source checks nonzero ID AND exact resource-name
equality before any owned-row query/click. The original does **not** log which
operand failed, resolved installed DocumentsUI package/version or resource-table
namespace. Do not guess Google/AOSP resource attribution or blame public metadata.
Returned tree admission, public metadata/read/descriptor/bookmark assertions were
not reached. Source/native prefix observations are not complete method acceptance.

## Independent custody and source

The assigned terminal identity was supplied before one metadata/run/job/inventory
acquisition, one target log and one artifact archive download (five exact GETs,
zero retries). Artifact13085032986 matches its server SHA256. All21 regular
JSON/XML members are bounded and inspected inertly; one original XML is retained
in the private original archive. Raw archives/logs and machine/native identities
are not exported. **50 passive custody/source/result checks pass; they are
not tests or proof the failed native methods passed.**

Independently bound all1223 combined/1147 library immutable Git blobs before
acquisition. All four actual before/after maps contain1147 identical entries and
match that fixed source;1223 is combined fixed-Git provenance, not an uploaded
actual combined map. Plans/filter/one actual connected-task marker/original XML
identify only the two new methods. Actual stable enforcing API35/x86_64 native
runtime and actual task Gradle9.7.1/JDK17.0.21 are recorded. No standalone root
daemon marker was uploaded; the receipt is not a separately reobserved marker.

## Cleanup and next scope

The controller independently records owned graceful emulator exit0/no forced
group. Separate ADB transport removal, reporter signer/install/uninstall or
direct native row/descriptor cleanup readbacks are unavailable. Immutable
`finally` retains the primary exception and attempts Activity/UI-flags/exact-row
cleanup; no suppressed cleanup failure is serialized. That absence is not a
standalone resource-success readback or a post-failure FD0 claim.

**#55 remains OPEN.** Both local-provider C1 executions are still failed; cloud
C1 remains a separate missing requirement. Authored Activity destruction/reopen
is not process restart; the system test caller is not public picker dispatch.
Use retained authoritative installed-resource evidence or exact bounded owning
diagnostics before any fixture repair/retry; do not relax native/control/cleanup
criteria. Accepted prior methods/compilers/source controls are not replayed.

No source/model/native test, compiler/planner, Git/GitHub mutation, live edit,
dispatch, retry, closure or package/release/deployment was performed by this
reviewer. Consumer/ABI/dependency/legal/security/readiness/publishing/Pages/main/
history and serial-local/8GiB/max2combined-hosted gates remain unchanged.
