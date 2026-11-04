# UI drag / shader related patch — 2026-11-04

Independent branch `development/batch-ui-drag-shader-20261104`; base
`1ae35d7d0f55724665b168f1b18696198e5b8978`. The lead alone integrates, pushes,
dispatches and accepts native evidence or closes issues.

## Source-confirmed current gaps and narrow fixes

- **DampedDragAnimation modifier callbacks:** cancelling synchronously from
  `onDragStarted` was followed by unconditional `press()`; cancelling inside
  `onDragStopped` was followed by unconditional delayed `release()`. Disposing
  the helper could also leave an older pointer session able to invoke later
  business callbacks. A cancellation generation now qualifies current-session
  start/drag/end/cancel/finally work; cancel clears only owned Job references.
  New pointer sessions and public programmatic use remain reusable. No animation,
  velocity algorithm, range, toolchain or dependency rewrite.
- **InteractiveHighlight terminal disposal:** a retained gesture node could
  restart feedback after disposal. Its prior non-state disposed flag did not
  invalidate drawing, and a null shader could become a flat fallback draw while
  old press state remained. Snapshot disposal invalidates the draw, feedback/
  gestures and exposed offset/progress; native ownership is cleared before close.
  Sibling resources/scopes remain independently owned. Lazy construction and
  per-draw temporary Shader closure remain unchanged.
- **Actual button evidence:** an optional internal composition-local observer
  observes the actual remembered `InteractiveHighlight` constructor used by
  public `LiquidGlassButton`, with no factory substitution, public signature,
  layout, gesture, effect or default behavior change. The null default does no
  observing. It supports the original 100-button trace criterion rather than
  repeating the accepted 100-standalone-helper scenario.

Original three preimages are retained here. Original eight
`DragAnimationAndHighlightTest` bodies and all attribution are unchanged. The
six [new scenarios, finite compiler command and remaining criteria](../../testing/ui-drag-shader-lifecycle.md)
are separate from accepted history.

## Verification status

- 23 initial passive source assertions qualify the six exact enabled method
  declarations/owned host, preserved original eight, public constructor source,
  attribution and isolated source admission. These are **not library tests**.
- The first actual bounded offline/JDK17 Gradle command fails before production
  or test compilation: **exit1 /14.003650535s wrapper /13s Gradle**. Its new init
  admitted task names before excluding unrelated included plugin builds, so
  foojay settings resolution exposed that guard refusal. Original
  `compiler.log`, `compiler-run.json`, both input maps and first runner are
  retained. The first refused init is restored with the exact inverse fragment
  and certified against the original held SHA256, not described as a pre-run
  copy. No source-admission JSON, KLIB/native tests or Apple links existed for
  that first attempt.
- The narrow recovery moves actual `:calf-ui` ownership admission before the
  main task check. Only this init hash changes in the 232-input inventory; all
  production sources, six authored bodies and toolchain hashes are held. Two
  changed-init passive assertions pass; they do not prove the loader works.
- Separately lead-granted recovery1 **passes exit0 /205.179449488s wrapper
  /3m23s Gradle**. Actual UI production and exact seven-source test compiler
  execute; unchanged core compilation is expressly `FROM-CACHE`, not replayed
  execution. The precompiler JSON confirms seven exact sources/common empty and
  all hashes match the held map. The two actual unpacked UI KLIB output trees
  exist with fresh file timestamps and recorded hashes; no assumption about a
  `.klib`-named regular file supplies that evidence.
- All 232 inventory input hashes are held before/after both attempts; only the
  init changes between attempts. Recovery's continuous one-second disk samples
  remain at least 9,808,285,696 bytes free, above the 8 GiB minimum, with no
  timeout/disk stop. Original command/guards/maps/logs are retained separately.
- 23 final passive custody/log/source/artifact assertions pass; all 21 warning
  lines (17 existing production /four host-native) remain in the original log.
  No authored-source compiler diagnostic is hidden or relaxed. These checks
  are not new native library tests.
- The first complete staged whitespace check flags three original producer
  spaces (both Gradle daemon lines and the empty precompiler common-source
  array). Their original bytes stay. This packet's isolated `.gitattributes`
  preserves every archive's checkout bytes and exempts **only those three
  producer files and their lossless quoted refusal** from whitespace, not
  authored Kotlin/init/docs. The owning
  whitespace check then passes; no shared/root policy is changed.
- A later live-daemon observation refuses the single-owning-runner selector;
  the cardinality/cause was not recorded and no live executable claim is made.
  The actual JDK17 launcher/release hashes and root `toolchainVersion=17` are
  recorded, not substituted for an accepted live-daemon witness. No unchanged
  compiler retry follows this refusal.

The input inventory includes 122 ordinary production-chain candidates, seven
selected test files, 102 repository configuration candidates and the new init.
That broad configuration inventory includes unselected init/consumer scripts;
it **does not** assert all candidates evaluated or compiled. Only exact effective
source admission and original Gradle task states decide actual compiler evidence.
The first raw map's "evaluated configuration" wording is corrected here and in
later capture metadata without rewriting its original bytes.

No Apple link, native library test, hardware/Instruments, consumer or API/ABI
acceptance has executed for this patch.

See [receipt.json](receipt.json), original failure/recovery logs and maps,
`compiler-recovery1-focused-compilation.json`,
`klib-artifact-hashes.json`, and `final-passive-review.json`. Original historical
eight-body observations remain historical, not a fresh pass against this changed
production source. The six newly compiled methods still require native execution.

#142 and #162 remain open for the original unverified runtime/performance/effects
criteria. No issue mutation, CI dispatch, release, package, deployment, Pages,
main/history or policy change is part of this agent's isolated patch.
