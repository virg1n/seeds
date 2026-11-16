"""CPU tests of st/data.py (no network):  python -m tests.test_data"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st import data as D  # noqa: E402
from st import exp0  # noqa: E402
from st import reward as RW  # noqa: E402
from st.exp0 import sandbox, scaler, utils  # noqa: E402

FIX = Path(__file__).parent / "fixtures"


class FakeTok:
    """Stands in for the model tokenizer: one token per whitespace-separated word."""

    def apply_chat_template(self, msgs, add_generation_prompt=True, tokenize=True):
        assert add_generation_prompt and tokenize
        return list(range(sum(len(m["content"].split()) for m in msgs) + 5))


def _heldout(test_rows):
    """Held-out set in exp0 format: one APPS-test problem (apps/4002) and one MBPP task."""
    r = next(x for x in test_rows if x["pid"] == "4002")
    apps = D.build_task(r, "apps")
    apps["id"], apps["ref"] = "apps/4002", apps.pop("reference")
    mbpp = {"id": "mbpp/1", "source": "mbpp", "kind": "func", "entry": "double", "setup": "",
            "text": "Write a function to double a number.", "starter": "", "example_test": "assert double(2) == 4",
            "tests": [{"type": "assert", "src": "assert double(2) == 4\nassert double(5) == 10"}],
            "ladder_recipe": scaler.func_recipe([(2,), (5,), (10,)], [1, 2, 4, 8], 0),
            "ref": ["def double(x):\n    return 2 * x\n"]}
    return [mbpp, apps]


def _no_calls(*a, **k):
    raise AssertionError("must come from the cache")


def run(tmp):
    exp0.setup(tmp)
    t0 = time.time()
    # ---- raw rows + their cache
    tr_rows = D.load_raw(str(FIX / "apps_mini_train.jsonl"), tmp / "raw" / "tr.jsonl")
    te_rows = D.load_raw(str(FIX / "apps_mini_test.jsonl"), tmp / "raw" / "te.jsonl")
    assert [r["pid"] for r in tr_rows] == ["0", "1", "2", "4", "6"], [r["pid"] for r in tr_rows]
    assert len(tr_rows[0]["solutions"]) == 4, "duplicate solution texts are dropped"
    orig_iter = D.data0._iter_lines
    D.data0._iter_lines = _no_calls
    try:
        assert len(D.load_raw(str(FIX / "apps_mini_train.jsonl"), tmp / "raw" / "tr.jsonl")) == 5
    finally:
        D.data0._iter_lines = orig_iter
    big = json.loads((FIX / "apps_mini_train.jsonl").read_text(encoding="utf-8").splitlines()[1])
    assert len(D.trim_row(big, max_tests=3)["io"]["inputs"]) == 3
    short = D.trim_row(big, max_chars=16)["io"]["inputs"]
    assert 0 < len(short) < 6 and all(len(json.dumps(i)) <= 16 for i in short), "long test inputs are dropped"
    part, complete = D.stream_raw(str(FIX / "apps_mini_train.jsonl"), limit=2)
    assert len(part) == 2 and not complete

    # ---- prep
    heldout = _heldout(te_rows)
    out = tmp / "data" / "candidates.jsonl"
    cands, rep = D.prep(out, tr_rows, te_rows, heldout, FakeTok(), cache_dir=tmp / "cache",
                        n_cand_train=100, n_cand_test=100, n_val=1, seed=1)
    dc = rep["decontam"]
    assert dc["appstr"] == {"raw": 5, "few_tests": 1, "kept": 4}, dc
    assert dc["appste"] == {"raw": 4, "heldout_pid": 1, "heldout_text": 1, "dup_text": 1, "kept": 1}, dc
    by = {t["id"]: t for t in D.load_tasks(out)}
    assert set(by) == {"appstr/0", "appstr/1", "appstr/2", "appste/4004"}, sorted(by)  # appstr/6: no valid ref
    assert len(by["appstr/0"]["ref"]) == 3 and len(by["appstr/1"]["ref"]) == 3
    assert all("return len(a)\n" not in c for c in by["appstr/0"]["ref"])
    assert by["appstr/0"]["kind"] == "func" and by["appstr/0"]["tests"][0] == {
        "type": "call", "args": "([1, 2, 2, 3],)", "expected": "[3]"}
    assert by["appstr/1"]["kind"] == "stdio" and by["appstr/1"]["ladder_recipe"]["type"] == "stdio"
    assert sum(t["split"] == "val" for t in by.values()) == 1
    assert all(t["prompt_tokens"] > D.PROMPT_SLACK and "reference" not in t for t in by.values())
    assert (out.with_name("prep_report.json")).exists()
    # resume: the reference validation comes from the cache
    orig_test = sandbox.test_program
    sandbox.test_program = _no_calls
    try:
        again, _ = D.prep(tmp / "data2" / "candidates.jsonl", tr_rows, te_rows, heldout, FakeTok(),
                          cache_dir=tmp / "cache", n_cand_train=100, n_cand_test=100, n_val=1, seed=1)
    finally:
        sandbox.test_program = orig_test
    assert [t["ref"] for t in again] == [t["ref"] for t in cands]
    print(time.strftime("%H:%M:%S"), f"prep ok ({time.time() - t0:.0f}s)", flush=True)

    # ---- pool
    t1 = time.time()
    probe_dir = tmp / "probe"
    probe_dir.mkdir()
    rows = []
    for t in cands:
        k = 2 if t["id"] in ("appstr/0", "appstr/1") else 0
        rows += [{"task": t["id"], "c": i < k, "ntok": 10} for i in range(2)]
    utils.write_jsonl(probe_dir / "shard0.jsonl", rows[: len(rows) // 2])
    utils.write_jsonl(probe_dir / "shard1.jsonl", rows[len(rows) // 2:])
    probe = D.read_probe(probe_dir)
    assert probe["appstr/0"] == {"n": 2, "correct": 2}
    train, val, test, rep = D.pool(tmp / "data", D.load_tasks(out), probe, heldout, FakeTok(), cache_dir=tmp / "cache",
                                   n_test=2, need_ladder=False, keep_min=1, zero_frac=0.5, seed=0)
    for name in ("train", "val", "test"):
        assert (tmp / "data" / f"{name}.jsonl").exists()
    rp = json.loads((tmp / "data" / "data_report.json").read_text(encoding="utf-8"))
    assert {"pool", "measured", "prep", "final", "final_ladder"} <= set(rp)
    assert [t["id"] for t in test] == ["mbpp/1", "apps/4002"] and all(t["split"] == "test" for t in test)
    assert all("probe" not in t and t["prompt_tokens"] > 0 for t in test)
    tid = {t["id"] for t in train}
    solved = {t["id"] for t in train if t["probe"]["correct"] >= 1}
    assert solved == {"appstr/0", "appstr/1"} - {t["id"] for t in val}, (tid, solved)
    assert len(tid - solved) == min(len(solved), sum(t["split"] == "train" and probe[t["id"]]["correct"] == 0
                                                     for t in cands)), "ZERO_FRAC = 0.5 of the pool"
    allt = {t["id"]: t for t in train + val + test}
    for t in allt.values():
        assert isinstance(t["rungs"], list) and all(isinstance(s, int) for s in t["rungs"]) and t["rungs"] == sorted(t["rungs"])
        assert set(t["ref_out"]) <= {str(s) for s in t["rungs"]} and set(t["ref_time"]) <= {str(s) for s in t["rungs"]}
        assert all(f["ok"] and f["ladder"] == t["lad"] for f in t["ref_fp"])
        assert t["ref_groups"] == len({x for x in RW.clusters(t["ref_fp"]) if x is not None})
        print(f"   {t['id']:12s} {t['split']:5s} lad={t['lad']} rungs={len(t['rungs'])} ref_out={len(t['ref_out'])} "
              f"refs={len(t.get('ref') or [])} fps={len(t['ref_fp'])} groups={t['ref_groups']} "
              f"{[f['k1'] for f in t['ref_fp']]}", flush=True)
    cd = allt["appstr/0"]
    assert cd["lad"] == "A" and len(cd["rungs"]) >= 3 and len(cd["ref_out"]) >= 3, cd["lad"]
    assert cd["ref_groups"] >= 1
    assert allt["mbpp/1"]["lad"] is not None
    # the measurement drives st.reward: a reference passes the ladder check, hard-coded answers do not
    m = RW.measure(cd, cd["ref"][0])
    assert m["fp"] and not m["ladder_fail"] and not m["slow"], m
    hard = "def count_distinct(a):\n    return {4: 3, 3: 1, 8: 8, 1: 1, 12: 7, 17: 3}.get(len(a), 0)\n"
    assert sandbox.test_program(cd, hard)["correct"]
    assert RW.measure(cd, hard)["ladder_fail"]
    # NEED_LADDER drops train tasks without a measurable ladder; resume comes from the cache
    orig_trace = sandbox.trace_program
    sandbox.trace_program = _no_calls
    try:
        train2, _, _, rep2 = D.pool(tmp / "data", D.load_tasks(out), probe, heldout, FakeTok(), cache_dir=tmp / "cache",
                                    n_test=2, need_ladder=True, keep_min=1, zero_frac=0.5, seed=0)
    finally:
        sandbox.trace_program = orig_trace
    assert {t["id"] for t in train2} == {t["id"] for t in train if t["lad"] and len(t["rungs"]) >= 3}
    assert rep2["need_ladder_dropped"] == len(train) - len(train2)
    print(time.strftime("%H:%M:%S"), f"pool ok ({time.time() - t1:.0f}s)", flush=True)


def test_helpers():
    ts = [{"id": f"a/{i}", "source": "a"} for i in range(10)] + [{"id": f"b/{i}", "source": "b"} for i in range(30)]
    D.split_val(ts, 4, 0)
    val = [t for t in ts if t["split"] == "val"]
    assert len(val) == 4 and sum(t["source"] == "a" for t in val) == 1
    held = [{"id": f"mbpp/{i}", "source": "mbpp"} for i in range(3)] + [{"id": f"apps/{i}", "source": "apps"} for i in range(3)]
    assert [t["id"] for t in D.select_test(held, 2)] == ["mbpp/0", "apps/0"]
    assert [t["id"] for t in D.select_test(held, 3)] == ["mbpp/0", "mbpp/1", "apps/0"]
    assert [t["id"] for t in D.select_test(held, 10)] == [t["id"] for t in held]
    assert D.text_hash("Hello   World\n") == D.text_hash(" hello world ")
    assert D.heldout_keys(held)[0] == {"0", "1", "2"}
    # ref_out needs >= 2 agreeing references and no error
    fake = {"runs": [{"ladder": "A", "size": s, "status": "ok", "out": f"o{s}", "lines": 10 * s} for s in (1, 2, 4, 8)],
            "timing": [{"ladder": "A", "size": s, "t": 1e-3 * s, "out": f"o{s}"} for s in (1, 2, 4, 8)]}
    other = json.loads(json.dumps(fake))
    other["runs"][3]["out"] = "different"
    other["timing"][3]["out"] = "different"
    s = D.summarize_traces(["x = 1\n", "y = 2\n"], [fake, fake])
    assert s["lad"] == "A" and s["rungs"] == [1, 2, 4, 8] and s["ref_out"] == {str(k): f"o{k}" for k in (1, 2, 4, 8)}
    assert s["ref_time"]["8"] == 8e-3
    s = D.summarize_traces(["x = 1\n", "y = 2\n"], [fake, other])
    assert s["rungs"] == [1, 2, 4] and "8" not in s["ref_out"]
    s = D.summarize_traces(["x = 1\n"], [fake])
    assert s["ref_out"] == {} and s["rungs"] == [1, 2, 4, 8], "one reference is not enough for ref_out"
    print(time.strftime("%H:%M:%S"), "helpers ok", flush=True)


if __name__ == "__main__":
    test_helpers()
    tmp = Path(tempfile.mkdtemp(prefix="st_test_data_"))
    try:
        run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        exp0.cleanup_tmp()
    print("all data tests passed", flush=True)
