# Shared Apple graph classifier repaired before missing-build recovery

Actual original Apple40967168162 has **navigationevent**, a distinct group/API,
in both compile graphs. Matching `org.jetbrains.androidx.navigation` by prefix
incorrectly classified it as the removed Navigation library. The owning repair
checks exact `org.jetbrains.androidx.navigation` and `androidx.navigation`
identities, continues rejecting either actual navigation group, and retains
full graph/unresolved/import/minSdk24 checks. No library/Compose dependency was
removed to silence a false positive; NavigationEvent version/device compatibility
is not certified.

New real-shape owning guard first fails1/1; [shared important tools](final-important001/review.json)
pass **77/77**, all962 inputs held, actionlint1.7.12/whitespace pass. The wrapper's
missing actionlint path **after**77 passing methods is retained; recovery runs
only actionlint, not those methods. These77 overlap the prior108, not185 unique
methods. ZERO new local Gradle/native/sample executions.

[Apple postmortem](../platform-apple-ci001/postmortem001/README.md) preserves
17/17 reported native sample methods/five XML/all960 BEFORE exact historical Git;
missing AFTER/process/output/fresh-task-marker receipts and failed whole workflow
remain explicit. Recover only missing frameworks/real unsigned Xcode app builds,
not accepted sample methods. #100/#154 remain open pending original criteria.
Single-agent/max2 combined heavy requests/8GiB reserve; publishing/Pages/main/
history and independent release/security gates unchanged.
