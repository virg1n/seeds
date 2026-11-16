"""Build ladders of growing inputs from a task's own test inputs (no hand-written generators).

func tasks:  arguments are Python values. Mode "A" grows containers/strings, mode "B" grows
             integers (problems like "n-th number"). Properties such as sortedness / distinctness
             of lists are preserved.
stdio tasks: heuristic, format-aware growth of competitive-programming stdin
             (count + list, count + rows, single number, single string). Plus a "nat" ladder made
             of the task's test inputs themselves (size = number of tokens).
"""
from __future__ import annotations

import os
import random

MAX_ELEMS = 200_000   # largest container / string produced by a ladder
MAX_INT = 10 ** 7     # largest integer produced by mode B


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _grow_list(v, f, rng):
    n = len(v)
    if n == 0 or f == 1:
        return list(v)
    m = min(MAX_ELEMS, n * f)
    if all(isinstance(x, int) and not isinstance(x, bool) for x in v):
        lo, hi = min(v), max(v)
        distinct = len(set(v)) == n
        span = hi - lo + 1
        if distinct:
            hi = lo + max(span * f, m) - 1
        out = [rng.randint(lo, hi) for _ in range(m)]
        if distinct:
            out = list(dict.fromkeys(out))
            while len(out) < m:
                out.append(hi + len(out))
    elif all(_is_num(x) for x in v):
        lo, hi = min(v), max(v)
        out = [rng.uniform(lo, hi) if lo != hi else lo for _ in range(m)]
    else:
        out = [rng.choice(v) for _ in range(m)]
    try:
        if v == sorted(v):
            out.sort()
        elif v == sorted(v, reverse=True):
            out.sort(reverse=True)
    except TypeError:
        pass
    return out


def scale_value(v, f, rng, mode):
    if f == 1:
        return v
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, int):
        if mode == "B" and 2 <= abs(v) <= MAX_INT:
            return v * f
        return v
    if isinstance(v, float):
        return v * f if mode == "B" and 2 <= abs(v) <= MAX_INT else v
    if mode != "A":
        return v
    if isinstance(v, str):
        if len(v) <= 1:
            return v
        return (v * f)[: MAX_ELEMS]
    if isinstance(v, list):
        if v and all(isinstance(x, list) for x in v):  # matrix / list of rows: grow rows only
            return _grow_list(v, f, rng)
        return _grow_list(v, f, rng)
    if isinstance(v, tuple):
        if len(v) > 2 and len({type(x) for x in v}) == 1:
            return tuple(_grow_list(list(v), f, rng))
        return v
    if isinstance(v, (set, frozenset)):
        g = _grow_list(sorted(v) if all(_is_num(x) for x in v) else list(v), f, rng)
        return type(v)(g)
    if isinstance(v, dict):
        if not v:
            return v
        keys = list(v)
        if all(isinstance(k, int) for k in keys):
            out = dict(v)
            base = max(keys) + 1
            vals = list(v.values())
            for i in range(len(keys) * (f - 1)):
                out[base + i] = rng.choice(vals)
            return out
        if all(isinstance(k, str) for k in keys):
            out = dict(v)
            vals = list(v.values())
            for i in range(len(keys) * (f - 1)):
                out[f"{rng.choice(keys)}_{i}"] = rng.choice(vals)
            return out
        return v
    return v


def has_mode(args, mode):
    for a in args:
        if mode == "A" and isinstance(a, (str, list, tuple, set, frozenset, dict)) and len(a) > 1:
            return True
        if mode == "B" and isinstance(a, (int, float)) and not isinstance(a, bool) and 2 <= abs(a) <= MAX_INT:
            return True
    return False


