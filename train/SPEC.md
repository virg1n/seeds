# Seed training — implementation spec

Goal of the experiment: fine-tune `Qwen/Qwen2.5-Coder-1.5B-Instruct` with GRPO so that N=4 fixed
**seeds** make the model write *algorithmically different correct programs*; one sample per seed
should then solve more tasks (pass@4) than 4 i.i.d. samples of a GRPO baseline trained without
seeds, and the correct solutions of different seeds should fall into different execution-fingerprint
groups. No LLM judge in the loop: the reward comes from tests + an execution fingerprint (exp0).

Target machine: Linux Jupyter pod, 4 x RTX 6000 Ada (48 GB), ~32 CPUs, conda `python3` that already
has torch + transformers (maybe vllm; we do NOT use vllm), internet access to huggingface.co, a disk
quota: **everything we write must stay under 20 GB inside `seeds/train/`**. No nvcc (nothing that
JIT-compiles CUDA: no flash-attn, no torch.compile). Total wall budget ~30 h. Local development
machine: Windows, CPU-only torch 2.10 / transformers 4.57 — every module must import and its unit
tests must run there (no `fcntl`, `resource`, `os.sched_setaffinity` at import time; guard them).

Code style: plain Python (compatible with 3.10+), `from __future__ import annotations`, no new
dependencies beyond `torch, transformers, numpy, requests, huggingface_hub` (no peft, trl,
accelerate, scipy, datasets, wandb). Comments/docstrings/log messages in English, short and factual.
Logging: `print(time.strftime("%H:%M:%S"), ..., flush=True)`. All files UTF-8 with LF newlines
(`run.sh` MUST have LF). Atomic writes (`.tmp` + `os.replace`) for every state file.

## Already written (do NOT edit; read them first)

- `st/config.py` — every setting (env-overridable). If you need a new setting, read it in your own
  module with `CFG._env("NAME", default, cast)` and list it in your final report.
- `st/exp0.py` — bridge to `seeds/exp0/src` (`C0, FP, fpstore, sandbox, scaler, prompts, utils`),
  `setup(run_dir)` (must be called once per process before sandbox work), `apply_cores()`,
  `physical_cores()`, `cpu_quota()`.
- `st/reward.py` — `dist`, `soft`, `clusters`, `ladder_inputs`, `judge_trace`, `measure`,
  `score_programs(items, need_fp)`, `group_reward(rows, full)`, `advantages(rewards)`.
- exp0 (read-only, do not modify): `exp0/src/{sandbox,harness,scaler,fingerprint,fpstore,data,prompts,utils}.py`.
  Useful: `sandbox.test_program(task, code)`, `sandbox.trace_program(task, code, inputs=None)`,
  `fpstore._slim`, `fpstore.valid_rungs(ref_traces)`, `FP.compute_all(code, trace, valid)`,
  `FP.select_ladder(fpalls)`, `FP.pick(fpall, lad)`, `scaler.func_recipe / stdio_recipe / build_ladder`,
  `prompts.problem_prompt(task)`, `prompts.extract_code(text)`, `data._iter_lines(url)`,
  `utils.parallel_map / JsonlCache / read_jsonl / write_jsonl / sha`.
- Engineering templates validated on the target server (read for patterns, do not import, and do
  not study what that project is about): `C:\Users\bogda\github\Myres\phase1\grpo.py` (HF-generate
  GRPO loop, resume), `phase1\film.py` (hand-rolled LoRA), `phase1\train.py` (`micro`, `collate`,
  `per_example_nll`), `pilot\run_all.py` (job runner, STATUS.md), `run_phase1_grpo.sh` (launcher).

## Task format (jsonl, exp0 format + extras)

`id, source, kind ("func"|"stdio"), entry, setup, text, starter, example_test, tests,
ladder_recipe, ref` (validated reference solutions) plus, added by `st.data`:

- `split`: "train" | "val" | "test"
- `lad`: name of the task's measurement ladder or null; `rungs`: sorted valid sizes on it
- `ref_out`: `{str(size): digest}` for rungs where >= 2 references produced output and all agree
- `ref_time`: `{str(size): seconds}` = max over references of the untraced timing on that rung
- `ref_fp`: fingerprints (on `lad`, only `ok` ones) of the references; `ref_groups`: number of
  `reward.clusters` groups among them
