// ============================================================
// src/data/mockData.ts
// SYNTHETIC DEMO DATA — for software pipeline testing only.
// NOT derived from real patient measurements.
// ============================================================

import type {
  DashboardSummary, GaitSession, GaitFeatures, Prediction,
  SensorPoint, SessionDetail, ModelPerformance, Subject,
  GaitClass,
} from '../types';

// ── Helpers ──────────────────────────────────────────────────
function rnd(min: number, max: number, decimals = 2): number {
  return parseFloat((Math.random() * (max - min) + min).toFixed(decimals));
}

const GAIT_COLORS: Record<GaitClass, string> = {
  normal:       '#22c55e',
  parkinsonian: '#f97316',
  hemiplegic:   '#ef4444',
  ataxic:       '#a855f7',
  spastic:      '#06b6d4',
  antalgic:     '#eab308',
};

// ── Mock Sensor Stream ────────────────────────────────────────
export function generateSensorPoints(n = 200, gaitClass: GaitClass = 'normal'): SensorPoint[] {
  const noiseMap: Record<GaitClass, number> = {
    normal: 0.3, parkinsonian: 0.6, hemiplegic: 0.8,
    ataxic: 1.2, spastic: 0.7, antalgic: 0.5,
  };
  const noise = noiseMap[gaitClass];
  return Array.from({ length: n }, (_, i) => ({
    timestamp: parseFloat((i * 0.01).toFixed(2)),
    acceleration_x: parseFloat((Math.sin(i * 0.3) * 2 + rnd(-noise, noise)).toFixed(4)),
    acceleration_y: parseFloat((Math.cos(i * 0.3) * 3 + 9.8 + rnd(-noise, noise)).toFixed(4)),
    acceleration_z: parseFloat((Math.sin(i * 0.15) * 1.5 + rnd(-noise, noise)).toFixed(4)),
    gyroscope_x:    parseFloat((Math.sin(i * 0.2) * 0.5 + rnd(-noise * 0.3, noise * 0.3)).toFixed(4)),
    gyroscope_y:    parseFloat((Math.cos(i * 0.25) * 0.4 + rnd(-noise * 0.3, noise * 0.3)).toFixed(4)),
    gyroscope_z:    parseFloat((Math.sin(i * 0.35) * 0.3 + rnd(-noise * 0.2, noise * 0.2)).toFixed(4)),
  }));
}

// ── Mock Features ─────────────────────────────────────────────
export const MOCK_FEATURES: Record<GaitClass, GaitFeatures> = {
  normal: {
    session_id: 'GS-240524-001', step_count: 82, cadence: 109.3,
    walking_speed: 1.35, step_length: 0.698, stride_length: 1.396,
    step_time: 0.549, stride_time: 1.098, stance_time: 0.659,
    swing_time: 0.415, gait_symmetry: 0.961,
    mean_acceleration: 9.85, acceleration_std: 0.82, acceleration_rms: 9.89,
  },
  parkinsonian: {
    session_id: 'GS-240524-002', step_count: 76, cadence: 120.0,
    walking_speed: 0.65, step_length: 0.325, stride_length: 0.65,
    step_time: 0.5, stride_time: 1.0, stance_time: 0.62,
    swing_time: 0.31, gait_symmetry: 0.781,
    mean_acceleration: 8.72, acceleration_std: 2.1, acceleration_rms: 9.12,
  },
  hemiplegic: {
    session_id: 'GS-240523-003', step_count: 38, cadence: 57.0,
    walking_speed: 0.48, step_length: 0.42, stride_length: 0.84,
    step_time: 1.053, stride_time: 2.105, stance_time: 0.73,
    swing_time: 0.38, gait_symmetry: 0.524,
    mean_acceleration: 8.15, acceleration_std: 3.2, acceleration_rms: 8.8,
  },
  ataxic: {
    session_id: 'GS-240523-004', step_count: 42, cadence: 72.0,
    walking_speed: 0.55, step_length: 0.458, stride_length: 0.916,
    step_time: 0.833, stride_time: 1.667, stance_time: 0.72,
    swing_time: 0.42, gait_symmetry: 0.632,
    mean_acceleration: 8.4, acceleration_std: 4.1, acceleration_rms: 9.2,
  },
  spastic: {
    session_id: 'GS-240522-005', step_count: 50, cadence: 71.4,
    walking_speed: 0.58, step_length: 0.41, stride_length: 0.82,
    step_time: 0.84, stride_time: 1.68, stance_time: 0.73,
    swing_time: 0.28, gait_symmetry: 0.712,
    mean_acceleration: 9.1, acceleration_std: 2.7, acceleration_rms: 9.5,
  },
  antalgic: {
    session_id: 'GS-240522-006', step_count: 68, cadence: 81.6,
    walking_speed: 0.82, step_length: 0.502, stride_length: 1.005,
    step_time: 0.735, stride_time: 1.47, stance_time: 0.51,
    swing_time: 0.48, gait_symmetry: 0.738,
    mean_acceleration: 9.3, acceleration_std: 1.6, acceleration_rms: 9.55,
  },
};

