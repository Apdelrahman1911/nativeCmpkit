# Exact official Node archive authenticated and passively inventoried

One GET of https://nodejs.org/dist/v24.16.0/node-v24.16.0-linux-x64.tar.gz succeeds:
HTTP200 / curl0 / verified ordinary TLS / redirects0 / retries0.

Archive 57,023,429 bytes; SHA256
2faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff.
Matches accepted canonical-vendor-HTTPS/GPG checksum proof, manifest
84e1bcb2fba6489b94d5c1645b4db63c76ab7faeb1a52755b4d32e90689a8fb9, reused without
signature/source/key/checksum reacquisition. TRUST_UNDEFINED remains; no personal
WOT, complete historical revocation or trusted-timestamp claim.

One bounded passive inventory passes:
- 200,417,280 expanded bytes.
- 6,668 raw headers including 939 GNU name extensions.
- 5,729 filesystem members: 4,661 regular / 1,065 directory / 3 symlink.
Every member is unique under the sole expected root; all parents are explicit
directories. All three relative links resolve to existing regular members inside
that root. No traversal, dangling target, resolution cycle, special/sparse/global-
PAX/unsupported/privileged member. Single gzip CRC/ISIZE/exact EOF and complete
block-aligned tar termination verified. Caps100 MiB archive/600 MiB expanded/
20,000 raw headers. 41 fresh in-memory controls pass:5 positive/36 refusal, not
runtime tests. Original local disk-reserve refusal before any GET is retained;
disk-backed private staging then chosen before the only GET.8 GiB reserve remains.

No extraction, downloaded code execution, cache seeding, Gradle/Node/U1/U2/U3/U4,
global/source/Git/GitHub mutation or issue closure. Archive authentication/inventory
is not genuine resolver indexes/descriptors/cache/offline readiness or code/legal/
security/release clearance. Original U1 stays FAILED with graph/gate/sentinel
acceptance absent and original network/RSS/full detached-cleanup controls null.
#40/all original gates stay open; the lead owns future resolver/U1 decisions.

Original archive/headers/client outputs/full names/member hashes/links stay only
in a separate private seal. This public derivative has scalars/hashes/scope, no
raw payloads, machine paths or transcripts. Source files0400; lead imports0644.
