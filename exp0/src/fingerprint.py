"""Execution fingerprint phi of a program and the distance d_phi.

phi has three levels, all computed from *execution* (traces on a ladder of growing inputs):

  L1  scaling      empirical growth exponent of executed line events (and, when C builtins hide
                   work, of untraced wall time) -> complexity class; growth of recursion depth.
  L2  scheme       recursion type (none / linear / branching), memoisation, nesting depth of loops
                   that actually iterate.
  L3  primitives   which data-structure / library primitives were actually executed
                   (heap, sort, set, dict, counter, deque, bisect, itertools, memo, math, re).
"""
from __future__ import annotations

import ast
import math

import numpy as np

from . import config as C

CATS = ["heap", "sort", "set", "dict", "counter", "deque", "bisect", "itertools", "memo", "math", "re"]

HEAP_NAMES = {"heappush", "heappop", "heapify", "heappushpop", "heapreplace", "nlargest", "nsmallest"}
BISECT_NAMES = {"bisect", "bisect_left", "bisect_right", "insort", "insort_left", "insort_right"}
ITER_NAMES = {"permutations", "combinations", "combinations_with_replacement", "product", "accumulate",
              "groupby", "chain", "islice", "zip_longest", "starmap", "takewhile", "dropwhile",
              "compress", "pairwise", "cycle", "tee", "filterfalse"}
NAME_CAT = {"set": "set", "frozenset": "set", "dict": "dict", "defaultdict": "dict", "OrderedDict": "dict",
            "Counter": "counter", "deque": "deque", "sorted": "sort", "lru_cache": "memo", "cache": "memo"}
MOD_CAT = {"heapq": "heap", "bisect": "bisect", "itertools": "itertools", "math": "math", "re": "re",
           "functools": "memo"}

# slope bins for ladders spanning ~2 decades: log n gives ~0.1-0.25, n log n gives ~1.1-1.25
CLASS_BINS = [(0.08, "O(1)"), (0.38, "O(log n)"), (0.75, "O(sqrt n)"), (1.08, "O(n)"), (1.6, "O(n log n)"),
              (2.5, "O(n^2)"), (3.5, "O(n^3)"), (1e9, "O(exp)")]


# ------------------------------------------------------------------ static analysis
def _call_cat(node):
    f = node.func
    if isinstance(f, ast.Name):
        if f.id in NAME_CAT:
            return NAME_CAT[f.id]
        if f.id in HEAP_NAMES:
            return "heap"
        if f.id in BISECT_NAMES:
            return "bisect"
        if f.id in ITER_NAMES:
            return "itertools"
    elif isinstance(f, ast.Attribute):
        if f.attr == "sort":
            return "sort"
        if isinstance(f.value, ast.Name):
            mod = f.value.id
            if mod == "collections":
                return NAME_CAT.get(f.attr)
            if mod == "functools":
                return "memo" if f.attr in ("lru_cache", "cache") else None
            if mod in MOD_CAT:
                return MOD_CAT[mod]
    return None


# primitives whose use is NOT visible as a C/Python call event (literals, constructors = type
# calls, decorators). Everything else (sorted/list.sort, heapq, bisect, math, re, set/dict/deque
# methods, Counter methods) is counted only from real call events, never from source lines.
STATIC_ONLY = {"set", "dict", "deque", "counter", "itertools", "memo"}


