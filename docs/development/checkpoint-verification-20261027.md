# Contained verification repair — 2026-10-27

Work remains single-agent on `development/preview-hardening`. The owner permits
verification Actions with all actions allowed/no mandatory SHA pinning; minimum
read-only permissions remain. **No packages, releases, snapshots, deployments or
Pages are authorized while readiness/security gates remain unsatisfied.**

## Fresh upstream reconciliation first

The [complete read-only refresh](upstream-refresh-20261027T014340Z/README.md)
recaptures16 open Calf issues,14 comments/47 timeline entries, and separately
one open PR (#551). All16 already have exactly one matching current destination
context. Zero imports/comments/closures are needed. Public descriptions/authors/
labels/timestamps/comments and stable timeline events match the earlier sync;
changed embedded destination projections are preserved in fresh raw payloads.
The [original posting/readback](upstream-sync-20261024T183300Z/README.md) and all
historical archives remain immutable. No runtime result or resolved-state
inference was added by this metadata refresh.

## Android's produced XML was missed by the old collector

Failed run [40434024680](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40434024680)
at immutable `569b1e16e2e6feb0dfa75721cd6422fc0c6b453c` compiles instrumentation
APKs, runs the connected command and cleanly tears down its owned Enforcing
API35/x86_64 emulator. The [independent review](evidence/github-actions/40434024680/lead-independent-review.json)
matches all704 selected source inputs and exact artifact/source contracts.

The new diagnostic inventories three actual `TEST-*.xml` files at
`build/outputs/androidTest-results/connected/androidMain`; the separately
declared intermediate was empty. The old collector/artifact glob targeted that
intermediate, so **zero uploaded/parsed testcase evidence was incorrectly treated
as evidence of zero execution**. Preserve the earlier receipts as observations
of that collector, not as proof that bodies never ran. Picker/WebView connected
tasks failed, but XML contents were not uploaded: counts and underlying causes
remain unknown. No testcase success is inferred from task status or file hashes.

The [owning regression pair](evidence/android-utp-xml-contract-20261027/lead-independent-review.json)
retains synthetic red20/18pass/2fail and green146/146 CI-tooling methods, with held
selected inputs. The collector now uses the observed UTP XML directory and keeps
the declared getter in a separate field. Both getter guards, strict fresh reports,
serial binding and failure propagation remain. Protobufs and intermediate-only
substitution cannot count as tests. A new clean immutable Android rerun is still
required; **zero Android/library methods execute in those Python fixtures**.

## Native application-host investigation, not UIKit success

[Actual Linux worker-body/failure/termination proof](evidence/native-worker-entry-contract-20261027-003/lead-independent-review.json)
executes two generated methods twice on an owned worker. Positive2pass/exit0 and
negative1pass/1intentional-fail/exit1 settle worker termination before process
exit. This is four fixture executions, not library/iOS tests; actual KGP/JUnit
parser integration remains pending.

[UIKit binding diagnostics](evidence/uikit-application-bindings-20261027/lead-independent-review.json)
retain the failed internal-ObjC/final-property/import attempt and the corrected
public-runtime-name/owned-window KLIB lowering. The latter exits0 on Linux in6s;
**zero Apple linking, application launch or library-native methods**. The existing
Compose v2 Skiko scene is not `UIApplication` hosting. See the
[native host contract](native-ui-application-host.md); do not skip the seven
presenter fixtures or waive the other native failures.

## State and remaining gates

The ledger stays **88 implemented / 68 partially verified / 8 unresolved /
0 verified**, covering all164 baseline findings/530 original requirements.
No issues closed; `main` remains at its synchronization checkpoint. Previous
successful same-input platform results are not blindly repeated, and no local
fixture/compile pass certifies a later commit.

The [held full preflight005](evidence/ci-preflight-20261027-005/lead-review.json)
passes21 commands/826 Python-tooling methods (including146 CI methods), strict
MkDocs and actionlint. All14,154 captured tracked/untracked inputs remain unchanged
through execution and before archive; **zero library/native/consumer methods**.
The preflight archive and this additive evidence-link update follow that freeze;
it is not circular self-verification or a release-candidate certification.
A new immutable Android rerun remains pending for the collector repair. Dependency enforcement,
native licenses/provenance, packaged consumers, ABI/minimum-platform and genuine
application/device requirements remain open in [release readiness](release-readiness.md).
