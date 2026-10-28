## Verified fix — close directly after important-test review

All **three original NATIVE-014 acceptance criteria** pass at immutable **c39d320c8f82d67e7671eb38cad19a4068f919aa**, [run40611192346](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40611192346): **8/8 real desktop cookie methods**, zero failures/errors/skips, including three new regression methods.

- Delayed reads retain the exact original absolute expiry.
- Copying a returned cookie to a second, independent real JDK store retains exactly the same expiry. Removing the source store does not alter the destination.
- Session/null, already-past/epoch, a genuinely elapsed one-millisecond-past-second-boundary deadline, supported years0001–9999 and invalid/Long overflow timestamps pass. Invalid inputs fail before mutating an existing cookie.

The owning repair retains original expiry metadata by native-cookie identity instead of inventing `now + maxAge`; reads filter elapsed exact deadlines. Foreign-store metadata is explicitly unknown. Input validation precedes mutation. Public cookie shape/namespaces remain compatible; native Max-Age still has whole-second precision, which is not misrepresented as API metadata.

Reviewed source, **all741 exact own-Git input blobs**, unchanged before/after maps, every XML/artifact hash, fresh testcase identities, command and SDK/runtime correspondence. Important tests → review → **direct closure now** → archive/index afterward.

**The whole workflow remains failed:39/40 executions,7 XML.** The independent JavaFX native-history test observed stale pageTitle (`A` instead of `C`); it does not use CookieManager and does not invalidate any cookie criterion. Its failure is retained and will be investigated, not hidden or called green. No unrelated successful suites were rerun.

This closure does **not** certify JavaFX authentication/global-cookie stores/native HTTP-header parity, other cookie/threading findings, physical/minimum devices, native sanitizers, ABI, dependency/legal/full consumers or release readiness. Those wider issues/gates remain open. No packages, releases or deployments published.

Evidence: `docs/development/evidence/github-actions/40611192346/`. Original issue body/title/labels and historical failures preserved.

<!-- nativecmpkit:direct-acceptance:NATIVE-014:c39d320c -->
