# Independent Android actual001 review

## Immutable request and acquisition

- Run **41273057295**, attempt **1**, profile `android-webview-request-state`, branch `development/preview-hardening`, commit `5705781330ba97fc86ba6faa748c70e35879b9bf`.
- Terminal completion is **FAILED**, 2026-11-01T04:35:42Z. Tooling succeeds; the only library job, API35 / `calf-webview`, fails step 17. Unselected consumer, sample and Apple jobs remain skipped.
- Terminal run/jobs/artifact metadata, the sole report ZIP, and only the relevant library-job log were acquired **once after completion**. Status cycles were at least 60 seconds apart. No all-run logs, dispatch, mutations, Git commands, builds, models or native replay were performed by this reviewer.
- Artifact **13069804923**, `library-evidence-android-device-api35`, is exactly **229,799 bytes**, SHA256 `7cf321cce8f7df0491944d75e2f69b208f04c3075d8ce40c33366043f9666698`. Metadata size/digest, run/SHA/branch, upload-step window, 19-member ZIP confinement/types/duplicates/links/modes/sizes and every member digest are verified.

## Original results, not reconstructed acceptance

| Original stage | Result | Boundary |
|---|---:|---|
| APK assembly | 0 / 342.09 s | Source-bound assembly only; individual compiler-task freshness and APK/signer bytes are not archived here. |
| Owned AVD creation | 0 / 2.00 s | Source-owned setup, not a method execution. |
| Connected Gradle command | 1 / 41.01 s | Owning selector refusal before runtime marker/UTP transport. |
| Native cases / XML | 0 / 0 | Both required methods remain unexecuted; no XML was reconstructed. |
| Owned emulator exit | 0, graceful, not forced | Original controller records clean engine exit; do not infer unarchived app uninstall or post-shutdown ADB-table absence. |

The exact required methods are:

1. `com.mohamedrejeb.calf.ui.web.AndroidWebViewRequestStateDeviceTest#twoHeldNativeTransportFailuresResetErrorsAndNativeReloadUsesCurrentOwnerUrl`
2. `com.mohamedrejeb.calf.ui.web.AndroidWebViewRequestStateDeviceTest#publicNavigatorStopClosesHeldTransportAndActual302RedirectReloadUsesCurrentOwner`

The original command requests those two methods as one comma-containing `class` value. Frozen `library_tests.py` emits that value at lines 1013–1014 / 3296–3300. Frozen `fresh-tests.init.gradle.kts` lines 61–68 refuse comma-containing selectors before its runtime marker and UTP action. The private relevant terminal log matches the fixed owning guard message five times; these are rendered repetitions of the same task refusal, **not five native failures**. Actual ATE selector truncation/data loss did not run and is not diagnosed. The guard and all original assertions are preserved; this review supplies no patch.

The original receipt has marker 0, totals 0, no reports, and the original three collector errors: missing exact fresh marker, missing the exact two-method XML selection, and no actual non-skipped cases. Both selected actual/declared report trees are existing, complete and empty. All 18 admitted output inventories are complete/empty, and the ZIP has no XML. There is no one-method partial acceptance.

## Source and fresh command windows

All four original actual maps are byte-identical **1,101-file library maps**, raw SHA256 `c1f1c280f297de1dc961251f575a39cf238b960d4b843595831685b67e0c9afa`. Their canonical input digest is `55cd36afda6bcb4cb0caa2d610ac19d9b02eea2ecd1012d1f46e8a0c01005064`. They match the frozen map, clean unchanged actual revision, and independent immutable Git tree/blob hashing. The **1,178-file combined map is frozen, not an uploaded actual combined map**. Every frozen combined input is independently checked against the untruncated tree `45e49e880056865eee7e56caa1d0c894f631fcbf`; 43 private review sources are independently bound, with no fallback/mismatch.

The two bodies are reviewed as **source, not runtime success**: real forwarded callback/generation/current-owner observations; held zero-response fail/fail and metadata/error reset; distinct no-store DOM at the current-URL Reload; public Stop requiring pre-cleanup peer EOF; actual 302/Location destination and final-URL Reload; exact acquired socket-route leases; native unmount while the Activity remains resumed before server disposal. Normal production callbacks and original source bodies are unchanged by this review. Accepted identity/lifetime/popup/camera/IO methods remain unselected and are not replayed.

The connected **command** window is `2026-11-01T04:34:49.963550+00:00`–`2026-11-01T04:35:30.974064+00:00`. Original controller, launch, runtime, command, shutdown, diagnostic and artifact-upload windows are timezone-aware and ordered. Diagnostic render timestamps occur after the command and are **not original failure timestamps**. ZIP/extraction timestamps are not used as original native/report freshness. No native execution interval is fabricated.

## Runtime and ownership boundary

Original boot, library runtime and after-command emulator identity are equal: API35, Android15, x86_64, Enforcing, boot complete, exact source-owned serial. Original controller plan/launch AVD name and serial match; ownership is the recorded Popen child, not a guessed process. Actual root daemon observation is Gradle9.7.1 / JDK17.0.21 with the existing launcher/daemon match assertions satisfied.

The original engine shutdown is graceful exit0, not forced, under the unchanged exact-owner check. No UTP app-install or app-uninstall witness and no explicit post-shutdown ADB table are archived for this profile. Do not promote these missing observations or source-level network/DOM/Stop assertions to runtime success.

## Safe delivery and remaining gates

`originals/` contains unchanged, individually reviewed safe original JSON. Four identical actual input maps and any identical source plan are explicitly deduplicated by original bytes/hashes in `ARTIFACT.json`; no map is relabeled as combined. The original diagnostic member contains log material/private runtime strings and is **not copied raw**: `FAILURE-DIAGNOSTICS.sanitized.json` retains bounded inventories, original member/log hashes and explicitly hashed omitted tails/excerpts. Raw job/Gradle/emulator logs, terminal transcripts, private command paths, apps and signing material are not delivered. Original ZIP and raw diagnostic/log material remain private. There is **no original XML** to publish or reconstruct.

The independent evidence validations in `REVIEW.json` are receipt/source/inventory checks, **not newly executed CI models or native tests**. **ZERO native methods accepted, ZERO whole-issue closures, #64 remains open.** Any further exact two-method recovery needs lead-owned owning-selector integration/freeze and its own immutable request; this review authorizes none. DNS/TLS/offline, other targets/minimum/physical, consumer/ABI/dependency/legal/security/readiness and publishing/Pages/main/history gates are unchanged.
