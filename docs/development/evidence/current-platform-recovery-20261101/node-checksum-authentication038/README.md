# Node v24.16.0 checksum signature authenticated — vendor HTTPS trust

The original retained signed metadata now passes **one actual GPG verification**:
GnuPG 2.4.4, exit 0, VALIDSIG full signing/primary fingerprint
`5BE8A3F6C8A5C01D106C0AD820B1A390B168D356`.

Canonical Node-project READMEs independently document that fingerprint as
**Antoine du Hamel's active primary Node.js release key**:
- nodejs/node commit `e97c75e15482eba7a4208e68a763fc0a0fcc9ee9`.
- nodejs/release-keys commit `481637f813e912c4aa3622d7964ab426c97b8e8d`.

The exact single public key is 924 bytes, SHA256
`5115095e2f8010c75da052ecb1cfb3af630e084f0f8daa93a863557b01b0f90a`.
Its Git blob, authorization README blobs and source tree bytes match retained
commit/source metadata. GitHub's commit-signature status is an API assertion,
not a locally verified Git commit signature.

Authenticated under this **canonical vendor HTTPS key-source policy**:
- `node-v24.16.0-linux-x64.tar.gz`
- SHA256 `2faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff`.

**Not personal identity / Web-of-Trust proof.** GPG explicitly reports
TRUST_UNDEFINED; that warning is preserved. Current active-key declarations are
not a complete historical revocation/authorization guarantee or trusted timestamp.

This stage made 11 distinct bounded official GitHub source/key metadata GETs:
no redirects, retries, earlier checksum reacquisition or aggregate keyring download.
Four isolated GPG operations (version/import/list/verify) all exit 0. Automatic
agent/dirmngr start and key retrieval are disabled; the exact initially empty
owned GPG home is removed after verified child-group shutdown. Raw key, source
bodies and original GPG outputs/keyring state remain in the separate private seal.
One owning source-comparator refusal (commitish tree SHA alias) is retained.

**No archive/Node/Gradle/build/cache/U1/U2/U3/U4 execution or global trust/source/
Git mutation.** No archive bytes/size/hash, genuine Gradle cache installation or
offline resolver proof exists. Original U1 remains FAILED / STOP AND REVIEW;
its graph/gate/sentinel/security/cleanup acceptance remains absent/null and #40
stays open. The lead decides the next fresh isolated normal-resolver prerequisite
and later original-home bridge. All release/security/readiness gates remain.

This public derivative contains concise scalars, source bindings and proof only:
no raw keys, outputs, machine paths, private home identities or runtime payloads.
Source packet files are 0400; lead import destinations may use 0644.
