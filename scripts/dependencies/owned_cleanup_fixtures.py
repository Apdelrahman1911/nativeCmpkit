"""Explicit real Linux Gradle cleanup regressions; NEVER offline unittest work.

Five fresh plugin-free/local-Maven invocations: normal completion, the preserved
finite60s timeout, SIGINT/SIGTERM cancellation, and TERM-resistant shutdown.
The driver signals only its directly constructed/pinned Python controller. It
never cleans up a daemon on the controller's behalf or signals receipt PIDs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time

import gradle_fixtures as f
import gradle_process as g
import integrity as d
import integrity_model as m
import owned_gradle as o
import runtime_witness as w

CASES = ("normal", "timeout", "sigint", "sigterm", "timeout-term-resistant")
HOLD = '''
// Deterministic finite hold of the exact acquisition graph, not library/native work.
gradle.taskGraph.whenReady { graph ->
    if (!graph.hasTask(":nativeCmpkitDependencyGraph")) throw new GradleException("Unexpected owned task")
    def target = file("build/dependency-integrity/bootstrap/owned-cancel-ready.json")
    target.parentFile.mkdirs()
    target.text = groovy.json.JsonOutput.toJson([record_type: "owned-cancellation-hold", pid: ProcessHandle.current().pid(), hold_milliseconds: 60000])
    Thread.sleep(60000)
}
'''
RESIST_TERM = '''
// Finite shutdown hold forces the owning controller's bounded pidfd escalation.
Runtime.runtime.addShutdownHook(new Thread({ Thread.sleep(30000) } as Runnable))
'''


def put(path: Path, value: dict) -> None:
    m.write_new(path, m.json_bytes(value))


def inputs() -> dict[str, str]:
    return {**w.checkpoint_files(), **{"scripts/dependencies/" + n: h for n, h in w.observer_files().items()},
            "scripts/dependencies/" + w.CHECKPOINT_FILENAME: w.CHECKPOINT_SHA256}


def create(root: Path, case: str) -> dict:
    d._new_workspace_path(root)
    root.mkdir()
    for source in d.TOOL_DIRECTORY.iterdir():
        if source.is_file() and source.suffix in {".py", ".gradle", ".md"}:
            f.put(root, "scripts/dependencies/" + source.name, source.read_bytes())
    f.put(root, "settings.gradle", b'rootProject.name = "nativecmpkit-dependency-fixture"\n')
    script = f.BASE_BUILD + (RESIST_TERM if case == "timeout-term-resistant" else "") + (HOLD if case != "normal" else "")
    f.put(root, "build.gradle", script.encode())
    for module, version in (("parent", "1.0"), ("leaf", "1.0"), ("extra", "1.0")):
        for name, raw in f.artifact_files(module, version).items():
            f.put(root, name, raw)
    f.put(root, f"repo/{f.GROUP_DIRECTORY}/leaf/maven-metadata.xml", f.version_metadata(["1.0"]))
    f.put(root, "gradle/verification-metadata.xml", m.metadata_bytes(f.known_metadata()))
    return f.write_marker(root)


def controller_bytes(workspace: Path, result_path: Path, jdk: Path, gradle: Path, timeout: int) -> bytes:
    return f'''from pathlib import Path
import json,os,sys
sys.path.insert(0,{str(d.TOOL_DIRECTORY)!r})
import integrity as d
os.environ['JAVA_HOME']={str(jdk)!r}
with d.sigterm_as_interrupt():
    result=d.run(Path({str(workspace)!r}),entry_root='.',run_id='bootstrap',mode='bootstrap',timeout={timeout},reserve_mib=8192,gradle_home=Path({str(gradle)!r}),fresh_cache=True)
with Path({str(result_path)!r}).open('x') as stream:
    stream.write(json.dumps(result,indent=2,sort_keys=True)+'\\n')
'''.encode()


def execute(destination: Path, gradle_home: Path, jdk_home: Path) -> dict:
    m.require(sys.platform == "linux" and o._ACTIVE is False, "Dedicated serial Linux controller required")
    for path in (destination, gradle_home, jdk_home):
        w.plain_absolute(path, existing=path != destination)
    m.require(gradle_home.name == "gradle-9.7.1" and (jdk_home / "bin/java").is_file(), "Exact Gradle/JDK required")
    release = m.read_regular(jdk_home / "release", 16384).decode()
    m.require(any(line.startswith('JAVA_VERSION="17.') for line in release.splitlines()), "Installed JDK17 required")
    frozen = inputs()  # Mandatory prelaunch freeze; failures cannot fall through to a build.
    d._new_workspace_path(destination)
    destination.mkdir()
    for name in frozen:
        f.put(destination, "source/" + name, (w.SOURCE_ROOT / name).read_bytes())
    put(destination / "inputs-before.json", frozen)
    m.require(all(shutil.disk_usage(p).free >= 8192 * 1024**2 for p in (w.SOURCE_ROOT, destination)),
              "Root and tmpfs reserve required")
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    outcomes = []
    for case in CASES:
        slot = destination / case
        slot.mkdir()
        workspace = slot / "project"
        marker = create(workspace, case)
        put(slot / "marker-before.json", marker)
        command_file = slot / "controller.py"
        result_path = slot / "controller-result.json"
        m.write_new(command_file, controller_bytes(workspace, result_path, jdk_home, gradle_home,
                                                  20 if case.startswith("timeout") else 60))
        command = [sys.executable, "-B", str(command_file)]
        environment = {"JAVA_HOME": str(jdk_home), "PATH": str(jdk_home / "bin") + os.pathsep + os.defpath,
                       "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "PYTHONDONTWRITEBYTECODE": "1"}
        began = time.monotonic()
        pin = None
        interrupted = False
        process = None
        result = None
        try:
            with (slot / "controller.log").open("xb") as output:
                process = subprocess.Popen(command, cwd=w.SOURCE_ROOT, env=environment,
                                           stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
                first = o.identity(process.pid)
                m.require(first.parent == os.getpid() and first.group == first.session == process.pid,
                          "Direct owned controller ancestry changed")
                pin = os.pidfd_open(process.pid, 0)
                m.require(not o.exited(pin) and o.identity(process.pid) == first, "Controller pin changed")
                put(slot / "controller-launch.json", {"command": command, "source_sha256": m.file_sha256(command_file),
                                                       "process": first.public(), "pidfd_pre_post_validated": True})
                while not o.exited(pin):
                    m.require(all(shutil.disk_usage(p).free >= 8192 * 1024**2 for p in (w.SOURCE_ROOT, destination)),
                              "Disk reserve reached")
                    m.require(time.monotonic() - began <= 75, "Owned fixture deadline exceeded")
                    ready = workspace / "build/dependency-integrity/bootstrap/owned-cancel-ready.json"
                    if case in {"sigint", "sigterm"} and not interrupted and ready.is_file():
                        stamp = m.read_json(ready)
                        m.require(stamp.get("record_type") == "owned-cancellation-hold" and
                                  stamp.get("hold_milliseconds") == 60000, "Actual finite hold missing")
                        m.require(o.identity(process.pid) == first and not o.exited(pin) and
                                  Path(os.readlink(f"/proc/{process.pid}/exe")) == Path(sys.executable).resolve() and
                                  g.fields(o.proc_bytes(process.pid, "cmdline")) == command,
                                  "Direct controller changed before interrupt")
                        signum = signal.SIGINT if case == "sigint" else signal.SIGTERM
                        signal.pidfd_send_signal(pin, signum)
                        interrupted = True
                        put(slot / "direct-controller-interrupt.json", {"signal": signum, "exact_controller_pidfd_used": True,
                                                                       "ready_record_pid_used_for_signal": False})
                    time.sleep(0.05)
                code = process.wait(timeout=2)
                m.require(code == 0 and result_path.is_file(), "Controller failed before final receipt")
                result = m.read_json(result_path)
                execution = result["execution"]
                cleanup = execution["owned_gradle_cleanup"]
                m.require(cleanup["complete"] is True and cleanup["errors"] == [], "Owning controller cleanup failed")
                leases = [cleanup["client"], *cleanup["daemons"]]
                m.require(len(leases) == 2 and all(l["exited"] and l["pid_absent"] and l["handle_closed"] for l in leases) and
                          all(not (Path("/proc") / str(l["pid"])).exists() for l in leases),
                          "Exact Gradle processes remain after controller returns")
                expected = (execution["exit_code"] == 0 and "reason" not in execution and result["selected_project_graph_complete"]
                            if case == "normal" else execution.get("reason") == ("timeout" if case.startswith("timeout") else "interrupted") and
                            execution["exit_code"] != 0 and not result["selected_project_graph_complete"])
                m.require(expected, "Actual expected controller result missing")
                if case == "timeout-term-resistant":
                    m.require(cleanup["daemons"][0]["kill_sent"] is True, "Real TERM resistance did not exercise escalation")
                m.require(d.check_source(workspace, marker) is not None and inputs() == frozen, "Held inputs changed")
                outcome = {"case": case, "passed": True, "controller_exit_code": code,
                           "elapsed_seconds": round(time.monotonic() - began, 3), "execution": execution,
                           "source_input_digest": marker["source_input_digest"], "actual_gradle_invocations": 1,
                           "external_daemon_cleanup_performed": False, "jcmd_attempts": 0,
                           "library_native_or_packaged_consumer_methods_executed": 0}
                put(slot / "outcome.json", outcome)
                outcomes.append(outcome)
                print(json.dumps({"case": case, "passed": True, "elapsed_seconds": outcome["elapsed_seconds"]}), flush=True)
        finally:
            if process is not None and process.poll() is None:
                if pin is not None and not o.exited(pin):
                    signal.pidfd_send_signal(pin, signal.SIGINT)
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        signal.pidfd_send_signal(pin, signal.SIGKILL)
                        process.wait(timeout=5)
                else:
                    process.terminate()  # Direct unreaped child only, never a nominated PID.
                    process.wait(timeout=15)
            if pin is not None:
                os.close(pin)
    after = inputs()
    put(destination / "inputs-after.json", after)
    m.require(after == frozen, "Held source changed")
    record = {"schema_version": 1, "record_type": "real-owned-gradle-cleanup-fixtures", "started_utc": started,
              "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "passed": len(outcomes) == len(CASES),
              "cases": outcomes, "actual_gradle_invocations": len(outcomes), "jcmd_attempts": 0,
              "source_files_held": len(frozen), "external_daemon_cleanup_performed": False,
              "library_native_or_packaged_consumer_methods_executed": 0, "release_readiness_certified": False}
    put(destination / "result.json", record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--gradle-home", required=True, type=Path)
    parser.add_argument("--jdk-home", required=True, type=Path)
    with d.sigterm_as_interrupt():
        try:
            record = execute(**vars(parser.parse_args()))
            print(json.dumps({"passed": record["passed"], "actual_gradle_invocations": record["actual_gradle_invocations"]}))
        except (m.IntegrityError, o.g.WitnessError, OSError, subprocess.SubprocessError, KeyboardInterrupt) as failure:
            print(json.dumps({"passed": False, "error_type": type(failure).__name__,
                              "error": str(failure) if isinstance(failure, m.IntegrityError) else
                              "Local controlled fixture failed; inspect preserved receipts. No success claim."}))
            raise SystemExit(1)
