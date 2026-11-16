# Experiment 0 — report

Main model: `Qwen/Qwen2.5-Coder-1.5B-Instruct`; extra models (part C): `Qwen/Qwen3.5-2B`, `Qwen/Qwen3.5-0.8B`. MBPP source: MBPP+ (EvalPlus tests). Generation backend: hf, max 2048 new tokens (HF transformers, float16 on V100 — not vLLM bf16).

## A. Does the fingerprint separate algorithms?

> **Part A is NOT complete.** The required set of ~200 manually labelled pairs of *model* solutions is missing, and PACD is not connected. Everything below rests on our own curated set, written by the same author as the fingerprint, made of textbook problems whose algorithms differ mostly in complexity — an optimistic setting. Label `data/labels/manual_pairs_todo.jsonl` and re-run `bash exp0/run.sh partA report`.

d_phi = weighted sum of level distances with weights **0.6/0.25/0.15** (scaling / scheme / primitives) fixed in advance; *d_phi equal weights* is shown only as a sensitivity check, *learned* is a leave-one-family-out logistic regression.
AUC of the distance as a score for *different algorithm*. Within a dataset all metrics use exactly the same pairs. The real answer of part A is the comparison with JPlag and embeddings **on the same pairs**; the DivAlgo value 0.73 (C++, other pairs) is shown for reference only and is not directly comparable. 95% CI: bootstrap over problem families.

**dataset: ours** (pairs used: 399 of 402, different-algorithm: 328)

| metric | AUC | 95% CI | DivAlgo ref. 0.73 (not comparable) |
|---|---|---|---|
| d_phi:L1 | 0.866 | [0.803, 0.914] | above |
| d_phi | 0.848 | [0.779, 0.904] | above |
| d_phi learned (leave-family-out) | 0.839 | [0.783, 0.897] | above |
| d_phi equal weights | 0.783 | [0.708, 0.853] | above |
| d_phi:L2 | 0.637 | [0.542, 0.724] | below |
| difflib tokens | 0.629 | [0.552, 0.691] | below |
| emb:unixcoder-base | 0.617 | [0.549, 0.673] | below |
| d_phi:L3 | 0.600 | [0.530, 0.682] | below |
| emb:Qwen3-Embedding-0.6B | 0.596 | [0.509, 0.681] | below |
| AST bag | 0.570 | [0.525, 0.625] | below |
| JPlag | 0.549 | [0.490, 0.611] | below |

**dataset: all** (pairs used: 399 of 402, different-algorithm: 328)

| metric | AUC | 95% CI | DivAlgo ref. 0.73 (not comparable) |
|---|---|---|---|
| d_phi:L1 | 0.866 | [0.803, 0.914] | above |
| d_phi | 0.848 | [0.779, 0.904] | above |
| d_phi learned (leave-family-out) | 0.839 | [0.783, 0.897] | above |
| d_phi equal weights | 0.783 | [0.708, 0.853] | above |
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
| L1 key [ours] | 0.43 | 0.72 | 0.54 | 402 |
| d_phi <= tau [ours] | 0.39 | 0.89 | 0.54 | 402 |

Repeatability (curated programs measured twice, 10 parallel pinned jobs): 1/135 changed their L1 class; median |Δslope| = 0.000, max = 0.053.

![ROC](figures/partA_roc.png)

## B. The model as is

