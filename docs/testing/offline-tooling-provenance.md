# Explicit offline producer and authenticated acquisition — NativeCmpKit

This is a **source-only preparation stage**, not accepted hosted reuse, a measured
CI saving, supply-chain attestation or release readiness. The unchanged accepted
`offline_tooling_reuse.py` and its31 existing control bodies remain exact. The new
thin driver is `scripts/ci/offline_tooling_provenance.py`; its NEW8 owning controls
plus two exact-origin controls use injected HTTP responses, modeled captures/scope
outcomes and disposable files. Two startup controls additionally exercise real
temporary-source hash/ownership refusals through in-process CLI/import loading.
They do not run real offline populations, network, processes, compilers, native
functionality, consumer integrations or GitHub mutations.

## Deliberate modes and independent gates

The workflow mode must be an explicitly validated **string** input, default `off`,
allowing exactly `off`, `produce`, `reuse`. Do not add a second YAML `options:` list:
the existing secure-profile reader assumes its single profile declaration. The
lead owns all workflow, index/mirror and routing integration and qualification.

- **off** runs the original fixed ten offline discoveries once (stopping on an
  actual red outcome), using the accepted scrubbed environment and owned Linux
  lifecycle runner. It does not capture eligibility, request authentication or
  create `receipt.json`. Ordinary named/unpinned Actions stay owner-authorized:
  **no mandatory SHA pinning**. Unresolved immutable identities restrict explicit
  produce/reuse only, never the ordinary off verification policy.
- **produce** accepts an optional freshly owned `--recorded-signature` from the
  genuine *Record exact offline tooling signature* step. The unchanged runner
  freshly captures before and after executing its exact ten scopes once. Do not
  add duplicate driver captures at those boundaries. Without a recorded signature,
  one driver capture establishes the expected signature, then those same two
  runner captures occur. Only a genuinely passed new producer gets an exact
  original-schema `receipt.json`; returned red preserves `scope-result.json`
  instead. A raised failure cannot invent results or certify a receipt.
- **reuse** requires the exact positive run, attempt, job and artifact IDs below,
  never latest/first/search/cache or another attempt. It freshly captures before
  any network, compares the recorded expectation if provided, performs once-only
  authenticated acquisition and unchanged consistency check, then freshly captures
  again. Only full agreement accepts zero new offline scope executions. It never
  writes a producer `receipt.json`, re-exports a successful producer or silently
  runs fresh tooling when requested reuse refuses.

Every invocation retains **five fresh index checks**: `verify_migration.py`,
`validate_audit.py`, `source_inventory.py --check`, `validate_resolutions.py --check`
and `generate_icon_catalogues.py --check`. The exact **requested profile preflight**
remains fresh. Native/consumer `needs: tooling`, source/runtime maps, XML, memory/
resource cleanup, actual platform behavior and API–ABI/dependency/legal/security/
release-readiness gates remain separate; none is an offline fixture pass.
**No publication**, package upload, release, deployment, Pages, main/history change
or waived native failure is authorized by this driver.

## CLI contract (lead integration only)

```sh
# Ordinary owner-authorized verification; no eligibility capture or token.
python3 -B scripts/ci/offline_tooling_provenance.py \
  --mode off --output-dir build/ci-tooling-reuse/off-current

# Genuine earlier record step: output must be new and confined.
python3 -B scripts/ci/offline_tooling_reuse.py capture \
  --output build/ci-tooling-reuse/record-current/signature.json

# Explicit producer: unchanged runner performs its fresh before/after captures.
python3 -B scripts/ci/offline_tooling_provenance.py \
  --mode produce --recorded-signature build/ci-tooling-reuse/record-current/signature.json \
  --output-dir build/ci-tooling-reuse/produce-current

# A separate same-SHA reuse invocation; selectors are the reviewed original IDs.
# The owner/lead supplies its ephemeral read credential through the named env only.
python3 -B scripts/ci/offline_tooling_provenance.py \
  --mode reuse --recorded-signature build/ci-tooling-reuse/record-current/signature.json \
  --producer-run-id "$PRODUCER_RUN_ID" --producer-attempt "$PRODUCER_ATTEMPT" \
  --producer-job-id "$PRODUCER_JOB_ID" --producer-artifact-id "$PRODUCER_ARTIFACT_ID" \
  --output-dir build/ci-tooling-reuse/reuse-current
```

