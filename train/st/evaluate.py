"""Evaluation of a policy: N_SEEDS x m samples per task, tests + fingerprints, diversity metrics.

The same `evaluate()` serves the validation inside training, the final evaluation and the probe
(base model, no fingerprints). CLI (one GPU job):

  python -m st.evaluate --out DIR --tasks FILE[,FILE] --policy base|PATH.pt --m M
                        [--no_fp] [--shard I --nshards N] [--limit K] [--seed S]
                        [--probe_out FILE] [--keep_text]

writes DIR/<stem>.json (metrics), DIR/<stem>.rows.jsonl.gz, DIR/<stem>.pairs.jsonl, then DIR/DONE.
With --probe_out only the metrics and the probe rows {"task", "c", ...} (one per sample) are written.
Tasks are processed in chunks of EVAL_CHUNK tasks whose rows are kept under DIR/.parts, so a killed
job resumes at the last finished chunk."""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
import math
import os
import random
import shutil
import time
from pathlib import Path

from . import config as CFG
from . import reward
from .exp0 import prompts

EVAL_CHUNK = CFG._env("EVAL_CHUNK", 50, int)     # tasks per resumable chunk of the CLI
MAX_DRAWS = 500                                   # one-sample-per-seed draws enumerated per task
SCORE_KEYS = ("tests", "c", "measured", "slow", "ladder_fail", "fp")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def slim_fp(fp):
    return {"k1": fp.get("k1"), "k2": fp.get("k2"), "b": fp.get("b")} if fp and fp.get("ok") else None


# ------------------------------------------------------------------ metrics
def task_metrics(rows, N, m):
    """Numbers of ONE task from its rows (task, seed, sample, c, elig, fp, ...)."""
    n = len(rows)
    nc = sum(bool(r["c"]) for r in rows)
    cbar = [_mean([float(r["c"]) for r in rows if r["seed"] == z]) for z in range(N)]
    pass_seeds = 1.0 - math.prod(1.0 - (c or 0.0) for c in cbar)
    k = min(N, n)
    pass_iid = 1.0 - math.comb(n - nc, k) / math.comb(n, k) if n else 0.0
    E = [r for r in rows if r.get("elig")]
    groups = gsd = None
    gsd_all = 0.0
    if E:
        lab = reward.clusters([r["fp"] for r in E])
        by = {(r["seed"], r["sample"]): lab[i] for i, r in enumerate(E)}
        if m ** N <= MAX_DRAWS:
            draws = itertools.product(range(m), repeat=N)
        else:
            rng = random.Random(0)
            draws = [tuple(rng.randrange(m) for _ in range(N)) for _ in range(MAX_DRAWS)]
        cnt = [len({by[(z, s)] for z, s in enumerate(d) if (z, s) in by}) for d in draws]
        gsd_all = sum(cnt) / len(cnt)
        if len(E) >= 2:
            groups, gsd = float(len(set(lab))), gsd_all
    cross, same = [], []
    for a in range(len(E)):
        for b in range(a + 1, len(E)):
            v = reward.soft(reward.dist(E[a]["fp"], E[b]["fp"]))
            (cross if E[a]["seed"] != E[b]["seed"] else same).append(v)
    return {"task": rows[0]["task"] if rows else None, "n": n, "n_c": nc, "n_elig": len(E),
            "pass1": nc / n if n else 0.0, "pass_seeds": pass_seeds, "pass_iid": pass_iid,
            "cbar": cbar, "groups": groups, "groups_seed_draw": gsd, "groups_draw_all": gsd_all,
            "d_cross": _mean(cross), "d_same": _mean(same)}


