# Isolated native recovery, not a production fix or runtime pass

[Tooling review](review.json) retains the first failed6-method run (5 passed /
1 failed), then only the failed guard's1/1 recovery. The synthetic native case
identity accidentally retained KGP's namespace prefix; stripping that prefix
fixes the fixture without changing strict result/Worker/runtime/binary/cleanup
checks. Six distinct important tooling methods are accepted, not seven native
tests. [The first timestamp-label error](timing-label-correction.json) is preserved.

`ios-slider-remaining` selects exactly the three never-started methods.
`ios-slider-structure` selects only the interrupted Liquid structural method.
Two completed unchanged enable/callback methods are not replayed. The original
six-method profile and full11-job matrix remain intact.

Structural tests emit62 finite renderer/axis/phase markers around the original
operations/assertions. Missing, reordered, duplicate, malformed, foreign-case
markers cannot make a structural case pass; unfinished phases are diagnostics
only. Focused slider app execution is bounded at300s rather than1920s, excluding
compilation/setup; other profiles retain1920s. This stricter failure deadline
does not remove any method/assertion, change production input, or clear a gate.
All869 final tooling inputs are held; no local changed KLIB/link/native test was
executed because capacity is below the8GiB reserve. Actual immutable CI is pending.
