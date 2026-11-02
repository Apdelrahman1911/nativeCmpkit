# JavaFX HTTP2Loader cancellation regression

This finite, genuine JavaFX test investigates the dependency beneath #64. It is
not a NativeCmpKit public-Stop, packaged-consumer or release acceptance substitute.
The patch is **nonactivated**: normal Gradle dependencies and shared caches remain
untouched. See [licensing and source provenance](NOTICE.md).

## Confirmed cause and correction

OpenJFX21.0.13 `HTTP2Loader.fwkCancel()` sets a volatile flag but never cancels
its pending `HttpClient` response future. Before response headers arrive there
is no body subscriber to notice the flag. The owned loopback peer therefore
remains connected even after the public Worker becomes `CANCELLED`.

The three-line patch cancels the existing future with `cancel(true)` after
setting the flag, preserving the invalid-URI/null-future path and native-callback
suppression. JDK17's cancellation can complete a dependent future normally;
`isCancelled()` is not a reliable connection-release oracle. Real peer EOF and
same-engine recovery are required instead.

Four finite scenarios use retained WebViews in an owned visible Stage:

1. **zero-header:** no server OutputStream; real EOF before server cleanup.
2. **plain-body:** actual native parsed title from an incomplete response.
3. **gzip-body:** actual native parsed title from an incomplete SYNC_FLUSH body,
   without a gzip trailer or forced response completion.
4. **concurrent:** three repeated idle cancellations, an independent pending
   engine that genuinely succeeds, then same-engine recovery.

Every case requires exactly one actual cancellation transition, genuine EOF
before fixture teardown and a successful same-engine request. The whole process
must exit0 after peer, Stage and toolkit cleanup; a printed success prefix is
insufficient. No private route property, reflection or fake peer EOF is used.
Thread waits and JavaFX queue waits are bounded; this is not heap/native-leak,
hard-preemption, hostile-process or all-network-protocol certification.

## Important results

**2026-11-02, subsequent private library-candidate preparation:**
[273–282](../../../docs/development/evidence/current-platform-recovery-20261101/javafx-full-candidate273-282/README.md)
adds `build_runtime_candidate.py` and an **explicitly loaded, one-task-only** init
script. The identified full-JAR candidate replaces the sole original web JAR for
only the failed original Windows library Stop method; it never changes normal
dependencies.27 new controls pass as21+5+1, packaging and corrected Gradle dry-run
pass, **zero new native/library executions**. Do not replay the accepted four
dependency cases to test this new library route. See
[ADR0013](../../../docs/decisions/0013-private-javafx-cancellation-candidate.md)
for complete native-source/legal/security/consumer/API-ABI and adoption gates.

**2026-11-02:** [Saved Windows270 and solo source/results review271](../../../docs/development/evidence/current-platform-recovery-20261101/javafx-cancel262-271/README.md)
now qualify **4/4 Windows dependency scenarios**, process0/6.813s on
Temurin17.0.20.1+1. Eleven source/JAR and ten reported compiled-class hashes
match exact Git/pins/independently retained Linux bytes. No actual binary or
independent after-map is uploaded. This is **zero NativeCmpKit library methods**;
the patch remains nonactivated. Both accepted Linux and Windows populations must
be reused, not replayed. The earlier missing-Windows wording below is historical.

The original Linux unmodified-JAR baseline failed once at real peerEOF0 with
responseBytes0. The exact private module patch subsequently passed **4/4 in
3.5332s**, with same-engine recovery and whole-process exit0. All source/JAR and
compiled-probe/patch hashes held. Member descriptors stayed identical; after
constant-pool index normalization only `fwkCancel` changed, and all four generated
inner classes remained identical. The missing AT-SPI bus warning is retained.

That result is dependency-level Linux evidence, not a retrospective explanation
of the unobserved loader instance in the failed Windows NativeCmpKit run.
Reuse it; do not rerun unchanged accepted Linux cases. The manual read-only
workflow selects missing Windows cases independently, without full Gradle
rebuilds or replay of the accepted iOS/browser/library populations.

## Reproduction of missing/changed cases only

JDK17, Python3.12 and a graphical host are required. Linux additionally needs
Xvfb/GTK; the runner's pinned classifiers currently cover Linux x64 and Windows
x64 only. Select a new owned output directory; existing results refuse overwrite.

```sh
# Offline synthetic runner guards; zero JavaFX/native/library executions.
python -B -m unittest discover -s tests/dependency/javafx-http2-cancellation -p 'test_*.py' -v

# Example only: changed/unseen population on a Windows host, not accepted270 replay.
python -B tests/dependency/javafx-http2-cancellation/probe_runner.py \
  --download --cases all --output build/javafx-dependency-regression

# Failed-only selection after an owning source/fixture correction:
# --cases gzip-body --output build/javafx-dependency-regression-next
```

`--download` obtains only fixed official Maven files and verifies exact bytes
and SHA256. An already acquired artifact directory may be supplied with
`--artifact-dir`; changed files fail without replacement. No classes/results
are cached as successful verification. Same-registry checksums are integrity
pins, not independent dependency-security/signing acceptance.

The inactive-for-library-builds workflow is
`.github/workflows/javafx-dependency-regression.yml`, development-branch only.
It also runs the missing Windows population on a push changing the exact probe,
patch or dependency-manifest bytes; documentation/runner-only changes do not
automatically replay native cases. This registers the new workflow without a
`main` change. It uses one hosted-heavy reservation, contents-read token, no stored checkout
credentials, no publishing/deployment/OIDC permissions. Uploads contain selected
test evidence only, never JARs or classes. Observe the project-wide maximum two
combined queued/running/reserved hosted-heavy jobs before dispatch.
Checkout preserves LF bytes, enables Git long paths before checkout and fetches
only this dependency-test subtree. Archived XML and the full Kotlin build are not
required by this diagnostic and are not checked out or claimed as verified.