def func_ladders(arg_tuples, factors, seed=0):
    """arg_tuples: list of tuples of Python values (from tests). Returns harness ladder items."""
    if not arg_tuples:
        return []

    def size_of(args):
        s = 0
        for a in args:
            if isinstance(a, (str, list, tuple, set, dict)):
                s += len(a)
            elif _is_num(a):
                s += abs(a) if abs(a) < 1e7 else 0
        return s

    base = max(arg_tuples, key=size_of)
    items = []
    for mode in ("A", "B"):
        if not has_mode(base, mode):
            continue
        longest = max([len(a) for a in base if isinstance(a, (str, list, tuple, set, frozenset, dict))] or [1])
        biggest = max([abs(a) for a in base if _is_num(a) and 2 <= abs(a) <= MAX_INT] or [1])
        for f in factors:
            if longest * f > MAX_ELEMS or (mode == "B" and biggest * f > MAX_INT):
                break
            rng = random.Random(seed * 1000 + f)
            args = scale_args(base, f, rng, mode)
            r = repr(args)
            if len(r) > 3_000_000:
                break
            items.append({"ladder": mode, "size": f, "arg": r})
    # natural ladder: the test arguments themselves, if they span >= 3 distinct sizes
    nat = {}
    for args in arg_tuples:
        nat.setdefault(size_of(args), args)
    if len(nat) >= 3:
        items += [{"ladder": "nat", "size": s, "arg": repr(a)} for s, a in sorted(nat.items()) if s > 0]
    return items


def _is_container(a):
    return isinstance(a, (str, list, tuple, set, frozenset, dict))


def scale_args(base, f, rng, mode):
    """Scales an argument tuple keeping simple cross-argument constraints: an integer argument
    equal to the length of a container argument (e.g. solve(n, a) with n == len(a)) moves together
    with that container in both modes."""
    linked = {}  # index of int arg -> index of the container whose length it equals
    for i, a in enumerate(base):
        if isinstance(a, int) and not isinstance(a, bool) and a > 1:
            for j, b in enumerate(base):
                if j != i and _is_container(b) and len(b) == a:
                    linked[i] = j
                    break
    new = list(base)
    if mode == "A":
        for i, a in enumerate(base):
            if i not in linked:
                new[i] = scale_value(a, f, rng, "A")
        for i, j in linked.items():
            new[i] = len(new[j])
    else:
        grow = set(linked.values())
        for i, a in enumerate(base):
            if _is_container(a):
                new[i] = scale_value(a, f, rng, "A") if i in grow else a
            else:
                new[i] = scale_value(a, f, rng, "B")
        for i, j in linked.items():
            new[i] = len(new[j])
    return tuple(new)


# ------------------------------------------------------------------ stdin
def _tok_lines(text):
    return [ln.split() for ln in text.strip("\n").split("\n")]


def _isint(t):
    try:
        int(t)
        return True
    except ValueError:
        return False


