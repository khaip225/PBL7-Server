"""Prototype-Guided Federated Learning Server — Flower Integration.

Implements Selective FedAvg:
  - image projection params:  aggregated from image + multimodal clients only
  - audio projection params:  aggregated from audio + multimodal clients only
  - prototypes:               aggregated from ALL clients

Supports 3 task types:
  - image:       DenseNet121Encoder-based FL (prototype-only sharing)
  - audio:       ASTEncoder-based FL (prototype-only sharing)
  - alignment:   Full prototype alignment FL (both modalities)

Design matched to notebook pbl7-fl.ipynb (fedavg_selective).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import OrderedDict
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import flwr as fl

# Path setup for shared modules
_server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _server_root not in sys.path:
    sys.path.insert(0, _server_root)

_client_path = os.path.join(_server_root, "..", "PBL7-Client")
if os.path.exists(_client_path) and _client_path not in sys.path:
    sys.path.insert(0, _client_path)

# Import shared components from Client (single source of truth)
from shared.encoder_models import DenseNet121Encoder, ASTEncoder
from shared.momentum_prototype import MomentumPrototypeModule


# ═══════════════════════════════════════════════════════════════════════════
# Task Configuration
# ═══════════════════════════════════════════════════════════════════════════

TASK_CONFIG = {
    "audio": {
        "display_name": "Audio Prototype FL",
        "default_port": 8080,
        "num_classes": 3,       # normal, crackle, wheeze
        "class_names": ["normal", "crackle", "wheeze"],
        "min_samples": 100,
        "round_prefix": "audio_proto",
        "best_model_file": "best_global_audio_proto.pth",
        "fl_mode": "proto",
    },
    "image": {
        "display_name": "Image Prototype FL",
        "default_port": 8081,
        "num_classes": 4,       # Normal, Pneumonia, COPD, Fibrosis
        "class_names": ["Normal", "Pneumonia", "COPD_Emphysema", "Fibrosis"],
        "min_samples": 100,
        "round_prefix": "image_proto",
        "best_model_file": "best_global_image_proto.pth",
        "fl_mode": "proto",
    },
    "alignment": {
        "display_name": "Prototype Alignment FL",
        "default_port": 8082,
        "num_classes": 0,
        "class_names": [],
        "min_samples": 50,
        "round_prefix": "alignment_proto",
        "best_model_file": "best_global_prototypes.pth",
        "fl_mode": "proto",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# FedAvg Selective — core aggregation logic
# ═══════════════════════════════════════════════════════════════════════════

def fedavg_selective(
    client_states: list[OrderedDict],
    client_weights: list[float],
    client_modalities: list[str],
) -> OrderedDict:
    """Selective FedAvg aggregation.

    - img_proj.*   → only from image + multimodal clients
    - aud_proj.*   → only from audio + multimodal clients
    - proto.*      → from ALL clients
    """
    weights_sqrt = [w ** 0.5 for w in client_weights]
    global_state = OrderedDict()

    if not client_states:
        return global_state

    first_keys = list(client_states[0].keys())

    # --- Image projection (image + multimodal) ---
    img_pairs = [
        (s, w) for s, w, m in zip(client_states, weights_sqrt, client_modalities)
        if m in ("image", "multimodal")
    ]
    img_total = sum(w for _, w in img_pairs) or 1.0
    for k in [k for k in first_keys if k.startswith("img_proj.")]:
        global_state[k] = sum(s[k].float() * w for s, w in img_pairs) / img_total

    # --- Audio projection (audio + multimodal) ---
    aud_pairs = [
        (s, w) for s, w, m in zip(client_states, weights_sqrt, client_modalities)
        if m in ("audio", "multimodal")
    ]
    aud_total = sum(w for _, w in aud_pairs) or 1.0
    for k in [k for k in first_keys if k.startswith("aud_proj.")]:
        global_state[k] = sum(s[k].float() * w for s, w in aud_pairs) / aud_total

    # --- Prototypes (all clients) ---
    total_w = sum(weights_sqrt) or 1.0
    for k in [k for k in first_keys if k.startswith("proto.")]:
        global_state[k] = sum(
            s[k].float() * w for s, w in zip(client_states, weights_sqrt)
        ) / total_w

    return global_state


# ═══════════════════════════════════════════════════════════════════════════
# Custom Flower Strategy
# ═══════════════════════════════════════════════════════════════════════════

class SelectiveAggregationStrategy(fl.server.strategy.FedAvg):
    """Custom FedAvg strategy with:
    - Selective aggregation by modality (fedavg_selective)
    - Per-round metrics logging with prototype structure tracking
    - Checkpoint saving
    - EVENT emission for LogParser / WebSocket
    """

    def __init__(
        self,
        task_key: str,
        min_samples: int,
        job_id: str | None = None,
        save_dir: str = "aggregated_models",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.task_key = task_key
        self.task_cfg = TASK_CONFIG[task_key]
        self.min_samples = min_samples
        self.job_id = job_id
        self.save_dir = save_dir

        os.makedirs(save_dir, exist_ok=True)

    def aggregate_fit(
        self,
        server_round: int,
        results: list[tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: list[BaseException],
    ) -> tuple[fl.common.Parameters | None, dict]:
        """Run selective FedAvg aggregation for one round."""
        # --- Log failures (disconnected clients) ---
        if failures:
            print(f"[{self.task_cfg['display_name']}] Round {server_round}: "
                  f"⚠️  {len(failures)} client(s) disconnected!")
            for i, exc in enumerate(failures):
                print(f"  ❌ Failure {i+1}: {type(exc).__name__}: {exc}")

        # --- Filter by min_samples ---
        eligible = []
        skipped = []
        for cp, fit_res in results:
            if fit_res.num_examples >= self.min_samples:
                eligible.append((cp, fit_res))
            else:
                cid = getattr(cp, "cid", "unknown")
                skipped.append((cid, fit_res.num_examples))

        if skipped:
            info = ", ".join(f"{c}:{n}" for c, n in skipped)
            print(f"[{self.task_cfg['display_name']}] Round {server_round}: "
                  f"SKIP {len(skipped)} clients below {self.min_samples} samples → {info}")

        if len(eligible) < self.min_fit_clients:
            skip_data = {
                "task": self.task_key,
                "round": server_round,
                "eligible": len(eligible),
                "min_required": self.min_fit_clients,
                "reason": f"need {self.min_fit_clients} clients, got {len(eligible)}",
            }
            print(f"[{self.task_cfg['display_name']}] Round {server_round}: "
                  f"only {len(eligible)} eligible (< {self.min_fit_clients}), skip aggregation.")
            print(f"EVENT:round_skipped:{json.dumps(skip_data)}")
            return None, {}

        # --- Extract modality info from each client ---
        client_modalities: list[str] = []
        for cp, fit_res in eligible:
            cid = getattr(cp, "cid", "unknown")
            modality = fit_res.metrics.get("modality", "image") if fit_res.metrics else "image"
            client_modalities.append(modality)

        # --- Convert results to OrderedDicts ---
        client_states = []
        client_weights: list[float] = []
        total_client_m = 0.0
        total_client_loss = 0.0

        print(f"\n{'='*70}")
        print(f"📊 AGGREGATION — Round {server_round}")
        print(f"{'='*70}")

        for i, (cp, fit_res) in enumerate(eligible):
            cid = getattr(cp, "cid", f"client_{i}")
            ndarrays = fl.common.parameters_to_ndarrays(fit_res.parameters)

            # Reconstruct OrderedDict from server's dummy model keys
            keys = list(self._dummy_state_keys)
            state = OrderedDict()
            for k, arr in zip(keys, ndarrays):
                state[k] = torch.tensor(arr)

            client_states.append(state)
            client_weights.append(float(fit_res.num_examples))

            loss_val = fit_res.metrics.get("loss", 0.0) if fit_res.metrics else 0.0
            mod = fit_res.metrics.get("modality", "?") if fit_res.metrics else "?"
            print(f"  ✅ {cid} ({mod}): {fit_res.num_examples} samples, loss={loss_val:.4f}")

            total_client_m += float(fit_res.num_examples)
            total_client_loss += loss_val * float(fit_res.num_examples)

        if not client_states:
            return None, {}

        # --- Run selective FedAvg ---
        aggregated_state = fedavg_selective(client_states, client_weights, client_modalities)

        avg_loss = total_client_loss / total_client_m if total_client_m > 0 else 0.0

        # Count aggregated tensors by type
        n_img = sum(1 for k in aggregated_state if k.startswith("img_proj."))
        n_aud = sum(1 for k in aggregated_state if k.startswith("aud_proj."))
        n_proto = sum(1 for k in aggregated_state if k.startswith("proto."))
        print(f"  📦 Aggregated: {n_img} img_proj + {n_aud} aud_proj + {n_proto} proto = {len(aggregated_state)} tensors")
        print(f"  📈 Avg loss: {avg_loss:.4f}")

        # --- Compute prototype structure metrics ---
        proto_metrics = self._compute_proto_metrics(aggregated_state)
        if proto_metrics:
            print(f"  🎯 Prototype structure: {json.dumps(proto_metrics)}")

        # --- Save checkpoint ---
        save_path = os.path.join(
            self.save_dir,
            f"{self.task_cfg['round_prefix']}_round_{server_round}.pth",
        )
        torch.save({k: v for k, v in aggregated_state.items()}, save_path)

        # Also save as best
        best_path = self.task_cfg["best_model_file"]
        torch.save({k: v for k, v in aggregated_state.items()}, best_path)

        print(f"  💾 Saved: {save_path}")
        print(f"  ✅ Best: {best_path}")
        print(f"{'='*70}\n")

        # --- Convert back to Flower Parameters ---
        agg_ndarrays = [aggregated_state[k].numpy() for k in aggregated_state]
        agg_params = fl.common.ndarrays_to_parameters(agg_ndarrays)

        # --- Emit event for LogParser ---
        event = {
            "task": self.task_key,
            "round": server_round,
            "num_clients": len(eligible),
            "num_skipped": len(skipped),
            "total_samples": int(total_client_m),
            "loss": round(avg_loss, 6),
            "proto_metrics": proto_metrics,
            "n_img_proj": n_img,
            "n_aud_proj": n_aud,
            "n_proto": n_proto,
            "client_modalities": client_modalities,
        }
        print(f"EVENT:round_completed:{json.dumps(event)}")
        print(f"EVENT:checkpoint_saved:{json.dumps({'task': self.task_key, 'round': server_round, 'path': save_path})}")

        # --- Build metrics dict ---
        metrics = {
            "loss": round(avg_loss, 6),
            "num_clients": len(eligible),
            "proto_metrics": proto_metrics or {},
        }

        return agg_params, metrics

    # ------------------------------------------------------------------
    # Dummy model for key tracking
    # ------------------------------------------------------------------
    @property
    def _dummy_state_keys(self) -> list[str]:
        if not hasattr(self, "__dummy_keys_cache"):
            # Build dummy encoder to get state keys
            dummy_img = DenseNet121Encoder(embedding_dim=256)
            dummy_aud = ASTEncoder(embedding_dim=256)
            dummy_proto = MomentumPrototypeModule(dim=256)

            keys = []
            for k in dummy_img.projection.state_dict():
                keys.append(f"img_proj.{k}")
            for k in dummy_aud.projection.state_dict():
                keys.append(f"aud_proj.{k}")
            for k, _ in dummy_proto.named_parameters():
                keys.append(f"proto.{k}")

            self.__dummy_keys_cache = keys
        return self.__dummy_keys_cache

    # ------------------------------------------------------------------
    # Prototype structure analysis
    # ------------------------------------------------------------------
    def _compute_proto_metrics(self, state: OrderedDict) -> dict | None:
        """Compute prototype similarity metrics from aggregated state."""
        try:
            # Extract prototype tensors
            proto_names = [
                "p_normal_img", "p_normal_aud",
                "p_pneumonia", "p_copd", "p_fibrosis",
                "p_crackle", "p_wheeze",
            ]
            protos: dict[str, torch.Tensor] = {}
            for name in proto_names:
                key = f"proto.{name}"
                if key in state:
                    protos[name] = state[key].float()

            if len(protos) < 7:
                return None

            # Key similarity pairs
            pairs = {
                "crackle_pneumonia":    ("p_crackle",    "p_pneumonia"),
                "crackle_fibrosis":     ("p_crackle",    "p_fibrosis"),
                "wheeze_copd":          ("p_wheeze",     "p_copd"),
                "pneumonia_fibrosis":   ("p_pneumonia",  "p_fibrosis"),
                "crackle_wheeze":       ("p_crackle",    "p_wheeze"),
                "normal_img_aud":       ("p_normal_img", "p_normal_aud"),
            }

            result = {}
            for label, (n1, n2) in pairs.items():
                if n1 in protos and n2 in protos:
                    sim = float(F.cosine_similarity(
                        protos[n1].unsqueeze(0), protos[n2].unsqueeze(0)
                    ))
                    result[label] = round(sim, 4)

            # Prototype norms
            norms = {n.replace("p_", "norm_"): round(float(protos[n].norm()), 4)
                     for n in proto_names if n in protos}
            result.update(norms)

            return result
        except Exception as e:
            print(f"  ⚠️  Proto metrics error: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════
# Dummy model builder for initial parameters
# ═══════════════════════════════════════════════════════════════════════════

def build_initial_parameters(task_key: str, pretrained_path: str | None = None) -> fl.common.Parameters:
    """Build initial parameters (prototypes + projection heads) as Flower Parameters.

    Loads pretrained weights if available, otherwise random init.
    """
    embed_dim = 256

    img_enc = DenseNet121Encoder(embedding_dim=embed_dim, dropout=0.2)
    aud_enc = ASTEncoder(embedding_dim=embed_dim, dropout=0.2)
    proto   = MomentumPrototypeModule(dim=embed_dim, momentum=0.99)

    # Try loading pretrained
    if pretrained_path and os.path.exists(pretrained_path):
        print(f"  📥 Loading pretrained from: {pretrained_path}")
        try:
            checkpoint = torch.load(pretrained_path, map_location="cpu")

            # Check what format the checkpoint is
            if "image_encoder" in checkpoint:
                # Notebook format: stage3/stage4 checkpoint
                img_enc.load_state_dict(checkpoint["image_encoder"], strict=False)
                aud_enc.load_state_dict(checkpoint["audio_encoder"], strict=False)
                proto.load_state_dict(checkpoint["prototype_module"], strict=False)
                print(f"  ✅ Loaded notebook checkpoint (round {checkpoint.get('round', '?')})")
            elif "img_proj.0.weight" in checkpoint:
                # Aggregated state dict format
                for k, v in checkpoint.items():
                    if k.startswith("img_proj."):
                        sub_key = k.replace("img_proj.", "")
                        if sub_key in img_enc.projection.state_dict():
                            img_enc.projection.state_dict()[sub_key].copy_(v)
                    elif k.startswith("aud_proj."):
                        sub_key = k.replace("aud_proj.", "")
                        if sub_key in aud_enc.projection.state_dict():
                            aud_enc.projection.state_dict()[sub_key].copy_(v)
                    elif k.startswith("proto."):
                        sub_key = k.replace("proto.", "")
                        if hasattr(proto, sub_key):
                            getattr(proto, sub_key).data.copy_(v)
                print("  ✅ Loaded aggregated state dict checkpoint")
            else:
                img_enc.load_state_dict(checkpoint, strict=False)
                print("  ✅ Loaded checkpoint (partial match)")
        except Exception as e:
            print(f"  ⚠️  Failed to load pretrained: {e}")
            print("  → Using random initialization")
    else:
        print("  → No pretrained found, using random initialization")

    # Build initial state
    state = OrderedDict()
    for k, v in img_enc.projection.state_dict().items():
        state[f"img_proj.{k}"] = v
    for k, v in aud_enc.projection.state_dict().items():
        state[f"aud_proj.{k}"] = v
    for k, v in proto.named_parameters():
        state[f"proto.{k}"] = v.data

    ndarrays = [val.cpu().numpy() for val in state.values()]
    params = fl.common.ndarrays_to_parameters(ndarrays)

    print(f"  📦 Initial parameters: {len(ndarrays)} tensors")
    total_size = sum(arr.nbytes for arr in ndarrays)
    print(f"  📏 Total size: {total_size / 1024:.1f} KB (~3MB typical for full weights)")

    return params, state.keys()


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prototype-Guided FL Server (Flower)")
    parser.add_argument("--task", type=str, default="image",
                        choices=["audio", "image", "alignment"],
                        help="Task type")
    parser.add_argument("--rounds", type=int, default=10,
                        help="Number of FL rounds")
    parser.add_argument("--min-fit-clients", type=int, default=1,
                        help="Minimum clients for aggregation")
    parser.add_argument("--min-available-clients", type=int, default=1,
                        help="Minimum available clients")
    parser.add_argument("--port", type=int, default=None,
                        help="Override default port")
    parser.add_argument("--pretrained", type=str, default=None,
                        help="Path to pretrained checkpoint")
    parser.add_argument("--min-samples", type=int, default=None,
                        help="Override minimum samples threshold")
    parser.add_argument("--config-path", type=str, default=None,
                        help="Path to run_config.json from FastAPI")
    parser.add_argument("--job-id", type=str, default=None,
                        help="Training job UUID")
    args = parser.parse_args()

    # Load runtime config from FastAPI if provided
    run_config = {}
    if args.config_path and os.path.exists(args.config_path):
        with open(args.config_path, "r") as f:
            run_config = json.load(f)
        args.job_id = args.job_id or run_config.get("job_id")

    cfg = TASK_CONFIG[args.task]
    port = args.port if args.port is not None else cfg["default_port"]
    min_samples = args.min_samples if args.min_samples is not None else cfg["min_samples"]

    if run_config:
        min_samples = run_config.get("min_samples", min_samples)

    print(f"\n{'='*70}")
    print(f"🔧 PROTOTYPE-GUIDED FL SERVER — {cfg['display_name']}")
    print(f"{'='*70}")
    print(f"   Task:        {args.task}")
    print(f"   Port:        {port}")
    print(f"   Rounds:      {args.rounds}")
    print(f"   Min clients: {args.min_fit_clients}")
    print(f"   Min samples: {min_samples}")
    print(f"   Job ID:      {args.job_id or 'N/A'}")
    print(f"   Mode:        PROTOTYPE-ONLY sharing")
    print(f"   What's synced: img_proj + aud_proj + prototypes")
    print(f"   What's local:  encoder backbones (DenseNet121 features, ViT transformer)")
    print(f"{'='*70}\n")

    # Emit job start event
    print(f"EVENT:job_started:{json.dumps(dict(task=args.task, job_id=args.job_id or 'unknown', rounds=args.rounds, min_clients=args.min_fit_clients, min_samples=min_samples, port=port, fl_mode='proto'))}")

    # Build initial parameters
    print(f"📦 Building initial parameters...")
    initial_params, _ = build_initial_parameters(args.task, args.pretrained)

    # Build strategy
    strategy = SelectiveAggregationStrategy(
        task_key=args.task,
        min_samples=min_samples,
        job_id=args.job_id,
        min_fit_clients=args.min_fit_clients,
        min_available_clients=args.min_available_clients,
        initial_parameters=initial_params,
    )

    print(f"\n✅ Server ready")
    print(f"EVENT:server_ready:{json.dumps({'task': args.task, 'port': port, 'job_id': args.job_id or 'unknown'})}")
    print(f"\nListening on 0.0.0.0:{port}...\n")

    # Start Flower server
    fl.server.start_server(
        server_address=f"0.0.0.0:{port}",
        config=fl.server.ServerConfig(num_rounds=args.rounds),
        strategy=strategy,
    )

    print(f"EVENT:job_completed:{json.dumps(dict(task=args.task, job_id=args.job_id or 'unknown'))}")
