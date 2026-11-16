"""Part A: does the execution fingerprint separate algorithms better than JPlag and embeddings?"""
from __future__ import annotations

import json
import random

import numpy as np

from . import baselines as BL
from . import graphs as GR
from . import config as C
from . import curated, pacd
from . import fingerprint as FP
from .fpstore import evaluate, fingerprints
from .utils import log, read_jsonl, write_json

DIVALGO_BAR = 0.73
LABELS = C.DATA_DIR / "labels" / "manual_pairs.jsonl"
# labelled pair sets: dataset name -> file (manual = pairs of model solutions, human = pairs of APPS human solutions)
LABEL_SETS = {"manual": LABELS, "human": C.DATA_DIR / "labels" / "human_pairs.jsonl"}


def _verify_curated(tasks, progs):
    """All programs of a curated task must agree with program #0 on the test inputs.
    Programs that fail are EXCLUDED from the benchmark (and reported)."""
    by = {}
    for p in progs:
        by.setdefault(p["task"], []).append(p)
    items = []
    for t in tasks:
        ref = by[t["id"]][0]["code"]
        g = {}
        exec(compile(ref, "<ref>", "exec"), g)  # our own trusted reference code
        t["tests"] = [{"type": "call", "args": a, "expected": repr(g["solve"](*eval(a)))} for a in t["test_args"]]
        items += [(t, p) for p in by[t["id"]]]
    res = evaluate([(t, p["code"]) for t, p in items], desc="curated-verify")
    bad = [p["pid"] for (t, p), r in zip(items, res) if not r["correct"]]
    if bad:
        log(f"WARNING: {len(bad)} curated programs fail their own tests and are excluded: {bad[:10]}")
    return [p for p in progs if p["pid"] not in set(bad)]


def _manual(name="manual"):
    from .data import tasks_path
    rows = [r for r in read_jsonl(LABEL_SETS[name]) if r.get("same") in (0, 1, "0", "1")]
    if not rows:
        return [], [], []
    tasks = {t["id"]: t for t in read_jsonl(tasks_path())}
    progs, pairs, used = [], [], {}
    for i, r in enumerate(rows):
        if r["task"] not in tasks:
            continue
        used[r["task"]] = tasks[r["task"]]
        pa, pb = f"{name}/{i}/a", f"{name}/{i}/b"
        progs += [{"pid": pa, "task": r["task"], "code": r["a"]}, {"pid": pb, "task": r["task"], "code": r["b"]}]
        pairs.append({"a": pa, "b": pb, "task": r["task"], "same": int(r["same"]), "dataset": name})
    log(f"{name} labels: {len(pairs)} labelled pairs")
    return list(used.values()), progs, pairs


def family(task_id):
    """Problem family used for grouping in the bootstrap and for leave-one-family-out CV:
    curated/sort and pacd/sort/<variant> are the same family."""
    parts = task_id.split("/")
    if parts[0] in ("curated", "pacd"):
        return parts[1]
    return task_id


def auc_with_ci(y_diff, score, groups, n_boot=1000, seed=0):
    from sklearn.metrics import roc_auc_score
    y, s, g = np.asarray(y_diff), np.asarray(score, dtype=float), np.asarray(groups)
    if len(y) == 0 or len(set(y)) < 2:
        return float("nan"), float("nan"), float("nan")
    auc = roc_auc_score(y, s)
    rng = np.random.default_rng(seed)
    ug = np.unique(g)
    idx_by = {u: np.where(g == u)[0] for u in ug}
    boots = []
    for _ in range(n_boot):
        pick = rng.choice(ug, size=len(ug), replace=True)
        idx = np.concatenate([idx_by[u] for u in pick])
        if len(set(y[idx])) == 2:
            boots.append(roc_auc_score(y[idx], s[idx]))
    lo, hi = (np.percentile(boots, [2.5, 97.5]) if boots else (float("nan"), float("nan")))
    return float(auc), float(lo), float(hi)


def _learned_scores(pairs, fps):
    """Logistic regression on phi pair-features, leave-one-FAMILY-out -> out-of-fold scores."""
    from sklearn.linear_model import LogisticRegression
    X = [FP.pair_features(fps[p["a"]], fps[p["b"]]) for p in pairs]
    fam = [family(p["task"]) for p in pairs]
    out = np.full(len(pairs), np.nan)
    for f in sorted(set(fam)):
        tr = [i for i in range(len(pairs)) if fam[i] != f and X[i] is not None]
        te = [i for i in range(len(pairs)) if fam[i] == f and X[i] is not None]
        ytr = [1 - pairs[i]["same"] for i in tr]
        if not te or len(set(ytr)) < 2:
            continue
        m = LogisticRegression(max_iter=1000, C=1.0).fit([X[i] for i in tr], ytr)
        out[te] = m.predict_proba([X[i] for i in te])[:, 1]
    return out


