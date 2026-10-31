# Apple help-only capture — owning process-control repair

[Actual 41250396548](../apple-appinfo-capability-20261031/native-ci002/README.md)
remains **failed**, helper **2 / 17.72 s**, `owned_control_leader_unavailable`.
Six preceding identity commands succeeded. Help completion, exit/output/support
and the TERM-versus-KILL phase remain unknown; no launch cause is inferred.

Only `stop`, `capture` and nested `collect.call` change. On missing owner/group,
an exact retained-Popen bounded wait plus absent-group readback is required;
unknown exit/live or reused group refuses. No nonzero signal follows wait/reaping.
A latch permits one stop attempt, including refusal. Bounded partial output
metadata is recorded before re-raising the original refusal: even exit0/Usage
cannot make partial capture a successful help or profile observation.

**14 new mock-only guards pass**, reused on exact integrated postimages; six
preimage reds remain archived. Independent source review found no new unsafe
after-reap signal or partial-green branch. Because the owning implementation
changed, exactly **three affected existing Linux synthetic-child regressions**
were freshly run: **3/3, exit0 / 1.4061 s**, held1023 inputs. No other accepted
models, app, SDK, Darwin or library test was replayed.

The same four source identities, six fixed identity tuples and one
`xcrun simctl help appinfo` tuple remain. Capture limits remain15s/128KiB per
command,90s/512KiB total, plus existing bounded cleanup; five-minute/read-only
job and receipt-only upload are unchanged. No simulator inventory, payload query,
boot/install/launch/profile or timeout expansion is added.

**#141 remains open.** Only this unchanged help-only verification is a valid
next request. Source/models/Linux children are not Darwin native cleanup or
Instruments/leaks acceptance. Prior startup/timeout/pre-PID failures remain failed,
unfixed/unwaived. EOF-based file reads and detached-child/native ownership limits
remain disclosed; no security/readiness/publication authorization follows.
