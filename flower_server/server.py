import flwr as fl
import argparse
import os
import json
import torch
from collections import OrderedDict
from cnn14_model import CNN14
from resnet18_model import ResNet18


TASK_CONFIG = {
    "audio": {
        "model_cls": CNN14,
        "default_port": 8080,
        "default_pretrained": "pretrained_audio.pth",
        "min_samples": 300,
        "round_prefix": "audio",
        "best_model_file": "best_global_audio.pth",
        "display_name": "Audio",
    },
    "image": {
        "model_cls": ResNet18,
        "default_port": 8081,
        "default_pretrained": "pretrained_xray.pth",
        "min_samples": 300,
        "round_prefix": "image",
        "best_model_file": "best_global_image.pth",
        "display_name": "Image",
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
            total_acc = 0.0
            acc_count = 0
            client_metrics = []
            for client_proxy, fit_res in eligible_results:
                client_id = getattr(client_proxy, "cid", "unknown")
                loss_val = fit_res.metrics.get('loss', 0.0) if fit_res.metrics else 0.0
                acc_val = fit_res.metrics.get('accuracy') if fit_res.metrics else None
                print(f"  ✅ Client {client_id}: {fit_res.num_examples} samples, Loss: {loss_val:.4f}", end="")
                if acc_val is not None:
                    print(f", Acc: {acc_val:.4f}")
                else:
                    print()
                total_samples += fit_res.num_examples
                total_loss += loss_val * fit_res.num_examples
                if acc_val is not None:
                    total_acc += acc_val * fit_res.num_examples
                    acc_count += fit_res.num_examples
                client_metrics.append({
                    "client_id": client_id,
                    "client_name": client_id,
                    "num_samples": fit_res.num_examples,
                    "loss": round(loss_val, 6),
                    "accuracy": round(acc_val, 6) if acc_val is not None else None,
                })
            avg_loss = total_loss / total_samples if total_samples > 0 else 0.0
            avg_accuracy = total_acc / acc_count if acc_count > 0 else None
            print(f"  📈 Total samples: {total_samples}, Avg Loss: {avg_loss:.4f}", end="")
            if avg_accuracy is not None:
                print(f", Avg Acc: {avg_accuracy:.4f}")
            else:
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

            # Emit structured events for LogParser — includes loss, accuracy + per-client metrics
            event_data = {
                'task': self.task_key,
                'round': server_round,
                'num_clients': len(eligible_results),
                'num_skipped': len(skipped_clients),
                'total_samples': total_samples,
                'loss': round(avg_loss, 6),
                'accuracy': round(avg_accuracy, 6) if avg_accuracy is not None else None,
                'client_metrics': client_metrics,
            }
            print(f"EVENT:round_completed:{json.dumps(event_data)}")
            print(f"EVENT:checkpoint_saved:{json.dumps({'task': self.task_key, 'round': server_round, 'path': save_path})}")

        return aggregated_weights, aggregated_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flower Server")
    parser.add_argument("--task", type=str, choices=["audio", "image"], default="audio")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--min-fit-clients", type=int, default=2)
    parser.add_argument("--min-available-clients", type=int, default=2)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--pretrained", type=str, default=None)
    parser.add_argument("--min-samples", type=int, default=None)
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

    print(f"EVENT:job_started:{json.dumps({'task': args.task, 'job_id': args.job_id or 'unknown', 'rounds': args.rounds, 'min_clients': args.min_fit_clients, 'min_samples': selected_min_samples, 'port': selected_port})}")

    print(f"\n{'='*70}")
    print(f"🔧 INITIALIZING {cfg['display_name'].upper()} MODEL")
    print(f"{'='*70}")
    print(f"Dang nap Pretrain {cfg['display_name']} lam trong so khoi diem...")
    dummy_model = cfg["model_cls"]()
    if os.path.exists(pretrained_path):
        state_dict = torch.load(pretrained_path, map_location="cpu")
        print(f"✅ File tim thay: {pretrained_path} ({len(state_dict)} layers)")

        try:
            dummy_model.load_state_dict(state_dict, strict=True)
            print(f"✅ Da nap trong so thanh cong (100% khop mo hinh)!")
            print(f"\n   Model info:")
            print(f"   - Output: 1 neuron (Binary Classification)")
            print(f"   - Loss: BCEWithLogitsLoss")
            print(f"   - Inference: sigmoid(output) > 0.5")
        except RuntimeError as e:
            print(f"⚠️  Canh bao: {str(e)}")
            print(f"   Fallback: Load voi strict=False")
            dummy_model.load_state_dict(state_dict, strict=False)
    else:
        print(f"⚠️  Khong tim thay {pretrained_path}")
        print(f"   Dung trong so khoi tao ngau nhien.")
    print(f"{'='*70}\n")

    initial_weights = [val.cpu().numpy() for _, val in dummy_model.state_dict().items()]
    initial_parameters = fl.common.ndarrays_to_parameters(initial_weights)

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