def youden_threshold(y_diff, score):
    """Threshold for 'same group if d <= tau': midway between the Youden-optimal ROC threshold
    (where d >= th means different) and the next smaller observed distance, so ties are not split."""
    from sklearn.metrics import roc_curve
    fpr, tpr, th = roc_curve(y_diff, score)
    k = int(np.argmax(tpr - fpr))
    t = float(th[k])
    below = np.asarray(score)[np.asarray(score) < t]
    return float((t + below.max()) / 2) if len(below) else t - 1e-9


def grouping_quality(pairs, same_pred):
    """Pairwise precision / recall / F1 of 'same group' predictions against 'same algorithm' labels."""
    y = np.array([p["same"] for p in pairs], bool)
    pr = np.array(same_pred, bool)
    tp = int((y & pr).sum())
    prec = tp / max(1, int(pr.sum()))
    rec = tp / max(1, int(y.sum()))
    return {"precision": prec, "recall": rec, "f1": 2 * prec * rec / max(1e-9, prec + rec), "n_pairs": len(pairs)}


def run():
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    tasks, progs = curated.build(seed=C.SEED)
    progs = _verify_curated(tasks, progs)
    pairs = curated.pairs(progs)
    log(f"curated: {len(tasks)} tasks, {len(progs)} programs, {len(pairs)} pairs "
        f"({sum(p['same'] for p in pairs)} same-algorithm)")
    t2, p2, pr2 = pacd.build()
    tasks, progs, pairs = tasks + t2, progs + p2, pairs + pr2
    seen_t = {t["id"] for t in tasks}
    for name in LABEL_SETS:
        t3, p3, pr3 = _manual(name)
        tasks += [t for t in t3 if t["id"] not in seen_t]
        seen_t |= {t["id"] for t in t3}
        progs, pairs = progs + p3, pairs + pr3
    tmap = {t["id"]: t for t in tasks}
    code = {p["pid"]: p["code"] for p in progs}
    pgroup = {p["pid"]: p.get("group", p["task"]) for p in progs}

    # ---- phi: ONE ladder per comparison group (chosen from all its programs, independent of labels)
    fall = fingerprints([(tmap[p["task"]], p["code"]) for p in progs], desc="partA-fingerprint")
    by_group = {}
    for p, fa in zip(progs, fall):
        by_group.setdefault(pgroup[p["pid"]], []).append(fa)
    lad = {g: FP.select_ladder(v) for g, v in by_group.items()}
    fps = {p["pid"]: FP.pick(fa, lad[pgroup[p["pid"]]]) for p, fa in zip(progs, fall)}
    nbad = sum(1 for f in fps.values() if not f.get("ok"))
    log(f"  fingerprint coverage: {len(fps) - nbad}/{len(fps)} programs")

    # repeatability: measure our labelled programs a second time, independently
    cur = [p for p in progs if p["task"].startswith("curated/")]
    f2 = fingerprints([(tmap[p["task"]], p["code"]) for p in cur], desc="partA-repeat", rep=1)
    flips, db = 0, []
    for p, fa in zip(cur, f2):
        a, b = fps[p["pid"]], FP.pick(fa, lad[pgroup[p["pid"]]])
        if a.get("ok") and b.get("ok"):
            flips += a["k1"] != b["k1"]
            db.append(abs(a["b"] - b["b"]))
    repeat = {"programs": len(db), "L1_class_flips": int(flips), "flip_rate": flips / max(1, len(db)),
              "median_abs_delta_b": float(np.median(db)) if db else None,
              "max_abs_delta_b": float(np.max(db)) if db else None, "fp_workers": C.FP_WORKERS}
    log(f"  repeatability: {flips}/{len(db)} programs changed L1 class on re-measurement")

    # ---- metrics per pair
    M = {k: np.full(len(pairs), np.nan) for k in ["d_phi", "d_phi equal weights", "d_phi:L1", "d_phi:L2", "d_phi:L3",
                                                   "d_phi learned (leave-family-out)",
                                                   "JPlag", "difflib tokens", "AST bag",
                                                   "AST WL", "CFG WL", "PDG WL"]}
    for i, pr in enumerate(pairs):
        a, b = fps[pr["a"]], fps[pr["b"]]
        if a.get("ok") and b.get("ok"):
            M["d_phi"][i] = FP.d_phi(a, b)
            M["d_phi equal weights"][i] = FP.d_phi(a, b, w=(1, 1, 1))
            M["d_phi:L1"][i] = FP.d1(a, b)
            M["d_phi:L2"][i] = FP.d2(a, b)
            M["d_phi:L3"][i] = FP.d3(a, b)
        M["difflib tokens"][i] = BL.d_difflib(code[pr["a"]], code[pr["b"]])
        M["AST bag"][i] = BL.d_ast(code[pr["a"]], code[pr["b"]])
        for k, v in GR.distances(code[pr["a"]], code[pr["b"]]).items():  # AST / CFG / PDG + WL kernel
            M[k][i] = v
    M["d_phi learned (leave-family-out)"] = _learned_scores(pairs, fps)

    # JPlag: one run per comparison group; a failed run leaves its pairs MISSING (never distance 1)
    from .setup_tools import find_java, jplag_jar
    if not (find_java() and jplag_jar().exists()):
        from . import setup_tools
        setup_tools.main()  # download JRE / JPlag if the tools stage was skipped
    groups = {}
    for p in progs:
        groups.setdefault(pgroup[p["pid"]], []).append(p)
    jsims, jfail = {}, []
    for g, ps in groups.items():
        s = BL.jplag_group([(p["pid"], p["code"]) for p in ps], C.TMP_DIR / "jplag" / g.replace("/", "_"))
        if s is None:
            jfail.append(g)
        else:
            jsims.update(s)
    cover = 0
    for i, pr in enumerate(pairs):
        s = jsims.get((pr["a"], pr["b"]))
        if s is not None:
            M["JPlag"][i] = 1.0 - s
            cover += 1
    log(f"  JPlag coverage: {cover}/{len(pairs)} pairs" + (f"; failed groups: {jfail[:5]}" if jfail else ""))
    if cover == 0:
        del M["JPlag"]

    # embeddings
    pids = [p["pid"] for p in progs]
    for repo in C.EMBED_MODELS:
        try:
            V = BL.embeddings(repo, [code[p] for p in pids])
        except SystemExit as e:
            log(f"embedding model {repo} skipped: {e}")
            V = None
        if V is None:
            continue
        vi = {p: V[k] for k, p in enumerate(pids)}
        M[f"emb:{repo.split('/')[-1]}"] = np.array([BL.d_cos(vi[pr["a"]], vi[pr["b"]]) for pr in pairs])

    # ---- AUC table on the SAME pairs for all metrics
    y = np.array([1 - p["same"] for p in pairs])
    ds = np.array([p["dataset"] for p in pairs])
    fam = np.array([family(p["task"]) for p in pairs])
    rows = []
    for dname in ["ours", "pacd", "manual", "human", "all"]:
        sel = np.ones(len(pairs), bool) if dname == "all" else ds == dname
        if sel.sum() == 0:
            continue
        common = sel.copy()
        for k, v in M.items():
            common &= ~np.isnan(v)
        for k, v in M.items():
            auc, lo, hi = auc_with_ci(y[common], v[common], fam[common])
            rows.append({"dataset": dname, "metric": k, "auc": auc, "ci_lo": lo, "ci_hi": hi,
                         "n_pairs": int(common.sum()), "n_pairs_in_dataset": int(sel.sum()),
                         "n_diff": int(y[common].sum()), "beats_divalgo_0.73": bool(auc > DIVALGO_BAR)})
    write_json(C.RESULTS_DIR / "partA_auc.json", rows)

    sel = (ds == "ours") & ~np.isnan(M["d_phi"])
    tau = youden_threshold(y[sel], M["d_phi"][sel]) if sel.sum() else 0.3
    # how well do the GROUPINGS used in Part B recover algorithm labels? (pairwise P/R/F1)
    ok = [i for i, pr in enumerate(pairs) if fps[pr["a"]].get("ok") and fps[pr["b"]].get("ok")]
    gq = {}
    for name, pred in [("phi exact key", lambda a, b: FP.full_key(a) == FP.full_key(b)),
                       ("L1 key", lambda a, b: a["k1"] == b["k1"]),
                       ("d_phi <= tau", lambda a, b: FP.d_phi(a, b) <= tau)]:
        for dname in ["ours", "pacd", "manual", "human"]:
            idx = [i for i in ok if pairs[i]["dataset"] == dname]
            if idx:
                gq[f"{name} [{dname}]"] = grouping_quality([pairs[i] for i in idx],
                                                           [pred(fps[pairs[i]["a"]], fps[pairs[i]["b"]]) for i in idx])
    status = {"pacd_pairs": int((ds == "pacd").sum()), "manual_pairs": int((ds == "manual").sum()),
              "human_pairs": int((ds == "human").sum()),
              "complete": bool((ds == "manual").sum() >= 100)}
    if not status["complete"]:
        log("  !!! Part A is NOT complete: the manually labelled pairs of model solutions are missing "
            "(required). Label data/labels/manual_pairs_todo.jsonl after the analysis stage.")
    write_json(C.RESULTS_DIR / "partA_threshold.json", {"tau_d_phi": tau, "grouping_quality": gq,
                                                         "repeatability": repeat, "status": status,
                                                         "weights": list(C.W_PHI)})
    dump = []
    for i, pr in enumerate(pairs):
        d = dict(pr)
        d.update({k: (None if np.isnan(v[i]) else float(v[i])) for k, v in M.items()})
        d["phi_a"], d["phi_b"] = FP.full_key(fps[pr["a"]]), FP.full_key(fps[pr["b"]])
        dump.append(d)
    write_json(C.RESULTS_DIR / "partA_pairs.json", dump)
    write_json(C.RESULTS_DIR / "partA_fingerprints.json",
               {p["pid"]: {"algo": p.get("algo"), **{k: fps[p["pid"]].get(k) for k in
                                                     ("ok", "reason", "ladder", "k1", "k2", "k3", "b", "b_lines", "b_time")}}
                for p in progs})
    _plot_roc(y, M, ds)
    for r in rows:
        if r["dataset"] in ("ours", "all"):
            log(f"  AUC[{r['dataset']}] {r['metric']:<34} {r['auc']:.3f} [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}] n={r['n_pairs']}")
    log(f"  d_phi clustering threshold (Youden, ours): {tau:.3f}")
    for k, v in gq.items():
        log(f"  grouping {k}: P={v['precision']:.2f} R={v['recall']:.2f} F1={v['f1']:.2f}")
    return rows


