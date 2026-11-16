"""Baseline distances: JPlag, text/AST similarity, code embeddings (via src.embed subprocess)."""
from __future__ import annotations

import ast
import csv
import difflib
import io
import json
import math
import re
import shutil
import subprocess
import sys
import tokenize
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

from . import config as C
from .setup_tools import find_java, jplag_jar
from .utils import log


# ------------------------------------------------------------------ text / AST
def _tokens(code):
    try:
        return [t.string for t in tokenize.generate_tokens(io.StringIO(code).readline)
                if t.type not in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                                  tokenize.DEDENT, tokenize.ENDMARKER)]
    except Exception:
        return code.split()


def d_difflib(a, b):
    return 1.0 - difflib.SequenceMatcher(None, _tokens(a), _tokens(b), autojunk=False).ratio()


def _ast_bag(code):
    try:
        return Counter(type(n).__name__ for n in ast.walk(ast.parse(code)))
    except SyntaxError:
        return Counter()


def d_ast(a, b):
    x, y = _ast_bag(a), _ast_bag(b)
    keys = set(x) | set(y)
    dot = sum(x[k] * y[k] for k in keys)
    nx, ny = math.sqrt(sum(v * v for v in x.values())), math.sqrt(sum(v * v for v in y.values()))
    return 1.0 - dot / (nx * ny) if nx and ny else 1.0


# ------------------------------------------------------------------ JPlag
def _parse_jplag_outputs(res_base: Path, names):
    sims = {}

    def put(a, b, s):
        if a is None or b is None or s is None:
            return
        a, b = Path(str(a)).stem, Path(str(b)).stem
        if a in names and b in names:
            s = float(s)
            sims[(a, b)] = sims[(b, a)] = s

    # 1) CSV export
    for f in list(res_base.parent.rglob("*.csv")):
        try:
            rows = list(csv.reader(open(f, encoding="utf-8", errors="replace")))
        except Exception:
            continue
        if not rows:
            continue
        hdr = [h.lower() for h in rows[0]]
        name_cols = [i for i, h in enumerate(hdr) if "name" in h or "submission" in h]
        sim_cols = [i for i, h in enumerate(hdr) if "avg" in h or "average" in h] or \
                   [i for i, h in enumerate(hdr) if "sim" in h]
        if len(name_cols) >= 2 and sim_cols:
            for r in rows[1:]:
                try:
                    put(r[name_cols[0]], r[name_cols[1]], r[sim_cols[0]])
                except (IndexError, ValueError):
                    pass
    # 2) result archive (.zip / .jplag) -> any JSON object describing a comparison
    archives = [p for p in res_base.parent.iterdir() if p.suffix in (".zip", ".jplag")]

    def walk(o):
        if isinstance(o, dict):
            keys = {k.lower().replace("_", ""): k for k in o}
            a = o.get(keys.get("firstsubmission")) or o.get(keys.get("firstsubmissionid")) or o.get(keys.get("id1"))
            b = o.get(keys.get("secondsubmission")) or o.get(keys.get("secondsubmissionid")) or o.get(keys.get("id2"))
            s = None
            simk = keys.get("similarities")
            if simk and isinstance(o[simk], dict):
                s = o[simk].get("AVG", o[simk].get("avg", o[simk].get("AVERAGE")))
            elif keys.get("similarity") is not None:
                s = o[keys["similarity"]]
            if isinstance(a, str) and isinstance(b, str) and isinstance(s, (int, float)):
                put(a, b, s)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for arc in archives:
        try:
            with zipfile.ZipFile(arc) as z:
                for n in z.namelist():
                    if n.endswith(".json"):
                        try:
                            walk(json.loads(z.read(n).decode("utf-8", "replace")))
                        except Exception:
                            pass
        except zipfile.BadZipFile:
            pass
    if sims and max(sims.values()) > 1.0:
        sims = {k: v / 100.0 for k, v in sims.items()}
    return sims


