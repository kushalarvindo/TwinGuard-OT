// Core TypeScript types matching the backend API responses

export interface SystemStatus {
  digital_twin: string;
  virtual_plc: string;
  modbus_server: string;
  telemetry_collector: string;
  detection_engine: string;
  ml_model: string;
  database: string;
  overall: string;
}

export interface TwinState {
  timestamp: number;
  simulated_time_sec: number;
  true_level: number;
  sensor_level: number;
  residual: number;
  pump_state: number;
  valve_state: number;
  true_inflow: number;
  sensor_inflow: number;
  true_outflow: number;
  sensor_outflow: number;
  is_overflow: boolean;
  is_dry_run: boolean;
  sensor_spoofed: boolean;
  setpoint: number;
  low_threshold: number;
  high_threshold: number;
  alarm_state: number;
  plc_mode: string;
}

export interface TelemetryFrame {
  timestamp: number;
  true_level: number;
  sensor_level: number;
  residual: number;
  inflow: number;
  outflow: number;
  pump_state: number;
  valve_state: number;
  setpoint: number;
  low_threshold: number;
  high_threshold: number;
  alarm_state: number;
  is_overflow: boolean;
  is_dry_run: boolean;
  sensor_spoofed: boolean;
  request_rate: number;
  anomaly_score: number;
  is_anomaly: boolean;
  active_attack: string | null;
  plc_mode: string;
}

export interface ModbusStatus {
  host: string;
  port: number;
  is_running: boolean;
  transaction_count: number;
  request_rate: number;
}

export interface ModbusRegister {
  offset: number;
  address: number;
  name: string;
  raw: number;
  value: number;
  unit: string;
  rw: string;
}

export interface ModbusEvent {
  id: number;
  timestamp: number;
  client_ip: string;
  function_code: number;
  function_name: string;
  register_address: number;
  register_name: string;
  value: number;
  is_write: number;
  request_rate: number;
}

export interface DetectionStatus {
  is_anomaly: boolean;
  category: string;
  severity: string;
  anomaly_score: number;
  explanation: string;
  active_rules: string[];
  ml_trained: boolean;
}

export interface Alert {
  id: string;
  timestamp: number;
  is_anomaly: boolean;
  category: string;
  severity: string;
  anomaly_score: number;
  explanation: string;
  active_rules: string[];
}

export interface AttackInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: string;
  target: string;
  params: Record<string, {
    type: string;
    default: number;
    min: number;
    max: number;
    description: string;
  }>;
  expected_effect: string;
}

export interface AttackJob {
  job_id: string;
  attack_type: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'STOPPED';
  elapsed_sec: number;
  duration_sec: number;
  progress: number;
  events_injected: number;
  metrics: Record<string, unknown>;
  error: string | null;
}

export interface ExperimentJob {
  job_id: string;
  experiment_type: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  phase: string;
  elapsed_sec: number;
  result_path: string | null;
  error: string | null;
  progress_log: string[];
}

export interface Experiment {
  id: string;
  name: string;
  attack_type: string;
  start_time: number;
  end_time: number | null;
  duration_sec: number | null;
  status: string;
  notes: string | null;
}

export interface EvaluationResult {
  id: number;
  experiment_id: string;
  model_name: string;
  total_samples: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  detection_latency_sec: number | null;
  computed_at: number;
}

export interface Dataset {
  id: string;
  filename: string;
  path: string;
  size_bytes: number;
  created: number;
}
