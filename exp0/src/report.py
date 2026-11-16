"""Collects Part A/B/C results into results/report.md."""
from __future__ import annotations

from . import config as C
from .analysis import LEVEL_NAMES, LEVELS
from .utils import log, read_json


def _f(x, nd=3):
    return "–" if x is None or x != x else f"{x:.{nd}f}"


def _part_a(A, T):
    w = "/".join(f"{x:g}" for x in T.get("weights", C.W_PHI))
    st = T.get("status", {})
    out = ["## A. Does the fingerprint separate algorithms?", ""]
    if not st.get("complete"):
        out += ["> **Part A is NOT complete.** The required set of ~200 manually labelled pairs of *model* "
                "solutions is missing" + ("" if st.get("pacd_pairs") else ", and PACD is not connected") +
                ". Everything below rests on our own curated set, written by the same author as the "
                "fingerprint, made of textbook problems whose algorithms differ mostly in complexity — "
                "an optimistic setting. Label `data/labels/manual_pairs_todo.jsonl` and re-run "
                "`bash exp0/run.sh partA report`.", ""]
    out += [f"d_phi = weighted sum of level distances with weights **{w}** (scaling / scheme / primitives) "
            "fixed in advance; *d_phi equal weights* is shown only as a sensitivity check, *learned* is "
            "a leave-one-family-out logistic regression.",
            "AUC of the distance as a score for *different algorithm*. Within a dataset all metrics use exactly "
            "the same pairs. The real answer of part A is the comparison with JPlag and embeddings **on the "
            "same pairs**; the DivAlgo value 0.73 (C++, other pairs) is shown for reference only and is not "
            "directly comparable. 95% CI: bootstrap over problem families.", ""]
    # "all" mixes datasets with opposite class balance and is not shown (it stays in partA_auc.json)
    for ds in ["manual", "human", "pacd", "ours"]:
        rows = sorted([r for r in A if r["dataset"] == ds], key=lambda r: -(r["auc"] if r["auc"] == r["auc"] else -1))
        if not rows:
            continue
        out += [f"**dataset: {ds}** (pairs used: {rows[0]['n_pairs']} of {rows[0].get('n_pairs_in_dataset', '?')}, "
                f"different-algorithm: {rows[0]['n_diff']})", "",
                "| metric | AUC | 95% CI | DivAlgo ref. 0.73 (not comparable) |", "|---|---|---|---|"]
        for r in rows:
            out.append(f"| {r['metric']} | {_f(r['auc'])} | [{_f(r['ci_lo'])}, {_f(r['ci_hi'])}] | "
                       f"{'above' if r['beats_divalgo_0.73'] else 'below'} |")
        out.append("")
    if T.get("grouping_quality"):
        out += ["How well do the *groupings* used in parts B/C recover algorithm labels (pairwise: predicted "
                "'same group' vs labelled 'same algorithm'). Precision < 1 means one group can contain several "
                "algorithms, recall < 1 means one algorithm is split over several groups — so the number of "
                "groups is **not** the number of algorithms:", "",
                "| grouping [dataset] | precision | recall | F1 | pairs |", "|---|---|---|---|---|"]
        for k, v in T["grouping_quality"].items():
            out.append(f"| {k} | {_f(v['precision'], 2)} | {_f(v['recall'], 2)} | {_f(v['f1'], 2)} | {v['n_pairs']} |")
        out.append("")
    rp = T.get("repeatability")
    if rp:
        out += [f"Repeatability (curated programs measured twice, {rp['fp_workers']} parallel pinned jobs): "
                f"{rp['L1_class_flips']}/{rp['programs']} changed their L1 class; median |Δslope| = "
                f"{_f(rp['median_abs_delta_b'])}, max = {_f(rp['max_abs_delta_b'])}.", ""]
    out += ["![ROC](figures/partA_roc.png)", ""]
    return out