_JPLAG_ARGSETS = [
    lambda t, r, s: ["-l", "python3", "-t", str(t), "-n", "-1", "-M", "RUN", "--csv-export", "--overwrite", "-r", r, s],
    lambda t, r, s: ["-l", "python3", "-t", str(t), "-n", "-1", "-M", "RUN", "--csv-export", "-r", r, s],
    lambda t, r, s: ["-l", "python3", "-t", str(t), "-n", "-1", "-M", "RUN", "-r", r, s],
    lambda t, r, s: ["-l", "python3", "-t", str(t), "-n", "-1", "-r", r, s],
]
_jplag_argset = None


def jplag_group(progs, workdir: Path, min_tokens=5):
    """progs: list of (pid, code) for one problem. Returns {(pid_a, pid_b): similarity in [0,1]}."""
    global _jplag_argset
    java = find_java()
    jar = jplag_jar()
    if len(progs) < 2:
        return {}
    if not java or not jar.exists():
        return None
    if workdir.exists():
        shutil.rmtree(workdir)
    sub = workdir / "sub"
    sub.mkdir(parents=True)
    names = {}
    for i, (pid, code) in enumerate(progs):
        nm = f"p{i}"
        names[nm] = pid
        (sub / f"{nm}.py").write_text(code, encoding="utf-8")
    res = workdir / "out" / "result"
    res.parent.mkdir()
    order = [_jplag_argset] if _jplag_argset is not None else range(len(_JPLAG_ARGSETS))
    p = None
    # a fixed argument set is retried once on timeout (an occasional JVM stall was seen on one group)
    order = [k for k in order for _ in range(2 if _jplag_argset is not None else 1)]
    for k in order:
        args = _JPLAG_ARGSETS[k](min_tokens, str(res), str(sub))
        try:
            p = subprocess.run([java, "-Xmx2g", "-jar", str(jar)] + args, capture_output=True, text=True,
                               timeout=300, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            log(f"  JPlag timeout in {workdir} (argset {k})")
            continue
        sims = _parse_jplag_outputs(res, set(names))
        if p.returncode == 0 and sims:
            _jplag_argset = k
            return {(names[a], names[b]): s for (a, b), s in sims.items()}
        if p.returncode == 0 and not sims and k == _jplag_argset:
            break
    err = (p.stdout[-300:] + p.stderr[-300:]) if p is not None else "timeout"
    log(f"  JPlag failed in {workdir}: {err}")
    return None  # tool failure -> pairs stay missing (NOT distance 1)


# ------------------------------------------------------------------ embeddings
def embeddings(repo, codes):
    """Runs src.embed in a subprocess (keeps CUDA out of the main process). Returns np.array [n, d]."""
    from .generate import delete_model, download_model, model_tag
    cache = C.CACHE_DIR / f"emb_{model_tag(repo)}_v2.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        m = dict(zip(z["keys"], z["vecs"]))
        if all(c in m for c in codes):
            return np.stack([m[c] for c in codes])
    path = download_model(repo)
    inp = C.TMP_DIR / "emb_in.json"
    out = C.TMP_DIR / "emb_out.npy"
    inp.parent.mkdir(parents=True, exist_ok=True)
    inp.write_text(json.dumps(codes), encoding="utf-8")
    import os
    # EMBED_GPU: which GPU computes embeddings ("" = CPU, e.g. when GPU 0 belongs to another job)
    env_gpu = {"CUDA_VISIBLE_DEVICES": os.environ.get("EMBED_GPU", "0")}
    p = subprocess.run([sys.executable, "-m", "src.embed", str(path), str(inp), str(out)], cwd=str(C.EXP_DIR),
                       env=dict(os.environ, **env_gpu))
    if p.returncode != 0:
        log(f"  embedding with {repo} failed")
        return None
    vecs = np.load(out)
    np.savez(cache, keys=np.array(codes, dtype=object), vecs=vecs)
    delete_model(repo)
    return vecs


def d_cos(u, v):
    return float(1.0 - np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-9))
