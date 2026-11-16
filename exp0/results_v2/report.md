# Experiment 0 — report

Main model: `Qwen/Qwen3.5-2B`; extra models (part C): `Qwen/Qwen3.5-0.8B`, `Qwen/Qwen2.5-Coder-1.5B-Instruct`. MBPP source: MBPP+ (EvalPlus tests). Generation backend: hf, max 2048 new tokens (HF transformers, float16 on V100 — not vLLM bf16).

## A. Does the fingerprint separate algorithms?

d_phi = weighted sum of level distances with weights **0.6/0.25/0.15** (scaling / scheme / primitives) fixed in advance; *d_phi equal weights* is shown only as a sensitivity check, *learned* is a leave-one-family-out logistic regression.
AUC of the distance as a score for *different algorithm*. Within a dataset all metrics use exactly the same pairs. The real answer of part A is the comparison with JPlag and embeddings **on the same pairs**; the DivAlgo value 0.73 (C++, other pairs) is shown for reference only and is not directly comparable. 95% CI: bootstrap over problem families.

**dataset: manual** (pairs used: 148 of 200, different-algorithm: 12)

| metric | AUC | 95% CI | DivAlgo ref. 0.73 (not comparable) |
|---|---|---|---|
| d_phi equal weights | 0.858 | [0.733, 0.954] | above |
| d_phi | 0.853 | [0.733, 0.948] | above |
| d_phi:L2 | 0.841 | [0.699, 0.970] | above |
| d_phi:L1 | 0.821 | [0.701, 0.921] | above |
| difflib tokens | 0.757 | [0.611, 0.868] | above |
| d_phi learned (leave-family-out) | 0.695 | [0.433, 0.925] | below |
| emb:unixcoder-base | 0.681 | [0.519, 0.842] | below |
| emb:Qwen3-Embedding-0.6B | 0.615 | [0.430, 0.779] | below |
| d_phi:L3 | 0.592 | [0.461, 0.729] | below |
| AST bag | 0.585 | [0.402, 0.758] | below |
| JPlag | 0.559 | [0.427, 0.685] | below |

**dataset: human** (pairs used: 125 of 196, different-algorithm: 28)

| metric | AUC | 95% CI | DivAlgo ref. 0.73 (not comparable) |
|---|---|---|---|
| d_phi | 0.774 | [0.676, 0.862] | above |
| d_phi equal weights | 0.764 | [0.672, 0.854] | above |
| d_phi:L1 | 0.761 | [0.658, 0.857] | above |
| difflib tokens | 0.741 | [0.641, 0.834] | above |
| AST bag | 0.727 | [0.615, 0.817] | below |
| emb:Qwen3-Embedding-0.6B | 0.709 | [0.593, 0.822] | below |
| d_phi learned (leave-family-out) | 0.707 | [0.575, 0.828] | below |
| emb:unixcoder-base | 0.686 | [0.563, 0.807] | below |
| JPlag | 0.683 | [0.567, 0.784] | below |
| d_phi:L3 | 0.670 | [0.574, 0.773] | below |
| d_phi:L2 | 0.542 | [0.453, 0.644] | below |

**dataset: ours** (pairs used: 399 of 402, different-algorithm: 328)

| metric | AUC | 95% CI | DivAlgo ref. 0.73 (not comparable) |
|---|---|---|---|
| d_phi:L1 | 0.864 | [0.808, 0.909] | above |
| d_phi | 0.851 | [0.790, 0.904] | above |
| d_phi learned (leave-family-out) | 0.836 | [0.789, 0.885] | above |
| d_phi equal weights | 0.781 | [0.705, 0.854] | above |
| d_phi:L2 | 0.637 | [0.542, 0.724] | below |
| difflib tokens | 0.629 | [0.552, 0.691] | below |
| emb:unixcoder-base | 0.617 | [0.549, 0.673] | below |
| d_phi:L3 | 0.600 | [0.530, 0.682] | below |
| emb:Qwen3-Embedding-0.6B | 0.596 | [0.509, 0.681] | below |
| AST bag | 0.570 | [0.525, 0.625] | below |
| JPlag | 0.549 | [0.490, 0.611] | below |

How well do the *groupings* used in parts B/C recover algorithm labels (pairwise: predicted 'same group' vs labelled 'same algorithm'). Precision < 1 means one group can contain several algorithms, recall < 1 means one algorithm is split over several groups — so the number of groups is **not** the number of algorithms:

| grouping [dataset] | precision | recall | F1 | pairs |
|---|---|---|---|---|
| phi exact key [ours] | 0.63 | 0.47 | 0.54 | 402 |
| phi exact key [manual] | 0.98 | 0.79 | 0.88 | 163 |
| phi exact key [human] | 0.91 | 0.59 | 0.71 | 127 |
| L1 key [ours] | 0.46 | 0.72 | 0.56 | 402 |
| L1 key [manual] | 0.96 | 0.89 | 0.92 | 163 |
| L1 key [human] | 0.86 | 0.84 | 0.85 | 127 |
| d_phi <= tau [ours] | 0.41 | 0.89 | 0.56 | 402 |
| d_phi <= tau [manual] | 0.96 | 0.91 | 0.94 | 163 |
| d_phi <= tau [human] | 0.86 | 0.90 | 0.88 | 127 |

Repeatability (curated programs measured twice, 10 parallel pinned jobs): 1/135 changed their L1 class; median |Δslope| = 0.000, max = 0.043.

![ROC](figures/partA_roc.png)
