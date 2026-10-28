# Important module-scoped native JAR verification — 2026-10-28

**BUILD-011/#146 was already closed during migration.** [Fresh readback](issue-146-existing-state.json) prevents a duplicate closure claim. The development ledger now accepts all three original module-scoping requirements from actual host archives; full native distribution/consumer/security/release gates remain separate.

[Actual JAR/staging review](jar001/accepted-review.json) binds immutable `9608ca19896fef3f48bcc8e6e983a7619aa6b77f`, clean source, **795** held library/build inputs and the actual JDK 17 daemon.

- Both `desktopJar` tasks and native preparation actually ran: **exit 0/37.01 s**; zero runtime tests. Initial `gradle002` **exit 1/30.01 s** because `rustup` was absent from PATH remains preserved; recovery explicitly used installed Cargo and JDK 17.
- Actual picker JAR: **453,188 bytes, 120 entries, zero duplicate entries**. Actual share JAR: **256,034 bytes, 84 entries, zero duplicate entries**. Each has only its own Linux binary plus its module-qualified native manifest; the native-resource path sets have **empty intersection**. Sizes are observed, not an invented performance threshold.
- Embedded native/manifest bytes match staged and processed resources exactly. The owning validator checks Linux CPU/container, binary size/hash, clean current revision, exact version/toolchain and complete expected source inventory.
- **Six actual `artifacts.py assemble` commands using extracted real native bytes:** own-module positives 2/2 succeed; foreign-only/missing-own negatives 2/2 and mixed-module negatives 2/2 fail closed before creating output. Only our own dedicated build-stage directories were removed afterward.
- **Two source-held tooling methods pass** at the same immutable revision: two modules × all five packaging platforms. These use **synthetic binary headers**, not native compilation or functionality. The earlier dirty-source diagnostic overlaps, not four unique methods.

The module-qualified staging convention and `duplicatesStrategy=FAIL` remain strict; only identical source-path/destination hierarchy repetitions are deduplicated. Legacy payload directories and combined publication workflows cannot bypass the manifest validator.

**Limits:** actual archives cover Linux x64 only; no complete five-target packaged distribution, artifact upload/download release pipeline, live JNI/modal/native runtime, intended-host ABI, consumer, dependency/provenance/legal/security or release gate is certified. BUILD-003 stays independent. Candidate JARs and extracted native binaries remain local and are **not archived/uploaded/published**. Stored evidence contains receipts, hashes, source inventories and compressed command result text only. No new issue closure, release, deployment or subagents.
