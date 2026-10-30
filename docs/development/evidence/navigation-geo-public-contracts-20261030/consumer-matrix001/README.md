# Standalone nav/geo source consumer — actual six-target pass

Immutable `6fd89634a4b143303b17ce7e99385d6a7d5627dc`: actual Android,
Desktop JVM, JS, WasmJS, iOSArm64 and iOSSimulatorArm64 compiler tasks pass.
[Command/result](build.log.result.json): exit0/169.04s, 1007 selected inputs
held before/after, clean revision, six exact fresh task begin/end markers.
**Zero runtime tests**; Apple KLIB typechecking only, not linking or execution.
Two explicit source substitutions for unpublished experiments, no hidden AndroidX/
GMS dependencies in the consumer; not Maven/ABI/publication evidence. Actual
Android003 red and earlier acquisition/caller failures stay in implementation001.
The later CI guard-only commit does not change this consumer or library build/
source; reuse this accepted compilation instead of rerunning it.
