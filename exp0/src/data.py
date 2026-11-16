"""MBPP+ (EvalPlus; falls back to sanitized MBPP) + APPS-introductory (test split)
-> validated tasks with tests and input-ladder recipes."""
from __future__ import annotations

import ast
import json
import os
import random
import time

import requests

from . import config as C
from .sandbox import test_program
from .scaler import func_recipe, stdio_recipe
from .utils import log, parallel_map, read_jsonl, write_jsonl

MBPP_URLS = ["https://raw.githubusercontent.com/google-research/google-research/master/mbpp/sanitized-mbpp.json",
             "https://raw.githubusercontent.com/google-research/google-research/master/mbpp/mbpp.jsonl"]
MBPP_PLUS_ROWS = "https://datasets-server.huggingface.co/rows?dataset=evalplus/mbppplus&config=default&split=test"
APPS_URL = os.environ.get("APPS_URL", "https://huggingface.co/datasets/codeparrot/apps/resolve/main/test.jsonl")

SAFE_BUILTINS = {"float": float, "int": int, "str": str, "list": list, "tuple": tuple, "set": set,
                 "frozenset": frozenset, "dict": dict, "range": range, "True": True, "False": False,
                 "None": None, "abs": abs, "len": len, "complex": complex, "bytes": bytes}


def _eval_arg(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        src = ast.unparse(node)
        return eval(compile(src, "<arg>", "eval"), {"__builtins__": SAFE_BUILTINS}, {})


def _literal_ok(v):
    """The harness re-creates arguments with eval(repr(v)); make sure that round-trips."""
    try:
        back = eval(repr(v), {"__builtins__": {"set": set, "frozenset": frozenset},
                              "inf": float("inf"), "nan": float("nan")})
        return back == v or v != v
    except Exception:
        return False


# ------------------------------------------------------------------ MBPP
def _fetch_mbpp():
    for url in MBPP_URLS:
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            if url.endswith(".json"):
                rows = r.json()
                return [{"task_id": x["task_id"], "text": x["prompt"], "code": x["code"],
                         "setup": "\n".join(x.get("test_imports", [])), "tests": x["test_list"]} for x in rows]
            rows = [json.loads(l) for l in r.text.splitlines() if l.strip()]
            return [{"task_id": x["task_id"], "text": x["text"], "code": x["code"],
                     "setup": x.get("test_setup_code", ""), "tests": x["test_list"]} for x in rows]
        except Exception as e:  # noqa
            log(f"MBPP download failed from {url}: {e}")
    raise SystemExit("could not download MBPP")


def _mbpp_entry(code, tests):
    try:
        defined = {n.name for n in ast.walk(ast.parse(code)) if isinstance(n, ast.FunctionDef)}
    except SyntaxError:
        defined = set()
    for t in tests:
        try:
            tree = ast.parse(t)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in defined:
                return n.func.id
    return None


def _mbpp_args(tests, entry):
    out = []
    for t in tests:
        try:
            tree = ast.parse(t)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == entry and not n.keywords:
                try:
                    args = tuple(_eval_arg(a) for a in n.args)
                    if all(_literal_ok(a) for a in args):
                        out.append(args)
                except Exception:
                    pass
                break
    return out


def _fetch_mbpp_plus():
    """MBPP+ rows via the HF datasets-server JSON API (no pyarrow needed)."""
    rows, off = [], 0
    while True:
        for attempt in range(8):  # the datasets-server occasionally answers 502/503
            try:
                r = requests.get(f"{MBPP_PLUS_ROWS}&offset={off}&length=100", timeout=120)
                r.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 7:
                    raise
                time.sleep(5 * (attempt + 1))
        d = r.json()
        rows += [x["row"] for x in d["rows"]]
        off += len(d["rows"])
        if not d["rows"] or off >= d.get("num_rows_total", off):
            return rows


def _plus_inputs(test_src):
    """The EvalPlus test script defines `inputs = [...]` (base + plus inputs); extract them."""
    try:
        tree = ast.parse(test_src)
    except SyntaxError:
        return []
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "inputs" for t in n.targets):
            try:
                vals = eval(compile(ast.Expression(n.value), "<inputs>", "eval"),
                            {"__builtins__": SAFE_BUILTINS, "inf": float("inf"), "nan": float("nan")})
            except Exception:
                return []
            return [tuple(v) for v in vals if isinstance(v, (list, tuple)) and all(_literal_ok(a) for a in v)]
    return []


