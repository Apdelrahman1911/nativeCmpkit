# Actual Android dropdown recovery

[Run 41019914123](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41019914123)
**SUCCESS**, immutable `0d0ba755decc9517c53ab566ae4b3b1ee939be8b`:
**one fresh actual Android method/one pass**, Gradle exit 0 /65.03 s.
API35/x86_64/Android15, SELinux Enforcing; compile SDK package
`platforms;android-37.0`. The finite recovery requests only
`MaterialDropdownAcceptanceTest#focusAndDismissalPropertiesControlActualBackAndPointerEvents`.

[Review](review.json) inspects fresh XML, actual instrumentation filter/task
marker, all918 library/all995 combined historical Git inputs, runtime and owned
emulator graceful shutdown. The owning fixture supplies current monotonic
KeyEvent/MotionEvent times and explicit keyboard identity. Native delivery,
enabled/disabled focus/dismissal, exactly-once callbacks and recycling assertions
remain; no direct dismissal callback, skip or timeout relaxation.

The older [four-target matrix](../platform-ci001/README.md) remains **FAILED**:
15 accepted results are reused without replay, plus this one fresh result,
**16 cumulative target executions/four distinct methods**, not a new green
16-case workflow. Original criteria and #132's closure are reviewed
[separately](../../dropdown-contracts-verified-20261030/README.md).

No physical/minimum-platform/other OS/browser/native iOS/accessibility/ABI/
consumer/dependency/legal/security/release certification. No publication,
deployment, Pages, main or history changes.