def _plot_roc(y, M, ds):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve
    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    sel = ds == "ours"
    fig, ax = plt.subplots(figsize=(6, 5.5))
    for k, v in M.items():
        m = sel & ~np.isnan(v)
        if m.sum() < 5 or len(set(y[m])) < 2:
            continue
        fpr, tpr, _ = roc_curve(y[m], v[m])
        ax.plot(fpr, tpr, lw=2.4 if k == "d_phi" else 1.2, label=k)
    ax.plot([0, 1], [0, 1], ls=":", c="gray", lw=1)
    ax.set_xlabel("false positive rate")
    ax.set_ylabel("true positive rate")
    ax.set_title("Part A: 'different algorithm' detection (our labelled pairs)")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(C.FIG_DIR / "partA_roc.png", dpi=150)
    plt.close(fig)


def _norm_code(c):
    return "\n".join(l.rstrip() for l in c.strip().splitlines() if l.strip())


def make_labeling_sheet(tasks, rows_by_task, n_pairs=200, seed=0):
    """Writes data/labels/manual_pairs_todo.jsonl (+ .md): pairs of *correct* model solutions of
    the same task, sampled uniformly among non-identical pairs (selection does not use any of the
    evaluated metrics). Fill `same` with 1/0, save as data/labels/manual_pairs.jsonl and run
    `bash run.sh partA report`."""
    rng = random.Random(seed)
    tids = [t for t, cs in rows_by_task.items() if len({_norm_code(c) for c in cs}) >= 2]
    rng.shuffle(tids)
    cand = []
    for tid in tids * 3:  # up to 3 pairs per task, tasks in random order
        uniq = list({_norm_code(c): c for c in rows_by_task[tid]}.values())
        a, b = rng.sample(uniq, 2)
        if not any(r["task"] == tid and {r["a"], r["b"]} == {a, b} for r in cand):
            cand.append({"task": tid, "a": a, "b": b, "same": None})
        if len(cand) >= n_pairs:
            break
    out = C.DATA_DIR / "labels" / "manual_pairs_todo.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in cand:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out.with_suffix(".md"), "w", encoding="utf-8") as f:
        for i, r in enumerate(cand):
            f.write(f"## pair {i}  ({r['task']})\n\n```python\n{r['a']}```\n\n```python\n{r['b']}```\n\n")
    log(f"labeling sheet: {len(cand)} pairs -> {out}")
