# Owned disk reserve recovery — 2026-11-04

These are storage operations, not test, runtime or release evidence. Neither
operation stopped processes or removed source, Git/history, SDKs, dependency
caches, unrelated projects, KLIBs/APKs/XMLs/native outcomes or original receipts.

## 695: archive-identical generated backing copies

Only 190 ignored, single-link `compileSync` copies sized 64KiB–less than1MiB
were discarded. Their complete bytes and modes matched 142 independently read
members of the original immutable archive690; all original identities were
verified immediately before removal. **72,867,381 bytes remain preserved** in
that archive. Its complete SHA256 is
`5522c86971f7e494f0b1e31eb7d767652692301a80d00252938968a1a15f9193`.
The full original archive/inventory and recovery driver remain locally under
`/root/nativecmpkit-disposable-archives-20261104/`; no archive is published.

## 696: dormant owned documentation verifier environment

The ignored `build/docs-verification/locked-002/venv` had no observed live command
using its path. Its **20,901 entries**, regular-file bytes, modes and symlink
targets were archived without following links or extracting anything. Every
archive member and each original identity/hash were checked before discarding
the dormant environment. Original verifier logs and receipts stayed untouched.

The retained 37,296,819-byte archive has SHA256
`66e9684ee7edbe1804b08ed4c9216cc987576143b49754d68ae806f50a1887ef`;
the original inventory has SHA256
`9dc71750bf254587f0d9242ec723ba73333bc4ebe9036da9fb67d4bfaace7e60`.
Both are private local preservation material under
`/root/nativecmpkit-disposable-archives-20261104/dormant-docs-venv696/`, not
redistributed package contents. To run a future check that specifically requires
this exact dormant verifier runtime, restore only its validated original target
from that authenticated archive; do not assume the environment still exists.

Free disk was freshly 8,682,213,376 bytes at subsequent CI668 adoption admission.
This is a point-in-time observation, not a promise that space remains available.
Keep the 8GiB reserve and inspect current resources before heavy work. The local
archives and original inventory/verification receipts must not be pruned or the
once-only recovery scripts replayed.
