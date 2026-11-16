"""Model download (within the disk budget) + data-parallel generation on all GPUs."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import zlib

from . import config as C
from . import prompts as PR
from .utils import CHILDREN, disk_status, ensure_budget, log, read_jsonl, sha, write_jsonl

ALLOW = ["*.json", "*.safetensors", "*.txt", "*.model", "*.jinja", "*.tiktoken", "tokenizer*", "merges*",
         "vocab*"]


def model_tag(repo):
    return repo.split("/")[-1].lower().replace(".", "_")


def model_dir(repo):
    return C.MODELS_DIR / repo.replace("/", "__")


def _repo_size_gb(repo):
    try:
        from fnmatch import fnmatch
        from huggingface_hub import HfApi
        info = HfApi().model_info(repo, files_metadata=True)
        names = [s.rfilename for s in info.siblings]
        allow = ALLOW + ([] if any(n.endswith(".safetensors") for n in names) else ["*.bin"])
        tot = 0
        for s in info.siblings:
            if any(fnmatch(s.rfilename, p) for p in allow):
                tot += s.size or 0
        return tot / 1e9
    except Exception as e:  # noqa
        log(f"  could not query size of {repo}: {e}; assuming 5 GB")
        return 5.0


def download_model(repo):
    d = model_dir(repo)
    if (d / ".complete").exists():
        return d
    size = _repo_size_gb(repo)
    ensure_budget(size + 0.3, f"download {repo} ({size:.1f} GB)")
    from huggingface_hub import list_repo_files, snapshot_download
    allow = list(ALLOW)
    try:
        if not any(f.endswith(".safetensors") for f in list_repo_files(repo)):
            allow.append("*.bin")  # old checkpoints (e.g. unixcoder) ship only pytorch_model.bin
    except Exception:
        pass
    log(f"downloading {repo} -> {d}")
    for attempt in range(3):
        try:
            snapshot_download(repo, local_dir=str(d), allow_patterns=allow)
            break
        except Exception as e:  # noqa
            log(f"  download attempt {attempt + 1} failed: {e}")
            time.sleep(10)
    else:
        raise SystemExit(f"could not download {repo}")
    shutil.rmtree(d / ".cache", ignore_errors=True)
    (d / ".complete").write_text("ok")
    disk_status(f"after download {repo}")
    return d


def delete_model(repo):
    if C.KEEP_MODELS:
        return
    d = model_dir(repo)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
        log(f"deleted weights of {repo} (KEEP_MODELS=0)")


def gpu_dtype():
    if C.DTYPE != "auto":
        return C.DTYPE
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=30).stdout
        caps = [float(x) for x in out.split()]
        if caps and min(caps) < 8.0:
            log(f"GPU compute capability {min(caps)} < 8.0 (no bfloat16) -> using float16")
            return "float16"
    except Exception:
        pass
    return "bfloat16"


def n_gpus():
    if C.GPU_IDS:
        return len(C.GPU_IDS)
    try:
        out = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=30).stdout
        n = sum(1 for l in out.splitlines() if l.startswith("GPU "))
        if not n:
            return 1
        return min(C.NUM_GPUS, n) if C.NUM_GPUS > 0 else n
    except Exception:
        return 1


def _seed(*parts):
    return zlib.crc32("|".join(map(str, parts)).encode()) & 0x7FFFFFFF


def _ptask(t):
    return {k: t.get(k) for k in ("id", "source", "kind", "entry", "text", "starter", "example_test")}


def build_jobs(tasks, tag, main: bool):
    jobs = [{"type": "sample", "name": "plain", "requests": [
        {"task": t["id"], "msgs": PR.plain(t), "n": C.N_SAMPLES, "seed": _seed(tag, t["id"], "plain"),
         "meta": {"strategy": 0}} for t in tasks]}]
    if main:
        for T in C.EXTRA_TEMPS:  # temperature sweep: plain sampling only
            jobs.append({"type": "sample", "name": f"plain_T{T}", "requests": [
                {"task": t["id"], "msgs": PR.plain(t), "n": C.N_SAMPLES, "seed": _seed(tag, t["id"], "plainT", T),
                 "temperature": float(T), "meta": {"strategy": 0, "temperature": float(T)}} for t in tasks]})
        jobs.append({"type": "sample", "name": "strategy", "requests": [
            {"task": t["id"], "msgs": PR.strategy(t, s), "n": C.N_PER_STRATEGY, "seed": _seed(tag, t["id"], "s", s),
             "meta": {"strategy": s}} for t in tasks for s in range(1, C.N_STRATEGIES + 1)]})
        jobs.append({"type": "chain", "name": "differently", "tasks": [_ptask(t) for t in tasks],
                     "chains": C.N_CHAINS, "rounds": C.CHAIN_LEN, "show": C.CHAIN_SHOW})
    return jobs


def _launch(spec_path, tag, G, backend):
    procs, shard_files = [], []
    for i in range(G):
        sf = C.GEN_DIR / f"{tag}.shard{i}.jsonl"
        if sf.exists():
            sf.unlink()
        shard_files.append(sf)
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(C.GPU_IDS[i]) if C.GPU_IDS else str(i),
                   VLLM_WORKER_MULTIPROC_METHOD="spawn",
                   TOKENIZERS_PARALLELISM="false", EXP0_BACKEND=backend)
        lf = open(C.LOG_DIR / f"gen_{tag}_{backend}_gpu{i}.log", "w")
        procs.append((subprocess.Popen([sys.executable, "-m", "src.gen_worker", str(spec_path), str(i), str(G), str(sf)],
                                       cwd=str(C.EXP_DIR), env=env, stdout=lf, stderr=subprocess.STDOUT), lf))
        CHILDREN.append(procs[-1][0])
    deadline = time.time() + C.GEN_TIMEOUT_H * 3600
    codes = [None] * G
    while any(c is None for c in codes):
        for k, (p, _) in enumerate(procs):
            if codes[k] is None:
                codes[k] = p.poll()
        failed = [c for c in codes if c not in (None, 0)]
        if failed or time.time() > deadline:  # fail fast: stop the siblings too
            for p, _ in procs:
                if p.poll() is None:
                    p.kill()
            for k, (p, _) in enumerate(procs):
                codes[k] = p.wait() if codes[k] is None else codes[k]
            if not failed:
                log(f"generation for {tag} exceeded GEN_TIMEOUT_H={C.GEN_TIMEOUT_H}")
                codes = [c if c else -1 for c in codes]
            break
        time.sleep(5)
    for _, lf in procs:
        lf.close()
    return codes, shard_files


def _spec_hash(spec):
    s = dict(spec)
    s.pop("model_path", None)
    return sha(json.dumps(s, sort_keys=True))


def run_model(repo, tasks, main: bool):
    tag = model_tag(repo)
    out_path = C.GEN_DIR / f"{tag}.jsonl"
    done = C.GEN_DIR / f"{tag}.done"
    spec = {"model_tag": tag, "repo": repo, "jobs": build_jobs(tasks, tag, main),
            "cfg": {"backend": C.BACKEND, "max_model_len": C.MAX_MODEL_LEN, "gpu_mem": C.GPU_MEM_UTIL,
                    "dtype": gpu_dtype(), "hf_batch": C.HF_BATCH, "hf_token_budget": C.HF_TOKEN_BUDGET},
            "sampling": {"temperature": C.TEMPERATURE, "top_p": C.TOP_P, "top_k": C.TOP_K,
                         "max_tokens": C.MAX_TOKENS}}
    h = _spec_hash(spec)
    if done.exists():
        if done.read_text().strip() == h:
            log(f"generation for {repo}: already done ({out_path})")
            return out_path
        log(f"generation for {repo}: configuration/tasks changed since the last run -> regenerating")
        done.unlink()
        out_path.unlink(missing_ok=True)
    path = download_model(repo)
    spec["model_path"] = str(path)
    C.GEN_DIR.mkdir(parents=True, exist_ok=True)
    C.LOG_DIR.mkdir(parents=True, exist_ok=True)
    spec_path = C.GEN_DIR / f"{tag}.spec.json"
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f)
    G = n_gpus()
    log(f"generation for {repo} on {G} GPU(s), backend={C.BACKEND}: jobs = {[j['name'] for j in spec['jobs']]}")
    t0 = time.time()
    codes, shard_files = _launch(spec_path, tag, G, C.BACKEND)
    if any(c != 0 for c in codes) and C.BACKEND == "vllm" and C.HF_FALLBACK:
        log(f"!!! vLLM workers failed (codes {codes}, see {C.LOG_DIR}/gen_{tag}_vllm_gpu*.log). "
            f"Retrying with the HF transformers backend in fresh processes (slow; recorded in every row). "
            f"Set HF_FALLBACK=0 to stop instead.")
        spec["cfg"]["backend"] = "hf"
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(spec, f)
        codes, shard_files = _launch(spec_path, tag, G, "hf")
    if any(c != 0 for c in codes):
        raise SystemExit(f"generation workers failed with codes {codes}; see {C.LOG_DIR}/gen_{tag}_*_gpu*.log")
    rows, seen = [], set()
    for sf in shard_files:
        for r in read_jsonl(sf):
            key = (r["cond"], r["task"], r.get("strategy"), r.get("chain"), r.get("round"), r["sample"])
            if key not in seen:
                seen.add(key)
                rows.append(r)
        sf.unlink()
    expected = _expected_rows(spec)
    if len(rows) != expected:
        raise SystemExit(f"generation for {repo}: got {len(rows)} rows, expected {expected}")
    write_jsonl(out_path, rows)
    done.write_text(h)
    spec_path.unlink()
    log(f"generation for {repo}: {len(rows)} samples in {time.time() - t0:.0f}s")
    delete_model(repo)
    return out_path


def _expected_rows(spec):
    n = 0
    for j in spec["jobs"]:
        if j["type"] == "sample":
            n += sum(r["n"] for r in j["requests"])
        else:
            n += len(j["tasks"]) * j["chains"] * j["rounds"]
    return n


def committed_generations():
    """Only fully finished generation files (with a .done marker); shards are never read."""
    rows = []
    for repo in [C.MAIN_MODEL] + C.EXTRA_MODELS:
        tag = model_tag(repo)
        f = C.GEN_DIR / f"{tag}.jsonl"
        if (C.GEN_DIR / f"{tag}.done").exists() and f.exists():
            rows += read_jsonl(f)
        else:
            log(f"WARNING: no finished generations for {repo}")
    return rows


def run_all(tasks):
    paths = {}
    for i, repo in enumerate([C.MAIN_MODEL] + C.EXTRA_MODELS):
        paths[repo] = run_model(repo, tasks, main=(i == 0))
    return paths
