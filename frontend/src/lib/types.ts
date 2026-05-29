export type TaskType = "audio" | "image";
export type JobStatus = "draft" | "pending" | "running" | "completed" | "stopped" | "failed";
export type ClientStatus = "online" | "offline" | "idle" | "training";
export type AggregationStrategy = "fedavg" | "fedprox" | "fedadam" | "custom";

export interface Client {
  id: string;
  client_name: string;
  client_host: string;
  task_type: TaskType | null;
  status: ClientStatus;
  last_heartbeat: string | null;
  hardware_info: Record<string, unknown>;
  dataset_info: Record<string, unknown>;
  fl_client_id: number | null;
  latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface TrainingJob {
  id: string;
  name: string;
  task_type: TaskType;
  status: JobStatus;
  strategy: AggregationStrategy;
  strategy_params: Record<string, unknown>;
  num_rounds: number;
  min_clients: number;
  min_samples: number;
  model_config: Record<string, unknown>;
  flower_config: Record<string, unknown>;
  pid: number | null;
  current_round: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoundMetrics {
  id: string;
  round_number: number;
  loss: number | null;
  accuracy: number | null;
  num_clients: number;
  num_skipped: number;
  duration_seconds: number | null;
  client_metrics: ClientRoundMetric[];
  aggregated_at: string;
}

export interface ClientRoundMetric {
  client_id: string;
  client_name: string;
  num_samples: number;
  loss: number;
  accuracy: number;
}

export interface Checkpoint {
  id: string;
  job_id: string;
  round_number: number;
  file_path: string;
  file_size_bytes: number | null;
  sha256_hash: string | null;
  is_best: boolean;
  is_active: boolean;
  created_at: string;
}

export interface EventLog {
  id: string;
  job_id: string | null;
  event_type: string;
  severity: "info" | "warning" | "error" | "critical";
  payload: Record<string, unknown>;
  created_at: string;
}

export interface OverviewMetrics {
  total_clients: number;
  online_clients: number;
  active_jobs: number;
  completed_jobs: number;
  total_checkpoints: number;
  best_accuracy: number | null;
}

export interface WSMessage {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface UserResponse {
  id: string;
  username: string;
  display_name: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}
