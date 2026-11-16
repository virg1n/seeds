"""RUN_DIR/report.md from whatever exists (can be re-run at any time):   python -m st.report

Main question: does one sample per seed (pass_seeds, groups) beat N i.i.d. samples of a GRPO
baseline trained without seeds, and of the base model?"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path

from . import config as CFG

RUN = CFG.RUN_DIR
BASELINES = ("none_correct", "base")
COLS = [("pass1", "pass@1"), ("pass_seeds", "pass@N seeds"), ("pass_iid", "pass@N iid"), ("groups_draw_all", "groups/draw"),
        ("groups", "groups (>=2 elig)"), ("d_cross", "d cross"), ("d_same", "d same"), ("gap", "gap"),
        ("frac_slow", "slow"), ("frac_fp", "fp ok"), ("frac_ladder_fail", "ladder fail"), ("mean_b", "mean b"),
        ("mean_ntok", "tokens"), ("frac_trunc", "trunc")]


def _json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _jsonl(path):
    out = []
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def _f(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def table(head, rows):
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(r) + " |" for r in rows]


def paired_boot(a, b, key, n=1000, seed=0):
    """Mean difference a - b of a per-task metric over the common tasks, with a 95 % bootstrap CI
    (tasks resampled). Missing values (None) count as 0."""
    pa = {p["task"]: (p.get(key) or 0.0) for p in a}
    pb = {p["task"]: (p.get(key) or 0.0) for p in b}
    ids = sorted(set(pa) & set(pb))
    if not ids:
        return None
    d = [pa[t] - pb[t] for t in ids]
    rng = random.Random(seed)
    bs = sorted(sum(d[rng.randrange(len(d))] for _ in d) / len(d) for _ in range(n))
    return sum(d) / len(d), bs[int(0.025 * n)], bs[int(0.975 * n) - 1], len(ids)


def _avg(recs, key):
    xs = [r[key] for r in recs if isinstance(r.get(key), (int, float))]
    return sum(xs) / len(xs) if xs else None


def main():
    L = [f"# Seed training: {CFG.RUN_NAME}", "", f"written {time.strftime('%Y-%m-%d %H:%M')}", ""]
    L += ["Columns. **pass@N seeds**: at least one of N samples, one per seed, is correct (for policies without seeds the",
          "seed is only a label, so this is N i.i.d. samples). **pass@N iid**: N samples drawn from the pooled samples.",
          "**groups/draw**: expected number of different fingerprint groups among the correct solutions of one",
          "sample-per-seed draw, over all tasks (0 when nothing is correct). **d cross / d same**: mean fingerprint",
          "distance between correct solutions of different seeds / of the same seed; **gap** = cross - same",
          "(seeds mean something only if gap > 0). **slow**: share of test-passing solutions that are too slow.", ""]

    # ---------------- data
    dr = _json(RUN / "data" / "data_report.json")
    if dr:
        L += ["## Data", ""]
        fin, lad, pool = dr.get("final", {}), dr.get("final_ladder", {}), dr.get("pool", {})
        L += table(["split", "tasks", "by source:kind", "with ladder", "tasks with >= 2 reference groups"],
                   [[s, _f(fin.get(s, {}).get("n")), ", ".join(f"{k.split(':', 1)[1]} {v}" for k, v in
                                                               sorted(fin.get(s, {}).get("by_source_kind", {}).items())),
                     _f(lad.get(s, {}).get("with_ladder")), _f(lad.get(s, {}).get("ref_groups_ge2"))]
                    for s in ("train", "val", "test")])
        L += ["", f"Probe of the base model: solve rate {pool.get('solve_rate')}, solved candidates {pool.get('solved')}, "
              f"unsolved {pool.get('unsolved')} (added to the pool: {pool.get('unsolved_added')}).", ""]
    st = _json(RUN / "steps.json")
    if st:
        L += [f"Steps per variant: **{st['steps']}** ({st.get('why')}); {CFG.P_TASKS} tasks x {CFG.N_SEEDS} seeds x "
              f"{CFG.M_PER_SEED} rollouts per step.", ""]

    # ---------------- final evaluation
    finals = {}
    fdir = RUN / "final"
    for d in sorted(fdir.glob("*")) if fdir.exists() else []:
        for split in ("val", "test"):
            m = _json(d / f"{split}.json")
            if m:
                finals.setdefault(split, {})[d.name] = m
    order = lambda names: sorted(names, key=lambda n: (n == "base", n in BASELINES, n))  # noqa: E731
    for split in ("test", "val"):
        if split not in finals:
            continue
        ms = finals[split]
        any_m = next(iter(ms.values()))
        L += [f"## Final evaluation: {split} ({any_m.get('n_tasks')} tasks, {any_m.get('N')} seeds x {any_m.get('m')} samples)", ""]
        L += table(["policy"] + [c[1] for c in COLS],
                   [[n] + [_f(ms[n].get(k), 1 if k == "mean_ntok" else 3) for k, _ in COLS] for n in order(ms)])
        L += ["", "Per seed pass@1: " + "; ".join(f"{n}: " + " ".join(_f(x) for x in ms[n].get("pass1_by_seed", []))
                                                 for n in order(ms)), ""]
        rows = []
        for n in order(ms):
            for b in BASELINES:
                if b == n or b not in ms or n in BASELINES and b == "none_correct":
                    continue
                for key, lab in (("pass_seeds", "pass@N seeds"), ("pass1", "pass@1"), ("groups_draw_all", "groups/draw")):
                    r = paired_boot(ms[n].get("per_task", []), ms[b].get("per_task", []), key)
                    if r:
                        sig = "yes" if r[1] > 0 or r[2] < 0 else "no"
                        rows.append([n, b, lab, f"{r[0]:+.3f}", f"[{r[1]:+.3f}, {r[2]:+.3f}]", sig, str(r[3])])
        if rows:
            L += ["Paired differences (bootstrap over tasks, 1000 resamples):", ""]
            L += table(["policy", "vs", "metric", "difference", "95 % CI", "significant", "tasks"], rows) + [""]

    # ---------------- training
    tdir = RUN / "train"
    runs = sorted(d for d in tdir.glob("*") if d.is_dir()) if tdir.exists() else []
    if runs:
        L += ["## Validation during training", ""]
        for d in runs:
            ev = _jsonl(d / "evals.jsonl")
            if not ev:
                continue
            res = _json(d / "result.json") or {}
            L += [f"**{d.name}**" + (f" ({res.get('steps_done')} steps, {_f(res.get('hours'), 1)} h, "
                                     f"{_f(res.get('sec_per_step'), 0)} s/step"
                                     f"{', ' + res['stopped'] if res.get('stopped') else ''})" if res else " (running)"), ""]
            L += table(["step", "pass@1", "pass@N seeds", "pass@N iid", "groups/draw", "d cross", "d same", "gap", "slow",
                        "tokens"],
                       [[_f(e.get("step")), _f(e.get("pass1")), _f(e.get("pass_seeds")), _f(e.get("pass_iid")),
                         _f(e.get("groups_draw_all")), _f(e.get("d_cross")), _f(e.get("d_same")), _f(e.get("gap")),
                         _f(e.get("frac_slow")), _f(e.get("mean_ntok"), 0)] for e in ev]) + [""]
        L += ["## Training rollouts (mean of the first / last 20 steps)", ""]
        rows = []
        for d in runs:
            sj = _jsonl(d / "steps.jsonl")
            if not sj:
                continue
            for lab, part in (("first", sj[:20]), ("last", sj[-20:])):
                gd = [r["gain"].get("gain_dev_mean") for r in part if isinstance(r.get("gain"), dict)
                      and r["gain"].get("gain_dev_mean") is not None]
                rows.append([d.name, lab, str(len(sj))] + [_f(_avg(part, k)) for k in
                                                           ("R", "correct", "frac_mixed", "D", "S", "frac_elig", "frac_slow",
                                                            "frac_ladder_fail", "mean_b")] +
                            [_f(_avg(part, "mean_ntok"), 0), _f(sum(gd) / len(gd) if gd else None, 4)])
        L += table(["run", "steps", "of", "R", "correct", "groups with signal", "D", "S", "eligible", "slow",
                    "ladder fail", "mean b", "tokens", "mean abs(gain-1)"], rows) + [""]
        L += ["## Reward-hacking monitors", "",
              "Watch for: `slow` or `mean b` (scaling exponent of correct solutions) rising, `tokens` growing, `ladder fail`",
              "rising (answers fitted to the visible tests), `D` rising while `groups/draw` on validation does not.",
              "`final/<policy>/*.pairs.jsonl` holds up to 50 pairs of correct solutions of different seeds with their",
              "distance: label them offline (same / different algorithm) to check that the reward still means what it should.", ""]
    stt = _json(RUN / "state.json")
    if stt and stt.get("notes"):
        L += ["## Notes of the launch", ""] + [f"- {x}" for x in stt["notes"]] + [""]
    out = RUN / "report.md"
    RUN.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(time.strftime("%H:%M:%S"), "report ->", out, flush=True)


if __name__ == "__main__":
    main()
