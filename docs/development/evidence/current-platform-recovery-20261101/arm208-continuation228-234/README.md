# ARM208 failed-case fixture continuation228–234

The original208 control run remains **FAILED**: 13 accepted cases from two methods, 23 separate partial G13_3 pass observations, and the metadata-dictionary cleanup error. A minimal private fixture repair restores function `__dict__` in place.

Actual229 remains **FAILED**: metadata-dictionary and class-doc cases pass, then class-name cleanup throws `TypeError` because `unittest.mock.patch` tries to delete the type `__name__` descriptor. This is a fixture cleanup error, not an ARM/native/library defect.

The owning family repair uses a finite `__name__`/`__qualname__` context manager and restores identifiers by assignment in `finally`, checking both original identity and value. Six other bodies and all16 private dependency payloads remain exact.

Actual232 selects only the failed class-name case and36 unseen cases: **five methods/37 cases PASS**, wrapper13.951063082s; original unittest log5/5 in13.505s. The metadata/doc229 passes, original13 accepted cases, original23 partial observations, accepted ownership8/R01–R04/NEW2 and JSON vector are not replayed. Source/profile/output guards, one footer hook and zero JSON function/body/forbidden/leftover counts were reviewed in234.

**This does not certify whole NEW7/75 or whole original G13_3.** The staged `library_tests.py` remains `b333567d…`, not the current live Share188 source. The reuse adapter is not integrated. No ARM hardware, native, consumer/API-ABI, dependency/security/release acceptance or issue closure follows.

[SOURCE-RESULTS-REVIEW.json](SOURCE-RESULTS-REVIEW.json) records the exact method/case inventory and original receipt/log/driver/lock hashes. Originals and private source packets are retained outside the repository; none was reacquired or relabelled. Solo continuation, serial local/8GiB reserve, maximum2 combined hosted reservations including queued, and all publishing/Pages/main/history gates remain.
