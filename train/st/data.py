"""Training / validation / test tasks of the seed experiment.

    python -m st.data prep   -> RUN_DIR/data/candidates.jsonl (+ prep_report.json)
    python -m st.data pool   -> RUN_DIR/data/{train,val,test}.jsonl + data_report.json   (after the probe)

prep: APPS-train introductory problems (+ the APPS-test introductory problems that are NOT in the
held-out exp0 set), decontaminated against the held-out set by problem id and by a hash of the
normalized statement, turned into exp0-format tasks, reference solutions validated with the tests,
prompt length measured with the model's tokenizer, a validation split drawn at random.
pool: probe filter of the train candidates, held-out test set, and the reference measurement
(traces on the full input ladders -> chosen ladder, valid rungs, reference outputs / times /
fingerprints) that st.reward needs.

Every step is a function with explicit inputs (rows in memory, paths) so tests need no network;
`prep_cli` / `pool_cli` only pass config values."""
from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

from . import config as CFG
from . import exp0
from .exp0 import C0, FP, fpstore, prompts, sandbox, scaler, utils
from src import data as data0  # noqa: E402  (exp0 data module; sys.path is set by st.exp0)

APPS_TRAIN_URL = CFG._env("APPS_TRAIN_URL", "https://huggingface.co/datasets/codeparrot/apps/resolve/main/train.jsonl")
APPS_TEST_URL = CFG._env("APPS_URL", "https://huggingface.co/datasets/codeparrot/apps/resolve/main/test.jsonl")
MAX_SOLUTIONS = 24          # solutions kept per raw problem
PROMPT_SLACK = 12           # tokens reserved for the "Strategy s." prefix of mode `prompt`
_FP_SRC = utils.sha((Path(FP.__file__)).read_text(encoding="utf-8"))


def _log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def _write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, default=str)
    os.replace(tmp, path)


def load_tasks(path) -> list[dict]:
    """Tasks of a jsonl file written by this module (rungs as ints)."""
    tasks = utils.read_jsonl(path)
    for t in tasks:
        if t.get("rungs") is not None:
            t["rungs"] = [int(s) for s in t["rungs"]]
    return tasks


# ------------------------------------------------------------------ decontamination
def norm_text(text) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def text_hash(text) -> str:
    return utils.sha("stmt", norm_text(text))


def heldout_keys(heldout) -> tuple[set, set]:
    """(APPS-test problem ids, statement hashes) of the held-out tasks (exp0 ids `apps/<pid>`)."""
    pids = {str(t["id"]).split("/", 1)[1] for t in heldout if str(t["id"]).startswith("apps/")}
    return pids, {text_hash(t.get("text")) for t in heldout}


# ------------------------------------------------------------------ raw APPS rows
def trim_row(x, max_tests=None, max_chars=None):
    """One APPS jsonl row -> small dict (introductory only, <= max_tests tests with short inputs /
    outputs, <= 24 distinct solutions), or None."""
    max_tests = CFG.MAX_TESTS if max_tests is None else max_tests
    max_chars = CFG.MAX_TEST_CHARS if max_chars is None else max_chars
    if x.get("difficulty") != "introductory":
        return None
    try:
        io = json.loads(x["input_output"]) if x.get("input_output") else None
        sols = json.loads(x["solutions"]) if x.get("solutions") else []
    except Exception:  # noqa
        return None
    if not io or not io.get("inputs") or not sols:
        return None
    ins, outs = io["inputs"], io.get("outputs") or []
    keep = [i for i in range(min(len(ins), len(outs)))
            if len(json.dumps(ins[i])) <= max_chars and len(json.dumps(outs[i])) <= max_chars][:max_tests]
    sols = [s for s in dict.fromkeys(s for s in sols if isinstance(s, str) and s.strip())][:MAX_SOLUTIONS]
    if not keep or not sols:
        return None
    return {"pid": str(x.get("problem_id", x.get("id"))), "question": x["question"],
            "starter": x.get("starter_code") or "", "solutions": sols,
            "io": {"inputs": [ins[i] for i in keep], "outputs": [outs[i] for i in keep], "fn_name": io.get("fn_name")}}


