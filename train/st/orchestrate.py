"""The whole launch in CFG.RUN_DIR:   python -m st.orchestrate      (resumable: re-run the same command)

  model   download the weights once (~3.1 GB)
  prep    candidates: APPS problems -> tasks, references validated, validation split   (CPU)
  probe   base model, PROBE_N samples per candidate, tests only                         (every GPU)
  pool    train pool = candidates the base model can solve; reference measurements      (CPU)
  calib   a few steps of every variant at once -> the number of steps S that fits TRAIN_HOURS
  train   one GRPO run per variant, one GPU each, the same S and the same tasks
  final   base model and every variant on val + held-out test
  report  RUN_DIR/report.md

Every job is a subprocess with its own GPU (CUDA_VISIBLE_DEVICES) and its own CPU cores (ST_CORES),
a log in RUN_DIR/logs/<job>.log and an output marker; finished jobs are skipped on a re-run.
STATUS.md shows the state. A failed job is retried once; what depends on it is skipped."""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from . import config as CFG

RUN = CFG.RUN_DIR
LOGS = RUN / "logs"
POSIX = os.name == "posix"
CORE_W_FULL = CFG._env("CORE_W_FULL", 2.5, float)       # CPU share of a run that traces every correct rollout
STATUS_EVERY, DISK_EVERY = 30.0, 120.0
T0 = time.time()
STATE = {"jobs": {}, "started": time.strftime("%Y-%m-%d %H:%M:%S"), "notes": []}
PROCS = {}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def note(msg):
    log(msg)
    STATE["notes"].append(time.strftime("%H:%M ") + msg)


# ------------------------------------------------------------------ resources
def find_gpus():
    """Physical GPU ids to use: CFG.GPUS, else every GPU with < 500 MiB in use; [None] = no CUDA (CPU)."""
    if CFG.GPUS:
        return [str(g) for g in CFG.GPUS]
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return [None]
    free = []
    for line in out.splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) == 2 and p[0].isdigit() and p[1].isdigit() and int(p[1]) < 500:
            free.append(p[0])
    return free or [None]


def core_slices(weights):
    """Splits the physical cores of this process between len(weights) jobs, proportionally to the
    weights (at least one core each). Returns a list of ST_CORES strings ("" = no restriction)."""
    from . import exp0
    groups = exp0.physical_cores()
    quota = exp0.cpu_quota()
    if quota:  # a container limit below the visible CPUs: use only that many
        keep, n = [], 0
        for g in groups:
            if n + len(g) > quota and keep:
                break
            keep.append(g)
            n += len(g)
        groups = keep
    k = len(weights)
    if not hasattr(os, "sched_setaffinity") or len(groups) < k:
        return [""] * k
    tot = float(sum(weights))
    cnt = [max(1, int(len(groups) * w / tot)) for w in weights]
    while sum(cnt) > len(groups):
        cnt[cnt.index(max(cnt))] -= 1
    i = 0
    while sum(cnt) < len(groups):  # leftovers to the heaviest jobs first
        cnt[sorted(range(k), key=lambda j: -weights[j])[i % k]] += 1
        i += 1
    out, pos = [], 0
    for c in cnt:
        out.append(",".join(str(x) for g in groups[pos:pos + c] for x in g))
        pos += c
    return out


def dir_gb(p):
    tot = 0
    for root, _, files in os.walk(p, onerror=lambda e: None):
        for f in files:
            try:
                fp = os.path.join(root, f)
                if not os.path.islink(fp):
                    tot += os.path.getsize(fp)
            except OSError:
                pass
    return tot / 1e9


# ------------------------------------------------------------------ jobs
class Job:
    def __init__(self, name, args, marker, gpu=True, weight=1.0, env=None):
        self.name, self.args, self.marker, self.gpu, self.weight = name, args, Path(marker), gpu, weight
        self.env = env or {}

    def done(self):
        return self.marker.exists()


def _last_line(path):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4000))
            lines = [x for x in f.read().decode("utf-8", "replace").splitlines() if x.strip()]
        return lines[-1][:150] if lines else ""
    except OSError:
        return ""


