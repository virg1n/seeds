"""Parts B and C: diversity of the model as-is, seed dependence, ceiling of forced diversity.

Labels per sample: None = incorrect; NOFP = correct but no usable fingerprint (counts for
pass@k, never as a group); otherwise the fingerprint group key of the requested level.
'Groups' are fingerprint groups (see Part A for how well they recover algorithm labels)."""
from __future__ import annotations

import itertools
import math
from collections import Counter, defaultdict

import numpy as np

from . import config as C
from . import fingerprint as FP
from .fpstore import evaluate, fingerprints
from .generate import committed_generations, model_tag
from .utils import log, read_json, write_json

LEVELS = ["L1", "L2", "L3", "phi", "phi_tau"]
LEVEL_NAMES = {"L1": "L1 scaling", "L2": "L2 scheme", "L3": "L3 primitives", "phi": "phi (all levels, exact key)",
               "phi_tau": "phi (d_phi <= tau clusters)"}
NOFP = "__nofp__"
MIN_CORRECT = (2, 4)  # homogeneity is reported for tasks with at least this many fingerprinted correct solutions


# ------------------------------------------------------------------ estimators
def expected_cover(strata, k):
    """strata: list of label lists. k samples are spread over the strata as evenly as possible
    (averaging over which strata get the remainder), drawn without replacement inside each stratum.
    Returns (P[>=1 correct], E[#distinct fingerprint groups among correct]) -- exact, hypergeometric."""
    strata = [s for s in strata if len(s) > 0]
    S = len(strata)
    if S == 0:
        return 0.0, 0.0
    base, extra = divmod(k, S)
    allocs = [[base + (1 if i in combo else 0) for i in range(S)] for combo in itertools.combinations(range(S), extra)]
    labels = {l for s in strata for l in s if l is not None and l != NOFP}
    p_pass, e_groups = 0.0, 0.0
    for alloc in allocs:
        alloc = [min(a, len(s)) for a, s in zip(alloc, strata)]

        def miss(pred):
            p = 1.0
            for s, a in zip(strata, alloc):
                n, g = len(s), sum(1 for l in s if pred(l))
                p *= math.comb(n - g, a) / math.comb(n, a)
            return p

        p_pass += 1 - miss(lambda l: l is not None)
        e_groups += sum(1 - miss(lambda l, L=L: l == L) for L in labels)
    return p_pass / len(allocs), e_groups / len(allocs)


def chain_cover(chains, k):
    vals = [(float(any(l is not None for l in ch[:k])), float(len({l for l in ch[:k] if l not in (None, NOFP)})))
            for ch in chains]
    if not vals:
        return 0.0, 0.0
    return float(np.mean([v[0] for v in vals])), float(np.mean([v[1] for v in vals]))


def _mi(x, y):
    """mutual information (nats) of two int-coded arrays; fast enough for permutation tests."""
    n = len(x)
    ny = int(y.max()) + 1
    joint = np.bincount(x * ny + y, minlength=(int(x.max()) + 1) * ny).reshape(-1, ny) / n
    px, py = joint.sum(1, keepdims=True), joint.sum(0, keepdims=True)
    nz = joint > 0
    return float((joint[nz] * np.log(joint[nz] / (px @ py)[nz])).sum())


def rarefied_groups(labels, m):
    labels = [l for l in labels if l not in (None, NOFP)]
    n = len(labels)
    if n == 0 or m <= 0:
        return 0.0
    m = min(m, n)
    return sum(1 - math.comb(n - g, m) / math.comb(n, m) for g in Counter(labels).values())


def _tau_clusters(fps, tau):
    """complete-linkage clusters (d_phi <= tau) of ONE population of fingerprints."""
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    out = [None] * len(fps)
    keys = {}
    for i, f in enumerate(fps):
        if f and f.get("ok"):
            keys.setdefault(FP.full_key(f) + "|" + str(f.get("b")), []).append(i)
    if not keys:
        return out
    reps = [v[0] for v in keys.values()]
    if len(reps) == 1:
        lab = [1]
    else:
        D = np.zeros((len(reps), len(reps)))
        for a in range(len(reps)):
            for b in range(a + 1, len(reps)):
                D[a, b] = D[b, a] = FP.d_phi(fps[reps[a]], fps[reps[b]])
        lab = fcluster(linkage(squareform(D, checks=False), "complete"), t=tau, criterion="distance")
    for members, l in zip(keys.values(), lab):
        for i in members:
            out[i] = f"c{l}"
    return out


