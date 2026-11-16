"""GRPO with fixed seeds: one training run on one GPU.

  python -m st.grpo --out DIR --mode film|prompt|none --reward full|correct --train FILE --val FILE
                    [--steps S | --steps_file F] [--calib N] [--max_hours H]

Step t takes P_TASKS tasks (consecutive slices of a per-epoch permutation seeded by (TRAIN_SEED,
epoch): the same tasks in the same order for every variant) and samples N_SEEDS x M_PER_SEED
rollouts of each (sampling seed fixed by (TRAIN_SEED, t)). The rollouts of one task are one group:
R from reward.group_reward, A = reward.advantages(R). One optimizer step per batch of rollouts
(on-policy, no ratio, no KL):
    loss = sum_i A_i * NLL_i / (n_rollouts * LEN_NORM)
Logs: steps.jsonl, rollouts.jsonl (every KEEP_ROLLOUTS_EVERY-th step), evals.jsonl (validation at
step 0, every EVAL_EVERY steps and at the end). Checkpoints: last.pt (resume), best.pt (highest
validation pass_seeds), final.pt; result.json; DONE. Resume from last.pt redraws the rollouts of
the resumed step with the same seed. --calib N: N steps + one validation on <= 24 tasks ->
calib.json {sec_per_step, sec_per_eval_task}, no checkpoints."""
from __future__ import annotations

import argparse
import functools
import json
import math
import os
import random
import time
from pathlib import Path

import numpy as np
import torch

from . import config as CFG
from . import reward, sampler
from .evaluate import _mean, device, evaluate, slim_fp, write_json
from .exp0 import prompts

CFG_KEYS = ("MODEL", "LORA_R", "LORA_ALPHA", "LORA_TARGETS", "N_SEEDS", "SEED_DIM", "FILM_HIDDEN", "FILM_RANK",
            "FILM_LAYERS", "FILM_MAX", "FILM_INIT")
VAL_SEED = 777_777        # the same validation rollouts' seed at every evaluation (comparable curves)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


@functools.lru_cache(maxsize=4)
def _perm(n, seed, epoch):
    order = list(range(n))
    random.Random(seed * 1_000_003 + epoch).shuffle(order)
    return order


