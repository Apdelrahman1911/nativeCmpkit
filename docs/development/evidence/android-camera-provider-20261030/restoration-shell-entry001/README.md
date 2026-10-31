# Protected native-shell entry for the disposable restoration caller

The [actual sixth request](../restoration-ci006/README.md) fails four native
methods at an empty `Status: ok` readback. Its underlying cause remains unknown.
[Public Android15 source](public-shell-entry-source.json) confirms the earlier
fixture's contract mismatch: Shell requests DUMP, does not request
START_ANY_ACTIVITY, and ordinary component checks reject a foreign nonexported
Activity without a bypass. These frozen public source URLs/digests/lines are
context, not extraction or attestation of the running emulator framework.

Only the disposable restoration-client entry changes to exported with
`android.permission.DUMP`; its secondary process remains. The test adds fixed
`com.android.shell` visibility and requires the actual installed shell UID2000,
granted DUMP, exact client permission/UID/process and existing native readback
before proceeding. **DUMP is signature|privileged|development, not shell-exclusive**;
another holder can satisfy this entry permission. No permission adoption, root,
manual grant or registry/result/lifecycle injection is added. The genuine public
camera launcher, real ComponentActivity state/save/results, Android URI grants,
four original native criteria and owned cleanup remain required.

Three new synthetic methods first fail **3/3**. The affected camera-tooling file
then passes **58/58** methods, including those three; these are synthetic guards,
not runtime executions. [Actionlint0 is reused](actionlint-reuse.json) from the
foreground review after exact workflow SHA256 equality, not rerun or claimed
fresh. Serial reporter APK assembly passes exit0/36.01s with **989 library/1066
combined inputs held and rechecked**. Unchanged receiver compile0/14.0s is reused,
not fresh. Private red/green/compiler logs are retained by digest only.

[Compiled APK inspection](apk-inspection.json) records the reporter's actual
export/DUMP/process/query values and nonexported providers, both APK byte hashes,
and equal local certificate SHA256. Reporter9742924bytes/
`b47b466e28736f6a588fbda3645f3970e8a4cd68b85a7a277f8e3b73ac36c612`;
receiver899301bytes/
`6f7d24cccf9f84346d1690a1cad0aafa8190e7ef88747e99e2a4c9edc5fe990d`.
This inspection does not establish the installed shell's permission, successful
foreground launch, native restoration or a production manifest/signature result.

**Zero native executions of this repair; #13 remains implemented/open.** Only
the four still-unverified API35 restoration scenarios need the next immutable
request. Accepted provider/API23/host/unrelated results are not replayed. No
production/public-API change, publishing/Pages/main/history mutation or native/
consumer/API-ABI/heap/dependency/legal/security/release gate clearance is inferred.
