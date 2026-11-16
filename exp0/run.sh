#!/usr/bin/env bash
# Experiment 0 — one command:   bash exp0/run.sh
#   quick end-to-end check:      SMOKE=1 bash exp0/run.sh
#   only some stages:            bash exp0/run.sh partA report
# Everything (venv, caches, models, data, results) stays inside exp0/ and is kept under
# DISK_LIMIT_GB (default 19). Model weights are deleted right after their generation stage.
set -euo pipefail
cd "$(dirname "$0")"
EXP="$(pwd)"

export HF_HOME="$EXP/.cache/hf"
export HF_HUB_DISABLE_XET=1            # no xet chunk cache (can silently use GBs)
export HF_HUB_ENABLE_HF_TRANSFER=0
export XDG_CACHE_HOME="$EXP/.cache"
export VLLM_CACHE_ROOT="$EXP/.cache/vllm"
export TRITON_CACHE_DIR="$EXP/.cache/triton"
export TORCHINDUCTOR_CACHE_DIR="$EXP/.cache/inductor"
export FLASHINFER_WORKSPACE_BASE="$EXP/.cache"
export TMPDIR="$EXP/.tmp"
export PIP_NO_CACHE_DIR=1
export UV_CACHE_DIR="$EXP/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$EXP/.cache/uv-python"   # uv-managed Python stays inside exp0 too
export PYTHONUNBUFFERED=1
export DISK_LIMIT_GB="${DISK_LIMIT_GB:-19}"
export TOKENIZERS_PARALLELISM=false
mkdir -p "$TMPDIR" "$HF_HOME" results

echo "[run.sh] free space: $(df -h "$EXP" | awk 'NR==2{print $4}')  (budget for exp0/: ${DISK_LIMIT_GB:-19} GB)"

# ------------------------------------------------------------ python environment
PY="${PYTHON:-}"
if [[ -z "$PY" ]]; then
  if [[ -x "$EXP/.venv/bin/python" && -f "$EXP/.venv/.installed" ]]; then
    PY="$EXP/.venv/bin/python"
  elif python3 -c "import vllm, sklearn, scipy, matplotlib" >/dev/null 2>&1; then
    PY="$(command -v python3)"
    echo "[run.sh] using system python with vLLM: $PY"
  fi
fi
if [[ -z "$PY" ]]; then
  FREE_GB=$(df -Pk "$EXP" | awk 'NR==2{printf "%d", $4/1048576}')
  USED_GB=$(du -sk "$EXP" 2>/dev/null | awk '{printf "%d", $1/1048576}')
  NEED_GB=${VENV_NEED_GB:-11}
  if (( FREE_GB < NEED_GB )) || (( USED_GB + NEED_GB > ${DISK_LIMIT_GB%.*} )); then
    echo "[run.sh] not enough disk for the venv: need ~${NEED_GB} GB, free ${FREE_GB} GB, exp0 uses ${USED_GB} GB"          "of the ${DISK_LIMIT_GB:-19} GB budget. Set PYTHON=/path/to/python with vllm installed, or free space."
    exit 1
  fi
  echo "[run.sh] creating venv in exp0/.venv (vLLM + torch, ~9 GB) ..."
  if command -v uv >/dev/null 2>&1; then UV=uv; else
    # uv itself is installed inside exp0 (no ~/.local writes)
    python3 -m pip install -q --no-cache-dir --target "$EXP/.cache/uvpkg" uv >/dev/null 2>&1 || true
    UV="$(ls "$EXP"/.cache/uvpkg/bin/uv 2>/dev/null || true)"
    [[ -x "$UV" ]] || UV=""
  fi
  if [[ -n "$UV" ]]; then
    "$UV" venv --python "${PY_VERSION:-3.12}" "$EXP/.venv"
    "$UV" pip install --python "$EXP/.venv/bin/python" -r requirements.txt
    if [[ "${VLLM_NIGHTLY:-0}" == "1" ]]; then
      "$UV" pip install --python "$EXP/.venv/bin/python" -U vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly
    fi
    "$UV" cache clean >/dev/null 2>&1 || true
  else
    python3 -m venv "$EXP/.venv"
    "$EXP/.venv/bin/pip" install -q --upgrade pip
    "$EXP/.venv/bin/pip" install -r requirements.txt
    if [[ "${VLLM_NIGHTLY:-0}" == "1" ]]; then
      "$EXP/.venv/bin/pip" install -U --pre vllm --extra-index-url https://wheels.vllm.ai/nightly
    fi
  fi
  touch "$EXP/.venv/.installed"
  PY="$EXP/.venv/bin/python"
  rm -rf "$EXP/.cache/uv" "$EXP/.cache/uvpkg" "$TMPDIR"/* 2>/dev/null || true
  echo "[run.sh] venv size: $(du -sh "$EXP/.venv" | cut -f1)"
fi
"$PY" -c "import vllm, transformers; print('[run.sh] vllm', vllm.__version__, '| transformers', transformers.__version__)" || true

# ------------------------------------------------------------ run
LOG="$EXP/results/run_$(date +%Y%m%d_%H%M%S).log"
[[ "${SMOKE:-0}" == "1" ]] && LOG="$EXP/results/run_smoke_$(date +%Y%m%d_%H%M%S).log"
echo "[run.sh] log: $LOG"
"$PY" -m src.pipeline "$@" 2>&1 | tee "$LOG"
exit "${PIPESTATUS[0]}"
