# Actual Apple allocation discovery — unsupported in this observation

The existing Apple host in [40974963662](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40974963662),
immutable `535b0353e2857d35ed799dbf997e3ab98e4c8684`, executed the owned public
**macOS HOST C** probe, not UIKit/iOS/GC/library tests. Actual clang0/4.53s,
xctrace record0/117.24s and TOC export0/7.68s produced **no allocation schemas or
exported rows**, so [discovery](discovery.json) records `supported=false`.
Command success is not an allocation/leak profile or native evidence.

[Original independent review](review.json) preserves its October29 timestamp
and the then-running sample-build observation; it is not re-dated after later
build completion. Artifact12943000408 digest was verified. Only safe JSON is
archived; owned private probe/log/trace/XML rows were removed on the runner.

This one host/template/probe observation does **not** establish universal
Instruments unavailability. #140/UI-037 and #141/UI-038 remain open: actual
large-buffer/concurrent GC/native diagnostics and a useful library allocation/
leak profile are still needed. Nine accepted UIImage methods are reused, not
replayed; no sanitizer/native lifetime/heap/release gate is certified.
