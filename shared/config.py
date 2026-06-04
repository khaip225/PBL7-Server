TASK_CONFIG = {
    "audio": {
        "display_name": "Audio Prototype FL",
        "default_port": 8080,
        "default_pretrained": None,  # Prototype FL: encoder pretrained from Kaggle checkpoint
        "min_samples": 100,
        "round_prefix": "audio_proto",
        "best_model_file": "best_global_audio_proto.pth",
        "num_classes": 3,            # normal, crackle, wheeze
        "class_names": ["normal", "crackle", "wheeze"],
        "fl_mode": "proto",          # Prototype-only sharing
    },
    "image": {
        "display_name": "Image Prototype FL",
        "default_port": 8081,
        "default_pretrained": None,  # Prototype FL: encoder pretrained from Kaggle checkpoint
        "min_samples": 100,
        "round_prefix": "image_proto",
        "best_model_file": "best_global_image_proto.pth",
        "num_classes": 4,            # Normal, Pneumonia, COPD, Fibrosis
        "class_names": ["Normal", "Pneumonia", "COPD_Emphysema", "Fibrosis"],
        "fl_mode": "proto",          # Prototype-only sharing
    },
    "alignment": {
        "display_name": "Prototype Alignment FL",
        "default_port": 8082,
        "default_pretrained": None,
        "min_samples": 50,
        "round_prefix": "alignment_proto",
        "best_model_file": "best_global_prototypes.pth",
        "num_classes": 0,            # No classes — pure prototype alignment
        "class_names": [],
        "fl_mode": "proto",
    },
}

DEFAULT_SETTINGS = {
    "flower.default_port_audio": 8080,
    "flower.default_port_image": 8081,
    "flower.default_port_alignment": 8082,
    "system.log_level": "INFO",
    "system.max_concurrent_jobs": 2,
    "system.models_dir": "aggregated_models",
    "aggregation.default_strategy": "fedavg",
    "aggregation.min_samples_default": 100,  # Prototype FL: lower threshold
    "aggregation.min_clients_default": 2,
    "fl.default_mode": "proto",              # Prototype-only sharing
}
