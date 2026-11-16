"""Reward of the seed experiment.

For one task we sample a GROUP of rollouts: N seeds x M rollouts per seed. For rollout i

    c_i  correctness: 1 if the program passes every test of the task AND (LADDER_CHECK) gives the
         same output as the reference solutions on the scaled inputs of the task's ladder
         (hard-coding the visible examples does not survive that), else 0.
    E    the "eligible" rollouts: c_i = 1, the execution fingerprint was measured, and the
         program is not TOO SLOW (see `measure`).
    d    distance between two fingerprints: scaling (L1) and computation scheme (L2); the
         primitives level (L3) is switched off by W_D because one extra `sorted()` games it.
         d' = max(0, d - DEADZONE) / (1 - DEADZONE): small differences are measurement noise.
    D_i  mean d'(i, j) over eligible rollouts j of OTHER seeds      (be different from other seeds)
    S_i  1 - mean d'(i, j) over eligible rollouts j of the SAME seed  (a seed is one algorithm)

    R_i = c_i * (1 + LAMBDA * D_i + GAMMA * S_i)                      for i in E

Wrong programs get 0. Correct programs outside E still get the reward for correctness:
  * too slow            -> R = 1                 (no diversity bonus: slowness is not a "new algorithm")
  * no fingerprint      -> R = 1 + mean bonus of E   (neutral: unmeasurable code is neither
                                                      rewarded nor punished)
D_i / S_i that cannot be computed (no eligible rollout of another seed / of the same seed) are
replaced by the group mean of the defined ones, i.e. they are neutral too.

Why this shape. All three policies below are equally correct; the reward orders them as we want:
  collapsed (every seed, one algorithm)        D = 0,   S = 1
  random    (each rollout picks A or B)        D ~ d/2, S ~ 1 - d/2
  seeded    (seed -> its own algorithm)        D ~ 2d/3 .. d, S = 1        <- the largest reward
Advantages are normalized inside the group: A_i = (R_i - mean) / max(std, STD_FLOOR).
"""
from __future__ import annotations

import threading
from collections import OrderedDict

from . import config as CFG
from .exp0 import C0, FP, fpstore, sandbox, scaler, utils


# ------------------------------------------------------------------ distance
def _flat(a):
    """No growth of executed lines: whatever grows is hidden inside C builtins (seen by timing only)."""
    return a.get("b_lines") is None or a["b_lines"] < 0.15


def d1_robust(a, b):
    """exp0's scaling distance d1 with two measurement artifacts removed (both showed up as false
    "different algorithm" pairs among solutions labelled the same on the exp0 pairs):
      * detection floor: both programs have flat line counts and only ONE has a measurable timing
        slope. The other one is usually the same C-level work running under the timer's floor, so
        the scaling of the two is treated as not comparable (no distance) rather than O(1) vs O(n);
      * class boundary: complexity classes are bins of the exponent; two exponents closer than
        CLASS_MIN_GAP on different sides of a bin edge do not count as different classes."""
    depth = 0.25 * (a["depth"] != b["depth"])
    if _flat(a) and _flat(b) and (a.get("b_time") is None) != (b.get("b_time") is None):
        return depth
    ba, bb = a.get("b"), b.get("b")
    if (ba is None) != (bb is None):
        return 0.5 + 0.25 * (a["cls"] != b["cls"]) + depth
    gap = 0.0 if ba is None else abs(ba - bb)
    cls = a["cls"] != b["cls"] and (ba is None or gap >= CLASS_MIN_GAP)
    return 0.5 * min(1.0, gap / 1.5) + 0.25 * cls + depth


CLASS_MIN_GAP = CFG._env("CLASS_MIN_GAP", 0.3, float)
ROBUST_L1 = CFG._env("ROBUST_L1", True, bool)


def dist(a, b, w=None):
    """Weighted fingerprint distance in [0, 1] with the levels of CFG.W_D; nan if a fingerprint is missing."""
    if not (a and b and a.get("ok") and b.get("ok")):
        return float("nan")
    w = CFG.W_D if w is None else w
    l1 = d1_robust(a, b) if ROBUST_L1 else FP.d1(a, b)
    tot = w[0] * l1 + w[1] * FP.d2(a, b) + (w[2] * FP.d3(a, b) if w[2] else 0.0)
    return tot / sum(w)


def soft(d, dead=None):
    dead = CFG.DEADZONE if dead is None else dead
    return max(0.0, d - dead) / (1.0 - dead)


