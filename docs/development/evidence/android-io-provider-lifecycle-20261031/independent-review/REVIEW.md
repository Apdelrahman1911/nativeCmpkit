# Final Android IO hooks review

**Ready for the lead’s contained source integration. No source-confirmed blocker
was found in the final adapter/controller/SDK/cache hooks.** This is source-only
readiness; no build, SDK inspection, native execution, CI dispatch or Git/GitHub
mutation was performed by this reviewer. #45/#55/#57 must remain open.

The reviewed patch is **25 files / 180,559 bytes**, SHA256
`11552d98ceae0b9f3cc9c67fcce91f895ad26652c7e8c39e37204d324f62623a`.
All 25 candidate hashes and current preimages match the final manifest at
HEAD `7380a04674c2dc83583a45953418ec2c823b4258`; each unified diff was independently
reconstructed from those preimages and equals the frozen candidate bytes.
The author’s recorded base remains `5e9cfdd1`; the newer current HEAD does not
change any patch preimage. The earlier independent fixture review applies to
18 unchanged inputs; the subsequently expanded adapter is covered here.

- **Signing and order:** `android_io_documents.py:186–278` requires one verified
  v2/v3 signer, exact private debug-key DER certificate equality, stable key stat,
  compiled minimal manifest policy, installed/source APK hash agreement and
  source/APK recheck. `android_device_tests.py:233–337` boots its owned Enforcing
  emulator, prepares and validates the helper, then assembles the reporter and
  executes native tests. `library_tests.py:2553–2627` emits the IO instrumentation
  bit only after prepared-receipt validation; assembly-only contains no connected
  task or IO bit. Helper, reporter and tests share the controller’s private key home.
- **Partial failure and cleanup:** inherited installer refuses an existing package
  and uses neither `-g` nor `-r` (`android_share_recipient.py:67–109`). Failed or
  uncertain installation retains the expected digest for reconciliation. Cleanup
  rechecks the actual owned lease and installed bytes before stop/uninstall; it
  refuses unknown/foreign identity. The adapter and controller preserve partial
  preparation facts and errors. Final pass requires passed preparation/cleanup,
  verified owned removal, unchanged sources, graceful child exit and ADB absence
  (`android_device_tests.py:378–431`); forced shutdown cannot become success.
- **SDK/cache/permissions:** workflow `gradle.yml:306` explicitly installs the
  cmdline23/platform37.0/build-tools36.0.0/API35 recipe for finite IO and full35.
  `dependency_cache_inputs.py:89–98` binds helper build/settings/properties,
  manifest and adapter recipe; existing catalog and IO project declarations are
  keyed. Java/tests/APKs/signing/XML outputs remain excluded. The exact-primary
  failure-safe cache steps remain unchanged and workflow permission is contents:read.
- **Finite and full routes:** exact five-method class filtering and one fresh XML
  remain mandatory (`library_tests.py:1677–1692,1898–1914,2398–2405`). Accepted
  oversize/host methods are excluded from this request. All eleven existing slots
  remain; its full Android slot is API35 with eight modules. API23 is only a finite
  camera route. Full API23 requests already refuse before host/lock/output/plan,
  and camera23 requires no IO helper (`android_device_tests.py:437–479`). Pure plan
  checks confirmed this; no exclusion or skipped-test policy is needed.

The source still requires actual Activity-result read/persistable/prefix grants,
client/provider self-kill with observed Binder death and changed native identities,
source-owner framework revocation, public recovery reads, and Coil descriptor
closure. All remain **native-unexecuted** here. The Coil methods use an injected
decoder with the real ImageLoader/KmpFileFetcher/Okio source path; they do not
prove default bitmap decoding. Directory null-size is not an unknown-size byte
stream. No default-decode/peak-memory/key/cloud/iCloud/reboot/ABI/security/readiness
or original issue closure inference is justified.

The 42 author-owned modeled acceptance lines and all eleven bound log hashes were
read back without replaying those methods or accepted suites. Initial failures
remain retained. See `checklist.json`, `provenance.json` and `api-selection.json`.
After integration, the lead must freeze actual inputs, complete only necessary
compiler/cross-owner checks when capacity frees, and review the five new native
results and owned cleanup against the original criteria.

One nonblocking handoff correction remains: author README lines9–10 describe the
old 19-file/v1 patch and lines76–87 say hooks are absent. Final proof/manifest/patch
correctly bind the 25-file hooks. Update that narrative while preserving v1 history.