The four selectors are canonical decimal strings in1..2^53; booleans, leading
zeros, signs, floating-point/exponents, foreign keys and URLs refuse. No API JSON,
archive, locally supplied authenticated decision or producer envelope is a CLI
input. Optional `--resolved-actions` is the accepted helper's confined JSON input
for **independently observed actual executor resolutions**, not guessed tags,
`ls-remote` or ambiguous commit lookups. The first smoke should use the existing
voluntarily exact checkout/upload references. Missing actual resolution stops an
explicit produce/reuse; it never changes owner-authorized off policy.

Only the combined tooling job needs additional **`actions: read`**, alongside
existing **`contents: read`**. No write, OIDC, packages or deployment scopes.
`NATIVECMPKIT_ACTIONS_READ_TOKEN` is an explicit ephemeral reuse-step environment
variable, never an argument, file, hash or printed value. After fresh mode/path/
recorded-input ownership checks, the driver takes and removes it **before** its
first live capture: the unchanged capture observes Git/tool versions through
subprocesses. Network/client construction still waits for that validated current
signature. A nonempty explicit read-token variable in produce refuses before any
capture instead of forwarding it. Scope children always use the accepted fixed
credential-free environment. Do not pass this credential to record, off, produce,
profile, native or consumer steps.

## Fixed authenticated acquisition and once-only custody

The standard-library `http.client.HTTPSConnection` client connects directly to
`api.github.com:443`, with platform certificate verification and hostname checking.
It does not use ambient proxies, a cache, automatic redirects or retries. Its
fixed endpoint generator permits only GETs under
`https://api.github.com/repos/Apdelrahman1911/nativeCmpkit/actions/`:

1. Exact `runs/<run>/attempts/<attempt>`.
2. Every100-item page of that attempt's jobs (up to100 pages/10,000 jobs), with
   strict constant totals, page cardinality, unique IDs, attempt/source/terminal
   consistency. Exactly one successful named tooling job must be the selected ID.
3. Exact `jobs/<job>`, compared with the entire governing paginated view, including
   numbered named successful producer steps, labels and timestamps. Other platform
   jobs may be failed/skipped; this cannot turn them into native acceptance.
4. Exact `artifacts/<artifact>`. Signature name, source/repository/run, original
   SHA256 digest, size, unexpired status and the completed job-attempt window must
   pass **before** ZIP download. Native/package/legacy artifacts refuse.
5. Exact `artifacts/<artifact>/zip` once. A direct authenticated200 is bounded and
   retained. A302 can mint only this client's once-only signed-storage capability.
   A caller cannot issue a storage request without that authenticated response.
6. Original bytes/metadata go to the unchanged checker; raw-current recapture must
   hold. The checker's `authenticated_transport_by_helper=false` stays unchanged.
   The separate driver decision means completed acquisition consistency only, not
   trust in a caller-supplied JSON file or machine attestation.

**Historical preparation gate: `REVIEWED_STORAGE_HOSTS` was EMPTY.** That exact
source stage and its accepted controls are preserved; it refused all signed
redirects, not a successful GitHub download. The lead then supplied original
header-only observation649 (2026-11-04, SHA256
`0807b1585c159821b88b2b4ee27b88a2b1e03fabdea4ea9f97fc94d9f0326614`):
authenticated API302 for run41776849543/artifact13299667834, HTTPS host
`productionresultssa0.blob.core.windows.net`, first path segment `actions-results`,
no port/userinfo and an opaque signed query. The redirect was **not followed**;
zero archive body bytes were acquired. Its native artifact name
`library-evidence-ios-iphone` is **origin evidence only**, never an eligible
offline producer or native/reuse acceptance.

