"""CPU tests of st/reward.py:  python -m tests.test_reward"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st import config as CFG  # noqa: E402
from st import exp0  # noqa: E402
from st import reward as RW  # noqa: E402


def fp(b=1.0, cls="O(n)", depth="none", rec="none", memo=False, nest=1, prims=()):
    return {"ok": True, "b": b, "cls": cls, "depth": depth, "rec": rec, "memo": memo, "nest": nest,
            "prims": list(prims)}


LIN = fp()
LIN_NOISY = fp(b=1.04)                                   # the same algorithm, timing noise
NLOGN = fp(b=1.25, cls="O(n log n)", prims=("sort",))
QUAD = fp(b=2.0, cls="O(n^2)", nest=2)
REC = fp(b=1.0, depth="linear", rec="linear")


def rows(spec):
    """spec: list of (seed, c, fp, slow)"""
    return [{"seed": s, "c": c, "fp": f, "slow": sl} for s, c, f, sl in spec]


def mean_r(rs):
    return sum(r["R"] for r in rs) / len(rs)


def test_distance():
    assert RW.dist(LIN, LIN) == 0
    assert RW.soft(RW.dist(LIN, LIN_NOISY)) == 0, "timing noise must fall into the dead zone"
    assert RW.soft(RW.dist(LIN, QUAD)) > 0.4
    assert RW.soft(RW.dist(LIN, REC)) > 0.1
    # L3 is off: an extra primitive alone is not a different algorithm
    assert RW.dist(LIN, fp(prims=("sort", "set"))) == 0
    assert RW.dist(LIN, None) != RW.dist(LIN, None)  # nan


def test_policy_ordering():
    """collapsed < random < seeded, all equally correct (N = 4 seeds, M = 2)."""
    collapsed = rows([(z, True, LIN, False) for z in range(4) for _ in range(2)])
    # an i.i.d.-looking draw of "each rollout picks LIN or QUAD": LL, QQ, LQ, QL
    pat = [(LIN, LIN), (QUAD, QUAD), (LIN, QUAD), (QUAD, LIN)]
    random_ = rows([(z, True, pat[z][m], False) for z in range(4) for m in range(2)])
    seeded2 = rows([(z, True, LIN if z < 2 else QUAD, False) for z in range(4) for _ in range(2)])
    seeded4 = rows([(z, True, [LIN, NLOGN, QUAD, REC][z], False) for z in range(4) for _ in range(2)])
    r = [mean_r(RW.group_reward(g)) for g in (collapsed, random_, seeded2, seeded4)]
    assert r[0] < r[1] < r[2] < r[3], r
    assert abs(r[0] - (1 + CFG.GAMMA)) < 1e-9          # D = 0, S = 1
    assert all(a == 0 for a in RW.advantages([x["R"] for x in collapsed]))


def test_gates():
    g = RW.group_reward(rows([(0, True, LIN, False), (0, True, LIN, False),
                              (1, True, QUAD, False), (1, True, QUAD, True),     # the 4th is too slow
                              (2, True, None, False),                            # no fingerprint
                              (3, False, None, False)]))                         # wrong
    lin, quad, slow, nofp, wrong = g[0], g[2], g[3], g[4], g[5]
    assert wrong["R"] == 0
    assert slow["R"] == 1.0 and not slow["elig"], "too slow: correctness only"
    assert lin["elig"] and quad["elig"]
    # the slow rollout is not a partner: the eligible QUAD has no same-seed sibling -> neutral S
    assert quad["S"] is None and quad["D"] > 0
    elig = [r for r in g if r["elig"]]
    assert abs(nofp["R"] - (1 + sum(r["bonus"] for r in elig) / len(elig))) < 1e-9, "no fingerprint is neutral"
    assert slow["R"] < min(r["R"] for r in elig)
    # correctness-only reward keeps the diversity numbers for the logs
    g2 = RW.group_reward(rows([(0, True, LIN, False), (1, True, QUAD, False), (2, False, None, False)]), full=False)
    assert [r["R"] for r in g2] == [1.0, 1.0, 0.0] and g2[0]["D"] > 0


def test_advantages():
    a = RW.advantages([1, 1, 0, 0])
    assert abs(a[0] - 1) < 1e-9 and abs(a[2] + 1) < 1e-9
    a = RW.advantages([1.00, 1.02, 1.00, 1.02])           # tiny spread: the floor keeps it small
    assert max(abs(x) for x in a) <= 0.11
    assert RW.advantages([]) == []


def test_clusters():
    lab = RW.clusters([LIN, LIN_NOISY, QUAD, None, QUAD, NLOGN])
    assert lab[3] is None and lab[0] == lab[1] and lab[2] == lab[4] and lab[0] != lab[2]
    # measurement artifacts are not differences: timing under the floor, exponents across a bin edge
    c_fast = dict(fp(b=0.0, cls="O(1)", nest=0), b_lines=0.0, b_time=None)
    c_slow = dict(fp(b=1.0, cls="O(n)", nest=0), b_lines=0.0, b_time=1.0)
    assert RW.dist(c_fast, c_slow) == 0
    assert RW.soft(RW.dist(fp(b=1.02), fp(b=1.19, cls="O(n log n)"))) == 0
    assert RW.soft(RW.dist(dict(LIN, b_lines=1.0, b_time=None), dict(QUAD, b_lines=2.0, b_time=2.0))) > 0.3


def test_judge_trace():
    """judge_trace on hand-made traces: ladder check and the MILD slow gate."""
    task = {"id": "t", "lad": "A", "rungs": [1, 2, 4, 8, 256],
            "ref_out": {"1": "a", "2": "b", "4": "c"}, "ref_time": {"4": 0.001, "8": 0.002, "256": 0.01}}

    def tr(outs, times, status="ok"):
        return {"status": status,
                "runs": [{"ladder": "A", "size": s, "status": "ok", "out": o, "lines": 10 * s, "max_rec": 0,
                          "hits": {}, "fcalls": {}} for s, o in outs],
                "timing": [{"ladder": "A", "size": s, "t": t} for s, t in times]}

    code = "x = 1\n"
    ok = RW.judge_trace(task, code, tr([(1, "a"), (2, "b"), (4, "c"), (8, "zz")], [(4, 0.004), (8, 0.03)]))
    assert not ok["ladder_fail"] and not ok["slow"], ok        # 15x slower but under the 50 ms floor
    bad = RW.judge_trace(task, code, tr([(1, "a"), (2, "WRONG")], []))
    assert bad["ladder_fail"]
    slow = RW.judge_trace(task, code, tr([(1, "a")], [(8, 0.2)]))
    assert slow["slow"]                                        # 100x the slowest reference and > 50 ms
    big = RW.judge_trace(task, code, tr([(1, "a")], [(256, 5.0)]))
    assert not big["slow"], "inputs beyond SLOW_MAX_SCALE never make a program 'too slow'"


def test_real_program():
    """The whole path on a real tiny task: tests -> trace -> fingerprint -> group reward."""
    exp0.setup(CFG.RUNS_DIR / "_test_reward")
    C0, FP, fpstore, sandbox, scaler = exp0.C0, exp0.FP, exp0.fpstore, exp0.sandbox, exp0.scaler
    args = [([3, 1, 2, 5, 4, 9, 7, 8],), ([5, 4],), ([1],), ([2, 2, 3, 9, 1],)]
    task = {"id": "toy/max", "source": "apps", "kind": "func", "entry": "biggest", "setup": "", "text": "max of a list",
            "starter": "", "example_test": "",
            "tests": [{"type": "call", "args": repr(a), "expected": repr(max(a[0]))} for a in args],
            "ladder_recipe": scaler.func_recipe(args, C0.LADDER_FACTORS[:9], 0)}
    lin = "def biggest(a):\n    m = a[0]\n    for x in a:\n        if x > m:\n            m = x\n    return m\n"
    quad = ("def biggest(a):\n    for x in a:\n        ok = True\n        for y in a:\n            if y > x:\n"
            "                ok = False\n        if ok:\n            return x\n")
    wrong = "def biggest(a):\n    return a[0]\n"
    refs = [lin, "def biggest(a):\n    return max(a)\n"]
    traces = [fpstore._slim(sandbox.trace_program(task, r)) for r in refs]
    valid = fpstore.valid_rungs(traces)
    fps = [FP.compute_all(r, t, valid) for r, t in zip(refs, traces)]
    lad = FP.select_ladder(fps)
    assert lad is not None, fps
    rungs = sorted(valid[lad])
    outs, times = {}, {}
    for t in traces:
        for r in t["runs"]:
            if r.get("ladder") == lad and r.get("out"):
                outs.setdefault(r["size"], set()).add(r["out"])
        for x in t["timing"]:
            if x.get("ladder") == lad:
                times[x["size"]] = max(times.get(x["size"], 0), x["t"])
    task.update(lad=lad, rungs=rungs, ref_out={str(s): next(iter(o)) for s, o in outs.items() if len(o) == 1},
                ref_time={str(s): t for s, t in times.items()})
    res = RW.score_programs([(task, lin), (task, quad), (task, wrong), (task, lin)])
    assert [r["c"] for r in res] == [True, True, False, True], res
    assert res[0]["fp"] and res[1]["fp"], res
    assert not res[0]["ladder_fail"] and not res[0]["slow"]
    d = RW.soft(RW.dist(res[0]["fp"], res[1]["fp"]))
    print("  linear vs quadratic: d' = %.3f, classes %s / %s, quad slow=%s" % (
        d, res[0]["fp"]["cls"], res[1]["fp"]["cls"], res[1]["slow"]))
    assert d > 0.2
    g = RW.group_reward([dict(r, seed=z) for z, r in zip([0, 1, 2, 0], res)])
    assert g[2]["R"] == 0 and g[0]["R"] > 1
    exp0.cleanup_tmp()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
