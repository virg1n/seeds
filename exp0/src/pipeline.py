"""Entry point:  python -m src.pipeline [tools] [data] [partA] [gen] [analysis] [report]   (default: all)
Every stage is resumable: finished work is cached under results/ and skipped on re-run."""
from __future__ import annotations

import sys
import time

from . import config as C
from .utils import disk_status, log, start_disk_monitor

ALL = ["tools", "data", "partA", "gen", "analysis", "report"]


def main(argv):
    stages = [a for a in argv if not a.startswith("-")] or ALL
    bad = [s for s in stages if s not in ALL]
    if bad:
        raise SystemExit(f"unknown stage(s) {bad}; choose from {ALL}")
    for d in (C.RESULTS_DIR, C.CACHE_DIR, C.GEN_DIR, C.FIG_DIR, C.LOG_DIR, C.TMP_DIR, C.DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)
    log(f"=== experiment 0 | stages={stages} | smoke={C.SMOKE} | workers={C.WORKERS} | results={C.RESULTS_DIR}")
    disk_status("start")
    start_disk_monitor()
    t0 = time.time()
    tasks = None
    if "tools" in stages:
        from . import setup_tools
        setup_tools.main()
    if any(s in stages for s in ("data", "gen", "analysis")):
        from .data import prepare_tasks
        tasks = prepare_tasks()
    if "partA" in stages:
        from . import part_a
        log("=== Part A: fingerprint vs JPlag vs embeddings")
        part_a.run()
        disk_status("after part A")
    if "gen" in stages:
        from . import generate
        log("=== generation")
        generate.run_all(tasks)
        disk_status("after generation")
    if "analysis" in stages:
        from . import analysis
        log("=== Parts B and C")
        analysis.run(tasks)
    if "report" in stages:
        from . import report
        report.build()
    disk_status("end")
    log(f"=== done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main(sys.argv[1:])