The lead authorized only that exact built-in host and literal `/actions-results/`
route. Production now permits those two source-reviewed literals; unknown/new
hosts, wildcard/account-pattern matches and environment overrides refuse. The
remaining blob path must be nonempty, unescaped and canonical, without empty,
dot/traversal or backslash components; no percent-decoding/normalization aliases.
An unseen escaped path or new storage shard needs separate original source review,
not a guessed allowance. The reserved `.invalid` model still is **not** a reviewed
public origin. New origin controls exercise the built-in literal through injected
responses only; neither they nor the header observation are genuine tooling
producer/ZIP/reuse verification. All source/window/digest/size checks still precede
the ZIP request. A fresh producer artifact may use a different host and refuse.

Never infer a wildcard Azure/CDN allowlist from logs, weaken this guard or forward
the token to storage. The signed URL/query stays in memory and is never written;
storage receives no Authorization or GitHub API version header. A storage redirect,
unknown host, non-HTTPS target, userinfo, port, fragment or noncanonical route
refuses without another request. Even an approved caller URL cannot mint a storage
capability: only this client's exact authenticated API302 can, once.

Bounds:16MiB per JSON,32MiB original ZIP,64MiB total acquired bodies,100 job pages,
180s total acquisition and at most30s per socket operation (with remaining-time
checks). Content length/encoding/duplicate governing headers and incomplete bytes
refuse. Actual hosted timing/schema/origin behavior is still unverified.

A fresh single child of ignored `build/ci-tooling-reuse/` is exclusively claimed;
symlinks, stale children, noncanonical/escaping names, hard-linked files and
changed file identities refuse. Direct openat/exclusive0600 writes in a0700 child
retain exact raw JSON and original ZIP: **no extraction, repack, substitute digest,
package upload or XML interpretation**. Reading those same held local bytes is
not another original API download. These are cooperative ownership/displacement
checks, not an adversarial same-user process sandbox.

Each logical request gets a fresh sanitized start journal **before** sending,
and one completion-attempt record. Duplicate logical requests refuse. The ledger
counts original API requests and signed-storage hops separately. Complete raw
response witnesses retain observed bytes/hash; partial stored prefixes remain
explicitly `complete=false`, with their actual stored prefix size/hash. Unread/
unavailable bodies are marked unavailable, not guessed empty/successful. Error
status bodies/headers are not exported. There is no retry or partial-success reuse.

## Outputs and sanitized raised refusal

Predetermined complete outputs: `signature.json`; producer `receipt.json` or red
`scope-result.json`, `producer-result.json`; off `off-result.json`; reuse
`signature-after.json`, `reuse-decision.json`; sanitized request start/results and
`acquisition-summary.json`. Raw acquired `run.json`, `jobs-page-*.json`, `job.json`,
`artifact.json`, `archive.zip` remain ignored local original evidence, not uploads.

The lead's producer upload step must upload **only** a new successful
`produce-current/receipt.json` under `offline-tooling-scopes-<signature_sha256>`;
never a wildcard directory, reuse decision, raw JSON/ZIP, package or old artifact.
The recorded named required step order stays exact. Reuse has no producer upload.
Any sanitized diagnostic retention is separately enumerated/read-only; never
publish headers, signed URLs, secrets, native XML or terminal transcripts.

The same sanitized boundary covers CLI and import-time source initialization.
Both exact public owner paths, their ordinary unshared file hashes and recognized
code objects must be observed before either owner is registered. A missing owner,
hash refusal or empty code witness leaves **no partial accepted registration**,
emits only canonical `source-observation` refusal stderr and exits nonzero; import
raises `SystemExit` without exporting the original exception chain. Successful
imports retain both witnesses. Initialization has not entered main, drained a
token, captured source/runtime or claimed an output directory: public-source frames
and signature observations remain unavailable rather than guessed. Normal CLI
execution keeps its existing `driver-main` boundary and exit behavior.