def _part_b(B, sub):
    out = [f"### B [{sub} tasks: {B.get('n_tasks', '?')}]", "",
           f"Plain sampling: {C.N_SAMPLES} samples/task, T={C.TEMPERATURE}, top_p={C.TOP_P}, top_k={C.TOP_K}. "
           f"Pass rate per sample = {_f(B['plain_pass_rate'])}; tasks with >=1 correct = {B['tasks_solved_any_plain']}.",
           "", "Fingerprint coverage (correct solutions with a usable fingerprint on the task's ladder): " +
           "; ".join(f"{k}: {v['fingerprinted']}/{v['correct']}" for k, v in B["coverage"].items()), "",
           "| level | tasks | mean # fingerprint groups among correct | share of tasks with 1 group |",
           "|---|---|---|---|"]
    for L in LEVELS:
        d = B["levels"][L]
        out.append(f"| {LEVEL_NAMES[L]} | {d['n_tasks_with_fingerprinted_correct']} | {_f(d['mean_groups'], 2)} | "
                   f"{_f(d['frac_single_group'], 2)} |")
    if all("at_least" in B["levels"][L] for L in LEVELS):
        ms = list(B["levels"][LEVELS[0]]["at_least"])
        out += ["", "The table above counts a task with ONE correct solution as 'one group', which inflates "
                "homogeneity. **Only tasks with at least m fingerprinted correct solutions, rarefied to exactly m** "
                "(this is the homogeneity number to quote):", "",
                "| level | " + " | ".join(f"tasks (≥{m}) | 1 group (≥{m}) | mean groups among {m}" for m in ms) + " |",
                "|---|" + "---|---|---|" * len(ms)]
        for L in LEVELS:
            a = B["levels"][L]["at_least"]
            out.append(f"| {LEVEL_NAMES[L]} | " + " | ".join(
                f"{a[m]['n_tasks']} | {_f(a[m]['frac_single_group'], 2)} | {_f(a[m]['mean_groups_rarefied'], 2)}"
                for m in ms) + " |")
    out += ["", "**Model vs human (APPS), rarefied to the same number of correct solutions per task** "
            "(a relative comparison — meaningful even though groups ≠ algorithms):", "",
            "| level | tasks | model | human |", "|---|---|---|---|"]
    for L, d in B["human"].items():
        out.append(f"| {LEVEL_NAMES[L]} | {d['n_tasks']} | {_f(d['model_mean'], 2)} | {_f(d['human_mean'], 2)} |")
    out += ["", "**Seed prefix «Strategy s»: association with the fingerprint group among correct solutions** "
            "(permutation test of s within each task; a large p means *no detected* association, "
            "not proof that the seed is ignored — see the number of tasks tested):", "",
            "| level | tasks tested | mean AMI | share of tasks p<0.05 | global permutation p |", "|---|---|---|---|---|"]
    for L in LEVELS:
        d = B["seed"][L]
        out.append(f"| {LEVEL_NAMES[L]} | {d['n_tasks']} | {_f(d['mean_AMI'])} | {_f(d['frac_tasks_p<0.05'], 2)} | "
                   f"{_f(d['global_p'], 4)} |")
    sc = B.get("seed_correctness", {})
    out += ["", f"Association of *correctness* with s: global permutation p = {_f(sc.get('global_p'), 4)} "
            f"over {sc.get('n_tasks', 0)} tasks. Pass rate per prefix: " +
            ", ".join(f"{k}: {_f(v)}" for k, v in B["strategy_pass_rate"].items()), ""]
    return out