def static_info(code: str):
    """loops: list of {line, parent (index or None), fn (co_firstlineno of the enclosing function or
    None at module level), comp (comprehension generator)}; prim_lines: cat -> source lines."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"loops": [], "prim_lines": {}, "ok": False}
    loops = []
    prim_lines = {}

    def add(cat, line):
        if cat in STATIC_ONLY:
            prim_lines.setdefault(cat, set()).add(line)

    def visit(node, parent, fn):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            decs = getattr(node, "decorator_list", [])
            first = min([node.lineno] + [d.lineno for d in decs])  # == code.co_firstlineno
            for dec in decs:
                d = dec.func if isinstance(dec, ast.Call) else dec
                name = d.attr if isinstance(d, ast.Attribute) else getattr(d, "id", "")
                if name in ("lru_cache", "cache"):
                    body0 = node.body[0].lineno if isinstance(node.body, list) and node.body else node.lineno
                    add("memo", body0)
                visit(dec, parent, fn)
            for ch in (node.body if isinstance(node.body, list) else [node.body]):
                visit(ch, None, first)
            return
        if isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            loops.append({"line": node.lineno, "parent": parent, "fn": fn, "comp": False})
            me = len(loops) - 1
            visit(node.iter if hasattr(node, "iter") else node.test, parent, fn)
            for ch in node.body:
                visit(ch, me, fn)
            for ch in node.orelse:
                visit(ch, parent, fn)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            if isinstance(node, ast.SetComp):
                add("set", node.lineno)
            if isinstance(node, ast.DictComp):
                add("dict", node.lineno)
            cur = parent
            for _ in node.generators:
                loops.append({"line": node.lineno, "parent": cur, "fn": fn, "comp": True})
                cur = len(loops) - 1
            for ch in ast.iter_child_nodes(node):
                visit(ch, cur, fn)
            return
        if isinstance(node, ast.Set):
            add("set", node.lineno)
        elif isinstance(node, ast.Dict):
            add("dict", node.lineno)
        elif isinstance(node, ast.Call):
            add(_call_cat(node), node.lineno)
        for ch in ast.iter_child_nodes(node):
            visit(ch, parent, fn)

    for stmt in tree.body:
        visit(stmt, None, None)
    return {"loops": loops, "prim_lines": {k: sorted(v) for k, v in prim_lines.items()}, "ok": True}


# ------------------------------------------------------------------ helpers
def fit_slope(points):
    pts = [(math.log(x), math.log(y)) for x, y in points if x > 0 and y > 0]
    xs = sorted(set(p[0] for p in pts))
    if len(xs) < 2:
        return None
    if len(xs) >= 4:  # drop the smallest size: dominated by constant overhead
        pts = [p for p in pts if p[0] > xs[0]]
    x = np.array([p[0] for p in pts])
    y = np.array([p[1] for p in pts])
    if np.ptp(x) == 0:
        return None
    return float(np.polyfit(x, y, 1)[0])


def time_slope(points):
    # least squares; Theil-Sen was tried and was *less* repeatable on re-measurement (the noise is a
    # run-to-run shift of the whole timing curve, not single outliers)
    return fit_slope(points)


def complexity_class(b):
    if b is None:
        return "unk"
    for th, name in CLASS_BINS:
        if b < th:
            return name
    return "O(exp)"


LADDER_PRIORITY = {"main": 3, "A": 2, "B": 1, "nat": 0}
MIN_SIZES = 3


def _dyn_nesting(loops, hits, fcalls):
    """Max nesting depth of loops that really iterate. A loop is active if its header line fires
    on average >= 2 times per entry (1 iteration = 2 header events). Entries = header hits of the
    nearest enclosing statement loop, else number of calls of the enclosing function (1 at module
    level). Comprehension generators share one line, so a comprehension is judged as a whole."""
    def h(line):
        return hits.get(str(line), 0)

    def entries(i):
        p = loops[i]["parent"]
        while p is not None and loops[p]["comp"] and loops[p]["line"] == loops[i]["line"]:
            p = loops[p]["parent"]
        if p is not None:
            return h(loops[p]["line"])
        fn = loops[i]["fn"]
        return fcalls.get(str(fn), 1) if fn is not None else 1

    active = [h(lp["line"]) >= 3 and h(lp["line"]) >= 2 * max(1, entries(i)) for i, lp in enumerate(loops)]
    best = 0
    for i in range(len(loops)):
        if not active[i]:
            continue
        depth, p = 1, loops[i]["parent"]
        while p is not None:
            same_comp = loops[p]["comp"] and loops[p]["line"] == loops[i]["line"]
            depth += 1 if (active[p] or same_comp) else 0
            p = loops[p]["parent"]
        best = max(best, depth)
    return best


def incremental_slope(points, min_gain=50, min_rel=0.01):
    """Growth exponent with the constant part removed. For y = c + a*x^k a plain log-log fit is
    flattened by a large c (e.g. a 10^6-element table built at start-up). Here the slope is read
    from the increments between consecutive sizes: (y2 - y1) / (x2 - x1) ~ x^(k-1) at the
    geometric mean of x1, x2, so the slope of that + 1 estimates k for any spacing of sizes.
    Returns None when the total increase is too small to be measured (then the program is
    treated as constant work by the caller's plain fit)."""
    pts = sorted(points)
    if len(pts) < 3:
        return None
    y0 = pts[0][1]
    if pts[-1][1] - y0 < max(min_gain, min_rel * y0):
        return None
    der = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if x2 > x1 and y2 > y1:
            der.append((math.sqrt(x1 * x2), (y2 - y1) / (x2 - x1)))
    if len({x for x, _ in der}) < 2:
        return None
    s = fit_slope(der)
    return None if s is None else s + 1.0


def compute(code: str, trace: dict, lad: str, valid=None) -> dict:
    """Fingerprint measured on ONE ladder (the same ladder for every program of a task).
    valid: sizes of this ladder validated by reference solutions (None = no filtering)."""
    ok_size = (lambda s: True) if valid is None else (lambda s: s in valid)
    rs = sorted([r for r in (trace.get("runs") or []) if r.get("ladder", "main") == lad
                 and r.get("status") in ("ok", "cap") and ok_size(r["size"])], key=lambda r: r["size"])
    uncapped = [r for r in rs if r["status"] == "ok"]
    n_ok = len({r["size"] for r in uncapped})
    if not rs:
        return {"ok": False, "reason": "no_successful_run", "ladder": lad}
    sinfo = static_info(code)

    # ---- L1: scaling. Capped runs are censored observations (lower bounds), never fitted as exact.
    lpts = [(r["size"], max(1, r.get("lines", 0))) for r in uncapped]
    b_lines = fit_slope(lpts) if n_ok >= 2 else None
    b_inc = incremental_slope(lpts)
    if b_inc is not None and b_lines is not None and b_inc > b_lines:
        b_lines = b_inc  # a constant part flattened the plain fit
    # untraced timing (min over calibrated repeats): use only points well above the call-overhead
    # floor (>= 20 us and >= 10x the fastest run), so C-level work such as len(set(x)) is visible
    tall = [(t["size"], t["t"]) for t in trace.get("timing", []) if t.get("ladder", "main") == lad and t["t"] > 0
            and ok_size(t["size"])]
    floor = min([t for _, t in tall] or [0])
    tpts = [(x, t) for x, t in tall if t >= max(2e-5, 10 * floor)]
    enough_t = len({x for x, _ in tpts}) >= MIN_SIZES and max([t for _, t in tpts] or [0]) >= 2e-4
    b_time = time_slope(tpts) if enough_t else None
    if n_ok >= MIN_SIZES:
        b = b_lines
    elif n_ok == 2 and any(r["status"] == "cap" for r in rs) and b_lines is not None and b_lines >= 3.5:
        b = b_lines  # explosive growth seen on the two sizes before the cap
    else:
        b = None
    if b_time is not None and b is not None and b_time > b + 0.3:
        b = b_time  # work hidden in C builtins (sorted, sum, x in list, str ops ...)
    if b is None and b_time is None:
        return {"ok": False, "reason": "insufficient_sizes(%d)" % n_ok, "ladder": lad}
    if b is None:
        b = b_time
    cls = complexity_class(b)

    max_rec = max(r.get("max_rec", 0) for r in rs)
    if max_rec <= 1:
        depth_cls = "none"
    else:
        bd = fit_slope([(r["size"], max(1, r.get("max_depth", 1))) for r in rs])
        depth_cls = "const" if bd is None or bd < 0.15 else ("log" if bd < 0.6 else "linear")

    # ---- L2: scheme (from the largest successfully traced run)
    big = rs[-1]
    if big.get("max_rec", 0) <= 1:
        rec = "none"
    else:
        rec = "linear" if big.get("rec_calls", 0) <= 2 * big.get("max_rec", 1) else "branching"
    hits = big.get("hits", {})
    nest = min(3, _dyn_nesting(sinfo["loops"], hits, big.get("fcalls", {}))) if sinfo["ok"] else 0

    # ---- L3: primitives actually executed
    counts = {c: 0 for c in CATS}
    for src in ("c", "py"):
        for k, v in (big.get(src) or {}).items():
            if k in counts:
                counts[k] += v
    for cat, lines in sinfo["prim_lines"].items():
        counts[cat] += sum(hits.get(str(ln), 0) for ln in lines)
    prims = sorted(c for c, v in counts.items() if v > 0)
    # heuristic (documented): recursion + lru_cache, or recursion + a dict that is actually used
    memo = rec != "none" and ("memo" in prims or "dict" in prims)

    return {"ok": True, "ladder": lad, "n_points": len(rs), "n_uncapped": n_ok, "b_lines": b_lines,
            "b_time": b_time, "b": b, "cls": cls, "depth": depth_cls, "rec": rec, "memo": bool(memo),
            "nest": int(nest), "prims": prims, "counts": counts,
            "k1": "%s|%s" % (cls, depth_cls), "k2": "%s|%s|nest%d" % (rec, "memo" if memo else "-", nest),
            "k3": ",".join(prims) or "-"}


def compute_all(code: str, trace: dict, valid=None) -> dict:
    """valid: {ladder: set(sizes)} from fpstore.valid_rungs, or None (no filtering)."""
    lads = sorted({r.get("ladder", "main") for r in (trace.get("runs") or [])})
    return {"by_ladder": {lad: compute(code, trace, lad, None if valid is None else valid.get(lad, set()))
                          for lad in lads}, "trace_status": trace.get("status")}


def select_ladder(fpalls):
    """Chooses ONE measurement ladder for a task, given fingerprints of reference programs (or of
    the whole pool when no reference exists): the ladder on which most programs are measurable,
    ties broken by preferring controlled ladders over natural test-size variation."""
    cnt = {}
    for fa in fpalls:
        for lad, fp in ((fa or {}).get("by_ladder") or {}).items():
            cnt[lad] = cnt.get(lad, 0) + (1 if fp.get("ok") else 0)
    if not cnt or max(cnt.values()) == 0:
        return None
    return max(cnt, key=lambda l: (cnt[l], LADDER_PRIORITY.get(l, -1)))


def pick(fpall, lad):
    fp = ((fpall or {}).get("by_ladder") or {}).get(lad) if lad else None
    return fp if fp else {"ok": False, "reason": "ladder_missing", "ladder": lad}


def full_key(fp):
    return f"{fp['k1']}#{fp['k2']}#{fp['k3']}" if fp and fp.get("ok") else None


def level_key(fp, level):
    if not fp or not fp.get("ok"):
        return None
    return {"L1": fp["k1"], "L2": fp["k2"], "L3": fp["k3"], "phi": full_key(fp)}[level]


# ------------------------------------------------------------------ distances
def d1(a, b):
    ba, bb = a.get("b"), b.get("b")
    db = 1.0 if (ba is None) != (bb is None) else (0.0 if ba is None else min(1.0, abs(ba - bb) / 1.5))
    return 0.5 * db + 0.25 * (a["cls"] != b["cls"]) + 0.25 * (a["depth"] != b["depth"])


def d2(a, b):
    return ((a["rec"] != b["rec"]) + (a["memo"] != b["memo"]) + min(1.0, abs(a["nest"] - b["nest"]) / 2)) / 3


def d3(a, b):
    sa, sb = set(a["prims"]), set(b["prims"])
    if not sa and not sb:
        return 0.0
    return 1.0 - len(sa & sb) / len(sa | sb)


def d_phi(a, b, w=None):
    """Weighted sum of the level distances. Default weights = config.W_PHI, fixed in advance
    (scaling > scheme > primitives); equal weights are reported only as a sensitivity check."""
    if not (a and b and a.get("ok") and b.get("ok")):
        return float("nan")
    w = C.W_PHI if w is None else w
    return (w[0] * d1(a, b) + w[1] * d2(a, b) + w[2] * d3(a, b)) / sum(w)


def pair_features(a, b):
    """Feature vector for the learned variant of d_phi (logistic regression on Part A)."""
    if not (a and b and a.get("ok") and b.get("ok")):
        return None
    ba, bb = a.get("b") or 0.0, b.get("b") or 0.0
    return [min(3.0, abs(ba - bb)), float(a["cls"] != b["cls"]), float(a["depth"] != b["depth"]),
            float(a["rec"] != b["rec"]), float(a["memo"] != b["memo"]), abs(a["nest"] - b["nest"]), d3(a, b)]
