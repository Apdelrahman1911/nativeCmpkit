# Same-frozen-batch offline tooling reuse — source preparation

This is an **inactive proposal**, developed separately from committed `ecb6559d`.
It changes no workflow, matrix, library, historical fixture, dependency, or gate.
The lead owns integration, producer execution, provenance review and activation.
Qualification combines modeled/source controls with bounded, actually executed
local nonnative Python owned-process lifecycle fixtures. Neither is a hosted
reuse, tooling-population, native, compiler, dependency-trust or consumer pass.

## Small, conservative scope

`gradle.yml` at that revision reruns five migration/audit/index commands and ten
offline unittest discoveries for every focused profile. Its tooling job emits
neither a source/runtime success receipt nor an artifact. **No existing job can
be grandfathered** merely because its step or workflow was green.

Only these ten existing discoveries can be reused, together and in their original
order: `scripts/audit`, `scripts/migration`, `scripts/development`, `scripts/ci`,
`scripts/native`, `scripts/dependencies`, `scripts/dependencies/yarn`,
`scripts/docs`, `tests/consumer` with `test_*.py`, then `scripts/development` with
`upstream_sync_tests.py`. The subprocess argv remains the original
`python3 -B -m unittest discover -s DIRECTORY -p PATTERN -v`.

**Every dispatch still freshly executes all five existing migration/audit/index
commands and the exact requested profile preflight.** Platform runtime capture,
raw-current production/native source admission, compilation requirements, fresh
XML, actual native methods, restoration/cleanup, independent consumers, dependency
and security/legal/API–ABI/release gates do not change. No old assertion or dated
source pin is flattened, refreshed, or skipped by this helper.

V1 allows only an identical frozen **commit**, complete source/dependency map,
workflow/tooling-action recipe, environment policy and actual hosted runtime.
Even a documentation-only commit misses. There is no changed-test inference,
ancestor projection, prefix key, cross-repository/branch/workflow reuse, dependency
cache result, or old XML restoration. The requested native profile is deliberately
not part of the *profile-independent* offline-scope signature; its plan stays fresh.

## Three helper operations

`scripts/ci/offline_tooling_reuse.py` has no network or GitHub mutation interface.
All outputs and acquired inputs are confined to `build/ci-tooling-reuse/`; outputs
must be fresh. It does not write `GITHUB_OUTPUT` or automatically bypass any job.

1. **`capture`** hashes every ordinary tracked raw file and executable mode in a
   clean checkout, recording the exact Git commit/tree and complete input map.
   Each raw file must also match its declared Git blob, even if index flags hide
   worktree changes from `git status`; no clean-status-only admission is used.
   The *entire* map also binds dependencies conservatively. The workflow bytes
   and configured/actual immutable tooling-action identities are bound separately.
   Unresolved named refs are ineligible for reuse, not prohibited from execution:
   owner policy remains Actions/all/no mandatory SHA pinning. Independently
   observed named-ref resolutions can be supplied; guessed resolutions cannot.
   Action inventory is all-or-refusal within the supported literal job/step
   layout. Plain references may have whitespace-separated inline comments; every
   such action still needs its actual immutable identity. Quoted/spaced keys,
   aliases/anchors/merges, flow action layouts, computed/block action values,
   duplicate/ambiguous step owners and unsupported indentation refuse reuse, not
   authorized ordinary Actions execution. Only explicitly recognized `run` and
   step-data literal/folded scalar owners make indented text data, never actions.
   Job data maps and step `with`/`env` maps use literal keys and scalar values;
   unsupported YAML is ineligible rather than a partially inventoried recipe.
