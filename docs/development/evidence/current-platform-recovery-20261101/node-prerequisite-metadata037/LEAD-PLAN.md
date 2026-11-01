# Minimal Node prerequisite — lead-run procedure, not admitted or executed

Original U1 `U1-f0db3fb734b3364e` remains FAILED / STOP AND REVIEW
(Gradle 1 / 53.01 s). Its graph, gate action and sentinel receipts are still absent.
This plan does not retry U1, enable U2/U3, replay U4 or make #40 releasable.

## What the current investigation establishes

Only these two distinct official HTTPS resources were acquired, once each:

- `https://nodejs.org/dist/v24.16.0/SHASUMS256.txt`
- `https://nodejs.org/dist/v24.16.0/SHASUMS256.txt.asc`

Both returned HTTP 200 with TLS peer/hostname verification and curl result 0.
The client required HTTPS, nodejs.org, TLS 1.2–1.3, no redirects/proxy/auth/cookies,
5 s connect / 15 s total per transfer and captured body/header caps of
64 KiB / 8 KiB. Receipt-local elapsed times are 0.514623 s and 0.512512 s.
Those are metadata-client bounds, not OS containment, TLS wire-byte or RSS proof.

The retained checksum text has 32 literal entries and advertises, exactly once:

- archive: `node-v24.16.0-linux-x64.tar.gz`
- **advertised, NOT authenticated** SHA256:
  `2faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff`

The clear-signed metadata structurally contains the same checksum text, excluding
one exact armor-separator newline. Its armor CRC matches. Its signature packet
self-asserts fingerprint `5BE8A3F6C8A5C01D106C0AD820B1A390B168D356`
and key ID `20B1A390B168D356`. **No signature was cryptographically verified,
no trusted key/chain was supplied, and no key was acquired/imported.** Neither TLS,
CRC, packet fields nor plaintext equality establishes release signer ownership.

Original parser refusals remain retained: the basename-only checksum reader
rejected eight observed official Windows relative names; a separate exact-name
reader recovered against the same body. The first signature comparator included
the armor separator; a separate reader accounts for exactly one extra newline.
No body mutation or metadata reacquisition followed either correction.

## Source-bound minimum

For the held Linux/x86_64 platform, the original KGP 2.4.20 bytes derive
`org.nodejs:node:24.16.0:linux-x64@tar.gz` and the intended official archive URL.
The original U1 log observed only the unclassified module and offline cache miss;
the platform-specific archive URL remains source-derived, not an archive response.

`AbstractSetupTask.kt:93–98` resolves the distribution classpath from a
configuration before setup actions. The onlyIf predicate at line 111 checks
download, not installation presence. Even the up-to-date marker path hashes the
archive at line 214. A preinstalled Node executable or manufactured
`node-v24.16.0-linux-x64.hash` cannot supply this prerequisite.

Setup extraction is unnecessary for cache readiness: lines 158–180 may delete
the destination, extract and write a sibling marker containing directory/archive
hashes. `NodeJsSetupTask.kt:39–46` preserves the archive root while copying to
the destination parent; symlink repair and executable mutation follow.
**Do not run KGP setup, extract the archive or execute Node for this task.**

Current static Gradle 9.7.1 cache sources show content-addressed artifact storage
plus repository-keyed module/artifact indexes and serialized descriptors written
through normal locked cache paths. The internal file-store key is SHA1, not
release authentication. An archive file alone, an invented descriptor, a manual
cache directory or copied binary index is not an offline resolver proof.

The standalone blueprint preserves the KGP repository name, official HTTPS URL,
exact artifact pattern, artifact-only metadata sources, exact module filter and
default non-M2-compatible pattern layout. Do not add Ivy/POM patterns,
`file://` repositories, mirrors or checksum/trust exemptions. Gradle's pattern
layout derives Ivy resource patterns from the artifact pattern when none are
explicit, even with artifact-only metadata; inventing a second pattern changes
repository identity inputs. The actual runtime repository ID is unobserved.

The extra Gradle core/dependency-management jars are **new current static inputs**,
not additions to the original six-runtime identity freeze. See source bindings.
The original 52-file source digest remains
`614c361b7a1d86b7345e648abaea064186d3c5f1a79118f870b9d60cbac72b9e`.
Byte decoding and template readbacks are not compiled tests.

## Smallest reversible procedure — future lead-owned stages

