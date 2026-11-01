# Fixed, private-safe Apple help diagnostics — 2026-11-01

[Actual41254296009](../apple-appinfo-capability-20261031/native-ci003/REVIEW.md)
remains **failed**: helper2/5.47s; complete help exit0 does not establish accepted
syntax. Raw help is deliberately withheld. This repair only distinguishes fixed
UTF-8/Usage refusal and finite allowlisted shape observations; the original exact
acceptance regex/equality and command, ownership, time, output, privacy, cleanup
and read-only gates remain unchanged. No appinfo payload/simulator/profile query
is enabled.

Eight new synthetic methods first fail for missing diagnostics, then pass8/8,
exit0/0.16106s;22 static checks pass. Lead integration matches both tested
postimages exactly and reuses these accepted models **without replay**. Existing
helper functions and existing test class AST bodies are unchanged except
`help_observation`. Test Popen is forbidden; one injected collect model uses
owned temporary files. No SDK/build/native/CI execution follows from this patch.

Full raw synthetic red/green logs remain private; their identities/classification
are retained. There were21 red subtest error blocks in eight methods, not21
methods. Prior actual failures, unexercised Darwin recovery, #141/UI-038 original
profiling/leaks/GC criteria, release/security and publishing gates remain open.