// ── Mock Sessions ─────────────────────────────────────────────
export const MOCK_SESSIONS: GaitSession[] = [
  {
    session_id: 'GS-240524-001', user_id: 2, subject_id: 'SUB-001',
    session_date: '2024-05-24T10:30:00+05:30', duration_seconds: 120,
    walking_condition: 'lab', data_source: 'uploaded_csv',
    file_name: 'walk_trial_01.csv', status: 'completed', created_at: '2024-05-24T10:30:00+05:30',
  },
  {
    session_id: 'GS-240524-002', user_id: 2, subject_id: 'SUB-002',
    session_date: '2024-05-24T09:15:00+05:30', duration_seconds: 110,
    walking_condition: 'lab', data_source: 'uploaded_csv',
    file_name: 'parkinson_trial.csv', status: 'completed', created_at: '2024-05-24T09:15:00+05:30',
  },
  {
    session_id: 'GS-240523-003', user_id: 2, subject_id: 'SUB-003',
    session_date: '2024-05-23T16:20:00+05:30', duration_seconds: 125,
    walking_condition: 'lab', data_source: 'uploaded_csv',
    file_name: 'hemi_trial.csv', status: 'completed', created_at: '2024-05-23T16:20:00+05:30',
  },
  {
    session_id: 'GS-240523-004', user_id: 2, subject_id: 'SUB-004',
    session_date: '2024-05-23T11:05:00+05:30', duration_seconds: 100,
    walking_condition: 'lab', data_source: 'simulated',
    status: 'completed', created_at: '2024-05-23T11:05:00+05:30',
  },
  {
    session_id: 'GS-240522-005', user_id: 2, subject_id: 'SUB-005',
    session_date: '2024-05-22T14:40:00+05:30', duration_seconds: 115,
    walking_condition: 'outdoor', data_source: 'uploaded_csv',
    file_name: 'spastic_trial.csv', status: 'completed', created_at: '2024-05-22T14:40:00+05:30',
  },
  {
    session_id: 'GS-240522-006', user_id: 2, subject_id: 'SUB-006',
    session_date: '2024-05-22T10:30:00+05:30', duration_seconds: 90,
    walking_condition: 'lab', data_source: 'uploaded_csv',
    file_name: 'antalgic_trial.csv', status: 'completed', created_at: '2024-05-22T10:30:00+05:30',
  },
  {
    session_id: 'GS-240521-007', user_id: 2, subject_id: 'SUB-001',
    session_date: '2024-05-21T09:00:00+05:30', duration_seconds: 130,
    walking_condition: 'treadmill', data_source: 'uploaded_csv',
    file_name: 'walk_trial_02.csv', status: 'completed', created_at: '2024-05-21T09:00:00+05:30',
  },
];

