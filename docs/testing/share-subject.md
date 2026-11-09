# Share subject: NATIVE-034 / issue #150

## Status and scope

Implementation and local checks updated 2026-11-09. The production and test
sources compile for desktop, JS and Wasm. **All 12 focused desktop mapping tests
passed once.** JS and Wasm browser methods remain unexecuted: local Chrome refuses
to launch as root with its sandbox configuration. The sandbox was not disabled;
actual browser execution requires a supported sandboxed host. The first desktop
compile attempt stopped because rustup was absent from PATH; the installed tool
was added only to the subsequent child process environment. Both attempts remain
in the external execution records.

The normal Linux CI browser phase now requests both calf-share browser tasks in
addition to calf-ui. No iOS compile/link, browser runtime, real Mail, native desktop,
fallback runtime or issue acceptance is established. Issue #150's original criteria
remain authoritative and open.

The isolated branch is `fix/native034-share-subject`, prepared at
`c2eeec65a0bfd8d03f0b3a7e27c3f97b4542f0f6`. All ten source baseline SHA-256 values
matched the lead's `issue150-preparation.json` before editing. The iOS item-source
implementation adapts only
`d968257ff8dd3340f6b4cda2f1b890044679635f:calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareContentExt.ios.kt`.
It does not import development launcher, outcome or lifecycle rewrites.

Public signatures, JNI ABI, Android behavior, payloads, platform result handling
and presentation/fallback lifecycles are unchanged. Internal web file helpers gain
a title argument; the actual web launcher mapping is exposed internally for tests.
Desktop's existing native mapping gains an internal injectable operation, with its
default still calling the unchanged JNI method.

## Subject behavior

| Route | Text / URL / single file / multiple files |
| --- | --- |
| iOS activity items | A non-null subject wraps each original item in an `NSObject` implementing `UIActivityItemSourceProtocol`. Placeholder and item selectors return the original item; the subject selector returns the supplied string. Null keeps the original unwrapped items. Empty string is supplied, not dropped. The view controller's navigation title is no longer used as an email subject. |
| JS and Wasm Web Share API | All four variants forward `subject` as `ShareData.title`. Null omits the own property; empty string retains `title: ""`. Text and URL fields are unchanged. File arrays contain the original browser `File` objects in original order. |
| Web clipboard fallback | Text/URL only; no subject channel. File fallback remains unavailable. |
| Desktop native JNI | No subject parameter exists. The original text, URL or absolute file paths are passed unchanged; subjects, including empty strings, cannot be delivered by this ABI. |
| Desktop clipboard/browse/open fallback | No subject channel. Text is copied, URLs are browsed or copied, and files are opened using the existing behavior. Subjects are not prepended to text, encoded into URLs or substituted for filenames. |

Receiving activities may ignore metadata. A web title is not a guaranteed email
subject, and the browser payload has no separate email subject, recipients or
per-file title fields. Web file names and MIME types come from the original `File`
objects, not `ShareContent.File.mimeType` / `ShareContent.Files.mimeType`; these
parameters do not rewrite browser file metadata. Desktop success does not mean
subject delivery or establish that an open/clipboard fallback is a native share.

## Test inventory (desktop executed; UIKit and browser pending)

| Source suite | `@Test` methods | Production boundary and assertions |
| --- | ---: | --- |
| `iosTest/.../ShareActivityItemsTest.kt` | 12 | Four variants × ordinary/null/empty subject. Calls production `toActivityItems`; invokes placeholder, item and subject selectors for Mail and unspecified activity types. Asserts text/URL content, actual file URL identity, multiple-item order and null-subject raw items. Creates an unpresented controller; never opens Mail. |
| `webTest/.../WebShareSubjectTest.kt` | 14 shared | Twelve payload cases (four variants × ordinary/null/empty) and two descriptor-restoration cases. Calls the production web launcher's `handleShare`, which reaches the JS/Wasm `navigator.share` call. Inspects exact own field names, text/URL/title, absence vs empty title, real file metadata and object identity/order. |
| `desktopTest/.../DesktopShareSubjectTest.kt` | 12 | Four variants × ordinary/null/empty subject. Calls production `showNativeShare` with an injected operation, checks exact arguments, ordered absolute paths, parent handle and one invocation. The operation returns the existing success code. No native library is initialized and no fallback or OS operation is invoked. |