2. **`run`** checks that signature before executing the fixed ten scopes serially
   and checks it again afterward. Each scope needs exit 0, one nonzero unittest
   summary and plain `OK`; skip/expected-failure/loader errors, missing/ambiguous
   summaries and drift cannot generate a reusable green receipt. An ordinary
   returned red scope summary stops execution and retains its same-execution
   count/log hash and bounded diagnostic tail. Setup/time/output/cleanup refusals
   propagate before that summary/log read and cannot make a success receipt;
   lead wiring must independently retain their sanitized refusal evidence, not
   invent a count or log hash. No failure is retried. Time/output bounds are cooperative,
   not kernel deadlines or containment of descendants escaping the original group.
   The direct child stays unreaped through proven same-session/group TERM and KILL
   disposal even after leader exit; a bounded wait reaps only that owned child.
   Cleanup refusals fail closed and cannot replace an earlier primary refusal.
   The receipt expressly certifies no native/consumer/readiness gate.
3. **`check`** recomputes raw-current source/runtime before and after checking one
   original digest-verified artifact ZIP plus independently acquired run, job and
   artifact metadata. Only `receipt.json` is read, without extraction. It requires
   bounded streaming decode matching the declared size, never whole-member
   unbounded inflation or an unknown compression/encryption format, as well as
   complete successful scope reports, the exact same signature and a freshly
   executed producer receipt, not a receipt re-exported after earlier reuse.

Admission requires explicit `RUNNER_ENVIRONMENT=github-hosted` before any tool
lookup; producer job labels must be exactly `["ubuntu-24.04"]`. Self-hosted,
missing/unknown environment markers and additional labels are ineligible. These
observations are conservative restrictions, not hosted attestation.

Runtime identity is actual GitHub-hosted Ubuntu24/X64 image version, OS/package
inventory hashes, Python/Git/shell/Node/Cargo/Rust versions and executable hashes,
including actual Cargo/Rust payloads behind rustup shims, and compiler configuration
hashes. Scope children use fresh empty HOME/tmp and a fixed locale/CI environment;
tokens, Python user-site/source overrides and Git global/system configuration are
not inherited. Rustup auto-install is disabled in observations and scope children;
an unavailable pinned compiler refuses rather than bootstrapping one. Observed
PATH/tool/compiler context remains input-bound. No raw
environment, private config body or tool path is exported. This is a conservative
**observed-runtime partition, not machine attestation or a supply-chain audit**;
all existing security and dependency gates remain independent.

## Practical lead integration recipe (not applied here)

Keep the existing `tooling` job and its native/consumer `needs` gates. Do not build
a new cache service or merge the many profile-specific runtime/cleanup conditionals.
After the owning workflow/source mirrors have been reviewed and important affected
controls qualified, freeze/push a new immutable development revision. New workflow
bytes need their own qualification; helper controls alone do not qualify them.

### First producer on a new frozen SHA

The tooling job must actually complete these named steps, in this order:

1. `Verify complete history, audit and current development indexes` — unchanged
   five commands, freshly executed.
2. `Record exact offline tooling signature`:

   ```sh
   python3 -B scripts/ci/offline_tooling_reuse.py capture \
     --output build/ci-tooling-reuse/current.json
   ```

3. `Offline verification-tool adversarial fixtures (not library passes)`:

   ```sh
   python3 -B scripts/ci/offline_tooling_reuse.py run \
     --signature build/ci-tooling-reuse/current.json \
     --output build/ci-tooling-reuse/receipt.json
   ```

4. `Select only the requested verification profile` — unchanged, fresh preflight
   and outputs. It must not be served from the producer's prior profile plan.
5. `Keep successful fixed offline tooling scope receipt` — upload **only** the
   fresh `receipt.json` under `offline-tooling-scopes-SIGNATURE_SHA256`, using a
   reviewed explicit upload-action reference, with error on missing files.
   Upload only when fresh execution and preceding steps succeeded; never upload
   a reused receipt as a new producer. Evidence only, no logs/packages/cache.