# ------------------------------------------------------------------ main
def run(tasks):
    tmap = {t["id"]: t for t in tasks}
    rows = [r for r in committed_generations() if r["task"] in tmap]
    if not rows:
        raise SystemExit("no finished generations found")
    log(f"analysis: {len(rows)} generated samples ({sum(1 for r in rows if r.get('skipped'))} skipped prompts "
        f"counted as incorrect); backends: {dict(Counter(r.get('backend', '?') for r in rows))}")
    res = evaluate([(tmap[r["task"]], r["code"]) for r in rows], desc="eval-generations")
    for r, v in zip(rows, res):
        r["correct"] = bool(v["correct"])
    log(f"  overall correctness: {np.mean([r['correct'] for r in rows]):.3f}")

    human = [{"model": "human", "cond": "human", "task": t["id"], "code": c, "correct": True, "sample": i}
             for t in tasks for i, c in enumerate(t.get("human", []))]
    corr = [r for r in rows if r["correct"]] + human
    fl = fingerprints([(tmap[r["task"]], r["code"]) for r in corr], desc="fingerprint-solutions")
    for r, f in zip(corr, fl):
        r["fpall"] = f
    # ONE measurement ladder per task, chosen from the validated reference solutions
    # (independent of the model samples); fall back to the pool only if no reference is measurable
    ref_items = [(tmap[tid], c) for tid, t in tmap.items() for c in t.get("ref", [])]
    ref_fps = fingerprints(ref_items, desc="fingerprint-references") if ref_items else []
    ref_by = defaultdict(list)
    for (t, _), f in zip(ref_items, ref_fps):
        ref_by[t["id"]].append(f)
    pool_by = defaultdict(list)
    for r in corr:
        pool_by[r["task"]].append(r["fpall"])
    ladder = {tid: (FP.select_ladder(ref_by[tid]) or FP.select_ladder(pool_by[tid])) for tid in tmap}
    for r in corr:
        r["fp"] = FP.pick(r["fpall"], ladder[r["task"]])
        r["lab"] = {L: (FP.level_key(r["fp"], L) or NOFP) for L in ("L1", "L2", "L3", "phi")}
    for r in rows:
        if not r["correct"]:
            r["lab"] = None
    tau = (read_json(C.RESULTS_DIR / "partA_threshold.json", {}) or {}).get("tau_d_phi", 0.25)

    main = model_tag(C.MAIN_MODEL)
    extra = [model_tag(m) for m in C.EXTRA_MODELS]
    G = defaultdict(lambda: defaultdict(list))  # task -> pool name -> rows
    for r in rows:
        if r["model"] == main and r["cond"] == "plain":
            G[r["task"]]["plain"].append(r)
        elif r["model"] == main and r["cond"].startswith("plain_T"):
            G[r["task"]][r["cond"]].append(r)
        elif r["model"] == main and r["cond"] == "strategy":
            G[r["task"]][f"s{r['strategy']}"].append(r)
        elif r["model"] == main and r["cond"] == "differently":
            G[r["task"]][f"chain{r['chain']}"].append(r)
        elif r["cond"] == "plain":
            G[r["task"]][f"m:{r['model']}"].append(r)
    for r in human:
        G[r["task"]]["human"].append(r)
    for tid in G:
        for k in G[tid]:
            G[tid][k].sort(key=lambda r: (r.get("round", 0), r.get("sample", 0)))

    strat_names = [f"s{s}" for s in range(1, C.N_STRATEGIES + 1)]
    conds = {f"plain ({main})": ("strata", lambda tid: [G[tid]["plain"]])}
    for T in C.EXTRA_TEMPS:
        conds[f"plain ({main}, T={T})"] = ("strata", lambda tid, T=T: [G[tid][f"plain_T{T}"]])
    conds.update({
             "Strategy 1..4 prompts (round robin)": ("strata", lambda tid: [G[tid][s] for s in strat_names]),
             "solve differently (sequential)": ("chain", lambda tid: [G[tid][f"chain{c}"] for c in range(C.N_CHAINS)])})
    for e in extra:  # every pairwise union with the main model (a weak partner hides complementarity)
        conds[f"union {main}+{e}"] = ("strata", lambda tid, e=e: [G[tid]["plain"], G[tid][f"m:{e}"]])
    if len(extra) >= 2:
        conds["union of 3 models"] = ("strata", lambda tid: [G[tid]["plain"]] + [G[tid][f"m:{e}"] for e in extra[:2]])
    for e in extra:
        conds[f"plain ({e})"] = ("strata", lambda tid, e=e: [G[tid][f"m:{e}"]])
    base = f"plain ({main})"
    # a condition whose pools are missing (e.g. a model that was not generated) is dropped, never
    # silently degraded into a different policy (a "union" without one of its models)
    for name in list(conds):
        if not all(len(p) > 0 for tid in tmap for p in conds[name][1](tid)):
            log(f"  WARNING: condition '{name}' has missing sample pools -> excluded from parts B/C")
            del conds[name]
    if base not in conds:
        raise SystemExit("plain samples of the main model are missing")

    # d_phi <= tau clusters are computed inside each condition's OWN population, so adding other
    # conditions can never change a condition's numbers
    tau_lab = {}  # (cond, id(row)) -> cluster

    def cluster_population(name, rs):
        cl = _tau_clusters([r["fp"] if r["lab"] else None for r in rs], tau)
        for r, c in zip(rs, cl):
            if r["lab"]:
                tau_lab[(name, id(r))] = c or NOFP

    for tid in tmap:
        for name, (_, f) in conds.items():
            cluster_population(name, [r for p in f(tid) for r in p])
        cluster_population("human", G[tid]["human"])

    def labs(rs, L, cond):
        if L == "phi_tau":
            return [tau_lab.get((cond, id(r))) if r["lab"] else None for r in rs]
        return [r["lab"][L] if r["lab"] else None for r in rs]

    # trivial tasks: every measurable reference solution is a constant-time, non-recursive
    # computation on the task's ladder (a formula, no choice of algorithm) -> reported separately
    trivial = {}
    for tid in tmap:
        refs = [FP.pick(f, ladder[tid]) for f in ref_by[tid]]
        refs = [f for f in refs if f.get("ok")]
        trivial[tid] = bool(refs) and all(f["cls"] == "O(1)" and f["rec"] == "none" for f in refs)
    subsets = {"all": list(tmap), "nontrivial": [t for t in tmap if not trivial[t]]}
    log(f"  trivial tasks (reference is O(1) formula): {sum(trivial.values())}/{len(tmap)}")

    def summarize(task_ids):
        # ================= Part B
        partB = {"tau": tau, "levels": {}, "seed": {}, "seed_correctness": {}, "human": {}, "coverage": {}}
        for name, (_, f) in list(conds.items()) + [("human", ("strata", lambda tid: [G[tid]["human"]]))]:
            c = [r for tid in task_ids for p in f(tid) for r in p if r["lab"]]
            partB["coverage"][name] = {"correct": len(c), "fingerprinted": sum(1 for r in c if r["lab"]["phi"] != NOFP)}
        for L in LEVELS:
            ng, pools_l = [], []
            for tid in task_ids:
                ls = [l for l in labs(G[tid]["plain"], L, base) if l not in (None, NOFP)]
                if ls:
                    ng.append(len(set(ls)))
                    pools_l.append(ls)
            # a task with ONE fingerprinted correct solution is trivially "one group": homogeneity is
            # only meaningful for tasks with >= m solutions, rarefied to exactly m so tasks are comparable
            at_least = {}
            for m in MIN_CORRECT:
                sel = [ls for ls in pools_l if len(ls) >= m]
                at_least[str(m)] = {
                    "n_tasks": len(sel),
                    "frac_single_group": float(np.mean([len(set(ls)) == 1 for ls in sel])) if sel else None,
                    "mean_groups_rarefied": float(np.mean([rarefied_groups(ls, m) for ls in sel])) if sel else None}
            partB["levels"][L] = {"n_tasks_with_fingerprinted_correct": len(ng),
                                  "mean_groups": float(np.mean(ng)) if ng else 0,
                                  "frac_single_group": float(np.mean([g == 1 for g in ng])) if ng else 0,
                                  "hist": dict(Counter(ng)), "at_least": at_least}
        partB["plain_pass_rate"] = float(np.mean([r["correct"] for tid in task_ids for r in G[tid]["plain"]] or [0]))
        partB["tasks_solved_any_plain"] = int(sum(any(r["correct"] for r in G[tid]["plain"]) for tid in task_ids))

        # model vs human (APPS): rarefied to the same number of fingerprinted correct solutions per task
        for L in LEVELS:
            mv, hv = [], []
            for tid in task_ids:
                hl = [l for l in labs(G[tid]["human"], L, "human") if l not in (None, NOFP)]
                ml = [l for l in labs(G[tid]["plain"], L, base) if l not in (None, NOFP)]
                m = min(len(hl), len(ml))
                if m >= 2:
                    mv.append(rarefied_groups(ml, m))
                    hv.append(rarefied_groups(hl, m))
            partB["human"][L] = {"n_tasks": len(mv), "model_mean": float(np.mean(mv)) if mv else None,
                                 "human_mean": float(np.mean(hv)) if hv else None}

        # seed dependence. (1) Is the fingerprint group associated with "Strategy s" among correct
        # solutions? (2) Is correctness associated with s? Permutation of s within each task.
        from sklearn.metrics import adjusted_mutual_info_score
        rng = np.random.default_rng(0)
        NP = 1000
        for L in LEVELS:
            obs_sum, null_sums, amis, pvals, n_used = 0.0, np.zeros(NP), [], [], 0
            for tid in task_ids:
                ss, ll = [], []
                for si, sn in enumerate(strat_names):
                    for r, l in zip(G[tid][sn], labs(G[tid][sn], L, "Strategy 1..4 prompts (round robin)")):
                        if l not in (None, NOFP):
                            ss.append(si)
                            ll.append(l)
                if len(ss) < 4 or len(set(ss)) < 2 or len(set(ll)) < 2:
                    continue
                n_used += 1
                ss_arr = np.array(ss)
                ll_arr = np.unique(np.array(ll), return_inverse=True)[1]
                mi = _mi(ss_arr, ll_arr)
                obs_sum += mi
                amis.append(adjusted_mutual_info_score(ss, ll))
                null = np.array([_mi(rng.permutation(ss_arr), ll_arr) for _ in range(NP)])
                null_sums += null
                pvals.append((1 + np.sum(null >= mi - 1e-12)) / (NP + 1))
            partB["seed"][L] = {"n_tasks": n_used, "mean_AMI": float(np.mean(amis)) if amis else None,
                                "frac_tasks_p<0.05": float(np.mean(np.array(pvals) < 0.05)) if pvals else None,
                                "global_p": float((1 + np.sum(null_sums >= obs_sum - 1e-12)) / (NP + 1)) if n_used else None}
        obs, nulls, n_used = 0.0, np.zeros(NP), 0
        for tid in task_ids:
            ss = np.array([si for si, sn in enumerate(strat_names) for _ in G[tid][sn]])
            cc = np.array([int(r["correct"]) for sn in strat_names for r in G[tid][sn]])
            if len(ss) < 4 or len(set(cc)) < 2:
                continue
            n_used += 1
            obs += _mi(ss, cc)
            nulls += np.array([_mi(rng.permutation(ss), cc) for _ in range(NP)])
        partB["seed_correctness"] = {"n_tasks": n_used, "global_p": float((1 + np.sum(nulls >= obs - 1e-12)) / (NP + 1))
                                     if n_used else None}
        partB["strategy_pass_rate"] = {sn: float(np.mean([r["correct"] for tid in task_ids for r in G[tid][sn]] or [0]))
                                       for sn in strat_names}

        # ================= Part C
        partC = {"ks": C.KS, "conds": {}, "pool_sizes": {}, "truncated": {}}
        per_task = {}
        for name, (kind, f) in conds.items():
            sizes = [sum(len(p) for p in f(tid)) for tid in task_ids]
            partC["pool_sizes"][name] = {"min": int(min(sizes)), "max": int(max(sizes))}
            pool = [r for tid in task_ids for p in f(tid) for r in p]
            partC["truncated"][name] = float(np.mean([bool(r.get("truncated")) for r in pool])) if pool else 0.0
            if max(sizes) == 0:
                log(f"  WARNING: condition '{name}' has no samples")
            partC["conds"][name] = {}
            for L in LEVELS:
                P, E = [], []
                for tid in task_ids:
                    pools = f(tid)
                    pk, ek = [], []
                    for k in C.KS:
                        if kind == "strata":
                            a, b = expected_cover([labs(p, L, name) for p in pools], k)
                        else:
                            a, b = chain_cover([labs(p, L, name) for p in pools if p], k)
                        pk.append(a)
                        ek.append(b)
                    P.append(pk)
                    E.append(ek)
                P, E = np.array(P), np.array(E)
                per_task[(name, L)] = (P, E)
                partC["conds"][name][L] = {"pass@k": P.mean(0).tolist(), "groups@k": E.mean(0).tolist()}
        partC["gain_vs_plain"] = {}
        for name in conds:
            if name == base:
                continue
            out = {}
            for j, metric in enumerate(["pass@k", "groups@k"]):
                d = per_task[(name, "phi")][j] - per_task[(base, "phi")][j]
                boots = np.array([d[rng.integers(0, len(d), len(d))].mean(0) for _ in range(1000)])
                lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
                out[metric] = {"mean": d.mean(0).tolist(), "ci_lo": lo.tolist(), "ci_hi": hi.tolist()}
            partC["gain_vs_plain"][name] = out

        # diversity at an EQUAL number of correct solutions. groups@k counts groups among correct
        # samples, so a condition that lowers correctness loses groups mechanically. Here both the
        # condition and plain sampling are rarefied to m = min(#fingerprinted correct) per task.
        def fp_labels(name, tid, L):
            return [l for p in conds[name][1](tid) for l in labs(p, L, name) if l not in (None, NOFP)]

        partC["groups_equal_correct"] = {}
        for name in conds:
            if name == base:
                continue
            partC["groups_equal_correct"][name] = {}
            for L in LEVELS:
                cv, bv = [], []
                for tid in task_ids:
                    cl, bl = fp_labels(name, tid, L), fp_labels(base, tid, L)
                    m = min(len(cl), len(bl))
                    if m >= 2:
                        cv.append(rarefied_groups(cl, m))
                        bv.append(rarefied_groups(bl, m))
                d = np.array(cv) - np.array(bv)
                if len(d):
                    boots = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(1000)]
                    lo, hi = np.percentile(boots, [2.5, 97.5])
                partC["groups_equal_correct"][name][L] = {
                    "n_tasks": len(d), "cond_mean": float(np.mean(cv)) if cv else None,
                    "plain_mean": float(np.mean(bv)) if bv else None,
                    "diff": float(d.mean()) if len(d) else None,
                    "ci_lo": float(lo) if len(d) else None, "ci_hi": float(hi) if len(d) else None}

        # headroom inside the model's own distribution: "Strategy s" is not associated with the
        # outcome (part B), so plain + Strategy samples are pooled into one large i.i.d.-like pool.
        # If pass@k keeps growing far beyond k=16, there is correct mass that better exploration
        # could reach with a small budget.
        strat_cond = "Strategy 1..4 prompts (round robin)"
        if strat_cond in conds:
            def pooled(tid):
                return ([l for l in labs(G[tid]["plain"], "phi", base)] +
                        [l for sn in strat_names for l in labs(G[tid][sn], "phi", strat_cond)])

            n_pool = min(len(pooled(tid)) for tid in task_ids)
            ks = sorted({k for k in (1, 2, 4, 8, 16, 32, 64, 128) if k < n_pool} | {n_pool})
            cur = np.array([[expected_cover([pooled(tid)[:n_pool]], k) for k in ks] for tid in task_ids])
            n_corr = np.array([sum(l is not None for l in pooled(tid)[:n_pool]) for tid in task_ids])
            partC["pooled_curve"] = {
                "pool_size": int(n_pool), "ks": ks, "pass@k": cur[:, :, 0].mean(0).tolist(),
                "groups@k": cur[:, :, 1].mean(0).tolist(),
                # tasks the model can solve but rarely does: the target of diversity / exploration
                "tasks_solved_in_pool": int((n_corr > 0).sum()),
                "tasks_rare_1_to_3_correct": int(((n_corr > 0) & (n_corr <= 3)).sum()),
                "n_tasks": len(task_ids)}
        return partB, partC

    results = {name: summarize(ids) for name, ids in subsets.items() if ids}
    partB = {k: v[0] for k, v in results.items()}
    partC = {k: v[1] for k, v in results.items()}
    for k in partB:
        partB[k]["n_tasks"] = len(subsets[k])
    partB["trivial_tasks"] = sorted(t for t, v in trivial.items() if v)
    write_json(C.RESULTS_DIR / "partB.json", partB)
    write_json(C.RESULTS_DIR / "partC.json", partC)

    sub = "nontrivial" if "nontrivial" in partC else "all"
    _plots(partB[sub], partC[sub], sub)
    from .part_a import make_labeling_sheet
    make_labeling_sheet(tasks, {tid: [r["code"] for r in G[tid]["plain"] + G[tid]["s1"] if r["correct"]]
                                for tid in tmap})
    return partB, partC


