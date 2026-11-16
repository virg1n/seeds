"""python -m src.embed MODEL_DIR IN.json OUT.npy  -> L2-normalised code embeddings."""
from __future__ import annotations

import json
import sys

import numpy as np


def main():
    import torch
    from transformers import AutoModel, AutoTokenizer
    path, inp, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    codes = json.load(open(inp, encoding="utf-8"))
    last_token = "qwen" in path.lower()
    tok = AutoTokenizer.from_pretrained(path)
    tok.padding_side = "left" if last_token else "right"
    model = AutoModel.from_pretrained(path, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(dev).eval()
    max_len = 1024 if last_token else 512
    vecs = []
    bs = 32
    unix = "unixcoder" in path.lower()

    def encode(batch):
        if not unix:
            return tok(batch, padding=True, truncation=True, max_length=max_len, return_tensors="pt")
        # official UniXcoder protocol (microsoft/CodeBERT/UniXcoder/unixcoder.py, encoder-only mode):
        # [CLS] <encoder-only> [SEP] code [SEP], mean pooling over non-pad tokens
        ids = []
        for c in batch:
            t = tok.tokenize(c)[: max_len - 4]
            t = [tok.cls_token, "<encoder-only>", tok.sep_token] + t + [tok.sep_token]
            ids.append(tok.convert_tokens_to_ids(t))
        n = max(len(x) for x in ids)
        pad = tok.pad_token_id
        input_ids = torch.tensor([x + [pad] * (n - len(x)) for x in ids])
        return {"input_ids": input_ids, "attention_mask": (input_ids != pad).long()}

    for i in range(0, len(codes), bs):
        batch = codes[i:i + bs]
        enc = {k: v.to(dev) for k, v in encode(batch).items()}
        with torch.no_grad():
            h = model(**enc).last_hidden_state.float()
        if last_token:
            v = h[:, -1]
        else:
            m = enc["attention_mask"].unsqueeze(-1).float()
            v = (h * m).sum(1) / m.sum(1).clamp(min=1)
        v = torch.nn.functional.normalize(v, dim=-1)
        vecs.append(v.cpu().numpy())
    np.save(outp, np.concatenate(vecs, 0) if vecs else np.zeros((0, 1)))


if __name__ == "__main__":
    main()
