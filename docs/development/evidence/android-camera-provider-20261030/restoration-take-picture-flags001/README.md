# Exact TakePicture grant flags — owning fixture correction

Native007 remains [failed0/4](../restoration-ci007/README.md). Cached AndroidX
Activity1.13.0 bytecode creates TakePicture with **READ|WRITE flags3**; the disposable
client required0 before selecting its fixed recipient. This is a definite fixture
incompatibility. The actual caught native007 exception site remains unknown.

The two-file correction checks exact original flags3 before recipient selection.
No flags/ClipData mutation, manual grant, registry/result injection, production,
receiver/manifest or four native method-body changes. Android still performs
EXTRA_OUTPUT/ClipData migration and grants at the real Activity boundary.

- `cached-bytecode/`: read-only javap and raw AAR/class hashes; no execution or
  claim those cached bytes were independently matched to native007's dependency.
- `public-corroboration/`: source and immutable links/hashes. The AndroidX mirror
  corroborates behavior, not exact release-source identity. Apache notices retained.
- `independent-source-review/`: actual source reds, stale mutation guard refusal,
  corrected v2 patch/guards and separate equality-versus-assignment caller failure.
- `integration/`: applied patch hash; **67/67 important modeled/host methods**,
  held994 library/1071 combined inputs. These are not camera native executions.
- [One actual bounded compile](../../camera-browser-fixtures-20261031/README.md):
  camera reporter/JS/Wasm test tasks exit0/58.01s; zero native/browser tests.

Only the four still-unverified API35 restoration methods may be requested next.
Provider API23/API35/host22 acceptance is not replayed. #13 remains open pending
all original criteria and source/results/ownership review; release/security gates stay.
