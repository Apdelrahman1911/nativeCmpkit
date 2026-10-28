# Equal-settings native state replacement — 2026-10-28

Three new actual public Compose/UIKit methods replace state A→B with equal selection/rules, the same colors object, RTL and disabled compact settings; inspect every new native view's min/max/tint/background/enabled/RTL, old-view detachment and ordinary recomposition retaining views. This targets original UI-003/#119; it is not executed evidence until a real native job passes and is reviewed.

[Run40711841110](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40711841110) at `b01e5399` was deliberately **cancelled once while its native job was queued before runner assignment**. Final readback shows runner_id0, no native steps/executions or artifact; tooling succeeded. [Cancellation receipts](cancelled001/cancel-receipt.json) and final readbacks are preserved. This is neither a runtime failure nor a pass. The known asynchronous controller-readiness race was repaired before consuming another native link.

The three methods are now included once with the four repaired failed date methods in [the combined seven-check run](../dates-recovery-important-20261028/README.md). The two passed backend methods are not repeated. **#119 remains open** until its three original criteria actually pass and are reviewed. Single-agent, no publication or broader release-gate waiver.
