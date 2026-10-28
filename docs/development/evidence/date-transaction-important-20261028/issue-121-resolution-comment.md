<!-- nativecmpkit-resolution:UI-006:date-transaction-fa125cf3 -->
## Verified fix — closing directly after important tests and source/result review

The Material compact picker now owns its scratch transaction by the hoisted state, cancels rather than transplants on replacement, disables forbidden commits, and revalidates the latest rule at the actual confirmation event boundary. Public APIs and the intentional null-selection policy remain unchanged.

All **three original acceptance criteria** pass in four actual public Compose dialog scenarios: March15 → March16 → tighten maximumMarch15 and invoke the previously enabled real confirmation action before recomposition; replacement owner/rules/yearRange; NoDates; and actual editable-input clearing, cancellation, reopening and null confirmation.

- **JS4/4**, fresh XML, zero failures/errors/skips at immutable **fa125cf388845f22fe26f0b17ce4a9a0d65859c1**, [run40652867059](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40652867059), library exit0/340.09s. The owning JS fixture now awaits real Skiko initialization and returns the flattened test Promise; failures are not caught or discarded.
- **Android API35 instrumentation4/4**, fresh XML, library exit0/93.05s at **b6f647b890b46f2409f8fa0797444fc70633eca2**, [run40651576776](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40651576776). Actual emulator, SELinux Enforcing, clean owned shutdown; no forced termination. This is not a physical-device claim.
- **Wasm4/4**, fresh XML at **0f02a0997024d690e9ccd384a7b4079448903afa**, [run40650621351](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40650621351). That whole two-browser run remains failed on its original JS initialization defect; its accepted Wasm result was not replayed.
- **Desktop4/4 and Android-host4/4 accepted** using three unchanged successful cases each at **c8b5c614** plus only the corrected null-input case each at **8120c27a** (fresh1/1 each, exit0/63.02s). The original combined run remains failed3/4 each: the fixture mistakenly tested the merged visible Date label rather than the actual empty editable value. Assertions outside that owning null fixture did not change.

Reviewed actual source, all recorded inputs against their own immutable Git blobs, exact XML identities/counts and runtime/controller receipts. **20 accepted platform-method pairs, four authored scenarios**, not20 unique methods. Browser XML durations are very short; Promise-supporting adapters/actual returned TestResult were source-reviewed, but these timings are not a performance measurement or proof of broader native behavior.

Original failures and technical issue body/labels/upstream references remain preserved. Full iOS/native/minimum-platform, consumer, ABI, dependency/legal/security and release gates remain separate. No packages, releases or deployments were published. Detailed evidence will be committed next, without delaying this direct verified closure.
