# Immutable hosted verification — 2026-10-26

These receipts describe `6eb7c66eb01b390353100c63882cd102846c7b8d`, **not later
source repairs**. The lead worked single-agent, inspected the completed jobs and
independently matched ZIP SHA256s, source input maps, commands, runtime identities,
XML hashes, actual testcase identities/outcomes and exact native scenario policy.
The contained workflow uploaded JSON/XML only, not packages. Raw archives remain
self-contained after GitHub's seven-day artifact expiry.

| Run / slot | Actual results | Reviewed evidence |
|---|---|---|
| [40414284598](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40414284598), Linux x64 desktop | 426 passed; one exact AppKit-only N/A | [Review](40414284598/lead-independent-review.json) |
| Same run, Android host/Robolectric | 405 passed; **not Android device execution** | Same review; combined 831 fresh executions / 141 XML reports |
| [40415332643](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40415332643), macOS Arm64 desktop | 426 passed; one non-mac-only N/A. Real AppKit GUI cancellation, ABI/diagnostic loading and borrowed-pointer rejection executed | [Review](40415332643/lead-independent-review.json) |
| Same run, iPhone Arm64 simulator / iOS26.5 | **Failed**: 348 executed, 332 passed / 16 failed. WebView production compilation failed; zero WebView tests | [Original failures](40415332643/ios-failures-concise.json); one explicitly missing suite |
| [40417671294](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40417671294), Windows x64 | **Failed**: 422 executed, 421 passed / one failed; five skipped, only one eligible N/A, four unexpected | [Review](40417671294/lead-independent-review.json), [failure](40417671294/windows-failures-concise.json) |

All three tooling jobs succeeded. Core's separately recounted tooling execution
was **760 Python methods**, not Kotlin/library/native/packaged-consumer tests.
Repeated common functions across target executions are not independent methods.
Successful slots do not make either failed platform workflow green.

## Evidence-review corrections, not suppressed failures

- Core's first recount assumed receipt testcase order followed ZIP entry order.
  The failed original script/receipt remain. The corrected comparison sorts
  unique `(classname,name)` identities; hashes, count/status checks and duplicate
  rejection were retained.
- Apple's recount transparently accepts **evidence of a missing failed suite**:
  it requires zero reports/cases, a matching missing-test error, failed execution
  and `passed=false`. Missing XML is never converted to a pass.
- Windows' first source-byte review failed because hosted Git checked out **692
  text files as CRLF**; three binary inputs were unchanged. The held before/after
  maps were equal. The corrected review proves each individual hash equals either
  its immutable Git blob or that blob's exact LF-to-CRLF transform, using the
  [per-path observation](40417671294/windows-line-ending-observation.json). No
  arbitrary whitespace/content normalization was accepted. The original failed
  review remains; future workflow checkouts explicitly disable autocrlf.

No issue was closed by these receipts. No preview, package, release, deployment
or Pages was created. Device behavior, complete native host/payload matrix, ABI,
legal/dependency trust and strict artifact-consumer gates remain independent.

## Subsequent immutable Android attempt

Run [40422019219](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40422019219)
at `d849515b2a1f6048ed280e44e677f532a57d4f5f` **failed with zero tests/XML**.
APK assembly passed and the owned API35 emulator booted and shut down cleanly;
the connected-task XML-path guard prevented all three suites from executing.
The [independent review](40422019219/lead-independent-review.json) verifies exact
source/ZIP/receipt integrity and missing suites, not native-feature success.
See the [getter inspection and owning repair](../../checkpoint-20261027.md).
