# Inert consumer material v2 — source review and owning recovery

This archive documents the **separate inert schema-v2 tooling** now integrated as
three new files. It does not adopt a real material catalog, add a v1 fallback,
change publication notices or approve any release. The lead owns repository
integration and Git/GitHub changes. Archive preparation performed only selected
source readback, receipt transformation and privacy inspection; **no new tests**.

## Source identity and applicability

| Selected integrated file | SHA256 |
| --- | --- |
| `tests/consumer/native_license_material_v2.py` | `ba1b20bc0cb9d18c6d7092f6c22df93ebcea7d97aac9ef60c5a402e7466d29c2` |
| `tests/consumer/native_license_material_v2.schema.json` | `f87235bc12f0081909757e383d20638fb513dffc52b92cd51a510629cfd2fc34` |
| `tests/consumer/test_native_license_material_v2.py` | `0281403a39a55bc254ab2ffcf5712cc10c7d64b541d2a4ee2d08383d935b4a67` |

Original unsafe proposal adapter: `3abfaabb0e977c9f709c87e92f488f0cf345d9bc87606ab4c2077504dc079239`.
Selected combined three-new-file patch: `230c122a39165cc3f84c25cd4217914a0757611fdcd7498dbb3f4d15940a8a42`.
These are source/patch hashes, **not** catalog approvals or publisher signatures.

`source-applicability.json` records the exact selected-file readback, ten unchanged
v1/notice/native-lock/checkout inputs and the saved original/repaired AST comparison.
Only `PendingMaterial` and `load_material` change; `_freeze` and `_plain` are added.
The schema and raw-object/tree/reader, index/lock, inheritance, relationship,
obligation, archive-inspection and report algorithms remain unchanged. This is a
selected-input claim, not a whole-worktree or commit claim. Earlier author results
retain their historical source and are not promoted to a new aggregate acceptance.

## Confirmed proposal-only findings and repairs

### CV2-001 — Medium: mutable held proof and emitted-origin aliasing

Original `native_license_material_v2.py:215-229,352-355` held caller dictionaries
inside a frozen dataclass and returned nested report aliases. Changing an exported
`text_origin.revision` changed the inspector's own reference, so forged-origin
inspection incorrectly passed. Constructor and direct-nesting controls also
reproduced mutable manifest, payload and observation references.

Current `:217-254` owns recursive read-only mapping/tuple snapshots of validated
JSON/immutable bytes and returns detached plain JSON. The inspector at `:379-382`
keeps its original comparison algorithm but now has an independent held reference.
Required controls: defensive snapshots, direct mutation refusal, serializable
export and forged-origin rejection. Synthetic owning tests are at
`test_native_license_material_v2.py:51-82`.

Risk/compatibility: intentionally read-only internals of this newly proposed Python
object; unchanged ordinary dict/list export and no Kotlin/Rust/public library API
change. Constructors do not validate provenance. No protection against arbitrary
malicious in-process code, v1/staging/notice/legal/publishing bypass or released
library exploit was demonstrated.

### CV2-002 — Low: malformed crate paths escape the owned error contract

Original `native_license_material_v2.py:250-254` keyed crate proofs before checking
path type/canonical form. List/dict paths raised raw `TypeError`; other malformed
shapes caused premature proof reads before eventual refusal. Current `:275-281`
checks canonical membership in the exact three-proof-name set before reads/keys,
retaining cardinality, full-set and duplicate refusal. No exception swallowing.

Required six-shape refusal/pre-read control is at
`test_native_license_material_v2.py:84-108`: list, dict, null, integer, traversal
and noncanonical paths. The fake bounded in-memory reader uses a selected format
name, nonexistent version and zero checksum only to reach that boundary. It has
no registry/provenance authenticity, archive, network or real material fixture.

`findings.json` contains priorities, exact locations, cause, impact, smallest fix,
compatibility risks, required tests and evidence references. These are two owning
proposal defects repaired before inert-tooling adoption, not additional GitHub
findings or completed release-gate issues.

## Previously executed results, reused without replay

