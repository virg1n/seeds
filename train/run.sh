#!/usr/bin/env bash
# Seed training, one command:      bash run.sh
#   1) a short smoke run in the foreground (tiny sizes, real model, ~10-20 min); if it fails nothing else starts
#   2) the full launch in the background (~26-30 h on 4 GPUs): data -> probe -> calibration -> 4 trainings
#      -> final evaluation -> runs/main/report.md
# Re-running the same command resumes (finished jobs are skipped, trainings continue from their checkpoints).
#   SKIP_SMOKE=1 bash run.sh      no smoke run          FOREGROUND=1 bash run.sh   full launch in the foreground
#   GPUS=0,1 bash run.sh          use only these GPUs   TRAIN_HOURS=10 bash run.sh shorter training
# Everything (caches, weights, data, results) stays inside this folder, within DISK_LIMIT_GB (default 20).
set -euo pipefail
cd "$(dirname "$0")"
HERE="$(pwd)"

export HF_HOME="$HERE/.cache/hf"
export XDG_CACHE_HOME="$HERE/.cache"
export TORCH_HOME="$HERE/.cache/torch"
export MPLCONFIGDIR="$HERE/.cache/mpl"
export HF_HUB_DISABLE_XET=1
export HF_XET_CHUNK_CACHE_SIZE_BYTES=0
export HF_HUB_ENABLE_HF_TRANSFER=0
export PIP_NO_CACHE_DIR=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PYTHONUTF8=1
export DISK_LIMIT_GB="${DISK_LIMIT_GB:-20}"
export TMPDIR="${TMPDIR_BASE:-/tmp}/seedtrain_$(id -u)"
export ST_TMP="$TMPDIR"
mkdir -p "$TMPDIR" "$HF_HOME" runs

[ -f "$HERE/../exp0/src/harness.py" ] || { echo "[run.sh] ../exp0/src is missing: copy the whole seeds/ folder (exp0 + train)"; exit 1; }
[ -f "$HERE/../exp0/data/tasks_53d89291.jsonl" ] || { echo "[run.sh] ../exp0/data/tasks_53d89291.jsonl (held-out tasks) is missing"; exit 1; }

# ------------------------------------------------------------ python
CHECK='import torch, transformers, numpy, requests, huggingface_hub; assert torch.cuda.is_available()'
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if [ -x "$HERE/.venv/bin/python" ] && [ -f "$HERE/.venv/.installed" ]; then
    PY="$HERE/.venv/bin/python"
  elif python3 -c "$CHECK" > /dev/null 2>&1; then
    PY="$(command -v python3)"
  fi
fi
if [ -z "$PY" ]; then
  USED_GB=$(du -sk "$HERE" 2> /dev/null | awk '{printf "%d", $1/1048576}')
  if [ $((USED_GB + 13)) -gt "${DISK_LIMIT_GB%.*}" ]; then
    echo "[run.sh] python3 has no torch+transformers with CUDA, and a venv (~7 GB) does not fit the ${DISK_LIMIT_GB} GB budget"
    echo "         (this folder already uses ${USED_GB} GB). Set PYTHON=/path/to/python or raise DISK_LIMIT_GB."
    exit 1
  fi
  echo "[run.sh] python3 has no torch+transformers with CUDA: creating .venv (~7 GB) ..."
  python3 -m venv "$HERE/.venv"
  "$HERE/.venv/bin/pip" install -q --no-cache-dir --upgrade pip
  "$HERE/.venv/bin/pip" install --no-cache-dir -r requirements.txt
  touch "$HERE/.venv/.installed"
  PY="$HERE/.venv/bin/python"
fi
"$PY" -c "$CHECK" || { echo "[run.sh] $PY cannot import torch/transformers/requests/huggingface_hub with CUDA"; exit 1; }

# ------------------------------------------------------------ one instance
command -v flock > /dev/null || { echo "[run.sh] flock not found (package util-linux)"; exit 1; }
exec 9> runs/main.lock
flock -n 9 || { echo "[run.sh] the launch is already running (PID $(cat runs/main.pid 2> /dev/null)); stop it first: kill \$(cat runs/main.pid)"; exit 1; }

"$PY" - << 'PYEOF'
import os, shutil, subprocess, torch, transformers
print("[run.sh] torch", torch.__version__, "| transformers", transformers.__version__, "| CUDA GPUs", torch.cuda.device_count(),
      "| CPUs", os.cpu_count())
try:
    print(subprocess.run(["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total", "--format=csv,noheader"],
                         capture_output=True, text=True, timeout=60).stdout.strip())
except Exception as e:
    print("[run.sh] nvidia-smi:", e)
print(f"[run.sh] free disk as the OS reports it: {shutil.disk_usage('.').free / 1e9:.0f} GB; "
      f"budget for this folder: {os.environ['DISK_LIMIT_GB']} GB (expected peak ~10 GB)")
PYEOF
echo "[run.sh] this folder now uses $(du -sh "$HERE" 2> /dev/null | cut -f1)"

# ------------------------------------------------------------ smoke run
if [ "${SKIP_SMOKE:-0}" != "1" ] && [ ! -f runs/main/STATUS.md ]; then
  echo "== smoke run (tiny sizes, real model): runs/smoke, log runs/smoke.log"
  rm -rf runs/smoke
  if ! SMOKE=1 RUN_NAME=smoke "$PY" -m st.orchestrate 2>&1 | tee runs/smoke.log; then
    echo "== smoke run FAILED: see runs/smoke.log and runs/smoke/logs/*.log; the full launch was not started"
    exit 1
  fi
  [ -f runs/smoke/report.md ] && sed -n '1,60p' runs/smoke/report.md
  rm -rf runs/smoke          # the real launch needs the space
  echo "== smoke OK"
fi

# ------------------------------------------------------------ full launch
if [ "${FOREGROUND:-0}" = "1" ]; then
  echo $$ > runs/main.pid
  exec env RUN_NAME=main "$PY" -m st.orchestrate
fi
echo "== starting the full launch in the background"
RUN_NAME=main nohup "$PY" -m st.orchestrate >> runs/main.log 2>&1 &
echo $! > runs/main.pid
echo "PID $(cat runs/main.pid)"
echo "status:  cat $HERE/runs/main/STATUS.md"
echo "log:     tail -f $HERE/runs/main.log        (per job: runs/main/logs/<job>.log)"
echo "stop:    kill \$(cat $HERE/runs/main.pid)   (then  bash run.sh  resumes)"
echo "report:  $HERE/runs/main/report.md  (any time:  RUN_NAME=main $PY -m st.report)"
