## Verified fix — direct closure after the important Android alias matrix

All **three original PERM-002 acceptance checks** pass at immutable **35f04ca404fc575927dceb676dba1cd6b84cfc06**, [run40620477866](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40620477866): **47/47 actual Android-host executions from43 authored methods**, seven fresh XML, zero failures/errors/skips. Two new methods each run on **SDK28,32,33**: six fresh cold-order/SDK executions, not six separately authored tests. Only the permissions core host suite runs; Gallery production is a test-only dependency.

1. **Actual public ReadStorage and Gallery singleton initializers** execute in each order, in distinct Robolectric instrumentation sandboxes. Fresh registry assertions run before any builtin access; after the first initialization the second is still absent. This is not repeatedly reading already-initialized objects or injecting substitute builtin mappings. Gallery-only requests return Gallery, even when the global legacy reverse lookup sees ReadStorage first.
2. Requests for **both aliases** keep two distinct member states and both original callback object identities. A single native READ_EXTERNAL_STORAGE request is deduplicated, then its granted and denied deliveries refresh **both states before the callback**. The result contains only requested logical keys.
3. All three SDKs run both orders. SDK33 builtin storage aliases explicitly report **NotRequired** with no native request. Custom camera aliases run granted/denied native ActivityResult paths on every SDK; an earlier globally registered unrequested alias never appears. Duplicate requested objects normalize without losing distinct aliases.

Root repair: snapshot each request's logical identities/native mappings, deduplicate native strings and calculate results for every requested logical alias. Production callbacks/plans never use the global first-match reverse lookup. Existing public APIs/packages remain.

Actual host integration uses public Compose factories, Android ActivityResult contracts/createIntent/dispatchResult and owning lifecycle cleanup. **Robolectric grants and OS-dialog interception are controlled host evidence, not physical-device permission UI, manifest authority or process recreation.** These unrelated device/minimum-platform and release gates remain open under their owning findings; this closes the request-scoped alias defect and its original SDK/identity criteria.

Review verifies744 exact own-Git inputs, before/after maps,43 authored identities plus all six SDK variants, every XML/artifact digest and actual command/runtime correspondence. Official Robolectric4.16.1 source explains configuration-keyed sandbox selection and the last selected SDK33's unmarked testcase name. Required important tests → review → **direct closure now** → archive afterward. Original issue body/title/labels and upstream PR263/commit references remain intact.

Evidence: `docs/development/evidence/github-actions/40620477866/`. No unrelated successful module/host replay, artifact/API-ABI/legal/dependency/security/release waiver or publishing/deployment.

<!-- nativecmpkit:direct-acceptance:PERM-002:35f04ca4 -->