def _plots(partB, partC, subset):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, len(LEVELS), figsize=(3.2 * len(LEVELS), 3.2), sharey=True)
    for ax, L in zip(axes, LEVELS):
        h = {int(k): v for k, v in partB["levels"][L]["hist"].items()}
        if h:
            xs = list(range(1, max(h) + 1))
            ax.bar(xs, [h.get(x, 0) for x in xs], color="#4C72B0")
        ax.set_title(LEVEL_NAMES[L], fontsize=9)
        ax.set_xlabel("# fingerprint groups among correct\n(of %d samples)" % C.N_SAMPLES, fontsize=8)
    axes[0].set_ylabel("# tasks")
    fig.suptitle(f"Part B: fingerprint groups per task ({subset} tasks). Groups are NOT algorithms "
                 f"(see grouping precision/recall in part A); compare distributions, not absolute counts",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(C.FIG_DIR / "partB_hist.png", dpi=150)
    plt.close(fig)
    for metric, fname, ylabel in [("pass@k", "partC_passk.png", "pass@k"),
                                  ("groups@k", "partC_groups.png", "E[# distinct correct fingerprint groups] (phi key)")]:
        fig, ax = plt.subplots(figsize=(6.4, 4.6))
        for name, d in partC["conds"].items():
            ax.plot(partC["ks"], d["phi"][metric], marker="o", label=name,
                    lw=2.4 if name.startswith("plain (") and name == list(partC["conds"])[0] else 1.5)
        ax.set_xscale("log", base=2)
        ax.set_xticks(partC["ks"])
        ax.set_xticklabels([str(k) for k in partC["ks"]])
        ax.set_xlabel("k (samples budget)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
        ax.set_title(f"Part C: plain sampling vs forced diversity, {metric} ({subset} tasks)", fontsize=10)
        fig.tight_layout()
        fig.savefig(C.FIG_DIR / fname, dpi=150)
        plt.close(fig)
