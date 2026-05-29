TASK_CONFIG = {
    "audio": {
        "default_port": 8080,
        "default_pretrained": "pretrained_audio_multilabel.pth",
        "min_samples": 300,
        "round_prefix": "audio",
        "best_model_file": "best_global_audio.pth",
        "display_name": "Audio",
        "num_classes": 2,
        "class_names": ["Crackle", "Wheeze"],
    },
    "image": {
        "default_port": 8081,
        "default_pretrained": "pretrained_xray_multilabel.pth",
        "min_samples": 300,
        "round_prefix": "image",
        "best_model_file": "best_global_image.pth",
        "display_name": "Image",
        "num_classes": 3,
        "class_names": ["Pneumonia", "COPD_Emphysema", "Fibrosis"],
    },
    "alignment": {
        "default_port": 8082,
        "default_pretrained": None,
        "min_samples": 100,
        "round_prefix": "alignment",
        "best_model_file": "best_global_prototypes.pth",
        "display_name": "Prototype Alignment",
        "fl_mode": "proto",
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
