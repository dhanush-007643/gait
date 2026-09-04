// ============================================================
// src/types/index.ts
// All TypeScript interfaces for GaitInsight
// ============================================================

// ── Gait Classes ─────────────────────────────────────────────
export type GaitClass =
  | 'normal'
  | 'parkinsonian'
  | 'hemiplegic'
  | 'ataxic'
  | 'spastic'
  | 'antalgic';

export type UserRole = 'admin' | 'researcher' | 'clinician' | 'student';

export type DataSource = 'uploaded_csv' | 'simulated' | 'public_dataset';

export type SessionStatus = 'pending' | 'processing' | 'completed' | 'failed';

// ── Auth ──────────────────────────────────────────────────────
export interface User {
  user_id: number;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
  avatar?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

// ── Gait Sessions ─────────────────────────────────────────────
export interface GaitSession {
  session_id: string;
  user_id: number;
  subject_id: string;
  session_date: string;
  duration_seconds: number;
  walking_condition: string;
  data_source: DataSource;
  file_name?: string;
  status: SessionStatus;
  created_at: string;
  predicted_class?: GaitClass;
  confidence_score?: number;
}

// ── Gait Features ─────────────────────────────────────────────
export interface GaitFeatures {
  session_id: string;
  step_count: number;
  cadence: number;            // steps/min
  walking_speed: number;      // m/s
  step_length: number;        // m
  stride_length: number;      // m
  step_time: number;          // s
  stride_time: number;        // s
  stance_time: number;        // s
  swing_time: number;         // s
  gait_symmetry: number;      // ratio 0–1
  mean_acceleration: number;  // m/s²
  acceleration_std: number;
  acceleration_rms: number;
}

// ── Predictions ───────────────────────────────────────────────
export interface Prediction {
  prediction_id: number;
  session_id: string;
  predicted_class: GaitClass;
  confidence_score: number;   // 0–1
  model_name: string;
  model_version: string;
  prediction_timestamp: string;
  probabilities: Record<GaitClass, number>;
}

// ── Sensor Data ───────────────────────────────────────────────
export interface SensorPoint {
  timestamp: number;
  acceleration_x: number;
  acceleration_y: number;
  acceleration_z: number;
  gyroscope_x: number;
  gyroscope_y: number;
  gyroscope_z: number;
}

// ── Dashboard ─────────────────────────────────────────────────
export interface DashboardSummary {
  total_sessions: number;
  normal_gait: number;
  abnormal_gait: number;
  avg_confidence: number;
  sessions_this_month: number;
  gait_distribution: GaitDistribution[];
  recent_sessions: RecentSession[];
  latest_features?: GaitFeatures;
}

export interface GaitDistribution {
  name: string;
  value: number;
  color: string;
}

export interface RecentSession {
  session_id: string;
  subject_id: string;
  gait_class: GaitClass;
  confidence: number;
  date: string;
}

// ── Session Detail ────────────────────────────────────────────
export interface SessionDetail {
  session: GaitSession;
  features: GaitFeatures;
  prediction: Prediction;
  sensor_data?: SensorPoint[];
}

// ── Model Performance ─────────────────────────────────────────
export interface ModelPerformance {
  model_id: number;
  model_name: string;
  model_version: string;
  accuracy: number;
  precision_score: number;
  recall_score: number;
  f1_score: number;
  training_samples: number;
  testing_samples: number;
  training_date: string;
  per_class_f1: Record<GaitClass, number>;
  confusion_matrix: number[][];
  class_names: GaitClass[];
}

// ── Subjects ──────────────────────────────────────────────────
export interface Subject {
  subject_id: string;
  age_group: string;
  sex?: 'M' | 'F' | 'Other' | 'Prefer not to say';
  session_count: number;
  last_session: string;
  latest_gait_class?: GaitClass;
}

// ── Upload ────────────────────────────────────────────────────
export interface UploadResult {
  session_id: string;
  rows_parsed: number;
  duration_seconds: number;
  columns_found: string[];
  status: 'success' | 'error';
  message: string;
}

// ── API Generic ───────────────────────────────────────────────
export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
