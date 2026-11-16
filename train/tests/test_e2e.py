"""CPU end-to-end test with the tiny random model:  MODEL_TINY=1 SMOKE=1 python -m tests.test_e2e

1) one GRPO step with injected "oracle" rollouts (reference solutions, one per seed, plus a wrong
   one): scoring, fingerprints, rewards, advantages, backward pass and optimizer step;
2) a real 2-step run of st.grpo (the random model writes garbage), killed after step 1 and resumed;
3) st.evaluate on the final checkpoint and on the base policy, the probe format, st.report."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("MODEL_TINY", "1")
os.environ.setdefault("SMOKE", "1")
os.environ["RUN_NAME"] = "_test_e2e"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch  # noqa: E402

from st import config as CFG  # noqa: E402
from st import data as D  # noqa: E402
from st import evaluate as EV  # noqa: E402
from st import exp0, grpo, sampler  # noqa: E402
from st.exp0 import utils  # noqa: E402
from st.model import Policy, model_path  # noqa: E402
from tests.test_data import FIX, FakeTok, _heldout  # noqa: E402


def build_data(tmp):
    exp0.setup(tmp)
    tr = D.load_raw(str(FIX / "apps_mini_train.jsonl"), tmp / "raw" / "tr.jsonl")
    te = D.load_raw(str(FIX / "apps_mini_test.jsonl"), tmp / "raw" / "te.jsonl")
    held = _heldout(te)
    cands, _ = D.prep(tmp / "data" / "candidates.jsonl", tr, te, held, FakeTok(), cache_dir=tmp / "cache",
                      n_cand_train=100, n_cand_test=100, n_val=1, seed=1)
    probe = {t["id"]: {"n": 2, "correct": 1} for t in cands}
    train, val, test, _ = D.pool(tmp / "data", cands, probe, held, FakeTok(), cache_dir=tmp / "cache", n_test=2,
                                 need_ladder=False, keep_min=1, zero_frac=0.0, seed=0)
    assert len(train) >= 2 and val and test
    return train, val, test


def oracle_step(train):
    """Trainer.step with rollouts replaced by reference solutions: seed z writes reference z (so
    seeds differ where the references do), the last rollout of every task is wrong."""
    pol = Policy(model_path(), "film", "cpu")
    by_id = {t["id"]: t for t in train}
    stop = sampler.stop_ids(pol.tok)[0]
    calls = {}

    def fake_rollout(policy, rows, seed, max_tokens=None, desc="", logprobs=False):
        out, seen = [], {}
        for r in rows:
            t = by_id[r["task"]]
            k = seen[r["task"]] = seen.get(r["task"], 0) + 1
            code = "def nope():\n    return 0\n" if k == CFG.N_SEEDS * CFG.M_PER_SEED else t["ref"][r["seed"] % len(t["ref"])]
            text = "```python\n" + code.strip("\n") + "\n```"
            ids = policy.tok.encode(text, add_special_tokens=False)[:200] + [stop]
            out.append({"t": ids, "truncated": False, "text": text})
        calls["n"] = len(rows)
        return out

    real = sampler.rollout
    sampler.rollout = fake_rollout
    try:
        tr = grpo.Trainer(pol, "film", "full", train)
        b0 = {n: w.B.detach().clone() for n, w in pol.lora.items()}
        u0 = pol.mod.U.detach().clone()
        rec, rows = tr.step(0)
    finally:
        sampler.rollout = real
    n = CFG.P_TASKS * CFG.N_SEEDS * CFG.M_PER_SEED
    assert calls["n"] == n == rec["n"] == len(rows)
    assert 0.5 < rec["correct"] < 1.0, rec
    assert rec["frac_mixed"] == 1.0 and rec["n_live"] > 0 and rec["stepped"] and rec["grad_norm"] > 0, rec
    assert all(r["R"] == 0 for r in rows if not r["c"]) and all(r["R"] >= 1 for r in rows if r["c"])
    assert all(r["A"] < 0 for r in rows if not r["c"])
    assert any(r["elig"] for r in rows), "fingerprints of the reference solutions were measured"
    assert any((w.B - b0[nm]).abs().sum() > 0 for nm, w in pol.lora.items()), "LoRA moved"
    assert (pol.mod.U - u0).abs().sum() > 0, "the seed modulator moved"
    print("ok oracle step: correct %.2f, R %.3f, D %s, S %s, eligible %s, grad norm %.3f" % (
        rec["correct"], rec["R"], rec["D"], rec["S"], rec["frac_elig"], rec["grad_norm"]))


def real_run(tmp, mode, reward):
    out = tmp / "train" / f"{mode}_{reward}"
    args = ["--out", str(out), "--mode", mode, "--reward", reward, "--train", str(tmp / "data" / "train.jsonl"),
            "--val", str(tmp / "data" / "val.jsonl"), "--steps", "2"]
    assert grpo.main(args + ["--stop_after", "1"]) == "stopped"
    assert (out / "last.pt").exists() and not (out / "DONE").exists()
    assert grpo.main(args) == "done"
    assert (out / "DONE").exists() and (out / "final.pt").exists() and (out / "best.pt").exists()
    assert not (out / "last.pt").exists()
    steps = utils.read_jsonl(out / "steps.jsonl")
    evals = utils.read_jsonl(out / "evals.jsonl")
    assert [r["step"] for r in steps] == [0, 1], steps
    assert [e["step"] for e in evals] == [0, 1, 2], [e["step"] for e in evals]
    res = json.loads((out / "result.json").read_text(encoding="utf-8"))
    assert res["complete"] and res["steps_done"] == 2
    assert grpo.main(args) == "done"
    ck = torch.load(out / "final.pt", map_location="cpu", weights_only=False)
    assert ck["mode"] == mode and ck["step"] == 2
    print(f"ok real run + resume: {mode}/{reward}")
    return out


def calib_run(tmp):
    out = tmp / "calib"
    grpo.main(["--out", str(out), "--mode", "none", "--reward", "correct", "--train", str(tmp / "data" / "train.jsonl"),
               "--val", str(tmp / "data" / "val.jsonl"), "--calib", "1"])
    c = json.loads((out / "calib.json").read_text(encoding="utf-8"))
    assert c["sec_per_step"] > 0 and c["sec_per_eval_task"] > 0
    print("ok calibration", {k: round(v, 2) for k, v in c.items() if isinstance(v, float)})


def eval_cli(tmp, ckpt):
    files = f"{tmp / 'data' / 'val.jsonl'},{tmp / 'data' / 'test.jsonl'}"
    for name, pol in (("film", str(ckpt)), ("base", "base")):
        out = tmp / "final" / name
        assert EV.main(["--out", str(out), "--tasks", files, "--policy", pol, "--m", "1"]) == 0
        m = json.loads((out / "val.json").read_text(encoding="utf-8"))
        assert m["n_rows"] == m["n_tasks"] * CFG.N_SEEDS and "per_task" in m and (out / "test.rows.jsonl.gz").exists()
    pr = tmp / "probe" / "shard0.jsonl"
    assert EV.main(["--out", str(tmp / "probe_jobs" / "s0"), "--tasks", str(tmp / "data" / "candidates.jsonl"),
                    "--policy", "base", "--m", "1", "--no_fp", "--shard", "0", "--nshards", "2",
                    "--probe_out", str(pr)]) == 0
    rows = utils.read_jsonl(pr)
    assert rows and set(rows[0]) >= {"task", "c"}
    assert D.read_probe(tmp / "probe")[rows[0]["task"]]["n"] == CFG.N_SEEDS
    print("ok evaluate CLI (checkpoint, base, probe)")


def metrics_unit():
    fa = {"ok": True, "b": 1.0, "cls": "O(n)", "depth": "none", "rec": "none", "memo": False, "nest": 1, "prims": []}
    fb = dict(fa, b=2.0, cls="O(n^2)", nest=2)
    rows = []
    for z in range(4):
        for s in range(2):
            ok = z < 3
            rows.append({"task": "t", "seed": z, "sample": s, "c": ok, "tests": ok, "elig": ok, "truncated": False, "ntok": 5,
                         "fp": (fa if z < 2 else fb) if ok else None, "slow": False, "ladder_fail": False})
    rows += [{"task": "u", "seed": z, "sample": s, "c": False, "tests": False, "elig": False, "truncated": True, "ntok": 9,
              "fp": None, "slow": False, "ladder_fail": False} for z in range(4) for s in range(2)]
    m = EV.metrics(rows, 4, 2)
    assert abs(m["pass1"] - 6 / 16) < 1e-9 and abs(m["pass_seeds"] - 0.5) < 1e-9 and m["n_tasks"] == 2
    t = m["per_task"][0]
    assert t["groups"] == 2 and t["groups_seed_draw"] == 2 and t["d_same"] == 0 and t["d_cross"] > 0.2
    assert abs(m["groups_draw_all"] - 1.0) < 1e-9 and m["gap"] > 0.2
    print("ok metrics")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="st_e2e_"))
    try:
        CFG.RUN_DIR = tmp
        metrics_unit()
        train, val, test = build_data(tmp)
        oracle_step(train)
        calib_run(tmp)
        out = real_run(tmp, "film", "full")
        real_run(tmp, "prompt", "correct")
        eval_cli(tmp, out / "final.pt")
        from st import report
        report.RUN = tmp
        report.main()
        txt = (tmp / "report.md").read_text(encoding="utf-8")
        assert "Final evaluation" in txt and "Validation during training" in txt
        print("ok report")
        print("ALL OK")
    finally:
        exp0.cleanup_tmp()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
