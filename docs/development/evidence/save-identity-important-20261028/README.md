# Important Android save identity and native recovery — 2026-10-28

**Accepted:** two fresh Android-host methods and nine fresh API35 device methods;
the independently accepted descriptor calibration is reused, not rerun. **IO-006 /
[#43](https://github.com/Apdelrahman1911/nativeCmpkit/issues/43) stays open.** Its
six original write/error/cancellation criteria are not all satisfied by identity
and Activity-recreation tests. Original technical issue body is preserved; the
[progress comment](https://github.com/Apdelrahman1911/nativeCmpkit/issues/43#issuecomment-6478127758)
was posted once and read back.

| Evidence | Actual outcome | Boundaries |
|---|---|---|
| `host001/` at immutable `4fa3f1bb` | **2/2**, one fresh XML, Gradle exit0/59.01s,803 held own-Git inputs, actual JDK17 | Real resolver/Unix source identity plus controlled destination-only zero/EACCES/EIO/EPERM; not Android kernel/ACL/hardlink proof |
| [40746114786](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40746114786), `native001/`, `4fa3f1bb` | **Whole workflow FAILED/incomplete.** Connected Gradle exit0/59.03s and **1/1 actually executed**; nine selected methods absent | The strict actual XML inventory correctly rejected missing cases. Never call this10/10 |
| [40749319485](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40749319485), `native002/`, immutable `f616a172` | **SUCCESS:9/9**, one fresh XML, zero failure/error/skip; connected exit0/78.03s, APK exit0/328.10s; all804 inputs match this commit's own Git blobs and remain held | API35/x86_64/SELinux Enforcing; actual JDK17 daemon; clean unforced emulator exit0. Exactly the nine missing methods, no successful calibration replay |
| `selection-tooling002/` | **205/205** selected Python methods, zero failure/error/skip,804 held inputs; dirty precommit source later committed as `f616a172` | Tooling only; the focused11 are included, not216 unique methods or native tests |
| `selector-compile001/` at immutable `f616a172` | **FAILED**, offline Android dependencies uncached; exit1/37.01s;804 held inputs, actual JDK17, launcher/daemon home correspondence false | Zero native tests; do not certify annotation APK compilation or selector configuration from this failure. Actual hosted recovery supplies compile/runtime evidence |

## Owning selection defect, not a relaxed test gate

Actual AGP9.4.0 bytecode serializes instrumentation argument maps into a comma-
separated `key=value` transport. Official Android Test Engine1.0.1 source
[`AndroidTestConfiguration.kt:105–112`](selection-inspection/AndroidTestConfiguration.kt.txt)
splits the entire transport on commas, then accepts fragments containing `=`.
Consequently only the first `class=Class#method` fragment survived; nine later
`Class#method` fragments were dropped. AndroidJUnitRunner1.7.0's actual
`ClassesArgTokenizer` does support commas: it is **not** the owning cause.
Read the selected disassemblies and original registry URL/SHA256 receipts.
The verbatim Google source retains its Apache header; JARs are not committed or
executed and archived data is not an instruction source.

Test-only runtime function annotations now select exactly ten acceptance
methods. Recovery uses `annotation=SaveIdentityAcceptance` and
`notAnnotation=SaveIdentityCalibration`, each fully qualified. No argument value
contains commas. All21 original declarations remain; full native profiles still
require the original hardlink scenario. The fresh-task adapter inspects actual
AGP TestData arguments and rejects mismatched/comma-containing selectors before
connected execution. Source annotation and exact fresh XML inventories reject
missing/extra/misplaced/failed/skipped tests. No downgrade, test skip, security
policy weakening or private APK source replacement was introduced.

## Reviewed native scope

Nine fresh passes cover native distinct inodes/copy/descriptor closure, strict
kernel inode parsing, actual ENOTDIR refusal without damage, tree/single document
aliases with no write/delete, provider read revocation/new-document cleanup,
public FileProvider export, actual pending-URI Activity recreation and lost bytes
reported as error rather than empty success. Calibration reuse binds its unchanged
body, helper and production files. The complete native test file is **not** byte-
identical because acceptance annotations changed; no whole-file claim is made.

This does **not** cover provider output write/close/disk-full errors, real OS grant
revocation, hardlink acquisition denied by the original untrusted-app policy,
process death, iOS staging/presentation safe points, minimum/physical devices,
the full consumer/ABI/dependency/legal/security matrix or a release gate.
No publication, release, deployment or Pages mutation occurred. JSON/XML and
selected public source evidence are archived; binary ZIP/JARs, private/full
workflow transcripts and environment dumps are excluded.