def _grow_tokens(toks, m, rng):
    if all(_isint(t) for t in toks):
        vals = _grow_list([int(t) for t in toks], max(1, -(-m // max(1, len(toks)))), rng)[:m]
        return [str(x) for x in vals]
    return [rng.choice(toks) for _ in range(m)]


def scale_stdin(text, f, rng):
    """Returns scaled stdin or None if the format is not recognised."""
    if f == 1:
        return text
    lines = _tok_lines(text)
    if not lines or not lines[0]:
        return None
    # single integer
    if len(lines) == 1 and len(lines[0]) == 1 and _isint(lines[0][0]):
        v = int(lines[0][0])
        return f"{v * f}\n" if 2 <= abs(v) and abs(v) * f <= MAX_INT else None
    # single token string
    if len(lines) == 1 and len(lines[0]) == 1:
        s = lines[0][0]
        return s * f + "\n" if 1 < len(s) and len(s) * f <= MAX_ELEMS else None
    head = lines[0]
    if not all(_isint(t) for t in head):
        return None
    hv = [int(t) for t in head]
    rest = lines[1:]
    # pattern: some header value == token count of a following line  ("n \n a1 .. an")
    # every header value equal to the grown count is grown with it ("n m" with n == m == len(list)
    # cannot tell which one is the list length; keeping them equal keeps constraints like m <= n)
    for hi, c in enumerate(hv):
        if c < 2 or c * f > MAX_ELEMS:
            continue
        for li, row in enumerate(rest):
            if len(row) == c:
                new_head = [v * f if v == c else v for v in hv]
                new_rest = [list(r) for r in rest]
                for lj, r2 in enumerate(rest):
                    if len(r2) == c:
                        new_rest[lj] = _grow_tokens(r2, c * f, rng)
                    elif len(r2) == 1 and len(r2[0]) == c:  # string of length n
                        new_rest[lj] = [(r2[0] * f)[: c * f]]
                return "\n".join([" ".join(map(str, new_head))] + [" ".join(r) for r in new_rest]) + "\n"
            if len(row) == 1 and len(row[0]) == c and not _isint(row[0]):
                new_head = [v * f if v == c else v for v in hv]
                new_rest = [list(r) for r in rest]
                new_rest[li] = [(row[0] * f)[: c * f]]
                return "\n".join([" ".join(map(str, new_head))] + [" ".join(r) for r in new_rest]) + "\n"
    # "header value == number of following lines" (n rows, edges, intervals ...): resampling rows
    # often produces invalid inputs (duplicate edges on the same few vertices, repeated exam days,
    # more rows than another header value allows) that reference solutions still agree on, so
    # they cannot be filtered. Off by default (these tasks use the natural ladder);
    # STDIO_ROW_RESAMPLE=1 turns it back on (all header values equal to the row count grow).
    if os.environ.get("STDIO_ROW_RESAMPLE", "0") == "1":
        for hi, c in enumerate(hv):
            if c >= 2 and c == len(rest):
                m = min(MAX_ELEMS // max(1, len(rest[0])), c * f)
                new_rows = [rng.choice(rest) for _ in range(m)]
                new_head = [m if v == c else v for v in hv]
                return "\n".join([" ".join(map(str, new_head))] + [" ".join(r) for r in new_rows]) + "\n"
    return None


def stdio_ladders(test_inputs, factors, seed=0, max_nat=10):
    items = []
    if not test_inputs:
        return items
    sized = sorted(test_inputs, key=lambda s: len(s.split()))
    base = sized[len(sized) // 2]
    for f in factors:
        rng = random.Random(seed * 1000 + f)
        s = scale_stdin(base, f, rng)
        if s is None:
            break
        if len(s) > 3_000_000:
            break
        items.append({"ladder": "A", "size": f, "arg": s})
    if len(items) < 3:
        items = []
    # natural ladder: the test inputs themselves (distinct sizes)
    seen = set()
    for s in sized:
        n = len(s.split())
        if n in seen or n == 0:
            continue
        seen.add(n)
        items.append({"ladder": "nat", "size": n, "arg": s})
    nat = [it for it in items if it["ladder"] == "nat"]
    if len(nat) > max_nat:
        keep = {id(nat[round(i * (len(nat) - 1) / (max_nat - 1))]) for i in range(max_nat)}
        items = [it for it in items if it["ladder"] != "nat" or id(it) in keep]
    return items


# ------------------------------------------------------------------ recipes
# Tasks store a compact, deterministic *recipe*; the (possibly multi-MB) ladder inputs are built
# only when a program is traced, so tasks.jsonl stays small.
_EVAL_NS = {"__builtins__": {"set": set, "frozenset": frozenset, "float": float, "complex": complex,
                             "tuple": tuple, "list": list, "dict": dict, "range": range, "bytes": bytes},
            "inf": float("inf"), "nan": float("nan")}


def func_recipe(arg_tuples, factors, seed, max_args=40):
    """Keeps up to max_args argument tuples spread over their sizes (for the base and the nat ladder)."""
    reps = []
    for a in arg_tuples:
        r = repr(tuple(a))
        if len(r) <= 300_000:
            reps.append(r)
    reps = list(dict.fromkeys(reps))
    if len(reps) > max_args:
        reps.sort(key=len)
        reps = [reps[round(i * (len(reps) - 1) / (max_args - 1))] for i in range(max_args)]
    return {"type": "func", "args": reps, "factors": list(factors), "seed": seed}


def stdio_recipe(factors, seed):
    return {"type": "stdio", "from_tests": True, "factors": list(factors), "seed": seed}


def build_ladder(task):
    if task.get("ladder") is not None:
        return task["ladder"]
    rc = task["ladder_recipe"]
    if rc["type"] == "func":
        args = [eval(a, dict(_EVAL_NS)) for a in rc["args"]]
        return func_ladders(args, rc["factors"], seed=rc["seed"])
    return stdio_ladders([t["input"] for t in task["tests"]], rc["factors"], seed=rc["seed"])
