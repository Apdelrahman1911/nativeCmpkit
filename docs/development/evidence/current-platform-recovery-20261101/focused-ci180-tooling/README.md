# Focused CI180: shared tooling failure before any platform test

The frozen related batch is `5539c0085dd8e1f3af4302026556aaa7bdabef96` on
`development/preview-hardening`. Main remains `94d2492e`.

- [Android Local2 original review](android-local2/README.md): run41355429513,
  tooling2275 source methods/122.049s/process1.
- [Wasm4 original review](wasm4/README.md): run41355901768,
  tooling2275 source methods/96.705s/process1.

Both actual workflows are **FAILED** with20 failure records across13 distinct
legacy mutation methods:18 missing old source anchors and two strict refusal
category mismatches. Profile selection/native jobs are skipped; **ZERO new
Android/Wasm/browser/Gradle/XML/artifacts**. This is a proven owning test-fixture
mismatch after the resource-admission change, not a provider/browser diagnosis.
Each designated reviewer acquired its own original logs once; no original
reacquisition or accepted-platform replay occurred. Their complete public-safe
reports and hash ledgers are retained alongside this note.

One minimal shared fixture repair is being independently prepared. Keep#55/#82
open; Local2, cloudC1 and Wasm4 remain separately required. Share13 is ready but
not requested against this known-failed tooling. No reservations remain after
these terminal failures; future requests retain max2 including queued work.
No publishing, release, deployment, Pages, main/history, native/consumer/API-ABI,
dependency/legal/security/readiness clearance follows.
