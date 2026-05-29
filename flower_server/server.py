import flwr as fl
import argparse
import os
import json
import torch
from collections import OrderedDict
from densenet121_model import DenseNet121MultiLabel
from ast_model import ASTMultiLabel
from prototype_fl_model import FLPrototypeModel

TASK_CONFIG = {
    "audio": {
        "model_cls": ASTMultiLabel,
        "num_classes": 2,
        "class_names": ["Crackle", "Wheeze"],
        "default_port": 8080,
        "default_pretrained": "pretrained_audio_multilabel.pth",
        "min_samples": 300,
        "round_prefix": "audio",
        "best_model_file": "best_global_audio.pth",
        "display_name": "Audio",
        "fl_mode": "full",
    },
    "image": {
        "model_cls": DenseNet121MultiLabel,
        "num_classes": 3,
        "class_names": ["Pneumonia", "COPD_Emphysema", "Fibrosis"],
        "default_port": 8081,
        "default_pretrained": "pretrained_xray_multilabel.pth",
        "min_samples": 300,
        "round_prefix": "image",
        "best_model_file": "best_global_image.pth",
        "display_name": "Image",
        "fl_mode": "full",
    },
    "alignment": {
        "model_cls": None,
        "num_classes": 0,
        "class_names": [],
        "default_port": 8082,
        "default_pretrained": None,
        "min_samples": 100,
        "round_prefix": "alignment",
        "best_model_file": "best_global_prototypes.pth",
        "display_name": "Prototype Alignment",
        "fl_mode": "proto",
    },
}


