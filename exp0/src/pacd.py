"""Optional loader for PACD (Python Algorithm Classification Dataset, arXiv:2510.27063:
~350 verified implementations of list sorting / primes / list search with algorithm-type labels).

No public download URL was found when this was written, so put the data under exp0/data/pacd/
(or set PACD_DIR) in one of these layouts and Part A will pick it up automatically:
  1) *.jsonl with fields  code, algorithm|algo|label|type, problem|task
  2) a tree  <problem>/<algorithm>/**/*.py   (problem name must contain sort / prime / search)
The calling convention of each program is detected automatically by probing candidate entry
functions against an oracle; programs that cannot be called are skipped (and counted).
"""
from __future__ import annotations

import ast
import json
import os
import random
from pathlib import Path

from . import config as C
from .curated import TASKS as CUR
from .sandbox import test_program
from .utils import log, parallel_map


def _root():
    p = os.environ.get("PACD_DIR")
    return Path(p) if p else C.DATA_DIR / "pacd"


def _problem(name):
    n = name.lower()
    if "sort" in n:
        return "sort"
    if "prime" in n:
        return "primes"
    if "search" in n:
        return "search"
    return None


def _read():
    root = _root()
    if not root.exists():
        return []
    rows = []
    for f in root.rglob("*.jsonl"):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                x = json.loads(line)
            except json.JSONDecodeError:
                continue
            code = x.get("code") or x.get("source")
            algo = x.get("algorithm") or x.get("algo") or x.get("label") or x.get("type")
            prob = _problem(str(x.get("problem") or x.get("task") or f.stem))
            if code and algo and prob:
                rows.append({"code": code, "algo": str(algo), "problem": prob})
    for f in root.rglob("*.py"):
        parts = f.relative_to(root).parts
        if len(parts) < 3:
            continue
        prob = _problem(parts[0])
        if prob:
            rows.append({"code": f.read_text(encoding="utf-8", errors="replace"), "algo": parts[1], "problem": prob})
    return rows


def _funcs(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)][::-1]  # last defined first


def _probe_tests(problem, variant):
    r = random.Random(5)
    tests = []
    if problem == "sort":
        for n in (0, 1, 5, 9):
            a = [r.randint(-20, 20) for _ in range(n)]
            tests.append(f"_x = {a!r}\n_r = F(_x)\nassert (_r if _r is not None else _x) == {sorted(a)!r}")
    elif problem == "primes":
        def primes_le(n):
            return [k for k in range(2, n + 1) if all(k % d for d in range(2, int(k ** .5) + 1))]
        for n in (2, 10, 29, 30):
            if variant == "list_le":
                tests.append(f"assert list(F({n})) == {primes_le(n)!r}")
            elif variant == "list_lt":
                tests.append(f"assert list(F({n})) == {primes_le(n - 1)!r}")
            elif variant == "is_prime":
                for k in (n, n + 1):
                    tests.append(f"assert bool(F({k})) == {k in primes_le(k)!r}")
            elif variant == "first_n":
                ps = primes_le(200)[:n]
                tests.append(f"assert list(F({n})) == {ps!r}")
    elif problem == "search":
        for n in (1, 6, 11):
            a = sorted(r.sample(range(100), n))
            for x in (a[n // 2], 1000):
                i = a.index(x) if x in a else -1
                call = f"F({a!r}, {x})" if variant == "ax" else f"F({x}, {a!r})"
                tests.append(f"_r = {call}\nassert _r == {i} or (_r is True and {i} >= 0) or "
                             f"(_r in (None, False, -1) and {i} < 0)")
    return tests


VARIANTS = {"sort": ["plain"], "primes": ["list_le", "list_lt", "is_prime", "first_n"], "search": ["ax", "xa"]}


def _ladder(problem, variant, entry):
    spec = CUR[problem]
    items = []
    for n in spec["sizes"]:
        rr = random.Random(7919 + n)
        args = spec["gen"](n, rr)
        if problem == "search" and variant == "xa":
            args = (args[1], args[0])
        items.append({"ladder": "main", "size": n, "arg": repr(args)})
    return items


def _adapt(row):
    for fn in _funcs(row["code"])[:4]:
        for var in VARIANTS[row["problem"]]:
            tests = [{"type": "assert", "src": f"F = {fn}\n" + t} for t in _probe_tests(row["problem"], var)]
            task = {"kind": "func", "entry": fn, "setup": "", "tests": tests}
            if test_program(task, row["code"])["correct"]:
                return {"entry": fn, "variant": var}
    return None


def build():
    rows = _read()
    if not rows:
        log(f"PACD not found under {_root()} -> skipped (see src/pacd.py for the expected layout)")
        return [], [], []
    log(f"PACD: {len(rows)} programs found, probing calling conventions ...")
    adapt = parallel_map(_adapt, rows, desc="pacd-probe")
    tasks, progs = {}, []
    skipped = 0
    for i, (row, ad) in enumerate(zip(rows, adapt)):
        if not ad:
            skipped += 1
            continue
        tid = f"pacd/{row['problem']}/{i}"
        tasks[tid] = {"id": tid, "source": "pacd", "kind": "func", "entry": ad["entry"], "setup": "",
                      "ladder": _ladder(row["problem"], ad["variant"], ad["entry"])}
        # programs are compared only within the same problem AND the same detected semantics
        # (e.g. is_prime vs primes-up-to-n are different computational problems)
        progs.append({"pid": f"pacd/{i}", "task": tid, "group": f"pacd/{row['problem']}/{ad['variant']}",
                      "algo": row["algo"], "code": row["code"]})
    log(f"PACD: {len(progs)} usable, {skipped} skipped (calling convention not recognised)")
    by = {}
    for p in progs:
        by.setdefault(p["group"], []).append(p)
    pairs = []
    rng = random.Random(0)
    for g, ps in by.items():
        allp = [(i, j) for i in range(len(ps)) for j in range(i + 1, len(ps))]
        rng.shuffle(allp)
        for i, j in allp[:4000]:  # cap per problem
            pairs.append({"a": ps[i]["pid"], "b": ps[j]["pid"], "task": g,
                          "same": int(ps[i]["algo"] == ps[j]["algo"]), "dataset": "pacd"})
    return list(tasks.values()), progs, pairs
