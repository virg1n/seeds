"""CPU tests of st/model.py + st/sampler.py on a tiny random Qwen2:
    MODEL_TINY=1 python -m tests.test_model"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("MODEL_TINY", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch  # noqa: E402

from st import config as CFG  # noqa: E402
from st import model as M  # noqa: E402
from st import sampler as S  # noqa: E402

TOL = 1e-3
TASKS = [{"id": f"t{i}", "source": "apps", "kind": k, "entry": "solve", "starter": "", "text": "Add numbers. " * (1 + 3 * i)}
         for i, k in enumerate(["func", "stdio", "func", "stdio"])]


def policy(mode):
    return M.Policy(M.model_path(), mode, "cpu")


def perturb(pol, std=0.3):
    g = torch.Generator().manual_seed(1)
    with torch.no_grad():
        pol.mod.U.copy_(torch.randn(pol.mod.U.shape, generator=g) * std)
        for w in pol.lora.values():
            w.B.copy_(torch.randn(w.B.shape, generator=g) * 0.05)


def left_logits(pol, prompts, seeds):
    """Logits of a left-padded batch at the real positions of every row (list of [len, V])."""
    L = max(map(len, prompts))
    x = torch.full((len(prompts), L), pol.pad, dtype=torch.long)
    att = torch.zeros_like(x)
    for r, p in enumerate(prompts):
        x[r, L - len(p):] = torch.tensor(p)
        att[r, L - len(p):] = 1
    pos = (att.cumsum(1) - 1).clamp(min=0)
    pol.model.eval()
    with torch.no_grad():
        pol.set_seeds(seeds)
        lg = pol.model(input_ids=x, attention_mask=att, position_ids=pos).logits
        pol.set_seeds(None)
    return [lg[r, L - len(p):] for r, p in enumerate(prompts)]


def close(a, b, tol=TOL):
    return float((a - b).abs().max()) <= tol


def test_render():
    pf, pp = policy("film"), policy("prompt")
    a, b = pf.render(TASKS[0], 0), pf.render(TASKS[0], 3)
    assert a == b and isinstance(a[0], int)
    c, d = pp.render(TASKS[0], 0), pp.render(TASKS[0], 1)
    assert c != d and "Strategy 1." in pp.tok.decode(c) and "Strategy 2." in pp.tok.decode(d)
    print("ok render")


def test_zero_init():
    base, film = policy("base"), policy("film")
    ps = [base.render(t) for t in TASKS[:2]]
    lb = left_logits(base, ps, None)
    lf = left_logits(film, ps, [0, 1])
    assert all(close(x, y, 1e-5) for x, y in zip(lb, lf)), "fresh film policy != base"
    assert film.gain_stats()["gain_dev_mean"] == 0.0
    print("ok zero-init equivalence")


def test_seeds_rows():
    pol = policy("film")
    perturb(pol)
    p = pol.render(TASKS[1])
    q = pol.render(TASKS[3])
    a = left_logits(pol, [p, p, q], [0, 1, 2])
    assert not close(a[0], a[1], 1e-2), "different seeds give the same logits"
    b = left_logits(pol, [p, q, p], [0, 3, 2])
    single = left_logits(pol, [p], [0])[0]
    assert close(a[0], b[0]) and close(a[0], single), "row 0 depends on the seeds of other rows"
    c = left_logits(pol, [q], [2])[0]
    assert close(a[2], c), "batched left-padded scoring != single row"
    st = pol.gain_stats()
    assert len(st["gain_dev"]) == CFG.N_SEEDS and st["delta_cos"] is not None and st["gain_dev_mean"] > 0
    print("ok seeds per row, no leak, left padding;", {k: st[k] for k in ("gain_dev_mean", "delta_cos")})


def test_rollout_logprob():
    pol = policy("film")
    perturb(pol)
    ps = [pol.render(t) for t in TASKS] + [pol.render(TASKS[0])[:-7]]
    seeds = [3, 0, 2, 1, 0]
    rows = [{"p": ps[i], "seed": seeds[i]} for i in (2, 0, 4, 3, 1)]       # not sorted by length
    old = CFG.GEN_BATCH
    CFG.GEN_BATCH = 3                                                      # several generate calls
    try:
        out = S.rollout(pol, rows, seed=5, max_tokens=12, desc="test", logprobs=True)
        again = S.rollout(pol, rows, seed=5, max_tokens=12)
    finally:
        CFG.GEN_BATCH = old
    assert [o["t"] for o in out] == [o["t"] for o in again], "rollout not reproducible"
    sc = [{"p": r["p"], "t": o["t"], "seed": r["seed"]} for r, o in zip(rows, out)]
    lp = S.sequence_logprob(pol, sc, mb_tokens=40)                         # several micro-batches
    d = [abs(a - o["lp"]) for a, o in zip(lp, out)]
    assert max(d) < TOL, f"rollout log-probs != sequence_logprob: {d}"
    # the training path (train mode, gradient checkpointing) gives the same numbers
    nll, ntok = S.backward_pg(pol, sc, [0.0] * len(sc), mb_tokens=10 ** 6)
    assert ntok == [len(o["t"]) for o in out]
    assert max(abs(a + b) for a, b in zip(lp, nll)) < TOL
    # wrong seeds must change the score (the test above is not vacuous)
    wrong = S.sequence_logprob(pol, [dict(r, seed=r["seed"] + 1) for r in sc])
    assert max(abs(a - b) for a, b in zip(lp, wrong)) > 1e-2
    # single-row scoring == batched scoring
    single = [S.sequence_logprob(pol, [r])[0] for r in sc]
    assert max(abs(a - b) for a, b in zip(lp, single)) < TOL
    print(f"ok rollout lp == sequence_logprob == -backward_pg nll (max diff {max(d):.2e}),"
          f" truncated {sum(o['truncated'] for o in out)}/{len(out)}")


def test_backward_and_state():
    pol = policy("film")
    perturb(pol)
    ps = [pol.render(t) for t in TASKS[:3]]
    out = S.rollout(pol, [{"p": p, "seed": z} for p, z in zip(ps, [0, 1, 2])], seed=0, max_tokens=8)
    rows = [{"p": p, "t": o["t"], "seed": z} for p, o, z in zip(ps, out, [0, 1, 2])]
    S.backward_pg(pol, rows, [1.0, -0.5, 0.25], mb_tokens=60)
    for n, w in pol.lora.items():
        assert w.A.grad is not None and w.A.grad.abs().sum() > 0, n
        assert w.B.grad is not None and w.B.grad.abs().sum() > 0, n
    for n, p in pol.mod.named_parameters():
        assert p.grad is not None and p.grad.abs().sum() > 0, n
    base = [n for n, p in pol.model.named_parameters() if not (n.endswith(".A") or n.endswith(".B"))]
    assert base and all(dict(pol.model.named_parameters())[n].grad is None for n in base)
    # gradient check of the modulator against a finite difference of sequence_logprob
    g = pol.mod.U.grad.clone()
    j = tuple(int(v) for v in (g.abs() == g.abs().max()).nonzero()[0])
    eps, coef = 1e-3, [1.0, -0.5, 0.25]
    def loss():
        return -sum(c * v for c, v in zip(coef, S.sequence_logprob(pol, rows)))
    with torch.no_grad():
        pol.mod.U[j] += eps
        lp_ = loss()
        pol.mod.U[j] -= 2 * eps
        lm_ = loss()
        pol.mod.U[j] += eps
    fd = (lp_ - lm_) / (2 * eps)
    assert abs(fd - float(g[j])) < 3e-2 * max(1.0, abs(fd)), (fd, float(g[j]))
    groups = pol.param_groups(1e-4)
    assert [gr["lr"] for gr in groups] == [1e-4, 1e-4 * CFG.FILM_LR_RATIO]
    assert sum(len(gr["params"]) for gr in groups) == len(pol.trainable())
    # state round trip
    sd = pol.state()
    ref = S.sequence_logprob(pol, rows)
    other = policy("film")
    assert max(abs(a - b) for a, b in zip(ref, S.sequence_logprob(other, rows))) > 1e-3
    other.load_state(sd)
    assert max(abs(a - b) for a, b in zip(ref, S.sequence_logprob(other, rows))) < 1e-5
    assert policy("base").trainable() == [] and policy("base").gain_stats() == {}
    assert policy("none").gain_stats() == {} and policy("none").trainable()
    print(f"ok backward_pg grads (fd {fd:.4f} vs {float(g[j]):.4f}), param groups, state round trip")


if __name__ == "__main__":
    torch.set_num_threads(max(1, min(8, os.cpu_count() or 1)))
    test_render()
    test_zero_init()
    test_seeds_rows()
    test_rollout_logprob()
    test_backward_and_state()
    print("ALL OK")
