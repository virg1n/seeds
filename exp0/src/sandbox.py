"""Parent-side API of the sandbox: builds jobs, launches `harness.py` in a subprocess."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from . import config as C

HARNESS = Path(__file__).with_name("harness.py")

_ENV = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "PYTHONHASHSEED": "0",
    "PYTHONDONTWRITEBYTECODE": "1",
    "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
}
if os.name == "nt":  # local smoke tests on Windows
    _ENV["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")


def run_job(job: dict, wall_timeout: float) -> dict:
    sb = C.TMP_DIR / "sandbox"
    sb.mkdir(parents=True, exist_ok=True)
    job.setdefault("mem_mb", C.MEM_LIMIT_MB)
    job.setdefault("cpu_s", int(wall_timeout) + 10)
    with tempfile.TemporaryDirectory(dir=sb) as d:
        env = dict(_ENV, HOME=d, TMPDIR=d)
        killed = False
        try:
            p = subprocess.run([sys.executable, "-I", "-X", "utf8", str(HARNESS)],
                               input=json.dumps(job).encode("utf-8"), stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, cwd=d, env=env, timeout=wall_timeout)
            raw, code = p.stdout, p.returncode
        except subprocess.TimeoutExpired as e:
            raw, code, killed = (e.stdout or b""), -9, True
    # the harness writes JSON checkpoints line by line; the last complete line is the result
    last = None
    for line in raw.decode("utf-8", "replace").splitlines():
        try:
            last = json.loads(line)
        except json.JSONDecodeError:
            pass
    fail = {"passed": 0, "total": len(job.get("tests", [])), "runs": [], "timing": []}
    if last is None:
        return dict(fail, status="wall_timeout" if killed else "crash", err=f"exit code {code}")
    if code != 0 or killed:
        # killed mid-way (watchdog / wall clock): keep the trace collected so far, but a test
        # job that did not finish is never counted as passed
        last = dict(last, status="killed")
        last.setdefault("runs", [])
        last.setdefault("timing", [])
    return last


def test_program(task: dict, code: str, tests=None) -> dict:
    tests = task["tests"] if tests is None else tests
    job = {"mode": "test", "kind": task["kind"], "code": code, "entry": task.get("entry"),
           "setup": task.get("setup", ""), "tests": tests, "timeout": C.TEST_TIMEOUT}
    wall = min(300.0, sum(float(t.get("timeout", C.TEST_TIMEOUT)) for t in tests) + 10)
    r = run_job(job, wall)
    r["correct"] = bool(r.get("status") == "ok" and r.get("passed") == len(tests) and len(tests) > 0)
    return r


def _physical_cores():
    """One logical CPU per physical core (hyper-thread siblings skipped), Linux only."""
    try:
        allowed = sorted(os.sched_getaffinity(0))
    except AttributeError:
        return []
    seen, out = set(), []
    for c in allowed:
        try:
            sib = open(f"/sys/devices/system/cpu/cpu{c}/topology/thread_siblings_list").read().strip()
        except OSError:
            sib = str(c)
        if sib not in seen:
            seen.add(sib)
            out.append(c)
    return out


_CORES = None
_CORE_Q = None


def core_pool():
    global _CORES, _CORE_Q
    if _CORES is None:
        import queue
        _CORES = _physical_cores()
        _CORE_Q = queue.Queue()
        for c in _CORES:
            _CORE_Q.put(c)
    return _CORES, _CORE_Q


def trace_program(task: dict, code: str, inputs=None) -> dict:
    if inputs is None:
        from .scaler import build_ladder
        inputs = build_ladder(task)
    job = {"mode": "trace", "kind": task["kind"], "code": code, "entry": task.get("entry"),
           "setup": task.get("setup", ""), "inputs": inputs, "max_events": C.TRACE_MAX_EVENTS,
           "timeout": C.TRACE_RUN_TIMEOUT, "timing_limit": C.TIMING_RUN_LIMIT}
    cores, q = core_pool()
    if not cores:
        return run_job(job, wall_timeout=240.0)
    cpu = q.get()  # pin the traced program to its own physical core (less timing noise)
    try:
        job["cpu"] = cpu
        return run_job(job, wall_timeout=240.0)
    finally:
        q.put(cpu)
