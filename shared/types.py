from enum import Enum


class TaskType(str, Enum):
    AUDIO = "audio"
    IMAGE = "image"
    ALIGNMENT = "alignment"



class JobStatus(str, Enum):
    DRAFT = "draft"
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
    ROUND_STARTED = "round_started"
    CLIENT_TRAINING_COMPLETED = "client_training_completed"
    ROUND_COMPLETED = "round_completed"
    AGGREGATION_COMPLETED = "aggregation_completed"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    CHECKPOINT_SAVED = "checkpoint_saved"
    SYSTEM_EVENT = "system_event"
    ERROR_EVENT = "error_event"


class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