def load_mbpp():
    if C.MBPP_SOURCE == "plus":
        try:
            rows = _fetch_mbpp_plus()
            log(f"MBPP+: {len(rows)} tasks (EvalPlus tests)")
            tasks = []
            for x in rows:
                entry = _mbpp_entry(x["code"], x["test_list"])
                if not entry or not x.get("test"):
                    continue
                tasks.append({"id": f"mbpp/{x['task_id']}", "source": "mbpp", "kind": "func", "entry": entry,
                              "setup": "\n".join(x.get("test_imports") or []), "text": x["prompt"], "starter": "",
                              "example_test": x["test_list"][0],
                              # the whole EvalPlus script (its own comparison function, base + plus inputs)
                              "tests": [{"type": "assert", "src": x["test"], "timeout": 60.0}],
                              "ladder_recipe": func_recipe(_plus_inputs(x["test"]) or _mbpp_args(x["test_list"], entry),
                                                           C.LADDER_FACTORS, C.SEED),
                              "reference": [x["code"]]})
            return tasks
        except Exception as e:  # noqa
            log(f"WARNING: MBPP+ unavailable ({e}); falling back to sanitized MBPP with 3 tests per task")
    rows = _fetch_mbpp()
    tasks = []
    for x in rows:
        entry = _mbpp_entry(x["code"], x["tests"])
        if not entry:
            continue
        tasks.append({"id": f"mbpp/{x['task_id']}", "source": "mbpp", "kind": "func", "entry": entry,
                      "setup": x["setup"], "text": x["text"], "starter": "", "example_test": x["tests"][0],
                      "tests": [{"type": "assert", "src": t} for t in x["tests"]],
                      "ladder_recipe": func_recipe(_mbpp_args(x["tests"], entry), C.LADDER_FACTORS, C.SEED),
                      "reference": [x["code"]]})
    return tasks


# ------------------------------------------------------------------ APPS
def _as_text(v):
    if isinstance(v, list):
        return "\n".join(str(x) for x in v)
    return str(v)


def _iter_lines(url):
    """Yields lines of a (huge) remote jsonl, resuming with HTTP Range after a broken connection.
    A local path is read directly (handy for tests)."""
    if os.path.exists(url):
        with open(url, "rb") as f:
            yield from f
        return
    pos, yielded, buf, fails = 0, 0, b"", 0
    while True:
        headers = {"Range": f"bytes={pos}-"} if pos else {}
        try:
            with requests.get(url, stream=True, timeout=120, headers=headers) as r:
                r.raise_for_status()
                if pos and r.status_code != 206:  # server ignored Range: restart, skip what we had
                    skip, pos, buf = yielded, 0, b""
                else:
                    skip = 0
                for chunk in r.iter_content(1 << 20):
                    pos += len(chunk)
                    fails = 0  # progress was made: only consecutive failures count
                    buf += chunk
                    if b"\n" in buf:
                        *lines, buf = buf.split(b"\n")
                        for line in lines:
                            if skip:
                                skip -= 1
                                continue
                            yielded += 1
                            yield line
            if buf:
                yield buf
            return
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:
            fails += 1
            if fails > 30:
                raise
            log(f"  APPS stream interrupted at {pos / 1e6:.0f} MB ({e.__class__.__name__}); resuming ...")
            time.sleep(min(60, 5 * fails))


def _stream_apps(max_candidates):
    """Streams APPS test.jsonl (1.3 GB; nothing large is stored) and keeps introductory problems."""
    out = []
    for line in _iter_lines(APPS_URL):
        if not line.strip():
            continue
        try:
            x = json.loads(line)
        except json.JSONDecodeError:
            continue
        if x.get("difficulty") != "introductory":
            continue
        try:
            io = json.loads(x["input_output"]) if x.get("input_output") else None
            sols = json.loads(x["solutions"]) if x.get("solutions") else []
        except Exception:
            continue
        if not io or not io.get("inputs") or not sols:
            continue
        out.append({"pid": x.get("problem_id", x.get("id")), "question": x["question"],
                    "starter": x.get("starter_code") or "", "io": io, "solutions": sols[:24]})
        if len(out) >= max_candidates:
            break
    return out


