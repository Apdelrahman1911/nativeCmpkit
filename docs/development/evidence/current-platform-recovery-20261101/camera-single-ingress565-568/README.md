# Shared camera CI single-ingress repair — 565–568

## Actual request and failure

The qualified HOME patch and fixture batch were pushed additively as
`23e0ed9bc68c78b7c1e2549c1518a86d172e4b8c`; protected `main` remains
`94d2492e99d5cbc060409d94d9f88febd06222d5`.
[Run41749936269](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41749936269)
requested **only** the missing original Dont-keep C1 method after all five
paginated active-status inventories were empty. One host was reserved, including
queued work. Its actual SHA matches the request.

The original run remains **FAILED before platform execution**. Tooling reports
2,695 test invocations in118.306s, one method failure and seven error records.
Three errors are class-setup failures blocking20 declared methods; these are not
20 failed native executions. Five other records concern actual source methods.
All platform jobs are skipped, with zero artifacts, library Gradle, APK, native
execution or XML. Migration/audit/development scopes35/80/96 pass separately.

Original metadata/log archive were acquired **once**. Whole/member SHA256 custody
and exact job/run IDs are preserved in `original566/`. No archive contents are
executed, and no original log is downloaded again.

## Confirmed source root causes and related patch

1. `arm64_stop_candidate_source_projection.py::current_source_before_arm64_stop_candidate`
   admitted the newest Tooling562 bytes, then delegated their exact old stage.
   Nested `camera_recents_fixture_source_projection.py::current_source_before_recents_fixture`
   incorrectly repeated raw-current admission on that already peeled stage.
   Its strict rejection was correct for raw input, but the invocation domain was
   wrong. This blocked Camera205, console/CI213 setup, CI245 and terminal maps.
2. The busy-boot adapter did not peel the newer tooling source before comparing
   its unchanged old pin. Its round-trip test also compared the old stage's
   forward result to the newest actual file, rather than that stage.

The fix qualifies Tooling566 then Tooling562 **once at the actual checkout
boundary** in `android_external328_source_projection.py::current_source_for_history`.
Nested readers retain exact ancestor-only idempotence and their original dated
pins; no old input can masquerade as a new listed raw source. Busy-boot and two
round-trip controls now explicitly distinguish actual bytes from old stages.
Six modified tooling paths/11 exact reversible fragments/three source additions
are bound to complete own-Git beforeimages. No generic repinning or arbitrary
normalization is introduced. All observer test bodies/raw custody hashes,
production helpers, controller/Kotlin/native assertions, workflow, dependencies,
public APIs and historical manifests remain unchanged.

## Important verification and review

**Only15 NEW/failed/meaningfully changed source controls execute, all pass once**:
8 NEW controls; three Tooling562 affected cases; one busy round-trip; two failed
CI245 cases; one terminal-map case. Unittest4.789s, whole wrapper5.3493400879669935s.
Three blocked admissions are qualified via the original source setups/read-only
readers, **not** replaying their20 accepted class methods. The accepted camera009
C2/C3 and JVM8/APK evidence are reused on applicable unchanged inputs.

Solo review568 accepts35 passive custody/source/results checks with all1,326
local inputs held. `source-input-delta.json` reconstructs that map from the
historical1,320 compiler map: nine tooling deltas/six additions,1,311 inputs
unchanged. Against the immediately prior1,323 map there are six deltas/three
additions and1,317 unchanged. **Zero new compiler or native executions.** The
historical1,320 APK map is never relabeled1,326. The first incorrect compiler-map
count and scalar-AST parser refusals are retained; only passive review correction
occurs, without replaying accepted15.

## Required next acceptance and limits

Freeze/push the qualified batch on development, obtain fresh combined capacity
(max2 INCLUDING queued/reserved), and request only missing native C1. Require
actual Activity destruction/rebuilt owner, exactly one readable public result,
grants/descriptor/sibling safety, original native/scalar/master restoration and
owned app/AVD/emulator/transport cleanup before closing #13. Earlier actual
failures remain failed; no blind unchanged retry or camera009 C2/C3 replay.

#29/iOS runtime causes remain separate/unknown; no startup or geometry fix is
claimed here. No issue closure: observed103 closed/69 open/172 total; ledger22
implemented/36 partial/101 verified/five unresolved. SOLO, serial local/8GiB,
read-only Actions/all/no mandatory SHA pinning and all publication/Pages/main/
history/native/consumer/API–ABI/dependency/legal/security/readiness gates remain.
No release, package or deployment publication.
