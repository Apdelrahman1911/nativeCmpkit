<!-- nativecmpkit-resolution:UI-031:95a8406fc7ab -->
## Verified fix — closing after important tests and review

The owning repair uses authoritative checked state, Foundation horizontal touch-slop/drag and full-track toggle commits; gesture cancellation restores preview and pairs Cancel without any business callback. Damped modifier cancellation only releases visual feedback; disposal/re-key finally releases its owned interaction. No public Calf API/package/native name changed.

All **three original acceptance criteria** are reviewed against source and actual results:
1. Existing real UIKit/Compose thumb-origin nested vertical-scroll and scene-cancel check gives **no toggle**. Default x32 is inside the unchecked thumb[2,42]. The standard Foundation axis/consumption contract owns arbitration; no measured scroll-offset claim.
2. Fresh primary-pointer handoff does **not** finish while the second pointer is down, commits/pairs Stop **once** at final up. Fresh disposal pairs Cancel **once**, suppresses stale up into the replacement and accepts one fresh tap. Unchanged native scene-cancel/external-checked/disabled-transition and actual Damped cancellation checks also pass.
3. Successful full-track tap, semantic activation and drag each have exact callback counts and authoritative final state; cancelled gestures never call the commit callback.

Fresh verification: [run40779367369](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40779367369), immutable `95a8406fc7abb9dcf6adeeea79edf7dc21885947`, **2/2 actual native methods**, one fresh XML, zero failure/error/skip, task **0/1368.82s**, all **814 own-Git/before/after inputs held**, actual JDK17, iPhone/iOS26.5 and Xcode26.6. Whole workflow **SUCCESS**. Worker/protocol/XML/runtime/owned application cleanup bindings reviewed. The producer performed the live linked-binary gate; the reports-only artifact intentionally excludes that binary, so this is not a new offline artifact/ABI check.

**Five unchanged relevant native passes** are reused from [40522929974 attempt2](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40522929974/attempts/2), immutable `202059090bbbf896d07d38a3441cf21c8888c63b`: full-track tap, rejected drag, pointer cancel/vertical scroll, external checked/disabled transition, Damped actual modifier cancel/success. Their original XML, eight unchanged control bodies/Damped tests and four owning production files were checked. **Seven accepted method executions, not a replay of the prior121-method suite.**

Evidence: `docs/development/evidence/switch-cancellation-important-20261028/` (additive final readback follows this direct closure). Original failures and issue body/history retained. Hardware/VoiceOver/Switch Control/older/minimum-device and sustained profiling gates remain independently open, including #35/#37. No broad consumer/ABI/native-memory/dependency/legal/security/release certificate or publication/deployment is implied.
