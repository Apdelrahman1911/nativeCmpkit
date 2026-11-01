# Storage compatibility actual001 — original failure preserved

[Run 41265416289](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41265416289)
completed **FAILED** at `1c74cb9a7951610fdb8098869f9daadd918b8a39` (attempt 1).
**Six selected routes; two failed child attempts, four refused before attempt;
ZERO native executions, ZERO original library receipts, ZERO XML, ZERO accepted rows.**
No issue closure or native/consumer/API-ABI/security/release acceptance is inferred.

## Actual boundaries

* API28/legacy28/target28 genuinely booted API28/Android9/x86_64, SELinux Enforcing.
  Helper assembly exit0/260.08s produced a 9,329,207-byte APK with SHA256
  `25098fac7341387f044a4fbc8f24face212b67ad5705948846468dc19f360dc9`.
  Child exit1/337.1s and `ValueError` identify exactly
  `android_storage_probe.py:116 validate_support_component`, the explicit unknown
  merged-component refusal. The rejected tag/name/attribute shape was **not
  captured**. Signer/installed-UID/reporter compilation/native dispatch were not
  reached. Do not infer a particular AndroidX/debug component or causal dependency.
* API29/legacyTarget28/target28 child exit2/1.0s, outer `FileNotFoundError`, retains
  `android_device_tests.py:95 require_host`. The fixed `/dev/kvm` character-device
  or read/write admission failed; **which predicate and why are unknown**.
  No controller/plan/preflight artifacts exist for this attempt. This is not a
  diagnosis of the older API34 failure. Four later routes were refused.

API28 cleanup preserved `prepare_status=failed`: no install attempt or foreign
app mutation, owned-recipient removal witness, graceful owned emulator exit0,
transport absence, and exact owned `avd`/`android-user` directory reclamation.
That cleanup is **not** native acceptance; API29 cleanup was uncertified.
All six original selectors and absence/result boundaries are in
[route-review.json](route-review.json).

## Integrity and original/public separation

Artifact `13066963000` is 230,944 bytes, SHA256
`f39b64ef0add0a8ec5b3081221ec0bb3c7ab43f5ac8cf298e534241f57cd2398`, equal to GitHub's digest. Its 24 original JSON files total
809,775 uncompressed bytes; ZIP CRC, safe regular entry names, extracted bytes
and original hashes were checked. Every original JSON was strictly parsed.
[ORIGINAL_PUBLIC_SHA256.json](ORIGINAL_PUBLIC_SHA256.json) records exact original
and public hashes/byte counts. **23 public copies are original-byte-identical**;
one API28 plan copy replaces only two known private SDK executable strings with
`<SDK>` placeholders. See [sanitization.json](sanitization.json); that copy is
not original-byte-identical and not an executable reproduction recipe.
Raw job logs, terminal transcripts, APKs, keystores, private source command fields
and unrelated artifacts are not copied. Public bounded metadata/hash facts alone
are retained. Original scripts/ci tooling passed1603 methods/73.643s, **not native**;
other tooling groups are not summed as storage/native coverage.

Four uploaded actual maps are **1071-library maps**, all equal to exact frozen
Git inputs and held before/after. There is **no uploaded actual combined map**.
The root recovery maps1071/1148 are source-only, clearly labeled in `freeze/`.
1167 previously collected Git-bound regular source files were rehashed unchanged;
21 shared storage contract inputs match all six plans and the API28 receipt.
Source/criteria review and exact immutable Git links are in `review/`. The #118
literal original criteria remain open. Earlier API33/API34 causes remain unknown;
no media, accepted suite or historical generated-manifest replay was performed.

This is an add-only **private delivery candidate**, not a live repository/GitHub
publication. Destination absence is unchecked; integration and any immutable
verification request remain the lead's responsibility. No rebuild, install,
SDK/device/native operation, dispatch or Git/GitHub mutation occurred during review.
