# Windows exact-import-context stat prerequisite — 2026-11-05

## Related patch and important checks

The unchanged R2C companion reproduces the failed observer's import prologue,
lookup context and immediate named/descriptor comparison. It closes and stops
**both on equality and mismatch, before the base body/hash, legacy import,
controller, worker or GET**. Only bounded numeric metadata is logged.

The additive workflow keeps all prior job filters, defaults, push registration,
permissions and artifact scopes unchanged. The new job is manual-only, exact
repository/development-ref/input guarded, Windows 2025, Python 3.12, two minutes,
`contents: read`, checkout credentials not persisted, and no upload.

The sole changed/new control passed **1/1 once**, independently reviewed by742:
0.147s suite,0.274895938s source protocol,0.334877562s launcher. Four explicit
source and model inputs held all ten metadata fields and hashes; child terminal,
empty owned state and model removal passed. Original controls were not replayed.
Actionlint passed once in0.007576270s; shellcheck/pyflakes were not executed.
The three-source patch was adopted once, preserving the existing workflow mode
and creating both additions0644. The original observer stayed byte/identity equal.

See [verification](verification.json) and the [bounded hosted plan](HOSTED-DIAGNOSTIC-PLAN.json).
Their observed HEAD precedes this evidence commit; neither claims runtime success.

## Original failure and strict next step

[42100069342/a1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42100069342)
remains FAILED before the body/hash/legacy/controller/GET. Its exact operands and
cause remain unknown. The different stat-only job
[42105898874/a1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42105898874)
at the source-checkpoint HEAD succeeded with equal seven-field rows, but that
is not the original import context or an explanation of the failure.

After immutable development push and fresh shared capacity, request **only the
new context diagnostic once**. Equality is neither dependency trust nor permission
to rerun the original unchanged observer blindly. No network observation, native
WebView request-state test, consumer integration, #64 closure or release gate
is established here. Preserve the original failed logs; do not reacquire them.
The protected untracked success-trace path is never accessed or staged.
