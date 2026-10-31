# Android default Coil decoder regression

The proper library fixture is
`calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoDefaultDecodeTest.kt`.
The [reviewed source proposal](evidence/android-io-default-decode-20261031/README.md)
and [held APK build](evidence/important-coil-yarn-local-20261031/README.md) retain
source hashes, root cause of a repaired test-only bitmap cleanup gap, original
red and actual compiler receipt. ReporterAPK0/156.03s compiles the new class,
**zero native executions** at this checkpoint.

`android-io-default-decode` selects exactly three API35 methods:

- Unknown-size seeded PNG: genuine native encode/default BitmapFactory decoder,
  every pixel/dimension/config, partial encoded-source buffering, original bytes
  and real descriptor closure.
- JPEG EXIF6/7: genuine native encoder/platform EXIF writes, default bounds/EXIF
  replay and independent rotation/reflection quadrant expectations.
- Four corrupt requests inside one whole method: genuine cross-UID
  DocumentsProvider tree grant, default null-bitmap error and monotonically
  matched opens/closes/zero descriptor/write errors.

The observational EventListener verifies actual fetcher/default decoder identity
and does not consume/replace the source. Returned bitmaps recycle on assertion
failure, loaders shut down, bookmarks/endpoints/directories are owned/cleaned and
primary plus secondary failures are preserved. Caches are disabled and calls run
on Dispatchers.IO; this is not request-key/invalidation or peak-memory testing.

The finite native request must retain exact immutable inputs, class/method/task
filter/fresh original XML and Enforcing runtime, helper source/installed-APK
identity+signature, actual grant/native-UID/REG-resource assertions and graceful
owned cleanup. Seven image requests are only planned if all methods complete;
they are not seven observed test methods. Reuse unchanged five accepted lifecycle
methods, oversize and host results without replay. #45/#55/#57 remain open beyond
these bounded default-decoder criteria; no cloud/system/Apple/minimum/physical/
packaged/API-ABI/security/legal/readiness or publishing gate is cleared.
