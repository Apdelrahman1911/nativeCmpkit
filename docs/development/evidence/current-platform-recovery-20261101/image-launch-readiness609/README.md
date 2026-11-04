# Image609 — owned-app prelaunch observations, not a launch fix

2026-11-04; isolated `development/batch-image-launch-readiness-20261104`
from `c8b07d046ffbc9b303ffcf3599fc6715c53f9285`. **#141 remains open.**
Integration and dispatch are **HOLD**, pending the lead's independent finite
batch and a separate exact launcher-history ingress qualification. This patch
does not make an unchanged original-profile retry appropriate.

## Scoped source change

Two NEW tooling files provide bounded observations and synthetic controls.
The sole existing change is one ten-line hook in `ios_ui_application.py`,
after the SDK-only return, only for the existing `calf-ui` profile-recovery focus.
Removing that hook restores the entire base launcher, including its original
argv, 360-second profile deadline and complete `finally`. No production, native,
signing, profile driver, build, workflow, selector, dependency or API bytes change.

The helper observes only the already-owned installation and one exact
`simctl appinfo <selected UUID> <current owned bundle>` query. It uses the
unchanged pinned help/tool/context guards and capture controls: 15 seconds per
command, 128 KiB combined capture and a cooperative 90-second observation budget.
One exclusive sanitized record is latched before tool resolution/query; there
is no query retry, inventory, standalone CLI or permission remediation.

Complete source-defined JSON, ASCII/XML plist and `bplist00` grammar matches
describe compatible **byte syntax**, not the SDK's actual serializer or
registration schema. Duplicate pairs are retained; only fixed counts/types and
the three existing own-plist names are summarized. Unknown keys, values and
paths are not exported. `{}` matches two grammars and remains ambiguous.
No absence, registered-path, semantic-field or root-cause claim follows.

The executable observer requires the original installed byte/type guard,
a regular unshared no-follow descriptor, two bounded hash reads and matching
before/after file/directory identity. Mode and host real-ID `X_OK` are observed
without chmod. **Host `X_OK` is not simulator executable acceptance.** A stable
negative result does not suppress the original launch. Query/schema/tool/resource
unavailability stays diagnostic; only positive identity drift or failure of the
original installed ownership guard may refuse before launching unowned bytes.
Private output is removed only after exact owned identity/membership checks;
foreign membership is preserved and cleanup refusal retained.

## Once-executed NEW controls; unchanged results not replayed

[`IMPORTANT609-FIRST.json`](IMPORTANT609-FIRST.json): **NEW18/18 passed once**,
0 failures/errors/skips, **0.1543111139908433 seconds**. Six complete-structure,
eight owned-query/access/identity/privacy and four recovery-hook controls were
selected. Every real subprocess boundary was denied: **0 attempted**. The older
transport class supplies synthetic fixture helpers with `methodName="runTest"`;
none of its accepted test methods was selected.

There were **zero** new SDK, Apple/native, Gradle/compiler, profiling, network
or GitHub executions. Accepted nine UIImage methods, original 20-GC and two
stress methods are reuse-only; ASan is not an original UI-038 requirement.
Three source-review corrections preceded the first execution: handling
`ET.ParseError`, validating owned context before executable observation, and
removing a shadowed mock assertion. They are not fabricated red executions.

[`SOURCE-REVIEW609.json`](SOURCE-REVIEW609.json) records **28 final passive checks**,
hash/AST/current-map inspection and cached-original reads only. The precheck's
1,340 base Git-blob checks are reused, not reexecuted. All **1,342** current file
digests still match the NEW18 before/after maps: one existing change, two additions,
**1,339 other existing inputs unchanged**. Held digest:
`a25f13e42dc11e83d32cbb4b5a0c1bf78739bd0269492e22d646d44f56f5cefd`.
This is not a compiler or native input-map receipt. The initial missing Python
alias, oversized metadata printer and incorrect outer SDK-key printer are
retained as passive-review refusals, not test/native failures or new downloads.

## Original evidence remains failed/limited

- Original **41242777493**, `7380a04674c2dc83583a45953418ec2c823b4258`:
  console exit 1 after 2.46 seconds, no PID/activation/Worker/native execution,
  no profile command; fixed `NSOSStatusErrorDomain -10814` and service-delegate
  denial do not establish a cause. Actual full argv and installed access/registered
  path were not observed. The original failure is neither waived nor replayed.
- SDK-only **41696878178**, `dd614a75bba7dda1678f7a0cfcf97943697db92f`:
  accepted one query exit 0, stdout 1,218 bytes and empty stderr. Raw bytes were
  removed; they are not reconstructed/reparsed from lexical counts. Serializer,
  registration, launch, native and profiling acceptance remain absent.
- Pinned help `actual006` certifies exact syntax/tool identity only. The cached
  receipt hashes for all three inputs are preserved in the source review.

## Required separate ingress and actual native gates

[`FRAGMENT609.json`](FRAGMENT609.json) contains one unique reversible insertion,
whole before/after hashes and a verified complete round-trip. Launcher SHA256:

- Before: `4e407426bc8535ea547eb5fbee74f7a801c87f222add88de94e26966f65690ae`
- After: `5cd8bc716484a7f1b1f65e41d0832e3855825d505dc78b24e7602980c4a8cee3`

**No historical reader was changed or executed here.** The lead must qualify an
exact complete new-postimage peel ahead of unchanged anchor/completion/repeat/
worker/modal launcher pins; refreshing old pins or admitting arbitrary historical
or drifted bytes is not acceptable. The fragment is evidence, not certification
of current hosted tooling. See [`CI-PROPOSAL609.json`](CI-PROPOSAL609.json).

Any subsequent lead-approved actual attempt must preserve fresh capacity
(maximum two combined hosted-heavy reservations INCLUDING queued/reserved work),
serial local heavy work and at least 8 GiB free. The sole existing method remains
`UIImageMemoryDiagnosticsTest.actualLibraryConversionsRemainBoundedDuringOwnedAllocationProfile`
under `ios-image-profile-recovery` / `ios-iphone` /
`ios-native-image-allocation-profile-recovery`.

Actual owned PID/activation/Worker/native XML/runtime agreement, target-bound
useful allocation exports, same-PID zero leaks, original signed/plist/input
custody and independent owned cleanup remain required. All native, consumer,
API–ABI, dependency, legal, security, publication and release-readiness gates
remain; **no issue closure, publication, push or CI dispatch** occurs here.
