# Accepted focused macOS filename-domain recovery

[Immutable run40820003878](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40820003878)
at `398a3332` is **SUCCESS: 5/5, exit0 /71.93s**, zero failed/errors/ignored.
[Independent source/results review](lead-source-results-review.json) checks
838 before/after inputs against the producing Git objects, actual macOSarm64,
JDK17.0.20.1, Rust1.98.0 and Xcode26.6. The workflow's 13 owning receipt-tooling
methods also pass; they are not native tests.

One actual filesystem test confirms both file and directory creation reject
unrepresentable bytes with **EILSEQ92**. Four explicitly **controlled PathBuf /
real-JNI** negative cases verify typed errors, valid replacement-character peers
and 128 weak-array cleanup iterations. They are **not actual invalid selected
files on macOS**, where creating those entries is impossible on this test host.
Linux's actual invalid-byte file cases remain mandatory.

Nine unchanged native methods were filtered. Accepted Unicode, Compose, Linux
and Windows cases were not replayed. Original failed matrices and their
before-JNI EILSEQ fixture failures remain unchanged; this recovery does not
retroactively make either failed matrix green.

[Digest review](download-review.json) verifies the GitHub ZIP digest and every
one of five selected JSON reports. The live runner observed the native compiler
executable hash; an offline reports-only review cannot re-execute that absent
payload. The [additive manifest](archive-manifest.json) stores ten JSON records,
**no ZIPs, native payloads, console logs or credentials**.

No additional issue is closed solely by this recovery. Native-parent #58,
settings/limits #53/#54, UIKit/provider, physical/minimum-platform, whole
ABI/consumer/dependency/provenance/legal/security/release gates remain open.
This finite native recovery is not full stable CI or a release authorization.