// ── Mock Predictions ──────────────────────────────────────────
export const MOCK_PREDICTIONS: Record<string, Prediction> = {
  'GS-240524-001': {
    prediction_id: 1, session_id: 'GS-240524-001',
    predicted_class: 'normal', confidence_score: 0.9312,
    model_name: 'random_forest_baseline', model_version: '1.0.0',
    prediction_timestamp: '2024-05-24T10:31:00+05:30',
    probabilities: { normal: 0.9312, parkinsonian: 0.02, hemiplegic: 0.01, ataxic: 0.01, spastic: 0.02, antalgic: 0.0088 },
  },
  'GS-240524-002': {
    prediction_id: 2, session_id: 'GS-240524-002',
    predicted_class: 'parkinsonian', confidence_score: 0.8741,
    model_name: 'random_forest_baseline', model_version: '1.0.0',
    prediction_timestamp: '2024-05-24T09:16:00+05:30',
    probabilities: { normal: 0.05, parkinsonian: 0.8741, hemiplegic: 0.02, ataxic: 0.03, spastic: 0.02, antalgic: 0.0059 },
  },
  'GS-240523-003': {
    prediction_id: 3, session_id: 'GS-240523-003',
    predicted_class: 'hemiplegic', confidence_score: 0.8120,
    model_name: 'random_forest_baseline', model_version: '1.0.0',
    prediction_timestamp: '2024-05-23T16:21:00+05:30',
    probabilities: { normal: 0.06, parkinsonian: 0.03, hemiplegic: 0.812, ataxic: 0.04, spastic: 0.03, antalgic: 0.028 },
  },
  'GS-240523-004': {
    prediction_id: 4, session_id: 'GS-240523-004',
    predicted_class: 'ataxic', confidence_score: 0.7654,
    model_name: 'random_forest_baseline', model_version: '1.0.0',
    prediction_timestamp: '2024-05-23T11:06:00+05:30',
    probabilities: { normal: 0.08, parkinsonian: 0.04, hemiplegic: 0.05, ataxic: 0.7654, spastic: 0.04, antalgic: 0.0246 },
  },
  'GS-240522-005': {
    prediction_id: 5, session_id: 'GS-240522-005',
    predicted_class: 'spastic', confidence_score: 0.8003,
    model_name: 'random_forest_baseline', model_version: '1.0.0',
    prediction_timestamp: '2024-05-22T14:41:00+05:30',
    probabilities: { normal: 0.07, parkinsonian: 0.04, hemiplegic: 0.03, ataxic: 0.04, spastic: 0.8003, antalgic: 0.0197 },
  },
  'GS-240522-006': {
    prediction_id: 6, session_id: 'GS-240522-006',
    predicted_class: 'antalgic', confidence_score: 0.8225,
    model_name: 'random_forest_baseline', model_version: '1.0.0',
    prediction_timestamp: '2024-05-22T10:31:00+05:30',
    probabilities: { normal: 0.06, parkinsonian: 0.03, hemiplegic: 0.04, ataxic: 0.025, spastic: 0.0225, antalgic: 0.8225 },
  },
};