There are **38 source test methods**. The 14 shared browser methods are intended
to run on **each** of JS and Wasm; the 12 UIKit methods are available through the
existing iOS source-set hierarchy. These are source counts, not run/pass counts.
The common Kotlin test dependency is inherited by these existing source sets.
`withBrowserTestBundling()` is enabled only in `calf-share`, following the existing
Compose browser-test convention; it also adds web executable distributions to
module assembly. No dependencies or target versions are changed.

### Browser fixture ownership

The JS and Wasm test fixtures install an own `navigator.share` property and retain
its complete previous own descriptor. `finally` restores that descriptor, or
deletes the test-owned property when it was originally absent (revealing any
inherited implementation). Installation failures also attempt restoration. No
prototype or clipboard property is changed. Explicit tests nest captures to force
the existing-own-descriptor path, compare all descriptor fields after normal
completion and an intentional assertion failure, and call production again to
confirm the restored outer capture is the recipient. An outer `finally` also
checks restoration of the browser's original descriptor.

Fixtures create real `File` objects with the browser constructor. They capture the
actual object passed by production, rather than constructing substitute share
payloads. Each intercepted call returns a deliberately pending Promise so all
payload assertions are synchronous. This neither tests nor claims anything about
promise resolution/rejection, cancellation, callback delivery or OS share UI.
A browser with configurable/shadowable `navigator.share` and `File` is required;
an incompatible descriptor must fail setup, not trigger native share UI.

## Pinned API signature inspection

No compiler was invoked. Bounded, read-only parsing of cached Kotlin/Native
metadata under
`/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20/klib/` established:

- `platform/ios_arm64/org.jetbrains.kotlin.native.platform.UIKit/default/manifest`:
  `compiler_version=2.4.20`, `metadata_version=2.4.0`, `native_targets=ios_arm64`;
  SHA-256 `310867ca93e23e039cd7caffdba0a6e3f7d8bbaecbccd6204cefe201d3d32c92`.
- `platform/ios_arm64/org.jetbrains.kotlin.native.platform.UIKit/default/linkdata/package_platform.UIKit/02_UIKit.knm`:
  SHA-256 `dc3737f43809867a602e125e0770b693223ecc0be460bb9a0d7ab01204b8df51`.
  `UIActivityItemSourceProtocol` declares:

  ```kotlin
  fun activityViewControllerPlaceholderItem(activityViewController: UIActivityViewController): Any
  fun activityViewController(activityViewController: UIActivityViewController, itemForActivityType: String?): Any?
  fun activityViewController(activityViewController: UIActivityViewController, subjectForActivityType: String?): String
  ```

- `common/stdlib/default/linkdata/package_kotlinx.cinterop/00_cinterop.knm`
  declares `kotlinx.cinterop.ObjCSignatureOverride`;
  SHA-256 `d0b7fce42b1d7f7a148813b546fd847ea2320419ecc772995dbf30d09b641397`.
  The cached stdlib manifest reports `compiler_version=2.4.20-dev-7885` and
  `metadata_version=2.4.0`; this is not described as a different tested release.

The implementation keeps the non-null underlying item as the covariant `Any`
return, annotates the two conflicting Kotlin overloads with
`ObjCSignatureOverride`, and explicitly opts into `ExperimentalForeignApi`.
Signature inspection is not compilation, linking or selector-dispatch evidence.

## Remaining original criterion gates

1. **iOS Mail:** on an Apple host, compile and execute the controlled tests, then
   actually present Mail for text, URL, single file and multiple files. Check
   subjects and original payload/attachment identity/order; retain null/empty
   cases without assuming what Mail does with absent metadata. Controlled selector
   calls alone cannot establish real Mail subject delivery.
2. **Web:** compile and execute the shared suite separately in JS and Wasm browser
   targets and retain the actual payload-inspection results. Source tests and this
   unsupported-metadata documentation do not count as that execution. Promise,
   cancellation and real share-target behavior require separate evidence.
3. **Desktop:** the 12 injected production-mapping tests passed once; retain real
   native and fallback evidence on their supported hosts, including the documented
   inability to deliver subjects. This seam does not test JNI loading, AppKit,
   clipboard, browsing, file opening or receiver behavior. Do not infer criterion
   closure from subject omission assertions alone.

The implementation sub-agent was not authorized to run any of these gates. The
lead reports that local heavy compiler admission does not meet the 8 GiB disk
floor. All integration, execution, Git/GitHub actions, acceptance and closure stay
with the lead; no resource-admission bypass or publication is authorized here.
