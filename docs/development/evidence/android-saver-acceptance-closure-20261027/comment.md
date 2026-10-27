<!-- nativecmpkit-resolution:IO-002:40414284598:40436756084 -->
## Verified resolution — IO-002

The Android saver now shares one `rememberSaveable` request holder across launcher/result recompositions, consumes/clears exactly once, rejects overlapping launches and treats restored/lost ByteArray content as an error, never an empty-success save. URI state is restored; large byte payloads are not put in the Activity Bundle. Existing public launch signatures are retained.

**All five original criteria are verified:**
1. Real Compose/Robolectric launch → recompose → result preserves both bytes and KmpFile content.
2. Actual Android Activity recreation below the real child Activity restores a URI request; lost bytes fail/clean up without a write or success callback.
3. Actual cancellation yields one null result, then a new launch writes its own payload; completed state cannot restore as pending.
4. Exactly-once consumption and native overlap rejection do not replace the accepted request.
5. Missing/lost/unreadable required content cannot report a no-op save as success; actual provider failure writes nothing and cleans only the new destination.

Reviewed immutable executions: [host run40414284598](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40414284598) at `6eb7c66eb01b390353100c63882cd102846c7b8d` (**35/35 picker host methods**, eight XML; host job exit0) and [device run40436756084](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40436756084) at `ab213b4016eed66bf92ab067bb867d4b1fdfb9bd` (**8/8 actual FileSaverActivityDeviceTest methods**, API35/x86_64, SELinux Enforcing). XML hashes and named cases were inspected. Current Android production/test/dependency inputs match the device revision except two exact project/POM display strings; host saver inputs also match, with only an unrelated `isDirectory` metadata repair that the saver does not call. These existing same-input results are reused explicitly; no new execution is claimed.

Closing the original five-criterion finding directly after review. **The overall device run remains failed** (24/25 picker; native hard-link fixture EACCES plus unrelated WebView history precondition); those independent coverage/security gates remain open under BUILD-006/release-readiness. OS process-death/persisted grants, physical/minimum API, broader provider/native ownership, legal/dependency, packaged consumer and API/ABI remain unverified. No package/release/deployment was published. Original issue body/labels/history are preserved.