def _part_c(Cc, sub):
    ks = Cc["ks"]
    out = [f"### C [{sub} tasks]", "",
           "| condition | " + " | ".join(f"pass@{k}" for k in ks) + " | " + " | ".join(f"#groups@{k}" for k in ks) + " |",
           "|---|" + "---|" * (2 * len(ks))]
    for name, d in Cc["conds"].items():
        out.append(f"| {name} | " + " | ".join(_f(v) for v in d["phi"]["pass@k"]) + " | " +
                   " | ".join(_f(v, 2) for v in d["phi"]["groups@k"]) + " |")
    for metric in ["pass@k", "groups@k"]:
        out += ["", f"Gain in {metric} over plain sampling at T={C.TEMPERATURE:g} (paired bootstrap 95% CI over tasks):", "",
                "| condition | " + " | ".join(f"Δ@{k}" for k in ks) + " |", "|---|" + "---|" * len(ks)]
        for name, g in Cc["gain_vs_plain"].items():
            g = g[metric]
            out.append(f"| {name} | " + " | ".join(f"{m:+.3f} [{lo:+.3f}, {hi:+.3f}]" for m, lo, hi in
                                                   zip(g["mean"], g["ci_lo"], g["ci_hi"])) + " |")
    ge = Cc.get("groups_equal_correct")
    if ge:
        out += ["", "**Diversity at an equal number of correct solutions.** #groups@k above counts groups among "
                "correct samples, so a condition that lowers correctness loses groups mechanically. Here the "
                "condition and plain sampling are both rarefied to the same number of fingerprinted correct "
                "solutions per task (tasks with ≥2 on both sides); Δ = condition − plain, paired bootstrap 95% CI:", "",
                "| condition | tasks | " + " | ".join(f"Δ {LEVEL_NAMES[L]}" for L in ("L1", "L2", "L3", "phi")) + " |",
                "|---|---|---|---|---|---|"]
        for name, d in ge.items():
            out.append(f"| {name} | {d['phi']['n_tasks']} | " + " | ".join(
                "–" if d[L]["diff"] is None else f"{d[L]['diff']:+.3f} [{d[L]['ci_lo']:+.3f}, {d[L]['ci_hi']:+.3f}]"
                for L in ("L1", "L2", "L3", "phi")) + " |")
    pc = Cc.get("pooled_curve")
    if pc:
        out += ["", f"**Headroom inside the model's own distribution.** Plain + «Strategy s» samples pooled "
                f"({pc['pool_size']} per task; valid because the prefix shows no association with the outcome):", "",
                "| k | " + " | ".join(str(k) for k in pc["ks"]) + " |", "|---|" + "---|" * len(pc["ks"]),
                "| pass@k | " + " | ".join(_f(v) for v in pc["pass@k"]) + " |",
                "| #groups@k | " + " | ".join(_f(v, 2) for v in pc["groups@k"]) + " |", "",
                f"Tasks solved at least once in the pool: {pc['tasks_solved_in_pool']}/{pc['n_tasks']}; of them "
                f"solved by only 1–3 samples of {pc['pool_size']} (rare correct mass, the target of exploration): "
                f"{pc['tasks_rare_1_to_3_correct']}."]
    out += ["", "Note on «solve differently»: the chain shows the model its previous solutions without testing "
            "them, so most of them are incorrect — a pessimistic variant of forced diversity."]
    out += ["", "Pool sizes per task: " + "; ".join(f"{k}: {v['min']}–{v['max']}" for k, v in Cc["pool_sizes"].items())]
    if Cc.get("truncated"):
        out += ["", f"Share of samples cut at MAX_TOKENS={C.MAX_TOKENS} (they almost never pass the tests): " +
                "; ".join(f"{k}: {v:.2f}" for k, v in Cc["truncated"].items())]
    out += [""]
    return out


def build():
    A = read_json(C.RESULTS_DIR / "partA_auc.json")
    T = read_json(C.RESULTS_DIR / "partA_threshold.json", {}) or {}
    B = read_json(C.RESULTS_DIR / "partB.json")
    Cc = read_json(C.RESULTS_DIR / "partC.json")
    out = ["# Experiment 0 — report", "",
           f"Main model: `{C.MAIN_MODEL}`; extra models (part C): {', '.join('`%s`' % m for m in C.EXTRA_MODELS)}. "
           f"MBPP source: {'MBPP+ (EvalPlus tests)' if C.MBPP_SOURCE == 'plus' else 'sanitized MBPP (3 tests/task)'}. "
           f"Generation backend: {C.BACKEND}, max {C.MAX_TOKENS} new tokens"
           + (" (HF transformers, float16 on V100 — not vLLM bf16)." if C.BACKEND == "hf" else "."), ""]
    if A:
        out += _part_a(A, T)
    subs = [s for s in ("nontrivial", "all") if B and s in B]
    if B:
        out += ["## B. The model as is", "",
                "Numbers of fingerprint groups are read **relatively** (model vs human, condition vs plain "
                "sampling); their absolute values are not numbers of algorithms (see part A, grouping quality). "
                f"Trivial tasks (every reference solution is an O(1) formula on the task's ladder): "
                f"{len(B.get('trivial_tasks', []))}; the main tables use the non-trivial ones.", "",
                f"τ for d_φ clusters = {_f(B[subs[0]]['tau'])} (Youden on part A; clusters are built inside each "
                "condition's own population).", "", "![hist](figures/partB_hist.png)", ""]
        for s in subs:
            out += _part_b(B[s], s)
    if Cc:
        out += ["## C. Ceiling: forced diversity and temperature at the same budget", "",
                "#groups@k = expected number of distinct correct fingerprint groups (φ exact key) among k samples; "
                "exact hypergeometric estimates, same budget k for every condition. Temperature sweep: plain "
                f"sampling of the main model at T = {', '.join([f'{C.TEMPERATURE:g}'] + C.EXTRA_TEMPS)}.", "",
                "![passk](figures/partC_passk.png)", "", "![groups](figures/partC_groups.png)", ""]
        for s in subs:
            if s in Cc:
                out += _part_c(Cc[s], s)
        out += ["Per level numbers: `partC.json`. Raw generations: `generations/*.jsonl`.", ""]
    path = C.RESULTS_DIR / "report.md"
    path.write_text("\n".join(out), encoding="utf-8")
    log(f"report written: {path}")
    try:
        import sys
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    print("\n".join(out))
