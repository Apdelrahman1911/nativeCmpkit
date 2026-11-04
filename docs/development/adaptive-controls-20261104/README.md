# Adaptive controls — new related patch, 2026-11-04

Baseline `ac487941316626cc4b19546ab70f939d98c1c52d`; independent branch
`development/batch-adaptive-controls-20261104`. Lead owns integration and closure.

- Actual new Desktop **red2 → green2**, same assertion/test bodies: 0.965s
  failing XML /34s Gradle, then 1.206s passing XML /45s Gradle. Only the
  production non-null custom-thumb color provider changed between scoped maps.
- Original init-loader (28s) and CLI-filter (42s) refusals remain separately: zero
  executed library tests; the latter actually compiled the one test input.
- Actual iOS production + focused six-source test KLIB **exit0 /53s**; 167
  current relevant input hashes held. Zero Apple linking or native executions.
- Seven NEW lexical controls pass once0.003s; only the later changed native thumb
  fixture control executes once more1/1/0.001s. These are not library tests.
- Existing accepted Liquid first-eight bodies are byte-identical, not replayed.

See [original receipt](receipt.json), retained red/green XML/log/maps and the
[detailed matrix/limitations](../../testing/adaptive-controls-native-matrix.md).
The original logs and XML are copied without modification. Initial broad maps
include uncompiled iOS drafts, not an asserted global freeze; later scoped Desktop
and final iOS maps are explicitly qualified. Build warnings remain in originals.

No GitHub mutation, native dispatch, package/release/deployment, history/main or
policy change. #133/#138 still need all four NEW methods per actual pre26 versus
26+ host with original application/Worker/XML/custody/cleanup. #129 remains partial
for genuine native populated26+ toolbar, keyboard/safe-area/orientation and native
bottom-bar integration. No extra unrelated spoken-assistive gate added to #133.