class SaveModelStrategy(fl.server.strategy.FedAvg):
    def __init__(self, task_key, min_samples, job_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_key = task_key
        self.task_cfg = TASK_CONFIG[task_key]
        self.min_samples = min_samples
        self.job_id = job_id

    def aggregate_fit(self, server_round, results, failures):
        eligible_results = []
        skipped_clients = []
        for client_proxy, fit_res in results:
            if fit_res.num_examples >= self.min_samples:
                eligible_results.append((client_proxy, fit_res))
            else:
                client_id = getattr(client_proxy, "cid", "unknown")
                skipped_clients.append((client_id, fit_res.num_examples))

        if skipped_clients:
            skipped_info = ", ".join(
                [f"{client_id}:{num_examples}" for client_id, num_examples in skipped_clients]
            )
            print(
                f"[{self.task_cfg['display_name']}] Round {server_round}: bo {len(skipped_clients)} client duoi nguong {self.min_samples} mau -> {skipped_info}"
            )

        if len(eligible_results) < self.min_fit_clients:
            print(
                f"[{self.task_cfg['display_name']}] Round {server_round}: chi co {len(eligible_results)} client hop le (< min_fit_clients={self.min_fit_clients}), bo qua aggregate."
            )
            return None, {}

        print(f"\n[{self.task_cfg['display_name']}] Round {server_round}: Tong hop {len(eligible_results)} client...")
        aggregated_weights, aggregated_metrics = super().aggregate_fit(server_round, eligible_results, failures)

        if aggregated_weights is not None:
            print(f"\n{'='*70}")
            print(f"📊 AGGREGATION REPORT - Round {server_round}")
            print(f"{'='*70}")

            total_samples = 0
            total_loss = 0.0
            total_auroc = 0.0
            total_auprc = 0.0
            total_f1 = 0.0
            total_precision = 0.0
            total_recall = 0.0
            metric_count = 0  # count of clients with valid auroc
            client_metrics = []
            class_names = self.task_cfg.get("class_names", [])
            # Aggregate per-class metrics weighted by samples
            aggregated_per_class_auroc = {}
            aggregated_per_class_auprc = {}
            for client_proxy, fit_res in eligible_results:
                client_id = getattr(client_proxy, "cid", "unknown")
                loss_val = fit_res.metrics.get('loss', 0.0) if fit_res.metrics else 0.0
                auroc_val = fit_res.metrics.get('auroc_macro') if fit_res.metrics else None
                auprc_val = fit_res.metrics.get('auprc_macro') if fit_res.metrics else None
                f1_val = fit_res.metrics.get('f1_macro') if fit_res.metrics else None
                prec_val = fit_res.metrics.get('precision_macro') if fit_res.metrics else None
                rec_val = fit_res.metrics.get('recall_macro') if fit_res.metrics else None
                per_class_auroc = fit_res.metrics.get('per_class_auroc', {}) if fit_res.metrics else {}
                per_class_auprc = fit_res.metrics.get('per_class_auprc', {}) if fit_res.metrics else {}
                print(f"  ✅ Client {client_id}: {fit_res.num_examples} samples, Loss: {loss_val:.4f}", end="")
                if auroc_val is not None:
                    print(f", AUROC: {auroc_val:.4f}", end="")
                if f1_val is not None:
                    print(f", F1: {f1_val:.4f}", end="")
                print()
                total_samples += fit_res.num_examples
                total_loss += loss_val * fit_res.num_examples
                if auroc_val is not None:
                    total_auroc += auroc_val * fit_res.num_examples
                if auprc_val is not None:
                    total_auprc += auprc_val * fit_res.num_examples
                if f1_val is not None:
                    total_f1 += f1_val * fit_res.num_examples
                if prec_val is not None:
                    total_precision += prec_val * fit_res.num_examples
                if rec_val is not None:
                    total_recall += rec_val * fit_res.num_examples
                if auroc_val is not None:
                    metric_count += fit_res.num_examples
                # Aggregate per-class AUROC
                for k, v in per_class_auroc.items():
                    if k not in aggregated_per_class_auroc:
                        aggregated_per_class_auroc[k] = {"sum": 0.0, "count": 0}
                    aggregated_per_class_auroc[k]["sum"] += v * fit_res.num_examples
                    aggregated_per_class_auroc[k]["count"] += fit_res.num_examples
                # Aggregate per-class AUPRC
                for k, v in per_class_auprc.items():
                    if k not in aggregated_per_class_auprc:
                        aggregated_per_class_auprc[k] = {"sum": 0.0, "count": 0}
                    aggregated_per_class_auprc[k]["sum"] += v * fit_res.num_examples
                    aggregated_per_class_auprc[k]["count"] += fit_res.num_examples
                client_metrics.append({
                    "client_id": client_id,
                    "client_name": client_id,
                    "num_samples": fit_res.num_examples,
                    "loss": round(loss_val, 6),
                    "auroc_macro": round(auroc_val, 6) if auroc_val is not None else None,
                    "auprc_macro": round(auprc_val, 6) if auprc_val is not None else None,
                    "f1_macro": round(f1_val, 6) if f1_val is not None else None,
                    "precision_macro": round(prec_val, 6) if prec_val is not None else None,
                    "recall_macro": round(rec_val, 6) if rec_val is not None else None,
                    "per_class_auroc": {k: round(v, 6) for k, v in per_class_auroc.items()} if per_class_auroc else {},
                    "per_class_auprc": {k: round(v, 6) for k, v in per_class_auprc.items()} if per_class_auprc else {},
                })
            avg_loss = total_loss / total_samples if total_samples > 0 else 0.0
            avg_auroc = total_auroc / metric_count if metric_count > 0 else None
            avg_auprc = total_auprc / metric_count if metric_count > 0 else None
            avg_f1 = total_f1 / metric_count if metric_count > 0 else None
            avg_precision = total_precision / metric_count if metric_count > 0 else None
            avg_recall = total_recall / metric_count if metric_count > 0 else None
            # Final per-class aggregates
            final_per_class_auroc = {}
            for k, v in aggregated_per_class_auroc.items():
                final_per_class_auroc[k] = round(v["sum"] / v["count"], 6) if v["count"] > 0 else 0.0
            final_per_class_auprc = {}
            for k, v in aggregated_per_class_auprc.items():
                final_per_class_auprc[k] = round(v["sum"] / v["count"], 6) if v["count"] > 0 else 0.0
            print(f"  📈 Total samples: {total_samples}, Avg Loss: {avg_loss:.4f}", end="")
            if avg_auroc is not None:
                print(f", Avg AUROC: {avg_auroc:.4f}", end="")
            if avg_f1 is not None:
                print(f", Avg F1: {avg_f1:.4f}", end="")
            print()

            ndarrays = fl.common.parameters_to_ndarrays(aggregated_weights)
            dummy_model = self.task_cfg["model_cls"]()
            params_dict = zip(dummy_model.state_dict().keys(), ndarrays)
            state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})

            dummy_model.load_state_dict(state_dict, strict=True)

            print(f"\n📋 MODEL WEIGHTS VERIFICATION:")
            for name, param in list(dummy_model.state_dict().items())[:3]:
                print(f"  {name}: shape={param.shape}, dtype={param.dtype}")
            print(f"  ... (total {len(dummy_model.state_dict())} layers)")

            os.makedirs("aggregated_models", exist_ok=True)
            save_path = f"aggregated_models/{self.task_cfg['round_prefix']}_round_{server_round}.pth"
            torch.save(dummy_model.state_dict(), save_path)
            print(f"\n💾 Da luu model: {save_path}")

            torch.save(dummy_model.state_dict(), self.task_cfg["best_model_file"])
            print(f"✅ Da cap nhat: {self.task_cfg['best_model_file']}")
            print(f"{'='*70}\n")

            # Emit structured events for LogParser — includes all metrics + per-client details
            event_data = {
                'task': self.task_key,
                'round': server_round,
                'num_clients': len(eligible_results),
                'num_skipped': len(skipped_clients),
                'total_samples': total_samples,
                'loss': round(avg_loss, 6),
                'auroc_macro': round(avg_auroc, 6) if avg_auroc is not None else None,
                'auprc_macro': round(avg_auprc, 6) if avg_auprc is not None else None,
                'f1_macro': round(avg_f1, 6) if avg_f1 is not None else None,
                'precision_macro': round(avg_precision, 6) if avg_precision is not None else None,
                'recall_macro': round(avg_recall, 6) if avg_recall is not None else None,
                'per_class_auroc': final_per_class_auroc,
                'per_class_auprc': final_per_class_auprc,
                'client_metrics': client_metrics,
            }
            print(f"EVENT:round_completed:{json.dumps(event_data)}")
            print(f"EVENT:checkpoint_saved:{json.dumps({'task': self.task_key, 'round': server_round, 'path': save_path})}")

        return aggregated_weights, aggregated_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flower Server")
    parser.add_argument("--task", type=str, choices=["audio", "image", "alignment"], default="audio")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--min-fit-clients", type=int, default=2)
    parser.add_argument("--min-available-clients", type=int, default=2)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--pretrained", type=str, default=None)
    parser.add_argument("--min-samples", type=int, default=None)
    parser.add_argument("--fl-mode", type=str, choices=["full", "proto"], default=None)
    parser.add_argument("--config-path", type=str, default=None, help="Path to run_config.json from FastAPI")
    parser.add_argument("--job-id", type=str, default=None, help="Training job UUID")
    args = parser.parse_args()

    # Load runtime config from FastAPI if provided
    run_config = {}
    if args.config_path and os.path.exists(args.config_path):
        with open(args.config_path, "r") as f:
            run_config = json.load(f)
        args.job_id = args.job_id or run_config.get("job_id")

    cfg = TASK_CONFIG[args.task]
    selected_port = args.port if args.port is not None else cfg["default_port"]
    pretrained_path = args.pretrained if args.pretrained is not None else cfg["default_pretrained"]
    selected_min_samples = args.min_samples if args.min_samples is not None else cfg["min_samples"]

    # Override from run_config if present
    if run_config:
        selected_min_samples = run_config.get("min_samples", selected_min_samples)
        pretrained_path = run_config.get("pretrained_path") or pretrained_path

    fl_mode = args.fl_mode if args.fl_mode is not None else cfg.get("fl_mode", "full")

    print(f"EVENT:job_started:{json.dumps({'task': args.task, 'job_id': args.job_id or 'unknown', 'rounds': args.rounds, 'min_clients': args.min_fit_clients, 'min_samples': selected_min_samples, 'port': selected_port, 'fl_mode': fl_mode})}")

    print(f"\n{'='*70}")
    print(f"🔧 INITIALIZING {cfg['display_name'].upper()} MODEL (FL mode: {fl_mode})")
    print(f"{'='*70}")

    if fl_mode == "proto":
        image_ckpt = "pretrained_xray_multilabel.pth"
        audio_ckpt = "pretrained_audio_multilabel.pth"
        print(f"Dang nap Prototype FL Model...")
        prototype_model = FLPrototypeModel(
            image_pretrained_path=image_ckpt,
            audio_pretrained_path=audio_ckpt,
        )
        if os.path.exists(image_ckpt):
            print(f"✅ Loaded image checkpoint: {image_ckpt}")
        if os.path.exists(audio_ckpt):
            print(f"✅ Loaded audio checkpoint: {audio_ckpt}")
        shareable = prototype_model.shareable_state_dict()
        print(f"   Shareable params: {len(shareable)} tensors")
        print(f"   - Disease prototypes: 3x256")
        print(f"   - Acoustic prototypes: 2x256")
        print(f"   - Projection heads: image(1024->256) + audio(768->256)")

        initial_weights = [v.cpu().numpy() for v in shareable.values()]
        initial_parameters = fl.common.ndarrays_to_parameters(initial_weights)
        dummy_model = prototype_model
    else:
        print(f"Dang nap Pretrain {cfg['display_name']} lam trong so khoi diem...")
        dummy_model = cfg["model_cls"]()
        if os.path.exists(pretrained_path):
            state_dict = torch.load(pretrained_path, map_location="cpu")
            print(f"✅ File tim thay: {pretrained_path} ({len(state_dict)} layers)")

            try:
                dummy_model.load_state_dict(state_dict, strict=True)
                print(f"✅ Da nap trong so thanh cong (100% khop mo hinh)!")
                num_classes = cfg.get("num_classes", 1)
                class_names = cfg.get("class_names", [])
                print(f"\n   Model info:")
                print(f"   - Output: {num_classes} logits (Multi-label: {', '.join(class_names)})")
                print(f"   - Loss: BCEWithLogitsLoss")
                print(f"   - Embedding dim: 256")
            except RuntimeError as e:
                print(f"⚠️  Canh bao: {str(e)}")
                print(f"   Fallback: Load voi strict=False")
                dummy_model.load_state_dict(state_dict, strict=False)
        else:
            print(f"⚠️  Khong tim thay {pretrained_path}")
            print(f"   Dung trong so khoi tao ngau nhien.")

        initial_weights = [val.cpu().numpy() for _, val in dummy_model.state_dict().items()]
        initial_parameters = fl.common.ndarrays_to_parameters(initial_weights)

    print(f"{'='*70}\n")

    strategy = SaveModelStrategy(
        task_key=args.task,
        min_samples=selected_min_samples,
        job_id=args.job_id,
        min_fit_clients=args.min_fit_clients,
        min_available_clients=args.min_available_clients,
        initial_parameters=initial_parameters,
    )

    print(
        f"Khoi dong FL Server {cfg['display_name']} tren cong {selected_port}... "
        f"(So vong cau hinh: {args.rounds}, min_samples: {selected_min_samples})"
    )
    print(f"EVENT:server_ready:{json.dumps({'task': args.task, 'port': selected_port, 'job_id': args.job_id or 'unknown'})}")

    fl.server.start_server(
        server_address=f"0.0.0.0:{selected_port}",
        config=fl.server.ServerConfig(num_rounds=args.rounds),
        strategy=strategy,
    )

    print(f"EVENT:job_completed:{json.dumps({'task': args.task, 'job_id': args.job_id or 'unknown'})}")