def clusters(fps, tau=None):
    """Complete-linkage groups (every pair inside a group has d <= tau) of a list of fingerprints.
    Returns a list of labels (0..k-1), None where the fingerprint is missing."""
    tau = CFG.TAU if tau is None else tau
    idx = [i for i, f in enumerate(fps) if f and f.get("ok")]
    groups = [[i] for i in idx]

    def link(g, h):
        return max(dist(fps[a], fps[b]) for a in g for b in h)

    while len(groups) > 1:
        best, pair = None, None
        for x in range(len(groups)):
            for y in range(x + 1, len(groups)):
                v = link(groups[x], groups[y])
                if best is None or v < best:
                    best, pair = v, (x, y)
        if best is None or best > tau:
            break
        x, y = pair
        groups[x] = groups[x] + groups[y]
        del groups[y]
    lab = [None] * len(fps)
    for k, g in enumerate(sorted(groups, key=min)):
        for i in g:
            lab[i] = k
    return lab


# ------------------------------------------------------------------ measuring one program
_LAD_CACHE = OrderedDict()
_LAD_LOCK = threading.Lock()
_LAD_KEEP = 24


def ladder_inputs(task):
    """Inputs of the task's chosen ladder restricted to the rungs validated by the references
    (task["lad"], task["rungs"], written by st.data). Built once per task and kept in a small LRU:
    building multi-megabyte inputs for every rollout would stall the trainer."""
    key = task["id"]
    with _LAD_LOCK:
        if key in _LAD_CACHE:
            _LAD_CACHE.move_to_end(key)
            return _LAD_CACHE[key]
    lad, rungs = task.get("lad"), set(task.get("rungs") or [])
    items = [it for it in scaler.build_ladder(task) if it.get("ladder", "main") == lad and it["size"] in rungs]
    with _LAD_LOCK:
        _LAD_CACHE[key] = items
        while len(_LAD_CACHE) > _LAD_KEEP:
            _LAD_CACHE.popitem(last=False)
    return items


def _scale_ok(lad, size):
    """Rungs used for the 'too slow' test: inputs at most SLOW_MAX_SCALE times the test input
    (ladders A / B: size IS the growth factor); the natural ladder consists of the tests themselves."""
    return lad == "nat" or size <= CFG.SLOW_MAX_SCALE


def judge_trace(task, code, tr):
    """Fingerprint + the two checks read from one trace of `code` on the task's ladder.
    Returns {"fp": fingerprint or None, "ladder_fail": bool, "slow": bool, "trace_status": str}.

    ladder_fail  on a rung where >= 2 references agree on the output (task["ref_out"]) the program
                 raised an error or printed something else.
    slow         MILD efficiency gate. Only a program that is MUCH slower than the slowest
                 reference solution is "too slow": on some rung of moderate size (see _scale_ok)
                 it needs more than SLOW_FACTOR x the slowest reference's time and more than
                 SLOW_FLOOR seconds, or its traced run timed out there. Programs that are merely
                 one complexity class worse on small / moderate inputs are NOT slow."""
    lad = task.get("lad")
    rungs = set(task.get("rungs") or [])
    ref_out = task.get("ref_out") or {}
    ref_time = task.get("ref_time") or {}
    fp = FP.compute(code, tr, lad, valid=rungs)
    outs, errs, slow = {}, set(), False
    for r in tr.get("runs") or []:
        if r.get("ladder", "main") != lad or r["size"] not in rungs:
            continue
        if r.get("status") == "ok" and r.get("out"):
            outs[r["size"]] = r["out"]
        elif r.get("status") == "error":
            errs.add(r["size"])
        elif r.get("status") == "timeout" and _scale_ok(lad, r["size"]):
            slow = True
    for t in tr.get("timing") or []:
        if t.get("ladder", "main") != lad or t["size"] not in rungs:
            continue
        if t.get("out"):
            outs.setdefault(t["size"], t["out"])
        rt = ref_time.get(str(t["size"]))
        if rt is not None and _scale_ok(lad, t["size"]) and t["t"] > max(CFG.SLOW_FACTOR * rt, CFG.SLOW_FLOOR):
            slow = True
    fail = False
    if CFG.LADDER_CHECK:
        for s in rungs:
            exp = ref_out.get(str(s))
            if exp is not None and (s in errs or (s in outs and outs[s] != exp)):
                fail = True
                break
    return {"fp": fp if fp.get("ok") else None, "ladder_fail": fail, "slow": slow,
            "trace_status": tr.get("status"), "fp_reason": None if fp.get("ok") else fp.get("reason")}


def measure(task, code):
    """Traces `code` on the task's ladder (nothing is cached on disk: rollouts are unique)."""
    inputs = ladder_inputs(task)
    if not task.get("lad") or not inputs:
        return {"fp": None, "ladder_fail": False, "slow": False, "trace_status": "no_ladder", "fp_reason": "no_ladder"}
    tr = fpstore._slim(sandbox.trace_program(task, code, inputs=inputs))
    return judge_trace(task, code, tr)