def write_status():
    lines = [f"# {CFG.RUN_NAME}: seed training", "",
             f"started {STATE['started']}, running {(time.time() - T0) / 3600:.2f} h, updated {time.strftime('%H:%M:%S')}",
             "", "| job | state | GPU | hours | last log line |", "|---|---|---|---|---|"]
    for n, j in STATE["jobs"].items():
        end = j.get("end") or time.time()
        hrs = f"{(end - j['start']) / 3600:.2f}" if j.get("start") else ""
        lines.append(f"| {n} | {j['state']} | {j.get('gpu', '')} | {hrs} | {_last_line(LOGS / (n + '.log')).replace('|', '/')} |")
    for d in sorted((RUN / "train").glob("*")) if (RUN / "train").exists() else []:
        for f in ("steps.jsonl", "evals.jsonl"):
            ln = _last_line(d / f)
            if ln:
                try:
                    r = json.loads(open(d / f, encoding="utf-8").read().strip().splitlines()[-1])
                    keys = ("step", "R", "correct", "D", "S", "frac_slow") if f[0] == "s" else \
                        ("step", "pass1", "pass_seeds", "pass_iid", "groups_draw_all", "gap")
                    ln = ", ".join(f"{k} {r[k]:.3f}" if isinstance(r.get(k), float) else f"{k} {r.get(k)}" for k in keys)
                except Exception:  # noqa
                    pass
                lines.append(f"\n- `{d.name}/{f}`: {ln}")
    if STATE["notes"]:
        lines += ["", "## notes"] + [f"- {x}" for x in STATE["notes"][-30:]]
    RUN.mkdir(parents=True, exist_ok=True)
    for path, text in ((RUN / "STATUS.md", "\n".join(lines) + "\n"), (RUN / "state.json", json.dumps(STATE, indent=1))):
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)


def kill_all():
    for p in list(PROCS.values()):
        try:
            if POSIX:
                os.killpg(p.pid, signal.SIGTERM)
            else:
                p.terminate()
        except (OSError, ProcessLookupError):
            pass
    t = time.time()
    while any(p.poll() is None for p in PROCS.values()) and time.time() - t < 20:
        time.sleep(0.5)
    for p in PROCS.values():
        if p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGKILL) if POSIX else p.kill()
            except (OSError, ProcessLookupError):
                pass


def _start(job, gpu, cores):
    LOGS.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONUNBUFFERED="1", TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="2",
               MKL_NUM_THREADS="2", RUN_NAME=CFG.RUN_NAME, **job.env)
    env["CUDA_VISIBLE_DEVICES"] = "" if (gpu is None or not job.gpu) else str(gpu)
    env.pop("ST_CORES", None)
    if cores:
        env["ST_CORES"] = cores
    cmd = [sys.executable] + job.args
    lf = open(LOGS / f"{job.name}.log", "a", encoding="utf-8")
    lf.write(f"\n### {time.strftime('%Y-%m-%d %H:%M:%S')} gpu={gpu} cores={cores or 'all'} :: {' '.join(cmd)}\n")
    lf.flush()
    p = subprocess.Popen(cmd, cwd=str(CFG.TRAIN_DIR), env=env, stdout=lf, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, start_new_session=POSIX)
    p._logfile = lf
    return p


