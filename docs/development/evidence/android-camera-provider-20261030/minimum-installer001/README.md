# API23 installed-byte ownership — focused repair

Actual [41079029687](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41079029687)
at `b5619a5f` boots Android6.0/API23/x86_64 with SELinux Enforcing after AVD0/2.0s
and reporter APK0/230.05s. Receiver prepare and cleanup fail ValueError before
any native method/XML. The originating guard remains **unknown** because partial
receipts/origins were discarded. Owned emulator and ADB transport removal pass;
receiver uninstall is not verified. [Original failed evidence](../minimum-ci002/README.md)
is retained, not relabeled successful.

Public Android6.0.1 toolbox/toybox build lists do not include `sha256sum`.
This is an independently observed compatibility concern, **not proof of the failed
image's exact guard**. API23 now explicitly streams only the validated installed
APK through owned `adb exec-out cat` and host SHA256: 64KiB read blocks, 256MiB
limit, 64KiB error limit, 30s deadline, no persisted raw bytes, lease checks before
and after. Failed/empty/oversized/error/changed-length reads stay failed; exact
source digest and native signature/UID assertions remain mandatory. API35 retains
its original native checksum route; neither route silently falls back.

The owning camera installer persists partial assembly/source-byte/install/cleanup
facts even on refusal. The controller retains those facts and exact public source
filename/symbol/line only, never exception text, locals or machine paths. Unknown
or foreign installed bytes never authorize force-stop/uninstall. Other sharing
contracts retain their successful results; only operation receipts are saved sooner.

**13 new/changed synthetic methods initially fail** (12 contract errors/one receipt
failure); after repair **79 important controller/camera/share methods pass**, then
three newly added refusal methods pass without replaying the79. These are actual
host unittest outcomes with controlled device commands and real bounded host pipes,
**zero Android/native/library executions**. The selected984 library/1061 combined
inputs are frozen in the receipts. No production/native fixture/compiler/dependency
inputs change. Reuse accepted API35 four and host22; only four still-unverified
API23 native methods need the new immutable request. #78/#13/#80/#141 stay open.
All publishing, Pages/main/history, solo/capacity and independent release/security
gates remain; nothing is published or deployed.
