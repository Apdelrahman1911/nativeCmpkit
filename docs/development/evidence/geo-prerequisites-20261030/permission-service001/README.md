# Owning permission-service recovery

The human `dumpsys package <package>` output is not a stable permission API.
Tagged Android15 `DumpHelper.doDump` lines135–168 instead implement
`dumpsys package check-permission <permission> <package> <user>`, printing the
actual PermissionManager constant. The controller now queries both foreground
permissions for its byte-verified installed package and explicit user0.
Only0/granted or−1/denied is accepted; errors, missing/duplicate/unknown output
fail, not become denial. Native same-UID reads still own the actual tests.

Five new synthetic contracts initially ran2pass/3errors and now pass, together
with12 applicable installer/selection contracts: **17 passing methods**.
Unexpected grants and malformed output cannot start native verification or skip
byte-reverified owned cleanup. The workflow uploads only the separate probe
`receipt.json`, not its APK or private signing tree. Actionlint1.7.12 passes.

All945 library/1022 combined inputs were held. Only four tooling/workflow paths
change; geo production, test bodies, source consumer and compiler declarations
are unchanged. Accepted two injected native and five host methods are reused,
not rerun. **Zero new native tests**; one immutable three-case request is required.
The prior failed run, unknown actual dump format, red tests and initial PATH-only
lint lookup remain documented. #25 is not closed; no release gate is cleared.