def run_wave(title, jobs, gpus, retries=1):
    """Runs the jobs (skipping finished ones), GPU jobs on at most len(gpus) slots at once, CPU jobs
    one at a time with every core. Returns {name: ok}."""
    res = {}
    for j in jobs:
        st = STATE["jobs"].setdefault(j.name, {"state": "pending"})
        if j.done():
            st["state"] = "done" if st.get("start") else "done (earlier run)"
            res[j.name] = True
    todo = [j for j in jobs if j.name not in res]
    if not todo:
        write_status()
        return res
    log(f"== {title}: {', '.join(j.name for j in todo)}")
    gpu_jobs = [j for j in todo if j.gpu]
    slots = gpus if gpu_jobs else [None]
    n_slots = min(len(slots), len(todo)) if gpu_jobs else 1
    if gpu_jobs and gpus == [None]:
        n_slots = 1
    first = todo[:n_slots]
    slices = core_slices([j.weight for j in first]) if (gpu_jobs and n_slots > 1) else [""] * n_slots
    free = list(range(n_slots))
    queue, running, tries = list(todo), {}, {}
    t_status = t_disk = 0.0
    while queue or running:
        while queue and free:
            j, s = queue.pop(0), free.pop(0)
            p = _start(j, slots[s] if gpu_jobs else None, slices[s])
            PROCS[j.name] = p
            running[j.name] = (j, p, s)
            STATE["jobs"][j.name].update(state="running", gpu=slots[s] if j.gpu else "cpu", start=time.time(), end=None)
            log(f"started {j.name} (gpu {slots[s] if j.gpu else '-'}, cores {slices[s] or 'all'})")
        time.sleep(2.0)
        for name, (j, p, s) in list(running.items()):
            rc = p.poll()
            if rc is None:
                continue
            p._logfile.close()
            del running[name], PROCS[name]
            free.append(s)
            ok = rc == 0 and j.done()
            if not ok and tries.get(name, 0) < retries:
                tries[name] = tries.get(name, 0) + 1
                note(f"{name} failed (exit code {rc}); retrying")
                queue.insert(0, j)
                continue
            res[name] = ok
            STATE["jobs"][name].update(state="done" if ok else f"FAILED (exit code {rc})", end=time.time())
            (log if ok else note)(f"{name} {'finished' if ok else 'FAILED, see logs/' + name + '.log'}")
        now = time.time()
        if now - t_status > STATUS_EVERY:
            t_status = now
            write_status()
        if now - t_disk > DISK_EVERY:
            t_disk = now
            used = dir_gb(CFG.TRAIN_DIR)
            if used > CFG.DISK_LIMIT_GB:
                note(f"ABORT: {CFG.TRAIN_DIR} uses {used:.1f} GB, over the {CFG.DISK_LIMIT_GB} GB budget")
                kill_all()
                write_status()
                raise SystemExit(5)
            if used > 0.9 * CFG.DISK_LIMIT_GB:
                log(f"WARNING: disk {used:.1f} GB of the {CFG.DISK_LIMIT_GB} GB budget")
    write_status()
    return res


# ------------------------------------------------------------------ the launch
def variants():
    out = []
    for v in CFG.VARIANTS:
        name, mode, rew = v.split(":")
        out.append({"name": name, "mode": mode, "reward": rew, "weight": CORE_W_FULL if rew == "full" else 1.0})
    return out


