"""Policy = frozen Qwen2.5-Coder + shared hand-rolled LoRA + (mode film) a seed modulator.

Seed modulator ("some_neurons * nn2(seed)"): seed z has a fixed code e_z ~ N(0, I) drawn from the
integer z; m(e_z) = Linear -> SiLU -> Linear (dimension FILM_RANK); for every modulated layer l
    delta_{z,l} = U_l @ m(e_z)                    [d_ff]
    gain_{z,l}  = 1 + FILM_MAX * tanh(delta / FILM_MAX)
multiplies the MLP hidden neurons (the input of down_proj) of every token of a row with seed z.
`set_seeds(seeds)` computes the gains of the rows of the NEXT forward / generate call; a forward
pre-hook on down_proj applies them. The gains tensor must stay set until the backward pass is done:
non-reentrant gradient checkpointing re-runs the hooks during backward."""
from __future__ import annotations

import math
import os
from contextlib import nullcontext
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from . import config as CFG

TOK_PATTERNS = ["tokenizer*", "vocab*", "merges*", "*.txt", "special_tokens_map.json", "added_tokens.json"]


def _local_dir(name, sub=""):
    return Path(CFG.MODELS_DIR) / (sub + name.replace("/", "--"))


def _download(repo, local, patterns):
    from huggingface_hub import snapshot_download
    marker = local / ".complete"
    if not marker.exists():
        local.mkdir(parents=True, exist_ok=True)
        snapshot_download(repo, local_dir=str(local), allow_patterns=patterns)
        marker.write_text("ok")
    return str(local)


def model_path() -> str:
    """Local dir of CFG.MODEL (downloaded on first use); "tiny" with MODEL_TINY=1."""
    if CFG._env("MODEL_TINY", False, bool):
        return "tiny"
    return _download(CFG.MODEL, _local_dir(CFG.MODEL),
                     ["*.json", "*.safetensors", "*.txt", "tokenizer*", "merges*", "vocab*"])


def compute_dtype(device) -> torch.dtype:
    """bf16 on CUDA, float32 on CPU; env DTYPE (float16 / bfloat16 / float32) overrides."""
    name = CFG._env("DTYPE", "")
    if name:
        return {"float16": torch.float16, "fp16": torch.float16, "half": torch.float16, "bfloat16": torch.bfloat16,
                "bf16": torch.bfloat16, "float32": torch.float32, "fp32": torch.float32}[name.lower()]
    return torch.bfloat16 if torch.device(device).type == "cuda" else torch.float32


def film_layers(n_layers):
    spec = str(CFG.FILM_LAYERS).strip()
    if spec == "all":
        return list(range(n_layers))
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return sorted(set(i for i in out if 0 <= i < n_layers))


class LoRALinear(nn.Module):
    """base(x) + scale * B A x; A kaiming, B = 0, fp32 params (cast to the activation dtype)."""

    def __init__(self, base, r, alpha):
        super().__init__()
        self.base = base
        dev = base.weight.device
        self.A = nn.Parameter(torch.empty(r, base.in_features, device=dev, dtype=torch.float32))
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5))
        self.B = nn.Parameter(torch.zeros(base.out_features, r, device=dev, dtype=torch.float32))
        self.scale = alpha / r

    def forward(self, x):
        return self.base(x) + F.linear(F.linear(x, self.A.to(x.dtype)), self.B.to(x.dtype)) * self.scale


def seed_code(z: int) -> torch.Tensor:
    """Fixed code e_z of integer seed z (CPU, float32): any integer works."""
    return torch.randn(CFG.SEED_DIM, generator=torch.Generator().manual_seed(10007 * int(z) + 1))


