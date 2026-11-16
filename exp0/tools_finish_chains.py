"""Recovery tool: finish the 'differently' chain job of selected shards after their workers were
stopped, continuing every chain from its last written round (same prompts, same seeds as
src/gen_worker.py), spread over several GPUs; then merge everything like src/generate.py does.

  python tools_finish_chains.py run   SPEC SHARDS(e.g. 3,4) PART NPART OUT.jsonl     (one per GPU)
  python tools_finish_chains.py merge SPEC
"""
import glob
import json
import os
import sys

EXP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, EXP)


def _read(path):
    rows = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # a line cut by the kill
    return rows


def _chain_rows(gen_dir, tag):
    rows = []
    for f in glob.glob(os.path.join(gen_dir, f"{tag}.shard*.jsonl")) + glob.glob(os.path.join(gen_dir, f"{tag}.finish*.jsonl")):
        rows += [r for r in _read(f) if r.get("cond") == "differently"]
    return rows


def run(spec_path, shards, part, npart, out_path):
    from src import prompts as PR
    from src.gen_worker import HFEngine, _seed
    spec = json.load(open(spec_path, encoding="utf-8"))
    tag, samp, cfg = spec["model_tag"], spec["sampling"], dict(spec["cfg"])
    job = [j for j in spec["jobs"] if j["type"] == "chain"][0]
    nshards = int(os.environ.get("NSHARDS", "8"))
    gen_dir = os.path.dirname(spec_path)
    tasks = [t for i, t in enumerate(job["tasks"]) if i % nshards in shards]
    chains = [(t, c) for t in tasks for c in range(job["chains"])][part::npart]
    have = {}
    for r in _chain_rows(gen_dir, tag):
        have.setdefault((r["task"], r["chain"]), {})[r["round"]] = r
    state = []
    for t, c in chains:
        done = have.get((t["id"], c), {})
        prev = []
        for rnd in range(job["rounds"]):
            if rnd not in done:
                break
            prev.append(done[rnd]["code"])
        state.append((t, c, prev))
    todo = sum(job["rounds"] - len(p) for _, _, p in state)
    print(f"part {part}/{npart}: {len(state)} chains, {todo} sequences to generate", flush=True)
    if todo == 0:
        return
    cfg["hf_batch"] = 32
    eng = HFEngine(spec["model_path"], cfg)
    tok = eng.tok
    budget = cfg["max_model_len"] - samp["max_tokens"] - 16

    def render(msgs):
        try:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    def fits(prompt):
        return len(tok.encode(prompt)) <= budget

    out = open(out_path, "a", encoding="utf-8")
    for rnd in range(job["rounds"]):
        prompts, params, idx = [], [], []
        for k, (t, c, prev) in enumerate(state):
            if len(prev) != rnd:
                continue
            shown = list(dict.fromkeys(p for p in prev if p.strip()))[-job["show"]:]
            while True:
                msgs = PR.plain(t) if rnd == 0 or not shown else PR.differently(t, shown)
                pr = render(msgs)
                if fits(pr) or not shown:
                    break
                shown = shown[1:]
            if not fits(pr):
                prev.append("")
                out.write(json.dumps(dict(model=tag, cond=job["name"], task=t["id"], chain=c, round=rnd, sample=rnd,
                                          text="", code="", skipped="prompt_too_long", backend="hf")) + "\n")
                continue
            prompts.append(pr)
            params.append(dict(samp, n=1, seed=_seed(tag, t["id"], c, rnd)))
            idx.append(k)
        texts = eng.generate(prompts, params) if prompts else []
        for k, ts in zip(idx, texts):
            t, c, prev = state[k]
            text, trunc = ts[0]
            code = PR.extract_code(text)
            prev.append(code)
            out.write(json.dumps(dict(model=tag, cond=job["name"], task=t["id"], chain=c, round=rnd, sample=rnd,
                                      text=text, code=code, backend="hf", truncated=bool(trunc)),
                                 ensure_ascii=False) + "\n")
        out.flush()
        print(f"part {part}: round {rnd + 1}/{job['rounds']} done", flush=True)
    out.close()


def merge(spec_path):
    from src.generate import _expected_rows, _spec_hash
    spec = json.load(open(spec_path, encoding="utf-8"))
    tag = spec["model_tag"]
    gen_dir = os.path.dirname(spec_path)
    files = sorted(glob.glob(os.path.join(gen_dir, f"{tag}.shard*.jsonl"))) + \
        sorted(glob.glob(os.path.join(gen_dir, f"{tag}.finish*.jsonl")))
    rows, seen = [], set()
    for f in files:
        for r in _read(f):
            key = (r["cond"], r["task"], r.get("strategy"), r.get("chain"), r.get("round"), r["sample"])
            if key not in seen:
                seen.add(key)
                rows.append(r)
    exp = _expected_rows(spec)
    print(f"merged {len(rows)} rows from {len(files)} files, expected {exp}")
    if len(rows) != exp:
        raise SystemExit("row count mismatch -> not writing the .done marker")
    out = os.path.join(gen_dir, f"{tag}.jsonl")
    with open(out + ".tmp", "w", encoding="utf-8") as fo:
        for r in rows:
            fo.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(out + ".tmp", out)
    # the same hash generate.run_model() computes (it excludes model_path), so the pipeline skips this model
    open(os.path.join(gen_dir, f"{tag}.done"), "w").write(_spec_hash(spec))
    for f in files:
        os.unlink(f)
    print(f"wrote {out} and {tag}.done")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], [int(x) for x in sys.argv[3].split(",")], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
    else:
        merge(sys.argv[2])