// ── Dashboard Summary ─────────────────────────────────────────
export const MOCK_DASHBOARD: DashboardSummary = {
  total_sessions: 24,
  normal_gait: 15,
  abnormal_gait: 9,
  avg_confidence: 0.874,
  sessions_this_month: 24,
  gait_distribution: [
    { name: 'Normal',       value: 15, color: GAIT_COLORS.normal },
    { name: 'Parkinsonian', value: 4,  color: GAIT_COLORS.parkinsonian },
    { name: 'Hemiplegic',   value: 2,  color: GAIT_COLORS.hemiplegic },
    { name: 'Ataxic',       value: 1,  color: GAIT_COLORS.ataxic },
    { name: 'Spastic',      value: 1,  color: GAIT_COLORS.spastic },
    { name: 'Antalgic',     value: 1,  color: GAIT_COLORS.antalgic },
  ],
  recent_sessions: [
    { session_id: 'GS-240524-001', subject_id: 'SUB-001', gait_class: 'normal',       confidence: 0.9312, date: '2 mins ago' },
    { session_id: 'GS-240524-002', subject_id: 'SUB-002', gait_class: 'parkinsonian', confidence: 0.8741, date: '1 hour ago' },
    { session_id: 'GS-240523-003', subject_id: 'SUB-003', gait_class: 'hemiplegic',   confidence: 0.8120, date: 'Yesterday' },
    { session_id: 'GS-240523-004', subject_id: 'SUB-004', gait_class: 'ataxic',       confidence: 0.7654, date: '2 days ago' },
    { session_id: 'GS-240522-005', subject_id: 'SUB-005', gait_class: 'spastic',      confidence: 0.8003, date: '3 days ago' },
  ],
  latest_features: MOCK_FEATURES.normal,
};

// ── Model Performance ─────────────────────────────────────────
export const MOCK_MODEL_PERFORMANCE: ModelPerformance = {
  model_id: 1,
  model_name: 'random_forest_baseline',
  model_version: '1.0.0',
  accuracy: 0.8333,
  precision_score: 0.8412,
  recall_score: 0.8333,
  f1_score: 0.8350,
  training_samples: 96,
  testing_samples: 24,
  training_date: '2024-09-01T08:00:00+05:30',
  per_class_f1: {
    normal: 0.912, parkinsonian: 0.875, hemiplegic: 0.812,
    ataxic: 0.765, spastic: 0.800, antalgic: 0.818,
  },
  confusion_matrix: [
    [14,  1,  0,  0,  0,  0],
    [ 1, 13,  1,  0,  0,  0],
    [ 0,  0, 10,  2,  0,  0],
    [ 0,  0,  1,  9,  0,  0],
    [ 0,  1,  0,  0, 12,  1],
    [ 0,  0,  0,  1,  0, 11],
  ],
  class_names: ['normal', 'parkinsonian', 'hemiplegic', 'ataxic', 'spastic', 'antalgic'],
};

// ── Subjects ──────────────────────────────────────────────────
export const MOCK_SUBJECTS: Subject[] = [
  { subject_id: 'SUB-001', age_group: '25-34', sex: 'M', session_count: 3, last_session: '2024-05-24', latest_gait_class: 'normal' },
  { subject_id: 'SUB-002', age_group: '55-64', sex: 'M', session_count: 2, last_session: '2024-05-24', latest_gait_class: 'parkinsonian' },
  { subject_id: 'SUB-003', age_group: '45-54', sex: 'F', session_count: 2, last_session: '2024-05-23', latest_gait_class: 'hemiplegic' },
  { subject_id: 'SUB-004', age_group: '35-44', sex: 'Other', session_count: 1, last_session: '2024-05-23', latest_gait_class: 'ataxic' },
  { subject_id: 'SUB-005', age_group: '18-24', sex: 'F', session_count: 1, last_session: '2024-05-22', latest_gait_class: 'spastic' },
  { subject_id: 'SUB-006', age_group: '65+',   sex: 'M', session_count: 1, last_session: '2024-05-22', latest_gait_class: 'antalgic' },
];

export const GAIT_COLORS_MAP = GAIT_COLORS;

// ── Session Detail helper ─────────────────────────────────────
export function getMockSessionDetail(sessionId: string): SessionDetail | null {
  const session = MOCK_SESSIONS.find(s => s.session_id === sessionId);
  if (!session) return null;
  const prediction = MOCK_PREDICTIONS[sessionId];
  if (!prediction) return null;
  const features = MOCK_FEATURES[prediction.predicted_class];
  const sensor_data = generateSensorPoints(200, prediction.predicted_class);
  return { session: { ...session }, features: { ...features, session_id: sessionId }, prediction, sensor_data };
}
