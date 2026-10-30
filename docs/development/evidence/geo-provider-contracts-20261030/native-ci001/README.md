# Actual Android provider batch: two accepted methods, one failed prerequisite

Run[41042004511](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41042004511),
immutablec446bad36492aec4308c63e0d6c5513b5c18af39, remains **FAILED**.
Actual Gradle exit1/46.02s; three fresh native methods/one XML: **2 passed/1 failed**,
zero errors/skips. Exact930 library/1007 combined historical inputs, runtime,
filter, one fresh task marker, artifact digest and owned graceful emulator shutdown
were independently reviewed. The private reviewer's initial `failure` versus
the real parser's `failed` status spelling error is preserved and corrected;
acceptance requirements were not relaxed.

Accepted unchanged methods, never to be replayed merely for a green workflow:
- `nativeProviderTaskErrorsRemovalRetryAndRecoveryAreObservable`;
- `nativeBackgroundCancellationAndQueuedOldCallbacksCannotOwnANewStart`.

Both use explicitly injected provider transport/permission accuracy with actual
Android GMS Tasks/threads/Main Looper/queued Handler callbacks. They are not actual
OS revocation, missing services, settings-off or GPS/fix accuracy certification.

The real default-GMS method failed its initial denied-permission assertion at
line68: an OS check returned GRANTED rather than DENIED. It stopped **before**
tracker creation/provider work/grant transitions. Its installed APK targets SDK37;
the exact permission-provisioning mechanism must be established, not blamed on
the library or hidden by loosening the assertion. Recover only this failed method
after repairing the owning fixture's initial state. No grants are to be revoked
mid-instrumentation, killing its reporter.

Both original #25 criteria still require actual permission/provider prerequisites;
#25/PERM-021 remains open. No accepted ownership/host/portable tests rerun, no
whole-CI or release gate pass inferred. Reports are sanitized; raw logs/ZIPs/APKs
remain private, not committed.
