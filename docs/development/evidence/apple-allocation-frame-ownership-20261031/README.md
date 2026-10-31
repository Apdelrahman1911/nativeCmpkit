# Apple allocation-frame ownership — modeled correction, not profile acceptance

Independent modeled red reproduces a foreign `ImageUtils.kt` allocation row being
treated as NativeCmpKit-owned. A basename or unqualified test class is not ownership.
The parser now requires the exact `com.mohamedrejeb.calf.ui.utils` namespace with
symbol boundaries in the **same frame field**, before matching optional whole
class/file labels. Explicit frame/backtrace references remain supported.

`modeled-source-review/` preserves the original red, candidate delta, patch and
hash manifest. `integration/` binds the applied patch and **8 new plus13 related
modeled checks,21/21**, on held994/1071 inputs. Foreign/prefix/suffix/glued symbols,
unrelated metadata, split fields and no-useful-row attempts cannot become passes.

Launch/signing/query count/driver acknowledgement/cleanup/leaks/PID/profile
thresholds and native source remain unchanged. Existing fixed NSError domain/code
observations use the same single owned query. **Zero new Apple executions**;
actual export format and launch cause remain unknown. A next finite failed-image
profile still requires real useful owned allocation frames and same-PID zero leaks.
#141 stays open; all prior strict/timeout/startup failures remain failed/unwaived.
