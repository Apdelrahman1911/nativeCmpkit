# Camera provider source / host / compilation evidence

Modified development checkout based on c5180776d711ceb4d4d704f8e0665a046ce00160;
not an immutable release candidate. All before/after source maps match within
their own executions. New device fixtures are additive after the accepted host
result; they are not silently represented as having run with the host suite.

- `host-red001`: **3 actual host executions/three failures**, exit1/36.01s.
  API23 configured URI is `file`, while missing/wrong provider setup launches and
  lacks a configuration result. Red source and existing regression behavior are
  preserved in the failed XML; no source fix claimed at that point.
- `host-green001`: **compiler failure/zero executions**, exit1/9.0s.
  Two fixture calls incorrectly supplied generics to non-generic Robolectric
  `getApplication()`. Only those two type arguments were removed. Stale red XML
  was not used as this attempt's output; the failed attempt remains failed.
- `host-green002`: **22/22 actual host cases/four fresh XML**, exit0/19.01s;
  includes all eight new provider regressions and existing lifecycle/reentrant
  camera checks. Real XML/provider/resolver/cache bytes; external activity/results
  driven. Not native different-UID grants, hardware or OS process death.
- `native-compile001`: reporter APK exit0/41.01s, **zero native executions**.
- `receiver-compile001`: independent native receiver APK exit0/11.0s,
  **zero native executions**. 983 library/1060 combined inputs held throughout.

179 important synthetic plan/ownership/archive/workflow checks plus907 disjoint
remaining scripts/ci methods pass (1086 distinct, no accepted179 replay);
Actionlint also passes, neither is an Android/library result. Earlier accepted
unrelated geo/sharing/native/portable outcomes were not replayed. API23/API35
native request/results and original #78/#13 criteria are still pending.

Archive includes selected JSON and console/property/hostname-sanitized XML only;
`XML-archives.json` binds original/archive bytes. No private logs/ZIPs/APKs,
credentials/signing inputs/environment or fabricated native outcomes. Baseline
finding/archive/history and publishing/security restrictions remain untouched.

Actual APK-byte/certificate/compiled-manifest inspection verifies min23/target37,
matching signatures and signature-protected receiver endpoints. The first private
reader failed by expecting literal `signature`; compiled XML is exact integer
`0x2` (signature). Only the reader interpretation was repaired; source/APKs were
not rebuilt and no native UID/grant outcome is inferred.
