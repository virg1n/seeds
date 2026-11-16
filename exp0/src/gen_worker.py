"""One generation worker = one GPU. Started by generate.py as
    python -m src.gen_worker SPEC.json SHARD NSHARDS OUT.jsonl
Handles "sample" jobs (independent requests) and "chain" jobs ("solve differently than these",
sequential rounds; the worker owns whole chains so no cross-GPU sync is needed)."""
from __future__ import annotations

import json
import os
import sys
import time
import zlib


def _seed(*parts):
    return zlib.crc32("|".join(map(str, parts)).encode()) & 0x7FFFFFFF


class VLLMEngine:
    def __init__(self, path, cfg):
        import dataclasses
        from vllm import LLM
        from vllm.engine.arg_utils import EngineArgs
        fields = {f.name for f in dataclasses.fields(EngineArgs)}
        # prefix caching off: the n samples of a request share the prompt anyway, and prefix caching
        # for hybrid (Gated DeltaNet / Mamba-style) models such as Qwen3.5 is still experimental
        kw = dict(model=path, dtype=cfg.get("dtype", "bfloat16"), max_model_len=cfg["max_model_len"],
                  gpu_memory_utilization=cfg["gpu_mem"], seed=0, enable_prefix_caching=False, max_num_seqs=256)
        with open(os.path.join(path, "config.json")) as f:
            hf_cfg = json.load(f)
        if "vision_config" in hf_cfg:  # Qwen3.5 is natively multimodal -> run text only
            if "language_model_only" in fields:
                kw["language_model_only"] = True
            elif "limit_mm_per_prompt" in fields:
                kw["limit_mm_per_prompt"] = {"image": 0, "video": 0}
        kw = {k: v for k, v in kw.items() if k in fields or k == "model"}
        self.llm = LLM(**kw)
        self.tok = self.llm.get_tokenizer()

    def generate(self, prompts, params):
        from vllm import SamplingParams
        sps = [SamplingParams(n=p["n"], temperature=p["temperature"], top_p=p["top_p"], top_k=p["top_k"],
                              max_tokens=p["max_tokens"], seed=p["seed"]) for p in params]
        outs = self.llm.generate(prompts, sps, use_tqdm=False)
        return [[(o.text, o.finish_reason == "length") for o in out.outputs] for out in outs]


