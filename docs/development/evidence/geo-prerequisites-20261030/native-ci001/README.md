# Android prerequisite attempt: pre-test harness failure

[Run41051631302](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41051631302)
at immutable `17b299fd3019193c2302503c31d32ab2bdb442b5` is **FAILED**.
Tooling passes. Reporter APK assembly exits0/297.08s; separate source consumer
assembly exits0/175.06s. Actual installation, APK-byte readback, owned removal
and graceful enforcingAPI35 emulator shutdown are independently verified.
All944 library/1021 combined inputs match that revision and remain held.

**Zero native/library tests, zero XML.** The controller reports `ValueError`
before recording its initial permission map. The actual human dump was not
archived, so its exact formatting/error is unknown, not an inferred denial.
The narrow private reviewer initially required a nonexistent invocation receipt;
the separate GET-only failure review preserves this failure without accepting tests.

The standalone probe receipt was also absent from the upload paths; the
controller contains its owning cleanup record. A new owning scalar permission
query and explicit receipt-only upload are covered in
[permission-service001](../permission-service001/README.md). Recover only the
three still-unexecuted native cases; do not replay accepted injected/host tests.
#25 stays open. Console excerpts are omitted from the archive with original and
archived hashes; raw ZIPs, logs, APKs and keystores remain private.