Numbers of fingerprint groups are read **relatively** (model vs human, condition vs plain sampling); their absolute values are not numbers of algorithms (see part A, grouping quality). Trivial tasks (every reference solution is an O(1) formula on the task's ladder): 82; the main tables use the non-trivial ones.

τ for d_φ clusters = 0.310 (Youden on part A; clusters are built inside each condition's own population).

![hist](figures/partB_hist.png)

### B [nontrivial tasks: 318]

Plain sampling: 16 samples/task, T=1.0, top_p=0.95, top_k=20. Pass rate per sample = 0.314; tasks with >=1 correct = 175.

Fingerprint coverage (correct solutions with a usable fingerprint on the task's ladder): plain (qwen2_5-coder-1_5b-instruct): 1349/1600; plain (qwen2_5-coder-1_5b-instruct, T=0.7): 1490/1772; plain (qwen2_5-coder-1_5b-instruct, T=1.3): 1109/1313; Strategy 1..4 prompts (round robin): 5399/6339; solve differently (sequential): 1510/1706; union qwen2_5-coder-1_5b-instruct+qwen3_5-2b: 2546/3153; union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b: 1965/2280; union of 3 models: 3162/3833; plain (qwen3_5-2b): 1197/1553; plain (qwen3_5-0_8b): 616/680; human: 1763/2686

| level | tasks | mean # fingerprint groups among correct | share of tasks with 1 group |
|---|---|---|---|
| L1 scaling | 140 | 1.26 | 0.76 |
| L2 scheme | 140 | 1.38 | 0.64 |
| L3 primitives | 140 | 1.19 | 0.82 |
| phi (all levels, exact key) | 140 | 1.66 | 0.50 |
| phi (d_phi <= tau clusters) | 140 | 1.19 | 0.82 |

The table above counts a task with ONE correct solution as 'one group', which inflates homogeneity. **Only tasks with at least m fingerprinted correct solutions, rarefied to exactly m** (this is the homogeneity number to quote):

| level | tasks (≥2) | 1 group (≥2) | mean groups among 2 | tasks (≥4) | 1 group (≥4) | mean groups among 4 |
|---|---|---|---|---|---|---|
| L1 scaling | 123 | 0.73 | 1.09 | 108 | 0.69 | 1.20 |
| L2 scheme | 123 | 0.59 | 1.14 | 108 | 0.55 | 1.27 |
| L3 primitives | 123 | 0.80 | 1.08 | 108 | 0.80 | 1.14 |
| phi (all levels, exact key) | 123 | 0.43 | 1.23 | 108 | 0.39 | 1.45 |
| phi (d_phi <= tau clusters) | 123 | 0.80 | 1.07 | 108 | 0.77 | 1.15 |

**Model vs human (APPS), rarefied to the same number of correct solutions per task** (a relative comparison — meaningful even though groups ≠ algorithms):

| level | tasks | model | human |
|---|---|---|---|
| L1 scaling | 27 | 1.19 | 1.68 |
| L2 scheme | 27 | 1.19 | 1.46 |
| L3 primitives | 27 | 1.26 | 1.51 |
| phi (all levels, exact key) | 27 | 1.56 | 2.34 |
| phi (d_phi <= tau clusters) | 27 | 1.15 | 1.57 |

**Seed prefix «Strategy s»: association with the fingerprint group among correct solutions** (permutation test of s within each task; a large p means *no detected* association, not proof that the seed is ignored — see the number of tasks tested):

| level | tasks tested | mean AMI | share of tasks p<0.05 | global permutation p |
|---|---|---|---|---|
| L1 scaling | 46 | 0.012 | 0.09 | 0.0629 |
| L2 scheme | 71 | 0.015 | 0.07 | 0.0340 |
| L3 primitives | 44 | -0.028 | 0.02 | 0.9850 |
| phi (all levels, exact key) | 96 | 0.005 | 0.06 | 0.2348 |
| phi (d_phi <= tau clusters) | 38 | 0.005 | 0.05 | 0.2288 |

Association of *correctness* with s: global permutation p = 0.4316 over 190 tasks. Pass rate per prefix: s1: 0.307, s2: 0.321, s3: 0.309, s4: 0.308

### B [all tasks: 400]

Plain sampling: 16 samples/task, T=1.0, top_p=0.95, top_k=20. Pass rate per sample = 0.357; tasks with >=1 correct = 245.

Fingerprint coverage (correct solutions with a usable fingerprint on the task's ladder): plain (qwen2_5-coder-1_5b-instruct): 2021/2282; plain (qwen2_5-coder-1_5b-instruct, T=0.7): 2199/2495; plain (qwen2_5-coder-1_5b-instruct, T=1.3): 1692/1900; Strategy 1..4 prompts (round robin): 7996/8975; solve differently (sequential): 2225/2436; union qwen2_5-coder-1_5b-instruct+qwen3_5-2b: 3836/4462; union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b: 3014/3340; union of 3 models: 4829/5520; plain (qwen3_5-2b): 1815/2180; plain (qwen3_5-0_8b): 993/1058; human: 1971/2894

| level | tasks | mean # fingerprint groups among correct | share of tasks with 1 group |
|---|---|---|---|
| L1 scaling | 210 | 1.22 | 0.80 |
| L2 scheme | 210 | 1.34 | 0.68 |
| L3 primitives | 210 | 1.16 | 0.85 |
| phi (all levels, exact key) | 210 | 1.59 | 0.56 |
| phi (d_phi <= tau clusters) | 210 | 1.17 | 0.84 |

The table above counts a task with ONE correct solution as 'one group', which inflates homogeneity. **Only tasks with at least m fingerprinted correct solutions, rarefied to exactly m** (this is the homogeneity number to quote):

| level | tasks (≥2) | 1 group (≥2) | mean groups among 2 | tasks (≥4) | 1 group (≥4) | mean groups among 4 |
|---|---|---|---|---|---|---|
| L1 scaling | 182 | 0.76 | 1.08 | 160 | 0.73 | 1.18 |
| L2 scheme | 182 | 0.63 | 1.13 | 160 | 0.61 | 1.24 |
| L3 primitives | 182 | 0.83 | 1.07 | 160 | 0.83 | 1.11 |
| phi (all levels, exact key) | 182 | 0.49 | 1.21 | 160 | 0.47 | 1.40 |
| phi (d_phi <= tau clusters) | 182 | 0.82 | 1.06 | 160 | 0.79 | 1.14 |

**Model vs human (APPS), rarefied to the same number of correct solutions per task** (a relative comparison — meaningful even though groups ≠ algorithms):

| level | tasks | model | human |
|---|---|---|---|
| L1 scaling | 36 | 1.17 | 1.51 |
| L2 scheme | 36 | 1.25 | 1.43 |
| L3 primitives | 36 | 1.25 | 1.39 |
| phi (all levels, exact key) | 36 | 1.58 | 2.10 |
| phi (d_phi <= tau clusters) | 36 | 1.14 | 1.43 |

**Seed prefix «Strategy s»: association with the fingerprint group among correct solutions** (permutation test of s within each task; a large p means *no detected* association, not proof that the seed is ignored — see the number of tasks tested):

| level | tasks tested | mean AMI | share of tasks p<0.05 | global permutation p |
|---|---|---|---|---|
| L1 scaling | 66 | 0.028 | 0.08 | 0.0130 |
| L2 scheme | 94 | 0.013 | 0.04 | 0.0509 |
| L3 primitives | 58 | -0.014 | 0.02 | 0.9071 |
| phi (all levels, exact key) | 134 | 0.014 | 0.06 | 0.0669 |
| phi (d_phi <= tau clusters) | 55 | 0.028 | 0.05 | 0.0340 |

Association of *correctness* with s: global permutation p = 0.6064 over 257 tasks. Pass rate per prefix: s1: 0.346, s2: 0.356, s3: 0.349, s4: 0.351

## C. Ceiling: forced diversity and temperature at the same budget

#groups@k = expected number of distinct correct fingerprint groups (φ exact key) among k samples; exact hypergeometric estimates, same budget k for every condition. Temperature sweep: plain sampling of the main model at T = 1, 0.7, 1.3.

![passk](figures/partC_passk.png)

![groups](figures/partC_groups.png)

### C [nontrivial tasks]

| condition | pass@1 | pass@4 | pass@8 | pass@16 | #groups@1 | #groups@4 | #groups@8 | #groups@16 |
|---|---|---|---|---|---|---|---|---|
| plain (qwen2_5-coder-1_5b-instruct) | 0.314 | 0.447 | 0.498 | 0.550 | 0.27 | 0.47 | 0.59 | 0.73 |
| plain (qwen2_5-coder-1_5b-instruct, T=0.7) | 0.348 | 0.458 | 0.498 | 0.538 | 0.29 | 0.47 | 0.56 | 0.67 |
| plain (qwen2_5-coder-1_5b-instruct, T=1.3) | 0.258 | 0.417 | 0.466 | 0.506 | 0.22 | 0.44 | 0.57 | 0.72 |
| Strategy 1..4 prompts (round robin) | 0.311 | 0.449 | 0.496 | 0.540 | 0.27 | 0.47 | 0.59 | 0.72 |
| solve differently (sequential) | 0.314 | 0.407 | 0.442 | 0.456 | 0.28 | 0.52 | 0.64 | 0.78 |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-2b | 0.310 | 0.502 | 0.570 | 0.631 | 0.25 | 0.50 | 0.65 | 0.83 |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b | 0.224 | 0.414 | 0.469 | 0.518 | 0.19 | 0.42 | 0.54 | 0.68 |
| union of 3 models | 0.251 | 0.465 | 0.537 | 0.599 | 0.21 | 0.45 | 0.59 | 0.76 |
| plain (qwen3_5-2b) | 0.305 | 0.487 | 0.560 | 0.623 | 0.24 | 0.45 | 0.59 | 0.75 |
| plain (qwen3_5-0_8b) | 0.134 | 0.272 | 0.343 | 0.406 | 0.12 | 0.27 | 0.36 | 0.46 |

Gain in pass@k over plain sampling at T=1 (paired bootstrap 95% CI over tasks):

| condition | Δ@1 | Δ@4 | Δ@8 | Δ@16 |
|---|---|---|---|---|
| plain (qwen2_5-coder-1_5b-instruct, T=0.7) | +0.034 [+0.021, +0.047] | +0.011 [-0.005, +0.026] | +0.000 [-0.022, +0.024] | -0.013 [-0.047, +0.022] |
| plain (qwen2_5-coder-1_5b-instruct, T=1.3) | -0.056 [-0.069, -0.043] | -0.031 [-0.046, -0.018] | -0.031 [-0.053, -0.011] | -0.044 [-0.075, -0.013] |
| Strategy 1..4 prompts (round robin) | -0.003 [-0.012, +0.005] | +0.002 [-0.010, +0.014] | -0.001 [-0.019, +0.017] | -0.011 [-0.041, +0.016] |
| solve differently (sequential) | +0.000 [-0.025, +0.024] | -0.040 [-0.064, -0.015] | -0.056 [-0.084, -0.028] | -0.094 [-0.129, -0.060] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-2b | -0.005 [-0.019, +0.009] | +0.055 [+0.033, +0.077] | +0.072 [+0.046, +0.099] | +0.081 [+0.048, +0.114] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b | -0.090 [-0.106, -0.077] | -0.034 [-0.044, -0.023] | -0.028 [-0.041, -0.015] | -0.032 [-0.049, -0.015] |
| union of 3 models | -0.063 [-0.081, -0.046] | +0.018 [-0.001, +0.039] | +0.040 [+0.016, +0.064] | +0.049 [+0.019, +0.079] |
| plain (qwen3_5-2b) | -0.009 [-0.037, +0.019] | +0.040 [+0.007, +0.075] | +0.063 [+0.026, +0.101] | +0.072 [+0.022, +0.119] |
| plain (qwen3_5-0_8b) | -0.181 [-0.211, -0.156] | -0.175 [-0.209, -0.144] | -0.154 [-0.193, -0.118] | -0.145 [-0.192, -0.104] |

Gain in groups@k over plain sampling at T=1 (paired bootstrap 95% CI over tasks):

| condition | Δ@1 | Δ@4 | Δ@8 | Δ@16 |
|---|---|---|---|---|
| plain (qwen2_5-coder-1_5b-instruct, T=0.7) | +0.028 [+0.017, +0.039] | -0.006 [-0.029, +0.018] | -0.030 [-0.067, +0.006] | -0.066 [-0.126, -0.003] |
| plain (qwen2_5-coder-1_5b-instruct, T=1.3) | -0.047 [-0.059, -0.035] | -0.037 [-0.061, -0.013] | -0.027 [-0.064, +0.010] | -0.009 [-0.069, +0.050] |
| Strategy 1..4 prompts (round robin) | +0.000 [-0.008, +0.007] | -0.002 [-0.020, +0.017] | -0.005 [-0.036, +0.025] | -0.013 [-0.065, +0.034] |
| solve differently (sequential) | +0.012 [-0.010, +0.033] | +0.047 [+0.003, +0.093] | +0.045 [-0.015, +0.107] | +0.042 [-0.041, +0.132] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-2b | -0.015 [-0.027, -0.003] | +0.024 [-0.002, +0.051] | +0.054 [+0.019, +0.093] | +0.096 [+0.046, +0.156] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b | -0.072 [-0.086, -0.059] | -0.056 [-0.073, -0.038] | -0.054 [-0.078, -0.030] | -0.054 [-0.089, -0.018] |
| union of 3 models | -0.058 [-0.074, -0.043] | -0.026 [-0.052, +0.001] | -0.001 [-0.036, +0.036] | +0.032 [-0.017, +0.086] |
| plain (qwen3_5-2b) | -0.030 [-0.055, -0.006] | -0.023 [-0.072, +0.026] | +0.000 [-0.067, +0.065] | +0.019 [-0.072, +0.113] |
| plain (qwen3_5-0_8b) | -0.144 [-0.171, -0.117] | -0.209 [-0.258, -0.165] | -0.235 [-0.301, -0.178] | -0.277 [-0.368, -0.198] |

**Diversity at an equal number of correct solutions.** #groups@k above counts groups among correct samples, so a condition that lowers correctness loses groups mechanically. Here the condition and plain sampling are both rarefied to the same number of fingerprinted correct solutions per task (tasks with ≥2 on both sides); Δ = condition − plain, paired bootstrap 95% CI:

| condition | tasks | Δ L1 scaling | Δ L2 scheme | Δ L3 primitives | Δ phi (all levels, exact key) |
|---|---|---|---|---|---|
| plain (qwen2_5-coder-1_5b-instruct, T=0.7) | 114 | -0.068 [-0.144, +0.005] | -0.140 [-0.229, -0.051] | -0.033 [-0.088, +0.021] | -0.213 [-0.339, -0.096] |
| plain (qwen2_5-coder-1_5b-instruct, T=1.3) | 114 | +0.058 [-0.012, +0.133] | +0.077 [-0.016, +0.177] | +0.088 [+0.025, +0.151] | +0.170 [+0.037, +0.301] |
| Strategy 1..4 prompts (round robin) | 123 | -0.023 [-0.082, +0.037] | -0.063 [-0.136, +0.008] | -0.001 [-0.054, +0.051] | -0.076 [-0.180, +0.034] |
| solve differently (sequential) | 113 | +0.144 [+0.060, +0.242] | +0.271 [+0.159, +0.384] | +0.465 [+0.317, +0.632] | +0.758 [+0.544, +0.993] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-2b | 123 | +0.006 [-0.028, +0.047] | +0.014 [-0.035, +0.064] | +0.038 [+0.005, +0.079] | +0.040 [-0.030, +0.116] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b | 123 | +0.022 [-0.010, +0.058] | +0.047 [-0.003, +0.104] | +0.050 [+0.010, +0.096] | +0.082 [+0.016, +0.150] |
| union of 3 models | 123 | +0.031 [-0.014, +0.078] | +0.043 [-0.014, +0.112] | +0.066 [+0.019, +0.122] | +0.089 [-0.004, +0.181] |
| plain (qwen3_5-2b) | 104 | -0.046 [-0.126, +0.034] | -0.097 [-0.199, +0.004] | +0.015 [-0.053, +0.086] | -0.135 [-0.282, +0.015] |
| plain (qwen3_5-0_8b) | 85 | -0.034 [-0.104, +0.031] | -0.054 [-0.158, +0.057] | +0.035 [-0.048, +0.128] | -0.043 [-0.192, +0.122] |

**Headroom inside the model's own distribution.** Plain + «Strategy s» samples pooled (80 per task; valid because the prefix shows no association with the outcome):

| k | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 80 |
|---|---|---|---|---|---|---|---|---|
| pass@k | 0.312 | 0.390 | 0.449 | 0.497 | 0.542 | 0.586 | 0.628 | 0.642 |
| #groups@k | 0.27 | 0.37 | 0.47 | 0.59 | 0.72 | 0.87 | 1.05 | 1.11 |

Tasks solved at least once in the pool: 204/318; of them solved by only 1–3 samples of 80 (rare correct mass, the target of exploration): 35.

Note on «solve differently»: the chain shows the model its previous solutions without testing them, so most of them are incorrect — a pessimistic variant of forced diversity.

Pool sizes per task: plain (qwen2_5-coder-1_5b-instruct): 16–16; plain (qwen2_5-coder-1_5b-instruct, T=0.7): 16–16; plain (qwen2_5-coder-1_5b-instruct, T=1.3): 16–16; Strategy 1..4 prompts (round robin): 64–64; solve differently (sequential): 32–32; union qwen2_5-coder-1_5b-instruct+qwen3_5-2b: 32–32; union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b: 32–32; union of 3 models: 48–48; plain (qwen3_5-2b): 16–16; plain (qwen3_5-0_8b): 16–16

Share of samples cut at MAX_TOKENS=2048 (they almost never pass the tests): plain (qwen2_5-coder-1_5b-instruct): 0.00; plain (qwen2_5-coder-1_5b-instruct, T=0.7): 0.00; plain (qwen2_5-coder-1_5b-instruct, T=1.3): 0.00; Strategy 1..4 prompts (round robin): 0.00; solve differently (sequential): 0.00; union qwen2_5-coder-1_5b-instruct+qwen3_5-2b: 0.12; union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b: 0.10; union of 3 models: 0.15; plain (qwen3_5-2b): 0.24; plain (qwen3_5-0_8b): 0.20

### C [all tasks]

| condition | pass@1 | pass@4 | pass@8 | pass@16 | #groups@1 | #groups@4 | #groups@8 | #groups@16 |
|---|---|---|---|---|---|---|---|---|
| plain (qwen2_5-coder-1_5b-instruct) | 0.357 | 0.501 | 0.555 | 0.613 | 0.32 | 0.55 | 0.68 | 0.83 |
| plain (qwen2_5-coder-1_5b-instruct, T=0.7) | 0.390 | 0.505 | 0.547 | 0.590 | 0.34 | 0.53 | 0.62 | 0.73 |
| plain (qwen2_5-coder-1_5b-instruct, T=1.3) | 0.297 | 0.470 | 0.526 | 0.573 | 0.26 | 0.51 | 0.66 | 0.83 |
| Strategy 1..4 prompts (round robin) | 0.351 | 0.498 | 0.546 | 0.591 | 0.31 | 0.54 | 0.66 | 0.80 |
| solve differently (sequential) | 0.351 | 0.446 | 0.484 | 0.502 | 0.32 | 0.57 | 0.70 | 0.85 |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-2b | 0.349 | 0.550 | 0.617 | 0.676 | 0.30 | 0.57 | 0.73 | 0.92 |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b | 0.261 | 0.467 | 0.525 | 0.576 | 0.24 | 0.49 | 0.62 | 0.77 |
| union of 3 models | 0.287 | 0.512 | 0.586 | 0.646 | 0.25 | 0.52 | 0.67 | 0.85 |
| plain (qwen3_5-2b) | 0.341 | 0.528 | 0.599 | 0.657 | 0.28 | 0.52 | 0.67 | 0.83 |
| plain (qwen3_5-0_8b) | 0.165 | 0.312 | 0.386 | 0.450 | 0.16 | 0.32 | 0.41 | 0.53 |

Gain in pass@k over plain sampling at T=1 (paired bootstrap 95% CI over tasks):

| condition | Δ@1 | Δ@4 | Δ@8 | Δ@16 |
|---|---|---|---|---|
| plain (qwen2_5-coder-1_5b-instruct, T=0.7) | +0.033 [+0.022, +0.045] | +0.005 [-0.011, +0.020] | -0.007 [-0.028, +0.015] | -0.022 [-0.058, +0.010] |
| plain (qwen2_5-coder-1_5b-instruct, T=1.3) | -0.060 [-0.071, -0.048] | -0.031 [-0.045, -0.017] | -0.029 [-0.048, -0.011] | -0.040 [-0.070, -0.013] |
| Strategy 1..4 prompts (round robin) | -0.006 [-0.014, +0.002] | -0.002 [-0.013, +0.009] | -0.008 [-0.026, +0.008] | -0.022 [-0.049, +0.001] |
| solve differently (sequential) | -0.005 [-0.028, +0.018] | -0.054 [-0.080, -0.030] | -0.071 [-0.095, -0.046] | -0.110 [-0.141, -0.077] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-2b | -0.008 [-0.021, +0.004] | +0.049 [+0.031, +0.068] | +0.063 [+0.041, +0.084] | +0.063 [+0.035, +0.091] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b | -0.096 [-0.108, -0.083] | -0.034 [-0.042, -0.024] | -0.029 [-0.040, -0.018] | -0.036 [-0.052, -0.021] |
| union of 3 models | -0.069 [-0.084, -0.054] | +0.012 [-0.005, +0.032] | +0.031 [+0.011, +0.056] | +0.034 [+0.009, +0.063] |
| plain (qwen3_5-2b) | -0.016 [-0.043, +0.010] | +0.027 [-0.005, +0.059] | +0.044 [+0.009, +0.080] | +0.045 [+0.003, +0.087] |
| plain (qwen3_5-0_8b) | -0.191 [-0.218, -0.162] | -0.188 [-0.220, -0.154] | -0.169 [-0.202, -0.135] | -0.163 [-0.205, -0.122] |

Gain in groups@k over plain sampling at T=1 (paired bootstrap 95% CI over tasks):

| condition | Δ@1 | Δ@4 | Δ@8 | Δ@16 |
|---|---|---|---|---|
| plain (qwen2_5-coder-1_5b-instruct, T=0.7) | +0.028 [+0.018, +0.038] | -0.018 [-0.042, +0.003] | -0.052 [-0.091, -0.017] | -0.100 [-0.163, -0.043] |
| plain (qwen2_5-coder-1_5b-instruct, T=1.3) | -0.051 [-0.064, -0.040] | -0.033 [-0.056, -0.010] | -0.019 [-0.052, +0.016] | -0.003 [-0.058, +0.050] |
| Strategy 1..4 prompts (round robin) | -0.003 [-0.011, +0.004] | -0.006 [-0.023, +0.011] | -0.013 [-0.042, +0.014] | -0.029 [-0.077, +0.016] |
| solve differently (sequential) | +0.004 [-0.015, +0.025] | +0.027 [-0.013, +0.068] | +0.019 [-0.033, +0.071] | +0.019 [-0.058, +0.084] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-2b | -0.016 [-0.028, -0.005] | +0.028 [+0.006, +0.050] | +0.054 [+0.021, +0.087] | +0.084 [+0.037, +0.131] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b | -0.080 [-0.092, -0.068] | -0.058 [-0.076, -0.042] | -0.058 [-0.081, -0.035] | -0.061 [-0.096, -0.028] |
| union of 3 models | -0.064 [-0.078, -0.050] | -0.026 [-0.049, -0.005] | -0.002 [-0.035, +0.026] | +0.022 [-0.025, +0.065] |
| plain (qwen3_5-2b) | -0.032 [-0.057, -0.010] | -0.024 [-0.069, +0.021] | -0.007 [-0.070, +0.052] | -0.005 [-0.090, +0.083] |
| plain (qwen3_5-0_8b) | -0.161 [-0.186, -0.136] | -0.231 [-0.276, -0.191] | -0.262 [-0.321, -0.210] | -0.305 [-0.390, -0.230] |

**Diversity at an equal number of correct solutions.** #groups@k above counts groups among correct samples, so a condition that lowers correctness loses groups mechanically. Here the condition and plain sampling are both rarefied to the same number of fingerprinted correct solutions per task (tasks with ≥2 on both sides); Δ = condition − plain, paired bootstrap 95% CI:

| condition | tasks | Δ L1 scaling | Δ L2 scheme | Δ L3 primitives | Δ phi (all levels, exact key) |
|---|---|---|---|---|---|
| plain (qwen2_5-coder-1_5b-instruct, T=0.7) | 167 | -0.070 [-0.128, -0.010] | -0.136 [-0.207, -0.062] | -0.024 [-0.064, +0.015] | -0.199 [-0.305, -0.101] |
| plain (qwen2_5-coder-1_5b-instruct, T=1.3) | 168 | +0.059 [+0.004, +0.113] | +0.054 [-0.017, +0.126] | +0.099 [+0.045, +0.157] | +0.166 [+0.067, +0.269] |
| Strategy 1..4 prompts (round robin) | 181 | -0.009 [-0.053, +0.035] | -0.048 [-0.099, +0.006] | +0.019 [-0.023, +0.061] | -0.046 [-0.121, +0.032] |
| solve differently (sequential) | 168 | +0.143 [+0.073, +0.218] | +0.241 [+0.145, +0.323] | +0.399 [+0.296, +0.517] | +0.661 [+0.502, +0.838] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-2b | 182 | +0.019 [-0.010, +0.053] | +0.017 [-0.021, +0.060] | +0.028 [+0.000, +0.060] | +0.035 [-0.020, +0.092] |
| union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b | 182 | +0.026 [-0.000, +0.057] | +0.036 [-0.001, +0.080] | +0.036 [+0.007, +0.067] | +0.064 [+0.016, +0.121] |
| union of 3 models | 182 | +0.036 [+0.002, +0.074] | +0.038 [-0.005, +0.085] | +0.048 [+0.014, +0.087] | +0.071 [+0.002, +0.143] |
| plain (qwen3_5-2b) | 156 | -0.030 [-0.095, +0.033] | -0.072 [-0.144, +0.004] | +0.010 [-0.041, +0.066] | -0.120 [-0.225, -0.007] |
| plain (qwen3_5-0_8b) | 128 | -0.007 [-0.066, +0.055] | -0.028 [-0.114, +0.061] | +0.013 [-0.053, +0.086] | -0.029 [-0.160, +0.091] |

**Headroom inside the model's own distribution.** Plain + «Strategy s» samples pooled (80 per task; valid because the prefix shows no association with the outcome):

| k | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 80 |
|---|---|---|---|---|---|---|---|---|
| pass@k | 0.352 | 0.436 | 0.499 | 0.548 | 0.595 | 0.640 | 0.681 | 0.693 |
| #groups@k | 0.31 | 0.43 | 0.54 | 0.67 | 0.81 | 0.97 | 1.15 | 1.22 |

Tasks solved at least once in the pool: 277/400; of them solved by only 1–3 samples of 80 (rare correct mass, the target of exploration): 43.

Note on «solve differently»: the chain shows the model its previous solutions without testing them, so most of them are incorrect — a pessimistic variant of forced diversity.

Pool sizes per task: plain (qwen2_5-coder-1_5b-instruct): 16–16; plain (qwen2_5-coder-1_5b-instruct, T=0.7): 16–16; plain (qwen2_5-coder-1_5b-instruct, T=1.3): 16–16; Strategy 1..4 prompts (round robin): 64–64; solve differently (sequential): 32–32; union qwen2_5-coder-1_5b-instruct+qwen3_5-2b: 32–32; union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b: 32–32; union of 3 models: 48–48; plain (qwen3_5-2b): 16–16; plain (qwen3_5-0_8b): 16–16

Share of samples cut at MAX_TOKENS=2048 (they almost never pass the tests): plain (qwen2_5-coder-1_5b-instruct): 0.00; plain (qwen2_5-coder-1_5b-instruct, T=0.7): 0.00; plain (qwen2_5-coder-1_5b-instruct, T=1.3): 0.00; Strategy 1..4 prompts (round robin): 0.00; solve differently (sequential): 0.00; union qwen2_5-coder-1_5b-instruct+qwen3_5-2b: 0.10; union qwen2_5-coder-1_5b-instruct+qwen3_5-0_8b: 0.08; union of 3 models: 0.12; plain (qwen3_5-2b): 0.20; plain (qwen3_5-0_8b): 0.17

Per level numbers: `partC.json`. Raw generations: `generations/*.jsonl`.