class SeedModulator(nn.Module):
    def __init__(self, n_layers, d_ff):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(CFG.SEED_DIM, CFG.FILM_HIDDEN), nn.SiLU(),
                                 nn.Linear(CFG.FILM_HIDDEN, CFG.FILM_RANK))
        self.U = nn.Parameter(torch.zeros(n_layers, d_ff, CFG.FILM_RANK))
        if CFG.FILM_INIT > 0:  # std(delta) = std(U) * |m(e_z)|
            with torch.no_grad():
                norm = self.net(torch.stack([seed_code(z) for z in range(max(CFG.N_SEEDS, 1))])).norm(dim=-1).mean()
                self.U.normal_(0.0, CFG.FILM_INIT / max(float(norm), 1e-6))
        self._codes = {}

    def codes(self, seeds):
        for z in seeds:
            if z not in self._codes:
                self._codes[z] = seed_code(z)
        return torch.stack([self._codes[z] for z in seeds]).to(self.U.device)

    def delta(self, seeds):
        """[n_layers, B, d_ff] (in the autocast dtype when autocast is on)."""
        m = self.net(self.codes(seeds))                              # [B, R]
        return torch.einsum("ldr,br->lbd", self.U, m)

    def gains(self, seeds):
        d = self.delta(seeds)
        return 1.0 + CFG.FILM_MAX * torch.tanh(d / CFG.FILM_MAX)


