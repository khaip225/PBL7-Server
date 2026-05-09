TASK_CONFIG = {
    "audio": {
        "default_port": 8080,
        "default_pretrained": "pretrained_audio.pth",
        "min_samples": 300,
        "round_prefix": "audio",
        "best_model_file": "best_global_audio.pth",
        "display_name": "Audio",
    },
    "image": {
        "default_port": 8081,
        "default_pretrained": "pretrained_xray.pth",
        "min_samples": 300,
        "round_prefix": "image",
        "best_model_file": "best_global_image.pth",
        "display_name": "Image",
    },
}

DEFAULT_SETTINGS = {
    "flower.default_port_audio": 8080,
    "flower.default_port_image": 8081,
    "system.log_level": "INFO",
    "system.max_concurrent_jobs": 2,
    "system.models_dir": "aggregated_models",
    "aggregation.default_strategy": "fedavg",
    "aggregation.min_samples_default": 300,
    "aggregation.min_clients_default": 2,
}
