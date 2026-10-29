# Related native lock/build verification batch — 2026-10-29

Related findings: BUILD-003/#2 native manifests, BUILD-004/#38 platform packaging,
BUILD-005/#39 Rust locks/toolchain, BUILD-007/#40 supply chain and BUILD-012/#147
picker dependency advisories. **No new issue closure or release gate is inferred
from the local tooling/metadata checks.**

## Important owning checks before immutable native CI

- [Local review](local/review.json):15new finite controller tests andonechanged
  original macOS-profile workflow guard pass. Orchestration tests use explicit
  adapters and execute **zero native builds/functionality tests**.859held inputs
  (858ordinary +oneexplicit native workflow), dirty at4fd0441e; immutable binding
  follows without replay after the production/recipe bytes are committed.
- Actual current-root conservative locked Cargo unions contain **93picker and
  48share packages/features**. Actual copied-source **offline** unchanged and
  restored controls agree exactly; removing one owning root dependency produces
  actual Cargo101/known `--locked` refusal without changing lock bytes. Production
  manifests untouched. The first exploratory diagnostic's unknown message
  classification is retained; owning parser recognizes Cargo1.98's new wording.
- [OSV](security/osv-native-locked-union.json): **92unique exact public crates.io
  coordinates, completed API scan, zero matches**. Conservative union includes
  dev/build/target-only dependencies; root unpublished crates excluded. OSV
  mirrors RustSec, but a separate direct RustSec-database scan was not executed.
  No compiled-payload/SBOM/exploitability/security-release certification.
- YAML/finite5host/minimum read-only credentials/reports-only source checks pass
  with existing locked docs PyYAML6.0.3. Initial system-Python missing-yaml check
  was not a workflow pass; no new dependency or library downgrade is introduced.

## Efficient exact native verification

`native-lock-reproducibility` selects five genuine builders: Linuxx64/arm64,
macOSarm64/x64 and Windowsx64, **max2jobs**. Windowsarm64 is not advertised.
Each builds **both** crates **twice**, with separately empty `CARGO_HOME` and
`target` directories, Cargo `--locked`, exact Rust1.98.0, existing release flags
and real binary/header/manifest validation. Complete sanitized Cargo graphs and
features, actual compiler/source/build metadata and binary hash/size observations
are compared. Byte differences remain explicit and are not hidden by graph passes.
Installed Rust/OS SDKs are prerequisites shared between attempts, not empty caches.

No Gradle/Android SDK/Java installation or accepted UI/native test suite replay.
Bounded process groups/time/disk preserve the8GiB reserve and stop only owned
processes. Owned temporary caches/binaries/fixtures are removed; failed stage/type
and exit receipts remain, raw private logs stay unuploaded. Artifacts are flat
JSON **reports only**, no native payload distribution/signing/publishing.

BUILD-005original clean-cache/pinned-every-target criteria await actual immutable
CI results. BUILD-003full candidate manifests/JAR/JNI, BUILD-004minimum/platform
compatibility, BUILD-007all ecosystem trust and BUILD-012real Linux chooser and
direct advisory checks remain independent. Native compiler passes execute zero
functionality tests, not UI/JNI/parent/provider/physical/minimum/ABI/full-consumer/
legal/provenance/security/release proof. Main/history/attribution unchanged;
**68closed/104open/172**, single-agent, immediate verified-subset batch closure.
