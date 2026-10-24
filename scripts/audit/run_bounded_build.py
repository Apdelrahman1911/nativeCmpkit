#!/usr/bin/env python3
"""Run a non-publishing audit command with time/disk limits and an evidence log.

This is a resource guard, not a command sandbox. Never pass credentials in argv.
It terminates only the process group it creates; it never deletes caches/files.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--reserve-mib", type=int, default=1024)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")
    # Defense against accidentally turning an audit invocation into a release.
    if any(arg.rsplit(":", 1)[-1].lower().startswith(("publish", "release", "gh-deploy"))
           or arg == "--scan" for arg in command):
        parser.error("publishing/release/build-scan commands are outside audit scope")
    cwd = args.cwd.resolve()
    args.log.parent.mkdir(parents=True, exist_ok=True)
    record = {"command": command, "cwd": str(cwd), "timeout_seconds": args.timeout,
              "reserve_mib": args.reserve_mib,
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    stats = os.statvfs(cwd)
    record["free_bytes_before"] = stats.f_bavail * stats.f_frsize
    if record["free_bytes_before"] < args.reserve_mib * 1024 ** 2:
        record.update(exit_code=75, reason="disk reserve not available; command not started")
    else:
        start = time.monotonic()
        with args.log.open("w") as log:
            log.write(json.dumps(record) + "\n")
            log.flush()
            process = subprocess.Popen(command, cwd=cwd, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            while process.poll() is None:
                stats = os.statvfs(cwd)
                if stats.f_bavail * stats.f_frsize < args.reserve_mib * 1024 ** 2:
                    record["reason"] = "disk reserve reached; audit-owned process group terminated"
                elif time.monotonic() - start > args.timeout:
                    record["reason"] = "timeout; audit-owned process group terminated"
                if "reason" in record:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    break
                time.sleep(1)
            record.update(exit_code=process.returncode,
                          elapsed_seconds=round(time.monotonic() - start, 2))
            log.write("\nAUDIT_RESULT=" + json.dumps(record) + "\n")
    stats = os.statvfs(cwd)
    record["free_bytes_after"] = stats.f_bavail * stats.f_frsize
    args.log.with_suffix(args.log.suffix + ".result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0 if record["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