The narrow driver boundary preserves the actual first exception/exit. A fresh
`refusal.json` contains known mode/stage/operation, validated requested IDs and
signature hashes only actually observed. Approved public source frames come from
that **same original traceback**, exact recognized code objects and held loaded
source hashes: relative owner/function/line/instruction offset only. No exception
messages, frame locals, raw chains/notes, private absolute paths, headers, queries
or token/credential hashes. Original-helper secondary-note presence may be noted;
its unknown detail remains unavailable, never parsed into a guessed cleanup cause.
Known separately caught storage/HTTPS/driver cleanup refusals are sanitized
without replacing the primary. A late disposal failure may be reported in sanitized
stderr if a stored capsule cannot safely be augmented without overwriting it.
If fresh output ownership/storage fails, stderr only; never overwrite evidence,
choose another path, retry the capsule or claim it was stored.

Ordinary returned-red scope receipts preserve their genuine result/count/log
observations through the unchanged helper. Raised setup/time/output/cleanup can
have **no observed scope result**: `availability=unavailable`, not zero tests,
made-up log hashes or cleanup success. A stored provisional result is not job/
artifact acceptance; terminal successful workflow/job and all later gates remain
necessary. Requested refusal never switches to another producer or fresh scopes.

## NEW important controls, not a full-population claim

`scripts/ci/test_offline_tooling_provenance.py` retains eight owning groups:
P1 mode/ID/fresh ownership preflight; P2 fixed fresh producer vs zero-scope reuse;
P3 once-only pages/sole direct job; P4 TLS/origin/token/redirect/proxy/bounds;
P5 complete/partial original bytes and artifact class; P6 sanitized original/secondary
raised failure; P7 before/after source/runtime/action/recipe invalidation;
P8 ordinary unpinned owner policy and independent gates. Two new owning origin
groups add O1 exact source-observed host/literal route/alias/environment refusal
and O2 authenticated-response-minted once-only token-free capability with unknown
shard refusal. S1/S2 cover genuine temporary-source hash refusals before main,
token/network work for CLI/import, complete successful registration, a foreign
helper owner path, empty registration on failure and sanitized nonzero import
exit without a private traceback. The observer/hash guards are not mocked.
Imports reuse accepted fixture factories, not their31 TestCase
executions. Real socket/process calls are
trapped; HTTPS/captures/scope outcomes are models. No model is reported as real
API/native/consumer behavior or measured saved executions/time.

Lead qualification uses only these NEW important controls and genuine failed/
changed owners, retains the actual first red (if any), then recovers only affected
methods. No nonexistent-import/placeholder failure is behavioral evidence.
Unchanged accepted helper/control/workflow/history/process/native results are
reused as historical evidence, never renamed fresh runs.

## Smallest hosted qualification (lead only, not executed here)

After exact source/workflow/mirror integration, independent review of the narrow
observed storage contract and a frozen development SHA: dispatch tooling/produce
once, review its
terminal original job, ten real scope results/cleanup/runtime/input maps and sole
new receipt artifact. At the same SHA/runtime dispatch tooling/reuse once with its
four exact IDs; review authenticated original API/ZIP bytes and once-only ledger,
fresh before/after maps, accepted decision/zero new offline scopes, actual five
fresh index checks and requested profile preflight. Only then consider the same
producer for focused platform profiles; native/consumer steps still run freshly.
Do not grandfather old green jobs or redispatch already accepted native subsets.

Any commit (including docs), tracked byte/mode/tree, tool/OS/image, action executor
identity, dependency/workflow/recipe/config drift invalidates reuse conservatively.
Actual tooling artifact origin/body/schema, runtime/REST behavior, real producer/
reuse, CI savings and full release/security readiness remain **unverified** in
this source-only preparation. Header-only origin evidence is not such acceptance.
