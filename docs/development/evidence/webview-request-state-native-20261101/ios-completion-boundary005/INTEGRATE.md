# Exact integration preconditions

1. Wait for the current root-owned Linux compiler to finish. This proposal never
   edits the shared repository and does not authorize dispatch.
2. Verify the archive seal and payload file identities/modes.
3. Check each of the two existing paths against `source-identities-before.json`;
   each exact fragment preimage must occur once. Require the new guard path absent.
4. Apply exactly `fragments.json`; install the new guard postimage (0644). Read
   back all three postimages against `source-identities-after.json`. Preserve all
   unrelated concurrent work; do not replace a whole changed live source from an
   outdated postimage if fragment preconditions fail.
5. Reuse the retained new source guard red/green and prior unaffected combined
   guards rather than replaying accepted suites. Root owns any actually needed
   newly affected check and the final source-map applicability review.
6. Refreeze final inputs. Request only the unchanged combined iOS request2 + DNS1
   selection in one Mac/iPhone application task; no accepted11/profile expansion.
   Root owns actual SDK/compiler/native proof, original XML/results/owned cleanup
   review and any issue closure. #64 remains open until its original criteria pass.
