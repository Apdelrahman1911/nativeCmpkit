# Bounded pure source-path memoization714

The failed producer709 exceeded its CI discovery allocation. Its last test and
underlying hosted cause are unknown. Two separately bounded pure source reads713
showed11.7746s/28.3M calls; the repeated joint-source `_identity` grammar check
alone made103680 calls. A prototype714 reduced those same two transformations
to6.8315s/9.8M calls, retaining exact input/output hashes. This is local profiling,
not a hosted capacity or native-success claim.

`macos_share_ci668_composition._identity` now memoizes only the immutable tuple
returned by the unchanged AppKit path grammar. It rejects nonexact string,
empty and >4096-character keys before cache hashing. `lru_cache(maxsize=512)`
stores successful results only. Invalid grammar retains its existing refusal;
misses may duplicate under concurrency. The cache is process-local and bounded.

No files, roots, descriptors, parsed mutable manifests, dependency acceptance,
source hashes, payload types/sizes, signature or native results are cached.
The complete joint280 source domain and the named175/190/40/36 predecessors stay
unchanged. Only its owner-template seal advances; the NEW controls are separately
tracked by the full offline producer source signature and scripts/ci discovery.

Focused controls cover warm hits, invalid/unhashable/oversized inputs, exact
historical grammar parity, bounds/eviction, concurrent pure reads, fresh ordinary
file/dependency/manifest reads, and the exact historical projection hash. The
FIRST RED one-method grammar-call regression remains failed until the changed
implementation is tested. Local compiler/native/consumer and release gates remain
separate. Never infer709's hidden last test or rerun709 unchanged.
