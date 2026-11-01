# Open upstream issue reconciliation — 2026-11-01 00:10:25 UTC

All **16 currently open Calf issues** have existing NativeCmpKit tracking context.
No import, duplicate issue, source mutation or destination issue mutation was
needed. One open upstream pull request (#551) is retained separately in the exact
17-record source response. Destination observation: **91 closed /81 open /172**.

The source descriptions, complete author/label objects, creation timestamps,
comment counts and updated timestamps match the [prior full snapshot](../20261027T014340Z/).
The exact field comparison is retained. Comments and timelines were **not fetched
again**: this does not claim fresh comment-body/timeline equivalence or that an
unchanged comment count proves no edit. The dated full discussion archives remain
available independently.

`receipt.json` maps every upstream issue to existing destination references.
Calf #39 has its existing primary #75 context and an additional #64 risk reference;
this is not another imported issue. Previously source-addressed/partially applicable
requests retain the [scoped prior reconciliation](../../../development/upstream-sync-20261024T183300Z/README.md).
No issue is closed solely because upstream has addressed it.

The initial paginated destination GET failed (exit1); its stderr was not retained
and its cause remains unknown. A subsequent explicit two-page read-only capture
succeeded. The failed capture record is not rewritten as success. These are exact
public API payloads plus review receipts, not executable instructions, HTTP-header
claims, native tests or release evidence.