def stream_raw(url, limit=None, count_if=None):
    """Streams an APPS jsonl (URL or local path) -> (trimmed introductory rows, complete flag).
    Stops after `limit` rows for which count_if(row) is true (smoke runs)."""
    rows, n = [], 0
    for line in data0._iter_lines(url):
        if not line.strip():
            continue
        try:
            x = json.loads(line)
        except json.JSONDecodeError:
            continue
        r = trim_row(x)
        if r is None:
            continue
        rows.append(r)
        n += 1 if (count_if is None or count_if(r)) else 0
        if limit is not None and n >= limit:
            return rows, False
    return rows, True


def load_raw(url, cache_path, limit=None, count_if=None):
    """Trimmed rows of one APPS split, cached in cache_path (+ .meta.json) so re-runs do not download."""
    cache_path = Path(cache_path)
    meta_path = cache_path.with_suffix(".meta.json")
    meta = utils.read_json(meta_path, None) if meta_path.exists() else None
    if meta and cache_path.exists():
        rows = utils.read_jsonl(cache_path)
        n = len([r for r in rows if count_if is None or count_if(r)])
        if meta.get("complete") or (limit is not None and n >= limit):
            _log(f"raw: {len(rows)} rows from {cache_path.name}")
            return rows
    _log(f"raw: streaming introductory problems from {url} ...")
    t0 = time.time()
    rows, complete = stream_raw(url, limit, count_if)
    utils.write_jsonl(cache_path, rows)
    _write_json(meta_path, {"complete": complete, "rows": len(rows), "url": url,
                            "max_tests": CFG.MAX_TESTS, "max_test_chars": CFG.MAX_TEST_CHARS})
    _log(f"raw: {len(rows)} rows ({'complete' if complete else 'partial'}) in {time.time() - t0:.0f}s, "
         f"cache {cache_path.stat().st_size / 1e6:.1f} MB")
    return rows


def raw_cache_path(tag, url):
    h = utils.sha(url, CFG.MAX_TESTS, CFG.MAX_TEST_CHARS, MAX_SOLUTIONS)[:8]
    return CFG.DATA_DIR / f"apps_{tag}_intro_{h}.jsonl"


# ------------------------------------------------------------------ tasks
def build_task(row, source):
    """Trimmed raw row -> exp0-format task (exactly like exp0 data.load_apps), `reference` = solutions."""
    io = row["io"]
    fn = io.get("fn_name")
    if fn:
        tests, args_list = [], []
        for i, o in zip(io["inputs"], io["outputs"]):
            if not isinstance(i, list):
                i = [i]
            tests.append({"type": "call", "args": repr(tuple(i)), "expected": repr(o)})
            args_list.append(tuple(i))
        recipe = scaler.func_recipe(args_list, C0.LADDER_FACTORS, CFG.DATA_SEED)
        kind = "func"
    else:
        tests = [{"input": data0._as_text(i), "output": data0._as_text(o)} for i, o in zip(io["inputs"], io["outputs"])]
        recipe = scaler.stdio_recipe(C0.LADDER_FACTORS, CFG.DATA_SEED)
        kind = "stdio"
    if not tests:
        return None
    return {"id": f"{source}/{row['pid']}", "source": source, "kind": kind, "entry": fn, "setup": "",
            "text": row["question"], "starter": row["starter"], "example_test": "", "tests": tests,
            "ladder_recipe": recipe, "reference": list(row["solutions"])}


def decontaminate(rows, source, held_pids, held_hashes, seen, min_tests=0, exclude_pid=False):
    """Filters raw rows of one source. `seen` (statement hashes of earlier candidates) is updated.
    Returns (kept rows, counts)."""
    cnt = Counter(raw=len(rows))
    out = []
    for r in rows:
        if len(r["io"]["inputs"]) < min_tests:
            cnt["few_tests"] += 1
            continue
        if exclude_pid and r["pid"] in held_pids:
            cnt["heldout_pid"] += 1
            continue
        h = text_hash(r["question"])
        if h in held_hashes:
            cnt["heldout_text"] += 1
            continue
        if h in seen:
            cnt["dup_text"] += 1
            continue
        seen.add(h)
        out.append(r)
    cnt["kept"] = len(out)
    _log(f"decontam {source}: {dict(cnt)}")
    return out, dict(cnt)


