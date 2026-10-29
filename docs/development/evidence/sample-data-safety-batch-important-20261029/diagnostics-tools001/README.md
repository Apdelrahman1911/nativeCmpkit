# Shared sample failure diagnostics — important tools, not runtime verification

The first three owning guards failed (one assertion/two missing-input errors):
there was no sample failure-capture step, and no source-error handling for the
real unsigned Xcode log. The minimal repair uses the existing bounded diagnostic
collector before JSON/XML upload. It retains its credential filter and never
uploads full logs, apps, packages or frameworks. Setup failures without a result
directory remain explicit; collector errors are not silently suppressed.

The source-held owning sweep passes **33/33** across the two changed tooling
modules, with **960 sample/library/workflow inputs unchanged**. This repeats the
immediately preceding same 33 methods, not 66 unique tests. Actionlint and
whitespace pass. All three original red outcomes/log hashes are retained. **Zero
local Gradle, sample, native or library runtime tests** ran. The two existing
immutable CI requests were not changed, cancelled or redispatched. This tooling
patch cannot close #100/#139/#154 or any release/security gate by itself.