class HFEngine:
    """HF transformers backend (e.g. GPUs that current vLLM does not support, such as V100).
    Sequences of many requests are generated together in length-sorted batches of up to
    cfg["hf_batch"] sequences under a token budget; on CUDA OOM the batch is halved."""

    def __init__(self, path, cfg):
        import torch
        import transformers as T
        dtype = getattr(torch, cfg.get("dtype", "bfloat16"))
        self.torch = torch
        self.tok = T.AutoTokenizer.from_pretrained(path)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        model = None
        for cls in ("AutoModelForCausalLM", "AutoModelForImageTextToText"):
            try:
                model = getattr(T, cls).from_pretrained(path, dtype=dtype)
                break
            except Exception as e:  # noqa
                print("HF load with", cls, "failed:", e, flush=True)
        self.model = model.cuda().eval()
        # stop on the end of the assistant turn (<|im_end|>) as well as on the model's eos: Qwen3.5's
        # config eos is <|endoftext|>, the chat turn ends with <|im_end|>
        stop = set()
        for t in ("<|im_end|>", "<|endoftext|>"):
            i = self.tok.convert_tokens_to_ids(t)
            if isinstance(i, int) and i != self.tok.unk_token_id:
                stop.add(i)
        for i in (self.tok.eos_token_id, getattr(self.model.generation_config, "eos_token_id", None)):
            if isinstance(i, int):
                stop.add(i)
            elif isinstance(i, (list, tuple)):
                stop.update(int(x) for x in i)
        self.stop_ids = sorted(stop)
        print(f"  stop token ids: {self.stop_ids}", flush=True)
        self.max_batch = int(cfg.get("hf_batch", 128))
        self.token_budget = int(cfg.get("hf_token_budget", 128 * 2048))

    def _run(self, batch, key, seed):
        torch = self.torch
        temperature, top_p, top_k, max_tokens = key
        enc = self.tok([b[1] for b in batch], return_tensors="pt", padding=True).to("cuda")
        torch.manual_seed(seed)
        with torch.no_grad():
            # repetition_penalty=1.0 explicitly: otherwise HF silently takes it from the model's
            # generation_config.json (Qwen2.5-Coder ships 1.1) and models would be sampled differently
            out = self.model.generate(**enc, do_sample=True, temperature=temperature, top_p=top_p, top_k=top_k,
                                      max_new_tokens=max_tokens, pad_token_id=self.tok.pad_token_id,
                                      eos_token_id=self.stop_ids, repetition_penalty=1.0)
        gen = out[:, enc["input_ids"].shape[1]:]
        finished = torch.isin(gen, torch.tensor(self.stop_ids, device=gen.device)).any(dim=1).tolist()
        texts = self.tok.batch_decode(gen, skip_special_tokens=True)
        return [(t, not f) for t, f in zip(texts, finished)]  # (text, truncated at max_tokens)

    def generate(self, prompts, params):
        import time
        torch = self.torch
        res = [[None] * p["n"] for p in params]
        plen = [len(self.tok.encode(pr)) for pr in prompts]
        groups = {}
        for i, (pr, p) in enumerate(zip(prompts, params)):
            key = (p["temperature"], p["top_p"], p["top_k"], p["max_tokens"])
            for j in range(p["n"]):
                groups.setdefault(key, []).append((i, pr, j, plen[i], p["seed"]))
        done, total, t0 = 0, sum(len(v) for v in groups.values()), time.time()
        for key, items in groups.items():
            items.sort(key=lambda x: x[3])
            k = 0
            while k < len(items):
                B = min(self.max_batch, len(items) - k)
                while B > 1 and B * (items[k + B - 1][3] + key[3]) > self.token_budget:
                    B //= 2
                batch = items[k:k + B]
                try:
                    texts = self._run(batch, key, seed=batch[0][4] + 7919 * batch[0][2] + k)
                except torch.cuda.OutOfMemoryError:
                    torch.cuda.empty_cache()
                    if B == 1:
                        raise
                    self.max_batch = max(1, B // 2)
                    print(f"  OOM at batch {B} -> max batch {self.max_batch}", flush=True)
                    continue
                for (i, _, j, _, _), t in zip(batch, texts):
                    res[i][j] = t
                k += B
                done += B
                print(f"  hf: {done}/{total} sequences, {time.time() - t0:.0f}s", flush=True)
        return res


def main():
    spec_path, shard, nshards, out_path = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    from . import prompts as PR
    cfg, samp = spec["cfg"], spec["sampling"]
    t0 = time.time()
    backend = cfg["backend"]
    try:
        eng = VLLMEngine(spec["model_path"], cfg) if backend == "vllm" else HFEngine(spec["model_path"], cfg)
    except Exception as e:  # noqa  -- fail fast; the orchestrator decides about a fallback
        import traceback
        traceback.print_exc()
        print(f"[worker {shard}] {backend} engine failed to start: {e!r}", flush=True)
        sys.exit(3)
    tok = eng.tok
    budget = cfg["max_model_len"] - samp["max_tokens"] - 16
    print(f"[worker {shard}] engine ready in {time.time() - t0:.0f}s", flush=True)

    def render(msgs):
        try:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    def fits(prompt):
        return len(tok.encode(prompt)) <= budget

    out = open(out_path, "a", encoding="utf-8")
    tag = spec["model_tag"]
    for job in spec["jobs"]:
        jt0 = time.time()
        if job["type"] == "sample":
            reqs = [r for i, r in enumerate(job["requests"]) if i % nshards == shard]
            prompts, params, keep = [], [], []
            for r in reqs:
                pr = render(r["msgs"])
                if not fits(pr):  # recorded as empty (= incorrect) samples, so the budget stays honest
                    for j in range(r["n"]):
                        out.write(json.dumps(dict(r["meta"], model=tag, cond=job["name"], task=r["task"], sample=j,
                                                  text="", code="", skipped="prompt_too_long",
                                                  backend=backend)) + "\n")
                    continue
                prompts.append(pr)
                params.append(dict(samp, n=r["n"], seed=r["seed"],
                                   **({"temperature": r["temperature"]} if "temperature" in r else {})))
                keep.append(r)
            texts = eng.generate(prompts, params) if prompts else []
            for r, ts in zip(keep, texts):
                for j, (t, trunc) in enumerate(ts):
                    row = dict(r["meta"], model=tag, cond=job["name"], task=r["task"], sample=j, text=t,
                               code=PR.extract_code(t), backend=backend, truncated=bool(trunc))
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
        elif job["type"] == "chain":
            tasks = [t for i, t in enumerate(job["tasks"]) if i % nshards == shard]
            chains = [(t, c, []) for t in tasks for c in range(job["chains"])]
            for rnd in range(job["rounds"]):
                prompts, params, idx = [], [], []
                for k, (t, c, prev) in enumerate(chains):
                    shown = list(dict.fromkeys(p for p in prev if p.strip()))[-job["show"]:]
                    while True:
                        msgs = PR.plain(t) if rnd == 0 or not shown else PR.differently(t, shown)
                        pr = render(msgs)
                        if fits(pr) or not shown:
                            break
                        shown = shown[1:]
                    if not fits(pr):
                        prev.append("")
                        out.write(json.dumps(dict(model=tag, cond=job["name"], task=t["id"], chain=c, round=rnd,
                                                  sample=rnd, text="", code="", skipped="prompt_too_long",
                                                  backend=backend)) + "\n")
                        continue
                    prompts.append(pr)
                    params.append(dict(samp, n=1, seed=_seed(tag, t["id"], c, rnd)))
                    idx.append(k)
                texts = eng.generate(prompts, params) if prompts else []
                for k, ts in zip(idx, texts):
                    t, c, prev = chains[k]
                    text, trunc = ts[0]
                    code = PR.extract_code(text)
                    prev.append(code)
                    row = dict(model=tag, cond=job["name"], task=t["id"], chain=c, round=rnd, sample=rnd,
                               text=text, code=code, backend=backend, truncated=bool(trunc))
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out.flush()
                print(f"[worker {shard}] chain round {rnd + 1}/{job['rounds']} done", flush=True)
        print(f"[worker {shard}] job {job['name']} done in {time.time() - jt0:.0f}s", flush=True)
    out.close()
    print(f"[worker {shard}] all done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
