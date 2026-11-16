"""Graph-based static code distances: AST, control-flow graph (CFG) and program dependence graph
(PDG), compared with a Weisfeiler-Lehman subtree kernel (as PDG+WL in DivAlgo).

All graphs are label-only: identifiers and literals are dropped, so renaming and constants do
not matter; only the structure of the code does.

  AST  every AST node (type name), edges parent -> child.
  CFG  statement-level control flow inside every function and at module level: one node per
       simple statement or compound-statement header; edges for fall-through, branches, loop
       back edges, break/continue, try handlers. return/raise end a path.
  PDG  the same statement nodes; control dependence = statement -> statements nested in its
       body (structured code), data dependence = statement defining a variable -> statement
       using it (flow-insensitive by name, so loop-carried dependences are included).

distance = 1 - cosine similarity of WL feature histograms (h iterations, directed, edge labels).
"""
from __future__ import annotations

import ast
import hashlib
import math
from collections import Counter

WL_ITERS = 3


# ------------------------------------------------------------------ WL kernel
def _h(s):
    return hashlib.blake2b(s.encode(), digest_size=8).hexdigest()


def wl_features(labels, edges, h=WL_ITERS):
    """labels: list of node labels; edges: list of (u, v, edge_label). Returns a Counter."""
    out_n = [[] for _ in labels]
    in_n = [[] for _ in labels]
    for u, v, el in edges:
        out_n[u].append((el, v))
        in_n[v].append((el, u))
    cur = [str(l) for l in labels]
    feats = Counter(f"0:{l}" for l in cur)
    for it in range(1, h + 1):
        nxt = []
        for i in range(len(cur)):
            sig = cur[i] + "|" + ",".join(sorted(f">{el}{cur[v]}" for el, v in out_n[i])) + "|" + \
                  ",".join(sorted(f"<{el}{cur[u]}" for el, u in in_n[i]))
            nxt.append(_h(sig))
        cur = nxt
        feats.update(f"{it}:{l}" for l in cur)
    return feats


def cos_dist(a, b):
    if not a or not b:
        return float("nan")
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return 1.0 - dot / (na * nb)


# ------------------------------------------------------------------ AST
def ast_graph(tree):
    labels, edges = [], []

    def visit(node, parent):
        i = len(labels)
        labels.append(type(node).__name__)
        if parent is not None:
            edges.append((parent, i, "a"))
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.expr_context, ast.boolop, ast.operator, ast.unaryop, ast.cmpop)):
                labels[i] += ":" + type(ch).__name__ if not isinstance(ch, ast.expr_context) else ""
                continue
            visit(ch, i)

    visit(tree, None)
    return labels, edges


# ------------------------------------------------------------------ statement graphs
def _stmt_label(s):
    if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call):
        return "ExprCall"
    return type(s).__name__


class _CFG:
    def __init__(self):
        self.labels, self.edges, self.loops = [], [], []

    def node(self, label, preds):
        i = len(self.labels)
        self.labels.append(label)
        for p in preds:
            self.edges.append((p, i, "c"))
        return i

    def block(self, stmts, preds):
        """Builds a statement list; returns the nodes that fall through to the next statement."""
        for s in stmts:
            preds = self.stmt(s, preds)
        return preds

    def stmt(self, s, preds):
        if isinstance(s, ast.If):
            c = self.node("If", preds)
            return self.block(s.body, [c]) + (self.block(s.orelse, [c]) if s.orelse else [c])
        if isinstance(s, (ast.For, ast.AsyncFor, ast.While)):
            hd = self.node(type(s).__name__, preds)
            self.loops.append((hd, []))
            body_exit = self.block(s.body, [hd])
            for p in body_exit:
                self.edges.append((p, hd, "b"))  # back edge
            _, breaks = self.loops.pop()
            after = self.block(s.orelse, [hd]) if s.orelse else [hd]
            return after + breaks
        if isinstance(s, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            t = self.node("Try", preds)
            body_exit = self.block(s.body, [t])
            ends = self.block(s.orelse, body_exit) if s.orelse else body_exit
            for hnd in s.handlers:
                ends = ends + self.block(hnd.body, [self.node("Except", [t])])
            return self.block(s.finalbody, ends) if s.finalbody else ends
        if isinstance(s, (ast.With, ast.AsyncWith)):
            return self.block(s.body, [self.node("With", preds)])
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d = self.node(type(s).__name__, preds)
            saved, self.loops = self.loops, []
            self.block(s.body, [self.node("Entry", [d]) if isinstance(s, ast.ClassDef) else d])
            self.loops = saved
            return [d]  # the body is a separate subgraph entered from the definition
        if isinstance(s, (ast.Return, ast.Raise)):
            self.node(type(s).__name__, preds)
            return []
        if isinstance(s, ast.Break):
            b = self.node("Break", preds)
            if self.loops:
                self.loops[-1][1].append(b)
            return []
        if isinstance(s, ast.Continue):
            c = self.node("Continue", preds)
            if self.loops:
                self.edges.append((c, self.loops[-1][0], "b"))
            return []
        if hasattr(ast, "Match") and isinstance(s, ast.Match):
            m = self.node("Match", preds)
            ends = []
            for case in s.cases:
                ends += self.block(case.body, [m])
            return ends + [m]
        return [self.node(_stmt_label(s), preds)]


def cfg_graph(tree):
    g = _CFG()
    g.block(tree.body, [g.node("Module", [])])
    return g.labels, g.edges


def _names(node, ctx):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ctx)}