class Policy:
    MODES = ("film", "prompt", "none", "base")

    def __init__(self, path, mode, device, lora=True):
        assert mode in self.MODES, mode
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.mode, self.path, self.device = mode, path, torch.device(device)
        self.dtype = compute_dtype(self.device)
        if path == "tiny":
            from transformers import Qwen2Config, Qwen2ForCausalLM
            self.tok = AutoTokenizer.from_pretrained(_download(CFG.MODEL, _local_dir(CFG.MODEL, "tok--"), TOK_PATTERNS))
            torch.manual_seed(0)
            cfg = Qwen2Config(vocab_size=len(self.tok), hidden_size=64, num_hidden_layers=2, num_attention_heads=4,
                              num_key_value_heads=2, intermediate_size=128, max_position_embeddings=4096,
                              tie_word_embeddings=True, initializer_range=0.1, attention_dropout=0.0,
                              pad_token_id=self.tok.pad_token_id, eos_token_id=self.tok.eos_token_id)
            self.model = Qwen2ForCausalLM(cfg).to(torch.float32 if not CFG._env("DTYPE", "") else self.dtype)
        else:
            self.tok = AutoTokenizer.from_pretrained(path)
            try:
                self.model = AutoModelForCausalLM.from_pretrained(path, dtype=self.dtype)
            except TypeError:
                self.model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=self.dtype)
        self.pad = self.tok.pad_token_id if self.tok.pad_token_id is not None else self.tok.eos_token_id
        m = self.model
        m.to(self.device)
        for p in m.parameters():
            p.requires_grad_(False)
        self.lora = {}
        if lora and mode != "base":
            for li, layer in enumerate(m.model.layers):
                for pname, parent in (("self_attn", layer.self_attn), ("mlp", layer.mlp)):
                    for name in CFG.LORA_TARGETS:
                        if hasattr(parent, name):
                            w = LoRALinear(getattr(parent, name), CFG.LORA_R, CFG.LORA_ALPHA)
                            setattr(parent, name, w)
                            self.lora[f"model.layers.{li}.{pname}.{name}"] = w
        self.mod, self._G, self.layers = None, None, []
        if mode == "film":
            self.layers = film_layers(len(m.model.layers))
            self.mod = SeedModulator(len(self.layers), m.config.intermediate_size).to(self.device)
            for j, li in enumerate(self.layers):
                m.model.layers[li].mlp.down_proj.register_forward_pre_hook(self._hook(j))
        m.config.use_cache = False
        m.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})

    # ------------------------------------------------------------------ seeds
    def _hook(self, j):
        def hook(module, args):
            G = self._G
            if G is None:
                return None
            x = args[0]
            if G.shape[1] != x.shape[0]:
                raise RuntimeError(f"set_seeds got {G.shape[1]} rows, the forward has {x.shape[0]}")
            # the product is taken in float32: in bf16 a gain of 1.003 rounds to 1 (spacing 2^-7 near 1),
            # so small gains would have no effect at all and larger ones would move in coarse steps
            return ((x.float() * G[j].unsqueeze(1)).to(x.dtype),) + tuple(args[1:])
        return hook

    def autocast(self):
        dt = self.device.type
        if dt == "cuda" and self.dtype != torch.float32:
            return torch.autocast("cuda", dtype=self.dtype)
        return nullcontext()

    def set_seeds(self, seeds):
        """Per-row seeds of the next forward / generate call (film); None clears. Call it in the
        same grad mode as the forward."""
        if self.mod is None or seeds is None:
            self._G = None
            return
        with torch.autocast(self.device.type, enabled=False):   # float32 gains (see the hook)
            self._G = self.mod.gains([int(z) for z in seeds]).float()

    def render(self, task, seed=0) -> list[int]:
        from .exp0 import prompts
        content = prompts.problem_prompt(task)
        if self.mode == "prompt":
            content = f"Strategy {int(seed) + 1}.\n\n" + content
        ids = self.tok.apply_chat_template([{"role": "user", "content": content}], add_generation_prompt=True,
                                           tokenize=True)
        if isinstance(ids, dict) or hasattr(ids, "input_ids"):
            ids = ids["input_ids"]
        return list(ids)

    # ------------------------------------------------------------------ parameters
    def trainable(self):
        ps = [p for w in self.lora.values() for p in (w.A, w.B)]
        if self.mod is not None:
            ps += list(self.mod.parameters())
        return ps

    def param_groups(self, lr):
        groups = []
        lp = [p for w in self.lora.values() for p in (w.A, w.B)]
        if lp:
            groups.append({"params": lp, "lr": lr, "name": "lora"})
        if self.mod is not None:
            groups.append({"params": list(self.mod.parameters()), "lr": lr * CFG.FILM_LR_RATIO, "name": "mod"})
        return groups

    def meta(self):
        return {"mode": self.mode, "model": CFG.MODEL, "lora_r": CFG.LORA_R, "lora_alpha": CFG.LORA_ALPHA,
                "lora_targets": list(CFG.LORA_TARGETS), "n_lora": len(self.lora), "seed_dim": CFG.SEED_DIM,
                "film_hidden": CFG.FILM_HIDDEN, "film_rank": CFG.FILM_RANK, "film_layers": self.layers,
                "film_max": CFG.FILM_MAX}

    def state(self) -> dict:
        sd = {"meta": self.meta()}
        for n, w in self.lora.items():
            sd[f"lora.{n}.A"] = w.A.detach().cpu().clone()
            sd[f"lora.{n}.B"] = w.B.detach().cpu().clone()
        if self.mod is not None:
            sd.update({f"mod.{k}": v.detach().cpu().clone() for k, v in self.mod.state_dict().items()})
        return sd

    def load_state(self, sd):
        meta = sd.get("meta", {})
        if meta.get("mode", self.mode) != self.mode:
            print(f"[policy] loading a {meta.get('mode')} state into a {self.mode} policy", flush=True)
        mine = {k: v for k, v in self.state().items() if k != "meta"}
        miss = sorted(set(mine) - set(sd))
        extra = sorted(set(k for k in sd if k != "meta") - set(mine))
        if miss or extra:
            raise KeyError(f"state mismatch: missing {miss[:3]}... ({len(miss)}), unexpected {extra[:3]}... ({len(extra)})")
        with torch.no_grad():
            for n, w in self.lora.items():
                w.A.copy_(sd[f"lora.{n}.A"])
                w.B.copy_(sd[f"lora.{n}.B"])
            if self.mod is not None:
                self.mod.load_state_dict({k[4:]: v for k, v in sd.items() if k.startswith("mod.")})

    @torch.no_grad()
    def gain_stats(self, seeds=None) -> dict:
        """Per-seed mean |gain - 1| and the mean pairwise cosine of the seeds' deltas (all layers)."""
        if self.mod is None:
            return {}
        seeds = list(range(CFG.N_SEEDS)) if seeds is None else list(seeds)
        d = self.mod.delta(seeds).float()                            # [L, S, d_ff]
        g = 1.0 + CFG.FILM_MAX * torch.tanh(d / CFG.FILM_MAX)
        dev = (g - 1).abs().mean(dim=(0, 2)).tolist()
        flat = d.permute(1, 0, 2).reshape(len(seeds), -1)
        nrm = flat.norm(dim=1)
        cos = None
        if len(seeds) > 1 and bool((nrm > 0).all()):
            c = (flat / nrm[:, None]) @ (flat / nrm[:, None]).t()
            iu = torch.triu_indices(len(seeds), len(seeds), 1)
            cos = float(c[iu[0], iu[1]].mean())
        return {"gain_dev": [round(v, 6) for v in dev], "gain_dev_mean": float(sum(dev) / len(dev)),
                "delta_cos": cos, "delta_norm": float(nrm.mean())}