- `probe`: `{"n": PROBE_N, "correct": k}` (train/val only), `prompt_tokens`

## Module A — `st/model.py`, `st/sampler.py`, `tests/test_model.py`

`st/model.py`
- `model_path() -> str`: local dir of `CFG.MODEL` under `CFG.MODELS_DIR`
  (`huggingface_hub.snapshot_download(..., local_dir=..., allow_patterns=["*.json","*.safetensors","*.txt","tokenizer*","merges*","vocab*"])`
  if not there yet). Env `MODEL_TINY=1`: return the string `"tiny"`.
- `class Policy(path, mode, device, lora=True)`; `mode` in `{"film","prompt","none","base"}`
  (`base` = frozen base model, no LoRA, no modulator: probe and base-model evaluation).
  - Loads tokenizer (`padding_side` is managed by the sampler) and `AutoModelForCausalLM`
    (`dtype=` bf16 on CUDA, float32 on CPU; fall back to `torch_dtype=` on TypeError), freezes
    the base, `gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})`.
    `path == "tiny"`: tokenizer of `CFG.MODEL` (download tokenizer files only) + a random
    `Qwen2ForCausalLM(Qwen2Config(vocab_size=len(tok), hidden_size=64, num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2, intermediate_size=128, ...))`, float32 — for CPU tests.
  - Hand-rolled LoRA (`LoRALinear`: A ~ kaiming, B = 0, scale = alpha / r, fp32 params, computed
    under autocast) on `CFG.LORA_TARGETS` of every decoder layer; shared by all seeds.
  - Seed modulator (mode `film`), the core idea "some_neurons * nn2(seed)":
    - code of seed z: fixed `e_z = torch.randn(SEED_DIM, generator=manual_seed(10007 * z + 1))` (a buffer,
      not trained; any integer z works, so new seeds can be drawn later);
    - `nn2`: `Linear(SEED_DIM, FILM_HIDDEN) -> SiLU -> Linear(FILM_HIDDEN, FILM_RANK)` = `m(e_z)`;
    - per modulated layer l (`CFG.FILM_LAYERS`): `U_l` of shape `[d_ff, FILM_RANK]`,
      `delta_{z,l} = U_l @ m(e_z)`, `gain = 1 + FILM_MAX * tanh(delta / FILM_MAX)`;
      `U_l` init: zeros if `FILM_INIT == 0` else normal with std chosen so that std(delta) ~ FILM_INIT;
    - applied to the MLP hidden neurons: a forward-pre-hook on `layer.mlp.down_proj` (the module
      actually called after LoRA wrapping) multiplies its input `[B, T, d_ff]` by `gain[rows] [B, 1, d_ff]`.
      Row b uses the seed of row b. Works with KV-cache decoding in `generate` and with gradient
      checkpointing (the gains are closed-over tensors that require grad: non-reentrant checkpoint).
    - params fp32; gains computed under the same autocast as the forward.
  - `render(task, seed) -> list[int]`: token ids of the chat-template prompt
    (`[{"role":"user","content": prompts.problem_prompt(task)}]`, `add_generation_prompt=True`);
    mode `prompt` prepends `f"Strategy {seed + 1}.\n\n"` to the user content. Other modes ignore `seed`.
  - `set_seeds(seeds: list[int] | None)`: per-row seeds of the NEXT forward / generate call
    (film: compute and store the gains; other modes: no-op). `None` clears.
  - `param_groups(lr) -> list[dict]` for AdamW (LoRA at `lr`, modulator at `lr * FILM_LR_RATIO`),
    `trainable() -> list[Parameter]`, `state() -> dict` (cpu tensors of LoRA + modulator + meta),
    `load_state(sd)`, `gain_stats() -> dict` (per-seed mean |gain - 1|, mean pairwise cosine of
    the seeds' deltas; `{}` for non-film modes).

`st/sampler.py`
- `stop_ids(tok)`: ids of `<|im_end|>`, `<|endoftext|>`, `tok.eos_token_id`.
- `rollout(policy, rows, seed, max_tokens=None, desc="") -> list[dict]`: `rows = [{"p": prompt ids, "seed": int}]`
  -> same order `[{"t": completion ids up to and including the first stop token, "truncated": bool, "text": str}]`.
  `model.eval()`, `torch.no_grad()`, left padding, rows sorted by prompt length, calls of at most
  `GEN_BATCH` rows and `rows * (longest prompt + max_tokens) <= GEN_TOKENS`, explicit
  `GenerationConfig(do_sample=True, temperature=CFG.TEMPERATURE, top_p=CFG.TOP_P, top_k=CFG.TOP_K, max_new_tokens=..., eos_token_id=stop ids, pad_token_id=..., use_cache=True, repetition_penalty=1.0)`
  (the model's own generation_config must not leak in; `top_k=0` must mean "off"), bf16 autocast on
  CUDA, `torch.manual_seed(seed + call index)` before each call, CUDA OOM -> halve the batch and retry.
  `text` = decode with `skip_special_tokens=True`.
- `backward_pg(policy, rows, coef, mb_tokens=None) -> (nll: list[float], ntok: list[int])`: accumulates
  the gradient of `sum_i coef_i * NLL_i`, `NLL_i = -sum_t log pi(t_it | p_i, t_i<t)` over the completion
  tokens `rows[i]["t"]` (prompt `rows[i]["p"]`, seed `rows[i]["seed"]`), in micro-batches of at most
  `mb_tokens` padded tokens (right padding, sorted by length), `model.train()` (gradient
  checkpointing on), bf16 autocast, **lm_head / log-softmax only on completion positions** (the
  vocabulary is 151k: full-sequence logits would not fit), log-softmax in float32. On CUDA OOM:
  zero the gradients, halve `mb_tokens`, restart the whole call. Does not step the optimizer.
- `sequence_logprob(policy, rows) -> list[float]`: no-grad `-NLL_i` (tests / diagnostics).

`tests/test_model.py` (CPU, `MODEL_TINY=1`, runnable as `python -m tests.test_model`): zero-init
equivalence (film policy with fresh modulator == base logits); after perturbing `U_l`, rows with
different seeds get different logits and row b is unaffected by the seeds of other rows; batched
left-padded scoring == single-row scoring; **the log-probability of a `rollout` sample recomputed by
`sequence_logprob` equals the sum of the sampling log-probs** (generate with `output_scores` in the
test, T=1) for film mode with mixed seeds in one batch; `backward_pg` gives non-zero grads on LoRA B…
(after a non-zero B) and on the modulator and none on the base; `state()`/`load_state` round trip.

## Module B — `st/data.py`, `tests/test_data.py`

CLI: `python -m st.data prep` and `python -m st.data pool` (both resumable, parallel on CPU via
`utils.parallel_map`, call `exp0.setup(CFG.RUN_DIR)` first).

`prep` -> `RUN_DIR/data/candidates.jsonl`
1. APPS **train** split (`https://huggingface.co/datasets/codeparrot/apps/resolve/main/train.jsonl`,
   107 MB, stream with `data0._iter_lines`; env `APPS_TRAIN_URL` may be a local path), difficulty
   `introductory`, with solutions and >= `MIN_TESTS` tests -> ids `appstr/<problem_id>`. Measured on
   the real file: 2639 introductory problems, 2504 with `fn_name` (function tasks), 1487 with >= 5 tests.
2. If `USE_APPS_TEST_REST`: APPS **test** split (`.../test.jsonl`, 1.3 GB, stream; env `APPS_URL`),
   `introductory`, ids `appste/<problem_id>`, **excluding** every problem of the held-out set
   `CFG.TEST_TASKS` (exp0 ids there are `apps/<problem_id>` of the same test split) and anything whose
   normalized statement hash (lowercase, whitespace collapsed) equals a held-out task's or an
   earlier candidate's (decontamination; report the counts).
   Cache the trimmed raw rows in `CFG.DATA_DIR` (so a re-run does not download again); keep at most
   `MAX_TESTS` tests per task, drop tests whose input is longer than `MAX_TEST_CHARS`.
3. Build tasks exactly like `exp0/src/data.py::load_apps` does (func tests `{"type":"call","args","expected"}`
   + `func_recipe`, stdio tests `{"input","output"}` + `stdio_recipe`, `C0.LADDER_FACTORS`, seed `DATA_SEED`).
4. Validate references with `sandbox.test_program`: try up to `N_REF_TRY`, keep the first
   `N_REF_KEEP` that pass -> `ref`; drop tasks with none. Deduplicate `ref` by text.
5. `prompt_tokens` with the tokenizer of `CFG.MODEL` (chat template as in `Policy.render`, plus 12
   tokens of slack for the "Strategy s." prefix); drop tasks above `MAX_PROMPT_TOKENS`.
6. Validation split: `N_VAL` tasks sampled at random (seed `DATA_SEED`, proportionally from both
   sources) BEFORE any probe filtering -> `split="val"`; the rest `split="train"` (candidates).
   `N_CAND_TRAIN` / `N_CAND_TEST` cap the number of raw candidates per source (smoke runs).

`pool` (after the probe; reads `RUN_DIR/probe/*.jsonl`, rows `{"task": id, "c": bool, ...}`)
-> `RUN_DIR/data/{train,val,test}.jsonl` + `data_report.json`
1. `probe = {"n", "correct"}` per candidate. Train pool = train candidates with
   `correct >= KEEP_MIN_CORRECT`, plus a random `ZERO_FRAC` share (of the pool size) of the unsolved ones.
2. Test set = first `N_TEST` tasks of `CFG.TEST_TASKS` kept in file order when `N_TEST >= len` else
   an even mix of its sources; `split="test"`.
3. For every task of train + val + test: measure the references (up to `N_REF_KEEP`):
   `tr = fpstore._slim(sandbox.trace_program(task, ref))` on the full ladder (all ladders; pinned
   cores; `workers=C0.FP_WORKERS`), `valid = fpstore.valid_rungs(traces[:3])`,
   `fps = [FP.compute_all(ref, tr, valid)]`, `lad = FP.select_ladder(fps)`, `rungs = sorted(valid[lad])`,
   `ref_fp = [FP.pick(f, lad)]` (ok ones), `ref_out`, `ref_time` as defined in "Task format"
   (from the `out` / `t` fields of `runs` and `timing` on `(lad, size)`), `ref_groups`.
   Cache per task in a `JsonlCache` under `RUN_DIR/cache` (key: task id + sha of refs + ladder recipe)
   so a restart resumes. Tasks without references in the test file: `lad = None`.
4. If `NEED_LADDER`: drop train tasks with `lad is None` or fewer than 3 `rungs`.
5. `data_report.json`: counts at every step per source and kind, probe solve-rate histogram,
   share of tasks with a ladder, distribution of `ref_groups` (how many tasks have >= 2 human
   algorithm groups), decontamination counts.

`load_tasks(path) -> list[dict]`. `tests/test_data.py`: builds tasks from a small local jsonl
fixture in APPS format (write 3-4 tiny problems by hand: func and stdio), runs prep-like and
pool-like functions end to end on CPU (the functions must be callable with explicit paths /
in-memory rows so the test needs no network).

## Module C — `st/evaluate.py`, `st/grpo.py`, `st/orchestrate.py`, `st/report.py`, `run.sh`, `README.md`, `requirements.txt`, `tests/test_e2e.py`

Interfaces of modules A and B are binding; they are written in parallel by other engineers.

`st/evaluate.py`
- `evaluate(policy, tasks, m, seed, need_fp=True, desc="") -> (metrics: dict, rows: list[dict])`:
  for every task `N_SEEDS x m` rollouts (seed slots 0..N-1 also for modes none/base, where the slot
  is only a label), `prompts.extract_code`, `reward.score_programs(..., need_fp)`,
  `reward.group_reward(group, full=True)` per task (for the D/S numbers).
  Row: `task, seed, sample, code, text?, truncated, ntok, tests, c, measured, slow, ladder_fail, elig, D, S, R, fp (k1,k2,b only)`.
  Metrics (also a `per_task` list with what is needed for paired bootstraps):
  - `pass1` = mean c; `pass_seeds` = mean over tasks of `1 - prod_z (1 - cbar_z)` (one sample per
    seed); `pass_iid` = mean over tasks of `1 - C(n - n_c, N) / C(n, N)` (N pooled samples);
    `pass1_by_seed`;
  - `groups` = mean number of `reward.clusters` groups among eligible rollouts, over tasks with >= 2
    eligible; `groups_seed_draw` = expected number of distinct groups in a one-sample-per-seed draw
    (enumerate the `m^N` draws, or 500 random ones if more), over the same tasks;
  - `d_cross`, `d_same` = mean `soft(dist)` over eligible pairs of different / same seed; `gap = d_cross - d_same`;
  - monitors: `frac_trunc`, `mean_ntok`, among tests-passing: `frac_ladder_fail`, `frac_slow`,
    `frac_fp`; mean `b` (scaling exponent) of eligible.
- CLI (one GPU job): `python -m st.evaluate --out DIR --tasks FILE[,FILE] --policy base|PATH.pt --m M [--no_fp] [--shard I --nshards N] [--limit K]`.
  Writes `DIR/<taskfile stem>.json` (metrics), `DIR/<stem>.rows.jsonl.gz`, `DIR/<stem>.pairs.jsonl`
  (up to 50 random pairs of eligible codes of one task and different seeds with their distance and
  fingerprints: material for an offline reward-hacking audit), then `DIR/DONE`.
  The **probe** is this CLI: `--policy base --no_fp --m PROBE_N --shard i --nshards n` on
  `candidates.jsonl`, writing rows `{"task","c",...}` to `RUN_DIR/probe/shard{i}.jsonl`
  (add a flag for that output format). `PATH.pt` holds `{"state", "mode", "cfg"}`.

`st/grpo.py` — one training run on one GPU:
`python -m st.grpo --out DIR --mode film|prompt|none --reward full|correct --train FILE --val FILE [--steps S | --steps_file F] [--calib N] [--max_hours H]`
- Step t: `P_TASKS` tasks = consecutive slices of a per-epoch permutation seeded by
  `(TRAIN_SEED, epoch)` (the same tasks in the same order for every variant); per task
  `N_SEEDS x M_PER_SEED` rollouts with `sampler.rollout(seed = f(TRAIN_SEED, t))`;
  score with `reward.score_programs(need_fp = (reward == "full"))`; `reward.group_reward(group, full = reward == "full")`;
  `A = reward.advantages(R of the group)`; rollouts with `A == 0` are skipped in the backward pass;
  loss `= sum_i (A_i) * NLL_i / (n_rollouts_of_step * LEN_NORM)` via `sampler.backward_pg(coef = A_i / (n * LEN_NORM))`
  (minimizing it raises the log-probability of positive-advantage rollouts); `clip_grad_norm_(GRAD_CLIP)`;
  `AdamW(policy.param_groups(LR), betas=(0.9, 0.99), weight_decay=0)`; linear warmup `WARMUP` steps, then constant.
  One optimizer step per rollout batch (on-policy; no PPO ratio, no KL). If nothing has a
  non-zero advantage the optimizer step is skipped but the step counts.
- Logs: `steps.jsonl` (step, seconds of gen / tests+trace / backward, mean R, frac correct,
  frac groups with a non-zero advantage, mean D, mean S, frac eligible / slow / ladder_fail /
  truncated among the relevant sets, mean ntok, pass per seed, grad norm, lr, `policy.gain_stats()`),
  `rollouts.jsonl` (every `KEEP_ROLLOUTS_EVERY`-th step: step, task, seed, code, c, R, D, S, slow, fp keys),
  `evals.jsonl` (`evaluate(policy, val, EVAL_M)` at step 0, every `EVAL_EVERY` steps and at the end).
- Checkpoints: `last.pt` (`state`, optimizer, step, python / numpy / torch / cuda RNG states, cfg)
  at every eval and every `CKPT_MINUTES`; `best.pt` (highest val `pass_seeds`, ties -> later) and
  `final.pt` as `{"state","mode","cfg","step"}`; `result.json`; `DONE` marker (and remove `last.pt`).
  Resume from `last.pt`: jsonl logs are cut back to the resumed step and its rollouts are redrawn
  with the same seed. A run with `DONE` returns at once. `--max_hours`: stop gracefully (write
  `final.pt`, `result.json` says "stopped early").
- `--calib N`: run N steps + one validation on `min(len(val), 24)` tasks, write
  `calib.json {"sec_per_step", "sec_per_eval_task"}`, no checkpoints.

`st/orchestrate.py` — `python -m st.orchestrate` runs the whole launch in `CFG.RUN_DIR`, resumable
(every job has a `DONE` / output marker; a re-run skips finished jobs), one subprocess per job
(`start_new_session=True`, `CUDA_VISIBLE_DEVICES=<one id>`, `ST_CORES=<its cpu list>`, log
`RUN_DIR/logs/<job>.log` in append mode), `STATUS.md` rewritten every ~30 s (job table: state, GPU,
hours, last log line; plus the latest line of every `steps.jsonl` / `evals.jsonl`), `state.json`.
- GPUs: `CFG.GPUS` or every GPU with < 500 MiB used (`nvidia-smi --query-gpu=index,memory.used`); fail
  clearly if none. No CUDA at all (local test): run GPU jobs on CPU one at a time.
- CPU slices: split `exp0.physical_cores()` (bounded by `exp0.cpu_quota()`) between the jobs that
  run at the same time; training jobs with `reward=full` get weight 2.5, the others 1; at least
  2 physical cores each. CPU-only jobs get everything.
- Jobs: `model` (download) -> `prep` (`st.data prep`) -> `probe_i` on every GPU -> `pool`
  -> `calib_<v>` for every variant in parallel -> write `steps.json` (the same S for all:
  `clamp((TRAIN_HOURS * 3600 - evals * eval_sec) / (1.25 * max sec_per_step), STEPS_MIN, STEPS_MAX)`
  unless `CFG.STEPS > 0`) -> `train_<v>` (`CFG.VARIANTS`, priority order, as many at once as there
  are GPUs) -> `final_base` + `final_<v>` (`st.evaluate` on `val.jsonl,test.jsonl`, `EVAL_M_FINAL`,
  policy `final.pt`) -> `report`.
  A failed job marks its dependents as skipped; everything independent still runs; exit code != 0 if anything failed.
- Disk watchdog: every 2 min `du` of `seeds/train`; warn at 90 % of `DISK_LIMIT_GB`, above it kill
  all jobs and exit with a clear message. SIGTERM / Ctrl-C: kill the job process groups.

`st/report.py` -> `RUN_DIR/report.md`: data summary; per policy (base, each variant) on val and
test: pass1, pass_seeds, pass_iid, groups, groups_seed_draw, d_cross, d_same, gap, monitors;
paired bootstrap (1000 resamples over tasks) of `pass_seeds` and `groups_seed_draw` for every
variant vs `none_correct` and vs base, with 95 % CI; validation curves from `evals.jsonl`; training
curves summary (first / last 20 steps: reward, correct, D, S, slow share); a short "reward hacking
monitors" section (slow share, mean scaling exponent, mean tokens over training).

`run.sh` — the ONE command: `bash run.sh` (from `seeds/train`). Pattern of `Myres/run_phase1_grpo.sh`:
`set -euo pipefail`, cd to its folder, caches inside `train/.cache` (`HF_HOME`, `XDG_CACHE_HOME`,
`TORCH_HOME`, `HF_HUB_DISABLE_XET=1`, `HF_XET_CHUNK_CACHE_SIZE_BYTES=0`, `PIP_NO_CACHE_DIR=1`,
`TOKENIZERS_PARALLELISM=false`, `PYTHONUNBUFFERED=1`), `TMPDIR` on `/tmp`, choose python
(`$PYTHON`, else `python3` if it imports torch + transformers + requests + huggingface_hub with CUDA,
else create `train/.venv` with pip `--no-cache-dir` after checking the disk budget), preflight
(versions, GPUs, free disk, CPU count, `du` of train/), `flock` single-instance lock + pid file,
then a **foreground smoke run** (`SMOKE=1 RUN_NAME=smoke`, tiny sizes from config, deleted afterwards;
skipped if `runs/main/STATUS.md` exists or `SKIP_SMOKE=1`) and, only if it passes, the full run with
`nohup ... >> runs/main.log 2>&1 &`; print how to watch (`cat runs/main/STATUS.md`, `tail -f runs/main.log`),
stop (`kill $(cat runs/main.pid)`) and where the report will be. Re-running resumes. `FOREGROUND=1`
runs the full launch in the foreground.

`README.md` (Russian, short): what the experiment does, the one command, what each stage does and
how long, where results are, main knobs, how to resume, disk use.

`tests/test_e2e.py`: with `MODEL_TINY=1 SMOKE=1` on CPU and a tiny hand-made task file, run
`st.grpo` for 2 steps (the random model writes garbage, so also unit-test the step function with
injected "oracle" completions: monkeypatch `sampler.rollout` to return reference solutions /
variants so rewards, advantages, backward and optimizer step are exercised), kill-and-resume
equivalence of `last.pt`, and `st.evaluate` metrics on hand-made rows.
