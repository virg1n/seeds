"""Rollouts (HF generate, KV cache, left padding) and the policy-gradient backward pass
(teacher forcing, right padding, gradient checkpointing) of a `st.model.Policy`.

Both paths compute the same log pi for the same tokens: the seed gains of a row follow the row
through the length sorting, the gains stay set until backward has run, and the vocabulary
projection is applied to completion positions only (log-softmax in float32)."""
from __future__ import annotations

import time

import torch
from torch.utils.checkpoint import checkpoint

from . import config as CFG

HEAD_CHUNK = CFG._env("HEAD_CHUNK", 2048, int)     # completion positions per lm_head / log-softmax chunk


def _log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def _is_oom(e):
    return isinstance(e, getattr(torch, "OutOfMemoryError", torch.cuda.OutOfMemoryError)) or "out of memory" in str(e).lower()


def stop_ids(tok):
    ids = [tok.convert_tokens_to_ids(t) for t in ("<|im_end|>", "<|endoftext|>")] + [tok.eos_token_id]
    return sorted({i for i in ids if isinstance(i, int) and i != tok.unk_token_id})


def gen_config(policy, max_tokens):
    """Explicit sampling config; also installed as the model's own one (see rollout)."""
    from transformers import GenerationConfig
    kw = dict(do_sample=True, temperature=CFG.TEMPERATURE, top_p=CFG.TOP_P, top_k=CFG.TOP_K) \
        if CFG.TEMPERATURE > 0 else dict(do_sample=False)
    return GenerationConfig(max_new_tokens=max_tokens, eos_token_id=stop_ids(policy.tok), pad_token_id=policy.pad,
                            use_cache=True, repetition_penalty=1.0, **kw)


def _plan(rows, max_tokens, batch, tokens):
    """Calls of row indices: sorted by prompt length, <= batch rows, rows * (longest + max_tokens) <= tokens."""
    order = sorted(range(len(rows)), key=lambda i: (len(rows[i]["p"]), i))
    calls = []
    for i in order:
        if calls and len(calls[-1]) < batch and (len(calls[-1]) + 1) * (len(rows[i]["p"]) + max_tokens) <= tokens:
            calls[-1].append(i)
        else:
            calls.append([i])
    return calls


