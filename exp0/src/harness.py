"""Sandbox child process. STANDALONE: stdlib only, imports nothing from the project.

Protocol: reads one JSON job from stdin, writes one JSON result to the original stdout fd.
The untrusted program never sees the real stdin/stdout/stderr (they are /dev/null) and runs
with rlimits (address space, CPU, file size), destructive os/shutil/subprocess functions disabled,
and a wall-clock timeout per run (each run happens in a thread with a large stack so deep
recursion does not crash the interpreter).

mode = "test":  run tests, stop at first failure.
mode = "trace": run the program on a ladder of inputs of growing size under sys.settrace /
                sys.setprofile and collect execution statistics, then time untraced runs.
"""
import builtins
import collections
import io
import json
import math
import os
import sys
import threading
import time
import types

SOL = "<solution>"
_real_open = builtins.open
_real_os_open = os.open
_write = os.write
_CWD = os.path.realpath(os.getcwd())
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_exit = os._exit
EVAL_NS = {"__builtins__": {"set": set, "frozenset": frozenset, "float": float, "complex": complex,
                            "tuple": tuple, "list": list, "dict": dict, "range": range, "bytes": bytes},
           "inf": float("inf"), "nan": float("nan")}


class CapExceeded(BaseException):
    pass


# ------------------------------------------------------------------ isolation
def set_limits(job):
    try:
        import resource
        mb = int(job.get("mem_mb", 4096))
        resource.setrlimit(resource.RLIMIT_AS, (mb << 20, mb << 20))
        resource.setrlimit(resource.RLIMIT_FSIZE, (16 << 20, 16 << 20))
        cpu = int(job.get("cpu_s", 180))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except Exception:
        pass


def guard():
    """Disable functions that could damage the host (same spirit as HumanEval's reliability_guard)."""
    import shutil
    import subprocess
    for name in ["system", "kill", "killpg", "fork", "forkpty", "remove", "unlink", "rmdir", "removedirs",
                 "rename", "renames", "replace", "truncate", "chmod", "chown", "fchmod", "fchown", "lchown",
                 "chroot", "setuid", "setgid", "execv", "execve", "execl", "execlp",
                 "execvp", "execvpe", "spawnl", "spawnv", "spawnve", "spawnvp", "posix_spawn",
                 "posix_spawnp", "fchdir", "chdir", "link", "symlink", "mkfifo", "startfile"]:
        if hasattr(os, name):
            setattr(os, name, None)
    for name in ["rmtree", "move", "chown", "copytree", "copyfile", "copy", "copy2"]:
        setattr(shutil, name, None)
    for name in ["Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput"]:
        setattr(subprocess, name, None)
    for m in ["socket", "urllib.request", "http.client", "ctypes", "multiprocessing"]:
        sys.modules[m] = None  # import -> ImportError

    def guarded_os_open(path, flags, *a, **k):
        if flags & _WRITE_FLAGS and not _inside_cwd(path):
            raise PermissionError("sandbox: writing outside the working directory is not allowed")
        return _real_os_open(path, flags, *a, **k)

    os.open = guarded_os_open


def _inside_cwd(path):
    try:
        if isinstance(path, int):
            return True
        return os.path.realpath(os.fspath(path)).startswith(_CWD + os.sep)
    except Exception:
        return False


class IOBox:
    """Fake stdin/stdout that also support .buffer and open(0)."""

    def __init__(self, text):
        self.stdin = io.TextIOWrapper(io.BytesIO(text.encode("utf-8")), encoding="utf-8")
        self.out_bytes = io.BytesIO()
        self.stdout = io.TextIOWrapper(self.out_bytes, encoding="utf-8", write_through=True)

    def install(self):
        sys.stdin, sys.stdout = self.stdin, self.stdout
        box = self

        def fake_open(file, mode="r", *a, **k):
            if file == 0 or file == "/dev/stdin":
                return box.stdin.buffer if "b" in mode else box.stdin
            if file == 1 or file == "/dev/stdout":
                return box.stdout.buffer if "b" in mode else box.stdout
            if any(c in mode for c in "wax+") and not _inside_cwd(file):
                raise PermissionError("sandbox: writing outside the working directory is not allowed")
            return _real_open(file, mode, *a, **k)

        builtins.open = fake_open
        io.open = fake_open

    def output(self):
        try:
            self.stdout.flush()
        except Exception:
            pass
        return self.out_bytes.getvalue().decode("utf-8", "replace")