def choose_steps(calibs, n_val):
    """The same number of steps for every variant: the slowest calibrated one fits TRAIN_HOURS."""
    if CFG.STEPS > 0:
        return CFG.STEPS, "STEPS is set"
    sec_step = max(c["sec_per_step"] for c in calibs.values())
    sec_eval = max(c["sec_per_eval_task"] for c in calibs.values()) * n_val
    budget = CFG.TRAIN_HOURS * 3600
    S = budget / (1.25 * sec_step)
    for _ in range(5):
        S = (budget - (S // CFG.EVAL_EVERY + 2) * sec_eval) / (1.25 * sec_step)
    S = int(max(CFG.STEPS_MIN, min(CFG.STEPS_MAX, S)))
    return S, f"{sec_step:.0f} s/step (slowest variant), {sec_eval:.0f} s per validation, {CFG.TRAIN_HOURS} h"


def main():
    RUN.mkdir(parents=True, exist_ok=True)
    gpus = find_gpus()
    py_m = ["-m"]
    data_dir, tr_dir = RUN / "data", RUN / "train"
    log(f"run {RUN}, GPUs {gpus}, variants {[v['name'] for v in variants()]}, budget {CFG.HOURS} h")
    if gpus == [None]:
        note("no free CUDA GPU found: GPU jobs run on the CPU one at a time (only sensible for smoke tests)")
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: (note("interrupted: stopping the jobs"), kill_all(), write_status(), os._exit(130)))
    failed = []

    def wave(title, jobs, fatal=False, **kw):
        res = run_wave(title, jobs, gpus, **kw)
        bad = [n for n, ok in res.items() if not ok]
        failed.extend(bad)
        if bad and fatal:
            note(f"cannot continue without {bad}")
            write_status()
            raise SystemExit(2)
        return res

    # ---- model, candidates, probe, pool
    tiny = CFG._env("MODEL_TINY", False, bool)
    wave("model", [Job("model", ["-c", "from st.model import model_path; print(model_path())"],
                       RUN / "model.ok" if tiny else CFG.MODELS_DIR / CFG.MODEL.replace("/", "--") / ".complete",
                       gpu=False)] if not tiny else [], fatal=True)
    wave("prep", [Job("prep", py_m + ["st.data", "prep"], data_dir / "candidates.jsonl", gpu=False)], fatal=True)
    nf = RUN / "probe" / "nshards.txt"       # a resumed launch may see another number of free GPUs
    n = int(nf.read_text()) if nf.exists() else len(gpus)
    nf.parent.mkdir(parents=True, exist_ok=True)
    nf.write_text(str(n))
    pm = max(1, CFG.PROBE_N // CFG.N_SEEDS)
    wave("probe", [Job(f"probe_{i}", py_m + ["st.evaluate", "--out", str(RUN / "probe_jobs" / f"shard{i}"),
                                              "--tasks", str(data_dir / "candidates.jsonl"), "--policy", "base",
                                              "--m", str(pm), "--no_fp", "--shard", str(i), "--nshards", str(n),
                                              "--probe_out", str(RUN / "probe" / f"shard{i}.jsonl")],
                       RUN / "probe_jobs" / f"shard{i}" / "DONE") for i in range(n)], fatal=True)
    wave("pool", [Job("pool", py_m + ["st.data", "pool"], data_dir / "data_report.json", gpu=False)], fatal=True)
    train_f, val_f, test_f = (str(data_dir / f"{s}.jsonl") for s in ("train", "val", "test"))
    n_train = sum(1 for _ in open(train_f, encoding="utf-8"))
    n_val = sum(1 for _ in open(val_f, encoding="utf-8"))
    if n_train < CFG.P_TASKS:
        note(f"only {n_train} training tasks (need >= P_TASKS = {CFG.P_TASKS}): cannot train")
        write_status()
        raise SystemExit(2)
    log(f"data: {n_train} train, {n_val} val tasks")

    # ---- calibration -> steps.json
    vs = variants()
    steps_f = RUN / "steps.json"
    if not steps_f.exists():
        def grpo(v, out, extra):
            return py_m + ["st.grpo", "--out", str(out), "--mode", v["mode"], "--reward", v["reward"],
                           "--train", train_f, "--val", val_f] + extra

        if CFG.STEPS <= 0:
            res = wave("calibration", [Job(f"calib_{v['name']}", grpo(v, RUN / "calib" / v["name"],
                                                                      ["--calib", str(CFG.CALIB_STEPS)]),
                                           RUN / "calib" / v["name"] / "calib.json", weight=v["weight"]) for v in vs])
            vs = [v for v in vs if res.get(f"calib_{v['name']}")]
            if not vs:
                note("every calibration failed")
                write_status()
                raise SystemExit(2)
        calibs = {v["name"]: json.load(open(RUN / "calib" / v["name"] / "calib.json", encoding="utf-8"))
                  for v in vs} if CFG.STEPS <= 0 else {}
        S, why = choose_steps(calibs, n_val)
        tmp = steps_f.with_name("steps.json.tmp")
        tmp.write_text(json.dumps({"steps": S, "why": why, "calib": calibs}, indent=1), encoding="utf-8")
        os.replace(tmp, steps_f)
        shutil.rmtree(RUN / "calib", ignore_errors=True)
        note(f"steps per variant: {S} ({why})")
    S = json.load(open(steps_f, encoding="utf-8"))["steps"]

    # ---- training
    res = wave("training", [Job(f"train_{v['name']}", py_m + [
        "st.grpo", "--out", str(tr_dir / v["name"]), "--mode", v["mode"], "--reward", v["reward"], "--train", train_f,
        "--val", val_f, "--steps_file", str(steps_f), "--max_hours", str(round(1.3 * CFG.TRAIN_HOURS, 2))],
        tr_dir / v["name"] / "DONE", weight=v["weight"]) for v in vs])
    trained = [v for v in vs if res.get(f"train_{v['name']}") and (tr_dir / v["name"] / "final.pt").exists()]

    # ---- final evaluation + report
    def final(name, policy):
        return Job(f"final_{name}", py_m + ["st.evaluate", "--out", str(RUN / "final" / name), "--tasks",
                                           f"{val_f},{test_f}", "--policy", policy, "--m", str(CFG.EVAL_M_FINAL)],
                   RUN / "final" / name / "DONE")

    wave("final evaluation", [final(v["name"], str(tr_dir / v["name"] / "final.pt")) for v in trained] +
         [final("base", "base")])
    try:
        from . import report
        report.main()
    except Exception as e:  # noqa
        note(f"report failed: {e!r}")
        failed.append("report")
    write_status()
    log(f"finished in {(time.time() - T0) / 3600:.2f} h; " + (f"FAILED: {failed}" if failed else "everything ok") +
        f"; report: {RUN / 'report.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