@torch.no_grad()
def rollout(policy, rows, seed, max_tokens=None, desc="", logprobs=False):
    """rows [{"p": prompt ids, "seed": int}] -> [{"t", "truncated", "text"}] in the same order.
    logprobs=True (tests) adds "lp": the sum of the sampling log-probs of t (raw logits, i.e. at T = 1)."""
    if not rows:
        return []
    t0 = time.time()
    max_tokens = int(max_tokens or CFG.MAX_TOKENS)
    model, dev = policy.model, policy.device
    gc = gen_config(policy, max_tokens)
    stops = set(gc.eos_token_id)
    model.eval()
    model.generation_config = gc          # generate() would otherwise fill "default" values from the hub config
    batch = CFG.GEN_BATCH
    todo = _plan(rows, max_tokens, batch, CFG.GEN_TOKENS)
    out, k, ntok = [None] * len(rows), 0, 0
    while todo:
        ids = todo.pop(0)
        L = max(len(rows[i]["p"]) for i in ids)
        x = torch.full((len(ids), L), policy.pad, dtype=torch.long)
        att = torch.zeros((len(ids), L), dtype=torch.long)
        for r, i in enumerate(ids):
            p = rows[i]["p"]
            x[r, L - len(p):] = torch.tensor(p, dtype=torch.long)
            att[r, L - len(p):] = 1
        torch.manual_seed(int(seed) + k)
        k += 1
        try:
            with policy.autocast():
                policy.set_seeds([rows[i]["seed"] for i in ids])
                res = model.generate(input_ids=x.to(dev), attention_mask=att.to(dev), generation_config=gc,
                                     return_dict_in_generate=True, output_logits=logprobs)
        except Exception as e:  # noqa: BLE001
            policy.set_seeds(None)
            if not (_is_oom(e) and len(ids) > 1):
                raise
            res = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            batch = max(1, len(ids) // 2)
            _log(f"[rollout{':' + desc if desc else ''}] OOM with {len(ids)} rows, retrying with {batch}")
            todo = [ids[:batch], ids[batch:]] + [c[j:j + batch] for c in todo for j in range(0, len(c), batch)]
            continue
        policy.set_seeds(None)
        seq = res.sequences[:, L:].tolist()
        lps = None
        if logprobs:
            lg = torch.stack(res.logits, 1).float().log_softmax(-1)   # [B, steps, V]
            lps = lg.gather(-1, res.sequences[:, L:, None].to(lg.device))[..., 0].cpu()
        for r, (i, t) in enumerate(zip(ids, seq)):
            cut = next((j for j, v in enumerate(t) if v in stops), None)
            t, trunc = (t[:cut + 1], False) if cut is not None else (t, True)
            out[i] = {"t": t, "truncated": trunc, "text": policy.tok.decode(t, skip_special_tokens=True)}
            if logprobs:
                out[i]["lp"] = float(lps[r, :len(t)].sum())
            ntok += len(t)
    if desc:
        _log(f"[rollout:{desc}] {len(rows)} rows, {k} calls, {ntok} tokens, "
             f"{sum(o['truncated'] for o in out)} truncated, {time.time() - t0:.1f}s")
    return out


# ------------------------------------------------------------------ teacher forcing
def micro(rows, budget):
    """Micro-batches of row indices, sorted by length, <= budget padded tokens (a longer row goes alone)."""
    idx = sorted(range(len(rows)), key=lambda i: (len(rows[i]["p"]) + len(rows[i]["t"]), i))
    out, cur, mx = [], [], 0
    for i in idx:
        n = len(rows[i]["p"]) + len(rows[i]["t"])
        if cur and max(mx, n) * (len(cur) + 1) > budget:
            out.append(cur)
            cur, mx = [], 0
        cur.append(i)
        mx = max(mx, n)
    if cur:
        out.append(cur)
    return out


def collate(rows, ids, pad, dev):
    """Right-padded inputs, attention mask, and the target of every position (-100: no target)."""
    T = max(len(rows[i]["p"]) + len(rows[i]["t"]) for i in ids)
    x = torch.full((len(ids), T), pad, dtype=torch.long)
    att = torch.zeros((len(ids), T), dtype=torch.long)
    tgt = torch.full((len(ids), T), -100, dtype=torch.long)
    for r, i in enumerate(ids):
        p, t = rows[i]["p"], rows[i]["t"]
        x[r, :len(p) + len(t)] = torch.tensor(list(p) + list(t), dtype=torch.long)
        att[r, :len(p) + len(t)] = 1
        if t:
            tgt[r, len(p) - 1:len(p) + len(t) - 1] = torch.tensor(t, dtype=torch.long)  # position j predicts j + 1
    return x.to(dev), att.to(dev), tgt.to(dev)


def _token_logp(head, h, y):
    return head(h).float().log_softmax(-1).gather(-1, y[:, None])[:, 0]


def _row_logp(policy, x, att, tgt, grad):
    """Sum of log pi over the target positions of every row: [B] float32."""
    h = policy.model.model(input_ids=x, attention_mask=att).last_hidden_state
    m = tgt != -100
    hs, y = h[m], tgt[m]
    rid = torch.arange(x.shape[0], device=x.device)[:, None].expand_as(tgt)[m]
    parts = []
    for s in range(0, len(y), HEAD_CHUNK):
        a, b = hs[s:s + HEAD_CHUNK], y[s:s + HEAD_CHUNK]
        parts.append(checkpoint(_token_logp, policy.model.lm_head, a, b, use_reentrant=False) if grad
                     else _token_logp(policy.model.lm_head, a, b))
    lp = torch.cat(parts) if parts else hs.new_zeros(0, dtype=torch.float32)
    return torch.zeros(x.shape[0], device=x.device, dtype=torch.float32).index_add_(0, rid, lp.float())


def _zero_grads(policy):
    for p in policy.trainable():
        p.grad = None


def backward_pg(policy, rows, coef, mb_tokens=None):
    """Accumulates the gradient of sum_i coef_i * NLL_i (NLL_i summed over the completion tokens of row i).
    Returns (NLL_i, number of completion tokens). CUDA OOM: zero the grads, halve mb_tokens, restart."""
    mb = int(mb_tokens or CFG.MB_TOKENS)
    while True:
        try:
            return _teacher(policy, rows, coef, mb, grad=True)
        except Exception as e:  # noqa: BLE001
            policy.set_seeds(None)
            if not _is_oom(e) or mb <= 256:
                raise
            _zero_grads(policy)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            mb //= 2
            _log(f"[backward_pg] OOM, restarting with mb_tokens={mb}")


@torch.no_grad()
def sequence_logprob(policy, rows, mb_tokens=None) -> list[float]:
    """No-grad sum of log pi(t | p, seed) per row."""
    nll, _ = _teacher(policy, rows, None, int(mb_tokens or CFG.MB_TOKENS), grad=False)
    return [-v for v in nll]


def _teacher(policy, rows, coef, mb, grad):
    nll, ntok = [0.0] * len(rows), [len(r["t"]) for r in rows]
    policy.model.train(grad)
    dev = policy.device
    for ids in micro(rows, mb):
        x, att, tgt = collate(rows, ids, policy.pad, dev)
        with policy.autocast():
            policy.set_seeds([rows[i]["seed"] for i in ids])
            lp = _row_logp(policy, x, att, tgt, grad)
        if grad:
            c = torch.tensor([float(coef[i]) for i in ids], device=dev, dtype=torch.float32)
            loss = -(lp * c).sum()
            if loss.requires_grad:
                loss.backward()           # the gains are still set: checkpointing re-runs the hooks here
        policy.set_seeds(None)
        for i, v in zip(ids, lp.detach().cpu().tolist()):
            nll[i] = -v
    policy.model.eval()
    return nll, ntok