_WATCHDOG_FILE = None


def run_in_thread(fn, timeout, allow_exit=False):
    """Runs fn in a thread with a deadline. sys.exit() is a normal end only when allow_exit
    (stdio programs); inside a function under test it is an error.
    A faulthandler watchdog (a C thread that needs no GIL) hard-kills the process if a C call
    holding the GIL (e.g. a pathological regex) prevents the normal timeout from firing; the
    parent then uses the last checkpoint written to the result pipe."""
    box = {}

    def target():
        try:
            box["ret"] = fn()
        except SystemExit as e:  # noqa
            if allow_exit:
                box["ret"] = None
            else:
                box["exc"] = RuntimeError("SystemExit(%r) inside tested code" % (e.code,))
        except BaseException as e:  # noqa
            box["exc"] = e

    import faulthandler
    if _WATCHDOG_FILE is not None:
        faulthandler.dump_traceback_later(timeout + 3, exit=True, file=_WATCHDOG_FILE)
    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if _WATCHDOG_FILE is not None:
        faulthandler.cancel_dump_traceback_later()
    if t.is_alive():
        return "timeout", None
    if "exc" in box:
        return "error", box["exc"]
    return "ok", box.get("ret")


def emit(res_fd, out):
    """Writes one JSON line (a checkpoint; the last complete line is the result)."""
    data = (json.dumps(out) + "\n").encode()
    while data:
        n = _write(res_fd, data)
        data = data[n:]


def finish(res_fd, out):
    emit(res_fd, out)
    _exit(0)


import hashlib
import re as _re

_INT_TOKEN = _re.compile(r"-?\d+")


