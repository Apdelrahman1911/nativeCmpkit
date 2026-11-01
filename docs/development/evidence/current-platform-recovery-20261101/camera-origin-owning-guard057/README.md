# Camera owning origin-line guard recovery

Primary source review found one existing dependent guard omitted by the earlier static assessment: mutable-path diagnostics captured the real live helper traceback but still required literal raise47. Adding the new Activities header shifted that real raise to48. One important source method genuinely fails on the current immutable f97a0e1b source; original failure and log hash are preserved.

Only this owning guard changes: derive the exact live original require raise from its AST and additionally require the original owned source path. Exact ValueError type/message, direct require symbol, all original state/no-dispatch/cleanup refusals and production/helper/native/workflow bytes remain. All12 affected synthetic methods pass once on the corrected guard; ZERO SDK/build/network/signal/native actions. The separate prerequisite-require-origin consumer was already dynamic; that fact did not justify ignoring this literal consumer.

Current hosted originals must be reviewed separately; local red does not diagnose their actual cause or imply a native pass. Reuse accepted compiler/native/plan results only for unchanged applicable source bytes. No issue closure, permission or release/security gate changes.