def metrics(rows, N=None, m=None, task_order=None):
    """Aggregate metrics + `per_task` (for paired bootstraps) of evaluation rows."""
    N = N or CFG.N_SEEDS
    by = {}
    for r in rows:
        by.setdefault(r["task"], []).append(r)
    if m is None:
        m = max([1] + [r["sample"] + 1 for r in rows])
    order = [t for t in (task_order or by) if t in by]
    per = [task_metrics(by[t], N, m) for t in order]
    passing = [r for r in rows if r.get("tests")]
    E = [r for r in rows if r.get("elig")]
    out = {"n_tasks": len(per), "n_rows": len(rows), "N": N, "m": m,
           "pass1": _mean([float(r["c"]) for r in rows]) or 0.0,
           "pass_seeds": _mean([p["pass_seeds"] for p in per]) or 0.0,
           "pass_iid": _mean([p["pass_iid"] for p in per]) or 0.0,
           "pass1_by_seed": [_mean([float(r["c"]) for r in rows if r["seed"] == z]) for z in range(N)],
           "groups": _mean([p["groups"] for p in per]),
           "groups_seed_draw": _mean([p["groups_seed_draw"] for p in per]),
           "groups_draw_all": _mean([p["groups_draw_all"] for p in per]),
           "n_tasks_div": sum(p["groups"] is not None for p in per),
           "d_cross": _mean([p["d_cross"] for p in per]), "d_same": _mean([p["d_same"] for p in per]),
           "frac_trunc": _mean([float(r.get("truncated", False)) for r in rows]),
           "mean_ntok": _mean([r.get("ntok") for r in rows]),
           "frac_tests": _mean([float(bool(r.get("tests"))) for r in rows]),
           "frac_ladder_fail": _mean([float(bool(r.get("ladder_fail"))) for r in passing]),
           "frac_slow": _mean([float(bool(r.get("slow"))) for r in passing]),
           "frac_fp": _mean([float(bool(r.get("fp"))) for r in passing]),
           "frac_elig": _mean([float(bool(r.get("elig"))) for r in passing]),
           "mean_b": _mean([(r["fp"] or {}).get("b") for r in E])}
    out["gap"] = None if out["d_cross"] is None or out["d_same"] is None else out["d_cross"] - out["d_same"]
    out["per_task"] = per
    return out


# ------------------------------------------------------------------ one evaluation
def evaluate(policy, tasks, m, seed, need_fp=True, desc="", keep_text=False):
    """N_SEEDS x m rollouts per task -> (metrics, rows). Rows keep the full fingerprint (`fp`)."""
    from . import sampler
    N = CFG.N_SEEDS
    idx = [(i, z, k) for i in range(len(tasks)) for z in range(N) for k in range(m)]
    cache = {}

    def prompt(i, z):
        if (i, z) not in cache:
            cache[(i, z)] = policy.render(tasks[i], z)
        return cache[(i, z)]

    t0 = time.time()
    outs = sampler.rollout(policy, [{"p": prompt(i, z), "seed": z} for i, z, _ in idx], seed, desc=desc)
    t1 = time.time()
    codes = [prompts.extract_code(o["text"]) for o in outs]
    sc = reward.score_programs([(tasks[i], c) for (i, _, _), c in zip(idx, codes)], need_fp=need_fp,
                               desc=desc or "eval")
    rows, groups = [], {}
    for (i, z, k), o, code, s in zip(idx, outs, codes, sc):
        r = {"task": tasks[i]["id"], "seed": z, "sample": k, "code": code, "truncated": bool(o["truncated"]),
             "ntok": len(o["t"]), **{key: s.get(key) for key in SCORE_KEYS}}
        if keep_text:
            r["text"] = o["text"]
        rows.append(r)
        groups.setdefault(i, []).append(r)
    for g in groups.values():
        reward.group_reward(g, full=True)
    met = metrics(rows, N, m, [t["id"] for t in tasks])
    met.update(gen_s=t1 - t0, score_s=time.time() - t1)
    return met, rows


def disk_row(r):
    """Row as written to disk: fingerprint keys only."""
    return dict(r, fp=slim_fp(r.get("fp")))


def pairs(rows, k=50, seed=0):
    """Up to k random pairs of eligible codes of one task and different seeds (reward-hacking audit)."""
    by = {}
    for r in rows:
        if r.get("elig"):
            by.setdefault(r["task"], []).append(r)
    cand = [(t, a, b) for t, E in by.items() for a in range(len(E)) for b in range(a + 1, len(E))
            if E[a]["seed"] != E[b]["seed"]]
    out = []
    for t, a, b in random.Random(seed).sample(cand, min(k, len(cand))):
        x, y = by[t][a], by[t][b]
        d = reward.dist(x["fp"], y["fp"])
        fpk = lambda f: {q: f.get(q) for q in ("k1", "k2", "k3", "b", "cls", "rec", "nest")}  # noqa: E731
        out.append({"task": t, "seed_a": x["seed"], "seed_b": y["seed"], "d": d, "soft": reward.soft(d),
                    "fp_a": fpk(x["fp"]), "fp_b": fpk(y["fp"]), "code_a": x["code"], "code_b": y["code"]})
    return out


# ------------------------------------------------------------------ policies / files
def device():
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def apply_cfg(cfg):
    """Architecture settings stored with a checkpoint win over the environment (the state must fit)."""
    for k, v in (cfg or {}).items():
        if k.isupper() and hasattr(CFG, k):
            setattr(CFG, k, v)