def _canon(x):
    """Canonical form of a returned value: floats rounded to 6 significant digits, sets sorted."""
    if isinstance(x, bool) or x is None or isinstance(x, (int, str, bytes)):
        return x
    if isinstance(x, float):
        return float(f"{x:.6g}")
    if isinstance(x, (list, tuple)):
        return [_canon(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((_canon(v) for v in x), key=repr)
    if isinstance(x, dict):
        return sorted(((_canon(k), _canon(v)) for k, v in x.items()), key=repr)
    return repr(x)


def digest_obj(x):
    try:
        s = repr(_canon(x))
    except Exception:  # noqa
        s = "<unrepresentable>"
    return hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:12]


def digest_text(s):
    """Digest of printed output: whitespace-insensitive, non-integer numbers rounded to 6 digits."""
    toks = []
    for t in s.split():
        if not _INT_TOKEN.fullmatch(t):
            try:
                t = f"{float(t):.6g}"
            except ValueError:
                pass
        toks.append(t)
    return hashlib.sha1(" ".join(toks).encode("utf-8", "replace")).hexdigest()[:12]


def norm(x):
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    return x


def values_match(got, exp):
    g, e = norm(got), norm(exp)
    if g == e or [g] == e:
        return True
    try:
        if isinstance(g, float) or isinstance(e, float):
            return math.isclose(float(g), float(e), rel_tol=1e-6, abs_tol=1e-6)
    except Exception:
        pass
    return False


def outputs_match(got, exp):
    if got.strip() == exp.strip():
        return True
    g, e = got.split(), exp.split()
    if g == e:
        return True
    if len(g) != len(e):
        return False
    for a, b in zip(g, e):
        if a == b:
            continue
        try:
            fa, fb = float(a), float(b)
        except ValueError:
            return False
        if not math.isclose(fa, fb, rel_tol=1e-6, abs_tol=1e-6):
            return False
    return True


# ------------------------------------------------------------------ loading
def load_module(job, code_obj):
    g = {"__name__": "__main__" if job["kind"] == "stdio" else "__solution__", "__builtins__": builtins}
    if job.get("setup"):
        exec(compile(job["setup"], "<setup>", "exec"), g)
    exec(code_obj, g)
    return g


def resolve_entry(g, entry):
    if entry and callable(g.get(entry)):
        return g[entry]
    if entry and "Solution" in g and isinstance(g["Solution"], type) and hasattr(g["Solution"], entry):
        return getattr(g["Solution"](), entry)
    if entry:
        for k, v in g.items():
            if isinstance(v, types.FunctionType) and k.lower() == entry.lower():
                return v
    funcs = [v for v in g.values() if isinstance(v, types.FunctionType) and v.__code__.co_filename == SOL]
    if len(funcs) == 1:
        return funcs[0]
    raise NameError("entry function %r not found" % entry)


# ------------------------------------------------------------------ test mode
def run_tests(job, res_fd):
    try:
        code_obj = compile(job["code"], SOL, "exec")
    except BaseException as e:  # noqa
        finish(res_fd, {"status": "compile_error", "passed": 0, "total": len(job["tests"]), "err": repr(e)[:300]})
    tests, tmo, kind = job["tests"], float(job.get("timeout", 4.0)), job["kind"]
    passed, err = 0, ""
    if kind == "stdio":
        for t in tests:
            box = IOBox(t["input"])
            box.install()
            st, val = run_in_thread(lambda: load_module(job, code_obj), tmo, allow_exit=True)
            if st == "timeout":
                finish(res_fd, {"status": "timeout", "passed": passed, "total": len(tests), "err": "timeout"})
            if st == "error":
                err = repr(val)[:300]
                break
            if not outputs_match(box.output(), t["output"]):
                err = "wrong answer"
                break
            passed += 1
    else:
        box = IOBox("")
        box.install()
        st, g = run_in_thread(lambda: load_module(job, code_obj), tmo)
        if st != "ok":
            finish(res_fd, {"status": "load_error" if st == "error" else "timeout", "passed": 0,
                            "total": len(tests), "err": repr(g)[:300]})
        for t in tests:
            if t["type"] == "assert":
                src = compile(t["src"], "<test>", "exec")
                fn = (lambda src=src: exec(src, g))
            else:
                try:
                    f = resolve_entry(g, job.get("entry"))
                except BaseException as e:  # noqa
                    err = repr(e)[:300]
                    break
                args = eval(t["args"], EVAL_NS)
                exp = eval(t["expected"], EVAL_NS)

                def fn(f=f, args=args, exp=exp):
                    r = f(*args)
                    if not values_match(r, exp):
                        raise AssertionError("wrong answer")
            st, val = run_in_thread(fn, float(t.get("timeout", tmo)))
            if st == "timeout":
                finish(res_fd, {"status": "timeout", "passed": passed, "total": len(tests), "err": "timeout"})
            if st == "error":
                err = repr(val)[:300]
                break
            passed += 1
    finish(res_fd, {"status": "ok", "passed": passed, "total": len(tests), "err": err})


# ------------------------------------------------------------------ tracer
def classify_c(fn):
    name = getattr(fn, "__name__", "")
    s = getattr(fn, "__self__", None)
    if s is None or isinstance(s, types.ModuleType):
        mod = s.__name__ if isinstance(s, types.ModuleType) else (getattr(fn, "__module__", "") or "")
        if mod in ("_heapq", "heapq"):
            return "heap"
        if mod in ("_bisect", "bisect"):
            return "bisect"
        if mod in ("math", "cmath"):
            return "math"
        if mod == "itertools":
            return "itertools"
        if mod in ("_functools", "functools"):
            return "memo" if name in ("lru_cache", "cache") else None
        if mod in ("_sre", "re"):
            return "re"
        if mod == "_collections":
            return "counter" if name == "_count_elements" else None
        if mod == "builtins" and name == "sorted":
            return "sort"
        return None
    if type(s) is list:
        return "sort" if name == "sort" else None
    if isinstance(s, (set, frozenset)):
        return "set"
    if isinstance(s, collections.Counter):
        return "counter"
    if isinstance(s, collections.deque):
        return "deque"
    if isinstance(s, dict):
        return "dict"
    if type(s).__name__ in ("Pattern", "SRE_Pattern", "Match"):
        return "re"
    return None


def classify_py(co):
    fn = co.co_filename.replace("\\", "/")
    base = fn.rsplit("/", 1)[-1]
    q = getattr(co, "co_qualname", co.co_name)
    if base == "heapq.py":
        return "heap"
    if base == "bisect.py":
        return "bisect"
    if fn.endswith("collections/__init__.py"):
        if q.startswith("Counter"):
            return "counter"
        if q.startswith("OrderedDict"):
            return "dict"
        return None
    if base == "functools.py" and co.co_name in ("lru_cache", "cache", "decorating_function"):
        return "memo"
    if fn.endswith("re/__init__.py") or base == "re.py":
        return "re"
    if base in ("fractions.py", "statistics.py"):
        return "math"
    return None


def make_tracer(cap):
    st = {"lines": 0, "calls": 0, "depth": 0, "max_depth": 0, "max_rec": 0, "rec_calls": 0}
    hits, active, funcs, py, cc, fcalls = {}, {}, set(), {}, {}, {}

    def local(frame, event, arg):
        if event == "line":
            st["lines"] += 1
            ln = frame.f_lineno
            hits[ln] = hits.get(ln, 0) + 1
            if st["lines"] > cap:
                st["capped"] = True
                raise CapExceeded()
        elif event == "return":
            st["depth"] -= 1
            co = frame.f_code
            if co in active:
                active[co] -= 1
        return local

    def glob(frame, event, arg):
        co = frame.f_code
        if co.co_filename == SOL:
            st["depth"] += 1
            if st["depth"] > st["max_depth"]:
                st["max_depth"] = st["depth"]
            if not co.co_name.startswith("<"):
                st["calls"] += 1
                funcs.add(co.co_name)
                fl = co.co_firstlineno
                fcalls[fl] = fcalls.get(fl, 0) + 1
                c = active.get(co, 0) + 1
                active[co] = c
                if c > 1:
                    st["rec_calls"] += 1
                if c > st["max_rec"]:
                    st["max_rec"] = c
            return local
        back = frame.f_back
        if back is not None and back.f_code.co_filename == SOL:
            cat = classify_py(co)
            if cat:
                py[cat] = py.get(cat, 0) + 1
        return None

    def prof(frame, event, arg):
        if event == "c_call" and frame.f_code.co_filename == SOL:
            cat = classify_c(arg)
            if cat:
                cc[cat] = cc.get(cat, 0) + 1

    def result():
        out = dict(st)
        out.pop("depth", None)
        out["capped"] = bool(st.get("capped"))
        out["hits"] = {str(k): v for k, v in hits.items()}
        out["funcs"] = len(funcs)
        out["fcalls"] = {str(k): v for k, v in fcalls.items()}
        out["py"], out["c"] = py, cc
        return out

    return glob, prof, result


def run_trace(job, res_fd):
    try:
        code_obj = compile(job["code"], SOL, "exec")
    except BaseException as e:  # noqa
        finish(res_fd, {"status": "compile_error", "err": repr(e)[:300], "runs": [], "timing": []})
    cap = int(job.get("max_events", 1_500_000))
    tmo = float(job.get("timeout", 8.0))
    tlim = float(job.get("timing_limit", 1.0))
    kind = job["kind"]
    ladders = collections.OrderedDict()
    for it in job["inputs"]:
        ladders.setdefault(it.get("ladder", "main"), []).append(it)
    out = {"status": "ok", "runs": [], "timing": []}

    def prepare(it):
        """Returns (zero-arg callable that runs the program once, digest(ret) of its output).
        The output digest lets the parent check that a ladder input is valid: reference
        solutions must agree on it (an input that breaks the task's format/constraints makes
        them fail or disagree)."""
        if kind == "stdio":
            box = IOBox(it["arg"])
            box.install()

            def run_stdio():
                try:
                    load_module(job, code_obj)
                except SystemExit:  # a normal way to end a stdio program
                    pass
            return run_stdio, (lambda ret, box=box: digest_text(box.output()))
        box = IOBox("")
        box.install()
        st, g = run_in_thread(lambda: load_module(job, code_obj), tmo)
        if st != "ok":
            raise RuntimeError("load failed: %s %r" % (st, g))
        f = resolve_entry(g, job.get("entry"))
        args = eval(it["arg"], EVAL_NS)
        return (lambda: f(*args)), digest_obj

    # ---- traced runs
    for lad, items in ladders.items():
        items.sort(key=lambda x: x["size"])
        walls = []
        for it in items:
            if len(walls) >= 2 and walls[-2] > 0:  # hidden C-level work can blow up even under the line cap
                if walls[-1] * max(1.0, walls[-1] / walls[-2]) * 2 > tmo / 2:
                    break
            rec = {"ladder": lad, "size": it["size"]}
            try:
                call, outfn = prepare(it)
            except BaseException as e:  # noqa
                rec.update(status="error", err=repr(e)[:200])
                out["runs"].append(rec)
                continue
            glob, prof, result = make_tracer(cap)

            def traced(call=call, glob=glob, prof=prof):
                sys.setprofile(prof)
                sys.settrace(glob)
                try:
                    return call()
                finally:
                    sys.settrace(None)
                    sys.setprofile(None)

            w0 = time.perf_counter()
            st, val = run_in_thread(traced, tmo)
            walls.append(time.perf_counter() - w0)
            rec.update(result())
            if st == "timeout":
                rec["status"] = "timeout"
                out["runs"].append(rec)
                out["status"] = "timeout"
                finish(res_fd, out)
            if rec["capped"]:
                rec["status"] = "cap"
            elif st == "error":
                rec.update(status="error", err=repr(val)[:200])
            else:
                rec["status"] = "ok"
                try:
                    rec["out"] = outfn(val)
                except Exception:  # noqa
                    pass
            out["runs"].append(rec)
            emit(res_fd, out)  # checkpoint (survives a watchdog kill later on)
            if rec["status"] == "cap":
                break  # bigger inputs would also hit the cap

    # ---- untraced timing runs (captures work done inside C builtins, e.g. sorted / `in list`)
    for lad, items in ladders.items():
        prev = []
        for it in items:
            if len(prev) >= 2 and prev[-2] > 0:
                predicted = prev[-1] * max(1.0, prev[-1] / prev[-2]) * 2
                if predicted > 3 * tlim:
                    break
            best, total, reps, digest = None, 0.0, 0, None
            while reps < 50 and (reps < 3 or total < 0.02) and total < 0.3:
                try:
                    call, outfn = prepare(it)
                except BaseException:  # noqa
                    best = None
                    break

                def timed(call=call):
                    t0 = time.perf_counter()
                    r = call()
                    return time.perf_counter() - t0, r

                st, val = run_in_thread(timed, 3 * tlim + 1)
                if st == "timeout":
                    out["status"] = "timeout"
                    finish(res_fd, out)
                if st != "ok":
                    best = None
                    break
                el, ret = val
                if digest is None:  # outside the timed region
                    try:
                        digest = outfn(ret)
                    except Exception:  # noqa
                        digest = None
                best = el if best is None else min(best, el)
                total += el
                reps += 1
            if best is None:
                break
            out["timing"].append({"ladder": lad, "size": it["size"], "t": best, "reps": reps, "out": digest})
            emit(res_fd, out)
            prev.append(best)
            if best > tlim:
                break
    finish(res_fd, out)


def main():
    job = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    res_fd = os.dup(1)
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)
    sys.stderr = io.StringIO()
    global _WATCHDOG_FILE
    _WATCHDOG_FILE = _real_open(os.devnull, "w")
    sys.setrecursionlimit(1_000_000)
    for mb in (256, 255, 128, 64):
        try:
            threading.stack_size(mb * 1024 * 1024)
            break
        except (ValueError, RuntimeError):
            continue
    set_limits(job)
    if job.get("cpu") is not None and hasattr(os, "sched_setaffinity"):
        try:
            os.sched_setaffinity(0, {int(job["cpu"])})
        except OSError:
            pass
    guard()
    try:
        if job["mode"] == "test":
            run_tests(job, res_fd)
        else:
            run_trace(job, res_fd)
    except BaseException as e:  # noqa
        finish(res_fd, {"status": "harness_error", "err": repr(e)[:300], "passed": 0,
                        "total": len(job.get("tests", [])), "runs": [], "timing": []})


if __name__ == "__main__":
    main()
