# Pinpoint the shared tap timeout without replaying accepted methods

The actual prior tap run completed zero native cases and timed out without any
phase witness. Add **24 finite phase markers** around the original content, tap,
drag, opposite-tap, 512ms frame-clock, scene cancellation and semantic actions.
Each renderer's exact active testcase owns its sequence. Partial progress remains
incomplete; missing/reordered/duplicated/foreign phases cannot become a pass.
An original assertion failure remains failure even with native runner exit zero.

Important shared synthetic tests run **105/105**, all **877** before/after source/
recipe inputs held. Six new phase guards test both renderers, incomplete/failure
preservation and forged report rejection. Existing selection, transport, Worker,
runtime, binary, XML, cleanup and same-host archival guards pass. These counts
overlap earlier tooling runs; **zero local KLIB/link/native application tests**.

Independent exact-body review proves the tap body is byte-identical after removing
only the 24 diagnostic calls. Enabled/structural methods, renderer helpers,
production and the actual application/control driver are unchanged. No tolerance,
skip, timeout extension, callback expectation or native behavior is changed. This
is diagnosis preparation, not an underlying source repair or issue closure.
Only unfinished tap methods require immutable native execution; accepted methods
are explicitly reused. See [review.json](review.json) and [receipt.json](receipt.json).

Single-agent; maximum two combined heavy hosted requests; no heavy local build
below the 8GiB reserve. All publication/Pages/main/history and independent
native/device/security/consumer/legal/release gates remain.
