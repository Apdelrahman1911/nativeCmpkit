# Read-only diagnosis of the failed Apple image-profile launch

The previous actual run41034923043 remains **FAILED / zero tests**. Signing,
installation and owned cleanup passed, but launch exited1 before a PID or native
application activation. Its service-delegate refusal has no proven root cause.
No profiler exports or leaks command ran; #141 remains open.

The new diagnostic reads only one selected simulator's unique owned bundle in
the actual failed-launch time window, only after the finite recovery's installed,
pre-PID/pre-activation nonzero console refusal. Bounds:30s/1MiB/2048 rows/8KiB per
message. Only hashes, counts, fixed system names and fixed error categories survive.
No raw messages, paths, guessed PID, arbitrary symbols, relaunch, launch-success
inference, heap inspection or public artifacts. Unavailable logs remain unavailable.
Diagnostic exceptions cannot prevent owned cleanup; diagnostic-bearing receipts
cannot be relabelled as green transport.

[Implementation evidence](implementation001/) preserves the six-method initial
red, then the five-method caller/fixture red and one-method receipt-guard red.
The original privacy fixture mistakenly matched the generic word `message` in a
legitimate Boolean key; unique private canaries replace that collision, with every
no-disclosure assertion retained. RuntimeError exposed missing diagnostic exception
containment; the timeout subtest subsequently encountered its uncleaned installation.
The actual caller fix retains failure while completing owned cleanup. Ten distinct
important synthetic methods now pass in two five-method requests; these are not
Apple/native/profile executions. Earlier unchanged accepted methods were not replayed.
The source-only one-case plan passes with932 library/1009 combined inputs held.

Only actual correlated useful owned allocation rows and same-PID actual zero leaks
can clear profiling. Strict startup and the earlier150s timeout remain unknown,
unfixed and unwaived. No issue, release/security/minimum-platform/ABI/packaged
consumer/provenance/legal gate or publishing/Pages/main/history change.