def validate_refs(tasks, cache=None):
    """Runs the tests on up to N_REF_TRY distinct reference solutions per task (in parallel over tasks,
    C0.WORKERS), keeps the first N_REF_KEEP that pass in `ref`. Returns the tasks with >= 1 ref."""
    def one(t):
        codes = list(dict.fromkeys(c for c in t.get("reference") or [] if c.strip()))[:CFG.N_REF_TRY]
        k = utils.sha("refs", fpstore.TEST_VERSION, fpstore._task_test_hash(t), CFG.N_REF_KEEP, *codes)
        hit = cache.get(k) if cache is not None else None
        if hit is not None:
            return [codes[i] for i in hit]
        ok = []
        for i, c in enumerate(codes):
            if sandbox.test_program(t, c)["correct"]:
                ok.append(i)
                if len(ok) >= CFG.N_REF_KEEP:
                    break
        if cache is not None:
            cache.put(k, ok)
        return [codes[i] for i in ok]

    refs = utils.parallel_map(one, tasks, workers=C0.WORKERS, desc="validate refs", every=60.0)
    out = []
    for t, r in zip(tasks, refs):
        t.pop("reference", None)
        if r:
            t["ref"] = r
            out.append(t)
    return out


# ------------------------------------------------------------------ prompt length
def _model_dirs(name):
    base = Path(CFG.MODELS_DIR)
    return [base / name.split("/")[-1], base / name.replace("/", "__"), base / name.replace("/", "--"), base / name]


def load_tokenizer(name=None):
    """Tokenizer of CFG.MODEL: from the local model folder if Module A downloaded it already, else
    only the tokenizer files from the hub (HF cache; no weights, never into MODELS_DIR)."""
    from transformers import AutoTokenizer
    name = name or CFG.MODEL
    for d in _model_dirs(name):
        if (d / "tokenizer_config.json").exists():
            return AutoTokenizer.from_pretrained(str(d))
    from huggingface_hub import snapshot_download
    p = snapshot_download(repo_id=name, allow_patterns=["tokenizer*", "vocab*", "merges*", "special_tokens_map.json",
                                                        "added_tokens.json", "config.json", "generation_config.json"])
    return AutoTokenizer.from_pretrained(p)


def prompt_len(tok, task) -> int:
    """Tokens of the chat-template prompt (as Policy.render) + PROMPT_SLACK."""
    ids = tok.apply_chat_template([{"role": "user", "content": prompts.problem_prompt(task)}],
                                  add_generation_prompt=True, tokenize=True)
    if isinstance(ids, dict) or hasattr(ids, "keys"):
        ids = ids["input_ids"]
    return len(ids) + PROMPT_SLACK


def add_prompt_tokens(tasks, tok):
    for t in tasks:
        t["prompt_tokens"] = prompt_len(tok, t)
    return tasks


