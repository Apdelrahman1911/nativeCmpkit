# Android share URI ownership batch — 2026-10-30

## Verified outcome

**#83 is closed/completed** after all three original criteria and independent
[readback](evidence/android-share-uri-grants-20261030/closure001/README.md), before docs.
Actual41062614557 at026a9903 passes3/3 fresh native methods/one XML/39.02s; all967/
1044 exact Git inputs, selector/runtime/installed identities/native three-UID
signature assertions and owned cleanup are reviewed. The earlier tooling-only
request remains failed. #81/#88/#141 and all independent release gates remain.

Primary finding: [#83/NATIVE-028](https://github.com/Apdelrahman1911/nativeCmpkit/issues/83).
The existing owning implementation converts local `file://` inputs through the
explicit narrow FileProvider, forwards content URIs unchanged, attaches every URI
to EXTRA_STREAM and ClipData, grants read only and exposes typed failures.
Public packages/APIs and dependency versions remain unchanged in this batch.

## Three distinct native UIDs, not fabricated reads

- Library instrumentation calls the real `launchAndroidShare` /
  `deliverAndroidShareResult` path from its foreground Activity.
- `tests/consumer/android-share-documents` owns a real DocumentsProvider and two
  fixed synthetic text/PNG documents. A signature-protected finite Activity
  returns real document URIs with read-only Activity-result flags. Android creates
  the caller's incoming grants; there is no manual `grantUriPermission` RPC.
- `tests/consumer/android-share-recipient` receives the real outgoing intent in a
  third UID. Package/signature/UID/nonce/finite Messenger checks authenticate its
  snapshot/read/clear protocol. Real ContentResolver/PFD reads are bounded8192
  bytes, hashed, and closed by one AutoCloseInputStream. Actual write attempts and
  third-UID provider open/close/error/write counters are asserted.

Only chooser recipient selection is redirected. Android still owns the outgoing
grants. This is not chooser UX or actual DocumentsUI/cloud/vendor/photo-picker,
physical/minimum-platform, public packaged-consumer or ABI certification. The PNG
is a genuine image document, not proof a vendor photo picker granted it.

Three finite methods cover local conversion/delayed read/revocation; foreign
incoming document read-grant forwarding/mixed MIME/ClipData/descriptor ownership;
invalid configuration/empty/unsupported/ungrantable/provider exceptions without
recipient delivery or source deletion. Closing each owned Activity owns its
nonpersistent grant lifetime. A nonowner does not invent authority to globally
revoke the third app's source URIs; explicit FileProvider revocation is separate.

## Controller and evidence

`android-share-grants` selects one API35 job and exactly these three library
methods. The full Android plan retains all prior six modules and adds share as
the seventh; all11 full-platform slots remain. The controller owns its AVD, builds
and installs both source fixtures with the same private signing environment and
without `-g`/`-r`, verifies installed bytes and removes both before graceful
shutdown. Any setup/source/cleanup/report failure remains failed. Only selected
receipt JSON/XML is uploaded, never APKs/signing inputs/candidate packages.

[Important checks and compilation](evidence/android-share-uri-grants-20261030/implementation001/README.md)
do not imply native execution. #83 is verified and closed after actual immutable results
and all three original criteria were reviewed. Related #81/result-stage and
#88/mobile-thread findings retain their unverified macOS/UIKit/public-launch
criteria; delayed Android reads alone cannot close them. No publication or
release/security gate is cleared.
