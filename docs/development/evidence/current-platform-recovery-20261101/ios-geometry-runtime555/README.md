# iOS geometry runtime prerequisites failed — original555

Both immutable `afcc8076dd175e36a221b09b446f4213bc4c6bd1` originals are
**FAILED before library Gradle, Apple linking or native execution**:

| Original | Host | Actual bootstatus text | Subsequent capture failure |
|---|---|---|---|
| [41737269177](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41737269177) | iPhone | `Status=3, isTerminal=YES`, **Data Migration Failed** | `rustc --version --verbose`, TimeoutExpired60 s |
| [41737322523](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41737322523) | iPad | `Status=4294967295, isTerminal=YES`, **Finished** | `git status --porcelain --untracked-files=normal`, TimeoutExpired60 s |

Do **not** attribute the phone's migration or Rust failure to the tablet. The
host-specific timeout causes and the phone migration cause are unknown. Runner
resource pressure is only a hypothesis, not a measured root cause.

Shared tooling passed. Each run has24 original log members and one artifact
containing **only `ci-runtime/selection.json`**. Neither has actual library input
maps, a completed postboot runtime receipt, native XML or a library receipt.
The exact job step **“Fresh actual library suite with strict nonzero receipts”**
is skipped in both, as confirmed by the cached
[readback](NO-LIBRARY-EXECUTION-READBACK.json).1,313 frozen inputs describe own-Git
provenance only; they are not actual native maps or an executed library suite.

Preboot selection binds the own clean SHA, Darwin/Arm64, JDK17.0.21, Xcode26.6
and iOS26.5/iPhone Air or iPad mini A17 Pro. That receipt does not establish
postboot cleanliness, Booted/readiness, regular/compact traits or OS geometry.

## Exact source boundary

`.github/workflows/gradle.yml:519–538` selects the simulator, requests its boot,
waits with `simctl bootstatus`, then requires a new actual runtime receipt.
`scripts/ci/runtime_context.py:168–203` rechecks Git/toolchains **before** the
actual Booted-state check. Its `command:29–38` gives these Git/Rust commands60 s;
only the two allowlisted simulator inventory commands get180 s. Neither capture
reaches its completed actual receipt or the later library execution step.
No longer timeout, alternate simulator, “Finished means ready” rule, stale
selection substitution or skipped toolchain check is introduced here.

## Once-acquired review and retained refusals

Original archives remain in private custody; whole/member hashes and permanent
run/job/artifact IDs are archived here. Metadata/reviews are copied from the
cached originals, **not downloaded again**.

- Phone reviewer1 incorrectly assumed every artifact had a library receipt.
- Phone reviewer2 completed and saved the core review, then a console formatter
  requested absent `counts`. The completed review was reused, not rerun.
- Tablet reviewer1 incorrectly required the phone's Rust timeout. Its correction
  checks the actual tablet Git timeout against its cached original.

Both final reviews and the separate skipped-step readback remain. None of these
reviewer failures changes either original run to green.

## Next and limits

Investigate the actual simulator-startup and host-specific runtime-capture
boundaries before another geometry request. Any repair must preserve the own
selected simulator, clean SHA, exact compiler/SDK checks, finite budgets and
owned cleanup; diagnose returned state and cooperative resource pressure without
exporting arbitrary environment/transcripts. Do not redispatch unchanged failed
geometry inputs or replay accepted anchor/bar/native/compiler populations.

**#29 stays open** for genuine geometry/explicit traits and legitimate real split
view even after these two methods eventually pass. #13 remains separate.
No issue/comment/closure, Git/main, consumer/API–ABI/security/readiness, Pages or
publishing mutation occurs.103 closed/69 open/172 total remains. The two original
reservations are terminal; fresh all-status capacity must still precede any new
request. SOLO, max2 combined reservations INCLUDING queued, serial local/8 GiB,
read-only Actions/all/no mandatory SHA pinning and all release gates remain.
