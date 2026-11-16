"""Central configuration. Every value can be overridden by an environment variable
of the same name (e.g. `N_MBPP=50 bash run.sh`)."""
from __future__ import annotations

import os
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parents[1]


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

# ---------------------------------------------------------------- paths
DATA_DIR = EXP_DIR / "data"
MODELS_DIR = EXP_DIR / "models"
TOOLS_DIR = EXP_DIR / "tools"
# RESULTS_NAME: separate results folder for a run with another main model (keeps earlier runs intact)
RESULTS_DIR = EXP_DIR / _env("RESULTS_NAME", "results_smoke" if SMOKE else "results")
CACHE_DIR = RESULTS_DIR / "cache"
GEN_DIR = RESULTS_DIR / "generations"
FIG_DIR = RESULTS_DIR / "figures"
LOG_DIR = RESULTS_DIR / "logs"
TMP_DIR = EXP_DIR / ".tmp"

# ---------------------------------------------------------------- storage
DISK_LIMIT_GB = _env("DISK_LIMIT_GB", 19.0, float)     # hard budget for everything under exp0/
KEEP_MODELS = _env("KEEP_MODELS", False, bool)        # delete weights right after their generation stage

# ---------------------------------------------------------------- data
N_MBPP = _env("N_MBPP", 6 if SMOKE else 200, int)
N_APPS = _env("N_APPS", 6 if SMOKE else 200, int)
MAX_TESTS = _env("MAX_TESTS", 30, int)                # tests kept per task (APPS)
MBPP_SOURCE = _env("MBPP_SOURCE", "plus")              # plus = MBPP+ (EvalPlus, ~100x more tests) | orig
MAX_HUMAN = _env("MAX_HUMAN", 16, int)                # human (APPS) solutions kept per task
SEED = _env("SEED", 1234, int)

# ---------------------------------------------------------------- models
MAIN_MODEL = _env("MAIN_MODEL", "Qwen/Qwen3.5-2B")
# extra models for the "union of models" ceiling (part C); main model is always included
EXTRA_MODELS = _env("EXTRA_MODELS", ["Qwen/Qwen3.5-0.8B"] if SMOKE else
                    ["Qwen/Qwen3.5-0.8B", "Qwen/Qwen2.5-Coder-1.5B-Instruct"], list)
EMBED_MODELS = _env("EMBED_MODELS", ["Qwen/Qwen3-Embedding-0.6B", "microsoft/unixcoder-base"], list)

NUM_GPUS = _env("NUM_GPUS", 0, int)                  # 0 = all visible GPUs
GPU_IDS = _env("GPU_IDS", [], list)                   # explicit physical GPU ids, e.g. 0,1,2,5 (overrides NUM_GPUS)
# auto: bfloat16 on Ampere+ (compute capability >= 8.0), float16 on older GPUs such as V100
DTYPE = _env("DTYPE", "auto")
GPU_MEM_UTIL = _env("GPU_MEM_UTIL", 0.85, float)
MAX_MODEL_LEN = _env("MAX_MODEL_LEN", 8192, int)
BACKEND = _env("BACKEND", "vllm")                     # vllm | hf
HF_FALLBACK = _env("HF_FALLBACK", True, bool)
HF_BATCH = _env("HF_BATCH", 128, int)                 # sequences per generate() call (HF backend)
HF_TOKEN_BUDGET = _env("HF_TOKEN_BUDGET", 128 * 2048, int)         # if vLLM cannot start: retry with HF in fresh processes
GEN_TIMEOUT_H = _env("GEN_TIMEOUT_H", 8.0, float)     # hard deadline per model

# ---------------------------------------------------------------- sampling
N_SAMPLES = _env("N_SAMPLES", 4 if SMOKE else 16, int)          # plain sampling, per task
N_STRATEGIES = _env("N_STRATEGIES", 4, int)                      # "Strategy 1..4"
N_PER_STRATEGY = _env("N_PER_STRATEGY", 2 if SMOKE else 16, int)
N_CHAINS = _env("N_CHAINS", 1 if SMOKE else 2, int)              # "solve differently" chains per task
CHAIN_LEN = _env("CHAIN_LEN", 4 if SMOKE else 16, int)
CHAIN_SHOW = _env("CHAIN_SHOW", 6, int)                          # previous solutions shown in prompt
TEMPERATURE = _env("TEMPERATURE", 1.0, float)                  # main temperature (all conditions)
# temperature sweep for plain sampling of the main model ("does temperature alone give diversity?")
EXTRA_TEMPS = _env("EXTRA_TEMPS", [] if SMOKE else ["0.7", "1.3"], list)
TOP_P = _env("TOP_P", 0.95, float)
TOP_K = _env("TOP_K", 20, int)
MAX_TOKENS = _env("MAX_TOKENS", 1536, int)
KS = [k for k in ([1, 4, 8, 16] if not SMOKE else [1, 2, 4])
      if k <= min(N_SAMPLES, N_STRATEGIES * N_PER_STRATEGY, CHAIN_LEN)]  # never report k beyond the pool

# ---------------------------------------------------------------- sandbox / tracer
def _ram_gb():
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / 1e6
    except OSError:
        pass
    return 32.0


N_REF_CHECK = _env("N_REF_CHECK", 3, int)            # reference solutions used to validate ladder rungs
MEM_LIMIT_MB = _env("MEM_LIMIT_MB", 3072, int)       # address-space limit per sandboxed program
# concurrency bounded by CPUs and by RAM: even if every program used its full limit at once,
# the sandboxes stay within ~60% of RAM (e.g. 100 GB -> 20 workers of 3 GB)
WORKERS = _env("WORKERS", max(2, min(64, (os.cpu_count() or 8) - 4, int(0.6 * _ram_gb() * 1024 / MEM_LIMIT_MB))), int)
TEST_TIMEOUT = _env("TEST_TIMEOUT", 4.0, float)        # per test case
TRACE_MAX_EVENTS = _env("TRACE_MAX_EVENTS", 1_500_000, int)   # line events cap per traced run
TRACE_RUN_TIMEOUT = _env("TRACE_RUN_TIMEOUT", 8.0, float)
TIMING_RUN_LIMIT = _env("TIMING_RUN_LIMIT", 1.0, float)       # stop untraced timing ladder past this (s)
# Growth factors of the input ladders. The traced ladder stops at the line-event cap; the larger
# factors are reached by the untraced timing runs only (they expose work hidden in C builtins such
# as min(...), set(...), list concatenation). Ladders stop earlier when inputs would exceed
# scaler.MAX_ELEMS elements or integers 1e7.
LADDER_FACTORS = [2 ** k for k in range(0, 18)]
# fingerprinting runs timing measurements: fewer parallel jobs, each pinned to its own CPU core,
# keeps timing noise down on a busy server
FP_WORKERS = _env("FP_WORKERS", max(2, min(WORKERS, (os.cpu_count() or 8) // 2 - 2)), int)

# ---------------------------------------------------------------- fingerprint distance
# d_phi = w1*d1 + w2*d2 + w3*d3 with weights FIXED IN ADVANCE ("large / medium / small" for
# scaling / scheme / primitives), not fitted on the evaluation pairs.
W_PHI = tuple(float(x) for x in _env("W_PHI", ["0.6", "0.25", "0.15"], list))
