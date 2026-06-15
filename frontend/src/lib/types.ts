export type TaskType = "audio" | "image" | "alignment";
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
  auroc_macro: number | null;
  per_class_auroc: Record<string, number> | null;
  prototype_data: Record<string, unknown> | null;
  num_clients: number;
  num_skipped: number;
  duration_seconds: number | null;
  client_metrics: Record<string, unknown>[];
  aggregated_at: string;
}

export interface PrototypeEvolution {
  job_id: string;
  rounds: number[];
  ontology_alignment: number[];
  positive_similarity: number[];
  negative_similarity: number[];
  similarity_matrix: number[][][];
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

export interface OverviewMetrics {
  total_clients: number;
  online_clients: number;
  active_jobs: number;
  completed_jobs: number;
  total_checkpoints: number;
  best_accuracy: number | null;
  best_auroc: number | null;
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
