# Actual Android default-Coil decode — three scoped native passes

[Run41250376146](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41250376146),
attempt1 at `69a93c6d879435d4c620979b992a77161baae615`, **SUCCESS**:
API35 **3/3 actual whole native methods / one original XML**, Gradle **0/40.02s**.
All three requested methods are accepted. **No recovery/replay is justified.**
The two earlier tooling-stopped runs41249622333/41249673735 remain failed.

## Exact accepted scope

- Native257x193 seeded PNG, real unknown-size/openable provider metadata,
  source-only streaming fetch with partial encoded buffering, unmodified default
  `BitmapFactoryDecoder` and equality of every opaque/transparent output pixel.
- Native96x64 JPEG with real EXIF orientation6/7, default buffered bounds/EXIF
  compatible decode, independent64x96 rotation/reflection quadrant expectations
  and interior RGB tolerance12. Not kernel seek or metadata `ImageDecoder`.
- Four sequential actual default corrupt-image failures, real cross-UID REG
  descriptors, fixed native Activity-result tree grants/bookmark and native
  signature/UID/nonce/PID/process/generation assertions, opens/closes1..4,
  zero closeErrors/writes and reporter FD0 after each failure.

PNG/JPEG FileProvider is **separate-process, same UID**. Corrupt-image source is
**separate UID**. No decoder is injected; listener observations only peek without
consuming/replacing the actual source. The three methods reach seven bounded
image requests internally; **seven is not the method/target execution count**.
Source/bitmap/bookmark/endpoint/thread and exclusive owned-file cleanup preserve
primary failures. Every normal successful/error path reaches its asserted cleanup;
this is not runtime calibration of every possible cleanup failure path.

## Immutable provenance and actual results

All **1018 library / 1095 combined** frozen hashes independently match Git objects
at the exact SHA, not the current dirty worktree. All four uploaded controller/
library before/after maps equal the **1018 library** map. **No actual combined1095
map is uploaded**; combined scope remains immutable-Git request applicability.
Exact source plans, task/class filter, one fresh marker and source revisions agree.
Actual runtime is Enforcing **API35 / Android15 / x86_64** on the owned emulator;
JDK17/Android37.0 are compile context, not minimum-API acceptance.

CI helper compilation **0/119.05s** and reporter compilation **0/266.07s** are
not extra native outcomes. Strict apksigner36.0.0 check is **integer API35/35
only**, with warning/error/single-modern-signer refusals intact. CI source and
installed helper bytes match its own private signing-certificate identity;
local APK equality across signing homes is not asserted. Native UID/signature/
grant assertions are source-bound through the passing whole methods; raw numeric
UID/PID/generation values are not separately exported. Helper receipt's generic
provider-only scope is not used to infer decoder execution.

Helper ownership is reverified, force-stop/uninstall exit0 and absence observed.
Owned emulator shutdown is graceful/exit0, no forced group, and ADB transport
removal observed. Original collector/fresh-init gates require actual new XML,
mtime within invocation +/-2s, stable regular files, exact unique methods and no
skips. Original stat values are not exported; naive XML/ZIP timestamps alone
are **not independent timezone or original-stat evidence**.

## Original criteria and reusable evidence

**#45/IO-008, #55/IO-019 and #57/IO-021 remain OPEN.** All16 original criteria
are preserved and mapped in `original-criteria.json`/`criterion-subset-review.json`.
This run strengthens #57 default-decoder error/source ownership, PNG binary/
pixel fidelity and JPEG EXIF compatibility. It does not newly complete #45/#55:
fixed grant/release is a prerequisite, not another restart/revocation outcome;
openable FileProvider metadata is not a `file://` or DocumentsContract single-
document regression. Do not create duplicate progress claims for those criteria.

The earlier [five native lifecycle outcomes](../../android-io-provider-lifecycle-20261031/native-ci001/README.md)
remain accepted and are reused, not replayed/recounted, on47 byte-identical owning
library/helper/host sources and declarations. Earlier injected paused-decoder
cancellation remains **injected**; no default-cancellation claim follows. Existing
accepted host/oversize/camera results are untouched, not executed again here.

Remaining work includes Apple/iCloud scopes/bookmarks/save callbacks, system/cloud
folder providers, broader restart/permanent-unavailability and `file://` cases;
large-image peak-memory benchmarks by target, stable request keys/invalidation,
main-thread misuse guidance and other-platform/default-cancellation verification.
No physical/min23/vendor/cloud, packaged consumer/API-ABI, dependency/legal/
security/readiness or release gate is cleared. Cache metadata is preserved only
as original run evidence, **not #40/cache-speedup/dependency-trust acceptance**.
No new production patch or confirmed library bug is claimed by this review.

## Private originals and public-safe archive

One artifact download only: ID13060484532, **215435 bytes**, SHA256
`86c4dcdcf899e2ccfd8e800c4491086aeab7db22a1bb2db4e9c968b7b1d0af25`.
Strict ZIP member/type/size/CRC/path checks pass;20 JSON/XML objects, no packages
or console logs. **19 artifact objects preserve exact original bytes**; only the
one device plan's two absolute SDK command prefixes are display-redacted.

The byte-exact original XML is **959 bytes**, SHA256
`f865db6092e318b5eca730b6c675dec92cec47d4e6e389cc3480ecdd947d8bb8`,
with a supported `testsuites` wrapper, one suite and the exact three passed cases.
It contains only the safe owned-device property; no failure/console bodies.
`archive-provenance.json` records original/archive hashes and treatment;
`withheld-values.json` records scalar/raw-original hashes without publishing
private values. Raw ZIP, SDK/local prefixes, API originals, sources, keys/APKs,
logs and private context remain private. Redacted command displays are **not
executable verification requests**.

`data-review.json` has94 independent source/data consistency checks, **not94
extra native/model tests**. The reviewer performs GET-only metadata/artifact
inspection and immutable Git reads: no builds, SDK operations, tests/model replay,
redispatch, Git/GitHub mutation, shared edit or issue closure. The lead alone
integrates this bounded archive and decides original-criterion progress updates.
`SHA256SUMS`, `manifest.json` and `manifest.sha256` anchor this delivery; these
hashes are integrity records, not publisher authentication or release readiness.