Use the already-reviewed checkout/explicit upload action versions where suitable;
this creates no mandatory pinning rule. Leave checkout credentials unpersisted,
read-only verification permissions, triggers and publication restrictions intact.
The producer **tooling job must be terminal SUCCESS**, with each required numbered
step successful. A native-red overall run is allowed only when that independently
observed tooling job is green; the decision records the overall failure and waives
nothing. Cancelled/nonterminal/unknown overall runs remain ineligible.

### Subsequent focused profile on that exact SHA

Run the fresh five commands, then capture `current.json` again on the actual
tooling host. Different image/tools/source means no match. A lead-supplied exact
producer run/attempt is a lookup hint, never authority. With minimum additional
**read-only** `actions: read` if needed, a reviewed acquisition step must:

- GET the exact repository's run-attempt metadata, then all pages of that attempt's
  jobs; select exactly one successful `tooling` job, not the first matching row.
- GET that immutable job ID and the explicitly selected artifact ID. Require the
  expected artifact name and exact run/attempt/job time window; artifacts span
  attempts, so a matching name alone is insufficient. Never merge attempt views.
- Download the original ZIP from the fixed
  `repos/Apdelrahman1911/nativeCmpkit/actions/artifacts/ID/zip` GET endpoint. Keep its
  original bytes and API SHA256 digest; do not extract/repack or substitute a file
  hash. Never accept user-provided arbitrary URLs, local cache files or labels as
  independent success provenance.
- Store raw acquired JSON/ZIP only under the confined build directory. Do not print
  tokens/environment or add write/OIDC/package/deployment permissions. Acquisition
  belongs to the lead/reviewed workflow: **local JSON is not authenticated by the
  offline helper**, whose decision explicitly says so.

Then check, preserving any refusal and original inputs:

```sh
python3 -B scripts/ci/offline_tooling_reuse.py check \
  --signature build/ci-tooling-reuse/current.json \
  --run build/ci-tooling-reuse/acquired/run.json \
  --job build/ci-tooling-reuse/acquired/job.json \
  --artifact build/ci-tooling-reuse/acquired/artifact.json \
  --archive build/ci-tooling-reuse/acquired/original.zip \
  --output build/ci-tooling-reuse/decision.json
```

Only an independently authenticated acquisition plus a complete eligible decision
can justify the lead's later workflow skip of **those ten scopes**. Profile preflight
must still run freshly; the current `tooling` job must still succeed before native
or consumer work. Archive the reuse decision separately and identify its original
producer; report zero new offline executions. Native fresh XML/results stay under
their existing evidence routes and are never inferred from this decision.

Cold/new-signature absence requires one genuinely fresh producer, not invented
success. A requested red/missing/cancelled/foreign/malformed producer or acquisition
failure refuses that reuse request; preserve it and stop for lead review. Do not
silently retry unchanged red tooling, downgrade the failure, select another attempt
or loop downloads. A deliberate later fresh validation/owning repair is separate.

## Source-only qualification

Run only the NEW control file, not the old full populations:

```sh
python3 -B -m unittest discover -s scripts/ci -p test_offline_tooling_reuse.py -v
```

That is a first-qualification command, not a replay instruction: during later
maintenance select only new/failed/changed/owning affected methods, and reuse
unchanged accepted source-held results without describing them as fresh runs.

Controls use modeled API/artifact/runtime identities, injected scope execution,
disposable local Git fixtures, source-only action-parser controls and bounded
actually executed local nonnative Python owned-process fixtures. Historical
red/green IPC lifecycle fixtures include independent disposal/orphan reaping and
restoration of the temporary runner subreaper state; accepted executions are not
replayed for action-parser maintenance. These controls perform zero GitHub
reads/mutations, hosted dispatches, full offline discoveries, builds or native
executions. They qualify schema/refusal/source-custody and local owned-process
behavior, not actual CI reuse or escaped-descendant containment. No measured
performance improvement, historical-job acceptance, issue closure or publishing
readiness is claimed before a separately reviewed real integration/producer/use.
