import flwr as fl
import argparse
import os
import torch
from collections import OrderedDict
from cnn14_model import CNN14 

class SaveModelStrategy(fl.server.strategy.FedAvg):
    def aggregate_fit(self, server_round, results, failures):
        # 1. Gọi FedAvg để tổng hợp tạ (dựa trên sample count của từng client)
        aggregated_weights, aggregated_metrics = super().aggregate_fit(server_round, results, failures)
        
        # 2. Lưu file best_global_model.pth
        if aggregated_weights is not None:
            print(f"--- Đang lưu mô hình toàn cục Vòng {server_round} ---")
            
            ndarrays = fl.common.parameters_to_ndarrays(aggregated_weights)
            dummy_model = CNN14()
            params_dict = zip(dummy_model.state_dict().keys(), ndarrays)
            state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
            
            dummy_model.load_state_dict(state_dict, strict=False)
            
            os.makedirs("aggregated_models", exist_ok=True)
            save_path = f"aggregated_models/audio_round_{server_round}.pth"
            torch.save(dummy_model.state_dict(), save_path)
            
            # Ghi đè luôn vào file public để Desktop App tải về
            torch.save(dummy_model.state_dict(), "best_global_audio.pth")
            print(f"--- Đã cập nhật: best_global_audio.pth ---")

        return aggregated_weights, aggregated_metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flower Server")
    parser.add_argument("--rounds", type=int, default=5)
    args = parser.parse_args()

    # --- BƯỚC NẠP PRETRAIN ---
    print("Đang nạp Pretrain Model làm trọng số khởi điểm...")
    dummy_model = CNN14()
    # Thay bằng tên file thực tế của bạn
    dummy_model.load_state_dict(torch.load("best_global_audio.pth", map_location="cpu"))
    
    # Ép kiểu PyTorch sang kiểu NumPy của Flower
    initial_weights = [val.cpu().numpy() for _, val in dummy_model.state_dict().items()]
    initial_parameters = fl.common.ndarrays_to_parameters(initial_weights)
    # -------------------------

    strategy = SaveModelStrategy(
        min_fit_clients=2,
        min_available_clients=2, 
        initial_parameters=initial_parameters # TRUYỀN TẠ GỐC VÀO ĐÂY
    )
    
    print(f"Khởi động FL Server... (Số vòng cấu hình: {args.rounds})")
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=args.rounds),
        strategy=strategy,
        grpc_max_message_length=1024 * 1024 * 1024
    )