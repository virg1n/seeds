"""Settings of the seed-training experiment. Every value can be overridden by an environment
variable of the same name (e.g. `P_TASKS=4 bash run.sh`). SMOKE=1 shrinks everything to a
few-minute end-to-end check."""
from __future__ import annotations

import os
from pathlib import Path

TRAIN_DIR = Path(__file__).resolve().parents[1]          # seeds/train
SEEDS_DIR = TRAIN_DIR.parent                             # seeds
EXP0_DIR = SEEDS_DIR / "exp0"


def _env(name, default, cast=str):
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    if cast is bool:
        return v.lower() in ("1", "true", "yes", "y")
    if cast is list:
        return [x.strip() for x in v.split(",") if x.strip()]
    return cast(v)


SMOKE = _env("SMOKE", False, bool)

# ---------------------------------------------------------------- paths / storage
RUN_NAME = _env("RUN_NAME", "smoke" if SMOKE else "main")
RUNS_DIR = TRAIN_DIR / "runs"
RUN_DIR = RUNS_DIR / RUN_NAME                            # everything one launch produces
DATA_DIR = TRAIN_DIR / "data"                            # raw dataset caches (shared by launches)
MODELS_DIR = TRAIN_DIR / "models"
DISK_LIMIT_GB = _env("DISK_LIMIT_GB", 20.0, float)       # budget for everything under seeds/train
TEST_TASKS = Path(_env("TEST_TASKS", str(EXP0_DIR / "data" / "tasks_53d89291.jsonl")))  # held-out (exp0)