def load_policy(spec, dev=None):
    from .model import Policy, model_path
    dev = dev or device()
    if spec == "base":
        return Policy(model_path(), "base", dev, lora=False)
    import torch
    ck = torch.load(spec, map_location="cpu", weights_only=False)
    apply_cfg(ck.get("cfg"))
    pol = Policy(model_path(), ck["mode"], dev)
    pol.load_state(ck["state"])
    log(f"loaded {spec}: mode {ck['mode']}, step {ck.get('step')}")
    return pol


def write_gz(path, rows):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def read_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def write_json(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    os.replace(tmp, path)


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--tasks", required=True, help="comma-separated task files (jsonl)")
    ap.add_argument("--policy", required=True, help="'base' or a checkpoint {state, mode, cfg}")
    ap.add_argument("--m", type=int, required=True, help="samples per (task, seed)")
    ap.add_argument("--no_fp", action="store_true", help="tests only (probe)")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0, help="first K tasks of every file (before sharding)")
    ap.add_argument("--seed", type=int, default=CFG._env("EVAL_SEED", 12345, int), help="sampling seed")
    ap.add_argument("--probe_out", default="", help="write probe rows {task, c, ...} to this jsonl")
    ap.add_argument("--keep_text", action="store_true", help="keep the raw completions in the rows")
    return ap.parse_args(argv)


def main(argv=None):
    a = parse(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "DONE").exists():
        log(f"{out} is done")
        return 0
    from . import data
    from . import exp0
    exp0.setup(out)
    try:
        policy = None
        probe_rows = []
        for fi, f in enumerate([x for x in a.tasks.split(",") if x]):
            stem = Path(f).name.split(".")[0]
            tasks = data.load_tasks(f)
            if a.limit:
                tasks = tasks[:a.limit]
            tasks = [t for i, t in enumerate(tasks) if i % a.nshards == a.shard]
            if (out / f"{stem}.json").exists() and not a.probe_out:
                log(f"{stem}: already evaluated")
                continue
            parts = out / ".parts"
            parts.mkdir(exist_ok=True)
            rows = []
            nch = max(1, math.ceil(len(tasks) / EVAL_CHUNK))
            for c in range(nch):
                pf = parts / f"{stem}.{c:04d}.jsonl.gz"
                if pf.exists():
                    rows += read_gz(pf)
                    continue
                if policy is None:
                    policy = load_policy(a.policy)
                chunk = tasks[c * EVAL_CHUNK:(c + 1) * EVAL_CHUNK]
                met, rs = evaluate(policy, chunk, a.m, a.seed + 7919 * c + 104729 * fi, need_fp=not a.no_fp,
                                   desc=f"{stem} {c + 1}/{nch}", keep_text=a.keep_text)
                log(f"{stem} chunk {c + 1}/{nch}: {len(chunk)} tasks, pass1 {met['pass1']:.3f}, "
                    f"pass_seeds {met['pass_seeds']:.3f}, gen {met['gen_s']:.0f}s, score {met['score_s']:.0f}s")
                write_gz(pf, rs)
                rows += rs
            met = metrics(rows, CFG.N_SEEDS, a.m, [t["id"] for t in tasks])
            met.update(policy=a.policy, file=str(f), m=a.m, seed=a.seed, need_fp=not a.no_fp,
                       shard=a.shard, nshards=a.nshards)
            if a.probe_out:
                probe_rows += [{"task": r["task"], "c": bool(r["c"]), "tests": bool(r["tests"]), "seed": r["seed"],
                                "sample": r["sample"], "truncated": r["truncated"], "ntok": r["ntok"]} for r in rows]
            else:
                write_gz(out / f"{stem}.rows.jsonl.gz", [disk_row(r) for r in rows])
                write_jsonl(out / f"{stem}.pairs.jsonl", pairs(rows))
            write_json(out / f"{stem}.json", met)
            log(f"{stem}: {met['n_tasks']} tasks, pass1 {met['pass1']:.3f}, pass_seeds {met['pass_seeds']:.3f}, "
                f"pass_iid {met['pass_iid']:.3f}, groups_seed_draw {met['groups_seed_draw']}")
        if a.probe_out:
            write_jsonl(a.probe_out, probe_rows)
        shutil.rmtree(out / ".parts", ignore_errors=True)
        (out / "DONE").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
        log("done", out)
        return 0
    finally:
        exp0.cleanup_tmp()


if __name__ == "__main__":
    raise SystemExit(main())