def step_tasks(n, P, step, seed=None):
    """Indices of the P tasks of a step: consecutive slices of a fresh permutation per epoch."""
    seed = CFG.TRAIN_SEED if seed is None else seed
    return [_perm(n, seed, i // n)[i % n] for i in range(step * P, (step + 1) * P)]


def gen_seed(step, seed=None):
    seed = CFG.TRAIN_SEED if seed is None else seed
    return 1_000_003 * (seed + 1) + 7919 * step


def save_atomic(obj, path):
    path = str(path)
    torch.save(obj, path + ".tmp")
    os.replace(path + ".tmp", path)


def trim_log(path, keep):
    """Keep the records r with keep(r["step"]); drops a torn last line."""
    path = Path(path)
    if not path.exists():
        return
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                if keep(json.loads(line)["step"]):
                    out.append(line if line.endswith("\n") else line + "\n")
            except (ValueError, KeyError):
                pass
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(out)
    os.replace(tmp, path)


def append_jsonl(path, recs):
    with open(path, "a", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False, default=float) + "\n")


def _frac(rows, key):
    return _mean([float(bool(r.get(key))) for r in rows])


# ------------------------------------------------------------------ one step
class Trainer:
    def __init__(self, policy, mode, reward_kind, train, opt=None):
        self.policy, self.mode, self.full = policy, mode, reward_kind == "full"
        self.train = train
        self.opt = opt or torch.optim.AdamW(policy.param_groups(CFG.LR), betas=(0.9, 0.99), weight_decay=0.0)
        self.base_lr = [g["lr"] for g in self.opt.param_groups]
        self._prompts = {}

    def prompt(self, task, z):
        key = (task["id"], z if self.mode == "prompt" else 0)
        if key not in self._prompts:
            self._prompts[key] = self.policy.render(task, z)
        return self._prompts[key]

    def step(self, t):
        """One GRPO step. Returns (record for steps.jsonl, rollout rows)."""
        N, M, P = CFG.N_SEEDS, CFG.M_PER_SEED, CFG.P_TASKS
        tasks = [self.train[i] for i in step_tasks(len(self.train), P, t)]
        rows = [{"ti": j, "task": task["id"], "seed": z, "p": self.prompt(task, z)}
                for j, task in enumerate(tasks) for z in range(N) for _ in range(M)]
        t0 = time.time()
        outs = sampler.rollout(self.policy, rows, gen_seed(t), desc=f"step {t}")
        t1 = time.time()
        for r, o in zip(rows, outs):
            r.update(t=o["t"], truncated=bool(o["truncated"]), text=o["text"], code=prompts.extract_code(o["text"]))
        sc = reward.score_programs([(tasks[r["ti"]], r["code"]) for r in rows], need_fp=self.full, desc=f"step {t}")
        for r, s in zip(rows, sc):
            r.update({k: s.get(k) for k in ("tests", "c", "measured", "slow", "ladder_fail", "fp")})
        mixed = []
        for j in range(len(tasks)):
            g = [r for r in rows if r["ti"] == j]
            reward.group_reward(g, full=self.full)
            A = reward.advantages([r["R"] for r in g])
            for r, a in zip(g, A):
                r["A"] = a
            mixed.append(any(a != 0 for a in A))
        t2 = time.time()
        n = len(rows)
        live = [r for r in rows if r["A"] != 0]
        mult = min(1.0, (t + 1) / max(CFG.WARMUP, 1))
        for g, lr in zip(self.opt.param_groups, self.base_lr):
            g["lr"] = lr * mult
        self.opt.zero_grad(set_to_none=True)
        gn, nll, ntok, stepped = 0.0, [], [], False
        if live:
            nll, ntok = sampler.backward_pg(self.policy, live, [r["A"] / (n * CFG.LEN_NORM) for r in live],
                                            mb_tokens=CFG.MB_TOKENS)
            gn = float(torch.nn.utils.clip_grad_norm_(self.policy.trainable(), CFG.GRAD_CLIP))
            if math.isfinite(gn):
                self.opt.step()
                stepped = True
            else:
                log(f"step {t}: non-finite gradient norm, optimizer step skipped")
            self.opt.zero_grad(set_to_none=True)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        t3 = time.time()
        corr = [r for r in rows if r["c"]]
        meas = [r for r in rows if r["tests"] and r["measured"]]
        E = [r for r in rows if r.get("elig")]
        rec = {"step": t, "gen_s": t1 - t0, "score_s": t2 - t1, "train_s": t3 - t2, "n": n,
               "R": _mean([r["R"] for r in rows]), "correct": _frac(rows, "c"), "frac_mixed": _mean(mixed),
               "D": _mean([r["D"] for r in rows]), "S": _mean([r["S"] for r in rows]),
               "frac_elig": _frac(corr, "elig"), "frac_slow": _frac(meas, "slow"),
               "frac_ladder_fail": _frac(meas, "ladder_fail"), "frac_trunc": _frac(rows, "truncated"),
               "mean_ntok": _mean([len(r["t"]) for r in rows]), "mean_b": _mean([r["fp"].get("b") for r in E]),
               "pass_by_seed": [_frac([r for r in rows if r["seed"] == z], "c") for z in range(N)],
               "n_live": len(live), "stepped": stepped, "grad_norm": gn,
               "nll_tok": sum(nll) / max(1, sum(ntok)) if ntok else None,
               "lr": CFG.LR * mult, "gain": self.policy.gain_stats()}
        return rec, rows


# ------------------------------------------------------------------ main
def parse(argv=None):
    ap = argparse.ArgumentParser(description="GRPO with fixed seeds (one run, one GPU)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["film", "prompt", "none"], required=True)
    ap.add_argument("--reward", choices=["full", "correct"], required=True)
    ap.add_argument("--train", required=True)
    ap.add_argument("--val", required=True)
    ap.add_argument("--steps", type=int, default=0)
    ap.add_argument("--steps_file", default="", help="json {'steps': S} written by the orchestrator")
    ap.add_argument("--calib", type=int, default=0, help="only N steps + a short validation -> calib.json")
    ap.add_argument("--max_hours", type=float, default=0.0, help="safety stop (0: none)")
    ap.add_argument("--stop_after", type=int, default=0, help=argparse.SUPPRESS)  # tests: as if killed
    return ap.parse_args(argv)


def run_cfg(a):
    c = {k: getattr(CFG, k) for k in CFG_KEYS}
    c.update(mode=a.mode, reward=a.reward)
    return c


def main(argv=None):
    a = parse(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "DONE").exists():
        log(f"{out} is done")
        return "done"
    from . import data, exp0
    from .model import Policy, model_path
    exp0.setup(out)
    try:
        return _run(a, out, data, Policy, model_path)
    finally:
        exp0.cleanup_tmp()


def _run(a, out, data, Policy, model_path):
    train, val = data.load_tasks(a.train), data.load_tasks(a.val)
    if not train:
        raise SystemExit(f"empty training set {a.train}")
    if a.calib:
        S = a.calib
    elif a.steps:
        S = a.steps
    elif a.steps_file and os.path.exists(a.steps_file):
        S = int(json.load(open(a.steps_file, encoding="utf-8"))["steps"])
    else:
        raise SystemExit("give --steps, --calib or an existing --steps_file")
    dev = device()
    policy = Policy(model_path(), a.mode, dev)
    tr = Trainer(policy, a.mode, a.reward, train)
    cfg = run_cfg(a)
    n_tr = sum(p.numel() for p in policy.trainable())
    st = {"step": 0, "elapsed": 0.0, "last_eval": None, "best": None, "best_step": None, "step_s": []}
    last = out / "last.pt"
    if last.exists() and not a.calib:
        ck = torch.load(last, map_location="cpu", weights_only=False)
        policy.load_state(ck["state"])
        tr.opt.load_state_dict(ck["opt"])
        st = ck["st"]
        random.setstate(ck["rng"]["py"])
        np.random.set_state(ck["rng"]["np"])
        torch.set_rng_state(ck["rng"]["torch"])
        if dev == "cuda" and ck["rng"].get("cuda") is not None:
            torch.cuda.set_rng_state_all(ck["rng"]["cuda"])
        log(f"resumed from {last} at step {st['step']}")
        del ck
    fs, fr, fe = out / "steps.jsonl", out / "rollouts.jsonl", out / "evals.jsonl"
    if a.calib:
        for f in (fs, fr, fe):
            f.unlink(missing_ok=True)
    trim_log(fs, lambda s: s < st["step"])
    trim_log(fr, lambda s: s < st["step"])
    trim_log(fe, lambda s: st["last_eval"] is not None and s <= st["last_eval"])
    log(f"GRPO {a.mode}/{a.reward}: {len(train)} train / {len(val)} val tasks, {S} steps x {CFG.P_TASKS} tasks x "
        f"{CFG.N_SEEDS}x{CFG.M_PER_SEED} rollouts, trainable {n_tr / 1e6:.2f}M, device {dev}")

    def save_last():
        save_atomic({"state": policy.state(), "opt": tr.opt.state_dict(), "st": st, "cfg": cfg, "mode": a.mode,
                     "rng": {"py": random.getstate(), "np": np.random.get_state(), "torch": torch.get_rng_state(),
                             "cuda": torch.cuda.get_rng_state_all() if dev == "cuda" else None}}, last)

    def save_policy(name):
        save_atomic({"state": policy.state(), "mode": a.mode, "cfg": cfg, "step": st["step"]}, out / name)

    def run_eval(tasks):
        t0 = time.time()
        met, _ = evaluate(policy, tasks, CFG.EVAL_M, VAL_SEED, need_fp=True, desc=f"val@{st['step']}")
        met.pop("per_task", None)
        met.update(step=st["step"], sec=time.time() - t0, n_tasks=len(tasks))
        return met

    def do_eval():
        met = run_eval(val)
        append_jsonl(fe, [met])
        st["last_eval"] = st["step"]
        log(f"val @ step {st['step']}: pass1 {met['pass1']:.3f}, pass_seeds {met['pass_seeds']:.3f}, pass_iid "
            f"{met['pass_iid']:.3f}, groups_seed_draw {met['groups_seed_draw']}, gap {met['gap']}, {met['sec']:.0f}s")
        if st["best"] is None or met["pass_seeds"] >= st["best"]:
            st["best"], st["best_step"] = met["pass_seeds"], st["step"]
            save_policy("best.pt")
        save_last()

    t_run, el0, n_run, t_save = time.time(), st["elapsed"], 0, time.time()
    stopped = None
    if not a.calib and val and st["last_eval"] is None:
        do_eval()
    while st["step"] < S:
        if a.max_hours and el0 + time.time() - t_run > a.max_hours * 3600:
            stopped = "time"
            log(f"safety limit of {a.max_hours} h reached at step {st['step']} of {S}: stopping early")
            break
        t, t0 = st["step"], time.time()
        rec, rows = tr.step(t)
        append_jsonl(fs, [rec])
        if CFG.KEEP_ROLLOUTS_EVERY and t % CFG.KEEP_ROLLOUTS_EVERY == 0:
            append_jsonl(fr, [{"step": t, "task": r["task"], "seed": r["seed"], "code": r["code"], "c": r["c"],
                               "R": r["R"], "A": r["A"], "D": r["D"], "S": r["S"], "slow": r["slow"],
                               "truncated": r["truncated"], "fp": slim_fp(r["fp"])} for r in rows])
        st["step"] += 1
        st["elapsed"] = el0 + time.time() - t_run
        st["step_s"].append(time.time() - t0)
        n_run += 1
        sps = float(np.mean(st["step_s"][-20:]))
        log(f"step {st['step']}/{S}: R {rec['R']:.3f}, correct {rec['correct']:.3f}, mixed {rec['frac_mixed']:.2f}, "
            f"D {rec['D']}, S {rec['S']}, trunc {rec['frac_trunc']:.2f}, ntok {rec['mean_ntok']:.0f}, "
            f"gn {rec['grad_norm']:.3f} | gen {rec['gen_s']:.0f}s score {rec['score_s']:.0f}s train "
            f"{rec['train_s']:.0f}s | {sps:.0f} s/step, {st['elapsed'] / 3600:.2f} h, "
            f"ETA {(S - st['step']) * sps / 3600:.1f} h")
        if a.calib:
            continue
        if val and (st["step"] % CFG.EVAL_EVERY == 0 or st["step"] == S):
            do_eval()
            t_save = time.time()
        elif time.time() - t_save > CFG.CKPT_MINUTES * 60:
            save_last()
            t_save = time.time()
        if a.stop_after and n_run >= a.stop_after and st["step"] < S:
            save_last()
            log(f"stopped after {n_run} steps (--stop_after)")
            return "stopped"
    if a.calib:
        sub = val[:min(len(val), 24)]
        met = run_eval(sub) if sub else {"sec": 0.0}
        dts = st["step_s"][1:] or st["step_s"]
        write_json(out / "calib.json", {"sec_per_step": float(np.mean(dts)), "sec_per_eval_task": met["sec"] / max(1, len(sub)),
                                        "steps": st["step"], "step_s": st["step_s"], "eval_tasks": len(sub),
                                        "mode": a.mode, "reward": a.reward, "eval_m": CFG.EVAL_M})
    else:
        if val and st["last_eval"] != st["step"]:
            do_eval()
        save_policy("final.pt")
        if not (out / "best.pt").exists():
            save_policy("best.pt")
        write_json(out / "result.json", {
            "steps": S, "steps_done": st["step"], "complete": st["step"] >= S,
            "stopped": "stopped early (max_hours)" if stopped else None, "hours": st["elapsed"] / 3600,
            "sec_per_step": float(np.mean(st["step_s"] or [0])), "best_pass_seeds": st["best"],
            "best_step": st["best_step"], "trainable_M": n_tr / 1e6, "train_tasks": len(train), "cfg": cfg})
        if last.exists() and not stopped:
            last.unlink()
    (out / "DONE").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
    log("done", out)
    return "done"


if __name__ == "__main__":
    main()
