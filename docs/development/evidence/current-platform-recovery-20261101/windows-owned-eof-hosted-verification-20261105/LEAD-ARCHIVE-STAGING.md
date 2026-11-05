# Additive archive staging correction

The first `git add` refused the new evidence directory because it was outside
this worktree's sparse-checkout definition. Commit `b975ca3b` therefore preserved
only the AGENTS progress entry. The explicit `git add --sparse` follow-up adopts
the exact already-read-back archive without repeating any test or artifact
acquisition. The first commit and all Git history are retained; no reset,
amend, force push, source reapplication, native replay or release occurred.
The pre-existing unqualified success-trace file remains unstaged and unchanged.
