from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import config as C


def log(*a):
    msg = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(msg, flush=True)
    try:
        C.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(C.LOG_DIR / "pipeline.log", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def sha(*parts) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(str(p).encode("utf-8", "replace"))
        h.update(b"\0")
    return h.hexdigest()[:20]


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, default=str)


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class JsonlCache:
    """Append-only key->value cache persisted as jsonl (survives restarts)."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {r["k"]: r["v"] for r in read_jsonl(self.path) if "k" in r}
        self.lock = threading.Lock()
        self.f = open(self.path, "a", encoding="utf-8")

    def get(self, k):
        return self.data.get(k)

    def __contains__(self, k):
        return k in self.data

    def put(self, k, v):
        with self.lock:
            self.data[k] = v
            self.f.write(json.dumps({"k": k, "v": v}, ensure_ascii=False) + "\n")
            self.f.flush()


def parallel_map(fn, items, workers=None, desc="", every=30.0):
    """Thread pool map (work happens in subprocesses, so threads are enough). Keeps order."""
    items = list(items)
    workers = workers or C.WORKERS
    out = [None] * len(items)
    if not items:
        return out
    t0, last, done = time.time(), time.time(), 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, it): i for i, it in enumerate(items)}
        for fu in as_completed(futs):
            out[futs[fu]] = fu.result()
            done += 1
            if time.time() - last > every or done == len(items):
                last = time.time()
                log(f"  [{desc}] {done}/{len(items)}  ({time.time() - t0:.0f}s)")
    return out


# ------------------------------------------------------------------ disk budget
def dir_size_gb(p) -> float:
    total = 0
    for root, _, files in os.walk(p, onerror=lambda e: None):
        for fn in files:
            try:
                fp = os.path.join(root, fn)
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
            except OSError:
                pass
    return total / 1e9


def disk_status(tag=""):
    used = dir_size_gb(C.EXP_DIR)
    free = shutil.disk_usage(C.EXP_DIR).free / 1e9
    log(f"[disk{(' ' + tag) if tag else ''}] exp0 uses {used:.2f} GB (budget {C.DISK_LIMIT_GB} GB), free on fs {free:.1f} GB")
    return used, free


def ensure_budget(extra_gb: float, what: str):
    used, free = disk_status(f"before {what}")
    if used + extra_gb > C.DISK_LIMIT_GB:
        raise SystemExit(f"[disk] {what} needs ~{extra_gb:.1f} GB but exp0 already uses {used:.1f} GB "
                         f"of the {C.DISK_LIMIT_GB} GB budget. Free space (e.g. delete exp0/models/*) "
                         f"or raise DISK_LIMIT_GB.")
    if free < extra_gb + 0.5:
        raise SystemExit(f"[disk] only {free:.1f} GB free on filesystem, {what} needs ~{extra_gb:.1f} GB")


CHILDREN = []  # long-running subprocesses (generation workers) to kill if the disk budget is blown


def start_disk_monitor(period=120.0):
    """Background watchdog: warns at 95% of DISK_LIMIT_GB and aborts the run (killing workers)
    if exp0/ grows beyond the budget at any moment, not only at stage boundaries."""
    def loop():
        warned = False
        while True:
            time.sleep(period)
            try:
                used = dir_size_gb(C.EXP_DIR)
            except Exception:
                continue
            if used > C.DISK_LIMIT_GB:
                log(f"[disk] ABORT: exp0 uses {used:.2f} GB > budget {C.DISK_LIMIT_GB} GB")
                for p in CHILDREN:
                    try:
                        p.kill()
                    except Exception:
                        pass
                os._exit(5)
            if used > 0.95 * C.DISK_LIMIT_GB and not warned:
                warned = True
                log(f"[disk] WARNING: exp0 uses {used:.2f} GB (95% of the {C.DISK_LIMIT_GB} GB budget)")

    threading.Thread(target=loop, daemon=True).start()


def python_exe():
    return sys.executable
