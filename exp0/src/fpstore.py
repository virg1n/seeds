"""Cached test evaluation and fingerprinting of (task, code) pairs.

Cache keys are content-addressed: they include the program, the task's tests / ladder, the
relevant limits and a hash of the source of the code that produces the result (harness, tracer,
fingerprint), so changing any of these never reuses stale results."""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import config as C
from . import fingerprint as FP
from .sandbox import test_program, trace_program
from .utils import JsonlCache, parallel_map, sha

_SRC = Path(__file__).parent
_caches = {}


def _src_hash(*files):
    return sha(*[(_SRC / f).read_text(encoding="utf-8") for f in files])


TEST_VERSION = _src_hash("harness.py", "sandbox.py")
# raw traces are cached (not fingerprints): changing fingerprint.py never requires re-running programs
TRACE_VERSION = _src_hash("harness.py", "sandbox.py", "scaler.py")


def _cache(name):
    if name not in _caches:
        _caches[name] = JsonlCache(C.CACHE_DIR / f"{name}.jsonl")
    return _caches[name]


def _task_test_hash(task):
    return sha(task["kind"], task.get("entry"), task.get("setup", ""), json.dumps(task["tests"], sort_keys=True),
               C.TEST_TIMEOUT, C.MEM_LIMIT_MB)


def _task_ladder_hash(task):
    lad = task.get("ladder") if task.get("ladder") is not None else task.get("ladder_recipe")
    if isinstance(lad, dict) and lad.get("from_tests"):  # stdio recipe: the base inputs are the tests
        lad = dict(lad, tests=[t.get("input") for t in task["tests"]])
    return sha(task["kind"], task.get("entry"), task.get("setup", ""), json.dumps(lad, sort_keys=True),
               C.TRACE_MAX_EVENTS, C.TRACE_RUN_TIMEOUT, C.TIMING_RUN_LIMIT, C.MEM_LIMIT_MB,
               os.environ.get("STDIO_ROW_RESAMPLE", "0"))


def _uniq(items):
    uniq = {}
    for t, c in items:
        uniq.setdefault((t["id"], c), (t, c))
    return uniq


def evaluate(items, desc="tests"):
    """items: list of (task, code) -> list of dicts {correct, status, passed, total}."""
    cache = _cache("tests")
    th = {}

    def one(it):
        task, code = it
        k = sha("test", TEST_VERSION, th[task["id"]], code)
        v = cache.get(k)
        if v is None:
            if not code.strip():
                v = {"correct": False, "status": "empty", "passed": 0, "total": len(task["tests"])}
            else:
                r = test_program(task, code)
                v = {"correct": r["correct"], "status": r.get("status"), "passed": r.get("passed", 0),
                     "total": r.get("total", 0)}
            cache.put(k, v)
        return v

    uniq = _uniq(items)
    for t, _ in uniq.values():
        if t["id"] not in th:
            th[t["id"]] = _task_test_hash(t)
    res = dict(zip(uniq.keys(), parallel_map(one, list(uniq.values()), desc=desc)))
    return [res[(t["id"], c)] for t, c in items]


def _slim(tr):
    """Keeps per-line hit counts only for the largest successful run of each ladder (the only run
    the fingerprint reads them from) so the trace cache stays small."""
    last = {}
    for i, r in enumerate(tr.get("runs") or []):
        if r.get("status") in ("ok", "cap"):
            last[r.get("ladder", "main")] = i
    keep = set(last.values())
    runs = []
    for i, r in enumerate(tr.get("runs") or []):
        r = dict(r)
        if i not in keep:
            r.pop("hits", None)
            r.pop("fcalls", None)
        runs.append(r)
    return dict(tr, runs=runs)


def valid_rungs(ref_traces):
    """Ladder rungs on which the input is trustworthy, judged by the task's reference solutions:
    a rung (ladder, size) is valid if at least one reference produced output there, every
    reference that produced output agrees, and none crashed or timed out there. Inputs that break
    the task's format or constraints (a scaled list whose count in the header was not scaled,
    sizes beyond the stated limits) make references crash or disagree and are dropped.
    Returns {ladder: set(sizes)}, or None when there are no references (no filtering)."""
    if not ref_traces:
        return None
    outs, bad = {}, set()
    for tr in ref_traces:
        for r in tr.get("runs") or []:
            key = (r.get("ladder", "main"), r["size"])
            if r.get("status") == "ok" and r.get("out"):
                outs.setdefault(key, set()).add(r["out"])
            elif r.get("status") in ("error", "timeout"):
                bad.add(key)
        for t in tr.get("timing") or []:
            if t.get("out"):
                outs.setdefault((t.get("ladder", "main"), t["size"]), set()).add(t["out"])
    valid = {}
    for (lad, size), o in outs.items():
        if len(o) == 1 and (lad, size) not in bad:
            valid.setdefault(lad, set()).add(size)
    return valid


def fingerprints(items, desc="fingerprint", rep=0):
    """items: list of (task, code) -> list of {by_ladder: {ladder: fp}, trace_status}.
    Use fingerprint.select_ladder / pick to get ONE comparable fingerprint per task.
    rep > 0 re-measures independently (repeatability check of the timing-based features).
    Only ladder rungs validated by the task's reference solutions (task["ref"], up to
    C.N_REF_CHECK of them) are used; tasks without references (curated) are not filtered."""
    from .sandbox import core_pool
    cache = _cache("traces")
    lh = {}

    def trace(task, code, r=0):
        k = sha("trace", TRACE_VERSION, lh[task["id"]], code) + (f"#rep{r}" if r else "")
        tr = cache.get(k)
        if tr is None:
            tr = _slim(trace_program(task, code))
            cache.put(k, tr)
        return tr

    uniq = _uniq(items)
    tasks = {}
    for t, _ in uniq.values():
        if t["id"] not in lh:
            lh[t["id"]] = _task_ladder_hash(t)
            tasks[t["id"]] = t
    cores = core_pool()[0]
    workers = min(C.FP_WORKERS, len(cores)) if cores else C.FP_WORKERS
    # 1) traces of reference solutions -> valid rungs per task
    ref_items = [(t, c) for t in tasks.values() for c in (t.get("ref") or [])[:C.N_REF_CHECK]]
    ref_tr = parallel_map(lambda it: trace(*it), ref_items, workers=workers, desc=desc + ":refs")
    by_task = {}
    for (t, _), tr in zip(ref_items, ref_tr):
        by_task.setdefault(t["id"], []).append(tr)
    valid = {tid: valid_rungs(by_task.get(tid)) for tid in tasks}

    # 2) the programs themselves, measured on valid rungs only
    def one(it):
        task, code = it
        return FP.compute_all(code, trace(task, code, rep), valid[task["id"]])

    res = dict(zip(uniq.keys(), parallel_map(one, list(uniq.values()), workers=workers, desc=desc)))
    return [res[(t["id"], c)] for t, c in items]
