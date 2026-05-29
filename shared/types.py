from enum import Enum


class TaskType(str, Enum):
    AUDIO = "audio"
    IMAGE = "image"
    ALIGNMENT = "alignment"


class FLMode(str, Enum):
    FULL_MODEL = "full"
    PROTOTYPE_ONLY = "proto"


class JobStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


class ClientStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    IDLE = "idle"
    TRAINING = "training"


class AggregationStrategy(str, Enum):
    FEDAVG = "fedavg"
    FEDPROX = "fedprox"
    FEDADAM = "fedadam"
    CUSTOM = "custom"


class WSEventType(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CLIENT_CONNECTED = "client_connected"
    CLIENT_DISCONNECTED = "client_disconnected"
    CLIENT_HEARTBEAT = "client_heartbeat"
    CLIENT_STATUS_CHANGED = "client_status_changed"
    ROUND_STARTED = "round_started"
    CLIENT_TRAINING_STARTED = "client_training_started"
    CLIENT_TRAINING_COMPLETED = "client_training_completed"
    TRAINING_PROGRESS = "training_progress"
    ROUND_COMPLETED = "round_completed"
    AGGREGATION_COMPLETED = "aggregation_completed"
    METRICS_UPDATE = "metrics_update"
    JOB_STARTED = "job_started"
    JOB_STOPPED = "job_stopped"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    CHECKPOINT_SAVED = "checkpoint_saved"
    MODEL_ACTIVATED = "model_activated"
    SYSTEM_EVENT = "system_event"
    ERROR_EVENT = "error_event"


class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
