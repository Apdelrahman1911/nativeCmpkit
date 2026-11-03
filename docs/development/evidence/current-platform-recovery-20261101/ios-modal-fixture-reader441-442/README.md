# Shared Worker fixture-reader recovery — 2026-11-03

## Original requests remain failed

At `2d0af6e92fe0aba099afb8a199ff9351cc6142c3`:

| Request | Result | Shared CI interval |
| --- | --- | --- |
| [41573898265](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41573898265), independent XCTest startup | FAILED before profile/platform | 2,517 methods /141.769s |
| [41573910311](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41573910311), Worker/memory3 | FAILED before profile/platform | 2,517 methods /139.232s |

Each original reports **seven records: three failures and four errors**, including
one CI224 class-setup refusal. All platform jobs were skipped. **Zero library
Gradle, Apple link, Swift/XCTest, native methods, XML or artifacts** occurred.
The1,253 own-Git frozen inputs are not uploaded actual platform-input receipts.
Original logs were acquired once, hashed/member-verified and reviewed before
repair. They remain private; sanitized metadata/reviews are archived here.

## Confirmed shared tooling root cause and fix

The preceding host-comparison repair correctly adapted the live alert source
control to the pooled Worker bridge, but changed that control's complete source
hash. CI224 and CI245 historical readers still require its original whole image
(`6de5af63…`), not the adapted live image (`972d9d91…`). Their setup, round-trip,
body-preservation and overlay checks failed; the Desktop historical reader failed
at that same setup boundary. These are tooling failures, not native failures.

The new `scripts/ci/ios_modal_fixture_reader_projection.py` and exact
`fixtures/ios-modal-fixture-reader-inverse.json` bind **one path/one fragment**.
They reconstruct only the original host-comparison control after complete current
admission, with both whole/fragment hashes, unique inverse/forward sites and exact
round-trip. The existing Worker history boundary composes it for every reader.
The live adapted control stays intact; no historical hash, old test body,
production source, native predicate, driver, workflow, dependency or API changes.
Historical preimage idempotence is distinct from strict current admission.

## Important affected/new tests and review

Only **six failed methods +three new regressions** execute: **9/9 once**, zero
failure/error records, wrapper1.557634s. CI224's owning setup/teardown qualify
without replaying its five accepted method bodies. **1,256 inputs remain held**.
The28 separate passive source/results checks preserve the existing six23-fragment
Worker and AWT manifests and exact four Kotlin compiler sources. No compiler or
accepted control/native population is replayed.

The first passive review incorrectly indexed workflow YAML through the library
snapshot, which excludes it, and refused with `KeyError`. Its receipt remains;
the corrected review checks workflow bytes separately against the frozen Git
blob. This is bookkeeping recovery, not a native or regression failure.

`local/inputs.json` is the single copy of the byte-identical before/after maps;
the original separate captures remain held privately. `ARCHIVE.json` binds the
public evidence, not the later commit that stores it.

## Next finite verification and restrictions

Freeze/push development only; after fresh capacity reconciliation request only
unexecuted memory3 and independent startup-only, each one reservation. Real
library XCTest iPhone7 waits for accepted startup; iPad7 follows later. Previously
accepted modal9 host pairs/repeated-disposal/state-replacement/native subsets
remain excluded. Original captured-owner retention and startup causes remain
unverified; the Worker hypothesis is not an established native retention chain.

No issue comment/closure: last verified **98 closed /74 open /172 total**;
22 implemented/41 partial/96 verified/five unresolved. SOLO, serial local/8GiB
reserve/max2 combined hosted reservations **including queued**. Read-only Actions,
all actions allowed/no mandatory SHA pinning, unchanged publishing/Pages/main/
history/legal/security/consumer/API–ABI/release-readiness gates. No publication.