1. **Authenticate first.** Obtain separately reviewed signer key bytes and an
   independent ownership/authorization anchor. Bind key/tool hashes, the full
   signing fingerprint, primary/subkey association, validity/revocation policy
   and exact release. Verify the retained clear-signed file cryptographically
   using an admitted offline verifier in a fresh owned verification home, without
   keyserver retrieval or global keyring/trust mutation. Bind the verified
   cleartext to the retained checksum text and the exact archive entry.
   Self-asserted issuer fields and a success exit without matching identity are
   insufficient. This input is currently MISSING.

2. **Admit a fresh exclusive disposable root/home.** Freeze runtime identities,
   inert template hashes, actual trust proof and finite request/control policy.
   Keep every writable HOME, Gradle user home, project cache, project and result
   path inside that owned root. Use the held existing launcher/JDK only after
   normal runtime admission; do not run a wrapper that downloads Gradle.
   Check the local heavy lane is free and at least 8 GiB disk reserve remains.
   No original/global Gradle cache is populated or copied.

3. **Normal resolver acquisition only.** Materialize the `.in` blueprints only
   after admission. Both XML and code placeholders must be rendered from the
   independently authenticated proof, never from the advertised checksum alone.
   Execute one plugin-free standalone `resolvePinnedNodeArchive` task online
   under strict dependency verification and an admitted bounded network/process
   harness. The proposed archive ceiling is 128 MiB, not a known archive size;
   oversize or any unexpected route must refuse, not widen scope automatically.
   The blueprint declares one exact component/artifact, but actual resolver
   HEAD/GET/checksum auxiliary operations have NOT been observed or certified.
   A finite host/method/path allowlist, TLS/redirect/download-byte/time control
   and full child ownership must be supplied before this stage. A CLI timeout
   and --no-daemon alone do not provide those controls. Configuration-script
   compilation, resolver operations and cache writes would be new executions,
   not U1, a library/native build or current evidence.

4. **Separate genuine offline probe.** After verified first-child shutdown,
   execute the same frozen standalone task with `--offline`, the same private
   home/repository definition and strict verification. Admit only a real exit 0,
   exactly one resolved pinned artifact with matching authenticated bytes,
   an actual offline scalar receipt and external proof of no network activity.
   Retain archive identity, normal repository-specific cache origin, both bounded
   child outcomes and owned cleanup. No classpath substitution or cache editing.
   The blueprint emits only safe scalars, but raw Gradle/control outputs remain
   private. Neither stage has run.

5. **Decide the later U1-home bridge separately.** A passing private cache probe
   makes only that private home ready for this exact Node-only resolution.
   It does NOT repair the original bound U1 home or prove the other plugin/runtime
   prerequisites available there. Do not copy private binary indexes into global
   caches or use a private home in the original U1 without a separately reviewed
   composition/admission decision and frozen proof. Original global-home mutation
   and any new U1 ID/retry remain unauthorized by this packet.

6. **Rollback only owned state.** Retain evidence outside the disposable runtime
   tree before cleanup. Verify all owned launcher/daemon/descendant processes are
   gone and retain bounded identity readback; then remove only the exclusively
   owned tree through the lead's admitted ownership/FD-confined cleanup path.
   Any uncertain child/path/cleanup state is quarantined; do not send broad
   signals or delete another cache. Fresh-root use makes filesystem rollback
   local, not atomic or proof against arbitrary concurrent writers.

## Exact missing inputs and preserved unknowns

- Trusted signer key/authorization anchor and actual signature verification.
- Actual archive response/bytes/size/hash and authenticated provenance binding.
- Admitted isolated-root runtime, finite resolver network policy and bound controls.
- Actual normal repository-specific cache installation and offline proof.
- Complete owned descendant shutdown/cleanup and a later U1-home bridge decision.
- Completeness of future dependency planning after this first missing prerequisite.

All `.in`/`.proposal` files are inert, not compiled or materialized, and contain
missing authenticated inputs. Original U1 network containment, RSS, bounds and
complete detached/composite cleanup remain null. No global cache/live source/trust
edit, archive download, Node/setup/Gradle/build/test execution, U1 retry, U2/U3 or
U4 replay occurred in this investigation. #40 remains open; ordinary adoption,
dependency/security/legal/native/consumer/API-ABI/readiness/publishing/Pages/
main/history gates are unchanged.