| Distinct historical batch | Original proposal | Repaired exact adapter |
| --- | --- | --- |
| Three new private authentic-fixture owning methods | exit1; 8 subfailures / 2 suberrors; unittest elapsed 0.264 s | exit0; 3/3; unittest elapsed 0.060 s |
| Three new synthetic-only repository methods | exit1; 12 subfailures / 2 suberrors; whole-process wall 0.142084 s | exit0; 3/3; whole-process wall 0.135991 s |

Private-fixture wall time was **not independently measured**. The synthetic
whole-process wall measurements were independent; its unittest-reported elapsed
values are respectively 0.009 s and 0.003 s. Each batch's unchanged method bodies
ran on its exact original/repaired adapter source. Original reds remain failures.
The batches are distinct; there is **no fresh 6/6, 12/12 or 15/15 aggregate claim**.
Neither accepted private-fixture nor author suites/index-shape cases were replayed.

- `private-fixture-*-summary.json`: counts, source hashes and limitations only;
  raw private fixture logs/material are deliberately excluded.
- `synthetic-*-result.json` / `synthetic-*-output.log`: exact already sanitized,
  synthetic-only receipts/logs; prior private prefixes were replaced by repository
  source paths. Sanitization does not change failure counts/assertions.
- All these are Python tooling controls, not native/library/packaged-consumer,
  legal/provenance, integration or release-readiness verification.

Focused maintainer command (documented only; not rerun during integration/archive):

```sh
python3 -B -m unittest discover -s tests/consumer -p test_native_license_material_v2.py -v
```

## Maintainer execution boundaries

| Current source | Contract and limitation |
| --- | --- |
| `Reader:76-95`; existing `regular_bytes` | Bounded regular-byte/no-follow reads and aggregate bound; caller must supply explicitly public roots. Not an OS filesystem sandbox. |
| `origin:117-172` | Raw Git object/tree/blob correspondence binds distinct origins; object hashes do not authenticate a publisher or verify all ancestry. |
| `resolve_manifests:175-198`; `relationship:201-214` | Exact original/normalized/workspace resolution; saved API ancestry is only reported, not full-history verification. |
| `load_material:257-326` | Original source and later text remain separate; no license option is selected and pending obligations cannot become true. |
| `load_material_set:329-370` | Requires an explicitly independently reviewed index SHA256 and exact current input bytes/finite identities from both selected Cargo locks. Never silently regenerate/adopt catalog or dependency graph. |
| `PendingMaterial:235-254` | Owns validated JSON/byte snapshots and exports detached JSON; direct construction/synthetic tests are not provenance validation. |
| `verify_archive:373-376` | Reuses unchanged archive checksum/path/member correspondence. **Not** notice or legal approval, collector fallback or staging permission. |
| `inspect_evidence:379-382` | Compares report/payloads against the independently held reference, not just producer self-hashes. |
| `pending_report:385-389`; `OBLIGATIONS:34-37` | Retains gaps, null license choice and false obligation/completeness/staging/publisher flags. |

## Original issue criteria and remaining gates

`original-issue-criteria.json` preserves the exact archived acceptance sections,
body hashes and public links for open #3/BUILD-006, #40/BUILD-007 and #103/NAV-018.
None is satisfied or closed by three Python owning controls. The owner's waiver
of **mandatory action SHA pinning remains in effect**; historical issue text is not
rewritten and does not reinstate that requirement.

Remaining separate obligations include exact-release text applicability,
contributor/derived-source attribution, SDK/source/distribution obligations,
independently trusted publisher provenance, artifact notices, minimum/platform and
packaged consumers, full-coordinate/native verification, ABI and dependency
security. Original failed collectors/staging and runtime results remain unchanged.
Do not run known-failing full staging to rediscover an unchanged legal gate.
A later notice-policy/collector integration requires independent evidence-based
obligation dispositions and fresh affected actual artifact/consumer verification.
No publication, release, Pages, main/history rewrite or issue closure follows here.

## Archive policy

This archive contains authored analysis, source hashes, public original criteria
and synthetic-only diagnostics. It excludes real catalog/manifests, raw Git
objects, third-party license text, SDK documents, research comments, fixture logs,
credentials and private filesystem paths. `privacy-source-check.json` describes
source-only checks and explicit non-executions. `ARCHIVE_MANIFEST.json` binds all
payload files; `SHA256SUMS` additionally binds the manifest. Neither lists itself.