def _header_exprs(s):
    """Expressions evaluated by the statement itself (not by its nested body)."""
    if isinstance(s, (ast.If, ast.While)):
        return [s.test]
    if isinstance(s, (ast.For, ast.AsyncFor)):
        return [s.iter, s.target]
    if isinstance(s, (ast.With, ast.AsyncWith)):
        return [x for it in s.items for x in (it.context_expr, it.optional_vars) if x is not None]
    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return list(s.decorator_list) + list(s.args.defaults)
    if isinstance(s, (ast.Try, getattr(ast, "TryStar", ast.Try), ast.ClassDef)):
        return []
    return [s]


def pdg_graph(tree):
    labels, edges, defs, uses = [], [], [], []

    def add(s, parent):
        i = len(labels)
        labels.append(_stmt_label(s))
        if parent is not None:
            edges.append((parent, i, "cd"))
        hx = _header_exprs(s)
        d, u = set(), set()
        for e in hx:
            d |= _names(e, ast.Store)
            u |= _names(e, ast.Load)
        if isinstance(s, ast.AugAssign) and isinstance(s.target, ast.Name):
            u.add(s.target.id)
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d.add(s.name)
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for a in s.args.args + s.args.kwonlyargs + s.args.posonlyargs:
                d.add(a.arg)
        defs.append(d)
        uses.append(u)
        for field in ("body", "orelse", "finalbody"):
            for ch in getattr(s, field, []) or []:
                if isinstance(ch, ast.stmt):
                    add(ch, i)
        for hnd in getattr(s, "handlers", []) or []:
            for ch in hnd.body:
                add(ch, i)

    root = len(labels)
    labels.append("Module")
    defs.append(set())
    uses.append(set())
    for s in tree.body:
        add(s, root)
    by_name = {}
    for i, d in enumerate(defs):
        for v in d:
            by_name.setdefault(v, []).append(i)
    for j, u in enumerate(uses):
        for v in u:
            for i in by_name.get(v, []):
                if i != j:
                    edges.append((i, j, "dd"))
    return labels, edges


# ------------------------------------------------------------------ public API
_cache = {}


def features(code):
    """{'AST': Counter, 'CFG': Counter, 'PDG': Counter} or None if the code does not parse."""
    if code in _cache:
        return _cache[code]
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        _cache[code] = None
        return None
    out = {name: wl_features(*fn(tree)) for name, fn in (("AST", ast_graph), ("CFG", cfg_graph), ("PDG", pdg_graph))}
    _cache[code] = out
    return out


def distances(a, b):
    """{'AST WL': d, 'CFG WL': d, 'PDG WL': d} (nan when a program does not parse)."""
    fa, fb = features(a), features(b)
    return {f"{k} WL": (cos_dist(fa[k], fb[k]) if fa and fb else float("nan")) for k in ("AST", "CFG", "PDG")}