# ---------------------------------------------------------------- model
MODEL = _env("MODEL", "Qwen/Qwen2.5-Coder-1.5B-Instruct")
LORA_R = _env("LORA_R", 32, int)
LORA_ALPHA = _env("LORA_ALPHA", 64, int)
LORA_TARGETS = _env("LORA_TARGETS", ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"], list)

# ---------------------------------------------------------------- seeds
N_SEEDS = _env("N_SEEDS", 4, int)                        # fixed seeds 0..N-1
SEED_DIM = _env("SEED_DIM", 64, int)                     # e_z = fixed N(0, I) vector drawn from the integer seed
FILM_HIDDEN = _env("FILM_HIDDEN", 256, int)
FILM_RANK = _env("FILM_RANK", 64, int)                   # per-layer gains live in a rank-r subspace
FILM_LAYERS = _env("FILM_LAYERS", "all")                 # "all" or "a-b" (inclusive layer indices)
FILM_MAX = _env("FILM_MAX", 1.0, float)                  # gain = 1 + FILM_MAX * tanh(delta / FILM_MAX)  in (0, 2)
FILM_INIT = _env("FILM_INIT", 0.0, float)                # std of the initial delta (0: start exactly at the base model)

# ---------------------------------------------------------------- data
MIN_TESTS = _env("MIN_TESTS", 5, int)                    # APPS-train problems need at least this many tests
MAX_TESTS = _env("MAX_TESTS", 20, int)                   # tests kept per task
MAX_TEST_CHARS = _env("MAX_TEST_CHARS", 100_000, int)    # tests with a larger input are dropped
N_REF_KEEP = _env("N_REF_KEEP", 6, int)                  # validated reference solutions kept per task
N_REF_TRY = _env("N_REF_TRY", 12, int)
MAX_PROMPT_TOKENS = _env("MAX_PROMPT_TOKENS", 1200, int)
USE_APPS_TEST_REST = _env("USE_APPS_TEST_REST", True, bool)   # APPS-test introductory problems NOT in the exp0 eval set
N_CAND_TRAIN = _env("N_CAND_TRAIN", 16 if SMOKE else 100000, int)   # candidates taken from APPS-train introductory
N_CAND_TEST = _env("N_CAND_TEST", 8 if SMOKE else 100000, int)      # candidates taken from the APPS-test rest
N_VAL = _env("N_VAL", 6 if SMOKE else 150, int)          # in-distribution validation tasks (chosen before the probe)
N_TEST = _env("N_TEST", 8 if SMOKE else 400, int)        # tasks of TEST_TASKS used in the final evaluation
PROBE_N = _env("PROBE_N", 2 if SMOKE else 8, int)        # base-model samples per candidate task
KEEP_MIN_CORRECT = _env("KEEP_MIN_CORRECT", 0 if SMOKE else 1, int)  # probe: train tasks need >= this many correct
ZERO_FRAC = _env("ZERO_FRAC", 0.1, float)                # share of unsolved-in-probe tasks added to the train pool
NEED_LADDER = _env("NEED_LADDER", not SMOKE, bool)       # train tasks must have a measurable ladder
DATA_SEED = _env("DATA_SEED", 1234, int)

# ---------------------------------------------------------------- sampling (rollouts AND evaluation)
TEMPERATURE = _env("TEMPERATURE", 1.0, float)            # the loss differentiates log pi: sample from pi itself
TOP_P = _env("TOP_P", 1.0, float)
TOP_K = _env("TOP_K", 0, int)
MAX_TOKENS = _env("MAX_TOKENS", 384 if SMOKE else 768, int)
GEN_BATCH = _env("GEN_BATCH", 256, int)                  # rows per generate() call (halved automatically on OOM)
GEN_TOKENS = _env("GEN_TOKENS", 400_000, int)            # rows * (longest prompt + MAX_TOKENS) per call

# ---------------------------------------------------------------- GRPO
P_TASKS = _env("P_TASKS", 2 if SMOKE else 8, int)        # tasks per optimizer step
M_PER_SEED = _env("M_PER_SEED", 2 if SMOKE else 4, int)  # rollouts per (task, seed): group = N_SEEDS * M_PER_SEED
STEPS = _env("STEPS", 0, int)                            # 0: from the calibration, to fit TRAIN_HOURS
STEPS_MAX = _env("STEPS_MAX", 2 if SMOKE else 600, int)
STEPS_MIN = _env("STEPS_MIN", 2 if SMOKE else 100, int)
TRAIN_HOURS = _env("TRAIN_HOURS", 0.5 if SMOKE else 19.0, float)
CALIB_STEPS = _env("CALIB_STEPS", 1 if SMOKE else 3, int)
LR = _env("LR", 5e-5, float)                             # LoRA
FILM_LR_RATIO = _env("FILM_LR_RATIO", 4.0, float)        # seed modulator LR / LoRA LR
WARMUP = _env("WARMUP", 10, int)
GRAD_CLIP = _env("GRAD_CLIP", 1.0, float)
MB_TOKENS = _env("MB_TOKENS", 12288, int)                # padded tokens per training micro-batch
LEN_NORM = _env("LEN_NORM", 200.0, float)                # loss = -sum_i A_i sum_t log pi / (n_rollouts * LEN_NORM)
STD_FLOOR = _env("STD_FLOOR", 0.1, float)                # A_i = (R_i - mean) / max(std, STD_FLOOR)
TRAIN_SEED = _env("TRAIN_SEED", 0, int)
CKPT_MINUTES = _env("CKPT_MINUTES", 20.0, float)
EVAL_EVERY = _env("EVAL_EVERY", 1 if SMOKE else 50, int)  # validation every this many steps (and at step 0 and at the end)
EVAL_M = _env("EVAL_M", 1 if SMOKE else 2, int)          # samples per (task, seed) in validation
EVAL_M_FINAL = _env("EVAL_M_FINAL", 1 if SMOKE else 4, int)
KEEP_ROLLOUTS_EVERY = _env("KEEP_ROLLOUTS_EVERY", 1 if SMOKE else 10, int)  # texts of every n-th step

# ---------------------------------------------------------------- reward
# R_i = c_i * (1 + LAMBDA * D_i + GAMMA * S_i)      (see st/reward.py)
LAMBDA = _env("LAMBDA", 1.0, float)                      # weight of D: distance to correct solutions of OTHER seeds
GAMMA = _env("GAMMA", 0.5, float)                        # weight of S: agreement with correct solutions of the SAME seed
W_D = tuple(float(x) for x in _env("W_D", ["0.6", "0.25", "0.0"], list))   # weights of L1 / L2 / L3 (L3 off: gameable)
DEADZONE = _env("DEADZONE", 0.1, float)                  # distances below this count as "the same algorithm"
TAU = _env("TAU", 0.3, float)                            # (reports only) two solutions are one group if d <= TAU
LADDER_CHECK = _env("LADDER_CHECK", True, bool)          # outputs on scaled inputs must match the references
# "too slow" (mild efficiency gate): only solutions MUCH slower than the slowest reference lose the
# diversity bonus; they keep the reward for correctness.
SLOW_FACTOR = _env("SLOW_FACTOR", 20.0, float)           # slower than SLOW_FACTOR x the slowest reference ...
SLOW_FLOOR = _env("SLOW_FLOOR", 0.05, float)             # ... and slower than this many seconds ...
SLOW_MAX_SCALE = _env("SLOW_MAX_SCALE", 64, int)         # ... on an input at most this many times the test input

# ---------------------------------------------------------------- sandbox
TEST_TIMEOUT = _env("TEST_TIMEOUT", 4.0, float)
MEM_LIMIT_MB = _env("MEM_LIMIT_MB", 3072, int)

# ---------------------------------------------------------------- orchestration
HOURS = _env("HOURS", 0.5 if SMOKE else 30.0, float)     # soft budget of the whole launch
GPUS = _env("GPUS", [], list)                            # physical GPU ids; empty = every GPU with < 500 MiB used
# name:mode:reward, in priority order (with fewer free GPUs the first ones run first)
VARIANTS = _env("VARIANTS", ["film_full:film:full", "none_correct:none:correct"] if SMOKE else
                ["film_full:film:full", "none_correct:none:correct", "prompt_full:prompt:full",
                 "film_correct:film:correct"], list)
