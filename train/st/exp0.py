"""Bridge to the exp0 code (sandbox, tracer, ladders, fingerprint): one copy of that code is used
by both experiments. Importing this module makes `C0, FP, fpstore, sandbox, scaler, prompts, utils`
available; `setup()` points exp0's scratch / cache folders into this run and applies our limits.

CPU cores. Several jobs (one per GPU) run at the same time and every one of them traces programs
with timing measurements pinned to physical cores. The orchestrator gives each job its own cores in
the ST_CORES environment variable; `apply_cores()` restricts the process to them BEFORE the first
trace, so exp0's core pool (sandbox.core_pool) only ever hands out this job's cores."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from . import config as CFG

if str(CFG.EXP0_DIR) not in sys.path:
    sys.path.insert(0, str(CFG.EXP0_DIR))

from src import config as C0  # noqa: E402
from src import fingerprint as FP  # noqa: E402
from src import fpstore, prompts, sandbox, scaler, utils  # noqa: E402,F401


def cpu_quota():
    """CPUs this container may use (cgroup quota), or None when unlimited / unknown."""
    try:
        with open("/sys/fs/cgroup/cpu.max") as f:  # cgroup v2
            q, p = f.read().split()[:2]
            return None if q == "max" else max(1, int(int(q) / int(p)))
    except (OSError, ValueError):
        pass
    try:
        with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us") as f:  # cgroup v1
            q = int(f.read())
        with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us") as f:
            p = int(f.read())
        return None if q <= 0 else max(1, q // p)
    except (OSError, ValueError):
        return None


def physical_cores():
    """[[logical cpus of one physical core], ...] of the CPUs this process may run on (Linux);
    elsewhere one fake core per logical CPU."""
    try:
        allowed = sorted(os.sched_getaffinity(0))
    except AttributeError:
        return [[i] for i in range(os.cpu_count() or 4)]
    groups, seen = [], {}
    for c in allowed:
        try:
            sib = open(f"/sys/devices/system/cpu/cpu{c}/topology/thread_siblings_list").read().strip()
        except OSError:
            sib = str(c)
        if sib not in seen:
            seen[sib] = len(groups)
            groups.append([])
        groups[seen[sib]].append(c)
    return groups


def apply_cores():
    """Restricts this process to the cores of ST_CORES (if set). Returns (logical, physical) counts
    available to this job, never more than the container's CPU quota."""
    spec = os.environ.get("ST_CORES", "").strip()
    if spec and hasattr(os, "sched_setaffinity"):
        try:
            os.sched_setaffinity(0, {int(x) for x in spec.split(",") if x.strip()})
        except (OSError, ValueError) as e:
            print(f"[cores] could not apply ST_CORES={spec}: {e}", flush=True)
    groups = physical_cores()
    logical, physical = sum(len(g) for g in groups), len(groups)
    quota = cpu_quota()
    if quota and not spec:  # no slice given: the quota is the only bound we know
        logical, physical = min(logical, quota), min(physical, quota)
    return max(1, logical), max(1, physical)


_READY = False


def setup(run_dir=None, workers=None, trace_workers=None):
    """Call once per process, before any sandbox work. run_dir: where exp0-style logs go."""
    global _READY
    logical, physical = apply_cores()
    C0.TMP_DIR = Path(os.environ.get("ST_TMP") or tempfile.gettempdir()) / f"st_sandbox_{os.getpid()}"
    C0.TMP_DIR.mkdir(parents=True, exist_ok=True)
    base = Path(run_dir) if run_dir else CFG.RUN_DIR
    C0.CACHE_DIR = base / "cache"
    C0.LOG_DIR = base / "logs"
    C0.TEST_TIMEOUT = CFG.TEST_TIMEOUT
    C0.MEM_LIMIT_MB = CFG.MEM_LIMIT_MB
    # tests are not timing-sensitive: one per logical CPU (one CPU is left to the GPU-feeding main thread);
    # traces measure time: one per physical core, each pinned to its own core by exp0's sandbox
    C0.WORKERS = int(workers or os.environ.get("ST_WORKERS") or max(1, logical - 1))
    C0.FP_WORKERS = int(trace_workers or os.environ.get("ST_TRACE_WORKERS") or max(1, physical - 1))
    _READY = True
    return C0.WORKERS, C0.FP_WORKERS


def cleanup_tmp():
    import shutil
    try:
        shutil.rmtree(C0.TMP_DIR, ignore_errors=True)
    except Exception:  # noqa
        pass