# ------------------------------------------------------------------ prep
def split_val(tasks, n_val, seed):
    """Marks n_val tasks (random, proportional over sources) split="val", the rest "train"."""
    n_val = max(0, min(n_val, len(tasks) // 2))
    by = {}
    for t in tasks:
        by.setdefault(t["source"], []).append(t)
    srcs = sorted(by)
    exact = {s: n_val * len(by[s]) / max(1, len(tasks)) for s in srcs}
    quota = {s: int(exact[s]) for s in srcs}
    for s in sorted(srcs, key=lambda s: exact[s] - quota[s], reverse=True)[: n_val - sum(quota.values())]:
        quota[s] += 1
    rng = random.Random(seed)
    val = set()
    for s in srcs:
        val |= {t["id"] for t in rng.sample(by[s], quota[s])}
    for t in tasks:
        t["split"] = "val" if t["id"] in val else "train"
    return tasks


def prep(out_path, train_rows, test_rows, heldout, tok, cache_dir=None, n_cand_train=None, n_cand_test=None,
         n_val=None, seed=None):
    """Raw rows of both sources -> candidates file (train + val). test_rows may be [] (no APPS-test rest).
    Returns (candidates, report)."""
    n_cand_train = CFG.N_CAND_TRAIN if n_cand_train is None else n_cand_train
    n_cand_test = CFG.N_CAND_TEST if n_cand_test is None else n_cand_test
    n_val = CFG.N_VAL if n_val is None else n_val
    seed = CFG.DATA_SEED if seed is None else seed
    out_path = Path(out_path)
    timings, t0 = {}, time.time()
    held_pids, held_hashes = heldout_keys(heldout)
    seen = set()
    rep = {"heldout": {"tasks": len(heldout), "apps_pids": len(held_pids)}, "steps": {}, "decontam": {}}
    rng = random.Random(seed)
    cands = []
    for source, rows, cap, kw in (("appstr", train_rows, n_cand_train, dict(min_tests=CFG.MIN_TESTS)),
                                  ("appste", test_rows, n_cand_test, dict(exclude_pid=True))):
        if not rows:
            continue
        kept, cnt = decontaminate(rows, source, held_pids, held_hashes, seen, **kw)
        rep["decontam"][source] = cnt
        rng.shuffle(kept)
        kept = kept[:cap]
        tasks = [t for t in (build_task(r, source) for r in kept) if t]
        rep["steps"][source] = {"capped": len(kept), "built": len(tasks)}
        cands += tasks
    timings["build"] = time.time() - t0

    t1 = time.time()
    cache = utils.JsonlCache(Path(cache_dir or C0.CACHE_DIR) / "ref_valid.jsonl")
    _log(f"validating references of {len(cands)} candidates (workers={C0.WORKERS}) ...")
    cands = validate_refs(cands, cache)
    timings["validate"] = time.time() - t1
    for s in rep["steps"]:
        rep["steps"][s]["with_ref"] = sum(t["source"] == s for t in cands)

    t2 = time.time()
    add_prompt_tokens(cands, tok)
    long_ = [t for t in cands if t["prompt_tokens"] > CFG.MAX_PROMPT_TOKENS]
    cands = [t for t in cands if t["prompt_tokens"] <= CFG.MAX_PROMPT_TOKENS]
    timings["tokens"] = time.time() - t2
    for s in rep["steps"]:
        rep["steps"][s]["prompt_ok"] = sum(t["source"] == s for t in cands)
        rep["steps"][s]["prompt_too_long"] = sum(t["source"] == s for t in long_)

    if not cands:
        raise SystemExit(f"prep: no candidate task survived (decontamination {rep['decontam']}, steps {rep['steps']})")
    split_val(cands, n_val, seed)
    rep["candidates"] = _counts(cands)
    rep["ref_per_task"] = dict(sorted(Counter(len(t["ref"]) for t in cands).items()))
    rep["prompt_tokens"] = _quantiles([t["prompt_tokens"] for t in cands])
    rep["seconds"] = {k: round(v, 1) for k, v in timings.items()}
    utils.write_jsonl(out_path, cands)
    _write_json(out_path.with_name("prep_report.json"), rep)
    _log(f"prep: {len(cands)} candidates -> {out_path}  {rep['candidates']['by_split']}")
    return cands, rep


def _counts(tasks):
    return {"n": len(tasks), "by_split": dict(Counter(t.get("split") for t in tasks)),
            "by_source_kind": dict(Counter(f"{t.get('split')}:{t['source']}:{t['kind']}" for t in tasks))}


def _quantiles(xs):
    if not xs:
        return {}
    xs = sorted(xs)
    return {f"p{q}": xs[min(len(xs) - 1, int(q / 100 * len(xs)))] for q in (0, 50, 90, 100)}


def prep_cli():
    exp0.setup(CFG.RUN_DIR)
    out = CFG.RUN_DIR / "data" / "candidates.jsonl"
    if out.exists():
        _log(f"prep: {out} exists, nothing to do")
        return
    t0 = time.time()
    heldout = utils.read_jsonl(CFG.TEST_TASKS)
    if not heldout:
        raise SystemExit(f"held-out task file {CFG.TEST_TASKS} is missing or empty")
    held_pids, _ = heldout_keys(heldout)
    CFG.DATA_DIR.mkdir(parents=True, exist_ok=True)
    big = 50_000
    lim_tr = None if CFG.N_CAND_TRAIN >= big else 2 * CFG.N_CAND_TRAIN + 50
    train_rows = load_raw(APPS_TRAIN_URL, raw_cache_path("train", APPS_TRAIN_URL), lim_tr,
                          count_if=lambda r: len(r["io"]["inputs"]) >= CFG.MIN_TESTS)
    test_rows = []
    if CFG.USE_APPS_TEST_REST:
        lim_te = None if CFG.N_CAND_TEST >= big else 2 * CFG.N_CAND_TEST + 50
        test_rows = load_raw(APPS_TEST_URL, raw_cache_path("test", APPS_TEST_URL), lim_te,
                             count_if=lambda r: r["pid"] not in held_pids)
    t_raw = time.time() - t0
    tok = load_tokenizer()
    _, rep = prep(out, train_rows, test_rows, heldout, tok)
    rep["seconds"]["raw"] = round(t_raw, 1)
    rep["seconds"]["total"] = round(time.time() - t0, 1)
    _write_json(out.with_name("prep_report.json"), rep)
    exp0.cleanup_tmp()


# ------------------------------------------------------------------ pool: probe + test set
def read_probe(probe_dir) -> dict:
    """RUN_DIR/probe/*.jsonl rows {"task", "c"} -> {task id: {"n", "correct"}}."""
    out = {}
    for p in sorted(Path(probe_dir).glob("*.jsonl")):
        for r in utils.read_jsonl(p):
            if "task" not in r:
                continue
            d = out.setdefault(r["task"], {"n": 0, "correct": 0})
            d["n"] += 1
            d["correct"] += int(bool(r.get("c")))
    return out


def select_pool(cands, probe, keep_min=None, zero_frac=None, seed=None):
    """Train pool: train candidates with correct >= keep_min, plus random unsolved ones so that they
    make up a zero_frac share of the pool. Val candidates are kept as they are.
    Returns (train, val, info). Every candidate gets its `probe`."""
    keep_min = CFG.KEEP_MIN_CORRECT if keep_min is None else keep_min
    zero_frac = CFG.ZERO_FRAC if zero_frac is None else zero_frac
    seed = CFG.DATA_SEED if seed is None else seed
    missing = 0
    for t in cands:
        p = probe.get(t["id"])
        missing += p is None
        t["probe"] = dict(p) if p else {"n": 0, "correct": 0}
    tr = [t for t in cands if t.get("split") == "train" and t["probe"]["n"] > 0]
    val = [t for t in cands if t.get("split") == "val"]
    solved = [t for t in tr if t["probe"]["correct"] >= keep_min]
    zero = [t for t in tr if t["probe"]["correct"] < keep_min]
    nz = min(len(zero), round(zero_frac * len(solved) / max(1e-9, 1.0 - zero_frac))) if zero_frac < 1 else len(zero)
    add = random.Random(seed).sample(zero, nz)
    ids = {t["id"] for t in solved + add}
    train = [t for t in cands if t["id"] in ids]
    info = {"train_candidates": sum(t.get("split") == "train" for t in cands), "probe_missing": missing,
            "solved": len(solved), "unsolved": len(zero), "unsolved_added": len(add), "pool": len(train),
            "probe_hist": {s: dict(sorted(Counter(t["probe"]["correct"] for t in cands if t.get("split") == s).items()))
                           for s in ("train", "val")},
            "solve_rate": {s: round(sum(t["probe"]["correct"] for t in xs) / max(1, sum(t["probe"]["n"] for t in xs)), 4)
                           for s, xs in (("train", [t for t in cands if t.get("split") == "train"]), ("val", val))}}
    if missing:
        _log(f"WARNING: {missing} candidates have no probe rows (left out of the train pool)")
    return train, val, info


def select_test(heldout, n_test=None):
    """First n_test held-out tasks in file order, or (n_test < len) an even mix of the sources."""
    n_test = CFG.N_TEST if n_test is None else n_test
    if n_test >= len(heldout):
        sel = list(heldout)
    else:
        srcs = list(dict.fromkeys(t["source"] for t in heldout))
        quota = {s: n_test // len(srcs) + (1 if i < n_test % len(srcs) else 0) for i, s in enumerate(srcs)}
        sel = []
        for t in heldout:
            if quota[t["source"]] > 0:
                quota[t["source"]] -= 1
                sel.append(t)
    out = []
    for t in sel:
        t = dict(t)
        t["split"] = "test"
        out.append(t)
    return out


# ------------------------------------------------------------------ pool: reference measurement
def summarize_traces(refs, traces):
    """Reference traces (slim, ladder order of the task) -> lad, rungs, ref_out, ref_time, ref_fp."""
    valid = fpstore.valid_rungs(traces[: C0.N_REF_CHECK])
    fps = [FP.compute_all(c, tr, valid) for c, tr in zip(refs, traces)]
    lad = FP.select_ladder(fps) if valid else None
    if lad is None:
        return {"lad": None, "rungs": [], "ref_out": {}, "ref_time": {}, "ref_fp": []}
    rungs = sorted(int(s) for s in (valid.get(lad) or set()))
    rs = set(rungs)
    outs, errs, times = {}, set(), {}
    for tr in traces:
        mine = {}
        for r in tr.get("runs") or []:
            if r.get("ladder", "main") != lad or r["size"] not in rs:
                continue
            if r.get("status") == "ok" and r.get("out"):
                mine.setdefault(r["size"], set()).add(r["out"])
            elif r.get("status") == "error":
                errs.add(r["size"])
        for t in tr.get("timing") or []:
            if t.get("ladder", "main") != lad or t["size"] not in rs:
                continue
            if t.get("out"):
                mine.setdefault(t["size"], set()).add(t["out"])
            times[t["size"]] = max(times.get(t["size"], 0.0), float(t["t"]))
        for s, o in mine.items():
            outs.setdefault(s, []).append(o)
    ref_out = {}
    for s, per_ref in outs.items():
        allv = set().union(*per_ref)
        if len(per_ref) >= 2 and len(allv) == 1 and s not in errs:
            ref_out[str(s)] = next(iter(allv))
    ref_fp = [f for f in (FP.pick(fa, lad) for fa in fps) if f.get("ok")]
    return {"lad": lad, "rungs": rungs, "ref_out": dict(sorted(ref_out.items(), key=lambda kv: int(kv[0]))),
            "ref_time": {str(s): times[s] for s in sorted(times)}, "ref_fp": ref_fp}


def _measure_key(task, refs):
    return utils.sha("refmeasure", task["id"], utils.sha(*refs), fpstore._task_ladder_hash(task),
                     fpstore.TRACE_VERSION, _FP_SRC, C0.N_REF_CHECK)


def measure_tasks(tasks, cache_path, workers=None):
    """Adds lad, rungs, ref_out, ref_time, ref_fp, ref_groups to every task (in place). The traces of
    the references (up to N_REF_KEEP) of one task run in one worker; results are cached per task."""
    from . import reward
    cache = utils.JsonlCache(cache_path)
    workers = workers or C0.FP_WORKERS
    cores = sandbox.core_pool()[0]
    if cores:
        workers = min(workers, len(cores))

    def one(task):
        refs = list(task.get("ref") or [])[: CFG.N_REF_KEEP]
        if not refs:
            return {"lad": None, "rungs": [], "ref_out": {}, "ref_time": {}, "ref_fp": [], "n_traced": 0}
        k = _measure_key(task, refs)
        v = cache.get(k)
        if v is None:
            inputs = scaler.build_ladder(task)
            traces = [fpstore._slim(sandbox.trace_program(task, c, inputs=inputs)) for c in refs]
            v = summarize_traces(refs, traces)
            v["n_traced"] = len(traces)
            v["trace_status"] = dict(Counter(tr.get("status") for tr in traces))
            cache.put(k, v)
        return v

    t0 = time.time()
    res = utils.parallel_map(one, tasks, workers=workers, desc="measure refs", every=60.0)
    for t, v in zip(tasks, res):
        t.update(lad=v["lad"], rungs=[int(s) for s in v["rungs"]], ref_out=v["ref_out"], ref_time=v["ref_time"],
                 ref_fp=v["ref_fp"])
        lab = reward.clusters(t["ref_fp"]) if t["ref_fp"] else []
        t["ref_groups"] = len({x for x in lab if x is not None})
    _log(f"measured {len(tasks)} tasks in {time.time() - t0:.0f}s (workers={workers})")
    return tasks


def _ladder_stats(tasks):
    n = len(tasks)
    lad = [t for t in tasks if t.get("lad")]
    return {"n": n, "with_ladder": len(lad), "share_ladder": round(len(lad) / max(1, n), 3),
            "rungs_ge3": sum(len(t.get("rungs") or []) >= 3 for t in lad),
            "by_lad": dict(Counter(t.get("lad") for t in tasks)),
            "ref_groups": dict(sorted(Counter(t.get("ref_groups", 0) for t in tasks).items())),
            "ref_groups_ge2": sum(t.get("ref_groups", 0) >= 2 for t in tasks),
            "with_ref_out": sum(bool(t.get("ref_out")) for t in tasks),
            "by_source_kind": dict(Counter(f"{t['source']}:{t['kind']}" for t in tasks))}


def pool(data_dir, cands, probe, heldout, tok=None, cache_dir=None, n_test=None, need_ladder=None,
         keep_min=None, zero_frac=None, seed=None):
    """Candidates + probe results + held-out tasks -> data_dir/{train,val,test}.jsonl + data_report.json.
    Returns (train, val, test, report)."""
    need_ladder = CFG.NEED_LADDER if need_ladder is None else need_ladder
    data_dir = Path(data_dir)
    t0 = time.time()
    train, val, info = select_pool(cands, probe, keep_min, zero_frac, seed)
    test = select_test(heldout, n_test)
    for t in test:
        t.pop("probe", None)
        if tok is not None and "prompt_tokens" not in t:
            t["prompt_tokens"] = prompt_len(tok, t)
    t1 = time.time()
    measure_tasks(train + val + test, Path(cache_dir or C0.CACHE_DIR) / "ref_measure.jsonl")
    t2 = time.time()
    rep = {"pool": info, "measured": {"train": _ladder_stats(train), "val": _ladder_stats(val), "test": _ladder_stats(test)}}
    if need_ladder:
        before = len(train)
        train = [t for t in train if t.get("lad") and len(t.get("rungs") or []) >= 3]
        rep["need_ladder_dropped"] = before - len(train)
    prep_rep = utils.read_json(data_dir / "prep_report.json", None)
    if prep_rep:
        rep["prep"] = prep_rep
    rep["final"] = {"train": _counts(train), "val": _counts(val), "test": _counts(test)}
    rep["final_ladder"] = {"train": _ladder_stats(train), "val": _ladder_stats(val), "test": _ladder_stats(test)}
    rep["seconds"] = {"select": round(t1 - t0, 1), "measure": round(t2 - t1, 1)}
    utils.write_jsonl(data_dir / "train.jsonl", train)
    utils.write_jsonl(data_dir / "val.jsonl", val)
    utils.write_jsonl(data_dir / "test.jsonl", test)
    _write_json(data_dir / "data_report.json", rep)
    _log(f"pool: train {len(train)}, val {len(val)}, test {len(test)} -> {data_dir}")
    return train, val, test, rep


def pool_cli():
    exp0.setup(CFG.RUN_DIR)
    data_dir = CFG.RUN_DIR / "data"
    cands = load_tasks(data_dir / "candidates.jsonl")
    if not cands:
        raise SystemExit(f"{data_dir / 'candidates.jsonl'} is missing: run `python -m st.data prep` first")
    probe = read_probe(CFG.RUN_DIR / "probe")
    if not probe:
        raise SystemExit(f"no probe results in {CFG.RUN_DIR / 'probe'}")
    heldout = utils.read_jsonl(CFG.TEST_TASKS)
    tok = load_tokenizer()
    pool(data_dir, cands, probe, heldout, tok)
    exp0.cleanup_tmp()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else ""
    if cmd == "prep":
        prep_cli()
    elif cmd == "pool":
        pool_cli()
    else:
        raise SystemExit("usage: python -m st.data prep|pool")


if __name__ == "__main__":
    main()