def load_apps(max_candidates):
    cache = C.DATA_DIR / "apps_intro_raw.jsonl"
    rows = read_jsonl(cache)
    if len(rows) < max_candidates:
        log(f"streaming APPS introductory problems from {APPS_URL} ...")
        rows = _stream_apps(max_candidates)
        for r in rows:  # keep the cached file small
            ins, outs = r["io"]["inputs"], r["io"]["outputs"]
            keep = [i for i in range(min(len(ins), len(outs))) if len(json.dumps(ins[i])) < 200_000]
            keep = keep[: C.MAX_TESTS]
            r["io"] = {"inputs": [ins[i] for i in keep], "outputs": [outs[i] for i in keep],
                       "fn_name": r["io"].get("fn_name")}
        write_jsonl(cache, rows)
    tasks = []
    for r in rows:
        io = r["io"]
        fn = io.get("fn_name")
        if fn:
            tests, args_list = [], []
            for i, o in zip(io["inputs"], io["outputs"]):
                if not isinstance(i, list):
                    i = [i]
                tests.append({"type": "call", "args": repr(tuple(i)), "expected": repr(o)})
                args_list.append(tuple(i))
            recipe = func_recipe(args_list, C.LADDER_FACTORS, C.SEED)
            kind = "func"
        else:
            tests = [{"input": _as_text(i), "output": _as_text(o)} for i, o in zip(io["inputs"], io["outputs"])]
            recipe = stdio_recipe(C.LADDER_FACTORS, C.SEED)
            kind = "stdio"
        if not tests:
            continue
        tasks.append({"id": f"apps/{r['pid']}", "source": "apps", "kind": kind, "entry": fn, "setup": "",
                      "text": r["question"], "starter": r["starter"], "example_test": "",
                      "tests": tests, "ladder_recipe": recipe, "reference": r["solutions"]})
    return tasks


# ------------------------------------------------------------------ validation + selection
def _validate(task):
    passing = []
    for code in task["reference"][: (1 if task["source"] == "mbpp" else 24)]:
        r = test_program(task, code)
        if r["correct"]:
            passing.append(code)
            if len(passing) >= C.MAX_HUMAN:
                break
    return passing


def tasks_path():
    from .utils import sha
    h = sha(C.N_MBPP, C.N_APPS, C.MAX_TESTS, C.MAX_HUMAN, C.SEED, C.LADDER_FACTORS, APPS_URL, C.MBPP_SOURCE)[:8]
    return C.DATA_DIR / f"tasks_{'smoke_' if C.SMOKE else ''}{h}.jsonl"


def prepare_tasks():
    path = tasks_path()
    if path.exists():
        tasks = read_jsonl(path)
        log(f"tasks: loaded {len(tasks)} from {path}")
        return tasks
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(C.SEED)
    mbpp = load_mbpp()
    rng.shuffle(mbpp)
    mbpp = mbpp[: int(C.N_MBPP * 1.4) + 5]
    apps = load_apps(max_candidates=min(1000, int(C.N_APPS * 2.5) + 10)) if C.N_APPS > 0 else []
    rng.shuffle(apps)
    apps = apps[: int(C.N_APPS * 1.6) + 5]
    log(f"validating reference solutions: {len(mbpp)} MBPP + {len(apps)} APPS candidates")
    cands = mbpp + apps
    passing = parallel_map(_validate, cands, desc="validate")
    sel = {"mbpp": [], "apps": []}
    for t, ps in zip(cands, passing):
        if not ps:
            continue
        t["human"] = ps if t["source"] == "apps" else []
        t["ref"] = ps  # validated reference solutions (MBPP: the dataset solution) -> ladder choice
        t.pop("reference", None)
        sel[t["source"]].append(t)
    tasks = sel["mbpp"][: C.N_MBPP] + sel["apps"][: C.N_APPS]
    write_jsonl(path, tasks)
    log(f"tasks: {len(sel['mbpp'][:C.N_MBPP])} MBPP + {len(sel['apps'][:C.N_APPS])} APPS-introductory "
        f"(valid of candidates: {len(sel['mbpp'])}/{len(mbpp)} MBPP, {len(sel['apps'])}/{len(apps)} APPS)")
    return tasks