# ------------------------------------------------------------------ scoring a batch of programs
def score_programs(items, need_fp=True, desc="score"):
    """items: list of (task, code). Runs the tests of every distinct program (in parallel), then
    traces the ones that pass (need_fp). Returns one dict per item:
      tests (bool), status, passed, total, measured (bool), fp, ladder_fail, slow, c (bool).
    c = tests and not ladder_fail. Without need_fp nothing is traced: c = tests."""
    uniq = OrderedDict()
    for t, code in items:
        uniq.setdefault((t["id"], code), (t, code))
    keys = list(uniq)

    def test_one(k):
        t, code = uniq[k]
        if not code.strip():
            return {"correct": False, "status": "empty", "passed": 0, "total": len(t["tests"])}
        r = sandbox.test_program(t, code)
        return {"correct": bool(r["correct"]), "status": r.get("status"), "passed": r.get("passed", 0),
                "total": r.get("total", 0)}

    tests = dict(zip(keys, utils.parallel_map(test_one, keys, workers=C0.WORKERS, desc=desc + ":tests", every=120.0)))
    res = {k: {"tests": v["correct"], "status": v["status"], "passed": v["passed"], "total": v["total"],
               "measured": False, "fp": None, "ladder_fail": False, "slow": False, "c": v["correct"]}
           for k, v in tests.items()}
    if need_fp:
        todo = [k for k in keys if tests[k]["correct"] and uniq[k][0].get("lad")]
        ms = utils.parallel_map(lambda k: measure(*uniq[k]), todo, workers=C0.FP_WORKERS, desc=desc + ":trace",
                                every=120.0)
        for k, m in zip(todo, ms):
            res[k].update(measured=True, fp=m["fp"], ladder_fail=m["ladder_fail"], slow=m["slow"],
                          trace_status=m["trace_status"], c=bool(tests[k]["correct"] and not m["ladder_fail"]))
    return [dict(res[(t["id"], code)]) for t, code in items]


# ------------------------------------------------------------------ reward of one group
def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def group_reward(rows, full=True):
    """rows: the rollouts of ONE task, dicts with seed (int), c (bool), fp (dict or None), slow (bool).
    Adds to every row: elig (bool), D, S (float or None), bonus (float), R (float).
    full=False is the correctness-only reward (R = c); D and S are still filled in when the
    fingerprints are there, so both kinds of runs log the same diversity numbers."""
    E = [i for i, r in enumerate(rows) if r["c"] and r.get("fp") and r["fp"].get("ok") and not r.get("slow")]
    dm = {}
    for a in range(len(E)):
        for b in range(a + 1, len(E)):
            v = soft(dist(rows[E[a]]["fp"], rows[E[b]]["fp"]))
            dm[(E[a], E[b])] = dm[(E[b], E[a])] = v
    for r in rows:
        r.update(elig=False, D=None, S=None, bonus=0.0, R=0.0)
    for i in E:
        oth = [dm[(i, j)] for j in E if rows[j]["seed"] != rows[i]["seed"]]
        sib = [dm[(i, j)] for j in E if j != i and rows[j]["seed"] == rows[i]["seed"]]
        rows[i]["elig"] = True
        rows[i]["D"] = _mean(oth)
        m = _mean(sib)
        rows[i]["S"] = None if m is None else 1.0 - m
    d_mean = _mean([rows[i]["D"] for i in E if rows[i]["D"] is not None]) or 0.0
    s_mean = _mean([rows[i]["S"] for i in E if rows[i]["S"] is not None]) or 0.0
    for i in E:
        r = rows[i]
        r["bonus"] = CFG.LAMBDA * (d_mean if r["D"] is None else r["D"]) + \
            CFG.GAMMA * (s_mean if r["S"] is None else r["S"])
    b_mean = _mean([rows[i]["bonus"] for i in E]) or 0.0
    for r in rows:
        if not r["c"]:
            continue
        if not r["elig"]:
            r["bonus"] = 0.0 if r.get("slow") else b_mean
        r["R"] = 1.0 + r["bonus"] if full else 1.0
    return rows


def advantages(rewards, floor=None):
    """GRPO advantages of one group: (R - mean) / max(std, STD_FLOOR); all zeros if the rewards are equal."""
    floor = CFG.STD_FLOOR if floor is None else floor
    n = len(rewards)
    if n == 0:
        return []
    mu = sum(rewards) / n
    var = sum((x - mu) ** 2 for x in rewards) / n
    if var <= 1e-12:
        return [0.0] * n
    sd = max(var ** 0.5, floor)
    return [(x - mu) / sd for x in rewards]
